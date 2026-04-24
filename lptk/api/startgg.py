"""start.gg GraphQL API client.

This module provides a client class for interacting with the start.gg
GraphQL API to fetch tournament data.
"""

# Standard library
import logging
import time
from types import TracebackType
from typing import Any, Self, cast

# Third-party
import pycountry
import requests

# Local
from lptk.api._retry import retry_with_backoff
from lptk.config import get_settings, get_token
from lptk.exceptions import StartGGAPIError
from lptk.models.team import Player, Team
from lptk.models.tournament import Phase, PhaseGroup, SetDetails

logger = logging.getLogger("lptk.api.startgg")


def _country_iso2(country_str: str | None) -> str | None:
    """Convert a country name to ISO 3166-1 alpha-2 code (lowercase).

    Args:
        country_str: Full country name (e.g., "France", "United States").

    Returns:
        Lowercase ISO-2 code (e.g., "fr", "us") or None if not found.
    """
    if not country_str:
        return None

    # Try exact match first
    country = pycountry.countries.get(name=country_str)
    if country:
        return str(country.alpha_2).lower()

    # Try fuzzy search (search_fuzzy raises LookupError on miss, never returns empty)
    try:
        results = pycountry.countries.search_fuzzy(country_str)
        # pycountry types are incomplete, alpha_2 exists on Country objects
        return str(results[0].alpha_2).lower()  # type: ignore[attr-defined]
    except LookupError:
        logger.warning("Could not find ISO code for country: '%s'", country_str)
        return None


