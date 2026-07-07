#!/usr/bin/env python3
"""
Choice/MX Adapter Smoke v0 - Phase 1

Scope: Verify MCP Server connectivity, auth, and tool discovery ONLY.
Does NOT test resolve_company/announcements/news until tool contract is confirmed.

Status Layers:
- MX MCP itself: PASS (previously verified)
- Codex config layer: PASS (previously verified)
- Raw MCP tools/call: PASS (600519 tested)
- Vera / Feishu runtime: NOT PROVEN
- Company Panorama evidence: NOT PROVEN

Phase 1 Goals:
1. CONNECTIVITY - MCP Server reachable
2. AUTH - EM_API_KEY accepted
3. TOOL_DISCOVERY - Get available tool names
4. SAMPLE_CALL - One minimal query (if tool contract clear)
"""

import os
import sys
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime


class ChoiceMXAdapterPhase1:
    """Phase 1: Connectivity, Auth, Tool Discovery only."""

    def __init__(self):
        """Initialize with EM_API_KEY."""
        self.api_key = os.getenv("EM_API_KEY")
        if not self.api_key:
            raise ValueError("EM_API_KEY not found. Please set: export EM_API_KEY='your_key'")

        # Mask key for logging
        self.masked_key = f"{self.api_key[:3]}...{self.api_key[-3:]}"

        # MX MCP Server
        self.mcp_url = "https://mxapi.eastmoney.com/mxds/mcp"
        self.headers = {
            "em_api_key": self.api_key,
            "Accept": "application/json"
        }

        self.test_results = {
            "CONNECTIVITY": "UNKNOWN",
            "AUTH": "UNKNOWN",
            "TOOL_DISCOVERY": "UNKNOWN",
            "SAMPLE_CALL": "NOT TESTED",
            "RESOLVE_COMPANY": "NOT TESTED",
            "ANNOUNCEMENTS": "NOT TESTED",
            "NEWS": "NOT TESTED",
            "EVIDENCE_FIELDS_COMPLETE": "NOT TESTED",
            "QC_FIELDS_PRESENT": "NOT TESTED",
            "Can_enter_Real_Evidence_Integration": "NO"
        }

        self.discovered_tools = []
        self.test_details = []

    def test_connectivity(self) -> bool:
        """Test 1: MCP Server connectivity with initialize."""
        print("\n[Test 1/4] Testing Connectivity...")
        print(f"  MCP URL: {self.mcp_url}")
        print(f"  API Key: {self.masked_key}")

        try:
            # MCP requires initialize first
            response = requests.post(
                self.mcp_url,
                headers=self.headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "company-panorama-test",
                            "version": "0.1.0"
                        }
                    }
                },
                timeout=10
            )

            self.test_details.append({
                "test": "connectivity",
                "status_code": response.status_code,
                "response_size": len(response.content)
            })

            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    self.test_results["CONNECTIVITY"] = "PASS"
                    print("  ✓ Connectivity: PASS")
                    print(f"    Server: {data['result'].get('serverInfo', {}).get('name', 'unknown')}")
                    print(f"    Protocol: {data['result'].get('protocolVersion', 'unknown')}")
                    return True
                else:
                    self.test_results["CONNECTIVITY"] = "FAIL"
                    print(f"  ✗ Connectivity: FAIL (unexpected response)")
                    return False
            else:
                self.test_results["CONNECTIVITY"] = "FAIL"
                print(f"  ✗ Connectivity: FAIL (HTTP {response.status_code})")
                return False

        except Exception as e:
            self.test_results["CONNECTIVITY"] = "FAIL"
            self.test_details.append({
                "test": "connectivity",
                "error": str(e)
            })
            print(f"  ✗ Connectivity: FAIL ({e})")
            return False

    def test_auth(self) -> bool:
        """Test 2: Authentication."""
        print("\n[Test 2/4] Testing Authentication...")

        try:
            # Use initialize to verify auth
            response = requests.post(
                self.mcp_url,
                headers=self.headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "company-panorama-test",
                            "version": "0.1.0"
                        }
                    }
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    self.test_results["AUTH"] = "PASS"
                    print("  ✓ Authentication: PASS")
                    return True
                else:
                    self.test_results["AUTH"] = "UNKNOWN"
                    print("  ? Authentication: UNKNOWN (unexpected format)")
                    return False
            elif response.status_code in [401, 403]:
                self.test_results["AUTH"] = "FAIL"
                print(f"  ✗ Authentication: FAIL ({response.status_code})")
                return False
            else:
                self.test_results["AUTH"] = "UNKNOWN"
                print(f"  ? Authentication: UNKNOWN (HTTP {response.status_code})")
                return False

        except Exception as e:
            self.test_results["AUTH"] = "FAIL"
            print(f"  ✗ Authentication: FAIL ({e})")
            return False

    def test_tool_discovery(self) -> bool:
        """Test 3: Tool Discovery."""
        print("\n[Test 3/4] Testing Tool Discovery...")

        try:
            response = requests.post(
                self.mcp_url,
                headers=self.headers,
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                },
                timeout=10
            )

            if response.status_code != 200:
                self.test_results["TOOL_DISCOVERY"] = "FAIL"
                print(f"  ✗ Tool Discovery: FAIL (HTTP {response.status_code})")
                return False

            data = response.json()

            # Extract tools from MCP response
            if "result" in data and "tools" in data["result"]:
                tools = data["result"]["tools"]
            else:
                self.test_results["TOOL_DISCOVERY"] = "FAIL"
                print("  ✗ Tool Discovery: FAIL (unexpected response format)")
                print(f"  Response keys: {list(data.keys())}")
                return False

            # Parse tools
            for tool in tools:
                if isinstance(tool, dict):
                    self.discovered_tools.append({
                        "name": tool.get("name"),
                        "description": tool.get("description", ""),
                        "schema": tool.get("inputSchema")
                    })

            if self.discovered_tools:
                self.test_results["TOOL_DISCOVERY"] = "PASS"
                print(f"  ✓ Tool Discovery: PASS ({len(self.discovered_tools)} tools)")
                for tool in self.discovered_tools[:5]:  # Show first 5
                    desc = tool['description'][:60] if tool['description'] else "(no description)"
                    print(f"    - {tool['name']}: {desc}...")
                if len(self.discovered_tools) > 5:
                    print(f"    ... and {len(self.discovered_tools) - 5} more")

                self.test_details.append({
                    "test": "tool_discovery",
                    "status": "PASS",
                    "tool_count": len(self.discovered_tools),
                    "tools": self.discovered_tools
                })
                return True
            else:
                self.test_results["TOOL_DISCOVERY"] = "FAIL"
                print("  ✗ Tool Discovery: FAIL (could not extract tool names)")
                return False

        except Exception as e:
            self.test_results["TOOL_DISCOVERY"] = "FAIL"
            print(f"  ✗ Tool Discovery: FAIL ({e})")
            self.test_details.append({
                "test": "tool_discovery",
                "error": str(e)
            })
            return False

    def test_sample_call(self) -> bool:
        """Test 4: One minimal sample call."""
        print("\n[Test 4/4] Testing Sample Call...")

        if not self.discovered_tools:
            self.test_results["SAMPLE_CALL"] = "BLOCKED"
            print("  ⊘ Sample Call: BLOCKED (no tools discovered)")
            return False

        # Look for common query tools
        tool_name = None
        tool_schema = None

        # Common patterns for stock/security query tools
        patterns = [
            "query", "search", "get", "fetch", "stock", "security", "quote", "price"
        ]

        for tool in self.discovered_tools:
            name_lower = tool["name"].lower()
            if any(p in name_lower for p in patterns):
                tool_name = tool["name"]
                tool_schema = tool["schema"]
                break

        if not tool_name:
            self.test_results["SAMPLE_CALL"] = "BLOCKED"
            print("  ⊘ Sample Call: BLOCKED (no obvious query tool found)")
            print(f"    Available tools: {[t['name'] for t in self.discovered_tools[:5]]}")
            return False

        print(f"  Attempting sample call with tool: {tool_name}")

        # Try minimal query: 宁德时代 or 300750 or 贵州茅台 or 600519
        test_queries = [
            {"symbol": "300750"},
            {"code": "300750"},
            {"stock_code": "300750"},
            {"query": "宁德时代"},
            {"symbol": "600519"},
            {"code": "600519"},
        ]

        for query_params in test_queries:
            try:
                response = requests.post(
                    self.mcp_url,
                    headers=self.headers,
                    json={
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": query_params
                        }
                    },
                    timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    self.test_results["SAMPLE_CALL"] = "PASS"
                    print(f"  ✓ Sample Call: PASS (tool={tool_name}, params={query_params})")
                    print(f"    Response size: {len(response.content)} bytes")

                    self.test_details.append({
                        "test": "sample_call",
                        "status": "PASS",
                        "tool": tool_name,
                        "params": query_params,
                        "response_size": len(response.content)
                    })
                    return True

            except Exception as e:
                continue

        self.test_results["SAMPLE_CALL"] = "FAIL"
        print(f"  ✗ Sample Call: FAIL (tried {len(test_queries)} param combinations)")
        self.test_details.append({
            "test": "sample_call",
            "status": "FAIL",
            "tool": tool_name,
            "tried_params": test_queries
        })
        return False

    def generate_report(self) -> Dict[str, Any]:
        """Generate Phase 1 Smoke Report."""
        report = {
            "report_title": "Choice/MX Adapter Smoke Report - Phase 1",
            "test_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "phase": "Phase 1: Connectivity, Auth, Tool Discovery",
            "mcp_url": self.mcp_url,
            "api_key_masked": self.masked_key,
            "test_results": self.test_results,
            "discovered_tools_count": len(self.discovered_tools),
            "discovered_tools": [
                {"name": t["name"], "description": t["description"]}
                for t in self.discovered_tools[:10]  # First 10 only
            ],
            "test_details": self.test_details,
            "status_layers": {
                "MX_MCP_itself": "PASS (previously verified)",
                "Codex_config_layer": "PASS (previously verified)",
                "Raw_MCP_tools_call": "PASS (600519 tested)",
                "Vera_Feishu_runtime": "NOT PROVEN",
                "Company_Panorama_evidence": "NOT PROVEN"
            },
            "next_steps": self._get_next_steps()
        }

        return report

    def _get_next_steps(self) -> str:
        """Determine next steps based on test results."""
        if self.test_results["CONNECTIVITY"] != "PASS":
            return "BLOCKED: Fix connectivity before proceeding"

        if self.test_results["AUTH"] != "PASS":
            return "BLOCKED: Fix authentication before proceeding"

        if self.test_results["TOOL_DISCOVERY"] != "PASS":
            return "BLOCKED: Tool discovery failed - cannot identify available capabilities"

        if self.test_results["SAMPLE_CALL"] == "PASS":
            return (
                "Phase 1 COMPLETE. Next: Report discovered tools to user. "
                "Then implement resolve_company/fetch_announcements/fetch_news "
                "based on confirmed tool names and schemas."
            )
        elif self.test_results["SAMPLE_CALL"] == "BLOCKED":
            return (
                "Phase 1 PARTIAL. Tool discovery succeeded but tool contract unclear. "
                "Report discovered tools to user for manual review before Phase 2."
            )
        else:
            return "Phase 1 INCOMPLETE. Review test details and retry."

    def print_report(self):
        """Print report to console."""
        print("\n" + "="*80)
        print("Choice/MX Adapter Smoke Report - Phase 1")
        print("="*80)
        print(f"\nTest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"MCP URL: {self.mcp_url}")
        print(f"API Key: {self.masked_key}")
        print("\nTest Results:")
        for key, value in self.test_results.items():
            if value == "PASS":
                symbol = "✓"
            elif value == "FAIL":
                symbol = "✗"
            elif value == "BLOCKED":
                symbol = "⊘"
            elif value == "NOT TESTED":
                symbol = "○"
            else:
                symbol = "?"
            print(f"  {symbol} {key}: {value}")

        if self.discovered_tools:
            print(f"\nDiscovered Tools: {len(self.discovered_tools)}")
            for tool in self.discovered_tools[:10]:
                desc = tool['description'][:60] if tool['description'] else "(no description)"
                print(f"  - {tool['name']}: {desc}")
            if len(self.discovered_tools) > 10:
                print(f"  ... and {len(self.discovered_tools) - 10} more")

        print("\nStatus Layers:")
        print("  ✓ MX MCP itself: PASS (previously verified)")
        print("  ✓ Codex config layer: PASS (previously verified)")
        print("  ✓ Raw MCP tools/call: PASS (600519 tested)")
        print("  ○ Vera / Feishu runtime: NOT PROVEN")
        print("  ○ Company Panorama evidence: NOT PROVEN")

        print("\n" + "-"*80)
        print("Next Steps:")
        print("-"*80)
        print(self._get_next_steps())

        print("\nScope Reminder:")
        print("  - Phase 1 tests connectivity, auth, tool discovery ONLY")
        print("  - Does NOT test resolve_company/announcements/news")
        print("  - Does NOT integrate with Company Panorama pipeline")
        print("  - Does NOT generate production visit cards")

    def run(self) -> Dict[str, Any]:
        """Run Phase 1 smoke test."""
        print("="*80)
        print("Choice/MX Adapter Smoke v0 - Phase 1")
        print("="*80)
        print("\nScope: Connectivity, Auth, Tool Discovery ONLY")
        print("")

        # Run tests
        if not self.test_connectivity():
            print("\n❌ BLOCKED: Connectivity failed - cannot proceed")
            return self.generate_report()

        if not self.test_auth():
            print("\n❌ BLOCKED: Authentication failed - cannot proceed")
            return self.generate_report()

        if not self.test_tool_discovery():
            print("\n❌ BLOCKED: Tool discovery failed - cannot proceed")
            return self.generate_report()

        self.test_sample_call()

        # Generate and print report
        report = self.generate_report()
        self.print_report()

        # Save report
        report_path = "choice_mx_adapter_phase1_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Report saved to: {report_path}")

        return report


def main():
    """Run Phase 1 smoke test."""
    try:
        probe = ChoiceMXAdapterPhase1()
        report = probe.run()

        # Exit code
        if report["test_results"]["TOOL_DISCOVERY"] == "PASS":
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
