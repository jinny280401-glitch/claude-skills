#!/usr/bin/env python3
"""
Announcements + News Adapter Mapping v0

Converts MX MCP List Format (columns + items) into Trust Gate EvidenceRecord[].
Does NOT include Company Identification. Does NOT connect to full pipeline.

Scope:
  - mx_finance_search_notice → EvidenceRecord[] (evidence_type: announcement)
  - mx_finance_search_news   → EvidenceRecord[] (evidence_type: news)

Not in scope:
  - resolve_company
  - Company Panorama pipeline
  - Production claims
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import requests


class EvidenceLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class EvidenceType(str, Enum):
    ANNOUNCEMENT = "announcement"
    NEWS = "news"


class AdapterStatus(str, Enum):
    OK = "ok"
    PARTIAL = "partial"
    REJECTED = "rejected"


class SourceRank:
    """Source ranking rules for announcements and news."""

    # Announcement source classification
    ANNOUNCEMENT_OFFICIAL_KEYWORDS = [
        "巨潮", "上交所", "深交所", "港交所", "交易所",
        "证监会", "官方", "cninfo", "sse", "szse"
    ]

    ANNOUNCEMENT_REGULATORY_KEYWORDS = [
        "监管", "处罚", "问询", "询问函", "警示函", "立案"
    ]

    # News source classification
    MAINSTREAM_MEDIA_KEYWORDS = [
        "新华社", "人民网", "证券时报", "中国证券报", "上海证券报",
        "第一财经", "财新", "经济观察报", "21世纪经济报道",
        "每日经济新闻", "中国基金报", "界面新闻"
    ]

    INDUSTRY_MEDIA_KEYWORDS = [
        "36氪", "虎嗅", "钛媒体", "证券之星", "东方财富",
        "新浪财经", "雪球", "同花顺", "wind", "华尔街见闻"
    ]

    SELF_MEDIA_KEYWORDS = [
        "搜狐", "网易", "百家号", "头条号", "知乎",
        "微信公众号", "微博", "抖音"
    ]

    @classmethod
    def rank_announcement_source(cls, source: str) -> str:
        """Rank announcement source."""
        source_lower = (source or "").lower()

        for keyword in cls.ANNOUNCEMENT_OFFICIAL_KEYWORDS:
            if keyword.lower() in source_lower:
                return "official_or_exchange"

        for keyword in cls.ANNOUNCEMENT_REGULATORY_KEYWORDS:
            if keyword.lower() in source_lower:
                return "regulatory"

        # Default for notice tool: assume company notice
        return "company_notice"

    @classmethod
    def rank_news_source(cls, source: str) -> str:
        """Rank news source and determine evidence_level."""
        source_text = source or ""

        for keyword in cls.MAINSTREAM_MEDIA_KEYWORDS:
            if keyword in source_text:
                return "mainstream_media"

        for keyword in cls.INDUSTRY_MEDIA_KEYWORDS:
            if keyword in source_text:
                return "industry_media"

        for keyword in cls.SELF_MEDIA_KEYWORDS:
            if keyword in source_text:
                return "self_media"

        return "unknown"

    @classmethod
    def news_source_to_evidence_level(cls, source_rank: str) -> EvidenceLevel:
        """Convert news source rank to evidence level."""
        if source_rank in ["mainstream_media", "industry_media"]:
            return EvidenceLevel.MEDIUM
        else:
            return EvidenceLevel.LOW


class BlockedFieldsDetector:
    """Detect blocked_fields in evidence content."""

    VALUATION_PATTERNS = [
        "估值", "目标价", "合理市值", "市值空间", "市盈率",
        "市净率", "P/E", "PB", "EV/EBITDA"
    ]

    ADVICE_PATTERNS = [
        "买入", "卖出", "增持", "减持", "强烈推荐", "建议",
        "加仓", "减仓", "配置比例", "仓位", "评级"
    ]

    FINANCIAL_CLAIMS_PATTERNS = [
        "营收", "收入", "利润", "净利润", "毛利率", "ROE"
    ]

    @classmethod
    def detect_announcement_blocked(cls, title: str, summary: str = "") -> Dict[str, Any]:
        """Detect blocked fields in announcement content."""
        content = (title or "") + " " + (summary or "")
        blocked = []

        # Announcements default blocked fields
        announcement_defaults = [
            "valuation",
            "investment_advice",
            "revenue_profit_if_not_explicit",
            "conclusion_on_risk_fact"
        ]

        # Additional scan
        content_lower = content.lower()

        for pattern in cls.VALUATION_PATTERNS:
            if pattern.lower() in content_lower:
                if "valuation" not in blocked:
                    blocked.append("valuation")

        for pattern in cls.ADVICE_PATTERNS:
            if pattern.lower() in content_lower:
                if "investment_advice" not in blocked:
                    blocked.append("investment_advice")

        # Merge defaults
        for default in announcement_defaults:
            if default not in blocked:
                blocked.append(default)

        return {
            "needs_blocked_fields": "YES" if blocked else "NO",
            "blocked_fields": blocked
        }

    @classmethod
    def detect_news_blocked(cls, title: str, summary: str = "") -> Dict[str, Any]:
        """Detect blocked fields in news content."""
        content = (title or "") + " " + (summary or "")
        blocked = []

        # News default blocked fields
        news_defaults = [
            "confirmed_fact_if_single_source",
            "valuation",
            "investment_advice",
            "financial_numbers_unless_official",
            "conclusion_on_risk_fact"
        ]

        content_lower = content.lower()

        for pattern in cls.VALUATION_PATTERNS:
            if pattern.lower() in content_lower:
                if "valuation" not in blocked:
                    blocked.append("valuation")

        for pattern in cls.ADVICE_PATTERNS:
            if pattern.lower() in content_lower:
                if "investment_advice" not in blocked:
                    blocked.append("investment_advice")

        for pattern in cls.FINANCIAL_CLAIMS_PATTERNS:
            if pattern.lower() in content_lower:
                if "financial_numbers_unless_official" not in blocked:
                    blocked.append("financial_numbers_unless_official")

        for default in news_defaults:
            if default not in blocked:
                blocked.append(default)

        return {
            "needs_blocked_fields": "YES" if blocked else "NO",
            "blocked_fields": blocked
        }


class AnnouncementsNewsAdapter:
    """
    Announcements + News Adapter Mapping v0.

    Converts MX MCP List Format to EvidenceRecord[].
    Does NOT perform company identification.
    """

    # MX MCP Server
    MCP_URL = "https://mxapi.eastmoney.com/mxds/mcp"

    def __init__(self):
        """Initialize with EM_API_KEY from environment."""
        self.api_key = os.getenv("EM_API_KEY")
        if not self.api_key:
            raise ValueError("EM_API_KEY not found. Please set: export EM_API_KEY='your_key'")

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
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "company-panorama-adapter",
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
            raise ConnectionError(
                f"Failed to initialize MCP: HTTP {response.status_code}"
            )

    def _call_mcp_tool(
        self,
        tool_name: str,
        query: str,
        call_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Call MX MCP tool and extract raw items."""
        self._ensure_initialized()

        payload = {
            "jsonrpc": "2.0",
            "id": call_id,
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

            # Extract content text
            result = data.get("result", {})
            content = result.get("content", [])

            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                texts = []
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        texts.append(item.get("text", ""))
                text = "\n".join(texts)
            else:
                text = json.dumps(content, ensure_ascii=False)

            # Parse inner JSON
            try:
                inner_data = json.loads(text)
            except json.JSONDecodeError:
                return None

            # Extract from data array
            if not isinstance(inner_data, dict) or "data" not in inner_data:
                return None

            data_list = inner_data["data"]
            if not isinstance(data_list, list):
                return None

            raw_items = []

            for data_item in data_list:
                if not isinstance(data_item, dict):
                    continue

                columns = data_item.get("columns", [])
                items = data_item.get("items", [])

                for row in items:
                    if not isinstance(row, list):
                        continue

                    # Map columns → dict
                    row_dict = {}
                    for i, col in enumerate(columns):
                        if i < len(row):
                            row_dict[col] = row[i]

                    raw_items.append(row_dict)

            return raw_items

        except Exception as e:
            print(f"  MCP call error: {e}")
            return None

    def _generate_evidence_id(
        self,
        evidence_type: str,
        company_name: str,
        date: Optional[str],
        title: str,
        url: Optional[str]
    ) -> str:
        """Generate evidence_id: {type}:{company}:{date}:{hash}"""
        date_str = (date or "unknown")[:10]
        hash_input = (title or "") + (url or "")
        hash_str = hashlib.sha256(hash_input.encode()).hexdigest()[:12]

        safe_company = company_name.replace(":", "_").replace("/", "_")
        return f"{evidence_type}:{safe_company}:{date_str}:{hash_str}"

    def _normalize_announcement_record(
        self,
        raw_item: Dict[str, Any],
        company_name: str,
        stock_code: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Normalize a single announcement item into EvidenceRecord."""
        title = raw_item.get("标题")
        summary = raw_item.get("摘要", "")
        date = raw_item.get("发布时间")
        source = raw_item.get("来源")
        url = raw_item.get("跳转链接")

        # Adapter status check
        if not title:
            return {
                "adapter_status": AdapterStatus.REJECTED,
                "rejection_reason": "missing_title",
                "raw_source": raw_item
            }

        if not url:
            return {
                "adapter_status": AdapterStatus.REJECTED,
                "rejection_reason": "missing_url",
                "raw_source": raw_item
            }

        # Source ranking
        source_rank = SourceRank.rank_announcement_source(source)

        # Blocked fields
        blocked = BlockedFieldsDetector.detect_announcement_blocked(title, summary)

        # Allowed use (announcement defaults)
        allowed_use = [
            "company_profile",
            "recent_events"
        ]

        # Add risk_signal if relevant
        risk_keywords = ["减持", "质押", "担保", "诉讼", "处罚", "问询", "警示", "立案"]
        if any(kw in (title or "") for kw in risk_keywords):
            allowed_use.append("risk_signal_if_supported")

        evidence_id = self._generate_evidence_id(
            EvidenceType.ANNOUNCEMENT,
            company_name,
            date,
            title,
            url
        )

        return {
            "evidence_id": evidence_id,
            "evidence_type": EvidenceType.ANNOUNCEMENT,
            "title": title,
            "date": date,
            "source": source,
            "url": url,
            "source_rank": source_rank,
            "evidence_level": EvidenceLevel.HIGH,  # Default High for announcements
            "allowed_use": allowed_use,
            "needs_blocked_fields": blocked["needs_blocked_fields"],
            "blocked_fields": blocked["blocked_fields"],
            "raw_source": raw_item,
            "adapter_status": AdapterStatus.OK
        }

    def _normalize_news_record(
        self,
        raw_item: Dict[str, Any],
        company_name: str,
        stock_code: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Normalize a single news item into EvidenceRecord."""
        title = raw_item.get("标题")
        summary = raw_item.get("摘要", "")
        date = raw_item.get("发布时间")
        source = raw_item.get("来源")
        url = raw_item.get("跳转链接")

        # Adapter status check
        if not title:
            return {
                "adapter_status": AdapterStatus.REJECTED,
                "rejection_reason": "missing_title",
                "raw_source": raw_item
            }

        if not url:
            return {
                "adapter_status": AdapterStatus.REJECTED,
                "rejection_reason": "missing_url",
                "raw_source": raw_item
            }

        # Source ranking for news
        source_rank = SourceRank.rank_news_source(source)
        evidence_level = SourceRank.news_source_to_evidence_level(source_rank)

        # Blocked fields
        blocked = BlockedFieldsDetector.detect_news_blocked(title, summary)

        # Allowed use (news defaults)
        allowed_use = [
            "recent_events",
            "background_context"
        ]

        # Add risk_signal_candidate if relevant
        risk_keywords = ["风险", "波动", "下滑", "亏损", "调查", "纠纷", "裁员"]
        if any(kw in (title or "") for kw in risk_keywords):
            allowed_use.append("risk_signal_candidate")

        evidence_id = self._generate_evidence_id(
            EvidenceType.NEWS,
            company_name,
            date,
            title,
            url
        )

        return {
            "evidence_id": evidence_id,
            "evidence_type": EvidenceType.NEWS,
            "title": title,
            "date": date,
            "source": source,
            "url": url,
            "source_rank": source_rank,
            "evidence_level": evidence_level,
            "allowed_use": allowed_use,
            "needs_blocked_fields": blocked["needs_blocked_fields"],
            "blocked_fields": blocked["blocked_fields"],
            "raw_source": raw_item,
            "adapter_status": AdapterStatus.OK
        }

    def fetch_announcements(
        self,
        company_name: str,
        stock_code: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch and normalize announcements.

        Args:
            company_name: Target company name
            stock_code: Stock code (if known)
            limit: Max records to return

        Returns:
            TrustGateInput envelope
        """
        query = f"{company_name}"
        if stock_code:
            query += f" {stock_code}"
        query += " 公告"

        print(f"[Announcements Adapter] Fetching for: {company_name}")
        print(f"  Query: {query}")

        raw_items = self._call_mcp_tool("mx_finance_search_notice", query, 1)

        if not raw_items:
            return self._empty_envelope(
                company_name, stock_code, "mx_finance_search_notice",
                "no_data"
            )

        records = []
        for raw_item in raw_items[:limit]:
            record = self._normalize_announcement_record(
                raw_item, company_name, stock_code
            )
            if record:
                records.append(record)

        ok_count = sum(1 for r in records if r.get("adapter_status") == AdapterStatus.OK)
        rejected_count = sum(1 for r in records if r.get("adapter_status") == AdapterStatus.REJECTED)

        print(f"  Records: {len(records)} (ok: {ok_count}, rejected: {rejected_count})")

        return self._build_envelope(
            company_name, stock_code,
            "mx_finance_search_notice",
            records
        )

    def fetch_news(
        self,
        company_name: str,
        stock_code: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fetch and normalize news.

        Args:
            company_name: Target company name
            stock_code: Stock code (if known)
            limit: Max records to return

        Returns:
            TrustGateInput envelope
        """
        query = f"{company_name}"
        if stock_code:
            query += f" {stock_code}"
        query += " 最新新闻"

        print(f"[News Adapter] Fetching for: {company_name}")
        print(f"  Query: {query}")

        raw_items = self._call_mcp_tool("mx_finance_search_news", query, 2)

        if not raw_items:
            return self._empty_envelope(
                company_name, stock_code, "mx_finance_search_news",
                "no_data"
            )

        records = []
        for raw_item in raw_items[:limit]:
            record = self._normalize_news_record(
                raw_item, company_name, stock_code
            )
            if record:
                records.append(record)

        ok_count = sum(1 for r in records if r.get("adapter_status") == AdapterStatus.OK)
        rejected_count = sum(1 for r in records if r.get("adapter_status") == AdapterStatus.REJECTED)

        print(f"  Records: {len(records)} (ok: {ok_count}, rejected: {rejected_count})")

        medium_count = sum(1 for r in records if r.get("evidence_level") == EvidenceLevel.MEDIUM)
        low_count = sum(1 for r in records if r.get("evidence_level") == EvidenceLevel.LOW)

        print(f"  Evidence Level: Medium: {medium_count}, Low: {low_count}")

        return self._build_envelope(
            company_name, stock_code,
            "mx_finance_search_news",
            records
        )

    def _empty_envelope(
        self,
        company_name: str,
        stock_code: Optional[str],
        source_tool: str,
        reason: str
    ) -> Dict[str, Any]:
        """Build empty TrustGateInput envelope."""
        return {
            "company_name": company_name,
            "stock_code": stock_code,
            "source_tool": source_tool,
            "adapter_version": "notice-news-adapter-mapping-v0",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "records": [],
            "adapter_summary": {
                "total": 0,
                "ok": 0,
                "rejected": 0,
                "rejection_reason": reason
            },
            "unresolved": {
                "company_identification": True
            }
        }

    def _build_envelope(
        self,
        company_name: str,
        stock_code: Optional[str],
        source_tool: str,
        records: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build TrustGateInput envelope."""
        ok = [r for r in records if r.get("adapter_status") == AdapterStatus.OK]
        rejected = [r for r in records if r.get("adapter_status") == AdapterStatus.REJECTED]

        return {
            "company_name": company_name,
            "stock_code": stock_code,
            "source_tool": source_tool,
            "adapter_version": "notice-news-adapter-mapping-v0",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "records": records,
            "adapter_summary": {
                "total": len(records),
                "ok": len(ok),
                "rejected": len(rejected)
            },
            "unresolved": {
                "company_identification": True
            }
        }


def main():
    """CLI entry point for testing."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python adapter_notice_news.py <company_name> [stock_code]")
        print("\nExample:")
        print("  python adapter_notice_news.py '宁德时代' 300750")
        sys.exit(1)

    company_name = sys.argv[1]
    stock_code = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        adapter = AnnouncementsNewsAdapter()

        # Fetch announcements
        print("\n" + "="*80)
        print("Announcements Adapter")
        print("="*80)
        announcement_envelope = adapter.fetch_announcements(
            company_name=company_name,
            stock_code=stock_code,
            limit=5
        )

        print(f"\n[Envelope Summary]")
        print(f"  Total: {announcement_envelope['adapter_summary']['total']}")
        print(f"  OK: {announcement_envelope['adapter_summary']['ok']}")
        print(f"  Rejected: {announcement_envelope['adapter_summary']['rejected']}")

        # Save announcements
        with open("adapter_announcements_output.json", "w", encoding="utf-8") as f:
            json.dump(announcement_envelope, f, ensure_ascii=False, indent=2)
        print(f"  Saved to: adapter_announcements_output.json")

        # Fetch news
        print("\n" + "="*80)
        print("News Adapter")
        print("="*80)
        news_envelope = adapter.fetch_news(
            company_name=company_name,
            stock_code=stock_code,
            limit=5
        )

        print(f"\n[Envelope Summary]")
        print(f"  Total: {news_envelope['adapter_summary']['total']}")
        print(f"  OK: {news_envelope['adapter_summary']['ok']}")
        print(f"  Rejected: {news_envelope['adapter_summary']['rejected']}")

        # Save news
        with open("adapter_news_output.json", "w", encoding="utf-8") as f:
            json.dump(news_envelope, f, ensure_ascii=False, indent=2)
        print(f"  Saved to: adapter_news_output.json")

        print("\n✅ Adapter mapping complete")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
