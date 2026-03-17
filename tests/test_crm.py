"""Tests for CRM modules: DonorManager, CampaignManager, EngagementTracker."""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from donormatch.crm.campaign import CampaignManager
from donormatch.crm.donor import DonorManager
from donormatch.crm.engagement import EngagementTracker
from donormatch.models import (
    Campaign,
    CampaignStatus,
    Donation,
    Donor,
    DonorSegment,
    InterestArea,
)


class TestDonorManager:
    def setup_method(self):
        self.mgr = DonorManager()

    def test_create_donor(self):
        donor = self.mgr.create("Jane", "Doe", "jane@example.com")
        assert donor.first_name == "Jane"
        assert self.mgr.count == 1

    def test_get_donor(self):
        donor = self.mgr.create("Jane", "Doe", "jane@example.com")
        found = self.mgr.get(donor.id)
        assert found is not None
        assert found.email == "jane@example.com"

    def test_get_nonexistent(self):
        assert self.mgr.get(uuid4()) is None

    def test_update_donor(self):
        donor = self.mgr.create("Jane", "Doe", "jane@example.com")
        updated = self.mgr.update(donor.id, first_name="Janet", city="Boston")
        assert updated.first_name == "Janet"
        assert updated.city == "Boston"

    def test_delete_donor(self):
        donor = self.mgr.create("Jane", "Doe", "jane@example.com")
        assert self.mgr.delete(donor.id) is True
        assert self.mgr.count == 0
        assert self.mgr.delete(uuid4()) is False

    def test_search_by_name(self):
        self.mgr.create("Jane", "Doe", "jane@example.com")
        self.mgr.create("John", "Smith", "john@example.com")
        results = self.mgr.search(query="jane")
        assert len(results) == 1
        assert results[0].first_name == "Jane"

    def test_search_by_segment(self):
        d1 = self.mgr.create("A", "B", "a@b.com")
        d2 = self.mgr.create("C", "D", "c@d.com")
        self.mgr.update(d1.id, segment=DonorSegment.MAJOR)
        results = self.mgr.search(segment=DonorSegment.MAJOR)
        assert len(results) == 1

    def test_search_by_interest(self):
        self.mgr.create("A", "B", "a@b.com", interests=[InterestArea.EDUCATION])
        self.mgr.create("C", "D", "c@d.com", interests=[InterestArea.HEALTH])
        results = self.mgr.search(interest=InterestArea.EDUCATION)
        assert len(results) == 1

    def test_search_by_donation_range(self):
        d1 = self.mgr.create("A", "B", "a@b.com")
        d2 = self.mgr.create("C", "D", "c@d.com")
        self.mgr.update(d1.id, total_donated=5000)
        self.mgr.update(d2.id, total_donated=500)
        results = self.mgr.search(min_donated=1000)
        assert len(results) == 1

    def test_segment_donors(self):
        d = self.mgr.create("A", "B", "a@b.com")
        self.mgr.update(
            d.id,
            total_donated=15000,
            donation_count=10,
            last_donation_date=date.today() - timedelta(days=30),
        )
        segments = self.mgr.segment_donors()
        assert d.segment == DonorSegment.MAJOR

    def test_get_top_donors(self):
        for i in range(5):
            d = self.mgr.create(f"Donor{i}", "Test", f"d{i}@test.com")
            self.mgr.update(d.id, total_donated=float(i * 1000))
        top = self.mgr.get_top_donors(3)
        assert len(top) == 3
        assert top[0].total_donated == 4000


