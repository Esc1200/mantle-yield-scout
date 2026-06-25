"""
Mantle Yield Scout — Onchain Research Agent
Queries Mantle L2 DeFi protocols via MCP tools and generates research reports.
"""

import json
import subprocess
import sys
import os
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

# ── Configuration ──────────────────────────────────────────────────────────

MANTLE_CHAIN_ID = 5000
MANTLE_RPC = "https://rpc.mantle.xyz"
MANTLE_EXPLORER = "https://mantlescan.xyz"

PROTOCOLS = {
    "aave_v3": {"name": "Aave V3", "type": "lending"},
    "merchant_moe": {"name": "Merchant Moe", "type": "dex"},
    "agni": {"name": "Agni Finance", "type": "dex"},
    "fluxion": {"name": "Fluxion", "type": "dex"},
}

# ── MCP Client ─────────────────────────────────────────────────────────────

class MantleMCPClient:
    """Client for Mantle MCP server over stdio."""
    
    def __init__(self):
        self.process = None
        self.request_id = 0
    
    def start(self):
        """Start the MCP server process."""
        try:
            # Try multiple npx locations
            npx_candidates = [
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes", "node", "npx.cmd"),
                os.path.join(os.environ.get("APPDATA", ""), "hermes", "node", "npx.cmd"),
                "npx",
            ]
            npx_path = "npx"
            for candidate in npx_candidates:
                if os.path.exists(candidate):
                    npx_path = candidate
                    break
            
            self.process = subprocess.Popen(
                [npx_path, "-y", "@mantleio/mantle-mcp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            # Initialize
            self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mantle-yield-scout", "version": "1.0.0"}
            })
            self._send_notification("notifications/initialized", {})
            return True
        except Exception as e:
            print(f"Warning: Could not start MCP server: {e}")
            return False
    
    def call_tool(self, tool_name: str, arguments: dict = None) -> dict:
        """Call an MCP tool."""
        return self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments or {}
        })
    
    def list_tools(self) -> list:
        """List available MCP tools."""
        result = self._send_request("tools/list", {})
        return result.get("tools", [])
    
    def _send_request(self, method: str, params: dict) -> dict:
        """Send a JSON-RPC request."""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        response_line = self.process.stdout.readline()
        if response_line:
            return json.loads(response_line)
        return {}
    
    def _send_notification(self, method: str, params: dict):
        """Send a JSON-RPC notification (no response expected)."""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        self.process.stdin.write(json.dumps(notification) + "\n")
        self.process.stdin.flush()
    
    def stop(self):
        """Stop the MCP server."""
        if self.process:
            self.process.terminate()


# ── Data Models ────────────────────────────────────────────────────────────

@dataclass
class LendingMarket:
    protocol: str
    token: str
    supply_apy: float
    borrow_apy: float
    utilization: float
    total_supplied: float
    total_borrowed: float
    tvl_usd: float = 0.0

@dataclass
class PoolOpportunity:
    protocol: str
    pair: str
    apy: float
    tvl_usd: float
    volume_24h: float = 0.0
    fee_tier: str = ""

@dataclass
class ResearchReport:
    timestamp: str
    lending_markets: list
    pool_opportunities: list
    protocol_tvl: dict
    top_opportunities: list
    summary: str
    x_post: str


# ── Research Engine ────────────────────────────────────────────────────────

