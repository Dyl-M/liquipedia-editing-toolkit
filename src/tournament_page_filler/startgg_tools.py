# -*- coding: utf-8 -*-

import os
import pycountry
import requests

"""File Information
@file_name: startgg_tools.py
@author: Dylan "dyl-m" Monfret
Collection of "start.gg tools" and useful functions

This module provides small utilities to interact with the start.gg GraphQL API:
- Resolve an event id from a public event slug
- Retrieve top-N standings (teams + players) for an event
- Normalize player country information to ISO 3166-1 alpha-2 format

Notes:
- This code assumes the presence of an API token on disk and will read it once at import time.
- Network calls are synchronous and may raise Exceptions on HTTP or GraphQL errors.
- The functions aim to return simple Python data structures for downstream processing.
"""

'GLOBAL VARIABLES'

API_URL = 'https://api.start.gg/gql/alpha'  # API URL

# Read the token from a local file and set up the Authorization header used by all GraphQL requests.
# Important:
# - The token file path is relative to this script's location (../../_token/start.gg-token.txt from this file).
# - Make sure the token file exists and contains a valid start.gg API token.
# - The token is read at import time; if it changes on disk, you must reload the module to use the new value.

_TOKEN_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '_token', 'start.gg-token.txt')
with open(_TOKEN_PATH, 'r', encoding='utf8') as token_file:
    QUERIES_HEADER = {"Authorization": f"Bearer {token_file.read()}"}


def country_iso2(country_str: str):
    """Convert a country name to the ISO 3166-1 alpha-2 code.

    This helper normalizes various country name inputs to a standardized ISO-2 code using the `pycountry` database.
    It will try a strict lookup first, then fall back to a fuzzy search which returns the best guess.

    Parameters
    ----------
    country_str : str
        The full country name (e.g., "France", "United States", "Brasil").

    Returns
    -------
    str | None
        The two-letter ISO 3166-1 alpha-2 code (e.g., "FR", "US", "BR"), or None if
        the input is falsy (empty string, None).

    Raises
    ------
    LookupError
        If a fuzzy search is attempted and no suitable match is found.
    Exception
        Any unexpected errors emitted by `pycountry` internals.

    Implementation notes
    --------------------
    - `pycountry.countries.get(name=...)` performs an exact match on the name.
    - If the exact match fails, `pycountry.countries.search_fuzzy(...)` is used, which may raise a LookupError if no
    candidates are found.
    """
    if not country_str:
        return None

    # Try the exact match first; if not available, attempt a fuzzy lookup to best-effort match
    country = pycountry.countries.get(name=country_str)

    if country:
        return country.alpha_2
    else:
        return pycountry.countries.search_fuzzy(country_str)[0].alpha_2


def get_event_id(comp_slug: str) -> tuple:
    """Return identifiers for a competition on start.gg.

    Given a public event slug, this function queries the start.gg GraphQL API to retrieve the event's internal ID and
    its display name.

    Parameters
    ----------
    comp_slug : str
        The URL slug of the event (e.g., "tournament/xyz/event/abc").

    Returns
    -------
    tuple
        A tuple (event_id, event_name).

    Raises
    ------
    Exception
        - If the HTTP request fails (non-2xx response).
        - If the GraphQL payload contains errors.
        - If the event is not found or the response payload is unexpectedly shaped.

    Example
    -------
    >>> get_event_id("tournament/my-tourney/event/rocket-league")
    (123456, "Rocket League")
    """
    r_body = {
        "query": """
            query getEventId($slug: String) {
                event(slug: $slug) {
                    id
                    name
                }
            }
        """,
        "variables": {
            "slug": comp_slug
        }
    }
    response = requests.post(url=API_URL, json=r_body, headers=QUERIES_HEADER)

    # Check HTTP errors early and fail fast with the server response for troubleshooting.
    if not response.ok:
        raise Exception(f"HTTP error when querying event: {response.status_code} - {response.text}")

    data = response.json()

    # Check GraphQL errors reported at the top-level "errors" field.
    if data.get("errors"):
        raise Exception(f"GraphQL error when querying event id: {data['errors']}")

    ids = (data.get('data') or {}).get('event')

    if ids:
        # Return as a simple tuple of (id, name)
        return ids.get('id'), ids.get('name')

    raise Exception(f'Error getting event identifiers: {ids}')