class TestCampaignManager:
    def setup_method(self):
        self.mgr = CampaignManager()

    def test_create_campaign(self):
        c = self.mgr.create(
            name="Test",
            description="A test campaign",
            goal=10000,
            interest_area=InterestArea.EDUCATION,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
        assert c.name == "Test"
        assert self.mgr.count == 1

    def test_record_donation(self):
        c = self.mgr.create(
            "Test", "Desc", 10000, InterestArea.HEALTH,
            date.today(), date.today() + timedelta(days=30),
        )
        donation = Donation(
            donor_id=uuid4(), campaign_id=c.id, amount=500
        )
        assert self.mgr.record_donation(donation) is True
        updated = self.mgr.get(c.id)
        assert updated.raised == 500
        assert updated.donation_count == 1

    def test_campaign_status_transitions(self):
        c = self.mgr.create(
            "Test", "Desc", 10000, InterestArea.ARTS,
            date.today(), date.today() + timedelta(days=30),
        )
        self.mgr.activate(c.id)
        assert self.mgr.get(c.id).status == CampaignStatus.ACTIVE

        self.mgr.pause(c.id)
        assert self.mgr.get(c.id).status == CampaignStatus.PAUSED

        self.mgr.complete(c.id)
        assert self.mgr.get(c.id).status == CampaignStatus.COMPLETED

    def test_get_active_campaigns(self):
        c1 = self.mgr.create(
            "Active", "Desc", 10000, InterestArea.HEALTH,
            date.today(), date.today() + timedelta(days=30),
        )
        self.mgr.activate(c1.id)
        c2 = self.mgr.create(
            "Draft", "Desc", 5000, InterestArea.ARTS,
            date.today(), date.today() + timedelta(days=30),
        )
        active = self.mgr.get_active_campaigns()
        assert len(active) == 1

    def test_delete_campaign(self):
        c = self.mgr.create(
            "Test", "Desc", 10000, InterestArea.EDUCATION,
            date.today(), date.today() + timedelta(days=30),
        )
        assert self.mgr.delete(c.id) is True
        assert self.mgr.count == 0


class TestEngagementTracker:
    def test_calculate_engagement(self):
        donor = Donor(
            first_name="Test",
            last_name="Donor",
            email="test@test.com",
            last_donation_date=date.today() - timedelta(days=10),
        )
        donations = [
            Donation(donor_id=donor.id, campaign_id=uuid4(), amount=100),
            Donation(donor_id=donor.id, campaign_id=uuid4(), amount=200),
        ]

        tracker = EngagementTracker()
        eng = tracker.calculate_engagement(donor, donations)

        assert eng.recency_score > 0
        assert eng.frequency_score > 0
        assert eng.monetary_score > 0
        assert eng.overall_score > 0

    def test_no_donations_low_engagement(self):
        donor = Donor(first_name="New", last_name="Donor", email="new@test.com")
        tracker = EngagementTracker()
        eng = tracker.calculate_engagement(donor, [])
        assert eng.recency_score == 0
        assert eng.frequency_score == 0
        assert eng.monetary_score == 0

    def test_batch_calculate(self):
        donors = [
            Donor(first_name="A", last_name="B", email="a@b.com",
                  last_donation_date=date.today()),
            Donor(first_name="C", last_name="D", email="c@d.com",
                  last_donation_date=date.today() - timedelta(days=100)),
        ]
        donations = [
            Donation(donor_id=donors[0].id, campaign_id=uuid4(), amount=500),
            Donation(donor_id=donors[1].id, campaign_id=uuid4(), amount=50),
        ]

        tracker = EngagementTracker()
        results = tracker.batch_calculate(donors, donations)
        assert len(results) == 2
        # More recent donor should have higher recency
        assert results[0].recency_score > results[1].recency_score

    def test_tier_distribution(self):
        tracker = EngagementTracker()
        donors = [
            Donor(first_name=f"D{i}", last_name="T", email=f"d{i}@t.com",
                  last_donation_date=date.today())
            for i in range(5)
        ]
        donations = [
            Donation(donor_id=d.id, campaign_id=uuid4(), amount=100)
            for d in donors
        ]
        tracker.batch_calculate(donors, donations)
        dist = tracker.get_tier_distribution()
        assert sum(dist.values()) == 5
