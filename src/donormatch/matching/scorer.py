"""DonorScorer - Compute donor lifetime value and propensity to give."""

from __future__ import annotations

from datetime import date
from typing import Optional

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from donormatch.models import Donation, Donor


class DonorScorer:
    """Computes donor lifetime value (LTV) and propensity to give scores."""

    def __init__(self) -> None:
        self._propensity_model = LogisticRegression(max_iter=1000, random_state=42)
        self._scaler = StandardScaler()
        self._is_fitted = False

    def compute_lifetime_value(
        self,
        donor: Donor,
        donations: list[Donation],
        projection_years: int = 5,
        discount_rate: float = 0.10,
    ) -> float:
        """Compute donor lifetime value using historical giving and projected retention.

        Uses a simplified CLV model:
        LTV = sum over years of (annual_value * retention_rate^year * discount_factor^year)
        """
        donor_donations = [d for d in donations if d.donor_id == donor.id]
        if not donor_donations:
            return 0.0

        # Calculate annual giving rate
        amounts = [d.amount for d in donor_donations]
        dates = sorted([d.donation_date for d in donor_donations])

        total = sum(amounts)
        span_days = (dates[-1] - dates[0]).days if len(dates) > 1 else 365
        span_years = max(span_days / 365.0, 0.5)
        annual_value = total / span_years

        # Estimate retention rate from giving patterns
        retention_rate = self._estimate_retention(donor, donor_donations)

        # NPV calculation
        ltv = 0.0
        for year in range(1, projection_years + 1):
            discount_factor = 1.0 / (1.0 + discount_rate) ** year
            ltv += annual_value * (retention_rate ** year) * discount_factor

        return round(ltv, 2)

    def _estimate_retention(self, donor: Donor, donations: list[Donation]) -> float:
        """Estimate donor retention probability based on giving history."""
        if len(donations) < 2:
            return 0.3  # Low retention for single-gift donors

        dates = sorted([d.donation_date for d in donations])
        gaps = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
        avg_gap = np.mean(gaps)

        # Retention based on giving frequency
        if avg_gap <= 30:  # Monthly
            return 0.95
        elif avg_gap <= 90:  # Quarterly
            return 0.85
        elif avg_gap <= 180:  # Semi-annual
            return 0.70
        elif avg_gap <= 365:  # Annual
            return 0.55
        else:
            return 0.30

    def compute_propensity(
        self,
        donor: Donor,
        donations: list[Donation],
        reference_date: Optional[date] = None,
    ) -> float:
        """Compute propensity to give score (0-100) using heuristic model.

        Factors: recency, frequency, monetary trends, donor tenure.
        """
        ref_date = reference_date or date.today()
        donor_donations = [d for d in donations if d.donor_id == donor.id]

        if not donor_donations:
            return 10.0  # Base propensity for new donors

        # Recency factor
        days_since = (
            (ref_date - donor.last_donation_date).days
            if donor.last_donation_date
            else 999
        )
        recency_factor = max(0, 100 - days_since * 0.15)

        # Frequency factor
        freq_factor = min(100, len(donor_donations) * 12)

        # Monetary trend factor
        amounts = [d.amount for d in sorted(donor_donations, key=lambda d: d.donation_date)]
        if len(amounts) >= 2:
            recent_half = amounts[len(amounts) // 2 :]
            older_half = amounts[: len(amounts) // 2]
            avg_recent = np.mean(recent_half)
            avg_older = np.mean(older_half)
            if avg_older > 0:
                trend = (avg_recent - avg_older) / avg_older
                trend_factor = 50 + min(50, max(-50, trend * 50))
            else:
                trend_factor = 50
        else:
            trend_factor = 50

        # Tenure factor
        if donor.first_donation_date:
            tenure_days = (ref_date - donor.first_donation_date).days
            tenure_factor = min(100, tenure_days * 0.1)
        else:
            tenure_factor = 0

        propensity = (
            0.35 * recency_factor
            + 0.25 * freq_factor
            + 0.20 * trend_factor
            + 0.20 * tenure_factor
        )

        return round(min(100.0, max(0.0, propensity)), 2)

    def fit_propensity_model(
        self,
        donors: list[Donor],
        donations: list[Donation],
        labels: list[int],
    ) -> None:
        """Train a logistic regression propensity model on labeled data.

        Labels: 1 = donated again within window, 0 = did not.
        """
        if len(donors) < 2:
            return

        features = []
        for donor in donors:
            donor_donations = [d for d in donations if d.donor_id == donor.id]
            features.append(self._extract_features(donor, donor_donations))

        X = np.array(features)
        y = np.array(labels)

        self._scaler.fit(X)
        X_scaled = self._scaler.transform(X)

        self._propensity_model.fit(X_scaled, y)
        self._is_fitted = True

    def predict_propensity(self, donor: Donor, donations: list[Donation]) -> float:
        """Predict propensity using fitted ML model. Falls back to heuristic if not fitted."""
        if not self._is_fitted:
            return self.compute_propensity(donor, donations)

        donor_donations = [d for d in donations if d.donor_id == donor.id]
        features = self._extract_features(donor, donor_donations)
        X = np.array([features])
        X_scaled = self._scaler.transform(X)
        proba = self._propensity_model.predict_proba(X_scaled)[0][1]
        return round(float(proba) * 100, 2)

    def _extract_features(self, donor: Donor, donations: list[Donation]) -> list[float]:
        """Extract feature vector for ML model."""
        if not donations:
            return [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        amounts = [d.amount for d in donations]
        dates = sorted([d.donation_date for d in donations])

        total = sum(amounts)
        count = len(donations)
        avg = total / count if count > 0 else 0
        std = float(np.std(amounts)) if len(amounts) > 1 else 0

        span = (dates[-1] - dates[0]).days if len(dates) > 1 else 0
        days_since_last = (
            (date.today() - donor.last_donation_date).days
            if donor.last_donation_date
            else 999
        )

        return [total, count, avg, std, span, days_since_last]

    def batch_score(
        self,
        donors: list[Donor],
        donations: list[Donation],
    ) -> list[tuple[Donor, float, float]]:
        """Score all donors, returning (donor, ltv, propensity) tuples."""
        results = []
        for donor in donors:
            ltv = self.compute_lifetime_value(donor, donations)
            propensity = self.compute_propensity(donor, donations)
            donor.lifetime_value = ltv
            donor.propensity_score = propensity
            results.append((donor, ltv, propensity))
        return results
