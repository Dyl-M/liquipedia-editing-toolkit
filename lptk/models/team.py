"""Team and player models for tournament data.

This module defines Pydantic models for representing players and teams
fetched from start.gg tournaments.
"""

# Third-party
from pydantic import BaseModel, Field


class Player(BaseModel):
    """A tournament participant/player.

    Attributes:
        player_id: Internal start.gg participant ID.
        player_tag: Player's in-game name/gamertag.
        player_country: ISO 3166-1 alpha-2 country code (lowercase, e.g., "fr", "us").
    """

    player_id: int | None = None
    player_tag: str = ""
    player_country: str | None = None

    def __str__(self) -> str:
        if self.player_country:
            return f"{self.player_tag} ({self.player_country})"
        return self.player_tag


class Team(BaseModel):
    """A tournament team/entrant with placement and roster.

    Attributes:
        placement: Current standing/placement in the tournament (1 = winner).
        team_name: Display name of the team (None for empty placeholders).
        members: List of players on the team roster.
        entrant_id: Internal start.gg entrant ID for API lookups.
        elimination_set_id: ID of the set where the team was eliminated.
        bracket_group: Bracket group identifier (e.g., "B1", "B2").
        bracket_identifier: Match identifier within the bracket (e.g., "AL", "AM").
        source_phase: Name of the phase this team was collected from.
        phase_type: Type of phase (finals, playoffs, swiss, pools).
        pool_group: Pool/group identifier for earlier stages.
        pool_placement: Placement within the pool/group.
        pool_number: Numeric pool identifier for sorting.
    """

    placement: int = Field(ge=1, description="Tournament placement (1 = winner)")
    team_name: str | None = None
    members: list[Player] = Field(default_factory=list)
    entrant_id: int | None = None
    elimination_set_id: int | None = None
    bracket_group: str | None = None
    bracket_identifier: str | None = None
    source_phase: str | None = None
    phase_type: str | None = None
    pool_group: str | None = None
    pool_placement: int | None = None
    pool_number: int | None = None

    def __str__(self) -> str:
        name = self.team_name or "TBD"
        return f"#{self.placement} {name}"

    @property
    def is_placeholder(self) -> bool:
        """Check if this is an empty placeholder entry."""
        return self.team_name is None
