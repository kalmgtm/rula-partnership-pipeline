#!/usr/bin/env python3
"""
outreach_generator.py

Generates a personalized one-line outreach hook for each Tier 1 Rula referral
partner practice, based on practice name, BH gap, provider count, and notes.

Hook selection logic (in priority order):
  1. Waitlist signal     - notes mention a specific-week waitlist
  2. Screening signal    - notes mention PHQ or active screening
  3. Provider voice      - notes say providers named BH as top unmet need
  4. No BH pathway       - notes say no current referral pathway / no on-site BH
  5. Overload signal     - notes mention ratio strain (e.g. 1 counselor for N providers)
  6. Full gap fallback   - bh_referral_gap == "full", no specific signal
  7. Generic fallback    - partial gap with high provider count
"""

import re
from typing import Optional

from rula_partnership_scorer import (
    PRACTICES,
    Practice,
    score_practice,
    _get_tier,
)

# ── Tier filter ───────────────────────────────────────────────────────────────
def _is_tier1(p: Practice) -> bool:
    return "Tier 1" in _get_tier(p)


# ── Note parsing helpers ──────────────────────────────────────────────────────
def _first_clause(notes: str) -> str:
    """Return the first semicolon-delimited clause, stripped."""
    return notes.split(";")[0].strip().rstrip(".")


def _mentions(notes: str, *keywords) -> bool:
    lower = notes.lower()
    return any(k in lower for k in keywords)


def _waitlist_weeks(notes: str) -> Optional[str]:
    m = re.search(r"(\d+)-week waitlist", notes, re.IGNORECASE)
    return m.group(1) if m else None


def _ratio_detail(notes: str) -> Optional[tuple]:
    """Return (staff_count, provider_count) if a ratio like '1 social worker for 22 providers' is found."""
    m = re.search(r"(\d+) \w+ for (\d+) providers", notes, re.IGNORECASE)
    return (m.group(1), m.group(2)) if m else None


# ── Hook generator ────────────────────────────────────────────────────────────
def generate_hook(p: Practice) -> str:
    notes    = p.notes
    name     = p.name
    ptype    = p.practice_type.lower()
    count    = p.provider_count

    # 1. Specific waitlist callout
    weeks = _waitlist_weeks(notes)
    if weeks:
        return (
            f"A {weeks}-week wait is a long time for a patient in crisis - "
            f"wanted to reach out because Rula has helped similar practices get people into care within the same week."
        )

    # 2. Active BH screening (PHQ-9, etc.)
    if _mentions(notes, "phq", "screening", "phq-9"):
        return (
            f"If you're already screening for behavioral health needs, the hardest part is done - "
            f"Rula can help make sure those patients actually land somewhere before they leave the building."
        )

    # 3. Providers themselves named BH as the gap
    if _mentions(notes, "top unmet need", "biggest unmet", "rank mental health"):
        return (
            f"Heard that your providers are naming mental health as their biggest unmet need - "
            f"that resonated with me, and I think Rula could be a low-lift way to start closing that gap."
        )

    # 4. No in-house BH pathway
    if _mentions(notes, "no on-site", "no current bh", "no current referral", "no in-house"):
        return (
            f"With {count} providers and no in-house BH pathway, "
            f"Rula could give your patients a same-week mental health option without adding any overhead to your team."
        )

    # 5. Staff-to-provider ratio strain
    ratio = _ratio_detail(notes)
    if ratio:
        staff, providers = ratio
        return (
            f"Supporting {providers} providers with {staff} BH staff is a tough spot - "
            f"Rula works alongside practices like {name} to take on overflow so your existing team isn't stretched so thin."
        )

    # 6. Full gap, no specific signal - lead with patient impact
    if p.bh_referral_gap == "full":
        return (
            f"With a full behavioral health gap across {count} providers, "
            f"a lot of your patients are probably leaving without a clear next step - "
            f"happy to share how Rula has helped {ptype} groups handle that."
        )

    # 7. Generic warm fallback
    return (
        f"Given the scale of what you're doing across {count} providers, "
        f"I thought it was worth a note - Rula's worked with a number of similar {ptype} groups "
        f"and I think there could be a real fit here."
    )


# ── Report ────────────────────────────────────────────────────────────────────
def print_hooks(practices) -> None:
    tier1 = [p for p in practices if _is_tier1(p)]
    tier1_sorted = sorted(tier1, key=lambda p: p.score, reverse=True)

    W = 80
    print()
    print("=" * W)
    print("  RULA TIER 1  -  PERSONALIZED OUTREACH HOOKS")
    print("=" * W)
    print("  Hooks are tailored to each practice's BH gap, notes, and provider profile.")
    print("  Signal used for each hook is noted in brackets.")
    print("=" * W)

    for i, p in enumerate(tier1_sorted, start=1):
        hook = generate_hook(p)
        gap_label = {"full": "Full BH Gap", "partial": "Partial BH Gap", "none": "No BH Gap"}.get(
            p.bh_referral_gap.lower(), p.bh_referral_gap
        )

        # Detect which signal fired for transparency
        signal = _detect_signal(p)

        print(f"\n  #{i}  {p.name}")
        print(f"       {p.practice_type}  |  {p.location}"
              f"  |  {p.provider_count} providers  |  {gap_label}  |  Score: {p.score}")
        print(f"       Signal: {signal}")
        print(f"       Notes:  {p.notes}")
        print(f"\n       Hook:")

        # Wrap the hook at ~72 chars for readability
        words = hook.split()
        line, lines = [], []
        for word in words:
            if sum(len(w) + 1 for w in line) + len(word) > 70:
                lines.append(" ".join(line))
                line = [word]
            else:
                line.append(word)
        if line:
            lines.append(" ".join(line))

        print(f'       "{lines[0]}')
        for l in lines[1:]:
            print(f"        {l}")
        if len(lines) > 1:
            print('       "', end="")
            print()

        if i < len(tier1_sorted):
            print(f"\n  {'- ' * 38}-")

    print()
    print("=" * W)
    print(f"  {len(tier1_sorted)} Tier 1 hook{'s' if len(tier1_sorted) != 1 else ''} generated.")
    print("=" * W)


def _detect_signal(p: Practice) -> str:
    """Return a short label for which hook trigger fired."""
    notes = p.notes
    if _waitlist_weeks(notes):
        return "Waitlist length mentioned in notes"
    if _mentions(notes, "phq", "screening", "phq-9"):
        return "Active BH screening detected"
    if _mentions(notes, "top unmet need", "biggest unmet", "rank mental health"):
        return "Providers named BH as top unmet need"
    if _mentions(notes, "no on-site", "no current bh", "no current referral", "no in-house"):
        return "No in-house BH pathway"
    if _ratio_detail(notes):
        return "Staff-to-provider ratio strain"
    if p.bh_referral_gap == "full":
        return "Full BH gap (no specific signal in notes)"
    return "Generic (partial gap, high provider count)"


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    scored = [score_practice(p) for p in PRACTICES]
    print_hooks(scored)


if __name__ == "__main__":
    main()
