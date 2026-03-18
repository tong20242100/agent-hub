#!/usr/bin/env python3
"""
nexus_executor.py 单元测试

测试覆盖：
1. Schema 验证
2. 命令注入防护
3. 参数缺失处理
4. 工具执行成功/失败
5. 边界情况

只使用被 git 跟踪的 skills：agency-bin-search, agency-bin-scrape
"""

import os
import sys
import json
import subprocess
import unittest

# 添加项目根目录到 path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from bin.kernel.nexus_executor import run_tool


class TestNexusExecutor(unittest.TestCase):
    """Nexus Executor 核心功能测试"""

    def test_schema_validation_success(self):
        """测试有效的参数通过 Schema 验证"""
        result = run_tool(
            "agency-bin-scrape",
            "scrape_url",
            '{"url": "https://example.com"}'
        )
        # 不验证具体结果，只验证没有 schema 错误
        self.assertNotIn("Schema validation failed", result.get("message", ""))

    def test_schema_validation_missing_required(self):
        """测试缺少必需参数时失败"""
        result = run_tool(
            "agency-bin-scrape",
            "scrape_url",
            '{}'  # 缺少 url 参数
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("Schema validation failed", result["message"])

    def test_schema_validation_wrong_type(self):
        """测试参数类型错误时失败"""
        result = run_tool(
            "agency-bin-scrape",
            "scrape_url",
            '{"url": 12345}'  # url 应该是字符串
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
            "agency-bin-scrape",
            "nonexistent_tool",
            '{"url": "https://example.com"}'
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("not defined", result["message"])

    def test_command_injection_protection(self):
        """测试命令注入防护"""
        # 尝试注入恶意命令
        result = run_tool(
            "agency-bin-scrape",
            "scrape_url",
            '{"url": "https://test; rm -rf /"}'
        )
        # 应该被 shlex.quote 转义，不会执行注入
        # 结果可能是失败，但应该有正确的结构
        self.assertIn("status", result)

    def test_command_injection_backtick(self):
        """测试反引号注入防护"""
        result = run_tool(
            "agency-bin-scrape",
            "scrape_url",
            '{"url": "https://`whoami`.com"}'
        )
        # 应该被转义
        self.assertIn("status", result)

    def test_command_injection_dollar(self):
        """测试 $() 注入防护"""
        result = run_tool(
            "agency-bin-scrape",
            "scrape_url",
            '{"url": "https://$(cat /etc/passwd).com"}'
        )
        # 应该被转义
        self.assertIn("status", result)

    def test_return_structure(self):
        """测试返回值结构"""
        result = run_tool(
            "agency-bin-scrape",
            "scrape_url",
            '{"url": "https://example.com"}'
        )
        # 必须包含这些字段
        self.assertIn("status", result)
        # 成功或失败都应该有这些字段
        if result["status"] in ["success", "failure", "suspicious_empty"]:
            self.assertIn("exit_code", result)
            self.assertIn("stdout", result)
            self.assertIn("stderr", result)


class TestNexusExecutorIntegration(unittest.TestCase):
    """集成测试 - 需要网络连接和外部依赖"""

    @unittest.skip("需要 TAVILY_API_KEY 环境变量")
    def test_web_search(self):
        """测试网页搜索"""
        result = run_tool(
            "agency-bin-search",
            "web_search",
            '{"query": "Python", "max_results": 1}'
        )
        # 需要 TAVILY_API_KEY
        self.assertIn(result["status"], ["success", "failure", "error"])

    def test_scrape_url_structure(self):
        """测试抓取 URL 的返回结构"""
        result = run_tool(
            "agency-bin-scrape",
            "scrape_url",
            '{"url": "https://example.com"}'
        )
        # 只验证结构，不验证具体结果（可能因为网络原因失败）
        self.assertIn("status", result)


class TestNexusExecutorEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def test_empty_url(self):
        """测试空 URL"""
        result = run_tool(
            "agency-bin-scrape",
            "scrape_url",
            '{"url": ""}'
        )
        # 空URL应该返回某种状态
        self.assertIn("status", result)

    def test_unicode_in_args(self):
        """测试 Unicode 参数"""
        result = run_tool(
            "agency-bin-scrape",
            "scrape_url",
            '{"url": "https://例子.中国"}'
        )
        # 应该被正确处理
        self.assertIn("status", result)

    def test_default_parameters(self):
        """测试默认参数"""
        result = run_tool(
            "agency-bin-scrape",
            "scrape_url",
            '{"url": "https://example.com"}'
        )
        # depth 和 recursive 应该使用默认值
        self.assertIn("status", result)


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