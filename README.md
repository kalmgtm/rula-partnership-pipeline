# Rula Partnership Pipeline

A Python toolkit for scoring, prioritizing, and managing outreach to healthcare practices as potential Rula mental health referral partners.

## Overview

This pipeline takes a set of healthcare practices, scores them across four dimensions, tiers them by partnership potential, simulates CRM records, tracks SLA compliance, and generates personalized outreach hooks for top-priority accounts.

## Files

| File | Description |
|------|-------------|
| `rula_partnership_scorer.py` | Core scoring engine. Scores each practice out of 100 across four dimensions and produces a ranked report, tier summary, bar chart, and CSV export. |
| `crm_output.py` | Generates simulated Salesforce CRM records for each practice. Includes tier, owner assignment, SLA status, and recommended action. Prints a formatted table and exports to CSV. |
| `sla_tracker.py` | Tracks days since last outreach per practice and flags SLA breaches by tier. Prints a urgency-sorted report with an owner action callout. Exports to CSV. |
| `outreach_generator.py` | Generates a personalized one-line outreach hook for each Tier 1 practice based on BH gap, provider count, and notes. Uses signal detection to tailor each hook. |

## Scoring Model

Practices are scored out of **100 points** across four dimensions:

| Dimension | Weight | Logic |
|-----------|--------|-------|
| Provider Count | 25 pts | Tiered: 1-2 = 5, 3-5 = 10, 6-10 = 15, 11-20 = 20, 21+ = 25 |
| BH Referral Gap | 35 pts | Full gap = 35, Partial = 20, No gap = 5 |
| Insurance Networks | 25 pts | Proportional overlap with Rula's 12 accepted plans |
| Monthly Volume | 15 pts | Tiered: <500 = 3, 500-1000 = 7, 1001-2000 = 11, 2001+ = 15 |

## Tiers

| Tier | Score Range | Outreach Action |
|------|-------------|-----------------|
| Tier 1 - High Priority | >= 70 | Personalized email with practice-specific hook |
| Tier 2 - Medium Priority | 50-69 | Templated intro email |
| Tier 3 - Lower Priority | < 50 | Drip nurture sequence, revisit in 90 days |

## SLA Rules

| Tier | SLA Threshold | Status Labels |
|------|---------------|---------------|
| Tier 1 | 48 hours (2 days) | URGENT - SLA BREACH / AT RISK / ON TRACK |
| Tier 2 | 7 days | OVERDUE / AT RISK / ON TRACK |
| Tier 3 | No hard SLA | MONITOR |

## Outputs

Running each script produces:

- **`rula_partner_scores.png`** - Horizontal bar chart of all practice scores, colored by tier
- **`rula_partner_scores.csv`** - Full scored and ranked practice list
- **`rula_crm_records.csv`** - Simulated Salesforce records with owner and SLA fields
- **`rula_sla_tracker.csv`** - SLA status report sorted by urgency

## Usage

```bash
# Score and rank all practices
python rula_partnership_scorer.py

# Generate CRM records and owner workload summary
python crm_output.py

# Run SLA tracker and flag overdue accounts
python sla_tracker.py

# Generate Tier 1 outreach hooks
python outreach_generator.py
```

## Requirements

```bash
pip install matplotlib
```

All other dependencies are from the Python standard library (`csv`, `dataclasses`, `re`).

## Sample Practices

The pipeline ships with 10 sample practices across primary care, internal medicine, pediatrics, OB/GYN, and FQHCs in markets including Phoenix, Chicago, Los Angeles, Tampa, Atlanta, Houston, and others. All data is simulated.
