"""Tests for lptk.models module."""

import pytest
from pydantic import ValidationError

from lptk.models import Phase, PhaseGroup, Player, SetDetails, SetSlot, Team


class TestPlayer:
    """Tests for the Player model."""

    def test_player_defaults(self) -> None:
        """Test Player with default values."""
        player = Player()
        assert player.player_id is None
        assert player.player_tag == ""
        assert player.player_country is None

    def test_player_with_values(self) -> None:
        """Test Player with all values set."""
        player = Player(
            player_id=12345,
            player_tag="TestPlayer",
            player_country="us",
        )
        assert player.player_id == 12345
        assert player.player_tag == "TestPlayer"
        assert player.player_country == "us"

    def test_player_str_with_country(self) -> None:
        """Test Player string representation with country."""
        player = Player(player_tag="TestPlayer", player_country="fr")
        assert str(player) == "TestPlayer (fr)"

    def test_player_str_without_country(self) -> None:
        """Test Player string representation without country."""
        player = Player(player_tag="TestPlayer")
        assert str(player) == "TestPlayer"


class TestTeam:
    """Tests for the Team model."""

    def test_team_minimal(self) -> None:
        """Test Team with minimal required values."""
        team = Team(placement=1)
        assert team.placement == 1
        assert team.team_name is None
        assert team.members == []
        assert team.is_placeholder is True

    def test_team_with_roster(self) -> None:
        """Test Team with full roster."""
        players = [
            Player(player_id=1, player_tag="P1", player_country="us"),
            Player(player_id=2, player_tag="P2", player_country="fr"),
            Player(player_id=3, player_tag="P3", player_country="de"),
        ]
        team = Team(
            placement=1,
            team_name="Test Team",
            members=players,
            entrant_id=999,
        )
        assert team.placement == 1
        assert team.team_name == "Test Team"
        assert len(team.members) == 3
        assert team.entrant_id == 999
        assert team.is_placeholder is False

    def test_team_str(self) -> None:
        """Test Team string representation."""
        team = Team(placement=5, team_name="Winners")
        assert str(team) == "#5 Winners"

    def test_team_str_placeholder(self) -> None:
        """Test Team string representation for placeholder."""
        team = Team(placement=10)
        assert str(team) == "#10 TBD"

    def test_team_placement_validation(self) -> None:
        """Test that placement must be >= 1."""
        with pytest.raises(ValidationError):
            Team(placement=0)

        with pytest.raises(ValidationError):
            Team(placement=-1)

    def test_team_bracket_fields(self) -> None:
        """Test Team bracket-related fields."""
        team = Team(
            placement=8,
            team_name="Bracket Team",
            bracket_group="B1",
            bracket_identifier="AL",
            elimination_set_id=12345,
        )
        assert team.bracket_group == "B1"
        assert team.bracket_identifier == "AL"
        assert team.elimination_set_id == 12345

    def test_team_pool_fields(self) -> None:
        """Test Team pool-related fields."""
        team = Team(
            placement=16,
            team_name="Pool Team",
            pool_group="Pool A",
            pool_placement=2,
            pool_number=1,
        )
        assert team.pool_group == "Pool A"
        assert team.pool_placement == 2
        assert team.pool_number == 1


class TestPhaseGroup:
    """Tests for the PhaseGroup model."""

    def test_phase_group_defaults(self) -> None:
        """Test PhaseGroup with default values."""
        group = PhaseGroup(id=123)
        assert group.id == 123
        assert group.identifier == ""
        assert group.state == 1
        assert group.num_seeds == 0

    def test_phase_group_completed(self) -> None:
        """Test PhaseGroup completion status."""
        group = PhaseGroup(id=1, state=3)
        assert group.is_completed is True
        assert group.is_active is False

        group_str = PhaseGroup(id=1, state="COMPLETED")
        assert group_str.is_completed is True

    def test_phase_group_active(self) -> None:
        """Test PhaseGroup active status."""
        group = PhaseGroup(id=1, state=2)
        assert group.is_active is True
        assert group.is_completed is False

        group_str = PhaseGroup(id=1, state="ACTIVE")
        assert group_str.is_active is True