def has_incomplete_sets(event_id: int, entrant_id: int) -> bool:
    """
    Check if an entrant has any incomplete sets (matches not yet finished).

    Parameters
    ----------
    event_id : int
        The internal event ID.
    entrant_id : int
        The entrant ID to check.

    Returns
    -------
    bool
        True if the entrant has incomplete sets (still playing), False otherwise.
    """
    r_body = {
        "query": """
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
        """,
        "variables": {
            "eventId": event_id,
            "entrantId": entrant_id
        }
    }

    resp = requests.post(url=API_URL, json=r_body, headers=QUERIES_HEADER)
    if not resp.ok:
        return False  # Assume no incomplete sets if request fails

    data = resp.json()
    if data.get("errors"):
        return False

    event = (data.get("data") or {}).get("event") or {}
    sets = event.get("sets") or {}
    page_info = sets.get("pageInfo") or {}
    total = page_info.get("total", 0)

    return total > 0  # True if there are any incomplete sets


def get_entrant_last_elimination_set_id(event_id: int, entrant_id: int) -> int | None:
    """Return the ID of the most recent completed set that eliminated the given entrant.

    Implementation details
    ----------------------
    - We fetch the most recent completed set for this entrant (sorted by RECENT).
    - If the entrant lost that set (winnerId != entrant_id), that is the elimination set.
    - If the entrant won their most recent set (e.g., the champion), return None.

    Notes
    -----
    - This is a best-effort heuristic that works for standard elimination brackets (single/double elim).
    - If the API returns no sets, or an unexpected shape, None is returned.
    """
    r_body = {
        "query": """
        query EntrantLastSet($eventId: ID!, $entrantId: ID!) {
          event(id: $eventId) {
            id
            sets(page: 1, perPage: 1, sortType: RECENT, filters: { entrantIds: [$entrantId], state: 3 }) {
              nodes {
                id
                winnerId
              }
            }
          }
        }
        """,
        "variables": {
            "eventId": event_id,
            "entrantId": entrant_id
        }
    }

    resp = requests.post(url=API_URL, json=r_body, headers=QUERIES_HEADER)
    if not resp.ok:
        # Fail soft: return None for this entrant if the request failed
        return None

    data = resp.json()
    if data.get("errors"):
        # Fail soft on GraphQL errors
        return None

    event = (data.get("data") or {}).get("event") or {}
    nodes = ((event.get("sets") or {}).get("nodes")) or []
    if not nodes:
        return None

    last_set = nodes[0]
    set_id = last_set.get("id")
    winner_id = last_set.get("winnerId")

    # If the entrant lost their most recent completed set, that is the elimination set.
    if set_id is not None and winner_id is not None and winner_id != entrant_id:
        return set_id

    return None


def get_set_details(set_id: int) -> dict | None:
    """
    Fetch details of a specific set (match) from start.gg.

    Parameters
    ----------
    set_id : int
        The internal ID of the set to fetch.

    Returns
    -------
    dict | None
        A dictionary with the following structure:
        {
            "winner_name": str,      # Name of the winning team/player
            "loser_name": str,       # Name of the losing team/player
            "winner_score": int,     # Winner's score
            "loser_score": int,      # Loser's score
            "identifier": str        # Match identifier (e.g., "AL", "AM")
        }
        Returns None if the set cannot be fetched or has invalid data.

    Notes
    -----
    - This function is useful for determining elimination details for tournament results
    - Returns None if the set is not completed or has missing data
    """
    r_body = {
        "query": """
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
        """,
        "variables": {
            "setId": set_id
        }
    }

    try:
        resp = requests.post(url=API_URL, json=r_body, headers=QUERIES_HEADER)
        if not resp.ok:
            return None

        data = resp.json()
        if data.get("errors"):
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

        # Extract both participants
        slot1, slot2 = slots[0], slots[1]

        entrant1 = (slot1.get("entrant") or {})
        entrant2 = (slot2.get("entrant") or {})

        id1 = entrant1.get("id")
        id2 = entrant2.get("id")
        name1 = entrant1.get("name")
        name2 = entrant2.get("name")

        # Get scores
        score1 = (((slot1.get("standing") or {}).get("stats") or {}).get("score") or {}).get("value")
        score2 = (((slot2.get("standing") or {}).get("stats") or {}).get("score") or {}).get("value")

        if name1 is None or name2 is None or id1 is None or id2 is None:
            return None

        # Determine winner and loser using winnerId (not scores, which may be missing)
        if id1 == winner_id:
            winner_name, loser_name = name1, name2
            winner_score, loser_score = score1, score2
        elif id2 == winner_id:
            winner_name, loser_name = name2, name1
            winner_score, loser_score = score2, score1
        else:
            # winnerId doesn't match either entrant (shouldn't happen)
            return None

        # Get identifier (match ID like "AL", "AM", etc.)
        identifier = set_data.get("identifier", "")

        return {
            "winner_name": winner_name,
            "loser_name": loser_name,
            "winner_score": winner_score,
            "loser_score": loser_score,
            "identifier": identifier
        }

    except Exception:
        return None


