# -*- coding: utf-8 -*-

"""Get results from individual phases/groups when event standings aren't available

This module handles ongoing tournaments where full event standings are incomplete.
It provides tools to:
- Understand tournament structure (phases and groups)
- Detect when event standings are unavailable
- Fetch results from specific completed phases
- Calculate cumulative placements across phase groups
"""

import sys
import requests

from pathlib import Path
from typing import Dict, List, Optional

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Handle both direct execution and module imports
try:
    # Relative import (when run as module)
    from ..tournament_page_filler import startgg_tools as sgg_t

except ImportError:
    # Absolute import (when run directly)
    from tournament_page_filler import startgg_tools as sgg_t


def get_tournament_structure(event_slug: str) -> Dict:
    """
    Get the structure of a tournament including all phases and groups.

    Args:
        event_slug: Event slug (e.g., "tournament/xyz/event/abc")

    Returns:
        Dictionary with tournament structure:
        {
            "event_id": int,
            "event_name": str,
            "phases": [
                {
                    "id": int,
                    "name": str,
                    "state": int | str,  # 3 or "COMPLETED" = finished
                    "num_seeds": int,    # Total number of participants in this phase
                    "groups": [
                        {
                            "id": int,
                            "identifier": str,  # e.g., "B1", "B2"
                            "state": int | str,
                            "num_seeds": int  # Number of participants in this group
                        }
                    ]
                }
            ]
        }

    Raises:
        Exception: If event not found or API error
    """
    # Get event ID first
    try:
        event_id, event_name = sgg_t.get_event_id(event_slug)
    except Exception as e:
        raise Exception(f"Failed to get event ID for '{event_slug}': {e}") from e

    # Query for phases and groups with participant counts
    query_body = {
        "query": """
        query EventPhases($eventId: ID!) {
          event(id: $eventId) {
            id
            name
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

    resp = requests.post(url=sgg_t.API_URL, json=query_body, headers=sgg_t.QUERIES_HEADER)

    if not resp.ok:
        raise Exception(f"HTTP error {resp.status_code}: {resp.text}")

    data = resp.json()

    if data.get("errors"):
        raise Exception(f"GraphQL errors: {data['errors']}")

    event = (data.get("data") or {}).get("event")
    if not event:
        raise Exception(f"Event not found: {event_slug}")

    # Structure the response
    phases = []
    for phase in (event.get("phases") or []):
        groups = []
        phase_groups = (phase.get("phaseGroups") or {}).get("nodes") or []

        for group in phase_groups:
            # Get num_seeds from seeds.pageInfo.total
            seeds_info = group.get("seeds") or {}
            page_info = seeds_info.get("pageInfo") or {}
            num_seeds = page_info.get("total", 0)

            groups.append({
                "id": group.get("id"),
                "identifier": group.get("displayIdentifier"),
                "state": group.get("state"),
                "num_seeds": num_seeds
            })

        phases.append({
            "id": phase.get("id"),
            "name": phase.get("name"),
            "state": phase.get("state"),
            "num_seeds": phase.get("numSeeds", 0),
            "groups": groups
        })

    return {
        "event_id": event_id,
        "event_name": event_name,
        "phases": phases
    }


def get_phase_group_standings(phase_group_id: int, page: int = 1, per_page: int = 50) -> List[Dict]:
    """
    Get standings from a specific phase group.

    Args:
        phase_group_id: The phase group ID
        page: Page number (default 1)
        per_page: Results per page (default 50)

    Returns:
        List of standing entries:
        [
            {
                "placement": int,
                "entrant": {
                    "id": int,
                    "name": str
                }
            }
        ]
    """
    query_body = {
        "query": """
        query PhaseGroupStandings($phaseGroupId: ID!, $page: Int!, $perPage: Int!) {
          phaseGroup(id: $phaseGroupId) {
            id
            displayIdentifier
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

    resp = requests.post(url=sgg_t.API_URL, json=query_body, headers=sgg_t.QUERIES_HEADER)

    if not resp.ok:
        return []

    data = resp.json()
    if data.get("errors"):
        return []

    phase_group = (data.get("data") or {}).get("phaseGroup")
    if not phase_group:
        return []

    standings = phase_group.get("standings") or {}
    nodes = standings.get("nodes") or []

    return nodes


def select_optimal_phases(phases: List[Dict], required_teams: int) -> List[Dict]:
    """
    Select the most efficient phases to process based on participant count.

    This optimization avoids processing phases with too many participants.
    For example, if you need top 128 teams:
    - Stage with 1000 participants → Skip (too large, inefficient)
    - Stage with 256 participants → Process (good fit)
    - Stage with 32 participants → Process (may contain some top teams)

    Strategy:
    - Skip phases where num_seeds > 4 * required_teams (way too large)
    - Prefer completed phases with reasonable participant counts
    - Sort phases by num_seeds (ascending) to process smaller/later stages first

    Args:
        phases: List of phase dictionaries from get_tournament_structure()
        required_teams: Number of teams needed (e.g., 128 for top 128)

    Returns:
        Filtered and sorted list of phases to process

    Example:
        >>> phases = [
        ...     {"name": "Swiss", "num_seeds": 1000, "state": 3},
        ...     {"name": "Day 2", "num_seeds": 256, "state": 3},
        ...     {"name": "Playoffs", "num_seeds": 32, "state": 3}
        ... ]
        >>> select_optimal_phases(phases, required_teams=128)
        [
            {"name": "Playoffs", "num_seeds": 32, ...},
            {"name": "Day 2", "num_seeds": 256, ...}
        ]
    """
    if not phases or required_teams <= 0:
        return phases

    # Filter out phases that are way too large (> 4x required teams)
    # This threshold is conservative - a phase with 4x teams is still useful
    # because it may contain all the teams we need
    max_seeds_threshold = required_teams * 4

    optimized_phases = []
    skipped_phases = []

    for phase in phases:
        num_seeds = phase.get("num_seeds", 0)
        phase_name = phase.get("name", "Unknown")

        # Only filter if we have valid seed count
        if num_seeds > 0 and num_seeds > max_seeds_threshold:
            skipped_phases.append({"name": phase_name, "num_seeds": num_seeds})
        else:
            optimized_phases.append(phase)

    # Report what was skipped
    if skipped_phases:
        print(f"\n[OPTIMIZATION] Skipping {len(skipped_phases)} phase(s) with too many participants:")
        for skipped in skipped_phases:
            print(f"  - '{skipped['name']}' ({skipped['num_seeds']} participants > {max_seeds_threshold} threshold)")

    # Sort by num_seeds ascending - process smaller stages first
    # Smaller stages = later in tournament = more relevant for top placements
    optimized_phases.sort(key=lambda p: p.get("num_seeds", float('inf')))

    return optimized_phases


def get_completed_phase_results(event_slug: str, phase_name_filter: Optional[str] = None, required_teams: Optional[int] = None) -> Dict[str, List[Dict]]:
    """
    Get results from all completed phases in an event.

    Args:
        event_slug: Event slug
        phase_name_filter: Optional filter for phase names (e.g., "Day 2")
                          If provided, only phases containing this string are processed
        required_teams: Optional number of teams needed (enables optimization to skip large phases)
                       If provided, phases with > 4x this number are skipped

    Returns:
        Dictionary mapping "Phase Name - Group ID" to list of standings:
        {
            "Day 2 - B1": [
                {
                    "placement": 1,
                    "entrant": {"id": 123, "name": "Team A"}
                },
                ...
            ]
        }

    Notes:
        - Only processes COMPLETED phases (state == 3 or "COMPLETED")
        - Groups are included in alphabetical order
        - Empty dict returned if no completed phases found
        - When required_teams is provided, phases with too many participants are skipped for efficiency
    """
    # Get tournament structure
    try:
        structure = get_tournament_structure(event_slug)
    except Exception as e:
        print(f"Error getting tournament structure: {e}")
        return {}

    # Apply optimization if required_teams is provided
    phases_to_process = structure["phases"]

    # First filter by completion status
    completed_phases = [
        phase for phase in phases_to_process
        if phase.get("state") in [3, "COMPLETED"]
    ]

    # Then apply phase name filter if requested
    if phase_name_filter:
        completed_phases = [
            phase for phase in completed_phases
            if phase_name_filter.lower() in phase.get("name", "").lower()
        ]

    # Apply smart phase selection optimization
    if required_teams:
        completed_phases = select_optimal_phases(completed_phases, required_teams)

    results = {}

    for phase in completed_phases:
        phase_name = phase["name"]
        phase_state = phase["state"]
        num_seeds = phase.get("num_seeds", 0)

        print(f"Phase '{phase_name}' ({num_seeds} participants) - State: {phase_state}")
        print(f"  -> Processing (COMPLETED)")

        # Get standings from each group
        for group in phase["groups"]:
            group_id = group["id"]
            group_identifier = group["identifier"]

            standings = get_phase_group_standings(group_id)
            if standings:
                key = f"{phase_name} - {group_identifier}"
                results[key] = standings
                print(f"  - {group_identifier}: {len(standings)} teams")

    return results


def calculate_cumulative_placements(phase_results: Dict[str, List[Dict]]) -> List[Dict]:
    """
    Calculate cumulative placements across multiple parallel phase groups.

    When a tournament has multiple parallel groups (B1, B2, B3...), teams are ranked
    by how far they progressed within their group, NOT by which group they were in.

    Groups are at the same level, so:
    - All 1st place teams from each group → overall placements 1-N (N = number of groups)
    - All 2nd place teams from each group → overall placements N+1 to 2N
    - All 3rd place teams from each group → overall placements 2N+1 to 3N
    - etc.

    Args:
        phase_results: Dictionary from get_completed_phase_results()
                      {"Phase - Group": [standings]}

    Returns:
        List of teams with cumulative placements:
        [
            {
                "cumulative_placement": int,  # Overall placement based on group performance
                "group_placement": int,        # Original placement within group
                "group_name": str,             # Group identifier
                "entrant_id": int,
                "team_name": str
            }
        ]

    Example:
        If B1-B8 each have teams with placements 1-32:
        - B1 1st place → cumulative placement 1
        - B2 1st place → cumulative placement 2
        - ...
        - B8 1st place → cumulative placement 8
        - B1 2nd place → cumulative placement 9
        - B2 2nd place → cumulative placement 10
        - ...
        - B8 2nd place → cumulative placement 16
    """
    # Organize teams by their group placement
    teams_by_placement = {}

    for group_key, standings in phase_results.items():
        for standing in standings:
            group_placement = standing.get("placement")
            entrant = standing.get("entrant") or {}

            if group_placement not in teams_by_placement:
                teams_by_placement[group_placement] = []

            teams_by_placement[group_placement].append({
                "group_placement": group_placement,
                "group_name": group_key,
                "entrant_id": entrant.get("id"),
                "team_name": entrant.get("name")
            })

    # Assign cumulative placements
    teams = []
    cumulative_placement = 1

    # Process by group placement (1st, 2nd, 3rd, etc.)
    for group_placement in sorted(teams_by_placement.keys()):
        teams_at_this_placement = teams_by_placement[group_placement]

        # Sort teams alphabetically by group name for consistent ordering
        teams_at_this_placement.sort(key=lambda t: t["group_name"])

        for team in teams_at_this_placement:
            team["cumulative_placement"] = cumulative_placement
            teams.append(team)
            cumulative_placement += 1

    return teams


def is_event_standings_complete(event_slug: str, required_teams: int) -> bool:
    """
    Check if event-level standings are complete and have enough teams.

    Args:
        event_slug: Event slug
        required_teams: Minimum number of teams needed

    Returns:
        True if event standings are complete and sufficient, False otherwise

    Notes:
        - Attempts to fetch required_teams from event standings
        - Returns False if API call fails or fewer teams returned
    """
    try:
        teams = sgg_t.get_event_top_teams(event_slug, top_n=required_teams)
        return len(teams) >= required_teams
    except Exception as e:
        print(f"Event standings check failed: {e}")
        return False


if __name__ == "__main__":
    # Example usage
    EVENT_SLUG = "tournament/rlcs-2026-europe-open-1/event/3v3-bracket"

    print("=" * 60)
    print("TOURNAMENT STRUCTURE")
    print("=" * 60)

    structure = get_tournament_structure(EVENT_SLUG)
    print(f"\nEvent: {structure['event_name']}")
    print(f"Event ID: {structure['event_id']}")
    print(f"\nPhases ({len(structure['phases'])}):")

    for phase in structure["phases"]:
        state_str = "COMPLETED" if phase["state"] in [3, "COMPLETED"] else "IN_PROGRESS"
        print(f"  - {phase['name']} [{state_str}]")
        print(f"    Groups: {', '.join(g['identifier'] for g in phase['groups'])}")

    print("\n" + "=" * 60)
    print("COMPLETED PHASE RESULTS")
    print("=" * 60)

    results = get_completed_phase_results(EVENT_SLUG, phase_name_filter="Day 2")
    print(f"\nFound {len(results)} phase groups with results")

    for phase_group_name, standings in list(results.items())[:2]:
        print(f"\n{phase_group_name}:")
        for standing in standings[:5]:
            placement = standing.get("placement")
            entrant = standing.get("entrant") or {}
            name = entrant.get("name", "N/A")
            print(f"  {placement}. {name}")

    print("\n" + "=" * 60)
    print("CUMULATIVE PLACEMENTS")
    print("=" * 60)

    teams = calculate_cumulative_placements(results)
    print(f"\nTotal teams with cumulative placements: {len(teams)}")
    print("\nFirst 10 teams:")
    for team in teams[:10]:
        print(
            f"  #{team['cumulative_placement']:3d} - {team['team_name']:30s} (Group: {team['group_name'].split(' - ')[-1]}, "
            f"Group Place: {team['group_placement']})")

    print("\nLast 10 teams:")
    for team in teams[-10:]:
        print(
            f"  #{team['cumulative_placement']:3d} - {team['team_name']:30s} (Group: {team['group_name'].split(' - ')[-1]}, "
            f"Group Place: {team['group_placement']})")
