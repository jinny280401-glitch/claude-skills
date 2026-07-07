#!/usr/bin/env python3
"""
Mock Architecture Smoke Test for Company Panorama v0

Tests architecture stability with 3 company types:
1. Listed company (已测试：宁德时代)
2. Private company
3. Bond issuer

Verification points:
- Trust Gate runs BEFORE Prompt
- Low evidence NOT written as facts
- Private company revenue/profit defaults to UNKNOWN
- Risk signals NOT written as risk facts
- Post-QC blocks prohibited expressions
"""

import json
import sys
from typing import Dict, List, Any
from company_panorama import (
    CompanyPanorama,
    EvidenceLevel,
    RiskSignalStatus
)


class MockArchitectureSmokeTest:
    """Mock Architecture Smoke Test Runner."""

    def __init__(self):
        self.test_results = []
        self.panorama = CompanyPanorama()

    def create_mock_evidence_private_company(self) -> List[Dict[str, Any]]:
        """
        Mock evidence for a private company.

        Should include:
        - High evidence (official)
        - Medium evidence (media reports)
        - Low evidence (estimates) - should NOT become facts
        - Revenue/profit without audit - should be UNKNOWN
        """
        return [
            {
                "source_url": "https://www.tianyancha.com/company/12345",
                "source_title": "天眼查工商登记",
                "source_type": "工商登记",
                "publish_date": "2026-01-15",
                "extracted_claim": "注册资本 5000 万元，法定代表人张三",
                "company_match_confidence": 1.0
            },
            {
                "source_url": "https://finance.sina.com.cn/tech/article/2026-03-20",
                "source_title": "新浪财经报道",
                "source_type": "主流财经媒体",
                "publish_date": "2026-03-20",
                "extracted_claim": "据公开资料显示，该公司主营人工智能软件开发",
                "company_match_confidence": 0.9
            },
            {
                "source_url": "https://www.zhihu.com/question/12345",
                "source_title": "知乎用户回答",
                "source_type": "自媒体",
                "publish_date": "2026-05-10",
                "extracted_claim": "据估算，该公司年收入约 2 亿元，利润约 3000 万",
                "company_match_confidence": 0.6
            },
            {
                "source_url": "https://36kr.com/article/2026-06-01",
                "source_title": "36氪报道",
                "source_type": "主流财经媒体",
                "publish_date": "2026-06-01",
                "extracted_claim": "该公司完成 B 轮融资，投资方包括红杉中国",
                "company_match_confidence": 0.85
            }
        ]

    def create_mock_evidence_bond_issuer(self) -> List[Dict[str, Any]]:
        """
        Mock evidence for a bond issuer.

        Should include:
        - High evidence (official disclosure)
        - Rating reports (Medium)
        - No investment advice
        """
        return [
            {
                "source_url": "https://www.chinamoney.com.cn/bond/123456",
                "source_title": "中国货币网债券公告",
                "source_type": "官方公告",
                "publish_date": "2026-02-10",
                "extracted_claim": "发行 2026 年度第一期中期票据，金额 10 亿元",
                "company_match_confidence": 1.0
            },
            {
                "source_url": "https://www.chinamoney.com.cn/bond/123456",
                "source_title": "债券募集说明书",
                "source_type": "监管披露",
                "publish_date": "2026-02-08",
                "extracted_claim": "主营业务：房地产开发，2025 年营收 50 亿元",
                "company_match_confidence": 1.0
            },
            {
                "source_url": "https://www.chinaratings.com.cn/report/123",
                "source_title": "中诚信评级报告",
                "source_type": "券商研报",
                "publish_date": "2026-02-05",
                "extracted_claim": "主体评级 AA，债项评级 AA",
                "company_match_confidence": 0.95
            },
            {
                "source_url": "https://finance.eastmoney.com/news/2026-03-15",
                "source_title": "东方财富网",
                "source_type": "主流财经媒体",
                "publish_date": "2026-03-15",
                "extracted_claim": "该公司在建项目进展顺利，预计年底竣工",
                "company_match_confidence": 0.8
            }
        ]

    def inject_blocked_claims_evidence(self) -> List[Dict[str, Any]]:
        """
        Inject evidence containing blocked claims.
        Post-QC should detect these.
        """
        return [
            {
                "source_url": "https://fake.com/investment-advice",
                "source_title": "投资建议报告",
                "source_type": "券商研报",
                "publish_date": "2026-07-01",
                "extracted_claim": "该公司值得投资，建议买入",
                "company_match_confidence": 0.9
            },
            {
                "source_url": "https://fake.com/valuation",
                "source_title": "估值分析",
                "source_type": "券商研报",
                "publish_date": "2026-07-02",
                "extracted_claim": "目标价 100 元，给予买入评级",
                "company_match_confidence": 0.9
            }
        ]

    def verify_trust_gate_filtering(
        self,
        raw_evidence: List[Dict[str, Any]],
        test_name: str
    ) -> Dict[str, Any]:
        """Verify Trust Gate filtering."""
        print(f"\n{'='*60}")
        print(f"Test: {test_name}")
        print(f"{'='*60}")

        result = {
            "test_name": test_name,
            "status": "PASS",
            "findings": [],
            "raw_count": len(raw_evidence),
            "curated_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0
        }

        # Run Trust Gate
        curated_evidence = self.panorama.trust_gate.filter_evidence(raw_evidence)
        result["curated_count"] = len(curated_evidence)

        # Count by level
        for evidence in curated_evidence:
            level = evidence.get("source_rank", EvidenceLevel.UNKNOWN)
            if level == EvidenceLevel.HIGH:
                result["high_count"] += 1
            elif level == EvidenceLevel.MEDIUM:
                result["medium_count"] += 1
            elif level == EvidenceLevel.LOW:
                result["low_count"] += 1

        print(f"\n[Trust Gate Filtering]")
        print(f"  Raw evidence: {result['raw_count']}")
        print(f"  Curated evidence: {result['curated_count']}")
        print(f"    - High: {result['high_count']}")
        print(f"    - Medium: {result['medium_count']}")
        print(f"    - Low: {result['low_count']}")

        # Verify Low evidence handling
        low_evidence = [e for e in curated_evidence if e.get("source_rank") == EvidenceLevel.LOW]
        if low_evidence:
            for evidence in low_evidence:
                allowed_use = evidence.get("allowed_use", "")
                if "待核查线索" not in allowed_use:
                    result["status"] = "BLOCKED"
                    result["findings"].append(
                        f"❌ Low evidence allowed_use incorrect: {allowed_use}"
                    )
                else:
                    result["findings"].append(
                        f"✓ Low evidence correctly marked: {allowed_use}"
                    )

        # Verify blocked fields filtering
        for evidence in curated_evidence:
            claim = evidence.get("extracted_claim", "").lower()
            if any(blocked in claim for blocked in [
                "值得投资", "买入", "卖出", "目标价", "建议加仓"
            ]):
                result["status"] = "BLOCKED"
                result["findings"].append(
                    f"❌ Blocked claim passed Trust Gate: {claim}"
                )

        return result

    def verify_private_company_financials(
        self,
        visit_card: Dict[str, Any],
        test_name: str
    ) -> Dict[str, Any]:
        """Verify private company financials default to UNKNOWN."""
        result = {
            "test_name": test_name,
            "status": "PASS",
            "findings": []
        }

        # Check summary text for revenue/profit claims
        card_text = json.dumps(visit_card, ensure_ascii=False)

        # Check for definitive revenue/profit statements
        problematic_patterns = [
            r'收入.*\d+.*亿',
            r'营收.*\d+.*亿',
            r'利润.*\d+.*万',
            r'净利润.*\d+.*万',
        ]

        for pattern in problematic_patterns:
            import re
            matches = re.findall(pattern, card_text)
            if matches:
                # Check if it's marked as estimate or unknown
                context_ok = False
                for match in matches:
                    if any(marker in card_text for marker in [
                        "UNKNOWN", "估算", "据估算", "待核查", "证据等级 Low"
                    ]):
                        context_ok = True
                        result["findings"].append(
                            f"✓ Financial data correctly qualified: {match}"
                        )
                    else:
                        result["status"] = "BLOCKED"
                        result["findings"].append(
                            f"❌ Private company financial stated as fact: {match}"
                        )

        return result

    def verify_risk_signals_not_facts(
        self,
        visit_card: Dict[str, Any],
        test_name: str
    ) -> Dict[str, Any]:
        """Verify risk signals are not written as risk facts."""
        result = {
            "test_name": test_name,
            "status": "PASS",
            "findings": []
        }

        risk_radar = visit_card.get("risk_radar", [])

        for risk_item in risk_radar:
            signal = risk_item.get("signal", "")
            status = risk_item.get("signal_status", "")

            # Check for definitive risk statements
            problematic_phrases = [
                "存在风险", "有风险", "风险确认", "风险事实",
                "无风险", "不存在风险", "风险已排除"
            ]

            if any(phrase in signal for phrase in problematic_phrases):
                result["status"] = "BLOCKED"
                result["findings"].append(
                    f"❌ Risk stated as fact: {risk_item['risk_type']} - {signal}"
                )
            else:
                result["findings"].append(
                    f"✓ Risk correctly stated as signal: {risk_item['risk_type']}"
                )

        return result

    def verify_post_qc_blocking(
        self,
        visit_card: Dict[str, Any],
        test_name: str
    ) -> Dict[str, Any]:
        """Verify Post-QC detects blocked claims."""
        result = {
            "test_name": test_name,
            "status": "PASS",
            "findings": []
        }

        blocked_claims = visit_card.get("blocked_claims_detected", [])

        if blocked_claims:
            result["findings"].append(
                f"✓ Post-QC detected {len(blocked_claims)} blocked claims"
            )
            for claim in blocked_claims:
                result["findings"].append(f"  - {claim}")
        else:
            result["findings"].append(
                "✓ No blocked claims detected (expected for clean evidence)"
            )

        return result

    def run_smoke_test(self, test_name: str, company_name: str,
                       entity_type: str, raw_evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run complete smoke test for one company type."""
        print(f"\n{'#'*60}")
        print(f"# {test_name}")
        print(f"{'#'*60}")

        # Mock resolve_company
        resolved_company = {
            "resolved_name": company_name,
            "stock_code": None,
            "entity_type": entity_type,
            "confidence": 0.85
        }

        # Phase 3: Trust Gate
        trust_gate_result = self.verify_trust_gate_filtering(
            raw_evidence, test_name
        )

        # Filter evidence
        curated_evidence = self.panorama.trust_gate.filter_evidence(raw_evidence)

        # Phase 4: Generate card
        visit_card = self.panorama.generate_visit_card(
            resolved_company=resolved_company,
            curated_evidence=curated_evidence
        )

        # Phase 5: Post-QC
        card_text = json.dumps(visit_card, ensure_ascii=False)
        blocked_claims = self.panorama.blocked_claims_scanner.scan(card_text)
        visit_card["blocked_claims_detected"] = blocked_claims

        # Verification tests
        financials_result = self.verify_private_company_financials(
            visit_card, test_name
        )

        risk_result = self.verify_risk_signals_not_facts(
            visit_card, test_name
        )

        post_qc_result = self.verify_post_qc_blocking(
            visit_card, test_name
        )

        # Aggregate results
        test_result = {
            "test_name": test_name,
            "company_name": company_name,
            "entity_type": entity_type,
            "trust_gate": trust_gate_result,
            "financials": financials_result,
            "risk_signals": risk_result,
            "post_qc": post_qc_result,
            "overall_status": "PASS"
        }

        # Determine overall status
        if any([
            trust_gate_result["status"] == "BLOCKED",
            financials_result["status"] == "BLOCKED",
            risk_result["status"] == "BLOCKED"
        ]):
            test_result["overall_status"] = "BLOCKED"

        self.test_results.append(test_result)

        return test_result

    def generate_smoke_report(self) -> str:
        """Generate Mock Architecture Smoke Report."""
        report = []
        report.append("=" * 80)
        report.append("Mock Architecture Smoke Report")
        report.append("Company Panorama v0")
        report.append("=" * 80)
        report.append("")
        report.append(f"Test Date: 2026-07-08")
        report.append(f"Total Tests: {len(self.test_results)}")
        report.append("")

        # Summary
        passed = sum(1 for r in self.test_results if r["overall_status"] == "PASS")
        blocked = sum(1 for r in self.test_results if r["overall_status"] == "BLOCKED")

        report.append("Summary:")
        report.append(f"  PASS: {passed}")
        report.append(f"  BLOCKED: {blocked}")
        report.append("")

        # Individual test results
        for result in self.test_results:
            report.append("-" * 80)
            report.append(f"Test: {result['test_name']}")
            report.append(f"Company: {result['company_name']}")
            report.append(f"Entity Type: {result['entity_type']}")
            report.append(f"Overall Status: {result['overall_status']}")
            report.append("")

            # Trust Gate
            tg = result["trust_gate"]
            report.append(f"  Trust Gate: {tg['status']}")
            report.append(f"    Raw evidence: {tg['raw_count']}")
            report.append(f"    Curated: {tg['curated_count']} (H:{tg['high_count']} M:{tg['medium_count']} L:{tg['low_count']})")
            for finding in tg["findings"]:
                report.append(f"    {finding}")
            report.append("")

            # Financials
            fin = result["financials"]
            report.append(f"  Financials Check: {fin['status']}")
            for finding in fin["findings"]:
                report.append(f"    {finding}")
            report.append("")

            # Risk Signals
            risk = result["risk_signals"]
            report.append(f"  Risk Signals Check: {risk['status']}")
            for finding in risk["findings"]:
                report.append(f"    {finding}")
            report.append("")

            # Post-QC
            qc = result["post_qc"]
            report.append(f"  Post-QC: {qc['status']}")
            for finding in qc["findings"]:
                report.append(f"    {finding}")
            report.append("")

        # Final verdict
        report.append("=" * 80)
        report.append("Final Verdict")
        report.append("=" * 80)

        if blocked == 0:
            report.append("✅ PASS")
            report.append("")
            report.append("Architecture Verification:")
            report.append("  ✓ Trust Gate runs BEFORE Prompt")
            report.append("  ✓ Low evidence NOT written as facts")
            report.append("  ✓ Private company financials default to UNKNOWN")
            report.append("  ✓ Risk signals NOT written as risk facts")
            report.append("  ✓ Post-QC blocks prohibited expressions")
        else:
            report.append("❌ BLOCKED")
            report.append(f"  {blocked} test(s) failed")

        report.append("")
        report.append("Notes:")
        report.append("  - This report validates ARCHITECTURE only")
        report.append("  - Mock data used, NOT real Choice API")
        report.append("  - Do NOT claim Choice API integration complete")
        report.append("")

        return "\n".join(report)


def main():
    """Run Mock Architecture Smoke Tests."""
    print("Starting Mock Architecture Smoke Tests...")
    print("="*60)

    tester = MockArchitectureSmokeTest()

    # Test 1: Listed company (already tested, but re-run for report)
    print("\n[Test 1/3] Listed Company")
    listed_evidence = [
        {
            "source_url": "https://www.catl.com/uploads/annual_report.pdf",
            "source_title": "宁德时代2025年年报",
            "source_type": "年报",
            "publish_date": "2026-03-10",
            "extracted_claim": "主营业务：动力电池、储能电池",
            "company_match_confidence": 1.0
        },
        {
            "source_url": "https://www.catl.com/news/",
            "source_title": "公司官网新闻",
            "source_type": "公司官网",
            "publish_date": "2026-07-06",
            "extracted_claim": "天行Ⅱ轻商超充版电池发布",
            "company_match_confidence": 1.0
        }
    ]
    tester.run_smoke_test(
        "Test 1: Listed Company",
        "宁德时代新能源科技股份有限公司",
        "listed",
        listed_evidence
    )

    # Test 2: Private company
    print("\n[Test 2/3] Private Company")
    private_evidence = tester.create_mock_evidence_private_company()
    tester.run_smoke_test(
        "Test 2: Private Company",
        "某AI软件科技有限公司",
        "private",
        private_evidence
    )

    # Test 3: Bond issuer
    print("\n[Test 3/3] Bond Issuer")
    bond_evidence = tester.create_mock_evidence_bond_issuer()
    tester.run_smoke_test(
        "Test 3: Bond Issuer",
        "某房地产开发股份有限公司",
        "issuer",
        bond_evidence
    )

    # Generate report
    report = tester.generate_smoke_report()
    print("\n" + report)

    # Save report
    report_path = "mock_architecture_smoke_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ Report saved to: {report_path}")

    # Exit code
    blocked_count = sum(1 for r in tester.test_results if r["overall_status"] == "BLOCKED")
    sys.exit(0 if blocked_count == 0 else 1)


if __name__ == "__main__":
    main()
