#!/usr/bin/env python3
"""
rula_partnership_scorer.py

Scores healthcare practices as potential Rula mental health referral partners.

Scoring criteria (100 points total):
  Providers (25 pts)  - larger panels generate more referral volume
  BH Gap    (35 pts)  - unmet behavioral health need drives partnership value
  Networks  (25 pts)  - insurance overlap reduces billing friction
  Volume    (15 pts)  - higher monthly visits = more patients who may need BH
"""

import csv
from dataclasses import dataclass, field
from typing import List

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# ── Rula's accepted insurance networks ────────────────────────────────────────
RULA_NETWORKS = {
    "Aetna", "Anthem", "Blue Cross Blue Shield", "Cigna", "Humana",
    "Medicaid", "Medicare", "Oscar Health", "United Healthcare",
    "Optum", "Molina Healthcare", "Centene",
}

# ── Data model ────────────────────────────────────────────────────────────────
@dataclass
class Practice:
    name: str
    practice_type: str
    location: str
    provider_count: int
    bh_referral_gap: str          # "none" | "partial" | "full"
    insurance_networks: List[str]
    monthly_patient_volume: int
    notes: str = ""

    # Populated by score_practice()
    score: float = field(default=0.0, init=False)
    breakdown: dict = field(default_factory=dict, init=False)


# ── Scoring functions ─────────────────────────────────────────────────────────
def _score_providers(count: int) -> float:
    """Max 25 pts."""
    if count >= 21: return 25.0
    if count >= 11: return 20.0
    if count >= 6:  return 15.0
    if count >= 3:  return 10.0
    return 5.0


def _score_bh_gap(gap: str) -> float:
    """Max 35 pts. Full gap = no in-house BH, highest unmet need."""
    return {"full": 35.0, "partial": 20.0, "none": 5.0}.get(gap.lower(), 0.0)


def _score_networks(networks: List[str]) -> float:
    """Max 25 pts. Scored proportionally by overlap with Rula's panel."""
    if not networks:
        return 0.0
    overlap = len(set(networks) & RULA_NETWORKS)
    return round(min((overlap / len(RULA_NETWORKS)) * 25, 25.0), 1)


def _score_volume(volume: int) -> float:
    """Max 15 pts."""
    if volume >= 2001: return 15.0
    if volume >= 1001: return 11.0
    if volume >= 500:  return 7.0
    return 3.0


def score_practice(p: Practice) -> Practice:
    providers = _score_providers(p.provider_count)
    bh        = _score_bh_gap(p.bh_referral_gap)
    networks  = _score_networks(p.insurance_networks)
    volume    = _score_volume(p.monthly_patient_volume)

    p.score     = round(providers + bh + networks + volume, 1)
    p.breakdown = {
        "Providers": providers,
        "BH Gap":    bh,
        "Networks":  networks,
        "Volume":    volume,
    }
    return p


