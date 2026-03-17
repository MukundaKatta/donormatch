"""Simulator - Generate synthetic donor, campaign, and donation data."""

from __future__ import annotations

import random
from datetime import date, timedelta

import numpy as np

from donormatch.models import (
    Campaign,
    CampaignStatus,
    Donation,
    Donor,
    DonorSegment,
    InterestArea,
)


# Realistic name pools
FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Lisa", "Daniel", "Nancy",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Carol", "Kevin", "Amanda", "Brian", "Dorothy", "George", "Melissa",
    "Timothy", "Deborah", "Priya", "Raj", "Aisha", "Wei", "Yuki", "Carlos",
    "Fatima", "Olga", "Hiroshi", "Amara",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill",
    "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
    "Mitchell", "Carter", "Patel", "Kumar", "Chen", "Yamamoto", "Kim", "Singh",
]

CITIES = [
    ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"),
    ("Houston", "TX"), ("Phoenix", "AZ"), ("Philadelphia", "PA"),
    ("San Antonio", "TX"), ("San Diego", "CA"), ("Dallas", "TX"),
    ("San Jose", "CA"), ("Austin", "TX"), ("Jacksonville", "FL"),
    ("Fort Worth", "TX"), ("Columbus", "OH"), ("Charlotte", "NC"),
    ("Seattle", "WA"), ("Denver", "CO"), ("Portland", "OR"),
    ("Nashville", "TN"), ("Boston", "MA"),
]

CAMPAIGN_TEMPLATES = [
    ("Save the Rainforest", "Protecting endangered rainforest ecosystems", InterestArea.ENVIRONMENT),
    ("Scholarship Fund", "Providing scholarships to underprivileged students", InterestArea.EDUCATION),
    ("Community Health Initiative", "Improving health access in underserved areas", InterestArea.HEALTH),
    ("Arts in Schools", "Bringing art programs to public schools", InterestArea.ARTS),
    ("Equal Justice Project", "Legal aid for marginalized communities", InterestArea.SOCIAL_JUSTICE),
    ("Animal Rescue Fund", "Rescuing and rehabilitating abused animals", InterestArea.ANIMAL_WELFARE),
    ("Disaster Response Team", "Rapid response for natural disaster relief", InterestArea.DISASTER_RELIEF),
    ("Tech for Good", "Technology solutions for nonprofit organizations", InterestArea.TECHNOLOGY),
    ("Neighborhood Revitalization", "Rebuilding and improving local communities", InterestArea.COMMUNITY),
    ("Cancer Research Fund", "Funding breakthrough cancer research", InterestArea.RESEARCH),
    ("Clean Water Initiative", "Providing clean water to developing regions", InterestArea.HEALTH),
    ("STEM Education Program", "Promoting STEM education in rural areas", InterestArea.EDUCATION),
    ("Wildlife Conservation", "Protecting endangered species globally", InterestArea.ENVIRONMENT),
    ("Youth Mentorship", "Mentoring at-risk youth in urban areas", InterestArea.COMMUNITY),
    ("Medical Research Grant", "Supporting innovative medical research", InterestArea.RESEARCH),
]


