"""
Mantle Yield Scout — Onchain Research Agent
Queries Mantle L2 DeFi protocols via DeFiLlama API for live yield data.
"""

import json
import sys
import os
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

import requests

# ── Configuration ──────────────────────────────────────────────────────────

DEFILLAMA_YIELDS_URL = "https://yields.llama.fi/pools"
MANTLE_CHAIN = "mantle"

# ── Data Models ────────────────────────────────────────────────────────────

@dataclass
class DeFiPool:
    symbol: str
    project: str
    apy: float
    tvl_usd: float
    pool_id: str

@dataclass
class ResearchReport:
    timestamp: str
    pools: list
    total_tvl: float
    top_opportunities: list
    summary: str
    x_post: str


# ── Data Fetcher ───────────────────────────────────────────────────────────

def fetch_mantle_pools() -> list:
    """Fetch live Mantle DeFi pool data from DeFiLlama."""
    print("  📊 Fetching live data from DeFiLlama...")
    try:
        r = requests.get(DEFILLAMA_YIELDS_URL, timeout=15)
        r.raise_for_status()
        data = r.json().get("data", [])
    except Exception as e:
        print(f"  ✗ DeFiLlama API error: {e}")
        return []
    
    # Filter for Mantle chain
    mantle = []
    for p in data:
        if p.get("chain", "").lower() != MANTLE_CHAIN:
            continue
        apy = p.get("apy", 0) or 0
        tvl = p.get("tvlUsd", 0) or 0
        if tvl < 1000:  # Skip dust pools
            continue
        mantle.append(DeFiPool(
            symbol=p.get("symbol", "Unknown"),
            project=p.get("project", "Unknown"),
            apy=apy,
            tvl_usd=tvl,
            pool_id=p.get("pool", ""),
        ))
    
    return mantle


# ── Research Engine ────────────────────────────────────────────────────────

class YieldScout:
    """Main research engine using live DeFiLlama data."""
    
    def research(self) -> ResearchReport:
        """Run full research sweep."""
        print("\n🔍 Scanning Mantle DeFi protocols...\n")
        
        pools = fetch_mantle_pools()
        
        if not pools:
            print("  ✗ No data found")
            return ResearchReport(
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                pools=[], total_tvl=0, top_opportunities=[],
                summary="No data available", x_post="No data available"
            )
        
        # Sort by TVL
        pools.sort(key=lambda x: x.tvl_usd, reverse=True)
        total_tvl = sum(p.tvl_usd for p in pools)
        
        # Rank by APY (only pools with meaningful TVL)
        significant = [p for p in pools if p.tvl_usd > 10000]
        significant.sort(key=lambda x: x.apy, reverse=True)
        
        report = self._generate_report(pools, significant, total_tvl)
        return report
    
    def _generate_report(self, all_pools, top_pools, total_tvl) -> ResearchReport:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        
        best = top_pools[0] if top_pools else None
        summary = f"Mantle DeFi scan at {now}. "
        if best:
            summary += f"Top opportunity: {best.symbol} on {best.project} at {best.apy:.2f}% APY. "
        summary += f"Found {len(all_pools)} active pools, total TVL ${total_tvl:,.0f}."
        
        x_post = self._generate_x_post(top_pools[:5], total_tvl)
        
        return ResearchReport(
            timestamp=now,
            pools=all_pools,
            total_tvl=total_tvl,
            top_opportunities=[{
                "symbol": p.symbol,
                "project": p.project,
                "apy": p.apy,
                "tvl_usd": p.tvl_usd,
            } for p in top_pools[:10]],
            summary=summary,
            x_post=x_post,
        )
    
    def _generate_x_post(self, top, total_tvl) -> str:
        lines = ["🔍 Mantle DeFi Research — Live Scan\n"]
        lines.append("📊 Top yield opportunities on @Mantle_Official:\n")
        
        for i, p in enumerate(top, 1):
            lines.append(f"{i}. {p.symbol} ({p.project})")
            lines.append(f"   APY: {p.apy:.2f}% | TVL: ${p.tvl_usd:,.0f}\n")
        
        lines.append(f"📈 Total Mantle DeFi TVL: ${total_tvl:,.0f}")
        lines.append(f"\n#Mantle #DeFi #OnchainFinance #AIResearchAgent")
        
        return "\n".join(lines)


# ── Report Formatter ───────────────────────────────────────────────────────

def format_report(report: ResearchReport) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("  MANTLE YIELD SCOUT — LIVE RESEARCH REPORT")
    lines.append(f"  {report.timestamp}")
    lines.append("=" * 60)
    
    lines.append(f"\n📋 SUMMARY")
    lines.append(f"  {report.summary}")
    
    lines.append(f"\n🏆 TOP 10 YIELD OPPORTUNITIES (by APY)")
    lines.append(f"  {'#':<4} {'Symbol':<25} {'Protocol':<20} {'APY':>8} {'TVL':>15}")
    lines.append(f"  {'─'*4} {'─'*25} {'─'*20} {'─'*8} {'─'*15}")
    
    for i, p in enumerate(report.top_opportunities, 1):
        lines.append(f"  {i:<4} {p['symbol']:<25} {p['project']:<20} {p['apy']:>7.2f}% ${p['tvl_usd']:>13,.0f}")
    
    lines.append(f"\n📈 Total pools: {len(report.pools)} | Total TVL: ${report.total_tvl:,.0f}")
    
    lines.append(f"\n{'='*60}")
    lines.append(f"  📝 X POST (READY TO PUBLISH)")
    lines.append(f"{'='*60}")
    lines.append(report.x_post)
    lines.append(f"{'='*60}")
    
    return "\n".join(lines)


# ── CLI Entry Point ────────────────────────────────────────────────────────

def main():
    print("🔮 Mantle Yield Scout — Onchain Research Agent")
    print("   Powered by DeFiLlama (live data)\n")
    
    scout = YieldScout()
    report = scout.research()
    print(format_report(report))
    
    report_path = os.path.join(os.path.dirname(__file__), "latest_report.md")
    with open(report_path, "w") as f:
        f.write(f"# Mantle Yield Scout Report — {report.timestamp}\n\n")
        f.write(f"## Summary\n{report.summary}\n\n")
        f.write(f"## X Post\n```\n{report.x_post}\n```\n")
    print(f"\n📄 Report saved to: {report_path}")


if __name__ == "__main__":
    main()
