#!/usr/bin/env python3
"""
pipeline_report.py

Generates a high-level summary report of the Rula partnership pipeline:
  - Total practices by tier and average score per tier
  - Number of SLA breaches
  - Top 5 highest-priority practices with scores, tiers, and recommended actions
"""

from rula_partnership_scorer import (
    PRACTICES,
    TIER_RULES,
    score_practice,
    _get_tier,
    _outreach_action,
)
from sla_tracker import (
    build_sla_records,
    URGENT,
    OVERDUE,
)


def _short_tier(full_tier: str) -> str:
    for t in ("Tier 1", "Tier 2", "Tier 3"):
        if t in full_tier:
            return t
    return "Unknown"


def _tier_priority(full_tier: str) -> int:
    return {"Tier 1": 0, "Tier 2": 1, "Tier 3": 2}.get(_short_tier(full_tier), 9)


def print_report(practices) -> None:
    W = 72

    # ── Tier breakdown ────────────────────────────────────────────────────────
    print()
    print("=" * W)
    print("  RULA PARTNERSHIP PIPELINE  -  SUMMARY REPORT")
    print("=" * W)

    print(f"\n  {'TIER':<42}  {'PRACTICES':>9}  {'AVG SCORE':>9}")
    print("  " + "-" * (W - 2))

    for label, condition in TIER_RULES:
        matches = [p for p in practices if condition(p.score)]
        count = len(matches)
        avg = sum(p.score for p in matches) / count if count else 0.0
        short = label.split("-")[0].strip()
        print(f"  {short:<42}  {count:>9}  {avg:>8.1f}")

    print(f"\n  {'Total':<42}  {len(practices):>9}")

    # ── SLA breach count ──────────────────────────────────────────────────────
    sla_records = build_sla_records(practices)
    breaches = [r for r in sla_records if r.status in (URGENT, OVERDUE)]
    urgent_count = sum(1 for r in breaches if r.status == URGENT)
    overdue_count = sum(1 for r in breaches if r.status == OVERDUE)

    print()
    print("=" * W)
    print("  SLA STATUS")
    print("=" * W)
    print(f"\n  Total SLA breaches : {len(breaches)}")
    print(f"  Urgent (Tier 1)    : {urgent_count}  (>48 hrs since last contact)")
    print(f"  Overdue (Tier 2)   : {overdue_count}  (>7 days since last contact)")

    if breaches:
        print()
        print(f"  {'Practice':<34}  {'Tier':<6}  {'Days Since Contact':>18}  Owner")
        print("  " + "-" * (W - 2))
        for r in sorted(breaches, key=lambda r: -r.days_since_contact):
            print(f"  {r.name:<34}  {r.tier:<6}  {r.days_since_contact:>18}  {r.owner}")

    # ── Top 5 highest-priority practices ─────────────────────────────────────
    sorted_practices = sorted(
        practices,
        key=lambda p: (_tier_priority(_get_tier(p)), -p.score),
    )
    top5 = sorted_practices[:5]

    print()
    print("=" * W)
    print("  TOP 5 HIGHEST-PRIORITY PRACTICES")
    print("=" * W)

    for rank, p in enumerate(top5, start=1):
        full_tier = _get_tier(p)
        short = _short_tier(full_tier)
        action = _outreach_action(p, full_tier)
        print(f"\n  #{rank}  {p.name}")
        print(f"       Score : {p.score} / 100   Tier: {short}   {p.location}")
        print(f"       Action: {action}")

    print()
    print("=" * W)
    print("  END OF REPORT")
    print("=" * W)
    print()


def main():
    scored = [score_practice(p) for p in PRACTICES]
    print_report(scored)


if __name__ == "__main__":
    main()
