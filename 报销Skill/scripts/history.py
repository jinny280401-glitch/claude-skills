#!/usr/bin/env python3
"""
报销历史记录管理
"""
import json
import os
from datetime import datetime
from pathlib import Path


HISTORY_FILE = os.path.expanduser("~/.claude/reimbursement_history.json")


def load_history():
    """加载历史记录"""
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"警告：无法加载历史记录：{e}")
        return []


def save_history(history):
    """保存历史记录"""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def add_record(record):
    """
    添加一条报销记录

    Args:
        record: dict, 包含以下字段：
            - date: 报销日期
            - reception_object: 接待对象
            - merchant: 商户名称
            - amount: 金额
            - reception_count: 接待人数
            - accompany_count: 陪餐人数
            - reason: 事由
            - receipt_image: 消费截图路径
            - invoice_pdf: 发票 PDF 路径
            - approval_form: 生成的审批单路径
    """
    history = load_history()

    # 添加记录 ID 和创建时间
    record['id'] = len(history) + 1
    record['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    history.append(record)
    save_history(history)

    return record['id']


def get_record(record_id):
    """获取指定 ID 的记录"""
    history = load_history()
    for record in history:
        if record.get('id') == record_id:
            return record
    return None


def list_records(limit=10):
    """列出最近的记录"""
    history = load_history()
    return history[-limit:]


def search_records(keyword):
    """搜索记录（按接待对象或商户名）"""
    history = load_history()
    results = []

    for record in history:
        if (keyword in record.get('reception_object', '') or
            keyword in record.get('merchant', '')):
            results.append(record)

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python3 history.py <command> [args]")
        print("命令:")
        print("  add <json_data>    - 添加记录")
        print("  get <id>           - 获取记录")
        print("  list [limit]       - 列出最近的记录")
        print("  search <keyword>   - 搜索记录")
        sys.exit(1)

    command = sys.argv[1]

    if command == "add":
        record = json.loads(sys.argv[2])
        record_id = add_record(record)
        print(f"✓ 记录已保存，ID: {record_id}")

    elif command == "get":
        record_id = int(sys.argv[2])
        record = get_record(record_id)
        if record:
            print(json.dumps(record, ensure_ascii=False, indent=2))
        else:
            print(f"✗ 未找到 ID 为 {record_id} 的记录")

    elif command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        records = list_records(limit)
        print(json.dumps(records, ensure_ascii=False, indent=2))

    elif command == "search":
        keyword = sys.argv[2]
        results = search_records(keyword)
        print(json.dumps(results, ensure_ascii=False, indent=2))