class StartGGClient:
    """Client for the start.gg GraphQL API.

    This client provides methods for fetching tournament data including
    event information, standings, phases, and match details.

    Attributes:
        api_url: The GraphQL API endpoint URL.
        rate_limit_delay: Delay between API calls in seconds.

    Example:
        >>> with StartGGClient() as client:
        ...     event_id, name = client.get_event_id("tournament/xyz/event/abc")
        ...     teams = client.get_event_standings(event_id, top_n=16)
    """

    def __init__(
            self,
            token: str | None = None,
            session: requests.Session | None = None,
    ) -> None:
        """Initialize the StartGG client.

        Args:
            token: API bearer token. If not provided, loaded from config.
            session: Optional requests session for connection pooling.

        Raises:
            ConfigurationError: If token is not provided and not found in config.
        """
        if token is None:
            token = get_token()

        self._token = token
        self._session = session or requests.Session()
        self._owns_session = session is None

        settings = get_settings()
        self.api_url = settings.startgg_api_url
        self.rate_limit_delay = settings.rate_limit_delay

        # Set up authorization header
        self._session.headers.update({"Authorization": f"Bearer {self._token}"})

    def __enter__(self) -> Self:
        """Enter context manager."""
        return self

    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: TracebackType | None,
    ) -> None:
        """Exit context manager and close session."""
        self.close()

    def close(self) -> None:
        """Close the HTTP session if we own it."""
        if self._owns_session:
            self._session.close()

    def _rate_limit(self) -> None:
        """Apply rate limiting delay."""
        if self.rate_limit_delay > 0:
            time.sleep(self.rate_limit_delay)

    @retry_with_backoff()
    def _post(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        """Execute a GraphQL query with retry logic.

        Args:
            query: GraphQL query string.
            variables: Query variables.

        Returns:
            JSON response data.

        Raises:
            StartGGAPIError: On HTTP or GraphQL errors.
        """
        response = self._session.post(
            self.api_url,
            json={"query": query, "variables": variables},
        )

        if not response.ok:
            raise StartGGAPIError(
                f"HTTP error: {response.text}",
                status_code=response.status_code,
                details={"url": self.api_url},
            )

        data: dict[str, Any] = response.json()

        if data.get("errors"):
            raise StartGGAPIError(
                "GraphQL error",
                details={"errors": data["errors"]},
            )

        return data

    def get_event_id(self, slug: str) -> tuple[int, str]:
        """Get event ID and name from a slug.

        Args:
            slug: Event URL slug (e.g., "tournament/xyz/event/abc").

        Returns:
            Tuple of (event_id, event_name).

        Raises:
            StartGGAPIError: If the event is not found or request fails.
        """
        query = """
            query getEventId($slug: String) {
                event(slug: $slug) {
                    id
                    name
                }
            }
        """

        data = self._post(query, {"slug": slug})
        self._rate_limit()

        event = (data.get("data") or {}).get("event")
        if not event:
            raise StartGGAPIError(
                f"Event not found: {slug}",
                details={"slug": slug},
            )

        return event["id"], event["name"]

    def get_event_standings(self, event_id: int, top_n: int) -> list[Team]:
        """Get event-level standings (final placements).

        Args:
            event_id: Internal start.gg event ID.
            top_n: Number of top teams to fetch.

        Returns:
            List of Team models with placement and roster data.
        """
        query = """
            query EventStandings($eventId: ID!, $perPage: Int!) {
                event(id: $eventId) {
                    standings(query: {page: 1, perPage: $perPage}) {
                        nodes {
                            placement
                            entrant {
                                id
                                name
                                participants {
                                    id
                                    gamerTag
                                    user {
                                        location {
                                            country
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """

        data = self._post(query, {"eventId": event_id, "perPage": top_n})
        self._rate_limit()

        nodes = (
            (data.get("data") or {})
            .get("event", {})
            .get("standings", {})
            .get("nodes", [])
        )

        teams = []
        for node in nodes:
            entrant = node.get("entrant") or {}
            members = self._parse_participants(entrant.get("participants") or [])

            teams.append(
                Team(
                    placement=node.get("placement", 0),
                    team_name=entrant.get("name"),
                    members=members,
                    entrant_id=entrant.get("id"),
                    source_phase="Event Standings",
                    phase_type="event",
                )
            )

        return teams

    def get_tournament_phases(self, event_id: int) -> list[Phase]:
        """Get all phases for an event with metadata.

        Args:
            event_id: Internal start.gg event ID.

        Returns:
            List of Phase models with phase groups.

        Raises:
            StartGGAPIError: If the event is not found or request fails.
        """
        query = """
            query EventPhases($eventId: ID!) {
                event(id: $eventId) {
                    id
                    phases {
                        id
                        name
                        state
                        numSeeds
                        phaseGroups {
                            nodes {
                                id
                                displayIdentifier
                                state
                                seeds(query: {page: 1, perPage: 1}) {
                                    pageInfo {
                                        total
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """

        data = self._post(query, {"eventId": event_id})
        self._rate_limit()

        event = (data.get("data") or {}).get("event")
        if not event:
            raise StartGGAPIError(
                f"Event not found: {event_id}",
                details={"event_id": event_id},
            )

        phases = []
        for phase_data in event.get("phases") or []:
            groups = []
            phase_groups = (phase_data.get("phaseGroups") or {}).get("nodes") or []

            for group in phase_groups:
                seeds_info = (group.get("seeds") or {}).get("pageInfo") or {}
                groups.append(
                    PhaseGroup(
                        id=group.get("id"),
                        identifier=group.get("displayIdentifier") or "",
                        state=group.get("state", 1),
                        num_seeds=seeds_info.get("total", 0),
                    )
                )

            phases.append(
                Phase(
                    id=phase_data.get("id"),
                    name=phase_data.get("name") or "",
                    state=phase_data.get("state", 1),
                    num_seeds=phase_data.get("numSeeds", 0),
                    groups=groups,
                )
            )

        return phases

    def get_phase_group_standings(self, phase_group_id: int) -> list[Team]:
        """Get standings from a specific phase group.

        Args:
            phase_group_id: Internal start.gg phase group ID.

        Returns:
            List of Team models with placement data.
        """
        all_standings: list[Team] = []
        page = 1
        per_page = 50

        query = """
            query PhaseGroupStandings($phaseGroupId: ID!, $page: Int!, $perPage: Int!) {
                phaseGroup(id: $phaseGroupId) {
                    id
                    standings(query: {page: $page, perPage: $perPage}) {
                        pageInfo {
                            total
                            totalPages
                        }
                        nodes {
                            placement
                            entrant {
                                id
                                name
                                participants {
                                    id
                                    gamerTag
                                    user {
                                        location {
                                            country
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """

        while True:
            data = self._post(
                query,
                {"phaseGroupId": phase_group_id, "page": page, "perPage": per_page},
            )
            self._rate_limit()

            phase_group = (data.get("data") or {}).get("phaseGroup")
            if not phase_group:
                break

            standings = phase_group.get("standings") or {}
            nodes = standings.get("nodes") or []

            if not nodes:
                break

            for node in nodes:
                entrant = node.get("entrant") or {}
                members = self._parse_participants(entrant.get("participants") or [])

                all_standings.append(
                    Team(
                        placement=node.get("placement", 0),
                        team_name=entrant.get("name"),
                        members=members,
                        entrant_id=entrant.get("id"),
                    )
                )

            page_info = standings.get("pageInfo") or {}
            if page >= page_info.get("totalPages", 1):
                break

            page += 1

        return all_standings

    def get_phase_group_seeds(self, phase_group_id: int) -> list[Team]:
        """Get seeds from a phase group (for upcoming phases).

        Args:
            phase_group_id: Internal start.gg phase group ID.

        Returns:
            List of Team models with seed number as placement.
        """
        all_seeds: list[Team] = []
        page = 1
        per_page = 50

        query = """
            query PhaseGroupSeeds($phaseGroupId: ID!, $page: Int!, $perPage: Int!) {
                phaseGroup(id: $phaseGroupId) {
                    id
                    seeds(query: {page: $page, perPage: $perPage}) {
                        pageInfo {
                            total
                            totalPages
                        }
                        nodes {
                            seedNum
                            entrant {
                                id
                                name
                                participants {
                                    id
                                    gamerTag
                                    user {
                                        location {
                                            country
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """

        while True:
            data = self._post(
                query,
                {"phaseGroupId": phase_group_id, "page": page, "perPage": per_page},
            )
            self._rate_limit()

            phase_group = (data.get("data") or {}).get("phaseGroup")
            if not phase_group:
                break

            seeds = phase_group.get("seeds") or {}
            nodes = seeds.get("nodes") or []

            if not nodes:
                break

            for node in nodes:
                entrant = node.get("entrant") or {}
                members = self._parse_participants(entrant.get("participants") or [])

                all_seeds.append(
                    Team(
                        placement=node.get("seedNum", 0),
                        team_name=entrant.get("name"),
                        members=members,
                        entrant_id=entrant.get("id"),
                    )
                )

            page_info = seeds.get("pageInfo") or {}
            if page >= page_info.get("totalPages", 1):
                break

            page += 1

        return all_seeds

    # noinspection PyUnnecessaryCast
    def get_set_details(self, set_id: int) -> SetDetails | None:
        """Get details of a specific match/set.

        Args:
            set_id: Internal start.gg set ID.

        Returns:
            SetDetails model or None if not found/incomplete.
        """
        query = """
            query SetDetails($setId: ID!) {
                set(id: $setId) {
                    id
                    identifier
                    slots {
                        entrant {
                            id
                            name
                        }
                        standing {
                            stats {
                                score {
                                    value
                                }
                            }
                        }
                    }
                    winnerId
                }
            }
        """

        try:
            data = self._post(query, {"setId": set_id})
            self._rate_limit()
        except StartGGAPIError:
            return None

        set_data = (data.get("data") or {}).get("set")
        if not set_data:
            return None

        slots = set_data.get("slots") or []
        if len(slots) != 2:
            return None

        winner_id = set_data.get("winnerId")
        if not winner_id:
            return None

        slot1, slot2 = slots[0], slots[1]

        entrant1 = slot1.get("entrant") or {}
        entrant2 = slot2.get("entrant") or {}

        id1 = entrant1.get("id")
        id2 = entrant2.get("id")
        name1 = entrant1.get("name")
        name2 = entrant2.get("name")

        if not all([id1, id2, name1, name2]):
            return None

        # Cast to str since we verified they're truthy above
        name1_str = cast(str, name1)
        name2_str = cast(str, name2)

        # Extract scores
        score1 = (
                ((slot1.get("standing") or {}).get("stats") or {}).get("score") or {}
        ).get("value")
        score2 = (
                ((slot2.get("standing") or {}).get("stats") or {}).get("score") or {}
        ).get("value")

        # Determine winner and loser
        if id1 == winner_id:
            winner_name, loser_name = name1_str, name2_str
            winner_score, loser_score = score1, score2
        elif id2 == winner_id:
            winner_name, loser_name = name2_str, name1_str
            winner_score, loser_score = score2, score1
        else:
            return None

        return SetDetails(
            set_id=set_id,
            identifier=set_data.get("identifier") or "",
            winner_id=winner_id,
            winner_name=winner_name,
            loser_name=loser_name,
            winner_score=winner_score,
            loser_score=loser_score,
        )

    def get_entrant_last_elimination_set_id(
            self, event_id: int, entrant_id: int
    ) -> int | None:
        """Get the ID of the set that eliminated an entrant.

        Args:
            event_id: Internal start.gg event ID.
            entrant_id: Internal start.gg entrant ID.

        Returns:
            Set ID of elimination match, or None if not eliminated/found.
        """
        query = """
            query EntrantLastSet($eventId: ID!, $entrantId: ID!) {
                event(id: $eventId) {
                    id
                    sets(
                        page: 1
                        perPage: 1
                        sortType: RECENT
                        filters: { entrantIds: [$entrantId], state: 3 }
                    ) {
                        nodes {
                            id
                            winnerId
                        }
                    }
                }
            }
        """

        try:
            data = self._post(query, {"eventId": event_id, "entrantId": entrant_id})
            self._rate_limit()
        except StartGGAPIError:
            return None

        event = (data.get("data") or {}).get("event") or {}
        nodes = (event.get("sets") or {}).get("nodes") or []

        if not nodes:
            return None

        last_set = nodes[0]
        set_id = last_set.get("id")
        winner_id = last_set.get("winnerId")

        # If the entrant lost their most recent completed set, that's the elimination
        if set_id and winner_id and winner_id != entrant_id:
            return int(set_id)

        return None

    def has_incomplete_sets(self, event_id: int, entrant_id: int) -> bool:
        """Check if an entrant has any incomplete sets (still playing).

        Args:
            event_id: Internal start.gg event ID.
            entrant_id: Internal start.gg entrant ID.

        Returns:
            True if the entrant has incomplete sets, False otherwise.
        """
        query = """
            query EntrantIncompleteSets($eventId: ID!, $entrantId: ID!) {
                event(id: $eventId) {
                    id
                    sets(
                        page: 1
                        perPage: 1
                        filters: {
                            entrantIds: [$entrantId]
                            state: [1, 2]
                        }
                    ) {
                        pageInfo {
                            total
                        }
                    }
                }
            }
        """

        try:
            data = self._post(query, {"eventId": event_id, "entrantId": entrant_id})
            self._rate_limit()
        except StartGGAPIError:
            return False

        event = (data.get("data") or {}).get("event") or {}
        sets = event.get("sets") or {}
        page_info = sets.get("pageInfo") or {}
        total: int = page_info.get("total", 0)

        return total > 0

    @staticmethod
    def _parse_participants(
            participants: list[dict[str, Any]]
    ) -> list[Player]:
        """Parse participant data into Player models.

        Args:
            participants: Raw participant data from API.

        Returns:
            List of Player models.
        """
        players = []
        for p in participants:
            country = (
                ((p.get("user") or {}).get("location") or {}).get("country")
            )
            players.append(
                Player(
                    player_id=p.get("id"),
                    player_tag=p.get("gamerTag") or "",
                    player_country=_country_iso2(country),
                )
            )
        return players