def _get_phase_groups_with_standings(event_id: int) -> list:
    """
    Get all phase groups for an event with their standings.

    This is an internal helper for the phase fallback mechanism.

    Parameters
    ----------
    event_id : int
        The internal event ID.

    Returns
    -------
    list[dict]
        List of phase groups with standings, each containing:
        {
            "phase_name": str,
            "group_identifier": str,
            "num_seeds": int,
            "state": int,
            "standings": [
                {
                    "placement": int,
                    "entrant_id": int,
                    "team_name": str,
                    "participants": [...]
                }
            ]
        }
    """
    # First get tournament structure (phases and groups)
    query_body = {
        "query": """
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
        """,
        "variables": {
            "eventId": event_id
        }
    }

    resp = requests.post(url=API_URL, json=query_body, headers=QUERIES_HEADER)
    if not resp.ok:
        return []

    data = resp.json()
    if data.get("errors"):
        return []

    event = (data.get("data") or {}).get("event")
    if not event:
        return []

    phase_groups_data = []

    for phase in (event.get("phases") or []):
        phase_name = phase.get("name", "Unknown")
        phase_state = phase.get("state")
        phase_num_seeds = phase.get("numSeeds", 0)

        # Process completed or ongoing phases (COMPLETED=3, STARTED=2, ACTIVE="ACTIVE")
        # Skip only CREATED (1) or unknown states
        if phase_state not in [2, 3, "STARTED", "ACTIVE", "COMPLETED"]:
            print(f"[INFO] Skipping phase '{phase_name}' (state={phase_state}) - not started yet")
            continue

        # Skip phases with too many participants (> 512) to avoid API timeouts
        if phase_num_seeds > 512:
            print(f"[INFO] Skipping phase '{phase_name}' ({phase_num_seeds} participants) - too large")
            continue

        phase_groups = (phase.get("phaseGroups") or {}).get("nodes") or []

        for group in phase_groups:
            group_id = group.get("id")
            group_identifier = group.get("displayIdentifier", "")
            group_state = group.get("state")
            seeds_info = (group.get("seeds") or {}).get("pageInfo") or {}
            num_seeds = seeds_info.get("total", 0)

            # Get standings for this phase group
            standings = _get_phase_group_standings_with_participants(group_id)

            phase_groups_data.append({
                "phase_name": phase_name,
                "group_identifier": group_identifier,
                "num_seeds": num_seeds,
                "state": group_state,
                "standings": standings
            })

    return phase_groups_data


def _get_phase_group_standings_with_participants(phase_group_id: int) -> list:
    """
    Get standings from a specific phase group with full participant details.

    Parameters
    ----------
    phase_group_id : int
        The phase group ID.

    Returns
    -------
    list[dict]
        List of standings with participant info.
    """
    all_standings = []
    page = 1
    per_page = 50

    while True:
        query_body = {
            "query": """
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
            """,
            "variables": {
                "phaseGroupId": phase_group_id,
                "page": page,
                "perPage": per_page
            }
        }

        resp = requests.post(url=API_URL, json=query_body, headers=QUERIES_HEADER)
        if not resp.ok:
            break

        data = resp.json()
        if data.get("errors"):
            break

        phase_group = (data.get("data") or {}).get("phaseGroup")
        if not phase_group:
            break

        standings = phase_group.get("standings") or {}
        nodes = standings.get("nodes") or []

        if not nodes:
            break

        for node in nodes:
            entrant = node.get("entrant") or {}
            all_standings.append({
                "placement": node.get("placement"),
                "entrant_id": entrant.get("id"),
                "team_name": entrant.get("name"),
                "participants": entrant.get("participants") or []
            })

        # Pagination
        page_info = standings.get("pageInfo") or {}
        total_pages = page_info.get("totalPages", 1)

        if page >= total_pages:
            break

        page += 1

    return all_standings


