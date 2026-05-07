#!/usr/bin/env python3
"""
报销数据验证脚本
"""
from difflib import SequenceMatcher
import sys
import json


def validate_merchant_match(receipt_merchant, invoice_merchant, threshold=0.6):
    """
    验证商户名称是否一致

    Args:
        receipt_merchant: 消费截图中的商户名
        invoice_merchant: 发票中的开票商户名
        threshold: 相似度阈值（默认 0.6）

    Returns:
        dict: {
            "match": bool,
            "similarity": float,
            "clean_receipt": str,
            "clean_invoice": str
        }
    """
    # 清洗规则：去除常见后缀
    stopwords = ['有限公司', '餐饮管理', '股份', '分公司', '营业部',
                 '福州市', '鼓楼区', '台江区', '仓山区', '晋安区', '马尾区']

    clean1 = receipt_merchant
    clean2 = invoice_merchant

    for word in stopwords:
        clean1 = clean1.replace(word, '')
        clean2 = clean2.replace(word, '')

    # 计算相似度
    ratio = SequenceMatcher(None, clean1, clean2).ratio()

    return {
        "match": ratio >= threshold,
        "similarity": round(ratio, 2),
        "clean_receipt": clean1,
        "clean_invoice": clean2
    }


def validate_amount(receipt_amount, invoice_total, tolerance=0.5):
    """
    验证金额是否一致

    Args:
        receipt_amount: 消费截图中的金额
        invoice_total: 发票中的价税合计
        tolerance: 允许的误差（默认 0.5 元）

    Returns:
        dict: {
            "match": bool,
            "difference": float
        }
    """
    diff = abs(receipt_amount - invoice_total)

    return {
        "match": diff <= tolerance,
        "difference": round(diff, 2)
    }


def validate_per_capita(total_amount, reception_count, accompany_count, limit=600):
    """
    验证人均费用是否合规

    Args:
        total_amount: 总金额
        reception_count: 接待人数
        accompany_count: 陪餐人数
        limit: 人均费用限额（默认 600 元）

    Returns:
        dict: {
            "compliant": bool,
            "per_capita": float,
            "limit": int,
            "over_limit": float
        }
    """
    total_people = reception_count + accompany_count
    if total_people == 0:
        return {
            "compliant": False,
            "per_capita": 0,
            "limit": limit,
            "over_limit": 0,
            "error": "接待人数和陪餐人数不能都为 0"
        }

    per_capita = total_amount / total_people

    return {
        "compliant": per_capita <= limit,
        "per_capita": round(per_capita, 2),
        "limit": limit,
        "over_limit": round(max(0, per_capita - limit), 2)
    }


if __name__ == "__main__":
    # 命令行接口
    if len(sys.argv) < 2:
        print("用法: python3 validate.py <json_data>")
        sys.exit(1)

    data = json.loads(sys.argv[1])

    # 商户名称验证
    if "receipt_merchant" in data and "invoice_merchant" in data:
        merchant_result = validate_merchant_match(
            data["receipt_merchant"],
            data["invoice_merchant"]
        )
        print(json.dumps(merchant_result, ensure_ascii=False, indent=2))

    # 金额验证
    if "receipt_amount" in data and "invoice_total" in data:
        amount_result = validate_amount(
            data["receipt_amount"],
            data["invoice_total"]
        )
        print(json.dumps(amount_result, ensure_ascii=False, indent=2))

    # 人均费用验证
    if all(k in data for k in ["total_amount", "reception_count", "accompany_count"]):
        per_capita_result = validate_per_capita(
            data["total_amount"],
            data["reception_count"],
            data["accompany_count"]
        )
        print(json.dumps(per_capita_result, ensure_ascii=False, indent=2))
