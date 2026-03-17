"""Report - Generate rich analytics reports for DonorMatch."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from donormatch.models import Campaign, Donation, Donor, DonorSegment, Engagement


class ReportGenerator:
    """Generates rich console reports for donor and campaign analytics."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def donor_summary_report(self, donors: list[Donor]) -> None:
        """Print a summary report of all donors."""
        self.console.print(
            Panel("[bold]Donor Summary Report[/bold]", style="blue")
        )

        table = Table(title="Donor Overview")
        table.add_column("Name", style="cyan")
        table.add_column("Email", style="dim")
        table.add_column("Segment", style="magenta")
        table.add_column("Total Donated", justify="right", style="green")
        table.add_column("Donations", justify="right")
        table.add_column("Avg Donation", justify="right", style="green")
        table.add_column("Engagement", justify="right", style="yellow")

        for donor in sorted(donors, key=lambda d: d.total_donated, reverse=True)[:20]:
            table.add_row(
                donor.full_name,
                donor.email,
                donor.segment.value,
                f"${donor.total_donated:,.2f}",
                str(donor.donation_count),
                f"${donor.average_donation:,.2f}",
                f"{donor.engagement_score:.1f}",
            )

        self.console.print(table)
        self.console.print()

        # Segment breakdown
        segments: dict[DonorSegment, list[Donor]] = {s: [] for s in DonorSegment}
        for d in donors:
            segments[d.segment].append(d)

        seg_table = Table(title="Segment Breakdown")
        seg_table.add_column("Segment", style="magenta")
        seg_table.add_column("Count", justify="right")
        seg_table.add_column("Total Donated", justify="right", style="green")
        seg_table.add_column("Avg Donated", justify="right", style="green")

        for seg, seg_donors in segments.items():
            total = sum(d.total_donated for d in seg_donors)
            avg = total / len(seg_donors) if seg_donors else 0
            seg_table.add_row(
                seg.value,
                str(len(seg_donors)),
                f"${total:,.2f}",
                f"${avg:,.2f}",
            )

        self.console.print(seg_table)

    def campaign_report(self, campaigns: list[Campaign]) -> None:
        """Print a campaign progress report."""
        self.console.print(
            Panel("[bold]Campaign Progress Report[/bold]", style="blue")
        )

        table = Table(title="Campaign Overview")
        table.add_column("Campaign", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Goal", justify="right", style="green")
        table.add_column("Raised", justify="right", style="green")
        table.add_column("Progress", justify="right")
        table.add_column("Remaining", justify="right", style="red")
        table.add_column("Donors", justify="right")

        for campaign in campaigns:
            progress_pct = campaign.progress
            if progress_pct >= 100:
                progress_style = "bold green"
            elif progress_pct >= 50:
                progress_style = "yellow"
            else:
                progress_style = "red"

            table.add_row(
                campaign.name,
                campaign.status.value,
                f"${campaign.goal:,.2f}",
                f"${campaign.raised:,.2f}",
                Text(f"{progress_pct:.1f}%", style=progress_style),
                f"${campaign.remaining:,.2f}",
                str(campaign.donor_count),
            )

        self.console.print(table)

    def engagement_report(self, engagements: list[Engagement], donors: list[Donor]) -> None:
        """Print an engagement analytics report."""
        self.console.print(
            Panel("[bold]Engagement Analytics Report[/bold]", style="blue")
        )

        # Build donor lookup
        donor_map = {d.id: d for d in donors}

        table = Table(title="Top Engaged Donors")
        table.add_column("Name", style="cyan")
        table.add_column("Recency", justify="right", style="yellow")
        table.add_column("Frequency", justify="right", style="yellow")
        table.add_column("Monetary", justify="right", style="yellow")
        table.add_column("Overall", justify="right", style="bold green")
        table.add_column("Tier", style="magenta")

        sorted_eng = sorted(engagements, key=lambda e: e.overall_score, reverse=True)
        for eng in sorted_eng[:15]:
            donor = donor_map.get(eng.donor_id)
            name = donor.full_name if donor else "Unknown"
            table.add_row(
                name,
                f"{eng.recency_score:.1f}",
                f"{eng.frequency_score:.1f}",
                f"{eng.monetary_score:.1f}",
                f"{eng.overall_score:.1f}",
                eng.rfm_tier,
            )

        self.console.print(table)

        # Tier distribution
        tiers: dict[str, int] = {}
        for eng in engagements:
            tier = eng.rfm_tier
            tiers[tier] = tiers.get(tier, 0) + 1

        tier_table = Table(title="Engagement Tier Distribution")
        tier_table.add_column("Tier", style="magenta")
        tier_table.add_column("Count", justify="right")
        tier_table.add_column("Percentage", justify="right", style="yellow")

        total = len(engagements) or 1
        for tier_name in ["champion", "loyal", "potential", "at_risk", "dormant"]:
            count = tiers.get(tier_name, 0)
            pct = count / total * 100
            tier_table.add_row(tier_name, str(count), f"{pct:.1f}%")

        self.console.print(tier_table)

    def match_report(
        self,
        campaign: Campaign,
        matches: list[tuple[Donor, float]],
    ) -> None:
        """Print a donor-campaign match report."""
        self.console.print(
            Panel(
                f"[bold]Match Report: {campaign.name}[/bold]",
                style="blue",
            )
        )

        table = Table(title=f"Top Donor Matches for '{campaign.name}'")
        table.add_column("Rank", justify="right", style="dim")
        table.add_column("Donor", style="cyan")
        table.add_column("Segment", style="magenta")
        table.add_column("Match Score", justify="right", style="bold green")
        table.add_column("Total Donated", justify="right", style="green")
        table.add_column("Interests", style="yellow")

        for rank, (donor, score) in enumerate(matches, 1):
            interests_str = ", ".join(i.value for i in donor.interests[:3])
            table.add_row(
                str(rank),
                donor.full_name,
                donor.segment.value,
                f"{score:.1f}",
                f"${donor.total_donated:,.2f}",
                interests_str,
            )

        self.console.print(table)

    def full_report(
        self,
        donors: list[Donor],
        campaigns: list[Campaign],
        engagements: list[Engagement],
        matches: dict | None = None,
    ) -> None:
        """Generate a comprehensive report with all analytics."""
        self.console.print()
        self.console.rule("[bold blue]DonorMatch Analytics Dashboard[/bold blue]")
        self.console.print()

        # Summary stats
        total_donated = sum(d.total_donated for d in donors)
        total_raised = sum(c.raised for c in campaigns)
        active_donors = sum(1 for d in donors if d.is_active)

        stats_table = Table(title="Key Metrics", show_header=False)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", justify="right", style="bold green")

        stats_table.add_row("Total Donors", str(len(donors)))
        stats_table.add_row("Active Donors", str(active_donors))
        stats_table.add_row("Total Campaigns", str(len(campaigns)))
        stats_table.add_row("Total Donated", f"${total_donated:,.2f}")
        stats_table.add_row("Total Raised", f"${total_raised:,.2f}")
        stats_table.add_row(
            "Avg Donation",
            f"${total_donated / max(sum(d.donation_count for d in donors), 1):,.2f}",
        )

        self.console.print(stats_table)
        self.console.print()

        self.donor_summary_report(donors)
        self.console.print()

        self.campaign_report(campaigns)
        self.console.print()

        if engagements:
            self.engagement_report(engagements, donors)