def _get_teams_from_phase_groups(event_id: int, event_slug: str, top_n: int, only_finalized_placements: bool = True) -> list:
    """
    Fallback method to get teams from phase group standings when event standings are empty.

    This is used for ongoing tournaments where event-level standings are not yet available.

    Parameters
    ----------
    event_id : int
        The internal event ID.
    event_slug : str
        The event slug (for logging).
    top_n : int
        Number of teams to fetch.
    only_finalized_placements : bool, optional
        If True (default), only include teams whose placement is finalized (eliminated teams
        or tournament winners). If False, include all teams with standings.

    Returns
    -------
    list[dict]
        List of team dictionaries in the same format as get_event_top_teams.
    """
    phase_groups = _get_phase_groups_with_standings(event_id)

    if not phase_groups:
        print(f"[WARN] No phase groups found for '{event_slug}'")
        return []

    # Organize teams by their placement within groups
    # Teams at the same placement across groups get cumulative placements
    teams_by_placement = {}

    for pg in phase_groups:
        phase_name = pg["phase_name"]
        group_id = pg["group_identifier"]

        for standing in pg["standings"]:
            placement = standing.get("placement")
            if placement is None:
                continue

            if placement not in teams_by_placement:
                teams_by_placement[placement] = []

            teams_by_placement[placement].append({
                "group_placement": placement,
                "group_name": f"{phase_name} - {group_id}",
                "entrant_id": standing.get("entrant_id"),
                "team_name": standing.get("team_name"),
                "participants": standing.get("participants", [])
            })

    # Calculate cumulative placements
    results = []
    cumulative_placement = 1

    for group_placement in sorted(teams_by_placement.keys()):
        teams_at_placement = teams_by_placement[group_placement]
        # Sort by group name for consistent ordering
        teams_at_placement.sort(key=lambda t: t["group_name"])

        for team in teams_at_placement:
            entrant_id = team.get("entrant_id")

            # Build members list
            members = []
            for p in team.get("participants", []):
                members.append({
                    "player_id": p.get("id"),
                    "player_tag": p.get("gamerTag"),
                    "player_country": country_iso2((((p.get("user") or {}).get("location") or {}).get("country")))
                })

            # Check if team is still playing (has incomplete sets)
            import time
            time.sleep(0.5)  # Rate limiting

            is_still_playing = False
            if entrant_id is not None and only_finalized_placements:
                is_still_playing = has_incomplete_sets(event_id, entrant_id)
                if is_still_playing:
                    # This team still has matches to play, skip it
                    continue

            # Get elimination set id and details for sorting by bracket position
            elimination_set_id = None
            bracket_group = None
            bracket_identifier = None

            if entrant_id is not None:
                elimination_set_id = get_entrant_last_elimination_set_id(event_id, entrant_id)

                # Get set details for bracket position sorting
                if elimination_set_id:
                    time.sleep(0.5)  # Rate limiting
                    set_details = get_set_details(elimination_set_id)
                    if set_details:
                        identifier = set_details.get("identifier", "")
                        # Extract group and identifier (e.g., "B1 AL" -> group="B1", id="AL")
                        # Format can be "AL", "B1 AL", etc.
                        parts = identifier.split()
                        if len(parts) >= 2:
                            bracket_group = parts[0]  # e.g., "B1"
                            bracket_identifier = parts[1]  # e.g., "AL"
                        else:
                            bracket_identifier = identifier

            results.append({
                "placement": cumulative_placement,
                "team_name": team.get("team_name"),
                "members": members,
                "elimination_set_id": elimination_set_id,
                "bracket_group": bracket_group,
                "bracket_identifier": bracket_identifier
            })

            cumulative_placement += 1

            if len(results) >= top_n:
                break

        if len(results) >= top_n:
            break

    # Sort by bracket position (group first, then identifier)
    results.sort(key=lambda t: (
        t.get("bracket_group") or "ZZZZ",  # Put teams without group at end
        t.get("bracket_identifier") or "ZZZZ"
    ))

    # Reassign placements after sorting
    for idx, team in enumerate(results, 1):
        team["placement"] = idx

    print(f"[INFO] Retrieved {len(results)} teams from phase group standings")
    return results


