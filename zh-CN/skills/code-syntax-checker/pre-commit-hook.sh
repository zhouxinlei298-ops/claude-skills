#!/bin/bash
# Git pre-commit hook: 代码语法检查
# 放置在 .git/hooks/pre-commit

echo "🔍 执行代码语法检查..."

# 获取暂存的文件
staged_files=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|js|ts|java|cpp|c|go|rs|html|css|json)$')

if [ -z "$staged_files" ]; then
    echo "✅ 没有待检查的代码文件"
    exit 0
fi

# 语法检查脚本路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK_SCRIPT="$SCRIPT_DIR/check_syntax.py"

# 检查是否存在语法检查脚本
if [ ! -f "$CHECK_SCRIPT" ]; then
    echo "⚠️  语法检查脚本不存在: $CHECK_SCRIPT"
    exit 0
fi

# 创建临时文件列表
temp_file=$(mktemp)

# 将文件写入临时文件
echo "$staged_files" > "$temp_file"

# 执行语法检查
echo "📁 检查文件:"
echo "$staged_files"
echo ""

# 运行检查
python3 "$CHECK_SCRIPT" --json $(cat "$temp_file") > /tmp/syntax_check_result.json 2>&1

# 获取检查结果
result=$(cat /tmp/syntax_check_result.json)

# 检查是否有错误
if echo "$result" | grep -q '"success": false'; then
    echo "❌ 代码语法检查失败！"
    echo ""

    # 提取错误信息
    echo "🔴 错误详情:"
    echo "$result" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data:
    if not item.get('success', True):
        file = item.get('file', 'unknown')
        errors = item.get('errors', [])
        if errors:
            print(f'  📄 {file}')
            for error in errors[:3]:  # 只显示前3个错误
                print(f'      行 {error.get(\"line\", 0)}: {error.get(\"message\", \"未知错误\")}')
        else:
            print(f'  📄 {file}: 未知错误')
"

    echo ""
    echo "请修复语法错误后重新提交。"
    echo "💡 使用提示: python3 $(realpath "$CHECK_SCRIPT") --help 查看帮助"

    # 清理临时文件
    rm -f "$temp_file"
    rm -f /tmp/syntax_check_result.json

    exit 1
fi

# 检查是否有警告（如果有警告但仍检查通过）
warnings=$(echo "$result" | python3 -c "
import sys, json
data = json.load(sys.stdin)
total_warnings = sum(len(item.get('warnings', [])) for item in data)
print(total_warnings)
")

if [ "$warnings" -gt 0 ]; then
    echo "⚠️  代码语法检查通过，但存在警告:"
    echo "$result" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data:
    warnings = item.get('warnings', [])
    if warnings:
        file = item.get('file', 'unknown')
        print(f'  📄 {file}')
        for warning in warnings[:2]:  # 只显示前2个警告
            print(f'      行 {warning.get(\"line\", 0)}: {warning.get(\"message\", \"未知警告\")}')
"
fi

echo "✅ 代码语法检查通过！"

# 清理临时文件
rm -f "$temp_file"
rm -f /tmp/syntax_check_result.json

exit 0