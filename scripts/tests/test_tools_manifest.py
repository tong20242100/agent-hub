#!/usr/bin/env python3
"""
测试 tools_manifest.json 生成
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from pathlib import Path
import json

def test_manifest_exists():
    """测试 manifest 文件存在"""
    manifest_path = Path("knowledge/tools_manifest.json")
    assert manifest_path.exists(), "tools_manifest.json 应该存在"
    print(f"✅ manifest 文件存在")

def test_manifest_structure():
    """测试 manifest 结构"""
    with open("knowledge/tools_manifest.json") as f:
        manifest = json.load(f)
    
    assert "version" in manifest, "应有 version 字段"
    assert "tools" in manifest, "应有 tools 字段"
    assert "total_tools" in manifest, "应有 total_tools 字段"
    assert manifest["total_tools"] == len(manifest["tools"]), "total_tools 应等于 tools 长度"
    print(f"✅ manifest 结构正确: {manifest['total_tools']} 个工具")

def test_tool_has_required_fields():
    """测试工具包含必需字段"""
    with open("knowledge/tools_manifest.json") as f:
        manifest = json.load(f)
    
    required_fields = ["name", "skill", "skill_dir", "description"]
    
    for tool in manifest["tools"][:5]:  # 测试前 5 个
        for field in required_fields:
            assert field in tool, f"工具 {tool.get('name', '?')} 缺少 {field}"
    
    print(f"✅ 工具包含必需字段")

def test_ai_hints_in_manifest():
    """测试 ai_hints 在 manifest 中"""
    with open("knowledge/tools_manifest.json") as f:
        manifest = json.load(f)
    
    has_hints = sum(1 for t in manifest["tools"] if "ai_hints" in t)
    print(f"✅ {has_hints}/{manifest['total_tools']} 个工具有 ai_hints")

def main():
    print("=" * 60)
    print("Tools Manifest 测试")
    print("=" * 60)
    
    tests = [
        test_manifest_exists,
        test_manifest_structure,
        test_tool_has_required_fields,
        test_ai_hints_in_manifest,
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
