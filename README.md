# DonorMatch

Nonprofit Donor CRM with intelligent donor-campaign matching powered by machine learning.

## Features

- **Donor Management**: Full CRUD operations, search, and segmentation for donor records
- **Campaign Tracking**: Manage fundraising campaigns with goals, progress tracking, and analytics
- **Engagement Scoring**: Score donor engagement using recency, frequency, and monetary (RFM) analysis
- **ML-Powered Matching**: Match donors to campaigns based on interest, capacity, and giving history
- **Donor Scoring**: Compute donor lifetime value and propensity to give
- **Donor Segmentation**: Cluster donors into segments (major, mid-level, small, lapsed, new)
- **Simulation & Reporting**: Generate synthetic data and produce rich analytics reports

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Run the CLI
donormatch --help

# Run a simulation with synthetic data
donormatch simulate --donors 100 --campaigns 5

# Generate a report
donormatch report

# Match donors to campaigns
donormatch match --campaign-id <id>
```

## Project Structure

```
src/donormatch/
  cli.py              - Click-based CLI interface
  models.py           - Pydantic data models (Donor, Campaign, Donation, Engagement)
  simulator.py        - Synthetic data generation
  report.py           - Rich analytics reports
  crm/
    donor.py           - DonorManager with CRUD, search, segmentation
    campaign.py        - CampaignManager for fundraising campaigns
    engagement.py      - EngagementTracker with RFM scoring
  matching/
    matcher.py         - DonorMatcher using ML for donor-campaign matching
    scorer.py          - DonorScorer for lifetime value and propensity scoring
    segmenter.py       - DonorSegmenter for clustering donors
```

## Dependencies

- numpy
- scikit-learn
- pydantic
- click
- rich

## Author

Mukunda Katta
