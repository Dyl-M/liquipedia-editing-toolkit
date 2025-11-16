# -*- coding: utf-8 -*-

"""File Information
@file_name: fill_prize_pool.py
@author: Dylan "dyl-m" Monfret
Fill Liquipedia prize pool wikitext with start.gg tournament results.

This module provides utilities to:
- Parse Liquipedia prize pool wikitext to extract slot placement ranges
- Match teams from start.gg tournament data to the correct slots
- Fill in opponent information (team name, last opponent, elimination score)
"""

import re
import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Handle both direct execution and module imports
try:
    # Relative imports (when run as module)
    from ..tournament_page_filler import startgg_tools as sgg_t
    from . import get_phase_results as phase_tools

except ImportError:
    # Absolute imports (when run directly)
    # Add parent directories to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from tournament_page_filler import startgg_tools as sgg_t
    import get_phase_results as phase_tools


def parse_placement_range(place_str: str) -> Tuple[int, int]:
    """
    Parse a placement string into a range tuple.

    Args:
        place_str: Placement string like "1", "3-4", "65-72", etc.

    Returns:
        Tuple of (start, end) inclusive. For single placements, start == end.

    Raises:
        ValueError: If the placement string is invalid.

    Examples:
        >>> parse_placement_range("1")
        (1, 1)
        >>> parse_placement_range("65-72")
        (65, 72)
        >>> parse_placement_range("3-4")
        (3, 4)
    """
    place_str = place_str.strip()

    if '-' in place_str:
        parts = place_str.split('-')
        if len(parts) != 2:
            raise ValueError(f"Invalid placement range format: {place_str}")
        try:
            start, end = int(parts[0].strip()), int(parts[1].strip())
            if start > end:
                raise ValueError(f"Invalid range: start ({start}) > end ({end})")
            return start, end
        except ValueError as e:
            raise ValueError(f"Invalid placement range: {place_str}") from e
    else:
        try:
            placement = int(place_str)
            return placement, placement
        except ValueError as e:
            raise ValueError(f"Invalid placement: {place_str}") from e


def extract_prize_pool_slots(wikitext: str) -> List[Dict]:
    """
    Extract all slots from wikitext that contain opponent entries to be filled.

    Args:
        wikitext: The Liquipedia wikitext containing prize pool slots.

    Returns:
        List of dictionaries with the following structure:
        [
            {
                "place_str": "65-72",
                "place_start": 65,
                "place_end": 72,
                "full_match": "...",  # Complete slot block including opponents
                "opponents_section": "...",  # Just the opponent entries
                "opponent_slots": [...]  # List of individual opponent strings
            }
        ]

    Notes:
        - Only returns slots that have opponent entries (multi-line slots)
        - Slots without opponents (single-line) are ignored
    """
    # Pattern: Match slot line followed by opponent entries
    # |{{Slot|place=X-Y|...
    # |{{Opponent|tbd|...}}
    # |{{Opponent|tbd|...}}
    # }}
    pattern = r'\|{{Slot\|place=([^|}\n]+)([^\n]*)\n((?:\|{{Opponent\|[^\n]+\n)+)}}'

    slots = []
    for match in re.finditer(pattern, wikitext):
        place_str = match.group(1).strip()
        place_start, place_end = parse_placement_range(place_str)

        full_match = match.group(0)
        opponents_section = match.group(3)

        # Extract individual opponent entries
        opponent_slots = re.findall(r'\|{{Opponent\|[^\n]+', opponents_section)

        slots.append({
            "place_str": place_str,
            "place_start": place_start,
            "place_end": place_end,
            "full_match": full_match,
            "opponents_section": opponents_section,
            "opponent_slots": opponent_slots
        })

    return slots


def calculate_required_teams(slots: List[Dict]) -> int:
    """
    Calculate the maximum number of teams needed based on slot placements.

    Args:
        slots: List of slot dictionaries from extract_prizepool_slots()

    Returns:
        Maximum placement number (to use as top_n for API fetch)

    Examples:
        >>> t_slots = [
        ...     {"place_start": 65, "place_end": 72},
        ...     {"place_start": 73, "place_end": 104},
        ... ]
        >>> calculate_required_teams(slots)
        104
    """
    if not slots:
        return 0

    return max(slot["place_end"] for slot in slots)


