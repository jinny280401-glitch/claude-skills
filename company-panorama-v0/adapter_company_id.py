#!/usr/bin/env python3
"""
Company Identification Adapter v0

Converts MX MCP Key-Value Format into CompanyIdentificationResult.
Used as company_match_filter BEFORE notice/news evidence enters Trust Gate.

Status:
  PATH CONFIRMED / DESIGN NEXT
  Announcements + News Mapping: DESIGN COMPLETE
  Company Match Filter: UNRESOLVED → BEING DESIGNED
  Real Evidence Integration: NOT AUTHORIZED

Freeze Rule:
  No notice/news record may enter Real Evidence Integration unless
  company_match_confidence is present and above the accepted threshold.

Scope:
  - resolve_company from mx_ashare/mx_comprehensive Key-Value Format
  - company_match_confidence calculation (high/medium/low)
  - Trust Gate routing rules

Not in scope:
  - Company Panorama pipeline
  - Production claims
"""

import os
import json
import re
from typing import Dict, List, Any, Optional
from enum import Enum
import requests


class EntityType(str, Enum):
    LISTED = "listed"
    PRIVATE = "private"
    ISSUER = "issuer"
    UNKNOWN = "unknown"


class CompanyMatchMethod(str, Enum):
    STOCK_CODE_MATCH = "stock_code_match"
    OFFICIAL_ENTITY_ID_MATCH = "official_entity_id_match"
    NORMALIZED_FULL_NAME_MATCH = "normalized_full_name_match"
    SHORT_NAME_MATCH = "short_name_match"
    CONTEXTUAL_WEAK_MATCH = "contextual_weak_match"
    NO_MATCH = "no_match"
    UNKNOWN = "unknown"


class CompanyMatchConfidence:
    """Confidence scoring rules."""

    HIGH_MIN = 0.9
    MEDIUM_MIN = 0.5
    LOW_MAX = 0.49  # Anything below 0.5 is rejected


class TrustGateRoute(str, Enum):
    ELIGIBLE_FACT_INPUT = "eligible_fact_input"
    PENDING_MANUAL_REVIEW = "pending_manual_review"
    REJECT_BEFORE_TRUST_GATE = "reject_before_trust_gate"


class CompanyIdentificationResult:
    """Normalized company identification output."""

    def __init__(
        self,
        company_name: str,
        company_name_normalized: Optional[str] = None,
        stock_code: Optional[str] = None,
        stock_exchange: Optional[str] = None,
        entity_type: EntityType = EntityType.UNKNOWN,
        raw_attributes: Optional[Dict[str, Any]] = None
    ):
        self.query_name = company_name
        self.company_name_normalized = company_name_normalized or company_name
        self.stock_code = stock_code
        self.stock_exchange = stock_exchange
        self.entity_type = entity_type
        self.raw_attributes = raw_attributes or {}
        self.resolution_source: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_name": self.query_name,
            "company_name_normalized": self.company_name_normalized,
            "stock_code": self.stock_code,
            "stock_exchange": self.stock_exchange,
            "entity_type": self.entity_type,
            "raw_attributes": self.raw_attributes,
            "resolution_source": self.resolution_source
        }


class CompanyMatchResult:
    """Result of matching evidence to a company."""

    def __init__(
        self,
        evidence_title: str,
        evidence_type: str,
        confidence: float,
        match_method: CompanyMatchMethod,
        matched_text: Optional[str] = None,
        note: Optional[str] = None,
        resolved_company_name: Optional[str] = None,
        resolved_stock_code: Optional[str] = None
    ):
        self.evidence_title = evidence_title
        self.evidence_type = evidence_type
        self.confidence = confidence
        self.match_method = match_method
        self.matched_text = matched_text
        self.note = note
        self.resolved_company_name = resolved_company_name
        self.resolved_stock_code = resolved_stock_code

        # Determine Trust Gate route
        self.route = self._determine_route()
        self.requires_manual_review = self.route == TrustGateRoute.PENDING_MANUAL_REVIEW

    def _determine_route(self) -> TrustGateRoute:
        """Determine Trust Gate routing based on confidence."""
        if self.confidence >= 0.9:
            return TrustGateRoute.ELIGIBLE_FACT_INPUT
        elif self.confidence >= 0.5:
            return TrustGateRoute.PENDING_MANUAL_REVIEW
        else:
            return TrustGateRoute.REJECT_BEFORE_TRUST_GATE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_match_confidence": self.confidence,
            "company_match_method": self.match_method,
            "company_match_route": self.route,
            "company_match_note": self.note,
            "resolved_company_name": self.resolved_company_name,
            "resolved_stock_code": self.resolved_stock_code,
            "matched_text": self.matched_text,
            "requires_manual_review": self.requires_manual_review
        }


