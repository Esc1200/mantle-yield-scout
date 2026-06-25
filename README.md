# Mantle Yield Scout 🔮

**Onchain Research Agent for Mantle Network**

A research tool that queries Mantle L2 DeFi protocols in real-time, compares yield opportunities, and generates structured research reports with X-ready summaries.

Built for the [Mantle Research Challenge](https://airdrops.io/mantle/) — Track 2: Research Agent.

## What It Does

1. **Scans DeFi protocols** — Aave V3, Merchant Moe, Agni Finance, Fluxion
2. **Compares yields** — Lending APY, LP pool APY, utilization rates
3. **Tracks TVL** — Protocol-level total value locked
4. **Assesses risk** — Utilization depth, liquidity levels
5. **Generates reports** — Structured research + X-ready posts

## How It Uses Mantle's AI Agent Skills

- **SKILL.md** — Structured skill definition following Mantle's agent skill format
- **MCP Server** — Uses `@mantleio/mantle-mcp` for live onchain data
- **19 MCP Tools** — Queries balances, lending markets, pool opportunities, TVL, token prices

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Yield Scout    │────▶│  Mantle MCP      │────▶│  Onchain Data   │
│  Python CLI     │     │  Server (stdio)  │     │  (Aave, DEXs)   │
└────────┬────────┘     └──────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│  Research Report │
│  + X Post        │
└─────────────────┘
```

## Quick Start

```bash
# Install MCP server
npm install -g @mantleio/mantle-mcp

# Run the scout
python src/scout.py
```

## MCP Tools Used

| Tool | Purpose |
|------|---------|
| `mantle_getLendingMarkets` | Aave V3 market data (APY, utilization) |
| `mantle_getPoolOpportunities` | LP pool discovery |
| `mantle_getPoolLiquidity` | Pool reserves and TVL |
| `mantle_getProtocolTvl` | Protocol-level TVL |
| `mantle_getTokenPrices` | USD prices |
| `mantle_getSwapQuote` | Swap quotes |

## Sample Output

```
🏆 TOP 10 YIELD OPPORTUNITIES
  #    Name                      Protocol         APY          TVL   Risk
  ── ───────────────────────── ─────────────── ──────── ──────────── ──────
  1    MNT/USDC                  Merchant Moe    28.45%   $2,850,000  🟡
  2    WMNT/WETH                 Agni Finance    22.18%   $1,820,000  🟡
  3    MNT/WETH                  Merchant Moe    18.34%   $1,450,000  🟡
  4    WMNT/USDC                 Agni Finance    15.67%     $980,000  🟡
  5    WETH/USDC                 Fluxion         12.45%   $3,200,000  🟡
```

## Why This Matters

Mantle Network has 4+ DeFi protocols with different yield surfaces. Manually comparing them requires:
- Checking each protocol's UI separately
- Calculating risk-adjusted returns
- Tracking TVL changes over time

Yield Scout does all of this in one command, using Mantle's own MCP tools for verified onchain data.

## Tech Stack

- **Python 3.11** — CLI and data processing
- **Mantle MCP Server** — Onchain data access
- **SKILL.md** — Mantle AI Agent Skills format
- **ERC-8004** — Agent identity (optional integration)

## License

MIT
