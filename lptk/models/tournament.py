"""Tournament structure models.

This module defines Pydantic models for representing tournament phases,
phase groups, and match/set details from start.gg.
"""

# Third-party
from pydantic import BaseModel, Field


class PhaseGroup(BaseModel):
    """A phase group (bracket/pool) within a tournament phase.

    Attributes:
        id: Internal start.gg phase group ID.
        identifier: Display identifier (e.g., "B1", "Pool A").
        state: Phase group state (1=CREATED, 2=ACTIVE, 3=COMPLETED).
        num_seeds: Number of entrants seeded into this group.
    """

    id: int
    identifier: str = ""
    state: int | str = 1
    num_seeds: int = 0

    @property
    def is_completed(self) -> bool:
        """Check if the phase group has completed."""
        return self.state in (3, "COMPLETED")

    @property
    def is_active(self) -> bool:
        """Check if the phase group is currently active."""
        return self.state in (2, "ACTIVE")


class Phase(BaseModel):
    """A tournament phase (stage) containing one or more phase groups.

    Attributes:
        id: Internal start.gg phase ID.
        name: Display name of the phase (e.g., "Day 2", "Playoffs").
        state: Phase state (1=CREATED, 2=ACTIVE, 3=COMPLETED).
        num_seeds: Total number of entrants in this phase.
        groups: List of phase groups within this phase.
    """

    id: int
    name: str
    state: int | str = 1
    num_seeds: int = 0
    groups: list[PhaseGroup] = Field(default_factory=list)

    @property
    def is_completed(self) -> bool:
        """Check if the phase has completed."""
        return self.state in (3, "COMPLETED")

    @property
    def is_active(self) -> bool:
        """Check if the phase is currently active."""
        return self.state in (2, "ACTIVE")


class SetSlot(BaseModel):
    """A participant slot in a match/set.

    Attributes:
        entrant_id: Internal start.gg entrant ID.
        entrant_name: Display name of the entrant.
        score: Game score for this entrant in the set.
    """

    entrant_id: int | None = None
    entrant_name: str | None = None
    score: int | None = None


class SetDetails(BaseModel):
    """Details of a completed match/set.

    Attributes:
        set_id: Internal start.gg set ID.
        identifier: Match identifier within the bracket (e.g., "AL", "B1 AM").
        winner_id: Entrant ID of the winner.
        winner_name: Display name of the winner.
        loser_name: Display name of the loser.
        winner_score: Winner's game score.
        loser_score: Loser's game score.
    """

    set_id: int
    identifier: str = ""
    winner_id: int | None = None
    winner_name: str = ""
    loser_name: str = ""
    winner_score: int | None = None
    loser_score: int | None = None

    @property
    def bracket_group(self) -> str | None:
        """Extract bracket group from identifier (e.g., 'B1' from 'B1 AL')."""
        parts = self.identifier.split()
        if len(parts) >= 2:
            return parts[0]
        return None

    @property
    def match_id(self) -> str:
        """Extract match ID from identifier (e.g., 'AL' from 'B1 AL')."""
        parts = self.identifier.split()
        if len(parts) >= 2:
            return parts[1]
        return self.identifier

    def format_score(self) -> str:
        """Format score for display, handling forfeits.

        Returns:
            Formatted score string (e.g., "3-2", "W-FF", "FF-W").
        """
        if self.winner_score is None and self.loser_score is None:
            return ""
        if self.loser_score == -1:
            return "W-FF"
        if self.winner_score == -1:
            return "FF-W"
        return f"{self.winner_score}-{self.loser_score}"
