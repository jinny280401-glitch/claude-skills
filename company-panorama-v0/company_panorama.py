#!/usr/bin/env python3
"""
Company Panorama v0: 3分钟生成客户拜访准备卡

Architecture:
1. Resolve Company
2. Collect Evidence from Choice API
3. Trust Gate Filter
4. LLM Generate Visit Card
5. Post-QC Blocked Claim Scan

Trust Gate is HARD GATE: must run before LLM Prompt.
"""

import os
import sys
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class EvidenceLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    UNKNOWN = "UNKNOWN"


class RiskSignalStatus(str, Enum):
    SIGNAL_PRESENT = "signal_present"
    SIGNAL_ABSENT = "signal_absent"
    UNKNOWN = "unknown"
    REQUIRES_MANUAL_CHECK = "requires_manual_check"


class TrustGate:
    """
    Trust Gate: Evidence filtering before LLM.

    HARD GATE: All evidence must pass through Trust Gate before entering LLM Prompt.
    """

    # Source ranking rules
    HIGH_SOURCES = [
        "官方公告", "年报", "招股书", "监管披露", "工商登记",
        "法院文书", "仲裁文书", "上市公司公告", "证监会文件"
    ]

    MEDIUM_SOURCES = [
        "主流财经媒体", "券商研报", "招投标", "招聘信息",
        "公司官网", "公开业务资料", "行业报告"
    ]

    LOW_SOURCES = [
        "自媒体", "论坛", "二手转述", "未标注来源", "估算数据"
    ]

    # Blocked fields that should never enter LLM
    BLOCKED_FIELDS = [
        "valuation", "rating", "buy_sell_hold", "position_sizing",
        "private_company_revenue_profit_without_audit",
        "definitive_legal_liability", "definitive_credit_conclusion",
        "due_diligence_replacement_claim"
    ]

    @classmethod
    def rank_source(cls, source_type: str, source_title: str) -> EvidenceLevel:
        """Rank evidence source."""
        source_lower = (source_type + " " + source_title).lower()

        for high_keyword in cls.HIGH_SOURCES:
            if high_keyword in source_lower:
                return EvidenceLevel.HIGH

        for medium_keyword in cls.MEDIUM_SOURCES:
            if medium_keyword in source_lower:
                return EvidenceLevel.MEDIUM

        for low_keyword in cls.LOW_SOURCES:
            if low_keyword in source_lower:
                return EvidenceLevel.LOW

        return EvidenceLevel.UNKNOWN

    @classmethod
    def validate_evidence(cls, evidence: Dict[str, Any]) -> bool:
        """Validate evidence has required fields."""
        required_fields = [
            "source_url", "source_title", "source_type",
            "publish_date", "extracted_claim", "company_match_confidence"
        ]

        for field in required_fields:
            if field not in evidence:
                return False

        # Check for blocked fields
        for blocked in cls.BLOCKED_FIELDS:
            if blocked in evidence.get("extracted_claim", "").lower():
                return False

        return True

    @classmethod
    def filter_evidence(cls, raw_evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter evidence through Trust Gate.

        Returns only evidence that:
        1. Has all required fields
        2. Does not contain blocked fields
        3. Has valid source ranking
        """
        curated_evidence = []

        for evidence in raw_evidence:
            if not cls.validate_evidence(evidence):
                continue

            # Add source rank
            evidence["source_rank"] = cls.rank_source(
                evidence.get("source_type", ""),
                evidence.get("source_title", "")
            )

            # Add allowed use guidance
            if evidence["source_rank"] == EvidenceLevel.HIGH:
                evidence["allowed_use"] = "可作为事实，但必须带来源"
            elif evidence["source_rank"] == EvidenceLevel.MEDIUM:
                evidence["allowed_use"] = '可作为背景或"据公开资料显示"，不得作最终结论'
            elif evidence["source_rank"] == EvidenceLevel.LOW:
                evidence["allowed_use"] = "只能作为待核查线索，不得写成事实"
            else:
                evidence["allowed_use"] = "不可使用"
                continue

            curated_evidence.append(evidence)

        return curated_evidence


class BlockedClaimsScanner:
    """
    Post-QC: Scan output for blocked claims.

    Runs AFTER LLM generation to detect prohibited expressions.
    """

    BLOCKED_PATTERNS = [
        r"值得投资",
        r"不值得投资",
        r"买入",
        r"卖出",
        r"持有评级",
        r"目标价",
        r"估值区间",
        r"合理市值",
        r"建议加仓",
        r"建议减仓",
        r"配置比例",
        r"无.*风险",
        r"不存在.*风险",
        r"可替代尽调",
        r"可替代审计",
        r"可替代.*核查",
        r"替代投委会",
    ]

    @classmethod
    def scan(cls, text: str) -> List[str]:
        """Scan text for blocked claims."""
        detected = []

        for pattern in cls.BLOCKED_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                detected.append(f"检测到禁用表达: {pattern} (匹配: {matches})")

        return detected


class CompanyPanorama:
    """Main class for Company Panorama v0."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Choice API key from environment."""
        self.api_key = api_key or os.getenv("CHOICE_MIAOXIANG_API_KEY")
        if not self.api_key:
            raise ValueError(
                "CHOICE_MIAOXIANG_API_KEY not found in environment. "
                "Please set: export CHOICE_MIAOXIANG_API_KEY='your_key'"
            )

        self.trust_gate = TrustGate()
        self.blocked_claims_scanner = BlockedClaimsScanner()

    def resolve_company(
        self,
        company_name: str,
        company_alias: Optional[List[str]] = None,
        entity_type: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Phase 1: Resolve company to avoid ambiguity.

        Returns:
            {
                "resolved_name": str,
                "stock_code": Optional[str],
                "entity_type": "listed" | "private" | "issuer" | "unknown",
                "confidence": float
            }
        """
        # TODO: Implement actual Choice API call for company resolution
        # For now, return mock data

        return {
            "resolved_name": company_name,
            "stock_code": None,
            "entity_type": entity_type,
            "confidence": 0.85,
            "aliases": company_alias or [],
            "resolution_note": "Mock resolution - implement Choice API call"
        }

    def collect_evidence(
        self,
        resolved_company: Dict[str, Any],
        as_of_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Phase 2: Collect evidence from Choice API or fallback sources.

        Evidence categories:
        - 公司基本资料
        - 公告与年报
        - 新闻与舆情
        - 行业背景
        - 股东结构（上市公司）

        Returns raw evidence (unfiltered).
        """
        # TODO: Implement actual Choice API calls
        # For now, return mock evidence

        raw_evidence = [
            {
                "source_url": "https://www.catl.com/uploads/1/file/public/202603/20260310001119_eph6t9ivki.pdf",
                "source_title": "宁德时代2025年年报摘要",
                "source_type": "年报",
                "publish_date": "2026-03-10",
                "extracted_claim": "主营业务：动力电池、储能电池的研发、生产、销售",
                "company_match_confidence": 1.0
            },
            {
                "source_url": "https://www.catl.com/news/",
                "source_title": "宁德时代新闻页",
                "source_type": "公司官网",
                "publish_date": "2026-07-06",
                "extracted_claim": "天行Ⅱ轻商超充版电池发布",
                "company_match_confidence": 1.0
            },
            {
                "source_url": "https://data.eastmoney.com/notice/300750.html",
                "source_title": "东方财富公告列表",
                "source_type": "公告",
                "publish_date": "2026-06-26",
                "extracted_claim": "绿色科技创新债券发行完成、套期保值/衍生品相关公告",
                "company_match_confidence": 0.95
            }
        ]

        return raw_evidence

    def generate_visit_card(
        self,
        resolved_company: Dict[str, Any],
        curated_evidence: List[Dict[str, Any]],
        visit_role: str = "general",
        language: str = "zh-CN"
    ) -> Dict[str, Any]:
        """
        Phase 4: Generate visit preparation card using LLM.

        Input: Trust Gate filtered evidence only.
        Output: Structured visit card.
        """
        company_name = resolved_company["resolved_name"]
        as_of_date = datetime.now().strftime("%Y-%m-%d")

        # Build evidence summary by level
        evidence_by_level = {
            EvidenceLevel.HIGH: [],
            EvidenceLevel.MEDIUM: [],
            EvidenceLevel.LOW: []
        }

        for evidence in curated_evidence:
            level = evidence.get("source_rank", EvidenceLevel.UNKNOWN)
            if level in evidence_by_level:
                evidence_by_level[level].append(evidence)

        # Generate visit card structure
        visit_card = {
            "company": company_name,
            "as_of_date": as_of_date,
            "card_title": "3分钟客户拜访准备卡",
            "one_page_summary": {
                "positioning": "UNKNOWN",
                "main_business": [],
                "key_people": [],
                "products_services": [],
                "recent_updates": []
            },
            "risk_radar": [
                {
                    "risk_type": "工商异常",
                    "signal_status": RiskSignalStatus.UNKNOWN,
                    "signal": "v0 样例未接入工商官方源，需人工核查",
                    "evidence_level": EvidenceLevel.UNKNOWN
                },
                {
                    "risk_type": "舆情风险",
                    "signal_status": RiskSignalStatus.REQUIRES_MANUAL_CHECK,
                    "signal": "近期新闻较多，需区分公司官网新闻、主流媒体报道与市场传闻",
                    "evidence_level": EvidenceLevel.MEDIUM
                },
                {
                    "risk_type": "诉讼风险",
                    "signal_status": RiskSignalStatus.UNKNOWN,
                    "signal": "需接法院/仲裁/公告源确认",
                    "evidence_level": EvidenceLevel.UNKNOWN
                },
                {
                    "risk_type": "股权/控制权风险",
                    "signal_status": RiskSignalStatus.REQUIRES_MANUAL_CHECK,
                    "signal": "上市公司股东结构可查，但本卡不作控制权稳定性结论",
                    "evidence_level": EvidenceLevel.MEDIUM
                },
                {
                    "risk_type": "经营波动风险",
                    "signal_status": RiskSignalStatus.SIGNAL_PRESENT,
                    "signal": "公司公告涉及套期保值/衍生品及债券融资事项，可作为拜访前核查信号",
                    "evidence_level": EvidenceLevel.HIGH
                }
            ],
            "evidence_grade_table": {
                "High": ["官方公告", "工商", "年报", "监管文件"],
                "Medium": ["主流媒体", "券商研报", "招投标", "招聘", "公开业务资料"],
                "Low": ["自媒体", "二手转述", "估算信息"]
            },
            "non_derivation_boundaries": [
                "未取得审计财报时，不确认未经审计财务口径",
                "媒体估算不等于事实",
                "非上市公司收入/利润默认 UNKNOWN",
                "本报告不构成投资建议",
                "风险信号不等于风险事实"
            ],
            "manual_check_questions": [
                "请确认当前主营收入来源及不同业务线占比",
                "是否存在大客户集中或区域集中情况？",
                "最近融资、扩产或海外布局进度如何？",
                "是否存在未披露诉讼、担保或关联交易风险？",
                "当前主要合作方和销售区域是什么？"
            ],
            "blocked_claims_detected": [],
            "disclaimer": "本卡片仅用于拜访前背景准备，不构成投资建议或尽调替代。",
            "evidence_summary": {
                "high_count": len(evidence_by_level[EvidenceLevel.HIGH]),
                "medium_count": len(evidence_by_level[EvidenceLevel.MEDIUM]),
                "low_count": len(evidence_by_level[EvidenceLevel.LOW]),
                "total_count": len(curated_evidence)
            }
        }

        # Fill in data from evidence
        for evidence in curated_evidence:
            claim = evidence.get("extracted_claim", "")
            level = evidence.get("source_rank", EvidenceLevel.UNKNOWN)

            if "主营业务" in claim:
                visit_card["one_page_summary"]["main_business"].append(
                    f"{claim}（证据等级 {level}）"
                )

            if any(keyword in claim for keyword in ["董事长", "CEO", "总经理"]):
                visit_card["one_page_summary"]["key_people"].append({
                    "name": "待提取",
                    "role": claim,
                    "evidence_level": level
                })

            if any(keyword in claim for keyword in ["产品", "服务", "业务"]):
                visit_card["one_page_summary"]["products_services"].append(
                    f"{claim}（证据等级 {level}）"
                )

            if evidence.get("publish_date", "").startswith("2026"):
                visit_card["one_page_summary"]["recent_updates"].append({
                    "date": evidence["publish_date"],
                    "signal": claim,
                    "source_rank": level
                })

        return visit_card

    def run(
        self,
        company_name: str,
        company_alias: Optional[List[str]] = None,
        entity_type: str = "unknown",
        visit_role: str = "general",
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Full pipeline: Resolve → Collect → Trust Gate → Generate → Post-QC
        """
        print(f"[Phase 1] Resolving company: {company_name}")
        resolved_company = self.resolve_company(
            company_name=company_name,
            company_alias=company_alias,
            entity_type=entity_type
        )
        print(f"  ✓ Resolved: {resolved_company['resolved_name']} "
              f"(confidence: {resolved_company['confidence']:.2f})")

        print(f"\n[Phase 2] Collecting evidence from Choice API")
        raw_evidence = self.collect_evidence(resolved_company)
        print(f"  ✓ Collected {len(raw_evidence)} raw evidence items")

        print(f"\n[Phase 3] Trust Gate filtering")
        curated_evidence = self.trust_gate.filter_evidence(raw_evidence)
        print(f"  ✓ Passed {len(curated_evidence)} evidence items through Trust Gate")
        print(f"    - High: {sum(1 for e in curated_evidence if e.get('source_rank') == EvidenceLevel.HIGH)}")
        print(f"    - Medium: {sum(1 for e in curated_evidence if e.get('source_rank') == EvidenceLevel.MEDIUM)}")
        print(f"    - Low: {sum(1 for e in curated_evidence if e.get('source_rank') == EvidenceLevel.LOW)}")

        print(f"\n[Phase 4] Generating visit preparation card")
        visit_card = self.generate_visit_card(
            resolved_company=resolved_company,
            curated_evidence=curated_evidence,
            visit_role=visit_role
        )
        print(f"  ✓ Generated visit card for {visit_card['company']}")

        print(f"\n[Phase 5] Post-QC: Scanning for blocked claims")
        card_text = json.dumps(visit_card, ensure_ascii=False)
        blocked_claims = self.blocked_claims_scanner.scan(card_text)
        visit_card["blocked_claims_detected"] = blocked_claims

        if blocked_claims:
            print(f"  ⚠ Detected {len(blocked_claims)} blocked claims:")
            for claim in blocked_claims:
                print(f"    - {claim}")
        else:
            print(f"  ✓ No blocked claims detected")

        # Save output
        if output_path is None:
            safe_name = re.sub(r'[^\w\-]', '_', company_name)
            timestamp = datetime.now().strftime("%Y%m%d")
            output_path = f"{safe_name}_visit_card_{timestamp}.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(visit_card, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Visit card saved to: {output_path}")

        return visit_card


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python company_panorama.py <company_name> [entity_type]")
        print("\nExample:")
        print("  python company_panorama.py '宁德时代新能源科技股份有限公司' listed")
        print("\nEntity types: listed, private, issuer, unknown")
        sys.exit(1)

    company_name = sys.argv[1]
    entity_type = sys.argv[2] if len(sys.argv) > 2 else "unknown"

    try:
        panorama = CompanyPanorama()
        visit_card = panorama.run(
            company_name=company_name,
            entity_type=entity_type
        )

        print("\n" + "="*60)
        print("Visit Card Summary")
        print("="*60)
        print(f"Company: {visit_card['company']}")
        print(f"As of Date: {visit_card['as_of_date']}")
        print(f"Evidence Count: {visit_card['evidence_summary']['total_count']}")
        print(f"  - High: {visit_card['evidence_summary']['high_count']}")
        print(f"  - Medium: {visit_card['evidence_summary']['medium_count']}")
        print(f"  - Low: {visit_card['evidence_summary']['low_count']}")
        print(f"Blocked Claims: {len(visit_card['blocked_claims_detected'])}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