class TestPhase:
    """Tests for the Phase model."""

    def test_phase_minimal(self) -> None:
        """Test Phase with minimal values."""
        phase = Phase(id=1, name="Day 1")
        assert phase.id == 1
        assert phase.name == "Day 1"
        assert phase.state == 1
        assert phase.num_seeds == 0
        assert phase.groups == []

    def test_phase_with_groups(self) -> None:
        """Test Phase with phase groups."""
        groups = [
            PhaseGroup(id=1, identifier="B1", state=3, num_seeds=16),
            PhaseGroup(id=2, identifier="B2", state=3, num_seeds=16),
        ]
        phase = Phase(
            id=100,
            name="Playoffs",
            state=3,
            num_seeds=32,
            groups=groups,
        )
        assert len(phase.groups) == 2
        assert phase.groups[0].identifier == "B1"

    def test_phase_status(self) -> None:
        """Test Phase status properties."""
        created = Phase(id=1, name="Created", state=1)
        assert created.is_completed is False
        assert created.is_active is False

        active = Phase(id=2, name="Active", state=2)
        assert active.is_active is True
        assert active.is_completed is False

        completed = Phase(id=3, name="Completed", state=3)
        assert completed.is_completed is True
        assert completed.is_active is False


class TestSetSlot:
    """Tests for the SetSlot model."""

    def test_set_slot_defaults(self) -> None:
        """Test SetSlot with default values."""
        slot = SetSlot()
        assert slot.entrant_id is None
        assert slot.entrant_name is None
        assert slot.score is None

    def test_set_slot_with_values(self) -> None:
        """Test SetSlot with values."""
        slot = SetSlot(
            entrant_id=123,
            entrant_name="Team A",
            score=3,
        )
        assert slot.entrant_id == 123
        assert slot.entrant_name == "Team A"
        assert slot.score == 3


class TestSetDetails:
    """Tests for the SetDetails model."""

    def test_set_details_minimal(self) -> None:
        """Test SetDetails with minimal values."""
        details = SetDetails(set_id=12345)
        assert details.set_id == 12345
        assert details.identifier == ""
        assert details.winner_name == ""
        assert details.loser_name == ""

    def test_set_details_full(self) -> None:
        """Test SetDetails with all values."""
        details = SetDetails(
            set_id=12345,
            identifier="B1 AL",
            winner_id=100,
            winner_name="Winner Team",
            loser_name="Loser Team",
            winner_score=3,
            loser_score=1,
        )
        assert details.set_id == 12345
        assert details.identifier == "B1 AL"
        assert details.winner_id == 100
        assert details.winner_name == "Winner Team"
        assert details.loser_name == "Loser Team"
        assert details.winner_score == 3
        assert details.loser_score == 1

    def test_bracket_group_extraction(self) -> None:
        """Test extracting bracket group from identifier."""
        # With group prefix
        details = SetDetails(set_id=1, identifier="B1 AL")
        assert details.bracket_group == "B1"
        assert details.match_id == "AL"

        # Without group prefix
        details_simple = SetDetails(set_id=2, identifier="AM")
        assert details_simple.bracket_group is None
        assert details_simple.match_id == "AM"

    def test_format_score_normal(self) -> None:
        """Test normal score formatting."""
        details = SetDetails(
            set_id=1,
            winner_score=3,
            loser_score=2,
        )
        assert details.format_score() == "3-2"

    def test_format_score_forfeit_loser(self) -> None:
        """Test forfeit score formatting (loser forfeit)."""
        details = SetDetails(
            set_id=1,
            winner_score=3,
            loser_score=-1,
        )
        assert details.format_score() == "W-FF"

    def test_format_score_forfeit_winner(self) -> None:
        """Test forfeit score formatting (winner forfeit notation)."""
        details = SetDetails(
            set_id=1,
            winner_score=-1,
            loser_score=0,
        )
        assert details.format_score() == "FF-W"

    def test_format_score_empty(self) -> None:
        """Test empty score formatting."""
        details = SetDetails(set_id=1)
        assert details.format_score() == ""
