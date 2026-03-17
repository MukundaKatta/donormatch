"""CLI interface for DonorMatch using Click."""

from __future__ import annotations

import click
from rich.console import Console

from donormatch.crm.campaign import CampaignManager
from donormatch.crm.donor import DonorManager
from donormatch.crm.engagement import EngagementTracker
from donormatch.matching.matcher import DonorMatcher
from donormatch.matching.scorer import DonorScorer
from donormatch.matching.segmenter import DonorSegmenter
from donormatch.report import ReportGenerator
from donormatch.simulator import Simulator

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """DonorMatch - Nonprofit Donor CRM with intelligent matching."""
    pass


@cli.command()
@click.option("--donors", "-d", default=100, help="Number of donors to simulate")
@click.option("--campaigns", "-c", default=5, help="Number of campaigns to simulate")
@click.option("--seed", "-s", default=42, help="Random seed for reproducibility")
def simulate(donors: int, campaigns: int, seed: int) -> None:
    """Run a simulation with synthetic data."""
    console.print(f"[bold blue]Generating synthetic data...[/bold blue]")
    console.print(f"  Donors: {donors}, Campaigns: {campaigns}, Seed: {seed}")
    console.print()

    sim = Simulator(seed=seed)
    donor_list, campaign_list, donation_list = sim.generate_full_dataset(
        n_donors=donors, n_campaigns=campaigns
    )

    # Score engagement
    tracker = EngagementTracker()
    engagements = tracker.batch_calculate(donor_list, donation_list)

    for donor in donor_list:
        eng = tracker.get_engagement(donor.id)
        if eng:
            donor.engagement_score = eng.overall_score

    # Score donors
    scorer = DonorScorer()
    scorer.batch_score(donor_list, donation_list)

    # Segment donors
    segmenter = DonorSegmenter()
    segmenter.segment_all(donor_list, donation_list)

    # Match donors to campaigns
    matcher = DonorMatcher()
    matcher.fit(donor_list, donation_list)

    # Generate report
    report = ReportGenerator(console=console)
    report.full_report(donor_list, campaign_list, engagements)

    # Show top matches for first active campaign
    active = [c for c in campaign_list if c.status.value == "active"]
    if active:
        top_campaign = active[0]
        matches = matcher.match_donors_to_campaign(
            top_campaign, donor_list, donation_list, top_n=10
        )
        console.print()
        report.match_report(top_campaign, matches)

    console.print()
    console.print("[bold green]Simulation complete![/bold green]")


@cli.command()
@click.option("--donors", "-d", default=50, help="Number of donors")
@click.option("--campaigns", "-c", default=5, help="Number of campaigns")
def report(donors: int, campaigns: int) -> None:
    """Generate an analytics report."""
    sim = Simulator(seed=42)
    donor_list, campaign_list, donation_list = sim.generate_full_dataset(
        n_donors=donors, n_campaigns=campaigns
    )

    tracker = EngagementTracker()
    engagements = tracker.batch_calculate(donor_list, donation_list)

    for donor in donor_list:
        eng = tracker.get_engagement(donor.id)
        if eng:
            donor.engagement_score = eng.overall_score

    scorer = DonorScorer()
    scorer.batch_score(donor_list, donation_list)

    segmenter = DonorSegmenter()
    segmenter.segment_all(donor_list, donation_list)

    rpt = ReportGenerator(console=console)
    rpt.full_report(donor_list, campaign_list, engagements)


@cli.command()
@click.option("--donors", "-d", default=50, help="Number of donors")
@click.option("--top", "-n", default=10, help="Number of matches to show")
def match(donors: int, top: int) -> None:
    """Match donors to campaigns."""
    sim = Simulator(seed=42)
    donor_list, campaign_list, donation_list = sim.generate_full_dataset(
        n_donors=donors, n_campaigns=5
    )

    tracker = EngagementTracker()
    tracker.batch_calculate(donor_list, donation_list)

    for donor in donor_list:
        eng = tracker.get_engagement(donor.id)
        if eng:
            donor.engagement_score = eng.overall_score

    scorer = DonorScorer()
    scorer.batch_score(donor_list, donation_list)

    matcher = DonorMatcher()
    matcher.fit(donor_list, donation_list)

    rpt = ReportGenerator(console=console)

    for campaign in campaign_list:
        matches = matcher.match_donors_to_campaign(
            campaign, donor_list, donation_list, top_n=top
        )
        rpt.match_report(campaign, matches)
        console.print()


if __name__ == "__main__":
    cli()