def _get_pool_placements_map(event_id: int) -> dict:
    """
    Get a mapping of entrant_id to their pool group and placement.

    Parameters
    ----------
    event_id : int
        The internal event ID.

    Returns
    -------
    dict
        Mapping of {entrant_id: {"pool_group": str, "pool_placement": int}}
    """
    phase_groups = _get_phase_groups_with_standings(event_id)
    pool_map = {}

    for pg in phase_groups:
        group_id = pg["group_identifier"]
        for standing in pg["standings"]:
            entrant_id = standing.get("entrant_id")
            if entrant_id:
                pool_map[entrant_id] = {
                    "pool_group": group_id,
                    "pool_placement": standing.get("placement")
                }

    return pool_map


def get_event_top_teams(event_slug: str, top_n: int, use_phase_fallback: bool = True,
                        only_finalized_placements: bool = True) -> list:
    """
    Fetch the top-N teams for a given event (by slug), ordered by placement via event.standings. The output includes
    teams' name and a list of members (player id, gamer tag, ISO-2 country code).

    Parameters
    ----------
    event_slug : str
        Event slug, e.g., "tournament/.../event/...".
    top_n : int
        Number of teams to fetch (Top 16, Top 32, etc.). Must be > 0.
    use_phase_fallback : bool, optional
        If True (default), when event standings are empty (ongoing event), automatically
        fall back to fetching from phase group standings. Set to False to disable this behavior.
    only_finalized_placements : bool, optional
        If True (default), only include teams with confirmed placements (eliminated or qualified).
        Teams still playing will be replaced with empty placeholders. Set to False to include all teams.

    Returns
    -------
    list[dict]
        A list of normalized dictionaries with the following shape:
        {
            "placement": int,
            "team_name": str,
            "members": [
                {
                    "player_id": str | int,
                    "player_tag": str | None,
                    "player_country": str | None # ISO 3166-1 alpha-2 (e.g., "FR") or None
                },
                ...],
            "elimination_set_id": int | None # ID of the set that eliminated the team, or None for the champion
        }

    The list is sorted by ascending placement and truncated to the requested top_n.

    Raises
    ------
    Exception
        - If the HTTP request fails (non-2xx response).
        - If the GraphQL payload contains errors.

    Notes
    -----
    - Pagination is handled automatically using page/perPage parameters.
    - Per-page size is capped at 50 for a balance between request count and payload size.
    - If fewer teams exist than requested, the function returns as many as available.
    - For ongoing events where event standings are empty, falls back to phase group standings
      (requires get_phase_results module from prize_pool_filler).
    - When only_finalized_placements=True, teams with incomplete sets (ongoing matches) are
      replaced with empty placeholders to allow manual editing later.
    """
    if top_n <= 0:
        return []

    # Resolve the event's internal ID before querying standings
    event_id, _ = get_event_id(event_slug)

    # Fetch pool placements map to enrich team data with pool group information
    print(f"[INFO] Fetching pool group placements...")
    pool_map = _get_pool_placements_map(event_id)
    print(f"[INFO] Found pool data for {len(pool_map)} teams")

    results = []
    page = 1
    per_page = min(50, top_n)  # Good balance between performance and API limits

    # Iterate through standing pages until we accumulate at least top_n entries or there are no more pages to read.
    while len(results) < top_n:
        r_body = {
            "query": """
            query EventTopTeams($eventId: ID!, $page: Int!, $perPage: Int!) {
              event(id: $eventId) {
                id
                standings(query: { page: $page, perPage: $perPage }) {
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
            """,
            "variables": {
                "eventId": event_id,
                "page": page,
                "perPage": per_page
            }
        }

        resp = requests.post(url=API_URL, json=r_body, headers=QUERIES_HEADER)
        # Surface HTTP errors with the raw response for easier debugging.
        if not resp.ok:
            raise Exception(f"HTTP error when fetching standings: {resp.status_code} - {resp.text}")

        data = resp.json()

        # If the API returns a GraphQL error, raise it (rather than silently returning an empty list).
        if data.get("errors"):
            raise Exception(f"GraphQL error when fetching standings: {data['errors']}")

        event = (data.get("data") or {}).get("event")

        if not event:
            # Defensive break: unexpected payload or missing event
            break

        standings = event.get("standings") or {}
        nodes = standings.get("nodes") or []

        if not nodes:
            # No entries on this page — stop paging
            break

        for node in nodes:
            if len(results) >= top_n:
                break
            placement = node.get("placement")
            entrant = node.get("entrant") or {}
            team_name = entrant.get("name")
            participants = entrant.get("participants") or []
            entrant_id = entrant.get("id")

            members = []

            # Normalize each participant: we only keep a few fields needed downstream.
            for p in participants:
                members.append({
                    "player_id": p.get("id"),
                    "player_tag": p.get("gamerTag"),
                    # `country` can be missing; `country_iso2` will return None if input is falsy.
                    "player_country": country_iso2((((p.get("user") or {}).get("location") or {}).get("country")))
                })

            # Get pool group and placement information
            pool_info = pool_map.get(entrant_id, {}) if entrant_id else {}
            pool_group = pool_info.get("pool_group")
            pool_placement = pool_info.get("pool_placement")

            # Compute the elimination set id (None for champions or if not determinable).
            elimination_set_id = None
            bracket_group = None
            bracket_identifier = None

            if entrant_id is not None:
                elimination_set_id = get_entrant_last_elimination_set_id(event_id, entrant_id)

                # Get set details for bracket position sorting
                if elimination_set_id:
                    import time
                    time.sleep(0.5)  # Rate limiting
                    set_details = get_set_details(elimination_set_id)
                    if set_details:
                        identifier = set_details.get("identifier", "")
                        # Extract group and identifier (e.g., "B1 AL" -> group="B1", id="AL")
                        # Format can be "AL", "B1 AL", etc.
                        parts = identifier.split()
                        if len(parts) >= 2:
                            bracket_group = parts[0]  # e.g., "B1"
                            bracket_identifier = parts[1]  # e.g., "AL"
                        else:
                            bracket_identifier = identifier

            results.append({
                "placement": placement,
                "team_name": team_name,
                "members": members,
                "elimination_set_id": elimination_set_id,
                "bracket_group": bracket_group,
                "bracket_identifier": bracket_identifier,
                "pool_group": pool_group,
                "pool_placement": pool_placement
            })

        # Pagination bookkeeping: move to the next page and stop when we pass totalPages.
        page += 1
        total_pages = ((standings.get("pageInfo") or {}).get("totalPages")) or page - 1

        if page > total_pages:
            break

    # If no results from event standings and fallback is enabled, try phase group standings
    if not results and use_phase_fallback:
        print(f"[INFO] Event standings empty for '{event_slug}', attempting phase group fallback...")
        # Set only_finalized_placements=True to only include teams with confirmed placements
        # (eliminated teams). Empty placeholders will be added later for unfilled positions.
        results = _get_teams_from_phase_groups(event_id, event_slug, top_n, only_finalized_placements=True)

        # Pad with empty placeholders if we got fewer teams than requested
        if len(results) < top_n:
            num_placeholders = top_n - len(results)
            print(f"[INFO] Adding {num_placeholders} empty placeholders for ongoing/unfilled positions")
            for i in range(num_placeholders):
                results.append({
                    "placement": len(results) + 1,
                    "team_name": None,  # Empty placeholder
                    "members": [],
                    "elimination_set_id": None,
                    "bracket_group": None,
                    "bracket_identifier": None
                })

    # Sort by pool placement and group for proper Liquipedia ordering
    # 1. By pool placement (1st place, 2nd place, 3rd place across all pools)
    # 2. By pool group (A1, A2, A3, A4 within each placement tier)
    # 3. By bracket identifier (for teams eliminated in same round)
    results.sort(key=lambda r: (
        r.get("pool_placement") or 9999,  # Primary: sort by placement within pool (1st, 2nd, etc.)
        r.get("pool_group") or "ZZZZ",  # Secondary: by pool group (A1, A2, A3, A4)
        r.get("bracket_identifier") or "ZZZZ"  # Tertiary: by match identifier (AL, AM, U, etc.)
    ))

    return results[:top_n]
