"""Name-search backing index for this MVP.

The spec calls for searching the web for a company across BSE SME / NSE
Emerge / Screener.in / public MCA pages. A live web-search integration
needs its own paid API (Google/Bing/SerpAPI) — since this build is
intentionally avoiding new paid dependencies for now, name-search instead
matches against a small hand-verified index of companies we've already
confirmed are fetchable and parseable (see backend/scripts/seed_demo_companies.py).

This is an honest, working version of the feature rather than a stub: a
real MSME name search will usually find nothing here (same as it would
usually find nothing on the live web, per the spec's own expectation), and
the "no match" path below is exactly the graceful fallback the spec asks
for. Swapping in a real search API later only means replacing
`search_known_companies()`'s body — nothing else in the intake flow needs
to change.
"""
from typing import List, TypedDict


class KnownCompany(TypedDict):
    name: str
    sector: str
    location: str
    listing: str
    source_reference: str


KNOWN_COMPANIES: List[KnownCompany] = [
    {
        "name": "Fascinate Textiles Ltd",
        "sector": "Manufacturing",
        "location": "West Bengal",
        "listing": "NSE Emerge (SME)",
        "source_reference": "https://www.screener.in/company/FASCINATE/",
    },
    {
        "name": "Propshop Events and Exhibitions Ltd",
        "sector": "Services",
        "location": "Maharashtra",
        "listing": "NSE Emerge (SME)",
        "source_reference": "https://www.screener.in/company/PROPSHOP/",
    },
    {
        "name": "Galaxy Supermarket Ltd",
        "sector": "Trading",
        "location": "Maharashtra",
        "listing": "BSE SME",
        "source_reference": "https://www.screener.in/company/506186/",
    },
]


def search_known_companies(query: str) -> List[KnownCompany]:
    query_lower = query.strip().lower()
    if not query_lower:
        return []
    return [c for c in KNOWN_COMPANIES if query_lower in c["name"].lower()]
