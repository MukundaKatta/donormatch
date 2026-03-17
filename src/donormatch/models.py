"""Pydantic data models for DonorMatch."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DonorSegment(str, Enum):
    """Donor segment classification."""

    MAJOR = "major"
    MID_LEVEL = "mid_level"
    SMALL = "small"
    LAPSED = "lapsed"
    NEW = "new"


class CampaignStatus(str, Enum):
    """Campaign lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class InterestArea(str, Enum):
    """Donor interest areas."""

    EDUCATION = "education"
    HEALTH = "health"
    ENVIRONMENT = "environment"
    ARTS = "arts"
    SOCIAL_JUSTICE = "social_justice"
    ANIMAL_WELFARE = "animal_welfare"
    DISASTER_RELIEF = "disaster_relief"
    TECHNOLOGY = "technology"
    COMMUNITY = "community"
    RESEARCH = "research"


class Donor(BaseModel):
    """Represents a nonprofit donor."""

    id: UUID = Field(default_factory=uuid4)
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    interests: list[InterestArea] = Field(default_factory=list)
    segment: DonorSegment = DonorSegment.NEW
    total_donated: float = 0.0
    donation_count: int = 0
    first_donation_date: Optional[date] = None
    last_donation_date: Optional[date] = None
    engagement_score: float = 0.0
    lifetime_value: float = 0.0
    propensity_score: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def average_donation(self) -> float:
        if self.donation_count == 0:
            return 0.0
        return self.total_donated / self.donation_count


class Campaign(BaseModel):
    """Represents a fundraising campaign."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    goal: float
    raised: float = 0.0
    interest_area: InterestArea
    status: CampaignStatus = CampaignStatus.DRAFT
    start_date: date
    end_date: date
    donor_count: int = 0
    donation_count: int = 0
    min_donation: float = 0.0
    target_segments: list[DonorSegment] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def progress(self) -> float:
        """Campaign progress as a percentage."""
        if self.goal <= 0:
            return 0.0
        return min((self.raised / self.goal) * 100, 100.0)

    @property
    def remaining(self) -> float:
        """Amount remaining to reach goal."""
        return max(self.goal - self.raised, 0.0)

    @property
    def is_complete(self) -> bool:
        return self.raised >= self.goal


class Donation(BaseModel):
    """Represents a single donation transaction."""

    id: UUID = Field(default_factory=uuid4)
    donor_id: UUID
    campaign_id: UUID
    amount: float
    donation_date: date = Field(default_factory=date.today)
    is_recurring: bool = False
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class Engagement(BaseModel):
    """Tracks donor engagement metrics."""

    id: UUID = Field(default_factory=uuid4)
    donor_id: UUID
    recency_score: float = 0.0  # 0-100, how recently they donated
    frequency_score: float = 0.0  # 0-100, how often they donate
    monetary_score: float = 0.0  # 0-100, how much they donate
    overall_score: float = 0.0  # Weighted composite score
    email_open_rate: float = 0.0
    event_attendance: int = 0
    volunteer_hours: float = 0.0
    last_interaction: Optional[date] = None
    calculated_at: datetime = Field(default_factory=datetime.now)

    @property
    def rfm_tier(self) -> str:
        """Classify donor into RFM tier."""
        avg = self.overall_score
        if avg >= 80:
            return "champion"
        elif avg >= 60:
            return "loyal"
        elif avg >= 40:
            return "potential"
        elif avg >= 20:
            return "at_risk"
        else:
            return "dormant"
