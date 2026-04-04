#!/usr/bin/env python3
"""
代码语法检查工具
支持多种编程语言的语法检查和编译验证
"""

import asyncio
import ast
import subprocess
import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse


class SyntaxChecker:
    """语法检查器类"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.checkers = {
            'python': self._check_python,
            'javascript': self._check_javascript,
            'typescript': self._check_typescript,
            'java': self._check_java,
            'cpp': self._check_cpp,
            'c': self._check_c,
            'go': self._check_go,
            'rust': self._check_rust,
            'html': self._check_html,
            'css': self._check_css,
            'json': self._check_json,
        }

    def detect_language(self, file_path: str) -> str:
        """根据文件扩展名检测编程语言"""
        ext = Path(file_path).suffix.lower().lstrip('.')
        lang_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'java': 'java',
            'cpp': 'cpp',
            'cc': 'cpp',
            'cxx': 'cpp',
            'c': 'c',
            'h': 'c',
            'hpp': 'cpp',
            'go': 'go',
            'rs': 'rust',
            'html': 'html',
            'css': 'css',
            'json': 'json',
        }
        return lang_map.get(ext, 'unknown')

    async def check_file(self, file_path: str) -> Dict:
        """检查单个文件的语法"""
        if not os.path.exists(file_path):
            return {
                'success': False,
                'errors': [{'message': f'文件不存在: {file_path}'}]
            }

        language = self.detect_language(file_path)
        if language == 'unknown':
            return {
                'success': True,
                'message': f'未知语言: {language}，跳过检查'
            }

        if language not in self.checkers:
            return {
                'success': False,
                'errors': [{'message': f'不支持的语言: {language}'}]
            }

        try:
            return await self.checkers[language](file_path)
        except Exception as e:
            return {
                'success': False,
                'errors': [{'message': f'检查出错: {str(e)}'}]
            }

    def _check_python(self, file_path: str) -> Dict:
        """检查 Python 语法"""
        errors = []
        warnings = []

        # 1. AST 解析检查
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            ast.parse(source, filename=file_path)
        except SyntaxError as e:
            errors.append({
                'line': e.lineno,
                'column': e.offset,
                'message': f'SyntaxError: {e.msg}',
                'code': 'E901'
            })
        except Exception as e:
            errors.append({
                'line': 0,
                'column': 0,
                'message': f'解析错误: {str(e)}',
                'code': 'E999'
            })

        # 2. 编译检查
        try:
            subprocess.run(
                ['python', '-m', 'py_compile', file_path],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            if 'SyntaxError' in e.stderr:
                # 已经由 AST 检查捕获
                pass
            else:
                errors.append({
                    'line': 0,
                    'column': 0,
                    'message': f'编译错误: {e.stderr}',
                    'code': 'E902'
                })

        # 3. Flake8 检查（如果安装）
        try:
            result = subprocess.run(
                ['flake8', file_path],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                for line in result.stderr.split('\n'):
                    if line:
                        match = re.match(r'(\d+):(\d+):\s+(.+)', line)
                        if match:
                            warnings.append({
                                'line': int(match.group(1)),
                                'column': int(match.group(2)),
                                'message': match.group(3),
                                'code': 'W501'
                            })
        except FileNotFoundError:
            pass  # flake8 未安装

        return {
            'success': len(errors) == 0,
            'language': 'python',
            'file': file_path,
            'errors': errors,
            'warnings': warnings
        }

    def _check_javascript(self, file_path: str) -> Dict:
        """检查 JavaScript 语法"""
        errors = []

        try:
            subprocess.run(
                ['node', '-c', file_path],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            # 解析 Node.js 错误信息
            error_lines = e.stderr.split('\n')
            for line in error_lines:
                if '(' in line and ')' in line:
                    # 提取错误信息
                    match = re.search(r'(\d+):(\d+)\s*:\s*(.+)', line)
                    if match:
                        errors.append({
                            'line': int(match.group(1)),
                            'column': int(match.group(2)),
                            'message': match.group(3),
                            'code': 'E901'
                        })

        return {
            'success': len(errors) == 0,
            'language': 'javascript',
            'file': file_path,
            'errors': errors,
            'warnings': []
        }

    def _check_typescript(self, file_path: str) -> Dict:
        """检查 TypeScript 语法"""
        errors = []

        try:
            subprocess.run(
                ['tsc', '--noEmit', file_path],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            # 解析 TypeScript 错误信息
            for line in e.stderr.split('\n'):
                if line.strip() and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        errors.append({
                            'line': 0,
                            'column': 0,
                            'message': line.strip(),
                            'code': 'E901'
                        })

        return {
            'success': len(errors) == 0,
            'language': 'typescript',
            'file': file_path,
            'errors': errors,
            'warnings': []
        }

    def _check_java(self, file_path: str) -> Dict:
        """检查 Java 语法"""
        errors = []

        try:
            # 首先找到文件名（不含扩展名）
            class_name = Path(file_path).stem
            result = subprocess.run(
                ['javac', file_path],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            # 解析 Java 编译错误
            for line in e.stderr.split('\n'):
                if ':' in line and ('.java:' in line or '.java:' in line):
                    # 解析错误行
                    match = re.search(r'(\w+\.java):(\d+):', line)
                    if match:
                        errors.append({
                            'line': int(match.group(2)),
                            'column': 0,
                            'message': line.strip(),
                            'code': 'E901'
                        })

        return {
            'success': len(errors) == 0,
            'language': 'java',
            'file': file_path,
            'errors': errors,
            'warnings': []
        }

    def _check_cpp(self, file_path: str) -> Dict:
        """检查 C++ 语法"""
        errors = []

        # 尝试使用 g++
        try:
            subprocess.run(
                ['g++', '-fsyntax-only', '-std=c++11', file_path],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError:
            # 尝试 clang++
            try:
                subprocess.run(
                    ['clang++', '-fsyntax-only', '-std=c++11', file_path],
                    check=True,
                    capture_output=True,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                # 解析错误信息
                for line in e.stderr.split('\n'):
                    if 'error:' in line or 'note:' in line:
                        # 提取错误位置
                        match = re.search(r'(\w+\.(cpp|cc|h)):(\d+):', line)
                        if match:
                            errors.append({
                                'line': int(match.group(3)),
                                'column': 0,
                                'message': line.strip(),
                                'code': 'E901'
                            })

        return {
            'success': len(errors) == 0,
            'language': 'cpp',
            'file': file_path,
            'errors': errors,
            'warnings': []
        }

    def _check_c(self, file_path: str) -> Dict:
        """检查 C 语法"""
        errors = []

        try:
            subprocess.run(
                ['gcc', '-fsyntax-only', file_path],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            # 解析错误信息
            for line in e.stderr.split('\n'):
                if 'error:' in line:
                    match = re.search(r'(\w+\.c):(\d+):', line)
                    if match:
                        errors.append({
                            'line': int(match.group(2)),
                            'column': 0,
                            'message': line.strip(),
                            'code': 'E901'
                        })

        return {
            'success': len(errors) == 0,
            'language': 'c',
            'file': file_path,
            'errors': errors,
            'warnings': []
        }

    def _check_go(self, file_path: str) -> Dict:
        """检查 Go 语法"""
        errors = []

        try:
            subprocess.run(
                ['go', 'build', '-o', '/dev/null', file_path],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            # 解析错误信息
            for line in e.stderr.split('\n'):
                if '.go:' in line:
                    match = re.search(r'(\w+\.go):(\d+):', line)
                    if match:
                        errors.append({
                            'line': int(match.group(2)),
                            'column': 0,
                            'message': line.strip(),
                            'code': 'E901'
                        })

        return {
            'success': len(errors) == 0,
            'language': 'go',
            'file': file_path,
            'errors': errors,
            'warnings': []
        }

    def _check_rust(self, file_path: str) -> Dict:
        """检查 Rust 语法"""
        errors = []

        try:
            subprocess.run(
                ['rustc', '--check', file_path],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            # 解析错误信息
            for line in e.stderr.split('\n'):
                if '.rs:' in line:
                    match = re.search(r'(\w+\.rs):(\d+):', line)
                    if match:
                        errors.append({
                            'line': int(match.group(2)),
                            'column': 0,
                            'message': line.strip(),
                            'code': 'E901'
                        })

        return {
            'success': len(errors) == 0,
            'language': 'rust',
            'file': file_path,
            'errors': errors,
            'warnings': []
        }

    def _check_html(self, file_path: str) -> Dict:
        """检查 HTML 语法"""
        # HTML 语法检查较为复杂，这里简化处理
        # 实际项目中可以使用 html5validator 或类似工具
        errors = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # 基本检查：标签是否闭合
                stack = []
                for i, char in enumerate(content):
                    if char == '<' and i + 1 < len(content):
                        # 开始标签
                        if content[i+1] != '/':
                            end = content.find('>', i)
                            if end != -1:
                                tag = content[i+1:end].split()[0]
                                stack.append(tag)
                        # 结束标签
                        elif content[i+1:i+2] == '/':
                            end = content.find('>', i)
                            if end != -1:
                                tag = content[i+2:end].split()[0]
                                if stack and stack[-1] == tag:
                                    stack.pop()
                                else:
                                    errors.append({
                                        'line': content[:i].count('\n') + 1,
                                        'column': 0,
                                        'message': f'未闭合标签: {tag}',
                                        'code': 'E901'
                                    })

            if stack:
                errors.append({
                    'line': 0,
                    'column': 0,
                    'message': f'未闭合标签: {stack[-1]}',
                    'code': 'E902'
                })
        except Exception as e:
            errors.append({
                'line': 0,
                'column': 0,
                'message': f'解析错误: {str(e)}',
                'code': 'E999'
            })

        return {
            'success': len(errors) == 0,
            'language': 'html',
            'file': file_path,
            'errors': errors,
            'warnings': []
        }

    def _check_css(self, file_path: str) -> Dict:
        """检查 CSS 语法"""
        # CSS 语法检查较为复杂，这里简化处理
        errors = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # 基本检查：花括号是否匹配
                stack = []
                for i, char in enumerate(content):
                    if char == '{':
                        stack.append(i)
                    elif char == '}':
                        if not stack:
                            errors.append({
                                'line': content[:i].count('\n') + 1,
                                'column': 0,
                                'message': '未匹配的 }',
                                'code': 'E901'
                            })
                        else:
                            stack.pop()

                if stack:
                    errors.append({
                        'line': content[:stack[0]].count('\n') + 1,
                        'column': 0,
                        'message': '未匹配的 {',
                        'code': 'E902'
                    })
        except Exception as e:
            errors.append({
                'line': 0,
                'column': 0,
                'message': f'解析错误: {str(e)}',
                'code': 'E999'
            })

        return {
            'success': len(errors) == 0,
            'language': 'css',
            'file': file_path,
            'errors': errors,
            'warnings': []
        }

    def _check_json(self, file_path: str) -> Dict:
        """检查 JSON 语法"""
        errors = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            errors.append({
                'line': e.lineno,
                'column': e.colno,
                'message': f'JSON 解析错误: {e.msg}',
                'code': 'E901'
            })

        return {
            'success': len(errors) == 0,
            'language': 'json',
            'file': file_path,
            'errors': errors,
            'warnings': []
        }


async def check_project(directory: str = '.', recursive: bool = True) -> List[Dict]:
    """检查项目中的所有代码文件"""
    checker = SyntaxChecker()
    results = []

    # 查找代码文件
    if recursive:
        code_files = []
        for root, dirs, files in os.walk(directory):
            # 排除常见目录
            dirs[:] = [d for d in dirs if d not in ['node_modules', 'venv', '__pycache__', '.git']]

            for file in files:
                ext = Path(file).suffix.lower()
                if ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.cc', '.cxx', '.go', '.rs', '.html', '.css', '.json']:
                    code_files.append(os.path.join(root, file))
    else:
        code_files = [f for f in os.listdir(directory) if os.path.isfile(f)]

    # 并发检查所有文件
    tasks = [checker.check_file(f) for f in code_files]
    results = await asyncio.gather(*tasks)

    return results


def print_report(results: List[Dict], format_type: str = 'text'):
    """打印检查报告"""
    if format_type == 'json':
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    # 文本格式
    total_files = len(results)
    passed_files = sum(1 for r in results if r['success'])
    failed_files = total_files - passed_files
    total_errors = sum(len(r.get('errors', [])) for r in results)
    total_warnings = sum(len(r.get('warnings', [])) for r in results)

    print("=" * 60)
    print(f"代码语法检查报告")
    print("=" * 60)
    print(f"总文件数: {total_files}")
    print(f"通过: {passed_files} ✅")
    print(f"失败: {failed_files} ❌")
    print(f"错误: {total_errors} 🔴")
    print(f"警告: {total_warnings} 🟡")
    print("=" * 60)

    # 详细结果
    for result in results:
        if not result['success'] or result.get('errors') or result.get('warnings'):
            print(f"\n📄 {result['file']} ({result.get('language', 'unknown')})")

            if result.get('errors'):
                print("❌ 错误:")
                for error in result['errors']:
                    print(f"   行 {error['line']}: {error['message']}")

            if result.get('warnings'):
                print("⚠️ 警告:")
                for warning in result['warnings']:
                    print(f"   行 {warning['line']}: {warning['message']}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='代码语法检查工具')
    parser.add_argument('files', nargs='*', help='要检查的文件或目录')
    parser.add_argument('--dir', '-d', default='.', help='检查目录（默认当前目录）')
    parser.add_argument('--recursive', '-r', action='store_true', help='递归检查子目录')
    parser.add_argument('--json', action='store_true', help='JSON 输出格式')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    if not args.files and not args.dir:
        args.dir = '.'

    # 确定要检查的路径
    if args.files:
        paths = args.files
    else:
        paths = [args.dir]

    # 检查所有路径
    all_results = []
    for path in paths:
        if os.path.isfile(path):
            checker = SyntaxChecker()
            result = await checker.check_file(path)
            all_results.append(result)
        elif os.path.isdir(path):
            results = await check_project(path, args.recursive)
            all_results.extend(results)

    # 打印报告
    print_report(all_results, 'json' if args.json else 'text')

    # 返回非零退出码表示有错误
    exit_code = 0 if all(r['success'] for r in all_results) else 1
    exit(exit_code)


if __name__ == '__main__':
    asyncio.run(main())