#!/usr/bin/env python3
"""
sla_tracker.py

Tracks days since last outreach for each scored Rula referral partner practice
and flags SLA status based on tier-specific thresholds.

SLA rules:
  Tier 1  -  URGENT - SLA BREACH : not contacted within 48 hours (2 days)
  Tier 1  -  AT RISK             : 1 day since contact (within 24 hrs of SLA)
  Tier 2  -  OVERDUE             : not contacted within 7 days
  Tier 2  -  AT RISK             : 5-7 days since contact (approaching SLA)
  Tier 3  -  MONITOR             : no hard SLA; tracked for awareness only
"""

import csv
from dataclasses import dataclass
from typing import List

from rula_partnership_scorer import (
    PRACTICES,
    score_practice,
    _get_tier,
    _outreach_action,
)

# ── SLA thresholds ────────────────────────────────────────────────────────────
SLA_DAYS = {
    "Tier 1": 2,  # 48 hours
    "Tier 2": 7,  # 7 days
}
AT_RISK_FROM = {
    "Tier 1": 1,  # AT RISK once >= 1 day (24 hrs to SLA)
    "Tier 2": 5,  # AT RISK once >= 5 days (2 days to SLA)
}

# ── Sample outreach data (days since last contact, keyed by practice name) ────
DAYS_SINCE_CONTACT = {
    "Sunrise Family Medicine":    3,
    "Metro Health Associates":    18,
    "Valley Primary Care":        6,
    "Lakewood Medical Group":     22,
    "Clearwater Pediatrics":      2,
    "Northside Community Clinic": 11,
    "Mountain View OB/GYN":       4,
    "South Bay Family Practice":  52,
    "Riverside Health Center":    9,
    "Westside Internal Medicine": 7,
}

PRACTICE_OWNERS = {
    "Sunrise Family Medicine":    "Jamie Reyes",
    "Metro Health Associates":    "Marcus Webb",
    "Valley Primary Care":        "Priya Shah",
    "Lakewood Medical Group":     "Marcus Webb",
    "Clearwater Pediatrics":      "Dana Okon",
    "Northside Community Clinic": "Tyler Brooks",
    "Mountain View OB/GYN":       "Jamie Reyes",
    "South Bay Family Practice":  "Priya Shah",
    "Riverside Health Center":    "Dana Okon",
    "Westside Internal Medicine": "Tyler Brooks",
}

# ── Status constants ──────────────────────────────────────────────────────────
URGENT   = "URGENT - SLA BREACH"
OVERDUE  = "OVERDUE"
AT_RISK  = "AT RISK"
ON_TRACK = "ON TRACK"
MONITOR  = "MONITOR"

STATUS_ORDER = {URGENT: 0, OVERDUE: 1, AT_RISK: 2, ON_TRACK: 3, MONITOR: 4}
STATUS_BADGE = {
    URGENT:   "[!!!]",
    OVERDUE:  "[OVR]",
    AT_RISK:  "[ ! ]",
    ON_TRACK: "[ OK]",
    MONITOR:  "[ - ]",
}


# ── Data model ────────────────────────────────────────────────────────────────
@dataclass
class SLARecord:
    name: str
    practice_type: str
    location: str
    score: float
    tier: str
    owner: str
    days_since_contact: int
    sla_days: int       # applicable SLA threshold in days (0 = none)
    days_overdue: int   # days past SLA (0 if not overdue)
    status: str
    recommended_action: str


# ── Helpers ───────────────────────────────────────────────────────────────────
def _short_tier(full_tier: str) -> str:
    for t in ("Tier 1", "Tier 2", "Tier 3"):
        if t in full_tier:
            return t
    return "Unknown"


def _compute_status(tier: str, days: int) -> str:
    if tier not in SLA_DAYS:
        return MONITOR
    sla = SLA_DAYS[tier]
    at_risk_threshold = AT_RISK_FROM[tier]
    if days > sla:
        return URGENT if tier == "Tier 1" else OVERDUE
    if days >= at_risk_threshold:
        return AT_RISK
    return ON_TRACK


def _days_overdue(tier: str, days: int) -> int:
    return max(0, days - SLA_DAYS.get(tier, days))


# ── Record builder ────────────────────────────────────────────────────────────
def build_sla_records(practices) -> List[SLARecord]:
    records = []
    for p in practices:
        full_tier = _get_tier(p)
        tier      = _short_tier(full_tier)
        days      = DAYS_SINCE_CONTACT.get(p.name, 0)

        records.append(SLARecord(
            name               = p.name,
            practice_type      = p.practice_type,
            location           = p.location,
            score              = p.score,
            tier               = tier,
            owner              = PRACTICE_OWNERS.get(p.name, "Unassigned"),
            days_since_contact = days,
            sla_days           = SLA_DAYS.get(tier, 0),
            days_overdue       = _days_overdue(tier, days),
            status             = _compute_status(tier, days),
            recommended_action = _outreach_action(p, full_tier),
        ))
    return records