class YieldScout:
    """Main research engine."""
    
    def __init__(self, use_mcp: bool = True):
        self.mcp = MantleMCPClient() if use_mcp else None
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to Mantle MCP server."""
        if self.mcp:
            self.connected = self.mcp.start()
            if self.connected:
                tools = self.mcp.list_tools()
                print(f"✓ Connected to Mantle MCP ({len(tools)} tools available)")
            else:
                print("✗ Could not connect to MCP server, using mock data")
        return self.connected
    
    def research(self) -> ResearchReport:
        """Run full research sweep."""
        print("\n🔍 Scanning Mantle DeFi protocols...\n")
        
        # Gather data
        lending = self._scan_lending_markets()
        pools = self._scan_pool_opportunities()
        tvl = self._scan_protocol_tvl()
        
        # Rank opportunities
        top = self._rank_opportunities(lending, pools)
        
        # Generate report
        report = self._generate_report(lending, pools, tvl, top)
        
        return report
    
    def _scan_lending_markets(self) -> list:
        """Scan Aave V3 lending markets on Mantle."""
        print("  📊 Querying A V3 lending markets...")
        
        if self.connected:
            try:
                result = self.mcp.call_tool("mantle_getLendingMarkets")
                # Parse MCP response
                markets = []
                if "content" in result:
                    data = json.loads(result["content"][0]["text"])
                    for market in data.get("markets", []):
                        markets.append(LendingMarket(
                            protocol="Aave V3",
                            token=market.get("symbol", "Unknown"),
                            supply_apy=market.get("supplyApy", 0),
                            borrow_apy=market.get("borrowApy", 0),
                            utilization=market.get("utilization", 0),
                            total_supplied=market.get("totalSupplied", 0),
                            total_borrowed=market.get("totalBorrowed", 0),
                            tvl_usd=market.get("tvlUsd", 0),
                        ))
                return markets
            except Exception as e:
                print(f"    Warning: MCP call failed: {e}")
        
        # Fallback: mock data for demonstration
        return self._mock_lending_markets()
    
    def _scan_pool_opportunities(self) -> list:
        """Scan LP pool opportunities across DEXs."""
        print("  💧 Scanning LP pool opportunities...")
        
        pools = []
        for protocol_id, info in PROTOCOLS.items():
            if info["type"] != "dex":
                continue
            
            if self.connected:
                try:
                    result = self.mcp.call_tool("mantle_getPoolOpportunities", {
                        "protocol": protocol_id
                    })
                    if "content" in result:
                        data = json.loads(result["content"][0]["text"])
                        for pool in data.get("pools", []):
                            pools.append(PoolOpportunity(
                                protocol=info["name"],
                                pair=pool.get("pair", "Unknown"),
                                apy=pool.get("apy", 0),
                                tvl_usd=pool.get("tvlUsd", 0),
                                volume_24h=pool.get("volume24h", 0),
                                fee_tier=pool.get("feeTier", ""),
                            ))
                except Exception as e:
                    print(f"    Warning: {info['name']} query failed: {e}")
        
        if not pools:
            pools = self._mock_pool_opportunities()
        
        return pools
    
    def _scan_protocol_tvl(self) -> dict:
        """Scan TVL across all Mantle protocols."""
        print("  📈 Fetching protocol TVL data...")
        
        tvl = {}
        for protocol_id, info in PROTOCOLS.items():
            if self.connected:
                try:
                    result = self.mcp.call_tool("mantle_getProtocolTvl", {
                        "protocol": protocol_id
                    })
                    if "content" in result:
                        data = json.loads(result["content"][0]["text"])
                        tvl[info["name"]] = data.get("tvlUsd", 0)
                except Exception as e:
                    tvl[info["name"]] = 0
        
        if not tvl:
            tvl = self._mock_protocol_tvl()
        
        return tvl
    
    def _rank_opportunities(self, lending: list, pools: list) -> list:
        """Rank all opportunities by APY."""
        all_opps = []
        
        for m in lending:
            all_opps.append({
                "type": "lending",
                "protocol": m.protocol,
                "name": f"Supply {m.token}",
                "apy": m.supply_apy,
                "tvl_usd": m.tvl_usd,
                "risk": "low" if m.utilization < 0.8 else "medium" if m.utilization < 0.95 else "high",
            })
        
        for p in pools:
            all_opps.append({
                "type": "lp",
                "protocol": p.protocol,
                "name": p.pair,
                "apy": p.apy,
                "tvl_usd": p.tvl_usd,
                "risk": "medium" if p.tvl_usd > 100000 else "high",
            })
        
        all_opps.sort(key=lambda x: x["apy"], reverse=True)
        return all_opps[:10]
    
    def _generate_report(self, lending, pools, tvl, top) -> ResearchReport:
        """Generate a structured research report."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        
        # Executive summary
        best = top[0] if top else None
        summary = f"Mantle DeFi scan completed at {now}. "
        if best:
            summary += f"Top opportunity: {best['name']} on {best['protocol']} at {best['apy']:.2f}% APY. "
        summary += f"Scanned {len(lending)} lending markets and {len(pools)} LP pools across {len(PROTOCOLS)} protocols."
        
        # X post
        x_post = self._generate_x_post(top, tvl)
        
        return ResearchReport(
            timestamp=now,
            lending_markets=lending,
            pool_opportunities=pools,
            protocol_tvl=tvl,
            top_opportunities=top,
            summary=summary,
            x_post=x_post,
        )
    
    def _generate_x_post(self, top, tvl) -> str:
        """Generate an X-ready post."""
        lines = ["🔍 Mantle DeFi Research — Live Scan\n"]
        lines.append(f"📊 Top yield opportunities on @Mantle_Official:\n")
        
        for i, opp in enumerate(top[:5], 1):
            risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(opp["risk"], "⚪")
            lines.append(f"{i}. {opp['name']} ({opp['protocol']})")
            lines.append(f"   APY: {opp['apy']:.2f}% {risk_emoji}")
            lines.append(f"   TVL: ${opp['tvl_usd']:,.0f}\n")
        
        if tvl:
            lines.append("📈 Protocol TVL:")
            for name, value in sorted(tvl.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  • {name}: ${value:,.0f}")
        
        lines.append(f"\n#Mantle #DeFi #OnchainFinance #AIResearchAgent")
        
        return "\n".join(lines)
    
    # ── Mock data for demonstration ────────────────────────────────────────
    
    def _mock_lending_markets(self) -> list:
        return [
            LendingMarket("Aave V3", "USDC", 4.82, 6.15, 0.78, 12500000, 9750000, 12500000),
            LendingMarket("Aave V3", "WETH", 3.21, 4.88, 0.66, 8200000, 5412000, 8200000),
            LendingMarket("Aave V3", "WMNT", 5.67, 8.92, 0.64, 3800000, 2432000, 3800000),
            LendingMarket("Aave V3", "USDT", 4.45, 5.98, 0.75, 9100000, 6825000, 9100000),
            LendingMarket("Aave V3", "WBTC", 1.89, 3.45, 0.55, 6500000, 3575000, 6500000),
        ]
    
    def _mock_pool_opportunities(self) -> list:
        return [
            PoolOpportunity("Merchant Moe", "MNT/USDC", 28.45, 2850000, 1250000, "0.3%"),
            PoolOpportunity("Agni Finance", "WMNT/WETH", 22.18, 1820000, 890000, "0.25%"),
            PoolOpportunity("Fluxion", "USDC/USDT", 8.92, 5200000, 3100000, "0.01%"),
            PoolOpportunity("Merchant Moe", "MNT/WETH", 18.34, 1450000, 720000, "0.3%"),
            PoolOpportunity("Agni Finance", "WMNT/USDC", 15.67, 980000, 450000, "0.25%"),
            PoolOpportunity("Fluxion", "WETH/USDC", 12.45, 3200000, 1800000, "0.05%"),
        ]
    
    def _mock_protocol_tvl(self) -> dict:
        return {
            "Aave V3": 40100000,
            "Merchant Moe": 4300000,
            "Agni Finance": 2800000,
            "Fluxion": 8400000,
        }


# ── Report Formatter ───────────────────────────────────────────────────────

def format_report(report: ResearchReport) -> str:
    """Format report for terminal output."""
    lines = []
    lines.append("=" * 60)
    lines.append("  MANTLE YIELD SCOUT — RESEARCH REPORT")
    lines.append(f"  {report.timestamp}")
    lines.append("=" * 60)
    
    # Summary
    lines.append(f"\n📋 SUMMARY")
    lines.append(f"  {report.summary}")
    
    # Protocol TVL
    lines.append(f"\n📈 PROTOCOL TVL")
    for name, tvl in sorted(report.protocol_tvl.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(tvl / max(report.protocol_tvl.values()) * 20)
        lines.append(f"  {name:<20} ${tvl:>12,.0f}  {bar}")
    
    # Top Opportunities
    lines.append(f"\n🏆 TOP 10 YIELD OPPORTUNITIES")
    lines.append(f"  {'#':<4} {'Name':<25} {'Protocol':<15} {'APY':>8} {'TVL':>12} {'Risk':>6}")
    lines.append(f"  {'─'*4} {'─'*25} {'─'*15} {'─'*8} {'─'*12} {'─'*6}")
    
    for i, opp in enumerate(report.top_opportunities, 1):
        risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(opp["risk"], "⚪")
        lines.append(f"  {i:<4} {opp['name']:<25} {opp['protocol']:<15} {opp['apy']:>7.2f}% ${opp['tvl_usd']:>10,.0f} {risk_emoji}")
    
    # Lending Markets
    lines.append(f"\n🏦 AAVE V3 LENDING MARKETS")
    lines.append(f"  {'Token':<10} {'Supply APY':>10} {'Borrow APY':>10} {'Utilization':>12} {'TVL':>12}")
    lines.append(f"  {'─'*10} {'─'*10} {'─'*10} {'─'*12} {'─'*12}")
    
    for m in report.lending_markets:
        util_bar = "█" * int(m.utilization * 10)
        lines.append(f"  {m.token:<10} {m.supply_apy:>9.2f}% {m.borrow_apy:>9.2f}% {m.utilization*100:>10.1f}% {util_bar} ${m.tvl_usd:>10,.0f}")
    
    # X Post
    lines.append(f"\n{'='*60}")
    lines.append(f"  📝 X POST (READY TO PUBLISH)")
    lines.append(f"{'='*60}")
    lines.append(report.x_post)
    lines.append(f"{'='*60}")
    
    return "\n".join(lines)


# ── CLI Entry Point ────────────────────────────────────────────────────────

def main():
    """Main entry point."""
    print("🔮 Mantle Yield Scout — Onchain Research Agent")
    print("   Powered by Mantle AI Agent Skills + MCP\n")
    
    scout = YieldScout(use_mcp=True)
    scout.connect()
    
    report = scout.research()
    print(format_report(report))
    
    # Save report
    report_path = os.path.join(os.path.dirname(__file__), "latest_report.md")
    with open(report_path, "w") as f:
        f.write(f"# Mantle Yield Scout Report — {report.timestamp}\n\n")
        f.write(f"## Summary\n{report.summary}\n\n")
        f.write(f"## X Post\n```\n{report.x_post}\n```\n")
    print(f"\n📄 Report saved to: {report_path}")
    
    if scout.mcp:
        scout.mcp.stop()


if __name__ == "__main__":
    main()
