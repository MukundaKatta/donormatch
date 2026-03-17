"""Tests for the Simulator."""

import pytest

from donormatch.simulator import Simulator


class TestSimulator:
    def test_generate_donors(self):
        sim = Simulator(seed=42)
        donors = sim.generate_donors(20)
        assert len(donors) == 20
        for d in donors:
            assert d.first_name
            assert d.last_name
            assert "@" in d.email
            assert len(d.interests) >= 1

    def test_generate_campaigns(self):
        sim = Simulator(seed=42)
        campaigns = sim.generate_campaigns(5)
        assert len(campaigns) == 5
        for c in campaigns:
            assert c.goal > 0
            assert c.start_date <= c.end_date

    def test_generate_donations(self):
        sim = Simulator(seed=42)
        donors = sim.generate_donors(10)
        campaigns = sim.generate_campaigns(3)
        donations = sim.generate_donations(donors, campaigns)
        # Should have some donations
        assert len(donations) > 0
        for d in donations:
            assert d.amount > 0

    def test_full_dataset(self):
        sim = Simulator(seed=42)
        donors, campaigns, donations = sim.generate_full_dataset(
            n_donors=50, n_campaigns=3
        )
        assert len(donors) == 50
        assert len(campaigns) == 3
        assert len(donations) > 0

    def test_reproducibility(self):
        sim1 = Simulator(seed=123)
        sim2 = Simulator(seed=123)
        d1 = sim1.generate_donors(10)
        d2 = sim2.generate_donors(10)
        for a, b in zip(d1, d2):
            assert a.first_name == b.first_name
            assert a.last_name == b.last_name
