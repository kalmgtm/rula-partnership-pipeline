#!/usr/bin/env python3
"""
crm_output.py

Generates simulated Salesforce CRM records for Rula referral partner practices
scored and tiered by rula_partnership_scorer.py.

Simulated fields per record:
  SF Record ID, Account Name, Practice Type, Location, Score, Tier,
  Owner, Days Since Last Contact, SLA Status, Recommended Action, Notes
"""

import csv
import random
import string
from dataclasses import dataclass
from typing import List

from rula_partnership_scorer import (
    PRACTICES,
    score_practice,
    _get_tier,
    _outreach_action,
)

# ── SLA thresholds by tier (days) ─────────────────────────────────────────────
TIER_SLA_DAYS = {
    "Tier 1": 5,   # High priority - follow up within 5 days
    "Tier 2": 14,  # Medium priority - follow up within 2 weeks
    "Tier 3": 30,  # Lower priority - follow up within 30 days
}

# ── Sample static data keyed by practice name ─────────────────────────────────
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


# ── Data model ────────────────────────────────────────────────────────────────
@dataclass
class SalesforceRecord:
    sf_id: str
    account_name: str
    practice_type: str
    location: str
    score: float
    tier: str               # "Tier 1" | "Tier 2" | "Tier 3"
    owner: str
    days_since_contact: int
    sla_status: str         # "On Track" | "At Risk" | "Overdue"
    recommended_action: str
    notes: str


# ── Helpers ───────────────────────────────────────────────────────────────────
def _make_sf_id(seed: int) -> str:
    """Generate a deterministic fake 18-character Salesforce Account ID."""
    random.seed(seed + 42)
    alphanum = string.ascii_uppercase + string.digits
    suffix = "".join(random.choices(alphanum, k=11))
    return f"001Rula{seed:03d}{suffix}"


def _short_tier(full_tier: str) -> str:
    for t in ("Tier 1", "Tier 2", "Tier 3"):
        if t in full_tier:
            return t
    return "Unknown"


def _sla_status(days: int, tier: str) -> str:
    sla = TIER_SLA_DAYS.get(tier, 30)
    if days <= sla:
        return "On Track"
    elif days <= round(sla * 1.5):
        return "At Risk"
    else:
        return "Overdue"


def _truncate(text: str, width: int) -> str:
    return text if len(text) <= width else text[: width - 3] + "..."


# ── Record builder ────────────────────────────────────────────────────────────
def build_records(practices) -> List[SalesforceRecord]:
    records = []
    for i, p in enumerate(practices, start=1):
        full_tier  = _get_tier(p)
        short_tier = _short_tier(full_tier)
        days       = DAYS_SINCE_CONTACT.get(p.name, 7)

        records.append(SalesforceRecord(
            sf_id              = _make_sf_id(i),
            account_name       = p.name,
            practice_type      = p.practice_type,
            location           = p.location,
            score              = p.score,
            tier               = short_tier,
            owner              = PRACTICE_OWNERS.get(p.name, "Unassigned"),
            days_since_contact = days,
            sla_status         = _sla_status(days, short_tier),
            recommended_action = _outreach_action(p, full_tier),
            notes              = p.notes,
        ))
    return records


# ── Display ───────────────────────────────────────────────────────────────────
SLA_BADGE = {"On Track": "[ OK ]", "At Risk": "[ !! ]", "Overdue": "[LATE]"}

TIER_ORDER = {"Tier 1": 0, "Tier 2": 1, "Tier 3": 2}


def print_crm_table(records: List[SalesforceRecord]) -> None:
    sorted_records = sorted(
        records, key=lambda r: (TIER_ORDER.get(r.tier, 9), -r.score)
    )

    # Column widths
    W_ID     = 18
    W_NAME   = 30
    W_SCORE  =  5
    W_TIER   =  6
    W_OWNER  = 14
    W_DAYS   =  4
    W_SLA    =  8
    W_ACTION = 44

    def row(sf_id, name, score, tier, owner, days, sla, action):
        return (
            f"  {sf_id:<{W_ID}}  "
            f"{name:<{W_NAME}}  "
            f"{score:>{W_SCORE}}  "
            f"{tier:<{W_TIER}}  "
            f"{owner:<{W_OWNER}}  "
            f"{days:>{W_DAYS}}  "
            f"{sla:<{W_SLA}}  "
            f"{action:<{W_ACTION}}"
        )

    header = row(
        "SF Record ID", "Account Name", "Score", "Tier",
        "Owner", "Days", "SLA", "Recommended Action",
    )
    divider = "  " + "-" * (len(header) - 2)
    W = len(header)

    print()
    print("=" * W)
    print("  RULA SALESFORCE CRM  -  PARTNER ACCOUNT RECORDS")
    print("=" * W)
    print(header)

    prev_tier = None
    for r in sorted_records:
        if r.tier != prev_tier:
            print(divider)
            tier_label = {
                "Tier 1": "TIER 1  -  HIGH PRIORITY   (score >= 70)",
                "Tier 2": "TIER 2  -  MEDIUM PRIORITY (score 50-69)",
                "Tier 3": "TIER 3  -  LOWER PRIORITY  (score <  50)",
            }.get(r.tier, r.tier.upper())
            print(f"  {tier_label}")
            print(divider)
            prev_tier = r.tier

        badge = SLA_BADGE.get(r.sla_status, r.sla_status)
        print(row(
            r.sf_id,
            _truncate(r.account_name, W_NAME),
            f"{r.score:.1f}",
            r.tier,
            _truncate(r.owner, W_OWNER),
            str(r.days_since_contact),
            badge,
            _truncate(r.recommended_action, W_ACTION),
        ))

    print("=" * W)

    # ── Footer stats ──────────────────────────────────────────────────────────
    on_track = sum(1 for r in records if r.sla_status == "On Track")
    at_risk  = sum(1 for r in records if r.sla_status == "At Risk")
    overdue  = sum(1 for r in records if r.sla_status == "Overdue")
    t1 = sum(1 for r in records if r.tier == "Tier 1")
    t2 = sum(1 for r in records if r.tier == "Tier 2")
    t3 = sum(1 for r in records if r.tier == "Tier 3")

    print()
    print(f"  Total records : {len(records)}")
    print(f"  By tier       : Tier 1 = {t1}  |  Tier 2 = {t2}  |  Tier 3 = {t3}")
    print(f"  SLA status    : {SLA_BADGE['On Track']} On Track = {on_track}"
          f"  |  {SLA_BADGE['At Risk']} At Risk = {at_risk}"
          f"  |  {SLA_BADGE['Overdue']} Overdue = {overdue}")
    print()