# ── Sample practices (fake data) ──────────────────────────────────────────────
PRACTICES = [
    Practice(
        name="Sunrise Family Medicine",
        practice_type="Primary Care",
        location="Phoenix, AZ",
        provider_count=14,
        bh_referral_gap="full",
        insurance_networks=[
            "Aetna", "Cigna", "United Healthcare", "Medicare", "Blue Cross Blue Shield"
        ],
        monthly_patient_volume=2400,
        notes="Large suburban group; no on-site therapist; high PHQ-9 screening rates.",
    ),
    Practice(
        name="Metro Health Associates",
        practice_type="Internal Medicine",
        location="Chicago, IL",
        provider_count=22,
        bh_referral_gap="partial",
        insurance_networks=[
            "Aetna", "Anthem", "Medicare", "Medicaid", "Cigna", "United Healthcare", "Humana"
        ],
        monthly_patient_volume=3100,
        notes="Urban multi-specialty group; 1 social worker for 22 providers, 6-week waitlist.",
    ),
    Practice(
        name="Valley Primary Care",
        practice_type="Primary Care",
        location="Fresno, CA",
        provider_count=4,
        bh_referral_gap="full",
        insurance_networks=["Medicaid", "Medicare", "Molina Healthcare"],
        monthly_patient_volume=620,
        notes="Rural-serving practice; providers cite BH as biggest unmet patient need.",
    ),
    Practice(
        name="Lakewood Medical Group",
        practice_type="Primary Care / Urgent Care",
        location="Denver, CO",
        provider_count=9,
        bh_referral_gap="partial",
        insurance_networks=[
            "Aetna", "Cigna", "United Healthcare", "Medicare", "Centene"
        ],
        monthly_patient_volume=1750,
        notes="Mixed PCP + urgent care; occasional psych consult but no ongoing BH support.",
    ),
    Practice(
        name="Clearwater Pediatrics",
        practice_type="Pediatrics",
        location="Tampa, FL",
        provider_count=6,
        bh_referral_gap="full",
        insurance_networks=["Medicaid", "Humana", "Cigna", "Blue Cross Blue Shield"],
        monthly_patient_volume=1300,
        notes="High ADHD and anxiety caseload; average 8-week wait for BH referrals.",
    ),
    Practice(
        name="Northside Community Clinic",
        practice_type="FQHC",
        location="Atlanta, GA",
        provider_count=11,
        bh_referral_gap="partial",
        insurance_networks=[
            "Medicaid", "Medicare", "Molina Healthcare", "Centene", "United Healthcare"
        ],
        monthly_patient_volume=2200,
        notes="Integrated BH model but only 2 counselors for 11 PCPs; chronic shortage.",
    ),
    Practice(
        name="Mountain View OB/GYN",
        practice_type="OB/GYN",
        location="Salt Lake City, UT",
        provider_count=5,
        bh_referral_gap="full",
        insurance_networks=["Aetna", "Blue Cross Blue Shield", "United Healthcare", "Optum"],
        monthly_patient_volume=900,
        notes="High postpartum depression screening; no current BH referral pathway.",
    ),
    Practice(
        name="South Bay Family Practice",
        practice_type="Primary Care",
        location="San Jose, CA",
        provider_count=2,
        bh_referral_gap="none",
        insurance_networks=["Aetna", "Oscar Health", "Medicare"],
        monthly_patient_volume=380,
        notes="Small 2-physician practice; embedded therapist covers most BH needs.",
    ),
    Practice(
        name="Riverside Health Center",
        practice_type="Internal Medicine",
        location="Houston, TX",
        provider_count=8,
        bh_referral_gap="partial",
        insurance_networks=[
            "United Healthcare", "Humana", "Medicare", "Medicaid", "Aetna", "Cigna"
        ],
        monthly_patient_volume=1500,
        notes="Strong network overlap; part-time psychiatrist 1 day/week, overwhelmed.",
    ),
    Practice(
        name="Westside Internal Medicine",
        practice_type="Internal Medicine",
        location="Los Angeles, CA",
        provider_count=7,
        bh_referral_gap="full",
        insurance_networks=[
            "Anthem", "Aetna", "Cigna", "Medicare", "Molina Healthcare", "Centene"
        ],
        monthly_patient_volume=1100,
        notes="Diverse patient population; providers rank mental health as top unmet need.",
    ),
]


# ── Reporting ─────────────────────────────────────────────────────────────────
_GAP_LABELS = {"full": "Full Gap  ", "partial": "Partial   ", "none": "No Gap    "}

TIER_RULES = [
    ("Tier 1 - High Priority   (score >= 70)", lambda s: s >= 70),
    ("Tier 2 - Medium Priority (score 50-69)", lambda s: 50 <= s < 70),
    ("Tier 3 - Lower Priority  (score <  50)", lambda s: s < 50),
]


def _bar(score: float, width: int = 50) -> str:
    filled = round(score / 100 * width)
    return "#" * filled + "-" * (width - filled)


