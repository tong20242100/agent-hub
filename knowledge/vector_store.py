#!/usr/bin/env python3
"""
向量检索核心 - 跨工具共享知识层
支持语义搜索 knowledge/ 目录下的所有研究和文档
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# 延迟导入，避免未安装时报错
_chromadb = None
_embedding_fn = None

KNOWLEDGE_DIR = Path(__file__).parent
CHROMA_DIR = KNOWLEDGE_DIR / ".chroma_db"
USER_PROFILE_PATH = KNOWLEDGE_DIR / "user_profile.json"


def _get_embedding_fn():
    """延迟加载嵌入模型"""
    global _embedding_fn
    if _embedding_fn is None:
        from chromadb.utils import embedding_functions
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"  # 384维，快速，适合本地
        )
    return _embedding_fn


def _get_chroma_client():
    """延迟加载 ChromaDB 客户端"""
    global _chromadb
    if _chromadb is None:
        import chromadb
        _chromadb = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _chromadb


def _get_collection():
    """获取或创建知识库集合"""
    client = _get_chroma_client()
    embedding_fn = _get_embedding_fn()
    return client.get_or_create_collection(
        name="knowledge",
        embedding_function=embedding_fn,
        metadata={"description": "Agent-Hub 跨工具知识库"}
    )


def _compute_hash(content: str) -> str:
    """计算内容哈希，用于去重"""
    return hashlib.md5(content.encode()).hexdigest()[:12]


def index_knowledge(force: bool = False) -> Dict[str, Any]:
    """
    索引 knowledge/research/ 目录下的所有 Markdown 文件
    
    Args:
        force: 是否强制重建索引
    
    Returns:
        索引统计信息
    """
    collection = _get_collection()
    research_dir = KNOWLEDGE_DIR / "research"
    
    if not research_dir.exists():
        return {"status": "error", "message": "research/ 目录不存在"}
    
    # 获取现有索引的 ID
    existing_ids = set()
    if not force:
        result = collection.get()
        existing_ids = set(result["ids"]) if result["ids"] else set()
    
    indexed = 0
    skipped = 0
    errors = []
    
    for md_file in research_dir.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            
            # 跳过空文件
            if len(content.strip()) < 100:
                continue
            
            # 生成唯一 ID
            doc_id = f"research_{md_file.stem}"
            content_hash = _compute_hash(content)
            
            # 检查是否需要更新
            if not force and doc_id in existing_ids:
                # 检查内容是否变化
                existing = collection.get(ids=[doc_id], include=["metadatas"])
                if existing["metadatas"] and existing["metadatas"][0].get("hash") == content_hash:
                    skipped += 1
                    continue
            
            # 分块：按标题切分，每块不超过 1000 字符
            chunks = _chunk_content(content, max_size=1000)
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                
                collection.upsert(
                    ids=[chunk_id],
                    documents=[chunk["content"]],
                    metadatas=[{
                        "source": str(md_file.relative_to(KNOWLEDGE_DIR)),
                        "title": md_file.stem,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "hash": content_hash,
                        "indexed_at": datetime.now().isoformat(),
                        "type": "research"
                    }]
                )
            
            indexed += 1
            
        except Exception as e:
            errors.append(f"{md_file.name}: {str(e)}")
    
    return {
        "status": "success",
        "indexed": indexed,
        "skipped": skipped,
        "errors": errors,
        "total_documents": collection.count()
    }


def _chunk_content(content: str, max_size: int = 1000) -> List[Dict[str, Any]]:
    """按标题切分内容"""
    chunks = []
    lines = content.split("\n")
    current_chunk = []
    current_size = 0
    current_title = ""
    
    for line in lines:
        # 检测标题
        if line.startswith("# "):
            # 保存当前块
            if current_chunk and current_size > 100:
                chunks.append({
                    "content": "\n".join(current_chunk),
                    "title": current_title
                })
            current_chunk = [line]
            current_title = line[2:].strip()
            current_size = len(line)
        elif line.startswith("## ") and current_size > max_size * 0.5:
            # 二级标题，如果当前块够大就切分
            if current_chunk:
                chunks.append({
                    "content": "\n".join(current_chunk),
                    "title": current_title
                })
            current_chunk = [line]
            current_size = len(line)
        else:
            current_chunk.append(line)
            current_size += len(line)
            
            # 超过最大尺寸，强制切分
            if current_size > max_size * 1.5:
                chunks.append({
                    "content": "\n".join(current_chunk),
                    "title": current_title
                })
                current_chunk = []
                current_size = 0
    
    # 保存最后一块
    if current_chunk and current_size > 50:
        chunks.append({
            "content": "\n".join(current_chunk),
            "title": current_title
        })
    
    return chunks


def memory_query(query: str, top_k: int = 5, source_filter: str = "") -> List[Dict[str, Any]]:
    """
    语义搜索知识库
    
    Args:
        query: 查询文本
        top_k: 返回结果数量
        source_filter: 来源过滤（如 "research"）
    
    Returns:
        匹配的知识片段列表
    """
    collection = _get_collection()
    
    where_filter = None
    if source_filter:
        where_filter = {"type": source_filter}
    
    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )
    
    formatted_results = []
    if results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            formatted_results.append({
                "id": doc_id,
                "content": results["documents"][0][i][:500] + "..." if len(results["documents"][0][i]) > 500 else results["documents"][0][i],
                "source": results["metadatas"][0][i].get("source", "unknown"),
                "title": results["metadatas"][0][i].get("title", ""),
                "score": 1 - results["distances"][0][i] if results["distances"] else 0.5,
                "indexed_at": results["metadatas"][0][i].get("indexed_at", "")
            })
    
    return formatted_results


def memory_save(content: str, memory_type: str = "insight", tags: List[str] = None, 
                source: str = "unknown") -> Dict[str, Any]:
    """
    保存新的记忆/洞察
    
    Args:
        content: 记忆内容
        memory_type: 类型 (insight / preference / decision / snippet)
        tags: 标签列表
        source: 来源工具
    
    Returns:
        保存结果
    """
    if tags is None:
        tags = []
    
    collection = _get_collection()
    
    # 生成唯一 ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    content_hash = _compute_hash(content)
    doc_id = f"memory_{memory_type}_{timestamp}_{content_hash}"
    
    # 存储到 notes 目录
    notes_dir = KNOWLEDGE_DIR / "notes"
    notes_dir.mkdir(exist_ok=True)
    
    note_file = notes_dir / f"{doc_id}.md"
    note_content = f"""# {memory_type.upper()}: {content[:50]}...

