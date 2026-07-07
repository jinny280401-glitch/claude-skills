#!/usr/bin/env python3
"""
Choice Adapter Smoke v0

Purpose: Verify Choice API can provide real evidence for Company Panorama.
Scope: Adapter probe ONLY - no full pipeline, no production visit cards.

Tests 3 capabilities:
1. resolve_company(company_name)
2. fetch_announcements(entity_id or stock_code)
3. fetch_news(company_name or entity_id)

Output: Choice Adapter Smoke Report
"""

import os
import json
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests


class ChoiceAdapterProbe:
    """
    Minimal probe for Choice API connectivity and evidence capability.

    NOT a production adapter. Only for smoke testing.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Choice Miaoxiang API key."""
        # Try both EM_API_KEY (official) and CHOICE_MIAOXIANG_API_KEY (legacy)
        self.api_key = api_key or os.getenv("EM_API_KEY") or os.getenv("CHOICE_MIAOXIANG_API_KEY")
        if not self.api_key:
            raise ValueError(
                "EM_API_KEY not found in environment. "
                "Please set: export EM_API_KEY='your_key'"
            )

        # Choice Miaoxiang MCP Server
        # Reference: https://mxapi.eastmoney.com/mxds/doc/mcp-install.md
        self.mcp_url = "https://mxapi.eastmoney.com/mxds/mcp"
        self.headers = {
            "em_api_key": self.api_key,
            "Content-Type": "application/json"
        }

        self.test_results = {
            "CONNECTIVITY": "UNKNOWN",
            "AUTH": "UNKNOWN",
            "RESOLVE_COMPANY": "UNKNOWN",
            "ANNOUNCEMENTS": "UNKNOWN",
            "NEWS": "UNKNOWN",
            "EVIDENCE_FIELDS_COMPLETE": "FAIL",
            "QC_FIELDS_PRESENT": "FAIL",
            "Can_enter_Real_Evidence_Integration": "NO"
        }

        self.test_details = []

    def test_connectivity(self) -> bool:
        """Test basic connectivity to Choice Miaoxiang MCP Server."""
        print("\n[Test 1/6] Testing Connectivity...")

        try:
            # Try MCP tools/list endpoint to test connectivity
            response = requests.post(
                self.mcp_url,
                headers=self.headers,
                json={"method": "tools/list"},
                timeout=10
            )

            if response.status_code == 200:
                self.test_results["CONNECTIVITY"] = "PASS"
                self.test_details.append({
                    "test": "connectivity",
                    "status": "PASS",
                    "note": "MCP Server reachable"
                })
                print("  ✓ Connectivity: PASS")
                return True
            else:
                self.test_results["CONNECTIVITY"] = "FAIL"
                self.test_details.append({
                    "test": "connectivity",
                    "status": "FAIL",
                    "note": f"HTTP {response.status_code}"
                })
                print(f"  ✗ Connectivity: FAIL (HTTP {response.status_code})")
                return False

        except Exception as e:
            self.test_results["CONNECTIVITY"] = "FAIL"
            self.test_details.append({
                "test": "connectivity",
                "status": "FAIL",
                "note": str(e)
            })
            print(f"  ✗ Connectivity: FAIL ({e})")
            return False

    def test_auth(self) -> bool:
        """Test authentication with MCP Server."""
        print("\n[Test 2/6] Testing Authentication...")

        try:
            # Use tools/list to verify auth
            response = requests.post(
                self.mcp_url,
                headers=self.headers,
                json={"method": "tools/list"},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                # Check if we got valid tools list
                if "tools" in data or "result" in data:
                    self.test_results["AUTH"] = "PASS"
                    self.test_details.append({
                        "test": "auth",
                        "status": "PASS",
                        "note": "API key valid"
                    })
                    print("  ✓ Authentication: PASS")
                    return True
                else:
                    self.test_results["AUTH"] = "UNKNOWN"
                    self.test_details.append({
                        "test": "auth",
                        "status": "UNKNOWN",
                        "note": "Unexpected response format"
                    })
                    print("  ? Authentication: UNKNOWN (unexpected format)")
                    return False
            elif response.status_code == 401 or response.status_code == 403:
                self.test_results["AUTH"] = "FAIL"
                self.test_details.append({
                    "test": "auth",
                    "status": "FAIL",
                    "note": f"API key invalid ({response.status_code})"
                })
                print(f"  ✗ Authentication: FAIL ({response.status_code} Unauthorized)")
                return False
            else:
                self.test_results["AUTH"] = "UNKNOWN"
                self.test_details.append({
                    "test": "auth",
                    "status": "UNKNOWN",
                    "note": f"HTTP {response.status_code}"
                })
                print(f"  ? Authentication: UNKNOWN (HTTP {response.status_code})")
                return False

        except Exception as e:
            self.test_results["AUTH"] = "FAIL"
            self.test_details.append({
                "test": "auth",
                "status": "FAIL",
                "note": str(e)
            })
            print(f"  ✗ Authentication: FAIL ({e})")
            return False

    def resolve_company(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Test 1: Resolve company to entity ID.

        Required output fields:
        - company_name_normalized
        - company_id or choice_entity_id
        - stock_code (if listed)
        - entity_type: listed / private / bond_issuer / unknown
        - match_confidence
        - source
        """
        print(f"\n[Test 3/6] Testing resolve_company('{company_name}')...")

        try:
            # TODO: 根据 Choice API 文档调整实际的公司搜索端点
            # 示例端点假设
            response = requests.post(
                f"{self.base_url}/api/company/search",
                headers=self.headers,
                json={"query": company_name, "limit": 1},
                timeout=10
            )

            if response.status_code != 200:
                print(f"  ✗ HTTP {response.status_code}")
                self.test_results["RESOLVE_COMPANY"] = "FAIL"
                self.test_details.append({
                    "test": "resolve_company",
                    "company": company_name,
                    "status": "FAIL",
                    "note": f"HTTP {response.status_code}"
                })
                return None

            data = response.json()

            # TODO: 根据实际 API 响应格式提取字段
            # 这里使用假设的响应格式
            if not data or "results" not in data or len(data["results"]) == 0:
                print("  ✗ No results found")
                self.test_results["RESOLVE_COMPANY"] = "FAIL"
                self.test_details.append({
                    "test": "resolve_company",
                    "company": company_name,
                    "status": "FAIL",
                    "note": "No results"
                })
                return None

            result = data["results"][0]

            # Normalize output
            resolved = {
                "company_name_normalized": result.get("name", company_name),
                "company_id": result.get("id"),
                "choice_entity_id": result.get("entity_id"),
                "stock_code": result.get("stock_code"),
                "entity_type": self._determine_entity_type(result),
                "match_confidence": result.get("confidence", 0.0),
                "source": "Choice API"
            }

            # Validate required fields
            required_fields = [
                "company_name_normalized", "company_id", "entity_type",
                "match_confidence", "source"
            ]
            missing_fields = [f for f in required_fields if not resolved.get(f)]

            if missing_fields:
                print(f"  ✗ Missing required fields: {missing_fields}")
                self.test_results["RESOLVE_COMPANY"] = "FAIL"
                self.test_details.append({
                    "test": "resolve_company",
                    "company": company_name,
                    "status": "FAIL",
                    "note": f"Missing fields: {missing_fields}",
                    "data": resolved
                })
                return None

            self.test_results["RESOLVE_COMPANY"] = "PASS"
            self.test_details.append({
                "test": "resolve_company",
                "company": company_name,
                "status": "PASS",
                "data": resolved
            })

            print(f"  ✓ Resolved: {resolved['company_name_normalized']}")
            print(f"    Entity ID: {resolved.get('company_id') or resolved.get('choice_entity_id')}")
            print(f"    Entity Type: {resolved['entity_type']}")
            print(f"    Confidence: {resolved['match_confidence']}")

            return resolved

        except Exception as e:
            print(f"  ✗ Exception: {e}")
            self.test_results["RESOLVE_COMPANY"] = "FAIL"
            self.test_details.append({
                "test": "resolve_company",
                "company": company_name,
                "status": "FAIL",
                "note": str(e)
            })
            return None

    def _determine_entity_type(self, result: Dict[str, Any]) -> str:
        """Determine entity type from API result."""
        if result.get("stock_code"):
            return "listed"
        if result.get("bond_issuer"):
            return "bond_issuer"
        if result.get("listed") is False:
            return "private"
        return "unknown"

    def fetch_announcements(
        self,
        entity_id: Optional[str] = None,
        stock_code: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Test 2: Fetch announcements.

        Required output fields per announcement:
        - title
        - date
        - source
        - url or source_id
        - evidence_level (default: High)
        - allowed_use
        """
        print(f"\n[Test 4/6] Testing fetch_announcements(entity_id={entity_id}, stock_code={stock_code})...")

        if not entity_id and not stock_code:
            print("  ✗ Missing entity_id or stock_code")
            self.test_results["ANNOUNCEMENTS"] = "FAIL"
            return None

        try:
            # TODO: 根据 Choice API 文档调整实际的公告接口
            params = {}
            if stock_code:
                params["stock_code"] = stock_code
            if entity_id:
                params["entity_id"] = entity_id
            params["limit"] = 5

            response = requests.get(
                f"{self.base_url}/api/announcements",
                headers=self.headers,
                params=params,
                timeout=10
            )

            if response.status_code != 200:
                print(f"  ✗ HTTP {response.status_code}")
                self.test_results["ANNOUNCEMENTS"] = "FAIL"
                self.test_details.append({
                    "test": "fetch_announcements",
                    "status": "FAIL",
                    "note": f"HTTP {response.status_code}"
                })
                return None

            data = response.json()

            # TODO: 根据实际 API 响应格式提取
            announcements_raw = data.get("announcements", [])

            if not announcements_raw:
                print("  ✗ No announcements found")
                self.test_results["ANNOUNCEMENTS"] = "FAIL"
                self.test_details.append({
                    "test": "fetch_announcements",
                    "status": "FAIL",
                    "note": "No data"
                })
                return None

            # Normalize announcements
            announcements = []
            for item in announcements_raw[:5]:  # Limit to 5 for smoke test
                announcement = {
                    "title": item.get("title"),
                    "date": item.get("publish_date") or item.get("date"),
                    "source": item.get("source", "官方公告"),
                    "url": item.get("url"),
                    "source_id": item.get("id"),
                    "evidence_level": "High",  # Default for official announcements
                    "allowed_use": "可作为事实，但必须带来源"
                }

                # Validate required fields
                required_fields = ["title", "date", "source"]
                if all(announcement.get(f) for f in required_fields):
                    announcements.append(announcement)

            if not announcements:
                print("  ✗ No valid announcements after normalization")
                self.test_results["ANNOUNCEMENTS"] = "FAIL"
                self.test_details.append({
                    "test": "fetch_announcements",
                    "status": "FAIL",
                    "note": "Missing required fields"
                })
                return None

            self.test_results["ANNOUNCEMENTS"] = "PASS"
            self.test_details.append({
                "test": "fetch_announcements",
                "status": "PASS",
                "count": len(announcements),
                "sample": announcements[0] if announcements else None
            })

            print(f"  ✓ Fetched {len(announcements)} announcements")
            print(f"    Sample: {announcements[0]['title'][:50]}...")

            return announcements

        except Exception as e:
            print(f"  ✗ Exception: {e}")
            self.test_results["ANNOUNCEMENTS"] = "FAIL"
            self.test_details.append({
                "test": "fetch_announcements",
                "status": "FAIL",
                "note": str(e)
            })
            return None

    def fetch_news(
        self,
        company_name: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Test 3: Fetch news.

        Required output fields per news item:
        - title
        - date
        - source
        - url or source_id
        - source_rank
        - evidence_level (default: Medium or Low)
        - allowed_use
        - blocked_fields (list)
        """
        print(f"\n[Test 5/6] Testing fetch_news(company_name={company_name}, entity_id={entity_id})...")

        if not company_name and not entity_id:
            print("  ✗ Missing company_name or entity_id")
            self.test_results["NEWS"] = "FAIL"
            return None

        try:
            # TODO: 根据 Choice API 文档调整实际的新闻接口
            params = {}
            if company_name:
                params["keyword"] = company_name
            if entity_id:
                params["entity_id"] = entity_id
            params["limit"] = 5

            response = requests.get(
                f"{self.base_url}/api/news",
                headers=self.headers,
                params=params,
                timeout=10
            )

            if response.status_code != 200:
                print(f"  ✗ HTTP {response.status_code}")
                self.test_results["NEWS"] = "FAIL"
                self.test_details.append({
                    "test": "fetch_news",
                    "status": "FAIL",
                    "note": f"HTTP {response.status_code}"
                })
                return None

            data = response.json()

            # TODO: 根据实际 API 响应格式提取
            news_raw = data.get("news", [])

            if not news_raw:
                print("  ✗ No news found")
                self.test_results["NEWS"] = "FAIL"
                self.test_details.append({
                    "test": "fetch_news",
                    "status": "FAIL",
                    "note": "No data"
                })
                return None

            # Normalize news
            news_items = []
            for item in news_raw[:5]:  # Limit to 5 for smoke test
                source = item.get("source", "")
                source_rank = self._rank_news_source(source)

                news_item = {
                    "title": item.get("title"),
                    "date": item.get("publish_date") or item.get("date"),
                    "source": source,
                    "url": item.get("url"),
                    "source_id": item.get("id"),
                    "source_rank": source_rank,
                    "evidence_level": "Medium" if source_rank == "Medium" else "Low",
                    "allowed_use": self._get_allowed_use(source_rank),
                    "blocked_fields": self._detect_blocked_fields(item)
                }

                # Validate required fields
                required_fields = ["title", "date", "source", "source_rank", "evidence_level", "allowed_use"]
                if all(news_item.get(f) for f in required_fields):
                    news_items.append(news_item)

            if not news_items:
                print("  ✗ No valid news after normalization")
                self.test_results["NEWS"] = "FAIL"
                self.test_details.append({
                    "test": "fetch_news",
                    "status": "FAIL",
                    "note": "Missing required fields"
                })
                return None

            self.test_results["NEWS"] = "PASS"
            self.test_details.append({
                "test": "fetch_news",
                "status": "PASS",
                "count": len(news_items),
                "sample": news_items[0] if news_items else None
            })

            print(f"  ✓ Fetched {len(news_items)} news items")
            print(f"    Sample: {news_items[0]['title'][:50]}...")

            return news_items

        except Exception as e:
            print(f"  ✗ Exception: {e}")
            self.test_results["NEWS"] = "FAIL"
            self.test_details.append({
                "test": "fetch_news",
                "status": "FAIL",
                "note": str(e)
            })
            return None

    def _rank_news_source(self, source: str) -> str:
        """Rank news source."""
        high_sources = ["官方", "监管", "证监会", "交易所"]
        medium_sources = ["新华社", "人民网", "财经", "证券", "第一财经", "东方财富"]

        source_lower = source.lower()

        if any(h in source_lower for h in high_sources):
            return "High"
        if any(m in source_lower for m in medium_sources):
            return "Medium"
        return "Low"

    def _get_allowed_use(self, source_rank: str) -> str:
        """Get allowed use guidance."""
        if source_rank == "High":
            return "可作为事实，但必须带来源"
        elif source_rank == "Medium":
            return '可作为背景或"据公开资料显示"，不得作最终结论'
        else:
            return "只能作为待核查线索，不得写成事实"

    def _detect_blocked_fields(self, item: Dict[str, Any]) -> List[str]:
        """Detect blocked fields in news item."""
        blocked = []
        content = json.dumps(item, ensure_ascii=False).lower()

        if any(word in content for word in ["估值", "目标价", "valuation"]):
            blocked.append("valuation")
        if any(word in content for word in ["评级", "rating", "买入", "卖出"]):
            blocked.append("rating")
        if any(word in content for word in ["建议", "仓位", "配置"]):
            blocked.append("investment_advice")

        return blocked

    def verify_evidence_fields(self) -> bool:
        """Test 6: Verify all evidence has required fields."""
        print("\n[Test 6/6] Verifying Evidence Fields Completeness...")

        # Check if previous tests passed
        if self.test_results["RESOLVE_COMPANY"] != "PASS":
            print("  ✗ Cannot verify - resolve_company failed")
            self.test_results["EVIDENCE_FIELDS_COMPLETE"] = "FAIL"
            return False

        if self.test_results["ANNOUNCEMENTS"] != "PASS":
            print("  ✗ Cannot verify - announcements failed")
            self.test_results["EVIDENCE_FIELDS_COMPLETE"] = "FAIL"
            return False

        if self.test_results["NEWS"] != "PASS":
            print("  ✗ Cannot verify - news failed")
            self.test_results["EVIDENCE_FIELDS_COMPLETE"] = "FAIL"
            return False

        # Check QC fields presence
        qc_fields_present = True

        # Check if announcements have evidence_level and allowed_use
        announcement_details = [d for d in self.test_details if d["test"] == "fetch_announcements"]
        if announcement_details:
            sample = announcement_details[0].get("sample", {})
            if not sample.get("evidence_level") or not sample.get("allowed_use"):
                qc_fields_present = False
                print("  ✗ Announcements missing QC fields")

        # Check if news has source_rank, evidence_level, allowed_use, blocked_fields
        news_details = [d for d in self.test_details if d["test"] == "fetch_news"]
        if news_details:
            sample = news_details[0].get("sample", {})
            required_qc = ["source_rank", "evidence_level", "allowed_use", "blocked_fields"]
            missing_qc = [f for f in required_qc if f not in sample]
            if missing_qc:
                qc_fields_present = False
                print(f"  ✗ News missing QC fields: {missing_qc}")

        if qc_fields_present:
            self.test_results["EVIDENCE_FIELDS_COMPLETE"] = "PASS"
            self.test_results["QC_FIELDS_PRESENT"] = "PASS"
            print("  ✓ All evidence fields complete")
            print("  ✓ QC fields present (evidence_level, allowed_use, blocked_fields)")
            return True
        else:
            self.test_results["EVIDENCE_FIELDS_COMPLETE"] = "FAIL"
            self.test_results["QC_FIELDS_PRESENT"] = "FAIL"
            return False

    def run_smoke_test(
        self,
        test_companies: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Run full adapter smoke test.

        test_companies: [
            {"name": "宁德时代", "type": "listed"},
            {"name": "某AI公司", "type": "private"},
            {"name": "某房地产", "type": "bond_issuer"}
        ]
        """
        print("="*80)
        print("Choice Adapter Smoke v0")
        print("="*80)
        print("\nScope: Adapter probe only - NO full pipeline, NO production")
        print("")

        # Test connectivity and auth first
        if not self.test_connectivity():
            print("\n❌ Connectivity failed - cannot proceed")
            return self.generate_report()

        if not self.test_auth():
            print("\n❌ Authentication failed - cannot proceed")
            return self.generate_report()

        # Test with sample companies
        for company in test_companies:
            company_name = company["name"]
            entity_type = company["type"]

            print(f"\n{'='*80}")
            print(f"Testing: {company_name} ({entity_type})")
            print(f"{'='*80}")

            # Resolve company
            resolved = self.resolve_company(company_name)
            if not resolved:
                continue

            # Fetch announcements (if has entity_id or stock_code)
            entity_id = resolved.get("company_id") or resolved.get("choice_entity_id")
            stock_code = resolved.get("stock_code")

            if entity_id or stock_code:
                self.fetch_announcements(entity_id=entity_id, stock_code=stock_code)

            # Fetch news
            self.fetch_news(company_name=company_name, entity_id=entity_id)

        # Verify evidence fields
        self.verify_evidence_fields()

        # Determine if can enter Real Evidence Integration
        can_proceed = all([
            self.test_results["RESOLVE_COMPANY"] == "PASS",
            self.test_results["ANNOUNCEMENTS"] == "PASS",
            self.test_results["NEWS"] == "PASS",
            self.test_results["EVIDENCE_FIELDS_COMPLETE"] == "PASS",
            self.test_results["QC_FIELDS_PRESENT"] == "PASS"
        ])

        self.test_results["Can_enter_Real_Evidence_Integration"] = "YES" if can_proceed else "NO"

        return self.generate_report()

    def generate_report(self) -> Dict[str, Any]:
        """Generate Choice Adapter Smoke Report."""
        report = {
            "report_title": "Choice Adapter Smoke Report",
            "test_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "test_results": self.test_results,
            "test_details": self.test_details,
            "verdict": self._get_verdict()
        }

        # Print report
        print("\n" + "="*80)
        print("Choice Adapter Smoke Report")
        print("="*80)
        print(f"\nTest Date: {report['test_date']}")
        print("\nTest Results:")
        for key, value in self.test_results.items():
            status_symbol = "✓" if value == "PASS" else ("✗" if value == "FAIL" else "?")
            print(f"  {status_symbol} {key}: {value}")

        print("\n" + "-"*80)
        print("Verdict:")
        print("-"*80)
        print(report["verdict"])

        return report

    def _get_verdict(self) -> str:
        """Get final verdict."""
        lines = []

        if self.test_results["Can_enter_Real_Evidence_Integration"] == "YES":
            lines.append("✅ PASS - Can enter Real Evidence Integration")
            lines.append("")
            lines.append("All 3 capabilities verified:")
            lines.append("  ✓ resolve_company: Real data returned")
            lines.append("  ✓ fetch_announcements: Real data returned")
            lines.append("  ✓ fetch_news: Real data returned")
            lines.append("")
            lines.append("All required fields present:")
            lines.append("  ✓ evidence_level")
            lines.append("  ✓ allowed_use")
            lines.append("  ✓ blocked_fields")
        else:
            lines.append("❌ BLOCKED - Cannot enter Real Evidence Integration")
            lines.append("")
            lines.append("Failed checks:")
            for key, value in self.test_results.items():
                if value == "FAIL" or value == "UNKNOWN":
                    lines.append(f"  ✗ {key}: {value}")

        lines.append("")
        lines.append("Scope:")
        lines.append("  - Adapter probe ONLY")
        lines.append("  - NO full Company Panorama pipeline")
        lines.append("  - NO production visit cards")
        lines.append("  - NO production claims")

        return "\n".join(lines)


def main():
    """Run Choice Adapter Smoke v0."""

    # Test companies
    test_companies = [
        {"name": "宁德时代新能源科技股份有限公司", "type": "listed"},
        {"name": "某AI软件科技有限公司", "type": "private"},
        {"name": "某房地产开发股份有限公司", "type": "bond_issuer"}
    ]

    try:
        probe = ChoiceAdapterProbe()
        report = probe.run_smoke_test(test_companies)

        # Save report
        report_path = "choice_adapter_smoke_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Report saved to: {report_path}")

        # Exit code
        exit_code = 0 if report["test_results"]["Can_enter_Real_Evidence_Integration"] == "YES" else 1
        sys.exit(exit_code)

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