def _outreach_action(p: "Practice", tier: str) -> str:
    """Return a recommended outreach action string based on the practice's tier."""
    if tier.strip().startswith("Tier 1"):
        hook = p.notes.split(";")[0].strip().rstrip(".")
        return f"Personalized email - Lead with: {hook}"
    if tier.strip().startswith("Tier 2"):
        return "Templated intro email - Use standard Rula referral partner template"
    return "Nurture list - Add to drip sequence; revisit in 90 days"


def _get_tier(p: Practice) -> str:
    """Return the tier label for a practice based on its score."""
    return next(
        (label for label, cond in TIER_RULES if cond(p.score)),
        "Unclassified",
    )


def _tier_sort_key(p: Practice) -> tuple:
    """Sort key: Tier 1 first, then Tier 2, then Tier 3; within tier, by score desc."""
    tier_order = {"Tier 1 - High Priority   (score >= 70)": 0,
                  "Tier 2 - Medium Priority (score 50-69)": 1,
                  "Tier 3 - Lower Priority  (score <  50)": 2}
    tier = _get_tier(p)
    return (tier_order.get(tier, 99), -p.score)


# Tier colors for bar chart (hex)
TIER_COLORS = {
    "Tier 1 - High Priority   (score >= 70)": "#2e7d32",
    "Tier 2 - Medium Priority (score 50-69)": "#ed6c02",
    "Tier 3 - Lower Priority  (score <  50)": "#757575",
}