**类型**: {memory_type}
**标签**: {', '.join(tags)}
**来源**: {source}
**时间**: {datetime.now().isoformat()}

---

{content}
"""
    note_file.write_text(note_content, encoding="utf-8")
    
    # 同时索引到向量库
    collection.upsert(
        ids=[doc_id],
        documents=[content],
        metadatas=[{
            "type": memory_type,
            "tags": ",".join(tags),
            "source": source,
            "created_at": datetime.now().isoformat(),
            "file": str(note_file.relative_to(KNOWLEDGE_DIR))
        }]
    )
    
    return {
        "status": "success",
        "id": doc_id,
        "file": str(note_file),
        "message": f"已保存 {memory_type} 到知识库"
    }


# ============ 用户偏好管理 ============

DEFAULT_PROFILE = {
    "user_id": "default",
    "preferences": {
        "language": "zh-CN",
        "tone": "direct",  # direct / detailed / casual
        "focus_areas": [],
        "output_format": "markdown"
    },
    "tool_favorites": {},
    "history": {
        "frequent_tools": [],
        "recent_topics": [],
        "banned_patterns": []
    },
    "updated_at": None
}


def get_user_profile() -> Dict[str, Any]:
    """获取用户偏好配置"""
    if USER_PROFILE_PATH.exists():
        try:
            return json.loads(USER_PROFILE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return DEFAULT_PROFILE.copy()


def update_user_profile(updates: Dict[str, Any]) -> Dict[str, Any]:
    """更新用户偏好"""
    profile = get_user_profile()
    
    # 深度合并
    def deep_merge(base: dict, new: dict) -> dict:
        for key, value in new.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                deep_merge(base[key], value)
            else:
                base[key] = value
        return base
    
    profile = deep_merge(profile, updates)
    profile["updated_at"] = datetime.now().isoformat()
    
    USER_PROFILE_PATH.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    return profile


# ============ CLI 接口 ============

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python vector_store.py index [--force]   # 索引知识库")
        print("  python vector_store.py query <query>     # 语义搜索")
        print("  python vector_store.py profile           # 查看用户偏好")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "index":
        force = "--force" in sys.argv
        result = index_knowledge(force=force)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif command == "query":
        if len(sys.argv) < 3:
            print("请提供查询内容")
            sys.exit(1)
        query = " ".join(sys.argv[2:])
        results = memory_query(query)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    
    elif command == "profile":
        profile = get_user_profile()
        print(json.dumps(profile, ensure_ascii=False, indent=2))
    
    else:
        print(f"未知命令: {command}")
        sys.exit(1)
