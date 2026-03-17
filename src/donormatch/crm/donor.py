"""DonorManager - CRUD, search, and segmentation for donor records."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from donormatch.models import Donor, DonorSegment, InterestArea


class DonorManager:
    """Manages donor records with CRUD, search, and segmentation capabilities."""

    def __init__(self) -> None:
        self._donors: dict[UUID, Donor] = {}

    @property
    def count(self) -> int:
        return len(self._donors)

    # ---- CRUD ----

    def create(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        interests: Optional[list[InterestArea]] = None,
    ) -> Donor:
        """Create a new donor record."""
        donor = Donor(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            interests=interests or [],
        )
        self._donors[donor.id] = donor
        return donor

    def get(self, donor_id: UUID) -> Optional[Donor]:
        """Retrieve a donor by ID."""
        return self._donors.get(donor_id)

    def update(self, donor_id: UUID, **kwargs) -> Optional[Donor]:
        """Update a donor's fields."""
        donor = self._donors.get(donor_id)
        if donor is None:
            return None
        for key, value in kwargs.items():
            if hasattr(donor, key):
                setattr(donor, key, value)
        donor.updated_at = datetime.now()
        self._donors[donor_id] = donor
        return donor

    def delete(self, donor_id: UUID) -> bool:
        """Delete a donor record. Returns True if found and deleted."""
        if donor_id in self._donors:
            del self._donors[donor_id]
            return True
        return False

    def list_all(self) -> list[Donor]:
        """List all donors."""
        return list(self._donors.values())

    def add(self, donor: Donor) -> Donor:
        """Add an existing Donor object to the manager."""
        self._donors[donor.id] = donor
        return donor

    # ---- Search ----

    def search(
        self,
        query: Optional[str] = None,
        segment: Optional[DonorSegment] = None,
        interest: Optional[InterestArea] = None,
        min_donated: Optional[float] = None,
        max_donated: Optional[float] = None,
        is_active: Optional[bool] = None,
        state: Optional[str] = None,
    ) -> list[Donor]:
        """Search donors with flexible filters."""
        results = list(self._donors.values())

        if query:
            q = query.lower()
            results = [
                d for d in results
                if q in d.first_name.lower()
                or q in d.last_name.lower()
                or q in d.email.lower()
                or q in d.full_name.lower()
            ]

        if segment is not None:
            results = [d for d in results if d.segment == segment]

        if interest is not None:
            results = [d for d in results if interest in d.interests]

        if min_donated is not None:
            results = [d for d in results if d.total_donated >= min_donated]

        if max_donated is not None:
            results = [d for d in results if d.total_donated <= max_donated]

        if is_active is not None:
            results = [d for d in results if d.is_active == is_active]

        if state is not None:
            results = [d for d in results if d.state == state]

        return results

    # ---- Segmentation ----

    def segment_donors(self) -> dict[DonorSegment, list[Donor]]:
        """Segment all donors based on giving patterns."""
        segments: dict[DonorSegment, list[Donor]] = {s: [] for s in DonorSegment}
        today = date.today()

        for donor in self._donors.values():
            segment = self._classify_segment(donor, today)
            donor.segment = segment
            segments[segment].append(donor)

        return segments

    def _classify_segment(self, donor: Donor, today: date) -> DonorSegment:
        """Classify a single donor into a segment."""
        if donor.donation_count == 0:
            return DonorSegment.NEW

        days_since_last = (
            (today - donor.last_donation_date).days
            if donor.last_donation_date
            else 9999
        )

        if days_since_last > 365:
            return DonorSegment.LAPSED

        if donor.total_donated >= 10000:
            return DonorSegment.MAJOR
        elif donor.total_donated >= 1000:
            return DonorSegment.MID_LEVEL
        else:
            return DonorSegment.SMALL

    def get_top_donors(self, n: int = 10) -> list[Donor]:
        """Get top N donors by total donated amount."""
        donors = list(self._donors.values())
        donors.sort(key=lambda d: d.total_donated, reverse=True)
        return donors[:n]

    def get_segment_summary(self) -> dict[str, dict]:
        """Get summary statistics for each segment."""
        segments = self.segment_donors()
        summary = {}
        for seg, donors in segments.items():
            if donors:
                totals = [d.total_donated for d in donors]
                summary[seg.value] = {
                    "count": len(donors),
                    "total_donated": sum(totals),
                    "avg_donated": sum(totals) / len(totals),
                    "max_donated": max(totals),
                }
            else:
                summary[seg.value] = {
                    "count": 0,
                    "total_donated": 0,
                    "avg_donated": 0,
                    "max_donated": 0,
                }
        return summary
