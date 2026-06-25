# Mantle Yield Scout — SKILL.md

## What This Does
Mantle Yield Scout is an onchain research agent that queries Mantle L2 DeFi protocols in real-time, compares yield opportunities, and generates structured research reports. It uses Mantle's MCP tools directly for live onchain data.

## When To Use
- Research current DeFi yields on Mantle Network
- Compare lending rates across Aave V3 pools
- Analyze LP opportunities on Merchant Moe, Agni Finance, Fluxion
- Track TVL trends across Mantle protocols
- Generate X-ready research posts with real data

## Architecture
```
User Query → Yield Scout CLI → Mantle MCP Server → Onchain Data
                                        ↓
                              Research Report + X Post
```

## Protocols Covered
- **Aave V3** — Lending/borrowing markets (supply APY, borrow APY, utilization)
- **Merchant Moe** — DEX swaps and LP pools
- **Agni Finance** — DEX swaps and LP pools  
- **Fluxion** — DEX swaps and LP pools

## MCP Tools Used
Read tools:
- `mantle_getLendingMarkets` — Aave V3 market data
- `mantle_getPoolOpportunities` — LP opportunities
- `mantle_getPoolLiquidity` — Pool reserves and TVL
- `mantle_getProtocolTvl` — Protocol-level TVL
- `mantle_getTokenPrices` — USD prices
- `mantle_getSwapQuote` — Swap price quotes
- `mantle_getTokenBalances` — ERC-20 balances
- `mantle_querySubgraph` — Subgraph queries

## Output Format
Reports include:
1. Executive summary (2-3 sentences)
2. Top yield opportunities (ranked by APY)
3. TVL comparison across protocols
4. Risk assessment (utilization, liquidity depth)
5. X-ready post with key findings

## Bonus Points
Uses Mantle's AI Agent Skills (SKILL.md format) + MCP tools directly.
