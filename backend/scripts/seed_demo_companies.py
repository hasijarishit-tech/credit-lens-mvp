"""Loads three real BSE SME / NSE Emerge companies (sourced from their public
Screener.in pages) as demo data: computes their real scores via the actual
scoring engine, and writes users/companies/financial_records/scores into the
app database. Run once to seed the hackathon demo dataset.
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine, SessionLocal
from app.models import Company, FinancialRecord, Score, Sector, SourceType, TrustLabel, User, UserRole
from app.auth import hash_password
from app.scoring.pipeline import run_pipeline

Base.metadata.create_all(bind=engine)

COMPANIES = [
    {
        "company_name": "Fascinate Textiles Ltd",
        "sector": Sector.manufacturing,
        "financial_year": "FY2025-26",
        "source_reference": "https://www.screener.in/company/FASCINATE/",
        "record": {
            "balance_sheet": {
                "cash_and_equivalents": 43_500_000,
                "receivables": 248_220_000,
                "inventory": 534_780_000,
                "other_current_assets": 43_500_000,
                "fixed_assets": 60_000_000,
                "current_liabilities": 360_000_000,
                "payables": 252_000_000,
                "long_term_debt": 260_000_000,
                "equity": 310_000_000,
            },
            "income_statement": {
                "revenue": 1_160_000_000,
                "cogs": 920_000_000,
                "operating_expenses": 0,
                "depreciation": 10_000_000,
                "interest_expense": 20_000_000,
                "net_income": 150_000_000,
            },
            "prior_year": {
                "balance_sheet": {
                    "cash_and_equivalents": 18_000_000,
                    "receivables": 131_320_000,
                    "inventory": 192_680_000,
                    "other_current_assets": 18_000_000,
                    "fixed_assets": 60_000_000,
                    "current_liabilities": 140_000_000,
                    "payables": 98_000_000,
                    "long_term_debt": 180_000_000,
                    "equity": 100_000_000,
                },
                "income_statement": {
                    "revenue": 590_000_000,
                    "cogs": 490_000_000,
                    "operating_expenses": 0,
                    "depreciation": 10_000_000,
                    "interest_expense": 20_000_000,
                    "net_income": 60_000_000,
                },
            },
        },
        "extraction_notes": {
            "overall_confidence": "medium",
            "warnings": [
                "Screener.in's public summary reports Sales/Expenses/Borrowings/Other "
                "Liabilities as aggregates, not the granular line items this schema "
                "wants. COGS and operating expenses could not be separated, so the "
                "full 'Expenses' line was assigned to cogs (operating_expenses set to "
                "0) — this makes EBIT-based ratios accurate but means gross_margin "
                "here effectively equals operating margin, not a true gross margin.",
                "Receivables and inventory were estimated by allocating the "
                "aggregated 'Other Assets' balance sheet line using Screener's own "
                "Debtor Days / Inventory Days ratios as weights, not read directly "
                "as line items.",
                "Payables estimated as 70% of the 'Other Liabilities' aggregate "
                "(a typical MSME trade-payables share), not a directly reported figure.",
                "Equity Capital rose from ₹1 Cr to ₹10 Cr between FY25 and FY26 — "
                "this company completed an SME IPO in this period, which is why "
                "equity jumped independent of retained profit.",
            ],
        },
        "msme_narrative": (
            "Your business is rated BBB, a solid middle grade — you're clearly growing fast "
            "(revenue nearly doubled this year, up 97%) and profit margins are healthy (13% "
            "net margin), but the numbers show growth is eating your cash.\n\n"
            "Your inventory grew by about ₹34 crore this year alone, pushing inventory days "
            "up to 212 — meaning stock now sits on your shelves for roughly seven months "
            "before it sells, well above the 75-day norm for manufacturers your size. That, "
            "combined with customers taking about 78 days to pay you, is why your operating "
            "cash flow was actually negative ₹14.5 crore this year, even though you reported "
            "a real profit of ₹15 crore. This is the biggest thing to fix: reducing inventory "
            "days toward the sector norm would free up a large amount of cash without needing "
            "a single new sale.\n\n"
            "Your debt levels (₹0.84 borrowed for every ₹1 of equity) and interest coverage "
            "(11.5x — you earn far more than enough to cover interest) are both healthy, and "
            "liquidity is comfortable too. The one number to watch closely: if inventory keeps "
            "growing this fast relative to sales, next year's debt service coverage could stay "
            "below 1.0, meaning cash generated won't fully cover debt obligations — worth "
            "acting on now while profit is strong."
        ),
        "lender_summary": (
            "Fascinate Textiles Ltd (Manufacturing) scores BBB (61.2/100). Revenue grew 97% "
            "YoY to ₹116 Cr, with a healthy 12.9% net margin and 40.4% ROCE — profitability "
            "and liquidity are strong (bucket scores 80.5 and 69.0).\n\n"
            "The key underwriting concern is cash conversion: operating cash flow is "
            "estimated at -₹14.5 Cr despite ₹15 Cr of reported net income, driven by "
            "inventory ballooning ₹34.2 Cr YoY (inventory days 212 vs a 75-day sector norm) "
            "and receivables extending to 78 days. Estimated DSCR is negative (-2.0x) this "
            "year on that basis — debt service coverage is currently not supported by "
            "operating cash generation, though leverage itself is moderate (D/E 0.84x, "
            "interest coverage 11.5x). Recommend requesting a working-capital breakdown and "
            "inventory aging before extending additional term debt; growth is real but "
            "currently self-funded by stretching payables and drawing down cash rather than "
            "converting profit to cash."
        ),
    },
    {
        "company_name": "Propshop Events and Exhibitions Ltd",
        "sector": Sector.services,
        "financial_year": "FY2025-26",
        "source_reference": "https://www.screener.in/company/PROPSHOP/",
        "record": {
            "balance_sheet": {
                "cash_and_equivalents": 126_790_000,
                "receivables": 109_310_000,
                "inventory": 0,
                "other_current_assets": 31_700_000,
                "fixed_assets": 3_800_000,
                "current_liabilities": 76_600_000,
                "payables": 53_620_000,
                "long_term_debt": 1_700_000,
                "equity": 193_300_000,
            },
            "income_statement": {
                "revenue": 702_900_000,
                "cogs": 591_700_000,
                "operating_expenses": 0,
                "depreciation": 1_500_000,
                "interest_expense": 1_800_000,
                "net_income": 80_200_000,
            },
            "prior_year": {
                "balance_sheet": {
                    "cash_and_equivalents": 97_700_000,
                    "receivables": 60_500_000,
                    "inventory": 0,
                    "other_current_assets": 24_500_000,
                    "fixed_assets": 1_900_000,
                    "current_liabilities": 65_100_000,
                    "payables": 45_570_000,
                    "long_term_debt": 6_300_000,
                    "equity": 113_200_000,
                },
                "income_statement": {
                    "revenue": 515_200_000,
                    "cogs": 428_800_000,
                    "operating_expenses": 0,
                    "depreciation": 1_100_000,
                    "interest_expense": 1_700_000,
                    "net_income": 63_200_000,
                },
            },
        },
        "extraction_notes": {
            "overall_confidence": "medium",
            "warnings": [
                "Same Screener.in aggregation limitation as above: full 'Expenses' "
                "line assigned to cogs; gross_margin here effectively equals "
                "operating margin.",
                "This is an events/exhibition services business — inventory is "
                "genuinely ~0 (no stock-in-trade), consistent with Screener showing "
                "no Inventory Days figure for this company.",
                "Receivables computed directly from Screener's reported Debtor Days "
                "x revenue (a reliable figure here). Cash vs other-current-assets "
                "split within the remaining balance is estimated (80/20).",
                "Payables estimated as 70% of the 'Other Liabilities' aggregate.",
            ],
        },
        "msme_narrative": (
            "Great result — your business is graded A (83.5/100), among the strongest scores "
            "this tool gives. You're almost debt-free (just ₹0.01 borrowed per ₹1 of equity) "
            "and earn 61x your interest expense in operating profit, so lenders will see very "
            "low leverage risk. Revenue grew a strong 36% this year to ₹7 crore, with an 11.4% "
            "net margin and a very efficient cash cycle (your cash conversion cycle is just 24 "
            "days, since you carry no inventory).\n\n"
            "The one thing worth watching: your receivables grew 81% this year — more than "
            "double your revenue growth of 36%. In plain terms, clients are taking longer to "
            "pay you relative to how much you're billing them; receivable days rose to about "
            "57 days. This hasn't hurt you yet — you still generate strong operating cash flow "
            "(about ₹4.1 crore) — but if this gap between receivables growth and revenue "
            "growth continues, it will eventually squeeze your cash even while your top line "
            "keeps growing. Tightening payment terms with a few of your larger clients now, "
            "while your grade is strong, is the easiest way to protect this score."
        ),
        "lender_summary": (
            "Propshop Events (Services) scores A (83.5/100) — the strongest of this "
            "portfolio. Balance sheet is very conservative: D/E of 0.01x, interest coverage "
            "60.9x, DSCR 19.1x, current ratio 3.5x. Revenue grew 36% YoY to ₹7.03 Cr with "
            "11.4% net margin and 56.3% ROCE; no inventory risk (events/exhibition services "
            "business).\n\n"
            "Only flag: receivables grew 81% YoY versus 36% revenue growth, pushing "
            "receivable days to 57 (up from 43). Operating cash flow remains solidly "
            "positive (₹4.1 Cr) so this is not yet a cash concern, but the gap is worth "
            "monitoring at next review — if receivables growth keeps outpacing revenue, "
            "DSCR and liquidity could compress from today's very comfortable levels. Low "
            "credit risk currently; suitable for standard terms, with a note to re-check "
            "receivables aging at next review."
        ),
    },
    {
        "company_name": "Galaxy Supermarket Ltd",
        "sector": Sector.trading,
        "financial_year": "FY2025-26",
        "source_reference": "https://www.screener.in/company/506186/",
        "record": {
            "balance_sheet": {
                "cash_and_equivalents": 35_880_000,
                "receivables": 2_900_000,
                "inventory": 35_880_000,
                "other_current_assets": 17_940_000,
                "fixed_assets": 103_700_000,
                "current_liabilities": 166_500_000,
                "payables": 116_550_000,
                "long_term_debt": 212_200_000,
                "equity": -182_400_000,
            },
            "income_statement": {
                "revenue": 423_100_000,
                "cogs": 384_800_000,
                "operating_expenses": 0,
                "depreciation": 12_800_000,
                "interest_expense": 12_700_000,
                "net_income": 15_200_000,
            },
            "prior_year": {
                "balance_sheet": {
                    "cash_and_equivalents": 34_280_000,
                    "receivables": 3_600_000,
                    "inventory": 34_280_000,
                    "other_current_assets": 17_140_000,
                    "fixed_assets": 96_700_000,
                    "current_liabilities": 170_200_000,
                    "payables": 119_140_000,
                    "long_term_debt": 213_500_000,
                    "equity": -197_700_000,
                },
                "income_statement": {
                    "revenue": 152_300_000,
                    "cogs": 124_300_000,
                    "operating_expenses": 0,
                    "depreciation": 5_800_000,
                    "interest_expense": 12_300_000,
                    "net_income": -32_900_000,
                },
            },
        },
        "extraction_notes": {
            "overall_confidence": "low",
            "warnings": [
                "This company (formerly a supermarket chain, now operating as "
                "'Galaxy Cloud Kitchens') has NEGATIVE equity (accumulated losses "
                "exceed paid-in capital) — confirmed directly from Screener's "
                "reported Equity Capital + Reserves, not an extraction error.",
                "Inventory Days / Days Payable rows on Screener were inconsistently "
                "aligned across the 12-year table for this company, so inventory "
                "was estimated as a proportional share of the 'Other Assets' "
                "aggregate rather than derived from a specific ratio — lower "
                "confidence than the other two demo companies.",
                "Same COGS/opex aggregation limitation as the other two records.",
            ],
        },
        "msme_narrative": (
            "Your score is BB (41.6/100), reflecting some real financial strain that needs "
            "attention. The biggest issue: your business currently has negative net worth "
            "(equity of -₹18.2 crore) — accumulated losses from past years have wiped out "
            "shareholders' capital, and total liabilities now exceed total assets. This alone "
            "is a serious red flag to any lender, regardless of other numbers, and it's the "
            "first thing to address, likely through fresh equity investment or sustained "
            "profitability to rebuild reserves.\n\n"
            "There's real good news too: revenue grew 178% this year (from ₹15.2 crore to "
            "₹42.3 crore) as the business shifted into B2B food production, and you returned "
            "to profit (₹1.52 crore net income, versus a ₹3.29 crore loss last year). Your "
            "inventory efficiency is strong (34 days) and you collect from customers quickly "
            "(2.5 days).\n\n"
            "But liquidity is tight — you have only ₹0.56 in current assets for every ₹1 of "
            "current liabilities — and estimated cash flow covers only 44% of what's needed "
            "for debt obligations this year. Priority order: rebuild equity first, then "
            "improve liquidity; the revenue turnaround gives you a real foundation to do both "
            "if it's sustained."
        ),
        "lender_summary": (
            "Galaxy Supermarket Ltd (Trading, operating as Galaxy Cloud Kitchens) scores BB "
            "(41.6/100) — elevated risk, recommend enhanced due diligence. Critical flag: "
            "negative equity of -₹18.24 Cr — accumulated losses exceed paid-in capital; "
            "debt-to-equity and ROCE are not meaningfully computable while this persists. "
            "Liquidity is weak (current ratio 0.56x, quick ratio 0.23x) and DSCR is 0.44x — "
            "estimated operating cash flow covers less than half of estimated annual debt "
            "obligations.\n\n"
            "Mitigating factors: revenue grew 178% YoY (₹15.2 Cr to ₹42.3 Cr) on a B2B pivot, "
            "and the company returned to net profit (₹1.52 Cr vs a ₹3.29 Cr prior-year loss) "
            "with efficient working capital (34 inventory days, 2.5 debtor days). If "
            "considering exposure, structure would need to address the equity deficit "
            "directly — e.g. promoter capital infusion or a profit-retention covenant — "
            "before extending unsecured term debt; current balance sheet cannot absorb "
            "additional leverage."
        ),
    },
]


def main():
    db = SessionLocal()

    lender = db.query(User).filter(User.email == "demo-lender@creditlens.dev").first()
    if not lender:
        lender = User(
            name="Demo Lender",
            org_name="CreditLens Demo NBFC",
            email="demo-lender@creditlens.dev",
            password_hash=hash_password("demo-password-123"),
            role=UserRole.lender,
        )
        db.add(lender)
        db.commit()
        db.refresh(lender)
        print(f"Created demo lender user: {lender.email} / demo-password-123")

    for entry in COMPANIES:
        existing = db.query(Company).filter(Company.name == entry["company_name"]).first()
        if existing:
            print(f"Skipping {entry['company_name']} — already loaded")
            continue

        company = Company(name=entry["company_name"], sector=entry["sector"], owner_user_id=lender.id)
        db.add(company)
        db.commit()
        db.refresh(company)

        extracted_data = dict(entry["record"])
        extracted_data["company_name"] = entry["company_name"]
        extracted_data["financial_year"] = entry["financial_year"]

        fin_record = FinancialRecord(
            company_id=company.id,
            financial_year=entry["financial_year"],
            source_type=SourceType.source_link,
            source_reference=entry["source_reference"],
            trust_label=TrustLabel.verified,
            extracted_data=extracted_data,
            extraction_confidence=entry["extraction_notes"],
            created_by_user_id=lender.id,
        )
        db.add(fin_record)
        db.commit()
        db.refresh(fin_record)

        result = run_pipeline(entry["record"], sector=entry["sector"].value)

        score = Score(
            financial_record_id=fin_record.id,
            composite_score=result["composite_score"],
            letter_grade=result["letter_grade"],
            ratios=result["ratios"],
            bucket_scores=result["bucket_scores"],
            anomaly_flags=result["anomaly_flags"],
            derived_cash_flow=result.get("cash_flow"),
            narrative_text=entry["msme_narrative"],
            lender_summary_text=entry["lender_summary"],
        )
        db.add(score)
        db.commit()

        print(f"\n{entry['company_name']} ({entry['sector'].value})")
        print(f"  Composite score: {result['composite_score']} -> {result['letter_grade']}")
        print(f"  Bucket scores: {json.dumps(result['bucket_scores'])}")
        print(f"  Anomaly flags: {[f['flag'] for f in result['anomaly_flags']]}")
        print(f"  Sanity issues: {[i['severity'] for i in result.get('issues', [])]}")

    db.close()


if __name__ == "__main__":
    main()
