#!/usr/bin/env python3
"""
Multi-Platform Price Comparison Script
Compares Vivid Seats vs StubHub for your Harry Styles tickets.
Filters for YOUR specific sections and excludes singles (except for solo tickets).

Run with: python compare_prices.py
"""
import asyncio
import httpx
from app.services.scrapers.stubhub_browser import StubHubBrowserScraper

# Your ticket inventory with event IDs and filtering rules
INVENTORY = [
    {
        "set": "Set A",
        "date": "Sept 2",
        "section": "Section 200s Row 1",
        "quantity": 4,
        "cost_per_ticket": 471.25,
        "vivid_id": "6564568",
        "stubhub_id": "160334450",
        "filter": {
            "section_match": ["Section 2"],  # Match 200-level sections
            "row": "1",  # Must be Row 1 (premium front row)
            "min_qty": 2,  # Exclude singles
        },
    },
    {
        "set": "Set C",
        "date": "Sept 18",
        "section": "Section 112",
        "quantity": 8,
        "cost_per_ticket": 324.88,
        "vivid_id": "6564610",
        "stubhub_id": "160334461",
        "filter": {
            "section_match": ["112"],  # Match Section 112 specifically
            "row": None,  # Any row
            "min_qty": 2,  # Exclude singles
        },
    },
    {
        "set": "Set B",
        "date": "Sept 19",
        "section": "Left GA",
        "quantity": 6,
        "cost_per_ticket": 490.67,
        "vivid_id": "6564614",
        "stubhub_id": "160334462",
        "filter": {
            "section_match": ["LEFT", "GA"],  # Must contain both LEFT and GA
            "section_match_all": True,  # All terms must match
            "row": None,
            "min_qty": 2,  # Exclude singles
        },
    },
    {
        "set": "Set E",
        "date": "Sept 25",
        "section": "Section 100s (4 solos)",
        "quantity": 4,
        "cost_per_ticket": 368.00,
        "vivid_id": "6564623",
        "stubhub_id": "160334464",
        "filter": {
            "section_match": ["Section 1"],  # Match 100-level sections (100-120)
            "row": None,
            "min_qty": 1,  # INCLUDE singles for this set
        },
    },
    {
        "set": "Set D",
        "date": "Oct 9",
        "section": "Left GA",
        "quantity": 5,
        "cost_per_ticket": 433.20,
        "vivid_id": "6564676",
        "stubhub_id": "160334466",
        "filter": {
            "section_match": ["LEFT", "GA"],  # Must contain both LEFT and GA
            "section_match_all": True,
            "row": None,
            "min_qty": 2,  # Exclude singles
        },
    },
]

VIVID_FEE = 0.10  # 10% seller fee
STUBHUB_FEE = 0.15  # 15% seller fee
STUBHUB_BUYER_FEE = 0.25  # ~25% buyer fees (base to all-in)


def filter_vivid_tickets(tickets: list, filter_rules: dict) -> list:
    """Filter Vivid Seats tickets based on rules."""
    filtered = []

    for t in tickets:
        section = str(t.get("s", "")).upper()
        row = str(t.get("r", "")).upper()
        qty = int(t.get("q", 1))
        price = float(t.get("aip", 0))

        # Skip invalid prices
        if price < 50:
            continue

        # Check minimum quantity
        if qty < filter_rules.get("min_qty", 1):
            continue

        # Check section match
        section_terms = filter_rules.get("section_match", [])
        match_all = filter_rules.get("section_match_all", False)

        if section_terms:
            if match_all:
                # All terms must be in section
                if not all(term.upper() in section for term in section_terms):
                    continue
            else:
                # Any term must be in section
                if not any(term.upper() in section for term in section_terms):
                    continue

        # Check section exclusions
        excludes = filter_rules.get("section_exclude", [])
        if any(ex.upper() in section for ex in excludes):
            continue

        # Check row filter
        row_filter = filter_rules.get("row")
        if row_filter and row != row_filter.upper():
            continue

        filtered.append({
            "section": t.get("s"),
            "row": t.get("r"),
            "qty": qty,
            "price": price,
        })

    return filtered


def filter_stubhub_listings(listings: list, filter_rules: dict) -> list:
    """Filter StubHub listings based on rules (limited data from scrape)."""
    # StubHub scraper gets limited data, so we're more lenient here
    filtered = []

    for l in listings:
        price = l.get("price", 0)
        if price < 50 or price > 20000:
            continue
        filtered.append(l)

    return filtered