def print_full_records(records: List[SalesforceRecord]) -> None:
    """Print expanded detail card for each record."""
    sorted_records = sorted(
        records, key=lambda r: (TIER_ORDER.get(r.tier, 9), -r.score)
    )
    W = 72
    print()
    print("=" * W)
    print("  FULL RECORD DETAIL")
    print("=" * W)

    for r in sorted_records:
        badge = SLA_BADGE.get(r.sla_status, r.sla_status)
        print(f"\n  {r.sf_id}  |  {r.tier}  |  Score: {r.score:.1f}")
        print(f"  Account Name   : {r.account_name}")
        print(f"  Practice Type  : {r.practice_type}")
        print(f"  Location       : {r.location}")
        print(f"  Owner          : {r.owner}")
        print(f"  Days Since Cntct: {r.days_since_contact}  -  SLA: {badge} {r.sla_status}")
        print(f"  Action         : {r.recommended_action}")
        print(f"  Notes          : {r.notes}")
        print(f"  {'-' * (W - 2)}")

    print("=" * W)


# ── Owner workload summary ────────────────────────────────────────────────────
def print_owner_workload(records: List[SalesforceRecord]) -> None:
    # Collect all unique owners in a stable order (by first appearance)
    owners = list(dict.fromkeys(r.owner for r in sorted(records, key=lambda r: r.owner)))

    W = 72
    print()
    print("=" * W)
    print("  OWNER WORKLOAD SUMMARY")
    print("=" * W)

    # Header
    print(f"\n  {'Owner':<16}  {'Accts':>5}  {'T1':>3}  {'T2':>3}  {'T3':>3}  "
          f"{'Avg Score':>9}  {'OK':>4}  {'Risk':>4}  {'Late':>4}  Accounts")
    print("  " + "-" * (W - 2))

    for owner in sorted(owners):
        owned = [r for r in records if r.owner == owner]
        t1    = sum(1 for r in owned if r.tier == "Tier 1")
        t2    = sum(1 for r in owned if r.tier == "Tier 2")
        t3    = sum(1 for r in owned if r.tier == "Tier 3")
        ok    = sum(1 for r in owned if r.sla_status == "On Track")
        risk  = sum(1 for r in owned if r.sla_status == "At Risk")
        late  = sum(1 for r in owned if r.sla_status == "Overdue")
        avg   = sum(r.score for r in owned) / len(owned)
        names = ", ".join(r.account_name for r in sorted(owned, key=lambda r: -r.score))

        print(f"  {owner:<16}  {len(owned):>5}  {t1:>3}  {t2:>3}  {t3:>3}  "
              f"{avg:>9.1f}  {ok:>4}  {risk:>4}  {late:>4}  {names}")

    # Overdue callouts
    overdue = [r for r in records if r.sla_status == "Overdue"]
    if overdue:
        print()
        print("  OVERDUE FOLLOW-UPS  (action required)")
        print("  " + "-" * (W - 2))
        for r in sorted(overdue, key=lambda r: -r.days_since_contact):
            sla_days = TIER_SLA_DAYS.get(r.tier, 30)
            over_by  = r.days_since_contact - sla_days
            print(f"  {r.owner:<16}  {r.account_name:<30}  {r.tier}  "
                  f"{r.days_since_contact} days since contact  ({over_by}d past SLA)")

    print()
    print("=" * W)


# ── CSV export ────────────────────────────────────────────────────────────────
def export_crm_to_csv(records: List[SalesforceRecord], filepath: str) -> None:
    sorted_records = sorted(
        records, key=lambda r: (TIER_ORDER.get(r.tier, 9), -r.score)
    )

    fieldnames = [
        "SF Record ID", "Account Name", "Practice Type", "Location",
        "Score", "Tier", "Owner", "Days Since Last Contact",
        "SLA Status", "Recommended Action", "Notes",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in sorted_records:
            writer.writerow({
                "SF Record ID":           r.sf_id,
                "Account Name":           r.account_name,
                "Practice Type":          r.practice_type,
                "Location":               r.location,
                "Score":                  r.score,
                "Tier":                   r.tier,
                "Owner":                  r.owner,
                "Days Since Last Contact": r.days_since_contact,
                "SLA Status":             r.sla_status,
                "Recommended Action":     r.recommended_action,
                "Notes":                  r.notes,
            })


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    scored  = [score_practice(p) for p in PRACTICES]
    records = build_records(scored)
    print_crm_table(records)
    print_owner_workload(records)
    print_full_records(records)
    export_crm_to_csv(records, "rula_crm_records.csv")
    print(f"\n  CSV export saved to: rula_crm_records.csv")


if __name__ == "__main__":
    main()
