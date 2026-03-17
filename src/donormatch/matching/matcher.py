"""DonorMatcher - ML-powered matching of donors to campaigns."""

from __future__ import annotations

from uuid import UUID

import numpy as np
from sklearn.preprocessing import StandardScaler

from donormatch.models import Campaign, Donation, Donor, InterestArea


class DonorMatcher:
    """Matches donors to campaigns using ML based on interest, capacity, and history."""

    # Map interest areas to numeric indices for feature vectors
    INTEREST_INDEX: dict[InterestArea, int] = {
        area: idx for idx, area in enumerate(InterestArea)
    }
    NUM_INTERESTS = len(InterestArea)

    def __init__(self) -> None:
        self._scaler = StandardScaler()
        self._fitted = False

    def _donor_feature_vector(self, donor: Donor, donations: list[Donation]) -> np.ndarray:
        """Build a feature vector for a donor."""
        # Interest one-hot encoding
        interest_vec = np.zeros(self.NUM_INTERESTS)
        for interest in donor.interests:
            interest_vec[self.INTEREST_INDEX[interest]] = 1.0

        # Capacity features
        donor_donations = [d for d in donations if d.donor_id == donor.id]
        avg_donation = donor.average_donation
        max_donation = max((d.amount for d in donor_donations), default=0.0)
        total = donor.total_donated
        count = donor.donation_count

        # Engagement
        engagement = donor.engagement_score
        propensity = donor.propensity_score

        capacity_features = np.array([
            avg_donation,
            max_donation,
            total,
            float(count),
            engagement,
            propensity,
        ])

        return np.concatenate([interest_vec, capacity_features])

    def _campaign_feature_vector(self, campaign: Campaign) -> np.ndarray:
        """Build a feature vector for a campaign."""
        interest_vec = np.zeros(self.NUM_INTERESTS)
        interest_vec[self.INTEREST_INDEX[campaign.interest_area]] = 1.0

        campaign_features = np.array([
            campaign.goal,
            campaign.min_donation,
            campaign.remaining,
            float(campaign.donor_count),
            campaign.progress,
            1.0 if campaign.is_complete else 0.0,
        ])

        return np.concatenate([interest_vec, campaign_features])

    def fit(self, donors: list[Donor], donations: list[Donation]) -> None:
        """Fit the scaler on donor features for normalization."""
        if not donors:
            return
        features = np.array([self._donor_feature_vector(d, donations) for d in donors])
        self._scaler.fit(features)
        self._fitted = True

    def match_donors_to_campaign(
        self,
        campaign: Campaign,
        donors: list[Donor],
        donations: list[Donation],
        top_n: int = 10,
    ) -> list[tuple[Donor, float]]:
        """Match and rank donors for a specific campaign.

        Returns list of (donor, match_score) tuples sorted by score descending.
        """
        if not donors:
            return []

        campaign_vec = self._campaign_feature_vector(campaign)

        scored: list[tuple[Donor, float]] = []
        for donor in donors:
            score = self._compute_match_score(donor, campaign, campaign_vec, donations)
            scored.append((donor, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]

    def match_campaigns_to_donor(
        self,
        donor: Donor,
        campaigns: list[Campaign],
        donations: list[Donation],
        top_n: int = 5,
    ) -> list[tuple[Campaign, float]]:
        """Find best campaign matches for a specific donor."""
        if not campaigns:
            return []

        scored: list[tuple[Campaign, float]] = []
        for campaign in campaigns:
            campaign_vec = self._campaign_feature_vector(campaign)
            score = self._compute_match_score(donor, campaign, campaign_vec, donations)
            scored.append((campaign, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]

    def _compute_match_score(
        self,
        donor: Donor,
        campaign: Campaign,
        campaign_vec: np.ndarray,
        donations: list[Donation],
    ) -> float:
        """Compute a match score between a donor and campaign.

        Combines:
        - Interest alignment (cosine similarity on interest vectors)
        - Capacity match (donor's giving capacity vs campaign needs)
        - Historical affinity (past donations to similar campaigns)
        """
        donor_vec = self._donor_feature_vector(donor, donations)

        # Interest similarity (first NUM_INTERESTS elements)
        d_int = donor_vec[: self.NUM_INTERESTS]
        c_int = campaign_vec[: self.NUM_INTERESTS]
        interest_sim = self._cosine_similarity(d_int, c_int)

        # Capacity score: does donor's giving level match campaign needs?
        avg_donation = donor.average_donation
        min_donation = campaign.min_donation
        if min_donation > 0 and avg_donation > 0:
            capacity_score = min(avg_donation / min_donation, 2.0) / 2.0
        elif avg_donation > 0:
            capacity_score = min(avg_donation / (campaign.goal * 0.01 + 1), 1.0)
        else:
            capacity_score = 0.1  # New donor gets a small base score

        # Engagement bonus
        engagement_bonus = donor.engagement_score / 100.0

        # Propensity bonus
        propensity_bonus = donor.propensity_score / 100.0

        # Weighted combination
        score = (
            0.35 * interest_sim
            + 0.25 * capacity_score
            + 0.20 * engagement_bonus
            + 0.20 * propensity_bonus
        )

        return round(float(score) * 100, 2)

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def bulk_match(
        self,
        donors: list[Donor],
        campaigns: list[Campaign],
        donations: list[Donation],
    ) -> dict[UUID, list[tuple[UUID, float]]]:
        """Generate match scores for all donor-campaign pairs.

        Returns dict mapping campaign_id to list of (donor_id, score) tuples.
        """
        results: dict[UUID, list[tuple[UUID, float]]] = {}
        for campaign in campaigns:
            matches = self.match_donors_to_campaign(
                campaign, donors, donations, top_n=len(donors)
            )
            results[campaign.id] = [(d.id, s) for d, s in matches]
        return results
