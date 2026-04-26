"""Tests for lptk.api.startgg module."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from lptk.api.startgg import StartGGClient, _country_iso2
from lptk.exceptions import StartGGAPIError
from lptk.models import Phase, PhaseGroup, SetDetails, Team


class TestCountryIso2:
    """Tests for the _country_iso2 helper function."""

    @staticmethod
    def test_exact_match() -> None:
        """Test exact country name match."""
        assert _country_iso2("France") == "fr"
        assert _country_iso2("Germany") == "de"
        assert _country_iso2("United States") == "us"

    @staticmethod
    def test_fuzzy_match() -> None:
        """Test fuzzy country name matching."""
        assert _country_iso2("USA") == "us"
        # Note: pycountry requires "Brazil", not "Brasil"
        assert _country_iso2("Brazil") == "br"

    @staticmethod
    def test_none_input() -> None:
        """Test None input returns None."""
        assert _country_iso2(None) is None

    @staticmethod
    def test_empty_string() -> None:
        """Test empty string returns None."""
        assert _country_iso2("") is None

    @staticmethod
    def test_unknown_country() -> None:
        """Test unknown country returns None."""
        assert _country_iso2("Not A Country") is None


class TestStartGGClient:
    """Tests for the StartGGClient class."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create a mock requests session."""
        session = MagicMock(spec=requests.Session)
        session.headers = {}
        return session

    @pytest.fixture
    def client(self, mock_session: MagicMock) -> StartGGClient:
        """Create a StartGGClient with mocked session."""
        with (
            patch("lptk.api.startgg.get_token", return_value="test-token"),
            patch("lptk.api.startgg.get_settings") as mock_settings,
        ):
            mock_settings.return_value.startgg_api_url = "https://api.test.gg/gql"
            mock_settings.return_value.rate_limit_delay = 0  # Disable for tests
            return StartGGClient(session=mock_session)

    @staticmethod
    def test_init_with_token(mock_session: MagicMock) -> None:
        """Test client initialization with explicit token."""
        with patch("lptk.api.startgg.get_settings") as mock_settings:
            mock_settings.return_value.startgg_api_url = "https://api.test.gg/gql"
            mock_settings.return_value.rate_limit_delay = 0
            StartGGClient(token="explicit-token", session=mock_session)
            assert "Authorization" in mock_session.headers

    @staticmethod
    def test_context_manager(mock_session: MagicMock) -> None:
        """Test client works as context manager."""
        with (
            patch("lptk.api.startgg.get_token", return_value="test-token"),
            patch("lptk.api.startgg.get_settings") as mock_settings,
        ):
            mock_settings.return_value.startgg_api_url = "https://api.test.gg/gql"
            mock_settings.return_value.rate_limit_delay = 0
            with StartGGClient(session=mock_session) as client:
                assert client is not None

    @staticmethod
    def test_get_event_id_success(client: StartGGClient, mock_session: MagicMock) -> None:
        """Test successful event ID retrieval."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "event": {
                    "id": 12345,
                    "name": "Test Tournament",
                }
            }
        }
        mock_session.post.return_value = mock_response

        event_id, event_name = client.get_event_id("tournament/test/event/main")

        assert event_id == 12345
        assert event_name == "Test Tournament"

    @staticmethod
    def test_get_event_id_not_found(client: StartGGClient, mock_session: MagicMock) -> None:
        """Test event not found raises error."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"event": None}}
        mock_session.post.return_value = mock_response

        with pytest.raises(StartGGAPIError) as exc_info:
            client.get_event_id("tournament/nonexistent/event/main")

        assert "Event not found" in str(exc_info.value)

    @staticmethod
    def test_get_event_id_http_error(client: StartGGClient, mock_session: MagicMock) -> None:
        """Test HTTP error handling."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_session.post.return_value = mock_response

        with pytest.raises(StartGGAPIError) as exc_info:
            client.get_event_id("tournament/test/event/main")

        assert exc_info.value.status_code == 500

    @staticmethod
    def test_get_event_id_graphql_error(client: StartGGClient, mock_session: MagicMock) -> None:
        """Test GraphQL error handling."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"errors": [{"message": "Invalid query"}]}
        mock_session.post.return_value = mock_response

        with pytest.raises(StartGGAPIError) as exc_info:
            client.get_event_id("tournament/test/event/main")

        assert "GraphQL error" in str(exc_info.value)

    @staticmethod
    def test_get_event_standings(client: StartGGClient, mock_session: MagicMock) -> None:
        """Test event standings retrieval."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "event": {
                    "standings": {
                        "nodes": [
                            {
                                "placement": 1,
                                "entrant": {
                                    "id": 100,
                                    "name": "Team Winner",
                                    "participants": [
                                        {
                                            "id": 1,
                                            "gamerTag": "Player1",
                                            "user": {"location": {"country": "France"}},
                                        }
                                    ],
                                },
                            },
                            {
                                "placement": 2,
                                "entrant": {
                                    "id": 101,
                                    "name": "Team Runner-up",
                                    "participants": [],
                                },
                            },
                        ]
                    }
                }
            }
        }
        mock_session.post.return_value = mock_response

        teams = client.get_event_standings(12345, top_n=2)

        assert len(teams) == 2
        assert isinstance(teams[0], Team)
        assert teams[0].placement == 1
        assert teams[0].team_name == "Team Winner"
        assert teams[0].entrant_id == 100
        assert len(teams[0].members) == 1
        assert teams[0].members[0].player_tag == "Player1"
        assert teams[0].members[0].player_country == "fr"

    @staticmethod
    def test_get_tournament_phases(client: StartGGClient, mock_session: MagicMock) -> None:
        """Test tournament phases retrieval."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "event": {
                    "phases": [
                        {
                            "id": 1,
                            "name": "Day 1",
                            "state": 3,
                            "numSeeds": 64,
                            "phaseGroups": {
                                "nodes": [
                                    {
                                        "id": 10,
                                        "displayIdentifier": "B1",
                                        "state": 3,
                                        "seeds": {"pageInfo": {"total": 32}},
                                    },
                                    {
                                        "id": 11,
                                        "displayIdentifier": "B2",
                                        "state": 3,
                                        "seeds": {"pageInfo": {"total": 32}},
                                    },
                                ]
                            },
                        }
                    ]
                }
            }
        }
        mock_session.post.return_value = mock_response

        phases = client.get_tournament_phases(12345)

        assert len(phases) == 1
        assert isinstance(phases[0], Phase)
        assert phases[0].name == "Day 1"
        assert phases[0].num_seeds == 64
        assert len(phases[0].groups) == 2
        assert isinstance(phases[0].groups[0], PhaseGroup)
        assert phases[0].groups[0].identifier == "B1"

    @staticmethod
    def test_get_phase_group_standings(client: StartGGClient, mock_session: MagicMock) -> None:
        """Test phase group standings retrieval."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "phaseGroup": {
                    "id": 10,
                    "standings": {
                        "pageInfo": {"total": 2, "totalPages": 1},
                        "nodes": [
                            {
                                "placement": 1,
                                "entrant": {
                                    "id": 100,
                                    "name": "Team A",
                                    "participants": [],
                                },
                            }
                        ],
                    },
                }
            }
        }
        mock_session.post.return_value = mock_response

        teams = client.get_phase_group_standings(10)

        assert len(teams) == 1
        assert teams[0].placement == 1
        assert teams[0].team_name == "Team A"

    @staticmethod
    def test_get_phase_group_seeds(client: StartGGClient, mock_session: MagicMock) -> None:
        """Test phase group seeds retrieval."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "phaseGroup": {
                    "id": 10,
                    "seeds": {
                        "pageInfo": {"total": 2, "totalPages": 1},
                        "nodes": [
                            {
                                "seedNum": 1,
                                "entrant": {
                                    "id": 100,
                                    "name": "Top Seed",
                                    "participants": [],
                                },
                            }
                        ],
                    },
                }
            }
        }
        mock_session.post.return_value = mock_response

        teams = client.get_phase_group_seeds(10)

        assert len(teams) == 1
        assert teams[0].placement == 1  # seedNum becomes placement
        assert teams[0].team_name == "Top Seed"

    @staticmethod
    def test_get_set_details_success(client: StartGGClient, mock_session: MagicMock) -> None:
        """Test set details retrieval."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "set": {
                    "id": 999,
                    "identifier": "B1 AL",
                    "winnerId": 100,
                    "slots": [
                        {
                            "entrant": {"id": 100, "name": "Winner Team"},
                            "standing": {"stats": {"score": {"value": 3}}},
                        },
                        {
                            "entrant": {"id": 101, "name": "Loser Team"},
                            "standing": {"stats": {"score": {"value": 1}}},
                        },
                    ],
                }
            }
        }
        mock_session.post.return_value = mock_response

        details = client.get_set_details(999)

        assert details is not None
        assert isinstance(details, SetDetails)
        assert details.set_id == 999
        assert details.identifier == "B1 AL"
        assert details.winner_name == "Winner Team"
        assert details.loser_name == "Loser Team"
        assert details.winner_score == 3
        assert details.loser_score == 1

    @staticmethod
    def test_get_set_details_not_found(client: StartGGClient, mock_session: MagicMock) -> None:
        """Test set details when set not found."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"set": None}}
        mock_session.post.return_value = mock_response

        details = client.get_set_details(999)
        assert details is None

    @staticmethod
    def test_get_set_details_incomplete(client: StartGGClient, mock_session: MagicMock) -> None:
        """Test set details for incomplete set."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "set": {
                    "id": 999,
                    "identifier": "AL",
                    "winnerId": None,  # No winner yet
                    "slots": [],
                }
            }
        }
        mock_session.post.return_value = mock_response

        details = client.get_set_details(999)
        assert details is None

    @staticmethod
    def test_get_entrant_last_elimination_set_id(client: StartGGClient, mock_session: MagicMock) -> None:
        """Test elimination set ID retrieval."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "event": {
                    "id": 12345,
                    "sets": {
                        "nodes": [
                            {"id": 999, "winnerId": 200}  # 200 won, so 100 was eliminated
                        ]
                    },
                }
            }
        }
        mock_session.post.return_value = mock_response

        set_id = client.get_entrant_last_elimination_set_id(12345, 100)
        assert set_id == 999

    @staticmethod
    def test_get_entrant_last_elimination_set_id_winner(client: StartGGClient, mock_session: MagicMock) -> None:
        """Test elimination set ID for tournament winner (no elimination)."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "event": {
                    "id": 12345,
                    "sets": {
                        "nodes": [
                            {"id": 999, "winnerId": 100}  # 100 won their last match
                        ]
                    },
                }
            }
        }
        mock_session.post.return_value = mock_response

        set_id = client.get_entrant_last_elimination_set_id(12345, 100)
        assert set_id is None

    @staticmethod
    def test_has_incomplete_sets_true(client: StartGGClient, mock_session: MagicMock) -> None:
        """Test has_incomplete_sets returns True when sets pending."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "event": {
                    "id": 12345,
                    "sets": {"pageInfo": {"total": 1}},
                }
            }
        }
        mock_session.post.return_value = mock_response

        result = client.has_incomplete_sets(12345, 100)
        assert result is True

    @staticmethod
    def test_has_incomplete_sets_false(client: StartGGClient, mock_session: MagicMock) -> None:
        """Test has_incomplete_sets returns False when no pending sets."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "event": {
                    "id": 12345,
                    "sets": {"pageInfo": {"total": 0}},
                }
            }
        }
        mock_session.post.return_value = mock_response

        result = client.has_incomplete_sets(12345, 100)
        assert result is False

    @staticmethod
    def test_close_session(mock_session: MagicMock) -> None:
        """Test session is closed properly."""
        with (
            patch("lptk.api.startgg.get_token", return_value="test-token"),
            patch("lptk.api.startgg.get_settings") as mock_settings,
        ):
            mock_settings.return_value.startgg_api_url = "https://api.test.gg/gql"
            mock_settings.return_value.rate_limit_delay = 0
            # Create client without passing session so it owns it
            client = StartGGClient(token="test")
            client._session = mock_session
            client._owns_session = True
            client.close()
            mock_session.close.assert_called_once()

    @patch("lptk.api.startgg.time.sleep")
    def test_rate_limit_sleeps_when_delay_positive(self, mock_sleep: MagicMock, mock_session: MagicMock) -> None:
        """Rate limit delay > 0 triggers time.sleep."""
        with (
            patch("lptk.api.startgg.get_token", return_value="test-token"),
            patch("lptk.api.startgg.get_settings") as mock_settings,
        ):
            mock_settings.return_value.startgg_api_url = "https://api.test.gg/gql"
            mock_settings.return_value.rate_limit_delay = 0.25
            client = StartGGClient(session=mock_session)
            client._rate_limit()
            mock_sleep.assert_called_once_with(0.25)

    @staticmethod
    def test_get_tournament_phases_event_not_found(client: StartGGClient, mock_session: MagicMock) -> None:
        """get_tournament_phases raises when event is missing."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"event": None}}
        mock_session.post.return_value = mock_response

        with pytest.raises(StartGGAPIError) as exc_info:
            client.get_tournament_phases(12345)

        assert "Event not found" in str(exc_info.value)

    @staticmethod
    def test_get_phase_group_standings_empty_phase_group(client: StartGGClient, mock_session: MagicMock) -> None:
        """get_phase_group_standings breaks when phaseGroup is None."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"phaseGroup": None}}
        mock_session.post.return_value = mock_response

        teams = client.get_phase_group_standings(10)
        assert teams == []

    @staticmethod
    def test_get_phase_group_standings_empty_nodes(client: StartGGClient, mock_session: MagicMock) -> None:
        """get_phase_group_standings breaks when nodes list is empty."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "phaseGroup": {
                    "id": 10,
                    "standings": {
                        "pageInfo": {"total": 0, "totalPages": 1},
                        "nodes": [],
                    },
                }
            }
        }
        mock_session.post.return_value = mock_response

        teams = client.get_phase_group_standings(10)
        assert teams == []

    @staticmethod
    def test_get_phase_group_standings_multi_page(client: StartGGClient, mock_session: MagicMock) -> None:
        """get_phase_group_standings paginates across multiple pages."""
        page1 = MagicMock()
        page1.ok = True
        page1.json.return_value = {
            "data": {
                "phaseGroup": {
                    "id": 10,
                    "standings": {
                        "pageInfo": {"total": 2, "totalPages": 2},
                        "nodes": [
                            {
                                "placement": 1,
                                "entrant": {
                                    "id": 100,
                                    "name": "Team A",
                                    "participants": [],
                                },
                            }
                        ],
                    },
                }
            }
        }
        page2 = MagicMock()
        page2.ok = True
        page2.json.return_value = {
            "data": {
                "phaseGroup": {
                    "id": 10,
                    "standings": {
                        "pageInfo": {"total": 2, "totalPages": 2},
                        "nodes": [
                            {
                                "placement": 2,
                                "entrant": {
                                    "id": 101,
                                    "name": "Team B",
                                    "participants": [],
                                },
                            }
                        ],
                    },
                }
            }
        }
        mock_session.post.side_effect = [page1, page2]

        teams = client.get_phase_group_standings(10)
        assert [t.team_name for t in teams] == ["Team A", "Team B"]

    @staticmethod
    def test_get_phase_group_seeds_empty_phase_group(client: StartGGClient, mock_session: MagicMock) -> None:
        """get_phase_group_seeds breaks when phaseGroup is None."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"phaseGroup": None}}
        mock_session.post.return_value = mock_response

        seeds = client.get_phase_group_seeds(10)
        assert seeds == []

    @staticmethod
    def test_get_phase_group_seeds_empty_nodes(client: StartGGClient, mock_session: MagicMock) -> None:
        """get_phase_group_seeds breaks when nodes list is empty."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "phaseGroup": {
                    "id": 10,
                    "seeds": {
                        "pageInfo": {"total": 0, "totalPages": 1},
                        "nodes": [],
                    },
                }
            }
        }
        mock_session.post.return_value = mock_response

        seeds = client.get_phase_group_seeds(10)
        assert seeds == []

    @staticmethod
    def test_get_phase_group_seeds_multi_page(client: StartGGClient, mock_session: MagicMock) -> None:
        """get_phase_group_seeds paginates across multiple pages."""
        page1 = MagicMock()
        page1.ok = True
        page1.json.return_value = {
            "data": {
                "phaseGroup": {
                    "id": 10,
                    "seeds": {
                        "pageInfo": {"total": 2, "totalPages": 2},
                        "nodes": [
                            {
                                "seedNum": 1,
                                "entrant": {
                                    "id": 100,
                                    "name": "Seed 1",
                                    "participants": [],
                                },
                            }
                        ],
                    },
                }
            }
        }
        page2 = MagicMock()
        page2.ok = True
        page2.json.return_value = {
            "data": {
                "phaseGroup": {
                    "id": 10,
                    "seeds": {
                        "pageInfo": {"total": 2, "totalPages": 2},
                        "nodes": [
                            {
                                "seedNum": 2,
                                "entrant": {
                                    "id": 101,
                                    "name": "Seed 2",
                                    "participants": [],
                                },
                            }
                        ],
                    },
                }
            }
        }
        mock_session.post.side_effect = [page1, page2]

        seeds = client.get_phase_group_seeds(10)
        assert [s.team_name for s in seeds] == ["Seed 1", "Seed 2"]

    @staticmethod
    def test_get_set_details_swallows_api_error(client: StartGGClient, mock_session: MagicMock) -> None:
        """get_set_details returns None on StartGGAPIError."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_session.post.return_value = mock_response

        details = client.get_set_details(999)
        assert details is None

    @staticmethod
    def test_get_set_details_missing_winner_id(client: StartGGClient, mock_session: MagicMock) -> None:
        """get_set_details returns None when winnerId is absent on a 2-slot set."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "set": {
                    "id": 999,
                    "identifier": "AL",
                    "winnerId": None,
                    "slots": [
                        {"entrant": {"id": 1, "name": "A"}, "standing": None},
                        {"entrant": {"id": 2, "name": "B"}, "standing": None},
                    ],
                }
            }
        }
        mock_session.post.return_value = mock_response

        details = client.get_set_details(999)
        assert details is None

    @staticmethod
    def test_get_set_details_falsy_entrant_fields(client: StartGGClient, mock_session: MagicMock) -> None:
        """get_set_details returns None when an entrant's name or id is missing."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "set": {
                    "id": 999,
                    "identifier": "AL",
                    "winnerId": 100,
                    "slots": [
                        {"entrant": {"id": 100, "name": "Winner"}, "standing": None},
                        {"entrant": {"id": None, "name": None}, "standing": None},
                    ],
                }
            }
        }
        mock_session.post.return_value = mock_response

        details = client.get_set_details(999)
        assert details is None

    @staticmethod
    def test_get_set_details_slot2_wins(client: StartGGClient, mock_session: MagicMock) -> None:
        """get_set_details correctly swaps when slot2 holds the winner."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "set": {
                    "id": 999,
                    "identifier": "B2 AM",
                    "winnerId": 200,
                    "slots": [
                        {
                            "entrant": {"id": 100, "name": "Loser Team"},
                            "standing": {"stats": {"score": {"value": 1}}},
                        },
                        {
                            "entrant": {"id": 200, "name": "Winner Team"},
                            "standing": {"stats": {"score": {"value": 3}}},
                        },
                    ],
                }
            }
        }
        mock_session.post.return_value = mock_response

        details = client.get_set_details(999)
        assert details is not None
        assert details.winner_name == "Winner Team"
        assert details.loser_name == "Loser Team"
        assert details.winner_score == 3
        assert details.loser_score == 1

    @staticmethod
    def test_get_set_details_winner_id_matches_neither_slot(client: StartGGClient, mock_session: MagicMock) -> None:
        """get_set_details returns None when winnerId matches no slot entrant."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "data": {
                "set": {
                    "id": 999,
                    "identifier": "AL",
                    "winnerId": 999999,  # Matches neither 100 nor 200
                    "slots": [
                        {"entrant": {"id": 100, "name": "A"}, "standing": None},
                        {"entrant": {"id": 200, "name": "B"}, "standing": None},
                    ],
                }
            }
        }
        mock_session.post.return_value = mock_response

        details = client.get_set_details(999)
        assert details is None

    @staticmethod
    def test_get_entrant_last_elimination_set_id_swallows_api_error(
        client: StartGGClient, mock_session: MagicMock
    ) -> None:
        """get_entrant_last_elimination_set_id returns None on StartGGAPIError."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "server error"
        mock_session.post.return_value = mock_response

        result = client.get_entrant_last_elimination_set_id(12345, 100)
        assert result is None

    @staticmethod
    def test_get_entrant_last_elimination_set_id_empty_nodes(client: StartGGClient, mock_session: MagicMock) -> None:
        """get_entrant_last_elimination_set_id returns None when no sets found."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {"data": {"event": {"id": 12345, "sets": {"nodes": []}}}}
        mock_session.post.return_value = mock_response

        result = client.get_entrant_last_elimination_set_id(12345, 100)
        assert result is None

    @staticmethod
    def test_has_incomplete_sets_swallows_api_error(client: StartGGClient, mock_session: MagicMock) -> None:
        """has_incomplete_sets returns False on StartGGAPIError."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "server error"
        mock_session.post.return_value = mock_response

        result = client.has_incomplete_sets(12345, 100)
        assert result is False