def plot_score_bar_chart(practices: List[Practice], filepath: str = "rula_partner_scores.png") -> None:
    """
    Generate a horizontal bar chart of practice scores, colored by tier.
    Practices are sorted by tier (Tier 1 first) then by score descending.
    """
    if not HAS_MATPLOTLIB:
        print("  (matplotlib not installed - skip bar chart. Run: pip install matplotlib)")
        return

    sorted_practices = sorted(practices, key=_tier_sort_key)
    names = [p.name for p in sorted_practices]
    scores = [p.score for p in sorted_practices]
    colors = [TIER_COLORS.get(_get_tier(p), "#9e9e9e") for p in sorted_practices]

    fig_h = max(6, 4 + 0.4 * len(sorted_practices))
    fig, ax = plt.subplots(figsize=(10, fig_h))
    ax.barh(names, scores, color=colors, edgecolor="white", linewidth=0.5)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Score")
    ax.set_ylabel("Practice")
    ax.set_title("Rula Referral Partner Scores by Tier")
    ax.invert_yaxis()

    # Legend for tiers
    legend_patches = [
        mpatches.Patch(color=TIER_COLORS[t[0]], label=t[0].split("-")[0].strip())
        for t in TIER_RULES if t[0] in TIER_COLORS
    ]
    ax.legend(handles=legend_patches, loc="lower right", fontsize=8)

    plt.tight_layout()
    plt.savefig(filepath, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  Bar chart saved to: {filepath}")


def print_tier_summary(practices: List[Practice]) -> None:
    """Print a summary of practices per tier with count and average score."""
    W = 60
    print("\n" + "=" * W)
    print("  TIER SUMMARY")
    print("=" * W)

    for label, condition in TIER_RULES:
        matches = [p for p in practices if condition(p.score)]
        count = len(matches)
        avg_score = sum(p.score for p in matches) / count if count else 0.0
        print(f"  {label}")
        print(f"    Practices: {count}   |   Average score: {avg_score:.1f} / 100")
        print()

    print("=" * W)


def print_report(practices: List[Practice]) -> None:
    ranked = sorted(practices, key=lambda p: p.score, reverse=True)
    W = 82

    print("=" * W)
    print("  RULA REFERRAL PARTNER PRIORITIZATION REPORT")
    print("=" * W)
    print("  Scoring weights:  Providers 25 pt  |  BH Gap 35 pt  |"
          "  Networks 25 pt  |  Volume 15 pt")
    print("=" * W)

    for rank, p in enumerate(ranked, start=1):
        gap_label    = _GAP_LABELS.get(p.bh_referral_gap.lower(), p.bh_referral_gap)
        net_overlap  = len(set(p.insurance_networks) & RULA_NETWORKS)
        bd           = p.breakdown

        tier = next(
            (t for t, cond in [(t, c) for t, c in TIER_RULES] if cond(p.score)),
            "Unclassified"
        ).split("-")[0].strip()

        print(f"\n  #{rank:02d}  {p.name:<34}  Score: {p.score:5.1f} / 100   [{tier}]")
        print(f"       {p.practice_type:<28}  {p.location}")
        print(f"       Providers: {p.provider_count:<4}  "
              f"BH Status: {gap_label}  "
              f"Rula Networks: {net_overlap}/{len(RULA_NETWORKS)}  "
              f"Volume: {p.monthly_patient_volume:,}/mo")
        print(f"       [{_bar(p.score)}] {p.score:.1f}")
        print(f"       Breakdown - "
              f"Providers: {bd['Providers']:.0f}  "
              f"BH Gap: {bd['BH Gap']:.0f}  "
              f"Networks: {bd['Networks']:.1f}  "
              f"Volume: {bd['Volume']:.0f}")
        print(f"       Outreach: {_outreach_action(p, tier)}")
        print(f"       Note: {p.notes}")

    # Tier summary
    print("\n" + "=" * W)
    print("  OUTREACH TIERS SUMMARY")
    print("=" * W)
    for label, condition in TIER_RULES:
        matches = [p for p in ranked if condition(p.score)]
        print(f"\n  {label}  ({len(matches)} practice{'s' if len(matches) != 1 else ''})")
        if matches:
            for p in matches:
                net_overlap = len(set(p.insurance_networks) & RULA_NETWORKS)
                print(f"    * {p.name:<34} {p.score:5.1f}  |  "
                      f"{p.practice_type}  |  {p.location}  |  "
                      f"{net_overlap} shared plans"
                      f"  ->  {_outreach_action(p, label)}")
        else:
            print("    (none)")

    print("\n" + "=" * W)
    print("  END OF REPORT")
    print("=" * W)


def export_scored_to_csv(practices: List[Practice], filepath: str) -> None:
    """
    Generate a CSV export of scored results sorted by tier (Tier 1 first, then 2, 3),
    and by score descending within each tier.
    """
    sorted_practices = sorted(practices, key=_tier_sort_key)

    fieldnames = [
        "Rank", "Tier", "Name", "Practice Type", "Location",
        "Provider Count", "BH Referral Gap", "Insurance Networks",
        "Monthly Patient Volume", "Score",
        "Providers (pts)", "BH Gap (pts)", "Networks (pts)", "Volume (pts)",
        "Outreach Action", "Notes",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for rank, p in enumerate(sorted_practices, start=1):
            tier = _get_tier(p)
            bd = p.breakdown
            writer.writerow({
                "Rank": rank,
                "Tier": tier,
                "Name": p.name,
                "Practice Type": p.practice_type,
                "Location": p.location,
                "Provider Count": p.provider_count,
                "BH Referral Gap": p.bh_referral_gap,
                "Insurance Networks": "; ".join(p.insurance_networks),
                "Monthly Patient Volume": p.monthly_patient_volume,
                "Score": p.score,
                "Providers (pts)": bd.get("Providers", 0),
                "BH Gap (pts)": bd.get("BH Gap", 0),
                "Networks (pts)": bd.get("Networks", 0),
                "Volume (pts)": bd.get("Volume", 0),
                "Outreach Action": _outreach_action(p, tier),
                "Notes": p.notes,
            })


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    scored = [score_practice(p) for p in PRACTICES]
    print_report(scored)
    print_tier_summary(scored)
    plot_score_bar_chart(scored, "rula_partner_scores.png")
    export_scored_to_csv(scored, "rula_partner_scores.csv")
    print("\n  CSV export saved to: rula_partner_scores.csv")


if __name__ == "__main__":
    main()
