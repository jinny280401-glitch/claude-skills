#!/usr/bin/env python3
"""
填充接待审批单 Word 文档（只填写上半部分 - 事前审批）
"""
from docx import Document
import sys
import json
from datetime import datetime


def fill_approval_form(template_path, output_path, data):
    """
    填充审批单（只填写事前审批部分）

    Args:
        template_path: 模板 Word 文档路径
        output_path: 输出 Word 文档路径
        data: dict, 包含以下字段：
            - send_date: 送审时间（如 "YYYY.M.D"）
            - reception_object: 接待对象（如 "客户A等"）
            - reception_date: 接待时间（如 "YYYY.M.D"）
            - reason: 事由（拓展客户/维护客户/商业合作/其他）
            - reception_count: 接待人数
            - accompany_count: 陪餐人数
            - per_capita: 人均费用
            - budget_total: 预算总额
    """
    try:
        doc = Document(template_path)
        table = doc.tables[0]

        # 事前审批部分
        # 第1行：承办部门（模板中已预填），送审时间
        table.rows[1].cells[6].text = data.get("send_date", "")

        # 第2行：接待对象、接待时间
        table.rows[2].cells[1].text = data.get("reception_object", "")
        table.rows[2].cells[6].text = data.get("reception_date", "")

        # 第3行：事由（修改复选框）
        reason = data.get("reason", "维护客户")
        reason_map = {
            "拓展客户": "☑拓展客户  □维护客户  □商业合作  □其他",
            "维护客户": "□拓展客户  ☑维护客户  □商业合作  □其他",
            "商业合作": "□拓展客户  □维护客户  ☑商业合作  □其他",
            "其他": "□拓展客户  □维护客户  □商业合作  ☑其他"
        }
        table.rows[3].cells[1].text = reason_map.get(reason, reason_map["维护客户"])

        # 第5行：商务宴请预算（接待人数、陪餐人数、人均费用、预算总额）
        table.rows[5].cells[1].text = str(data.get("reception_count", ""))
        table.rows[5].cells[2].text = str(data.get("accompany_count", ""))
        table.rows[5].cells[3].text = str(data.get("per_capita", ""))
        table.rows[5].cells[4].text = str(data.get("budget_total", ""))

        # 保存文档
        doc.save(output_path)
        return True, f"✓ 审批单已生成：{output_path}"

    except Exception as e:
        return False, f"✗ 填表失败：{str(e)}"


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: python3 fill_approval_form.py <template_path> <output_path> <json_data>")
        sys.exit(1)

    template_path = sys.argv[1]
    output_path = sys.argv[2]
    data = json.loads(sys.argv[3])

    success, message = fill_approval_form(template_path, output_path, data)
    print(message)
    sys.exit(0 if success else 1)