async def get_vivid_prices(event_id: str, filter_rules: dict) -> dict:
    """Get filtered prices from Vivid Seats API."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"https://www.vividseats.com/hermes/api/v1/listings?productionId={event_id}"
            )
            data = resp.json()
            tickets = data.get("tickets", [])

            # Apply filters
            filtered = filter_vivid_tickets(tickets, filter_rules)
            prices = [t["price"] for t in filtered]

            if prices:
                return {
                    "count": len(prices),
                    "min": min(prices),
                    "max": max(prices),
                    "avg": sum(prices) / len(prices),
                    "sample": sorted(filtered, key=lambda x: x["price"])[:5],
                }
    except Exception as e:
        print(f"  [Vivid] Error: {e}")
    return {"count": 0, "min": None, "max": None, "avg": None, "sample": []}


async def get_stubhub_prices(event_id: str, filter_rules: dict, scraper: StubHubBrowserScraper) -> dict:
    """Get prices from StubHub via browser scraper."""
    try:
        result = await scraper.get_event_listings(f"event/{event_id}")
        listings = result.get("listings", [])

        # Apply filters
        filtered = filter_stubhub_listings(listings, filter_rules)
        prices = [l["price"] for l in filtered if l.get("price")]

        if prices:
            all_in = [p * (1 + STUBHUB_BUYER_FEE) for p in prices]
            return {
                "count": len(prices),
                "min_base": min(prices),
                "max_base": max(prices),
                "min_allin": min(all_in),
                "max_allin": max(all_in),
                "avg_allin": sum(all_in) / len(all_in),
            }
    except Exception as e:
        print(f"  [StubHub] Error: {e}")
    return {"count": 0, "min_base": None, "min_allin": None}


async def main():
    print("=" * 80)
    print("HARRY STYLES TICKET PRICE COMPARISON")
    print("Filtered for YOUR specific sections | Excluding singles (except Set E)")
    print("=" * 80)
    print()

    scraper = StubHubBrowserScraper()
    total_cost = 0
    total_vivid_value = 0
    total_stubhub_value = 0
    total_tickets = 0

    try:
        for inv in INVENTORY:
            filter_rules = inv.get("filter", {})

            print(f"{'='*80}")
            print(f"{inv['set']}: {inv['date']} - {inv['section']} ({inv['quantity']} tickets)")
            print(f"Filter: {filter_rules.get('section_match')} | Row: {filter_rules.get('row', 'Any')} | Min Qty: {filter_rules.get('min_qty', 1)}")
            print(f"Cost: ${inv['cost_per_ticket']:.0f}/ticket (${inv['cost_per_ticket'] * inv['quantity']:,.0f} total)")
            print()

            # Get prices from both platforms
            vivid = await get_vivid_prices(inv["vivid_id"], filter_rules)
            stubhub = await get_stubhub_prices(inv["stubhub_id"], filter_rules, scraper)

            # Vivid Seats
            if vivid["min"]:
                vs_net = vivid["min"] * (1 - VIVID_FEE)
                vs_profit = (vs_net - inv["cost_per_ticket"]) * inv["quantity"]
                print(f"VIVID SEATS: {vivid['count']} comparable listings")
                print(f"  Price range: ${vivid['min']:.0f} - ${vivid['max']:.0f} (all-in)")
                print(f"  You receive: ${vs_net:.0f}/ticket (after 10% fee)")
                print(f"  Profit on {inv['quantity']} tickets: ${vs_profit:+,.0f}")

                # Show sample listings
                if vivid.get("sample"):
                    print(f"  Sample listings:")
                    for s in vivid["sample"][:3]:
                        print(f"    {s['section']} Row {s['row']} - ${s['price']:.0f} ({s['qty']} tix)")

                total_vivid_value += vs_net * inv["quantity"]
            else:
                print("VIVID SEATS: No comparable listings found")
                vs_net = 0
                vs_profit = 0

            print()

            # StubHub
            if stubhub.get("min_allin"):
                sh_net = stubhub["min_allin"] * (1 - STUBHUB_FEE)
                sh_profit = (sh_net - inv["cost_per_ticket"]) * inv["quantity"]
                print(f"STUBHUB: {stubhub['count']} listings found")
                print(f"  Price range: ${stubhub['min_base']:.0f} - ${stubhub['max_base']:.0f} (base)")
                print(f"  All-in estimate: ${stubhub['min_allin']:.0f} - ${stubhub['max_allin']:.0f}")
                print(f"  You receive: ${sh_net:.0f}/ticket (after 15% fee)")
                print(f"  Profit on {inv['quantity']} tickets: ${sh_profit:+,.0f}")
                total_stubhub_value += sh_net * inv["quantity"]
            else:
                print("STUBHUB: No comparable listings found")
                sh_net = 0
                sh_profit = 0

            print()

            # Recommendation
            if vs_net and sh_net:
                better = "STUBHUB" if sh_net > vs_net else "VIVID SEATS"
                diff = abs(sh_net - vs_net)
                diff_total = diff * inv["quantity"]
                print(f">>> RECOMMENDATION: Sell on {better}")
                print(f"    Difference: +${diff:.0f}/ticket (+${diff_total:,.0f} total)")
            elif vs_net:
                print(f">>> RECOMMENDATION: Sell on VIVID SEATS (only option with data)")
            elif sh_net:
                print(f">>> RECOMMENDATION: Sell on STUBHUB (only option with data)")

            total_cost += inv["cost_per_ticket"] * inv["quantity"]
            total_tickets += inv["quantity"]
            print()

        # Summary
        print("=" * 80)
        print("SUMMARY - ALL 27 TICKETS")
        print("=" * 80)
        print(f"Total Tickets: {total_tickets}")
        print(f"Total Cost: ${total_cost:,.0f}")
        print()
        print(f"If sold on Vivid Seats:")
        print(f"  Total Revenue: ${total_vivid_value:,.0f}")
        print(f"  Total Profit: ${total_vivid_value - total_cost:+,.0f}")
        print()
        print(f"If sold on StubHub:")
        print(f"  Total Revenue: ${total_stubhub_value:,.0f}")
        print(f"  Total Profit: ${total_stubhub_value - total_cost:+,.0f}")
        print()

        diff = total_stubhub_value - total_vivid_value
        if diff > 0:
            print(f">>> OVERALL WINNER: STUBHUB (+${diff:,.0f} more than Vivid)")
        else:
            print(f">>> OVERALL WINNER: VIVID SEATS (+${-diff:,.0f} more than StubHub)")

    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