def get_teams_with_placements(
        event_slug: str,
        required_teams: int,
        phase_name: Optional[str] = None,
        use_phase_fallback: bool = True
) -> List[Dict]:
    """
    Get team placements from start.gg, trying event standings first, then phases.

    This is the main function for section 1.4 - it handles:
    - Detecting if event standings are complete
    - Falling back to phase results for ongoing tournaments
    - Enriching data with elimination_set_id

    Args:
        event_slug: Event slug (e.g., "tournament/xyz/event/abc")
        required_teams: Number of teams needed (from calculate_required_teams)
        phase_name: Optional specific phase to get results from (e.g., "Day 2")
        use_phase_fallback: If True, fall back to phase results when event standings incomplete

    Returns:
        List of team dictionaries:
        [
            {
                "placement": int,
                "team_name": str,
                "entrant_id": int,
                "elimination_set_id": int | None
            }
        ]

    Notes:
        - Tries event standings first (fastest, most accurate for completed events)
        - Falls back to phase results if event standings incomplete or unavailable
        - Returns teams sorted by placement
    """
    print(f"\nFetching teams for {event_slug}...")
    print(f"Required teams: {required_teams}")

    # Strategy 1: Try event standings first
    if not phase_name:
        print("\nAttempting to get event standings...")
        try:
            teams = sgg_t.get_event_top_teams(event_slug, top_n=required_teams)
            if len(teams) >= required_teams:
                print(f"[OK] Got {len(teams)} teams from event standings")
                return teams
            else:
                print(f"[WARNING] Event standings incomplete: got {len(teams)}/{required_teams} teams")
                if not use_phase_fallback:
                    return teams
        except Exception as e:
            print(f"[ERROR] Event standings failed: {e}")
            if not use_phase_fallback:
                return []

    # Strategy 2: Fall back to phase results
    print("\nFalling back to phase results...")
    try:
        # Get event ID first (needed for elimination_set_id lookup)
        event_id, event_name = sgg_t.get_event_id(event_slug)
        print(f"Event: {event_name} (ID: {event_id})")

        # Get phase results (with optimization to skip large phases)
        phase_results = phase_tools.get_completed_phase_results(
            event_slug,
            phase_name_filter=phase_name,
            required_teams=required_teams  # Enable smart phase selection
        )

        if not phase_results:
            print("[ERROR] No completed phase results found")
            return []

        # Calculate cumulative placements
        teams_data = phase_tools.calculate_cumulative_placements(phase_results)
        print(f"\n[OK] Got {len(teams_data)} teams from phase results")

        # Enrich with elimination_set_id
        print("Enriching with elimination data...")
        enriched_teams = []

        for team in teams_data:
            entrant_id = team.get("entrant_id")
            elimination_set_id = None

            if entrant_id and event_id:
                # Rate limiting: delay between API calls
                time.sleep(0.5)
                elimination_set_id = sgg_t.get_entrant_last_elimination_set_id(event_id, entrant_id)

            enriched_teams.append({
                "placement": team["cumulative_placement"],
                "team_name": team["team_name"],
                "entrant_id": entrant_id,
                "elimination_set_id": elimination_set_id,
                "group_name": team.get("group_name", "")  # Preserve group info for sorting
            })

        # Sort by placement
        enriched_teams.sort(key=lambda t: t["placement"])

        return enriched_teams

    except Exception as e:
        print(f"[ERROR] Phase results failed: {e}")
        return []


def get_elimination_details(set_id: int) -> Optional[Dict]:
    """
    Get elimination details for a team from a specific set.

    Wrapper around startgg_tools.get_set_details() with additional formatting.

    Args:
        set_id: The set ID where the team was eliminated

    Returns:
        Dictionary with elimination details:
        {
            "winner_name": str,      # Team that won (eliminated this team)
            "loser_name": str,       # Team that lost (the eliminated team)
            "winner_score": int,     # Winner's score
            "loser_score": int       # Loser's score (-1 for forfeit)
        }
        Returns None if set details unavailable

    Notes:
        - Uses existing startgg_tools.get_set_details()
        - Adds rate limiting (call from outside with delays)
    """
    return sgg_t.get_set_details(set_id)


