"""DonorSegmenter - Cluster donors into segments using ML."""

from __future__ import annotations

from datetime import date
from typing import Optional

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from donormatch.models import Donation, Donor, DonorSegment


class DonorSegmenter:
    """Clusters donors into segments: major, mid-level, small, lapsed, new."""

    SEGMENT_LABELS = {
        "high_value": DonorSegment.MAJOR,
        "mid_value": DonorSegment.MID_LEVEL,
        "low_value": DonorSegment.SMALL,
        "lapsed": DonorSegment.LAPSED,
        "new": DonorSegment.NEW,
    }

    def __init__(self, n_clusters: int = 4, random_state: int = 42) -> None:
        self._n_clusters = n_clusters
        self._kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
        self._scaler = StandardScaler()
        self._is_fitted = False
        self._cluster_to_segment: dict[int, DonorSegment] = {}

    def _extract_features(
        self,
        donor: Donor,
        donations: list[Donation],
        reference_date: Optional[date] = None,
    ) -> np.ndarray:
        """Extract features for clustering: recency, frequency, monetary, tenure."""
        ref_date = reference_date or date.today()
        donor_donations = [d for d in donations if d.donor_id == donor.id]

        if not donor_donations:
            return np.array([999.0, 0.0, 0.0, 0.0, 0.0])

        amounts = [d.amount for d in donor_donations]
        dates = sorted([d.donation_date for d in donor_donations])

        recency = (
            (ref_date - donor.last_donation_date).days
            if donor.last_donation_date
            else 999
        )
        frequency = len(donor_donations)
        monetary = sum(amounts)
        avg_donation = monetary / frequency
        tenure = (ref_date - dates[0]).days

        return np.array([
            float(recency),
            float(frequency),
            monetary,
            avg_donation,
            float(tenure),
        ])

    def fit(
        self,
        donors: list[Donor],
        donations: list[Donation],
        reference_date: Optional[date] = None,
    ) -> None:
        """Fit the segmentation model on donor data."""
        if len(donors) < self._n_clusters:
            return

        # Separate new donors (no donations) from others
        donors_with_history = [
            d for d in donors
            if any(don.donor_id == d.id for don in donations)
        ]
        if len(donors_with_history) < self._n_clusters:
            return

        features = np.array([
            self._extract_features(d, donations, reference_date)
            for d in donors_with_history
        ])

        self._scaler.fit(features)
        features_scaled = self._scaler.transform(features)
        self._kmeans.fit(features_scaled)

        # Map clusters to segments based on cluster centroids
        self._map_clusters_to_segments(features)
        self._is_fitted = True

    def _map_clusters_to_segments(self, features: np.ndarray) -> None:
        """Map KMeans cluster labels to donor segments based on centroid characteristics."""
        centroids = self._kmeans.cluster_centers_
        # Inverse transform to get original scale
        centroids_orig = self._scaler.inverse_transform(centroids)

        # Sort clusters by monetary value (index 2) to assign segments
        cluster_monetary = [(i, centroids_orig[i][2]) for i in range(self._n_clusters)]
        cluster_monetary.sort(key=lambda x: x[1], reverse=True)

        segment_order = [
            DonorSegment.MAJOR,
            DonorSegment.MID_LEVEL,
            DonorSegment.SMALL,
            DonorSegment.LAPSED,
        ]

        for rank, (cluster_id, _) in enumerate(cluster_monetary):
            if rank < len(segment_order):
                # Check if this cluster has high recency (lapsed)
                recency = centroids_orig[cluster_id][0]
                if recency > 300 and rank >= 2:
                    self._cluster_to_segment[cluster_id] = DonorSegment.LAPSED
                else:
                    self._cluster_to_segment[cluster_id] = segment_order[rank]
            else:
                self._cluster_to_segment[cluster_id] = DonorSegment.SMALL

    def predict(
        self,
        donor: Donor,
        donations: list[Donation],
        reference_date: Optional[date] = None,
    ) -> DonorSegment:
        """Predict segment for a single donor."""
        donor_donations = [d for d in donations if d.donor_id == donor.id]

        if not donor_donations:
            return DonorSegment.NEW

        if not self._is_fitted:
            return self._rule_based_segment(donor, reference_date)

        features = self._extract_features(donor, donations, reference_date)
        features_scaled = self._scaler.transform(features.reshape(1, -1))
        cluster = self._kmeans.predict(features_scaled)[0]
        return self._cluster_to_segment.get(cluster, DonorSegment.SMALL)

    def segment_all(
        self,
        donors: list[Donor],
        donations: list[Donation],
        reference_date: Optional[date] = None,
    ) -> dict[DonorSegment, list[Donor]]:
        """Segment all donors, fitting the model if needed."""
        if not self._is_fitted:
            self.fit(donors, donations, reference_date)

        segments: dict[DonorSegment, list[Donor]] = {s: [] for s in DonorSegment}

        for donor in donors:
            segment = self.predict(donor, donations, reference_date)
            donor.segment = segment
            segments[segment].append(donor)

        return segments

    def _rule_based_segment(
        self, donor: Donor, reference_date: Optional[date] = None
    ) -> DonorSegment:
        """Fallback rule-based segmentation when ML model is not fitted."""
        ref_date = reference_date or date.today()

        if donor.donation_count == 0:
            return DonorSegment.NEW

        days_since = (
            (ref_date - donor.last_donation_date).days
            if donor.last_donation_date
            else 9999
        )

        if days_since > 365:
            return DonorSegment.LAPSED
        if donor.total_donated >= 10000:
            return DonorSegment.MAJOR
        elif donor.total_donated >= 1000:
            return DonorSegment.MID_LEVEL
        else:
            return DonorSegment.SMALL

    def get_segment_stats(
        self, segments: dict[DonorSegment, list[Donor]]
    ) -> dict[str, dict]:
        """Compute statistics for each segment."""
        stats = {}
        for segment, donors in segments.items():
            if donors:
                totals = [d.total_donated for d in donors]
                stats[segment.value] = {
                    "count": len(donors),
                    "total_donated": round(sum(totals), 2),
                    "avg_donated": round(sum(totals) / len(totals), 2),
                    "avg_engagement": round(
                        sum(d.engagement_score for d in donors) / len(donors), 2
                    ),
                }
            else:
                stats[segment.value] = {
                    "count": 0,
                    "total_donated": 0,
                    "avg_donated": 0,
                    "avg_engagement": 0,
                }
        return stats
