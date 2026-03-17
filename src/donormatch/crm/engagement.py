"""EngagementTracker - Score donor engagement using recency, frequency, and monetary analysis."""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

import numpy as np

from donormatch.models import Donation, Donor, Engagement


class EngagementTracker:
    """Tracks and scores donor engagement using RFM (Recency, Frequency, Monetary) analysis."""

    def __init__(
        self,
        recency_weight: float = 0.35,
        frequency_weight: float = 0.30,
        monetary_weight: float = 0.35,
    ) -> None:
        self.recency_weight = recency_weight
        self.frequency_weight = frequency_weight
        self.monetary_weight = monetary_weight
        self._engagements: dict[UUID, Engagement] = {}

    def calculate_engagement(
        self,
        donor: Donor,
        donations: list[Donation],
        reference_date: Optional[date] = None,
    ) -> Engagement:
        """Calculate engagement score for a donor based on their donation history."""
        ref_date = reference_date or date.today()

        recency = self._score_recency(donor, ref_date)
        frequency = self._score_frequency(donor, donations)
        monetary = self._score_monetary(donor, donations)

        overall = (
            recency * self.recency_weight
            + frequency * self.frequency_weight
            + monetary * self.monetary_weight
        )

        engagement = Engagement(
            donor_id=donor.id,
            recency_score=round(recency, 2),
            frequency_score=round(frequency, 2),
            monetary_score=round(monetary, 2),
            overall_score=round(overall, 2),
        )

        self._engagements[donor.id] = engagement
        return engagement

    def _score_recency(self, donor: Donor, reference_date: date) -> float:
        """Score recency: how recently the donor last gave (0-100)."""
        if donor.last_donation_date is None:
            return 0.0

        days_since = (reference_date - donor.last_donation_date).days
        if days_since <= 0:
            return 100.0

        # Exponential decay: score drops off over time
        # Half-life of ~90 days
        score = 100.0 * np.exp(-0.0077 * days_since)
        return max(float(score), 0.0)

    def _score_frequency(self, donor: Donor, donations: list[Donation]) -> float:
        """Score frequency: how often the donor gives (0-100)."""
        if not donations:
            return 0.0

        donor_donations = [d for d in donations if d.donor_id == donor.id]
        count = len(donor_donations)

        if count == 0:
            return 0.0

        # Logarithmic scaling: diminishing returns for very frequent donors
        score = min(100.0, 20.0 * np.log1p(count))
        return float(score)

    def _score_monetary(self, donor: Donor, donations: list[Donation]) -> float:
        """Score monetary value: how much the donor gives (0-100)."""
        if not donations:
            return 0.0

        donor_donations = [d for d in donations if d.donor_id == donor.id]
        if not donor_donations:
            return 0.0

        total = sum(d.amount for d in donor_donations)

        # Logarithmic scaling with reasonable thresholds
        # $100 -> ~33, $1000 -> ~53, $10000 -> ~73, $100000 -> ~93
        if total <= 0:
            return 0.0
        score = min(100.0, 14.5 * np.log1p(total / 10))
        return float(score)

    def batch_calculate(
        self,
        donors: list[Donor],
        donations: list[Donation],
        reference_date: Optional[date] = None,
    ) -> list[Engagement]:
        """Calculate engagement scores for all donors."""
        results = []
        for donor in donors:
            engagement = self.calculate_engagement(donor, donations, reference_date)
            results.append(engagement)
        return results

    def get_engagement(self, donor_id: UUID) -> Optional[Engagement]:
        """Retrieve cached engagement for a donor."""
        return self._engagements.get(donor_id)

    def get_top_engaged(self, n: int = 10) -> list[Engagement]:
        """Get top N most engaged donors."""
        engagements = list(self._engagements.values())
        engagements.sort(key=lambda e: e.overall_score, reverse=True)
        return engagements[:n]

    def get_tier_distribution(self) -> dict[str, int]:
        """Get count of donors in each engagement tier."""
        tiers: dict[str, int] = {
            "champion": 0,
            "loyal": 0,
            "potential": 0,
            "at_risk": 0,
            "dormant": 0,
        }
        for engagement in self._engagements.values():
            tier = engagement.rfm_tier
            tiers[tier] = tiers.get(tier, 0) + 1
        return tiers