def format_score(team_score: int, opponent_score: int) -> str:
    """
    Format a match score for Liquipedia wikitext.

    Args:
        team_score: The eliminated team's score
        opponent_score: The winning team's score

    Returns:
        Formatted score string for lastvsscore field

    Examples:
        >>> format_score(1, 3)
        '1-3'
        >>> format_score(-1, 0)  # Team forfeited
        'FF-W'
        >>> format_score(0, -1)  # Opponent forfeited (unusual but possible)
        'W-FF'
    """
    # Handle forfeits
    if team_score == -1:
        return "FF-W"  # This team forfeited, opponent won
    if opponent_score == -1:
        return "W-FF"  # Opponent forfeited, this team won (shouldn't happen for eliminated teams)

    return f"{team_score}-{opponent_score}"


def fill_prizepool_opponents(wikitext: str, teams_data: List[Dict]) -> str:
    """
    Fill prize pool wikitext with team opponent data.

    This is the main function for Phase 2 - it handles:
    - 2.1: Respecting placement order when filling slots
    - 2.2: Handling forfeit losses (via format_score)

    Args:
        wikitext: The Liquipedia prize pool wikitext with empty opponent slots
        teams_data: List of team dictionaries from get_teams_with_placements():
            [
                {
                    "placement": int,
                    "team_name": str,
                    "entrant_id": int,
                    "elimination_set_id": int | None
                }
            ]

    Returns:
        Updated wikitext with filled opponent information

    Notes:
        - Teams are matched to slots by placement number
        - For placement ranges (e.g., 65-72), teams are filled in placement order
        - Elimination details fetched from start.gg API (with rate limiting)
        - If elimination data unavailable, lastvs/lastvsscore left empty
    """
    # Create a mapping of placement -> team data
    teams_by_placement = {team["placement"]: team for team in teams_data}

    # Extract slots from wikitext
    slots = extract_prize_pool_slots(wikitext)

    # Process each slot
    result = wikitext
    for slot in slots:
        place_start = slot["place_start"]
        place_end = slot["place_end"]
        opponent_slots = slot["opponent_slots"]

        # Get teams for this placement range
        teams_in_range = []
        for placement in range(place_start, place_end + 1):
            if placement in teams_by_placement:
                teams_in_range.append(teams_by_placement[placement])
            else:
                # No team data for this placement
                teams_in_range.append(None)

        # Enrich teams with elimination details (identifier for sorting)
        teams_with_details = []
        for team in teams_in_range:
            if team is None:
                teams_with_details.append(None)
                continue

            team_name = team["team_name"]
            elimination_set_id = team.get("elimination_set_id")

            # Get elimination details
            lastvs = ""
            lastvsscore = ""
            identifier = ""  # Match identifier for sorting (e.g., "AL", "AM")

            if elimination_set_id:
                # Add rate limiting to avoid overwhelming the API
                time.sleep(0.5)

                try:
                    elim_details = get_elimination_details(elimination_set_id)
                    if elim_details:
                        # The winner is who they lost to
                        lastvs = elim_details["winner_name"]
                        # Format the score from loser's perspective
                        lastvsscore = format_score(
                            elim_details["loser_score"],
                            elim_details["winner_score"]
                        )
                        # Get match identifier for sorting
                        identifier = elim_details.get("identifier", "")
                except Exception as e:
                    print(f"[WARNING] Could not fetch elimination details for {team_name}: {e}")

            teams_with_details.append({
                "team_name": team_name,
                "lastvs": lastvs,
                "lastvsscore": lastvsscore,
                "identifier": identifier,
                "placement": team["placement"],
                "group_name": team.get("group_name", "")
            })

        # Sort by group first (B1, B2, ...), then by match identifier (AL, AM, ...) within each group
        # This ensures teams are ordered by bracket position:
        # - B1-AL, B1-AM, ... B2-AL, B2-AM, ... etc.
        teams_with_details.sort(key=lambda t: (
            t is None,  # None teams last
            t["group_name"] if t else "",  # Sort by group (B1, B2, B3, ...)
            t["identifier"] == "" if t else "",  # Empty identifiers last within group
            t["identifier"] if t else ""  # Alphabetical by identifier within group
        ))

        # Build replacement opponent entries
        new_opponents = []
        for team_detail in teams_with_details:
            if team_detail is None:
                # Keep as tbd if no team data available
                new_opponents.append("|{{Opponent|tbd|lastvs=|lastvsscore=}}")
                continue

            # Build the opponent entry
            opponent_entry = f"|{{{{Opponent|{team_detail['team_name']}|lastvs={team_detail['lastvs']}|lastvsscore={team_detail['lastvsscore']}}}}}"
            new_opponents.append(opponent_entry)

        # Replace the opponents section in this slot
        # Build the new opponents section
        new_opponents_section = "\n".join(new_opponents) + "\n"

        # Replace in the full slot match
        old_slot = slot["full_match"]
        new_slot = old_slot.replace(slot["opponents_section"], new_opponents_section)

        # Replace in the result
        result = result.replace(old_slot, new_slot)

    return result


