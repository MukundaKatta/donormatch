"""Tests for DonorMatch data models."""

from datetime import date, timedelta

import pytest

from donormatch.models import (
    Campaign,
    CampaignStatus,
    Donation,
    Donor,
    DonorSegment,
    Engagement,
    InterestArea,
)


class TestDonor:
    def test_create_donor(self):
        donor = Donor(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
        )
        assert donor.first_name == "Jane"
        assert donor.last_name == "Doe"
        assert donor.full_name == "Jane Doe"
        assert donor.segment == DonorSegment.NEW
        assert donor.is_active is True

    def test_average_donation_no_donations(self):
        donor = Donor(first_name="A", last_name="B", email="a@b.com")
        assert donor.average_donation == 0.0

    def test_average_donation(self):
        donor = Donor(
            first_name="A",
            last_name="B",
            email="a@b.com",
            total_donated=1000.0,
            donation_count=4,
        )
        assert donor.average_donation == 250.0

    def test_donor_interests(self):
        donor = Donor(
            first_name="A",
            last_name="B",
            email="a@b.com",
            interests=[InterestArea.EDUCATION, InterestArea.HEALTH],
        )
        assert len(donor.interests) == 2
        assert InterestArea.EDUCATION in donor.interests


class TestCampaign:
    def test_create_campaign(self):
        campaign = Campaign(
            name="Test Campaign",
            description="A test",
            goal=10000.0,
            interest_area=InterestArea.EDUCATION,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
        assert campaign.progress == 0.0
        assert campaign.remaining == 10000.0
        assert not campaign.is_complete

    def test_campaign_progress(self):
        campaign = Campaign(
            name="Test",
            description="Test",
            goal=10000.0,
            raised=7500.0,
            interest_area=InterestArea.HEALTH,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
        assert campaign.progress == 75.0
        assert campaign.remaining == 2500.0

    def test_campaign_complete(self):
        campaign = Campaign(
            name="Test",
            description="Test",
            goal=5000.0,
            raised=5000.0,
            interest_area=InterestArea.ARTS,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
        assert campaign.is_complete
        assert campaign.progress == 100.0


class TestDonation:
    def test_create_donation(self):
        from uuid import uuid4

        donation = Donation(
            donor_id=uuid4(),
            campaign_id=uuid4(),
            amount=100.0,
        )
        assert donation.amount == 100.0
        assert donation.is_recurring is False


class TestEngagement:
    def test_rfm_tiers(self):
        eng = Engagement(donor_id=Donor(first_name="A", last_name="B", email="a@b.com").id)

        eng.overall_score = 90
        assert eng.rfm_tier == "champion"

        eng.overall_score = 65
        assert eng.rfm_tier == "loyal"

        eng.overall_score = 45
        assert eng.rfm_tier == "potential"

        eng.overall_score = 25
        assert eng.rfm_tier == "at_risk"

        eng.overall_score = 10
        assert eng.rfm_tier == "dormant"
