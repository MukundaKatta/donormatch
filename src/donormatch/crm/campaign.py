"""CampaignManager - Track fundraising campaigns with goals and progress."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from donormatch.models import (
    Campaign,
    CampaignStatus,
    Donation,
    DonorSegment,
    InterestArea,
)


class CampaignManager:
    """Manages fundraising campaigns with goal tracking and analytics."""

    def __init__(self) -> None:
        self._campaigns: dict[UUID, Campaign] = {}
        self._donations: dict[UUID, list[Donation]] = {}  # campaign_id -> donations

    @property
    def count(self) -> int:
        return len(self._campaigns)

    # ---- CRUD ----

    def create(
        self,
        name: str,
        description: str,
        goal: float,
        interest_area: InterestArea,
        start_date: date,
        end_date: date,
        min_donation: float = 0.0,
        target_segments: Optional[list[DonorSegment]] = None,
    ) -> Campaign:
        """Create a new campaign."""
        campaign = Campaign(
            name=name,
            description=description,
            goal=goal,
            interest_area=interest_area,
            start_date=start_date,
            end_date=end_date,
            min_donation=min_donation,
            target_segments=target_segments or [],
        )
        self._campaigns[campaign.id] = campaign
        self._donations[campaign.id] = []
        return campaign

    def get(self, campaign_id: UUID) -> Optional[Campaign]:
        """Retrieve a campaign by ID."""
        return self._campaigns.get(campaign_id)

    def update(self, campaign_id: UUID, **kwargs) -> Optional[Campaign]:
        """Update a campaign's fields."""
        campaign = self._campaigns.get(campaign_id)
        if campaign is None:
            return None
        for key, value in kwargs.items():
            if hasattr(campaign, key):
                setattr(campaign, key, value)
        campaign.updated_at = datetime.now()
        self._campaigns[campaign_id] = campaign
        return campaign

    def delete(self, campaign_id: UUID) -> bool:
        """Delete a campaign."""
        if campaign_id in self._campaigns:
            del self._campaigns[campaign_id]
            self._donations.pop(campaign_id, None)
            return True
        return False

    def list_all(self) -> list[Campaign]:
        """List all campaigns."""
        return list(self._campaigns.values())

    def add(self, campaign: Campaign) -> Campaign:
        """Add an existing Campaign object."""
        self._campaigns[campaign.id] = campaign
        if campaign.id not in self._donations:
            self._donations[campaign.id] = []
        return campaign

    # ---- Status Management ----

    def activate(self, campaign_id: UUID) -> Optional[Campaign]:
        """Activate a campaign."""
        return self.update(campaign_id, status=CampaignStatus.ACTIVE)

    def pause(self, campaign_id: UUID) -> Optional[Campaign]:
        """Pause a campaign."""
        return self.update(campaign_id, status=CampaignStatus.PAUSED)

    def complete(self, campaign_id: UUID) -> Optional[Campaign]:
        """Mark a campaign as completed."""
        return self.update(campaign_id, status=CampaignStatus.COMPLETED)

    def cancel(self, campaign_id: UUID) -> Optional[Campaign]:
        """Cancel a campaign."""
        return self.update(campaign_id, status=CampaignStatus.CANCELLED)

    # ---- Donations ----

    def record_donation(self, donation: Donation) -> bool:
        """Record a donation to a campaign and update totals."""
        campaign = self._campaigns.get(donation.campaign_id)
        if campaign is None:
            return False

        if donation.campaign_id not in self._donations:
            self._donations[donation.campaign_id] = []

        self._donations[donation.campaign_id].append(donation)
        campaign.raised += donation.amount
        campaign.donation_count += 1

        # Track unique donors
        unique_donors = {d.donor_id for d in self._donations[donation.campaign_id]}
        campaign.donor_count = len(unique_donors)
        campaign.updated_at = datetime.now()
        return True

    def get_campaign_donations(self, campaign_id: UUID) -> list[Donation]:
        """Get all donations for a campaign."""
        return self._donations.get(campaign_id, [])

    # ---- Analytics ----

    def get_active_campaigns(self) -> list[Campaign]:
        """Get all active campaigns."""
        return [c for c in self._campaigns.values() if c.status == CampaignStatus.ACTIVE]

    def get_by_interest(self, interest: InterestArea) -> list[Campaign]:
        """Get campaigns by interest area."""
        return [c for c in self._campaigns.values() if c.interest_area == interest]

    def get_progress_summary(self) -> list[dict]:
        """Get progress summary for all campaigns."""
        summaries = []
        for campaign in self._campaigns.values():
            summaries.append({
                "id": str(campaign.id),
                "name": campaign.name,
                "goal": campaign.goal,
                "raised": campaign.raised,
                "progress": campaign.progress,
                "remaining": campaign.remaining,
                "status": campaign.status.value,
                "donor_count": campaign.donor_count,
                "donation_count": campaign.donation_count,
            })
        return summaries

    def get_top_campaigns(self, n: int = 5) -> list[Campaign]:
        """Get top N campaigns by amount raised."""
        campaigns = list(self._campaigns.values())
        campaigns.sort(key=lambda c: c.raised, reverse=True)
        return campaigns[:n]
