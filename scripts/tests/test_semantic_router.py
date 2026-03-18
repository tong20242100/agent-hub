#!/usr/bin/env python3
"""
测试 semantic_router.py 的核心功能
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from pathlib import Path
import json

def test_semantic_router_loads():
    """测试语义路由器能否正常加载"""
    from bin.semantic_router import SemanticRouter
    router = SemanticRouter()
    
    assert len(router.tools) > 0, "工具列表不应为空"
    # Embedding 现在是延迟加载，初始化时不加载
    assert router._embeddings_loaded == False, "初始化时不应加载 embedding"
    print(f"✅ 加载成功: {len(router.tools)} 个工具 (延迟加载模式)")

def test_rule_matching():
    """测试规则匹配"""
    from bin.semantic_router import SemanticRouter
    router = SemanticRouter()
    
    # 测试隐身抓取
    match = router.route("隐身抓取小红书页面")
    assert match is not None, "应该匹配到 stealth_get"
    assert match.tool_name == "stealth_get", f"期望 stealth_get，实际 {match.tool_name}"
    print(f"✅ 隐身抓取匹配: {match.tool_name}")
    
    # 测试 GitHub
    match = router.route("查看 GitHub 仓库 torvalds/linux")
    assert match is not None, "应该匹配到 gh_view"
    assert match.tool_name == "gh_view", f"期望 gh_view，实际 {match.tool_name}"
    print(f"✅ GitHub 匹配: {match.tool_name}")

def test_semantic_matching():
    """测试语义匹配"""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("⚠️ 跳过语义匹配测试 (缺少 sentence-transformers)")
        return
    
    from bin.semantic_router import SemanticRouter
    router = SemanticRouter()
    
    # 测试一个不在规则中的查询
    match = router.route("帮我搜索一下 AI Agent 的最新动态")
    assert match is not None, "应该有匹配结果"
    assert match.score >= 0.3, f"相似度应 >= 0.3，实际 {match.score}"
    print(f"✅ 语义匹配: {match.tool_name} (score: {match.score:.3f})")

def test_ai_hints_loaded():
    """测试 ai_hints 是否加载"""
    from bin.semantic_router import SemanticRouter
    router = SemanticRouter()
    
    # 检查是否有 ai_hints
    has_hints = False
    for tool_name, tool_info in router.tools.items():
        if "ai_hints" in tool_info:
            has_hints = True
            break
    
    assert has_hints, "应该有工具包含 ai_hints"
    print(f"✅ ai_hints 已加载")

def test_requires_check():
    """测试 requires 门控检查"""
    from bin.semantic_router import check_requires
    
    # 测试存在的命令
    passed, missing = check_requires({"bins": ["python3"], "env": []})
    assert passed, f"python3 应该存在: missing={missing}"
    print(f"✅ requires 检查通过: python3 存在")
    
    # 测试不存在的命令
    passed, missing = check_requires({"bins": ["nonexistent_cmd_12345"], "env": []})
    assert not passed, "不存在的命令应该失败"
    print(f"✅ requires 检查失败: {missing}")

def main():
    print("=" * 60)
    print("Semantic Router 测试")
    print("=" * 60)
    
    tests = [
        test_semantic_router_loads,
        test_rule_matching,
        test_semantic_matching,
        test_ai_hints_loaded,
        test_requires_check,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
