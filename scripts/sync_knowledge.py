#!/usr/bin/env python3
import os
import json
import glob
import re
from datetime import datetime

def extract_frontmatter(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 简单的正则匹配 Frontmatter
    match = re.search(r'^---\s*(.*?)\s*---\s*(.*)', content, re.DOTALL)
    if match:
        yaml_str, body = match.groups()
        metadata = {}
        for line in yaml_str.split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                metadata[k.strip()] = v.strip().strip('"').strip("'").strip('[]')
        return metadata, body[:1000] # 返回摘要
    return None, content[:1000]

def sync_knowledge():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    research_dir = os.path.join(root_dir, "knowledge/research")
    index_path = os.path.join(root_dir, "knowledge/KNOWLEDGE_INDEX.json")
    map_path = os.path.join(root_dir, "knowledge/KNOWLEDGE_MAP.md")
    
    index = {"last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "findings": []}
    
    print(f"🔄 [Sync-Knowledge] 正在同步知识库: {research_dir}")
    
    md_files = glob.glob(os.path.join(research_dir, "*.md"))
    for f_path in sorted(md_files, reverse=True):
        fname = os.path.basename(f_path)
        meta, summary_snippet = extract_frontmatter(f_path)
        
        # 尝试从文件名提取日期: Name_Type_YYYYMMDD.md
        date_match = re.search(r'(\d{8})', fname)
        date_str = date_match.group(1) if date_match else "Unknown"
        if date_str != "Unknown":
            date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            
        tags = ["research"]
        title = fname.replace(".md", "")
        final_date = date_str
        
        if meta:
            tags = [t.strip() for t in meta.get("tags", "research").split(',')]
            title = meta.get("title", title)
            final_date = meta.get("date", final_date)
            
        index["findings"].append({
            "title": title,
            "date": final_date,
            "path": f"research/{fname}",
            "tags": tags,
            "summary": summary_snippet.replace('\n', ' ')[:200] + "..."
        })

    # 1. 写入 INDEX.json
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    # 2. 刷新 KNOWLEDGE_MAP.md
    with open(map_path, 'w', encoding='utf-8') as f:
        f.write("# 🦞 Nexus Knowledge Map\n\n")
        f.write(f"最后同步时间: {index['last_updated']}\n\n")
        f.write("| 日期 | 主题 | 标签 | 路径 |\n|---|---|---|---|\n")
        for item in index["findings"]:
            f.write(f"| {item['date']} | {item['title']} | `{','.join(item['tags'])}` | [{item['path']}]({item['path']}) |\n")

    print(f"✅ [Sync-Knowledge] 同步完成。已入库 {len(index['findings'])} 篇研报。")

if __name__ == "__main__":
    sync_knowledge()
