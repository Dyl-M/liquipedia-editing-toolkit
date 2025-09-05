# -*- coding: utf-8 -*-

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
# - The token file path is relative to this script's location (../token/start.gg-token.txt).
# - Make sure the token file exists and contains a valid start.gg API token.
# - The token is read at import time; if it changes on disk, you must reload the module to use the new value.
with open('../token/start.gg-token.txt', 'r', encoding='utf8') as token_file:
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
    iso2 = pycountry.countries.get(name=country_str).alpha_2

    if iso2:
        return iso2
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


def _get_entrant_last_elimination_set_id(event_id: int, entrant_id: int) -> int | None:
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


def get_event_top_teams(event_slug: str, top_n: int) -> list:
    """
    Fetch the top-N teams for a given event (by slug), ordered by placement via event.standings. The output includes
    teams' name and a list of members (player id, gamer tag, ISO-2 country code).

    Parameters
    ----------
    event_slug : str
        Event slug, e.g., "tournament/.../event/...".
    top_n : int
        Number of teams to fetch (Top 16, Top 32, etc.). Must be > 0.

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
    """
    if top_n <= 0:
        return []

    # Resolve the event's internal ID before querying standings
    event_id, _ = get_event_id(event_slug)

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

            # Compute the elimination set id (None for champions or if not determinable).
            elimination_set_id = None
            if entrant_id is not None:
                elimination_set_id = _get_entrant_last_elimination_set_id(event_id, entrant_id)

            results.append({
                "placement": placement,
                "team_name": team_name,
                "members": members,
                "elimination_set_id": elimination_set_id
            })

        # Pagination bookkeeping: move to the next page and stop when we pass totalPages.
        page += 1
        total_pages = ((standings.get("pageInfo") or {}).get("totalPages")) or page - 1

        if page > total_pages:
            break

    # Ensure ascending order by placement and slice to top_n to match the requested size.
    results.sort(key=lambda r: (
        r.get("placement") is None, r.get("placement"),
        r.get("elimination_set_id") is None, r.get("elimination_set_id")
    ))
    return results[:top_n]