def process_prizepool_from_event(
        event_slug: str,
        wikitext_path: str,
        output_path: str,
        top_n: Optional[int] = None,
        phase_name: Optional[str] = None
) -> None:
    """
    Complete workflow to fetch tournament data and fill prize pool wikitext.

    This is the main entry point that combines all Phase 1 and Phase 2 functionality:
    - Reads wikitext file
    - Extracts slots and calculates required teams
    - Fetches team data from start.gg
    - Fills opponent information
    - Writes updated wikitext to output file

    Args:
        event_slug: start.gg event slug (e.g., "tournament/xyz/event/abc")
        wikitext_path: Path to input wikitext file
        output_path: Path to save filled wikitext
        top_n: Optional number of teams to fetch (if None, auto-calculated from wikitext)
        phase_name: Optional phase name for ongoing tournaments (e.g., "Day 2")

    Example:
        >>> process_prizepool_from_event(
        ...     event_slug="tournament/rlcs-2026-europe-open-1/event/3v3-bracket",
        ...     wikitext_path="wikitext_input.txt",
        ...     output_path="wikitext_output.txt",
        ...     top_n=128
        ... )
    """
    print("=" * 70)
    print("PRIZE POOL FILLER - Complete Workflow")
    print("=" * 70)

    # Step 1: Read wikitext
    print(f"\n[1/5] Reading wikitext from: {wikitext_path}")
    with open(wikitext_path, 'r', encoding='utf-8') as f:
        wikitext = f.read()
    print(f"[OK] Read {len(wikitext)} characters")

    # Step 2: Extract slots and calculate required teams
    print(f"\n[2/5] Analyzing wikitext structure...")
    slots = extract_prize_pool_slots(wikitext)
    print(f"[OK] Found {len(slots)} slots with opponent entries")

    if top_n is None:
        top_n = calculate_required_teams(slots)
        print(f"[OK] Calculated required teams: {top_n}")
    else:
        print(f"[OK] Using specified top_n: {top_n}")

    # Step 3: Fetch team data
    print(f"\n[3/5] Fetching team data from start.gg...")
    teams_data = get_teams_with_placements(
        event_slug=event_slug,
        required_teams=top_n,
        phase_name=phase_name,
        use_phase_fallback=True
    )

    if not teams_data:
        print("[ERROR] Failed to fetch team data. Aborting.")
        return

    print(f"[OK] Retrieved {len(teams_data)} teams")

    # Step 4: Fill opponents
    print(f"\n[4/5] Filling opponent information...")
    filled_wikitext = fill_prizepool_opponents(wikitext, teams_data)
    print(f"[OK] Filled wikitext ready")

    # Step 5: Write output
    print(f"\n[5/5] Writing output to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(filled_wikitext)
    print(f"[OK] Wrote {len(filled_wikitext)} characters")

    print("\n" + "=" * 70)
    print("COMPLETE - Prize pool wikitext has been filled!")
    print("=" * 70)