class CompanyIdentificationAdapter:
    """
    Converts MX MCP Key-Value Format into CompanyIdentificationResult.

    Used as pre-filter for notice/news evidence.
    """

    MCP_URL = "https://mxapi.eastmoney.com/mxds/mcp"

    # Attribute keys for extracting normalized info
    ATTR_KEYS_COMPANY_NAME = [
        "公司中文名称", "公司名称", "企业名称", "机构名称",
        "公司全称", "名称", "机构简称"
    ]

    ATTR_KEYS_STOCK_SHORT = [
        "股票简称", "证券简称", "A股简称", "H股简称"
    ]

    ATTR_KEYS_STOCK_CODE = [
        "A股代码", "股票代码", "证券代码", "代码"
    ]

    ATTR_KEYS_ENTITY_TYPE = [
        "公司类型", "企业类型", "上市状态"
    ]

    ATTR_KEYS_CREDIT_CODE = [
        "统一社会信用代码", "注册号"
    ]

    def __init__(self):
        """Initialize with EM_API_KEY."""
        self.api_key = os.getenv("EM_API_KEY")
        if not self.api_key:
            raise ValueError("EM_API_KEY not found")

        self.headers = {
            "em_api_key": self.api_key,
            "Accept": "application/json"
        }
        self._session_initialized = False

    def _ensure_initialized(self):
        """Ensure MCP session is initialized."""
        if self._session_initialized:
            return

        init_payload = {
            "jsonrpc": "2.0", "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "company-id-adapter",
                    "version": "0.1.0"
                }
            }
        }

        response = requests.post(
            self.MCP_URL,
            headers=self.headers,
            json=init_payload,
            timeout=10
        )

        if response.status_code == 200:
            self._session_initialized = True
        else:
            raise ConnectionError(f"Init failed: HTTP {response.status_code}")

    def _call_mcp(self, tool_name: str, query: str, call_id: int) -> Optional[Dict[str, Any]]:
        """Call MX MCP and return parsed JSON."""
        self._ensure_initialized()

        payload = {
            "jsonrpc": "2.0", "id": call_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": {"query": query}
            }
        }

        try:
            response = requests.post(
                self.MCP_URL,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                return None

            data = response.json()
            content = data.get("result", {}).get("content", [])

            if isinstance(content, list):
                texts = [
                    item.get("text", "")
                    for item in content
                    if isinstance(item, dict) and item.get("type") == "text"
                ]
                text = "\n".join(texts)
            else:
                text = str(content)

            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return None

        except Exception as e:
            print(f"  MCP error: {e}")
            return None

    def resolve_company(
        self,
        company_name: str,
        stock_code_hint: Optional[str] = None
    ) -> CompanyIdentificationResult:
        """
        Resolve company from MX MCP Key-Value Format.

        Strategy:
        1. Try mx_ashare_finance_data first (listed companies)
        2. Fall back to mx_comprehensive_finance_data (private/unknown)
        3. Extract normalized name, stock_code, entity_type from attributes
        """
        query = company_name
        if stock_code_hint:
            query = f"{company_name} {stock_code_hint}"
        query += " 公司中文名称 股票简称 上市日期"

        # Step 1: Try A-share
        data = self._call_mcp("mx_ashare_finance_data", query, 1)

        if data and "data" in data:
            result = self._parse_key_value_data(
                data["data"], company_name, "mx_ashare_finance_data"
            )
            if result and result.stock_code:
                return result

        # Step 2: Try comprehensive
        query2 = f"{company_name} 企业基本信息 公司名称"
        data2 = self._call_mcp("mx_comprehensive_finance_data", query2, 2)

        if data2 and "data" in data2:
            result = self._parse_key_value_data(
                data2["data"], company_name, "mx_comprehensive_finance_data"
            )
            if result:
                return result

        # Step 3: Return unresolved
        return CompanyIdentificationResult(
            company_name=company_name,
            entity_type=EntityType.UNKNOWN,
            raw_attributes={"error": "no_data"}
        )

    def _parse_key_value_data(
        self,
        data: List[Dict[str, Any]],
        query_name: str,
        source: str
    ) -> Optional[CompanyIdentificationResult]:
        """Parse MX MCP Key-Value Format into CompanyIdentificationResult."""
        attributes = {}
        stock_code = None
        stock_exchange = None
        company_name_normalized = None
        short_name = None

        for data_item in data:
            if not isinstance(data_item, dict):
                continue

            columns = data_item.get("columns", [])
            items = data_item.get("items", [])

            # Case 1: Company info table - ["指标", "公司A(000001.SZ)", "公司A(HK)"]
            if len(columns) >= 2 and "指标" in columns:
                # Extract stock_code from column header
                stock_code, stock_exchange = self._parse_stock_from_columns(columns)

                # Parse attribute rows
                for row in items:
                    if not isinstance(row, list) or len(row) < 2:
                        continue
                    attr_name = str(row[0])
                    attr_value = str(row[1]) if row[1] is not None else None

                    if attr_value and attr_value != "-":
                        attributes[attr_name] = attr_value

                        # Extract normalized name
                        if attr_name in self.ATTR_KEYS_COMPANY_NAME:
                            company_name_normalized = attr_value

                        # Extract short name
                        if attr_name in self.ATTR_KEYS_STOCK_SHORT:
                            short_name = attr_value

            # Case 2: Enterprise info table - ["机构简称", "华为"]
            elif len(columns) == 2 and columns[0] in ["机构简称", "机构名称"]:
                short_name = columns[1] if len(columns) > 1 else None

                for row in items:
                    if not isinstance(row, list) or len(row) < 2:
                        continue
                    attr_name = str(row[0])
                    attr_value = str(row[1]) if row[1] is not None else None

                    if attr_value:
                        attributes[attr_name] = attr_value

                        if attr_name in self.ATTR_KEYS_COMPANY_NAME:
                            company_name_normalized = attr_value
                        if attr_name in self.ATTR_KEYS_CREDIT_CODE and not stock_code:
                            # Non-listed: use credit code as identifier
                            stock_code = None  # Private company has no stock code
                            company_name_normalized = company_name_normalized or short_name

        # Use short_name as normalized if full name not found
        if not company_name_normalized and short_name:
            company_name_normalized = short_name

        # Determine entity type
        if stock_code:
            entity_type = EntityType.LISTED
        elif company_name_normalized and not stock_code:
            entity_type = EntityType.PRIVATE
        else:
            entity_type = EntityType.UNKNOWN

        if not company_name_normalized:
            return None

        return CompanyIdentificationResult(
            company_name=query_name,
            company_name_normalized=company_name_normalized,
            stock_code=stock_code,
            stock_exchange=stock_exchange,
            entity_type=entity_type,
            raw_attributes=attributes
        )

    def _parse_stock_from_columns(self, columns: List[str]) -> tuple:
        """Extract stock_code and exchange from column headers.

        Example: "宁德时代(300750.SZ)" → ("300750", "SZ")
                 "宁德时代(03750.HK)" → ("03750", "HK")
        """
        for col in columns:
            match = re.search(r'\((\d+)\.(SZ|SH|HK|BJ|NQ)\)', col)
            if match:
                return match.group(1), match.group(2)

        return None, None

    def _title_starts_with(self, title: str, name: str) -> bool:
        """Check if title starts with name (followed by colon, separator, or space).

        Matches patterns like:
        - "宁德时代:H股公告..."
        - "宁德时代 申请电池..."
        - "宁德时代股价波动..."
        """
        if not title or not name:
            return False
        # Remove any whitespace prefix
        t = title.lstrip()
        if t.startswith(name):
            # Followed by colon, space, or title separator chars → likely subject
            after = t[len(name):]
            if not after or after[0] in [':', '：', ' ', '(', '（', '_', '-']:
                return True
            # Also allow "straight" start like "宁德时代申请...", "宁德时代股价..."
            if after[0].isalpha() or after[0].isdigit():
                return True
        return False

    def _title_starts_with_other_company(self, title: str, our_names: List[str]) -> bool:
        """Check if title starts with a DIFFERENT company name.

        Format: "OTHER_CO: our company mentioned in context..."
        This is the classic misattribution pattern.
        """
        if not title or ':' not in title and '：' not in title:
            return False

        # Split at first colon
        for sep in [':', '：']:
            if sep in title:
                prefix = title.split(sep)[0].strip()
                if prefix and not any(name in prefix for name in our_names):
                    return True

        return False

    def match_evidence(
        self,
        company_result: CompanyIdentificationResult,
        evidence_title: str,
        evidence_type: str = "news"
    ) -> CompanyMatchResult:
        """
        Match evidence to resolved company.

        Rules (tightened):
        - HIGH: stock_code, full_name at title start, short_name at title start
        - MEDIUM: short_name appearing in middle of title (not start, not other company prefix)
        - LOW: company only mentioned in context, or another company is the subject
        """

        normalized = company_result.company_name_normalized
        short_name = company_result.raw_attributes.get("股票简称") or company_result.raw_attributes.get("机构简称")
        stock_code = company_result.stock_code

        # Build list of our names for "other company" detection
        our_names = [n for n in [normalized, short_name, company_result.query_name] if n]

        # Rule 1: Explicit stock_code match → HIGH
        if stock_code and stock_code in evidence_title:
            return CompanyMatchResult(
                evidence_title=evidence_title,
                evidence_type=evidence_type,
                confidence=0.95,
                match_method=CompanyMatchMethod.STOCK_CODE_MATCH,
                matched_text=stock_code,
                note=None,
                resolved_company_name=normalized,
                resolved_stock_code=stock_code
            )

        # Rule 2: Normalized full name at title start → HIGH
        # Pattern: "宁德时代新能源科技股份有限公司:H股公告..."
        if normalized and len(normalized) >= 6 and self._title_starts_with(evidence_title, normalized):
            return CompanyMatchResult(
                evidence_title=evidence_title,
                evidence_type=evidence_type,
                confidence=0.93,
                match_method=CompanyMatchMethod.NORMALIZED_FULL_NAME_MATCH,
                matched_text=normalized,
                note=None,
                resolved_company_name=normalized,
                resolved_stock_code=stock_code
            )

        # Rule 3: Short name at title start → HIGH
        # Pattern: "宁德时代:H股公告..." or "宁德时代 申请专利..."
        # This is the standard announcement format: "公司:标题"
        if short_name and len(short_name) >= 2 and self._title_starts_with(evidence_title, short_name):
            return CompanyMatchResult(
                evidence_title=evidence_title,
                evidence_type=evidence_type,
                confidence=0.90,
                match_method=CompanyMatchMethod.SHORT_NAME_MATCH,
                matched_text=short_name,
                note="标题以公司简称开头，符合公告/新闻主体格式",
                resolved_company_name=normalized,
                resolved_stock_code=stock_code
            )

        # Rule 4: Another company is the title subject → LOW (reject)
        # Pattern: "恒翼能:宁德时代既是股东又是客户..."
        if self._title_starts_with_other_company(evidence_title, our_names):
            # Identify the actual subject
            for sep in [':', '：']:
                if sep in evidence_title:
                    other = evidence_title.split(sep)[0].strip()
                    return CompanyMatchResult(
                        evidence_title=evidence_title,
                        evidence_type=evidence_type,
                        confidence=0.30,
                        match_method=CompanyMatchMethod.CONTEXTUAL_WEAK_MATCH,
                        matched_text=other,
                        note=(
                            f"标题主体是「{other}」而非目标公司，"
                            f"目标公司仅被提及/关联"
                        ),
                        resolved_company_name=normalized,
                        resolved_stock_code=stock_code
                    )

        # Rule 5: Short name in middle of title → MEDIUM (pending review)
        if short_name and len(short_name) >= 2 and short_name in evidence_title:
            return CompanyMatchResult(
                evidence_title=evidence_title,
                evidence_type=evidence_type,
                confidence=0.65,
                match_method=CompanyMatchMethod.SHORT_NAME_MATCH,
                matched_text=short_name,
                note=(
                    f"标题含简称「{short_name}」但不在句首，"
                    f"可能是主体也可能是被提及对象，需人工确认"
                ),
                resolved_company_name=normalized,
                resolved_stock_code=stock_code
            )

        # Rule 6: Full name anywhere in title → MEDIUM (unusual: full name not at start)
        if normalized and len(normalized) >= 6 and normalized in evidence_title:
            return CompanyMatchResult(
                evidence_title=evidence_title,
                evidence_type=evidence_type,
                confidence=0.70,
                match_method=CompanyMatchMethod.NORMALIZED_FULL_NAME_MATCH,
                matched_text=normalized,
                note="全称在标题中但不在句首，需确认主体归属",
                resolved_company_name=normalized,
                resolved_stock_code=stock_code
            )

        # Rule 7: Query name match only → LOW (reject)
        query_name = company_result.query_name
        if query_name and len(query_name) >= 2 and query_name in evidence_title:
            return CompanyMatchResult(
                evidence_title=evidence_title,
                evidence_type=evidence_type,
                confidence=0.35,
                match_method=CompanyMatchMethod.CONTEXTUAL_WEAK_MATCH,
                matched_text=query_name,
                note=(
                    f"标题含查询词「{query_name}」，"
                    f"但无法确认主体归属，目标公司可能仅被提及"
                ),
                resolved_company_name=normalized,
                resolved_stock_code=stock_code
            )

        # Rule 8: No match
        return CompanyMatchResult(
            evidence_title=evidence_title,
            evidence_type=evidence_type,
            confidence=0.0,
            match_method=CompanyMatchMethod.NO_MATCH,
            note="标题不含公司任何标识，无法建立主体关联",
            resolved_company_name=normalized,
            resolved_stock_code=stock_code
        )

    def resolve_and_match_batch(
        self,
        company_name: str,
        stock_code_hint: Optional[str],
        evidence_records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Full pipeline: resolve → match each evidence record.

        Returns enrichment data for EvidenceRecord.
        """
        print(f"\n[Company ID Adapter] Resolving: {company_name}")

        company_result = self.resolve_company(company_name, stock_code_hint)
        print(f"  Normalized: {company_result.company_name_normalized}")
        print(f"  Stock Code: {company_result.stock_code or 'N/A'}")
        print(f"  Entity Type: {company_result.entity_type}")

        match_results = []
        for record in evidence_records:
            title = record.get("title") or record.get("样本标题", "")
            etype = record.get("evidence_type", "unknown")

            match = self.match_evidence(company_result, title, etype)
            match_results.append({
                "evidence_title": title[:80],
                **match.to_dict()
            })

        high_count = sum(1 for m in match_results if m["company_match_confidence"] >= 0.9)
        medium_count = sum(1 for m in match_results if 0.5 <= m["company_match_confidence"] < 0.9)
        low_count = sum(1 for m in match_results if 0 < m["company_match_confidence"] < 0.5)
        reject_count = sum(1 for m in match_results if m["company_match_confidence"] == 0.0)

        print(f"  Match Results:")
        print(f"    High (eligible_fact_input):   {high_count}")
        print(f"    Medium (pending_manual_review): {medium_count}")
        print(f"    Low (reject_before_trust_gate): {low_count}")
        print(f"    No Match (reject):            {reject_count}")

        return {
            "company_identification": company_result.to_dict(),
            "match_results": match_results,
            "summary": {
                "total": len(match_results),
                "high_confidence": high_count,
                "medium_confidence": medium_count,
                "low_confidence": low_count,
                "rejected": reject_count
            }
        }


def main():
    """CLI: Test Company Identification Adapter."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python adapter_company_id.py <company_name> [stock_code]")
        sys.exit(1)

    company_name = sys.argv[1]
    stock_code = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        adapter = CompanyIdentificationAdapter()

        # Step 1: Resolve
        print("="*80)
        print("Company Identification Adapter v0")
        print("="*80)

        result = adapter.resolve_company(company_name, stock_code)
        print(f"\n[Resolve Result]")
        print(f"  Query: {result.query_name}")
        print(f"  Normalized: {result.company_name_normalized}")
        print(f"  Stock Code: {result.stock_code or 'N/A'}")
        print(f"  Exchange: {result.stock_exchange or 'N/A'}")
        print(f"  Entity Type: {result.entity_type}")
        print(f"  Attributes: {json.dumps(result.raw_attributes, ensure_ascii=False, indent=2)[:500]}")

        # Step 2: Test match against known problematic cases
        print(f"\n[Match Test - Real Evidence from Phase 2]")

        test_evidence = [
            ("恒翼能:宁德时代既是股东又是客户,ACC自身难保,回款差,高负债_财经头条_新浪财经", "news"),
            ("宁德时代:H股公告(截至2026年6月30日止股份发行人的证券变动月报表)", "announcement"),
            ("宁德时代股价波动背后的市场信号分析_公司_行业_新能源", "news"),
            ("宁德时代申请电池装置专利提升底板刚度性能_投资_企业_箱体", "news"),
            ("宁德时代入股开洋船舶，布局船舶制造市场_股东_技术_电船", "news"),
            ("某房地产开发公司季度报告", "announcement"),
        ]

        for title, etype in test_evidence:
            match = adapter.match_evidence(result, title, etype)
            route_symbol = {
                TrustGateRoute.ELIGIBLE_FACT_INPUT: "✓",
                TrustGateRoute.PENDING_MANUAL_REVIEW: "⚠",
                TrustGateRoute.REJECT_BEFORE_TRUST_GATE: "✗"
            }
            print(f"  {route_symbol[match.route]} [{match.confidence:.2f}] {match.match_method}")
            print(f"    {title[:70]}")
            if match.note:
                print(f"    Note: {match.note}")
            print()

        # Save
        output = {
            "adapter": "company-identification-adapter-v0",
            "resolution": result.to_dict(),
            "match_tests": [
                {
                    "title": title,
                    "type": etype,
                    **adapter.match_evidence(result, title, etype).to_dict()
                }
                for title, etype in test_evidence
            ]
        }

        with open("adapter_company_id_output.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"✅ Saved to: adapter_company_id_output.json")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