# ── Report ────────────────────────────────────────────────────────────────────
STATUS_SECTION_LABEL = {
    URGENT:   "URGENT - SLA BREACH  (Tier 1: not contacted within 48 hours)",
    OVERDUE:  "OVERDUE  (Tier 2: not contacted within 7 days)",
    AT_RISK:  "AT RISK  (approaching SLA threshold)",
    ON_TRACK: "ON TRACK",
    MONITOR:  "MONITOR  (Tier 3: no hard SLA)",
}


def print_sla_report(records: List[SLARecord]) -> None:
    sorted_records = sorted(
        records,
        key=lambda r: (STATUS_ORDER.get(r.status, 99), -r.days_since_contact),
    )

    W = 80
    print()
    print("=" * W)
    print("  RULA PARTNER OUTREACH  -  SLA TRACKER")
    print("=" * W)
    print("  SLA rules:"
          "  Tier 1 = 48 hrs (2 days)"
          "  |  Tier 2 = 7 days"
          "  |  Tier 3 = no SLA")
    print("=" * W)

    prev_status = None
    for r in sorted_records:
        if r.status != prev_status:
            if prev_status is not None:
                print()
            print(f"\n  {STATUS_BADGE[r.status]}  {STATUS_SECTION_LABEL[r.status]}")
            print("  " + "-" * (W - 2))
            prev_status = r.status

        overdue_note = f"  ({r.days_overdue}d past SLA)" if r.days_overdue else ""
        sla_label    = f"SLA: {r.sla_days}d" if r.sla_days else "no SLA"

        print(f"  {STATUS_BADGE[r.status]}  {r.name:<34}  {r.tier}"
              f"  |  Score: {r.score:4.1f}"
              f"  |  {r.days_since_contact}d since contact{overdue_note}")
        print(f"          Owner: {r.owner:<16}"
              f"  {r.practice_type:<28}  {r.location}  [{sla_label}]")
        print(f"          Action: {r.recommended_action}")

    # ── Summary counts ────────────────────────────────────────────────────────
    print()
    print("=" * W)
    print("  SUMMARY")
    print("=" * W)
    for status in (URGENT, OVERDUE, AT_RISK, ON_TRACK, MONITOR):
        count = sum(1 for r in records if r.status == status)
        print(f"  {STATUS_BADGE[status]}  {status:<22}  {count} practice{'s' if count != 1 else ''}")

    # ── Owner action callout ──────────────────────────────────────────────────
    needs_action = [r for r in records if r.status in (URGENT, OVERDUE)]
    if needs_action:
        print()
        print("  OWNER ACTION REQUIRED:")
        print("  " + "-" * (W - 2))
        by_owner: dict = {}
        for r in needs_action:
            by_owner.setdefault(r.owner, []).append(r)
        for owner, items in sorted(by_owner.items()):
            for r in sorted(items, key=lambda r: -r.days_since_contact):
                print(f"  {owner:<16}  [{r.days_since_contact:>2}d]  "
                      f"{r.name:<34}  {r.status}")

    print()
    print("=" * W)


# ── CSV export ────────────────────────────────────────────────────────────────
def export_sla_to_csv(records: List[SLARecord], filepath: str) -> None:
    sorted_records = sorted(
        records,
        key=lambda r: (STATUS_ORDER.get(r.status, 99), -r.days_since_contact),
    )

    fieldnames = [
        "Status", "Practice Name", "Practice Type", "Location",
        "Tier", "Score", "Owner", "Days Since Contact",
        "SLA (days)", "Days Overdue", "Recommended Action",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in sorted_records:
            writer.writerow({
                "Status":               r.status,
                "Practice Name":        r.name,
                "Practice Type":        r.practice_type,
                "Location":             r.location,
                "Tier":                 r.tier,
                "Score":                r.score,
                "Owner":                r.owner,
                "Days Since Contact":   r.days_since_contact,
                "SLA (days)":           r.sla_days if r.sla_days else "N/A",
                "Days Overdue":         r.days_overdue if r.days_overdue else "",
                "Recommended Action":   r.recommended_action,
            })


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    scored  = [score_practice(p) for p in PRACTICES]
    records = build_sla_records(scored)
    print_sla_report(records)
    export_sla_to_csv(records, "rula_sla_tracker.csv")
    print(f"  CSV export saved to: rula_sla_tracker.csv")


if __name__ == "__main__":
    main()
