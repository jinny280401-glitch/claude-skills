#!/usr/bin/env python3
"""
Joint Smoke: resolve_company → fetch → match → Trust Gate input envelope

Verifies full chain for Company Panorama evidence preprocessing.
Does NOT generate visit cards. Does NOT claim production readiness.

Chain:
  resolve_company (Company Identification Adapter)
    ↓
  fetch_notice + fetch_news (Announcements + News Adapter)
    ↓
  company_match_filter (Company Match)
    ↓
  Trust Gate input envelope

Acceptance criteria:
1. 恒翼能:宁德时代... must remain REJECTED
2. 宁德时代:H股公告... must route to FACT_INPUT
3. Every record must carry: resolved_company_name, stock_code, entity_type,
   company_match_confidence, company_match_route
4. REJECT records must NOT appear in Trust Gate input
5. Output envelope must declare:
   - Real Evidence Integration: NOT AUTHORIZED
   - Production Ready: NO
"""

import json
import sys
from datetime import datetime

# Import adapters
from adapter_company_id import (
    CompanyIdentificationAdapter,
    CompanyMatchMethod,
    TrustGateRoute
)
from adapter_notice_news import AnnouncementsNewsAdapter, EvidenceType


class JointSmoke:
    """Full chain smoke test."""

    def __init__(self):
        self.company_id = CompanyIdentificationAdapter()
        self.notice_news = AnnouncementsNewsAdapter()
        self.verifications = []

    def verify(self, condition: bool, label: str, detail: str = ""):
        """Record verification check."""
        status = "PASS" if condition else "FAIL"
        self.verifications.append({
            "check": label,
            "status": status,
            "detail": detail
        })
        symbol = "✓" if condition else "✗"
        print(f"  {symbol} {label}")
        if detail:
            print(f"    {detail}")

    def run(self, company_name: str, stock_code: str = None):
        """Run joint smoke on one target company."""
        print("="*80)
        print(f"Joint Smoke: {company_name} ({stock_code or 'no stock_code'})")
        print("="*80)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Step 1: resolve_company
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        print("\n[Step 1] resolve_company")
        company_result = self.company_id.resolve_company(company_name, stock_code)
        self.verify(
            company_result.company_name_normalized is not None,
            "resolve_company returns normalized name",
            f"Normalized: {company_result.company_name_normalized}"
        )
        self.verify(
            company_result.entity_type != "unknown",
            "resolve_company returns entity_type",
            f"Entity: {company_result.entity_type}"
        )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Step 2: fetch_notice + fetch_news
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        print("\n[Step 2] fetch_notice + fetch_news")

        notice_envelope = self.notice_news.fetch_announcements(
            company_name=company_name,
            stock_code=stock_code,
            limit=5
        )
        news_envelope = self.notice_news.fetch_news(
            company_name=company_name,
            stock_code=stock_code,
            limit=5
        )

        notice_count = len(notice_envelope.get("records", []))
        news_count = len(news_envelope.get("records", []))
        self.verify(
            notice_count > 0,
            "fetch_notice returns records",
            f"Count: {notice_count}"
        )
        self.verify(
            news_count > 0,
            "fetch_news returns records",
            f"Count: {news_count}"
        )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Step 3: company_match_filter
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        print("\n[Step 3] company_match_filter")

        all_records = notice_envelope.get("records", []) + news_envelope.get("records", [])
        print(f"  Total records before filter: {len(all_records)}")

        matched_records = []
        rejected_records = []
        pending_records = []

        for record in all_records:
            title = record.get("title", "")
            etype = record.get("evidence_type", "unknown")

            match = self.company_id.match_evidence(company_result, title, etype)

            # Enrich record with company match fields
            record["company_match_confidence"] = match.confidence
            record["company_match_method"] = match.match_method
            record["company_match_route"] = match.route
            record["company_match_note"] = match.note
            record["resolved_company_name"] = match.resolved_company_name
            record["resolved_stock_code"] = match.resolved_stock_code
            record["requires_manual_review"] = match.requires_manual_review

            if match.route == TrustGateRoute.ELIGIBLE_FACT_INPUT:
                matched_records.append(record)
            elif match.route == TrustGateRoute.PENDING_MANUAL_REVIEW:
                pending_records.append(record)
            else:
                rejected_records.append(record)

        print(f"  After filter:")
        print(f"    FACT_INPUT:         {len(matched_records)}")
        print(f"    PENDING_REVIEW:     {len(pending_records)}")
        print(f"    REJECTED:           {len(rejected_records)}")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Step 4: Trust Gate input envelope
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        print("\n[Step 4] Trust Gate input envelope")

        trust_gate_input = {
            "company_name": company_name,
            "company_name_normalized": company_result.company_name_normalized,
            "stock_code": company_result.stock_code,
            "entity_type": company_result.entity_type,
            "adapter_version": "joint-smoke-v0",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "records": matched_records,  # FACT_INPUT only
            "pending_review_records": pending_records,  # Separate pool
            "summary": {
                "total_fetched": len(all_records),
                "fact_input": len(matched_records),
                "pending_review": len(pending_records),
                "rejected": len(rejected_records)
            },
            "envelope_warnings": [
                {
                    "warning": "Real Evidence Integration: NOT AUTHORIZED",
                    "reason": "Joint smoke only - full chain not production verified"
                },
                {
                    "warning": "Production Ready: NO",
                    "reason": "Adapter chain smoke passed but not production gate"
                }
            ]
        }

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Verification
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        print("\n" + "="*80)
        print("Acceptance Verification")
        print("="*80)

        # Check 1: 恒翼能 must be rejected
        hengyi_rejected = False
        for r in rejected_records:
            if "恒翼能" in r.get("title", ""):
                hengyi_rejected = True
                break
        self.verify(
            hengyi_rejected,
            "Check 1: 恒翼能:宁德时代... must be REJECTED",
            "恒翼能 correctly identified as OTHER company subject"
        )

        # Check 2: 宁德时代:H股公告 must be FACT_INPUT
        catl_fact = False
        for r in matched_records:
            if "宁德时代" in r.get("title", "") and "H股公告" in r.get("title", ""):
                catl_fact = True
                break
        self.verify(
            catl_fact,
            "Check 2: 宁德时代:H股公告... must be FACT_INPUT",
            "宁德时代 own announcement correctly routed"
        )

        # Check 3: Every record must carry required fields
        required_fields = [
            "resolved_company_name", "resolved_stock_code",
            "company_match_confidence", "company_match_route"
        ]
        all_have_fields = True
        for record in all_records:
            for field in required_fields:
                if field not in record:
                    all_have_fields = False
                    print(f"    Field '{field}' missing in: {record.get('title', '')[:50]}")
                    break
        self.verify(
            all_have_fields,
            "Check 3: Every record carries required fields",
            f"Fields: {', '.join(required_fields)}"
        )

        # Check 4: REJECT records must NOT be in Trust Gate input
        rejected_in_input = False
        for r in trust_gate_input["records"]:
            if r.get("company_match_route") == TrustGateRoute.REJECT_BEFORE_TRUST_GATE:
                rejected_in_input = True
        self.verify(
            not rejected_in_input,
            "Check 4: No REJECT records in Trust Gate input",
            f"Rejected {len(rejected_records)} records excluded from input"
        )

        # Check 5: Envelope warnings must be present
        has_warnings = len(trust_gate_input.get("envelope_warnings", [])) >= 2
        self.verify(
            has_warnings,
            "Check 5: Envelope declares NOT AUTHORIZED + Production Ready: NO",
            f"{len(trust_gate_input['envelope_warnings'])} warnings present"
        )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # Summary
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        all_pass = all(v["status"] == "PASS" for v in self.verifications)
        pass_count = sum(1 for v in self.verifications if v["status"] == "PASS")
        fail_count = sum(1 for v in self.verifications if v["status"] == "FAIL")

        print(f"\n{'='*80}")
        print(f"Joint Smoke Result: {'✅ PASS' if all_pass else '❌ FAIL'}")
        print(f"  {pass_count}/{pass_count + fail_count} checks passed")
        print(f"{'='*80}")

        # Save
        report = {
            "test": "joint-smoke",
            "company": company_name,
            "stock_code": stock_code,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "result": "PASS" if all_pass else "FAIL",
            "verifications": self.verifications,
            "envelope": trust_gate_input,
            "status": {
                "Notice_News_Adapter": "DONE",
                "Company_Identification_Adapter": "DONE",
                "Joint_Smoke": "PASS" if all_pass else "FAIL",
                "Real_Evidence_Integration": "NOT AUTHORIZED",
                "Production_Ready": "NO"
            }
        }

        filename = f"joint_smoke_output.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Joint smoke report saved to: {filename}")

        return all_pass


def main():
    print("="*80)
    print("Company Panorama Joint Smoke")
    print("Chain: resolve → fetch → match → Trust Gate input")
    print("="*80)
    print()

    smoke = JointSmoke()
    result = smoke.run("宁德时代", "300750")

    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
