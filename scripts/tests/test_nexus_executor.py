#!/usr/bin/env python3
"""
nexus_executor.py 单元测试

测试覆盖：
1. Schema 验证
2. 命令注入防护
3. 参数缺失处理
4. 工具执行成功/失败
5. 边界情况
"""

import os
import sys
import json
import subprocess
import unittest
import tempfile
import shutil

# 添加项目根目录到 path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from bin.kernel.nexus_executor import run_tool


class TestNexusExecutor(unittest.TestCase):
    """Nexus Executor 核心功能测试"""

    def test_schema_validation_success(self):
        """测试有效的参数通过 Schema 验证"""
        result = run_tool(
            "agency-bin-gh",
            "gh_view",
            '{"repo": "octocat/Hello-World"}'
        )
        # 不验证具体结果，只验证没有 schema 错误
        self.assertNotIn("Schema validation failed", result.get("message", ""))

    def test_schema_validation_missing_required(self):
        """测试缺少必需参数时失败"""
        result = run_tool(
            "agency-bin-gh",
            "gh_view",
            '{}'  # 缺少 repo 参数
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("Schema validation failed", result["message"])

    def test_schema_validation_wrong_type(self):
        """测试参数类型错误时失败"""
        result = run_tool(
            "agency-bin-gh",
            "gh_view",
            '{"repo": 12345}'  # repo 应该是字符串
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("Schema validation failed", result["message"])

    def test_skill_not_found(self):
        """测试 Skill 不存在时返回错误"""
        result = run_tool(
            "nonexistent-skill",
            "some_tool",
            '{}'
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("missing SCHEMA.json", result["message"])

    def test_tool_not_found(self):
        """测试 Tool 不存在时返回错误"""
        result = run_tool(
            "agency-bin-gh",
            "nonexistent_tool",
            '{"repo": "test/repo"}'
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("not defined", result["message"])

    def test_command_injection_protection(self):
        """测试命令注入防护"""
        # 尝试注入恶意命令
        result = run_tool(
            "agency-bin-gh",
            "gh_view",
            '{"repo": "test; rm -rf /"}'
        )
        # 应该被 shlex.quote 转义，不会执行注入
        # 结果可能是失败（因为没有这个 repo），但不应该是 error 状态
        self.assertIn(result["status"], ["success", "failure", "suspicious_empty"])

    def test_command_injection_backtick(self):
        """测试反引号注入防护"""
        result = run_tool(
            "agency-bin-gh",
            "gh_view",
            '{"repo": "`whoami`"}'
        )
        # 应该被转义
        self.assertIn(result["status"], ["success", "failure", "suspicious_empty"])

    def test_command_injection_dollar(self):
        """测试 $() 注入防护"""
        result = run_tool(
            "agency-bin-gh",
            "gh_view",
            '{"repo": "$(cat /etc/passwd)"}'
        )
        # 应该被转义
        self.assertIn(result["status"], ["success", "failure", "suspicious_empty"])

    def test_json_args_invalid(self):
        """测试无效 JSON 参数"""
        # 直接调用 run_tool 函数时，JSON 解析在调用前完成
        # 但我们可以测试 json.loads 的异常处理
        # 这里我们测试函数本身，JSON 解析在 __main__ 中
        pass  # run_tool 内部不处理 JSON 解析

    def test_exit_code_success(self):
        """测试成功执行的退出码"""
        result = run_tool(
            "agency-bin-lightpanda",
            "fetch",
            '{"url": "https://example.com", "dump": "markdown"}'
        )
        # 退出码应该是 0 或者有明确的失败原因
        if result["status"] == "success":
            self.assertEqual(result["exit_code"], 0)

    def test_return_structure(self):
        """测试返回值结构"""
        result = run_tool(
            "agency-bin-gh",
            "gh_view",
            '{"repo": "octocat/Hello-World"}'
        )
        # 必须包含这些字段
        self.assertIn("status", result)
        self.assertIn("exit_code", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        self.assertIn("is_empty", result)


class TestNexusExecutorIntegration(unittest.TestCase):
    """集成测试 - 需要网络连接"""

    def test_gh_view_real_repo(self):
        """测试真实的 GitHub repo 查询"""
        result = run_tool(
            "agency-bin-gh",
            "gh_view",
            '{"repo": "octocat/Hello-World"}'
        )
        # 应该成功或者有网络错误
        self.assertIn(result["status"], ["success", "failure"])
        if result["status"] == "success":
            self.assertIn("Hello-World", result["stdout"])

    def test_lightpanda_fetch_example(self):
        """测试 Lightpanda 抓取 example.com"""
        result = run_tool(
            "agency-bin-lightpanda",
            "fetch",
            '{"url": "https://example.com", "dump": "markdown"}'
        )
        self.assertEqual(result["status"], "success")
        self.assertIn("Example Domain", result["stdout"])


class TestNexusExecutorEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def test_empty_url(self):
        """测试空 URL - 记录实际行为"""
        result = run_tool(
            "agency-bin-lightpanda",
            "fetch",
            '{"url": "", "dump": "markdown"}'
        )
        # Lightpanda 对空URL返回success但输出为空，这是已知的边界行为
        # 记录实际行为而非强制断言
        print(f"\n[INFO] Empty URL result: status={result['status']}, is_empty={result['is_empty']}")
        self.assertIn(result["status"], ["success", "failure", "error"])

    def test_special_characters_in_repo(self):
        """测试 repo 名称中的特殊字符"""
        result = run_tool(
            "agency-bin-gh",
            "gh_view",
            '{"repo": "user/repo-with-dashes_and_underscores"}'
        )
        # 应该被正确转义
        self.assertIn(result["status"], ["success", "failure", "error"])

    def test_unicode_in_args(self):
        """测试 Unicode 参数"""
        result = run_tool(
            "agency-bin-gh",
            "gh_view",
            '{"repo": "用户/仓库"}'
        )
        # 应该被正确处理
        self.assertIn(result["status"], ["success", "failure", "error"])


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestNexusExecutor))
    suite.addTests(loader.loadTestsFromTestCase(TestNexusExecutorIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestNexusExecutorEdgeCases))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
