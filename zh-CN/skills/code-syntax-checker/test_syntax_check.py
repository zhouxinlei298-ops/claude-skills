#!/usr/bin/env python3
"""
测试代码语法检查功能
"""

import asyncio
import os
from check_syntax import SyntaxChecker

async def test_basic_syntax_check():
    """基本语法检查测试"""
    print("🧪 测试基本语法检查...")

    # 创建测试代码文件
    test_files = [
        {
            'name': 'test_valid.py',
            'content': '''def hello():
    """测试函数"""
    print("Hello, World!")

hello()
''',
            'expected_success': True
        },
        {
            'name': 'test_invalid.py',
            'content': '''def hello()
    """测试函数"""
    print("Hello, World!"

hello()
''',
            'expected_success': False
        },
        {
            'name': 'test_valid.js',
            'content': '''function hello() {
    console.log("Hello, World!");
}

hello();
''',
            'expected_success': True
        },
        {
            'name': 'test_invalid.js',
            'content': '''function hello() {
    console.log("Hello, World!"
}

hello();
''',
            'expected_success': False
        }
    ]

    checker = SyntaxChecker()

    # 创建临时目录
    os.makedirs('temp_test', exist_ok=True)

    try:
        for test_file in test_files:
            file_path = f'temp_test/{test_file["name"]}'

            # 写入测试文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(test_file['content'])

            print(f"\n📄 检查文件: {file_path}")
            result = await checker.check_file(file_path)

            print(f"  预期结果: {'成功' if test_file['expected_success'] else '失败'}")
            print(f"  实际结果: {'成功' if result['success'] else '失败'}")
            print(f"  检查结果: {'✅ 通过' if result['success'] == test_file['expected_success'] else '❌ 失败'}")

            # 显示错误信息
            if not result['success'] and result.get('errors'):
                print("  错误信息:")
                for error in result['errors']:
                    print(f"    行 {error['line']}: {error['message']}")

        print("\n✅ 所有测试完成！")

    finally:
        # 清理临时文件
        import shutil
        shutil.rmtree('temp_test', ignore_errors=True)

async def test_project_check():
    """项目检查测试"""
    print("\n🧪 测试项目检查...")

    # 模拟项目目录
    os.makedirs('temp_project/src', exist_ok=True)
    os.makedirs('temp_project/tests', exist_ok=True)

    # 创建项目文件
    project_files = [
        {
            'path': 'temp_project/src/main.py',
            'content': '''import sys

def main():
    print("Hello from main function")

if __name__ == "__main__":
    main()
''',
            'should_pass': True
        },
        {
            'path': 'temp_project/src/utils.py',
            'content': '''def add(a, b):
    """加法函数"""
    return a + b

def multiply(a, b):
    """乘法函数"""
    return a * b
''',
            'should_pass': True
        },
        {
            'path': 'temp_project/tests/test_main.py',
            'content': '''import unittest
from src.main import main

class TestMain(unittest.TestCase):
    def test_main(self):
        # 这里应该测试 main 函数
        pass
''',
            'should_pass': True
        }
    ]

    # 写入文件
    for file_info in project_files:
        os.makedirs(os.path.dirname(file_info['path']), exist_ok=True)
        with open(file_info['path'], 'w', encoding='utf-8') as f:
            f.write(file_info['content'])

    # 执行项目检查
    checker = SyntaxChecker()
    results = await check_project('temp_project')

    print(f"\n📊 项目检查结果:")
    print(f"  文件总数: {len(results)}")
    print(f"  通过检查: {sum(1 for r in results if r['success'])}")
    print(f"  有错误: {sum(1 for r in results if not r['success'])}")

    # 显示详细结果
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"  {status} {result['file']}")

        if not result['success']:
            for error in result.get('errors', []):
                print(f"    错误: {error['message']}")

    # 清理
    import shutil
    shutil.rmtree('temp_project', ignore_errors=True)

if __name__ == '__main__':
    asyncio.run(test_basic_syntax_check())
    asyncio.run(test_project_check())