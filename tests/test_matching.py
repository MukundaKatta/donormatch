"""Tests for matching modules: DonorMatcher, DonorScorer, DonorSegmenter."""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from donormatch.matching.matcher import DonorMatcher
from donormatch.matching.scorer import DonorScorer
from donormatch.matching.segmenter import DonorSegmenter
from donormatch.models import (
    Campaign,
    Donation,
    Donor,
    DonorSegment,
    InterestArea,
)
from donormatch.simulator import Simulator


class TestDonorMatcher:
    def setup_method(self):
        self.matcher = DonorMatcher()

    def test_match_donors_to_campaign(self):
        campaign = Campaign(
            name="Education Fund",
            description="Test",
            goal=50000,
            interest_area=InterestArea.EDUCATION,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=90),
        )
        donors = [
            Donor(
                first_name="Alice", last_name="A", email="a@a.com",
                interests=[InterestArea.EDUCATION],
                total_donated=5000, donation_count=10,
                engagement_score=80, propensity_score=70,
            ),
            Donor(
                first_name="Bob", last_name="B", email="b@b.com",
                interests=[InterestArea.HEALTH],
                total_donated=100, donation_count=1,
                engagement_score=20, propensity_score=10,
            ),
        ]
        donations = [
            Donation(donor_id=donors[0].id, campaign_id=campaign.id, amount=500),
        ]

        matches = self.matcher.match_donors_to_campaign(
            campaign, donors, donations, top_n=2
        )
        assert len(matches) == 2
        # Alice should match better (education interest, higher engagement)
        assert matches[0][0].first_name == "Alice"
        assert matches[0][1] > matches[1][1]

    def test_match_campaigns_to_donor(self):
        donor = Donor(
            first_name="Test", last_name="D", email="t@d.com",
            interests=[InterestArea.ENVIRONMENT],
            total_donated=2000, donation_count=5,
            engagement_score=60, propensity_score=50,
        )
        campaigns = [
            Campaign(
                name="Green", description="Env",
                goal=10000, interest_area=InterestArea.ENVIRONMENT,
                start_date=date.today(), end_date=date.today() + timedelta(days=60),
            ),
            Campaign(
                name="Art", description="Art",
                goal=10000, interest_area=InterestArea.ARTS,
                start_date=date.today(), end_date=date.today() + timedelta(days=60),
            ),
        ]
        matches = self.matcher.match_campaigns_to_donor(donor, campaigns, [])
        assert len(matches) == 2
        # Environment campaign should rank higher
        assert matches[0][0].name == "Green"

    def test_empty_donors(self):
        campaign = Campaign(
            name="Test", description="T", goal=1000,
            interest_area=InterestArea.HEALTH,
            start_date=date.today(), end_date=date.today() + timedelta(days=30),
        )
        matches = self.matcher.match_donors_to_campaign(campaign, [], [])
        assert matches == []

    def test_bulk_match(self):
        sim = Simulator(seed=99)
        donors, campaigns, donations = sim.generate_full_dataset(
            n_donors=20, n_campaigns=3
        )
        results = self.matcher.bulk_match(donors, campaigns, donations)
        assert len(results) == 3
        for campaign_id, matches in results.items():
            assert len(matches) == 20


class TestDonorScorer:
    def setup_method(self):
        self.scorer = DonorScorer()

    def test_lifetime_value_no_donations(self):
        donor = Donor(first_name="A", last_name="B", email="a@b.com")
        ltv = self.scorer.compute_lifetime_value(donor, [])
        assert ltv == 0.0

    def test_lifetime_value_with_donations(self):
        donor = Donor(
            first_name="A", last_name="B", email="a@b.com",
            last_donation_date=date.today(),
        )
        donations = [
            Donation(
                donor_id=donor.id, campaign_id=uuid4(), amount=100,
                donation_date=date.today() - timedelta(days=i * 30),
            )
            for i in range(6)
        ]
        ltv = self.scorer.compute_lifetime_value(donor, donations)
        assert ltv > 0

    def test_propensity_no_donations(self):
        donor = Donor(first_name="A", last_name="B", email="a@b.com")
        score = self.scorer.compute_propensity(donor, [])
        assert score == 10.0

    def test_propensity_with_donations(self):
        donor = Donor(
            first_name="A", last_name="B", email="a@b.com",
            last_donation_date=date.today() - timedelta(days=15),
            first_donation_date=date.today() - timedelta(days=365),
        )
        donations = [
            Donation(
                donor_id=donor.id, campaign_id=uuid4(), amount=100 + i * 10,
                donation_date=date.today() - timedelta(days=i * 30),
            )
            for i in range(5)
        ]
        score = self.scorer.compute_propensity(donor, donations)
        assert 0 <= score <= 100

    def test_batch_score(self):
        sim = Simulator(seed=55)
        donors, campaigns, donations = sim.generate_full_dataset(n_donors=10, n_campaigns=2)
        results = self.scorer.batch_score(donors, donations)
        assert len(results) == 10
        for donor, ltv, propensity in results:
            assert ltv >= 0
            assert 0 <= propensity <= 100


class TestDonorSegmenter:
    def test_rule_based_segmentation(self):
        segmenter = DonorSegmenter()

        new_donor = Donor(first_name="N", last_name="D", email="n@d.com")
        assert segmenter.predict(new_donor, []) == DonorSegment.NEW

        major = Donor(
            first_name="M", last_name="D", email="m@d.com",
            total_donated=15000, donation_count=20,
            last_donation_date=date.today() - timedelta(days=30),
        )
        donations = [Donation(donor_id=major.id, campaign_id=uuid4(), amount=100)]
        assert segmenter.predict(major, donations) == DonorSegment.MAJOR

    def test_ml_segmentation(self):
        sim = Simulator(seed=77)
        donors, campaigns, donations = sim.generate_full_dataset(
            n_donors=50, n_campaigns=3
        )
        segmenter = DonorSegmenter(n_clusters=4)
        segments = segmenter.segment_all(donors, donations)

        total_segmented = sum(len(v) for v in segments.values())
        assert total_segmented == 50

        # Every segment type should be a key
        for seg in DonorSegment:
            assert seg in segments

    def test_segment_stats(self):
        sim = Simulator(seed=88)
        donors, campaigns, donations = sim.generate_full_dataset(n_donors=30, n_campaigns=2)
        segmenter = DonorSegmenter()
        segments = segmenter.segment_all(donors, donations)
        stats = segmenter.get_segment_stats(segments)
        assert isinstance(stats, dict)
        for key in stats:
            assert "count" in stats[key]
            assert "total_donated" in stats[key]