class Simulator:
    """Generates synthetic data for testing and demonstration."""

    def __init__(self, seed: int = 42) -> None:
        self.rng = random.Random(seed)
        self.np_rng = np.random.RandomState(seed)

    def generate_donors(self, n: int = 100) -> list[Donor]:
        """Generate n synthetic donors with realistic attributes."""
        donors = []
        for _ in range(n):
            city, state = self.rng.choice(CITIES)
            num_interests = self.rng.randint(1, 4)
            interests = self.rng.sample(list(InterestArea), num_interests)

            donor = Donor(
                first_name=self.rng.choice(FIRST_NAMES),
                last_name=self.rng.choice(LAST_NAMES),
                email=f"{self.rng.choice(FIRST_NAMES).lower()}.{self.rng.choice(LAST_NAMES).lower()}{self.rng.randint(1,999)}@example.com",
                phone=f"({self.rng.randint(200,999)}) {self.rng.randint(200,999)}-{self.rng.randint(1000,9999)}",
                city=city,
                state=state,
                zip_code=f"{self.rng.randint(10000, 99999)}",
                interests=interests,
            )
            donors.append(donor)
        return donors

    def generate_campaigns(self, n: int = 5) -> list[Campaign]:
        """Generate n synthetic campaigns."""
        campaigns = []
        templates = self.rng.sample(
            CAMPAIGN_TEMPLATES, min(n, len(CAMPAIGN_TEMPLATES))
        )
        if n > len(CAMPAIGN_TEMPLATES):
            templates = templates * (n // len(CAMPAIGN_TEMPLATES) + 1)
            templates = templates[:n]

        for name, desc, interest in templates:
            goal = round(self.rng.uniform(5000, 500000), 2)
            start = date.today() - timedelta(days=self.rng.randint(0, 180))
            end = start + timedelta(days=self.rng.randint(30, 365))

            status = self.rng.choice([
                CampaignStatus.ACTIVE,
                CampaignStatus.ACTIVE,
                CampaignStatus.ACTIVE,
                CampaignStatus.DRAFT,
                CampaignStatus.COMPLETED,
            ])

            target_segs = self.rng.sample(
                list(DonorSegment),
                self.rng.randint(1, 3),
            )

            campaign = Campaign(
                name=name,
                description=desc,
                goal=goal,
                interest_area=interest,
                start_date=start,
                end_date=end,
                status=status,
                min_donation=round(self.rng.uniform(10, 100), 2),
                target_segments=target_segs,
            )
            campaigns.append(campaign)
        return campaigns

    def generate_donations(
        self,
        donors: list[Donor],
        campaigns: list[Campaign],
        avg_per_donor: float = 3.0,
    ) -> list[Donation]:
        """Generate synthetic donation history."""
        donations = []

        for donor in donors:
            # Number of donations follows a power-law-ish distribution
            n_donations = max(0, int(self.np_rng.exponential(avg_per_donor)))

            for _ in range(n_donations):
                campaign = self.rng.choice(campaigns)

                # Donation amount with log-normal distribution
                base_amount = self.np_rng.lognormal(mean=4.0, sigma=1.5)
                amount = round(max(5.0, min(base_amount, 50000.0)), 2)

                # Random date within campaign window
                days_range = max(1, (campaign.end_date - campaign.start_date).days)
                donation_date = campaign.start_date + timedelta(
                    days=self.rng.randint(0, days_range)
                )

                donation = Donation(
                    donor_id=donor.id,
                    campaign_id=campaign.id,
                    amount=amount,
                    donation_date=donation_date,
                    is_recurring=self.rng.random() < 0.2,
                )
                donations.append(donation)

                # Update donor stats
                donor.total_donated += amount
                donor.donation_count += 1
                if donor.first_donation_date is None or donation_date < donor.first_donation_date:
                    donor.first_donation_date = donation_date
                if donor.last_donation_date is None or donation_date > donor.last_donation_date:
                    donor.last_donation_date = donation_date

                # Update campaign stats
                campaign.raised += amount
                campaign.donation_count += 1

        # Update unique donor counts per campaign
        for campaign in campaigns:
            campaign_donations = [d for d in donations if d.campaign_id == campaign.id]
            campaign.donor_count = len({d.donor_id for d in campaign_donations})

        return donations

    def generate_full_dataset(
        self,
        n_donors: int = 100,
        n_campaigns: int = 5,
        avg_donations_per_donor: float = 3.0,
    ) -> tuple[list[Donor], list[Campaign], list[Donation]]:
        """Generate a complete synthetic dataset."""
        donors = self.generate_donors(n_donors)
        campaigns = self.generate_campaigns(n_campaigns)
        donations = self.generate_donations(donors, campaigns, avg_donations_per_donor)
        return donors, campaigns, donations
