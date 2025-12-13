# -*- coding: utf-8 -*-

"""
Application script for generating TeamParticipants format wikitext.
This script fetches tournament data from start.gg and generates the new
TeamParticipants format for Liquipedia.
"""

import json
import sys
import os
from tournament_page_filler import liquipedia_tools as lp_t, startgg_tools as sgg_t

# Ensure UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

# Get absolute path to _data directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, '_data')


def generate_team_participants_wikitext(event_slug: str, top_n: int, segments: list = None,
                                        output_file: str = None, save_json: bool = True):
    """
    Complete workflow to generate TeamParticipants wikitext from a start.gg event.

    Args:
        event_slug: The start.gg event slug (e.g., "tournament/.../event/...")
        top_n: Number of top teams to fetch
        segments: List of placement breakpoints for tabs (e.g., [12, 32] for "Top 12" and "Places 13-32")
                 If None, generates without tabs
        output_file: Optional path to save the wikitext output
        save_json: Whether to save the raw JSON data to _data/ directory

    Returns:
        The generated wikitext string
    """
    print(f"Fetching top {top_n} teams from: {event_slug}")
    print("=" * 80)

    # Fetch data from start.gg
    # Pass segments to enable smart placement filtering for ongoing tournaments
    top_teams = sgg_t.get_event_top_teams(event_slug, top_n=top_n, segments=segments)

    if not top_teams:
        print("[ERROR] No teams fetched. Check the event slug and API token.")
        return None

    print(f"✓ Successfully fetched {len(top_teams)} teams")

    # Save JSON if requested
    if save_json:
        tournament_name = event_slug.split('/')[1]
        json_path = os.path.join(DATA_DIR, f'{tournament_name}.json')

        # Create _data directory if it doesn't exist
        os.makedirs(DATA_DIR, exist_ok=True)

        with open(json_path, 'w', encoding='utf-8') as json_file:
            json.dump(top_teams, json_file, indent=4, ensure_ascii=False)
        print(f"✓ Saved JSON data to: {json_path}")

    else:
        # Create temporary JSON for processing
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
        json.dump(top_teams, temp_file)
        json_path = temp_file.name
        temp_file.close()

    print("\nGenerating TeamParticipants wikitext...")
    print("=" * 80)

    # Generate wikitext
    if segments:
        wikitext = lp_t.generate_team_participants_tabs_from_json(
            json_path,
            segments=segments,
            remove_empty_optional=True
        )
        print(f"✓ Generated with {len(segments)} tabs: {segments}")

    else:
        wikitext = lp_t.generate_team_participants_from_json(
            json_path,
            remove_empty_optional=True
        )
        print("✓ Generated without tabs")

    # Clean up temp file if created
    if not save_json:
        os.unlink(json_path)

    # Save output if requested
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(wikitext)
        print(f"✓ Saved wikitext to: {output_file}")

    print("\n" + "=" * 80)
    print("GENERATED WIKITEXT:")
    print("=" * 80)

    return wikitext


def generate_from_existing_json(json_path: str, segments: list = None, output_file: str = None):
    """
    Generate TeamParticipants wikitext from an existing JSON file.

    Args:
        json_path: Path to the JSON file containing team data
        segments: List of placement breakpoints for tabs
        output_file: Optional path to save the wikitext output

    Returns:
        The generated wikitext string
    """
    print(f"Loading data from: {json_path}")
    print("=" * 80)

    if not os.path.exists(json_path):
        print(f"[ERROR] File not found: {json_path}")
        return None

    print("Generating TeamParticipants wikitext...")
    print("=" * 80)

    # Generate wikitext
    if segments:
        wikitext = lp_t.generate_team_participants_tabs_from_json(
            json_path,
            segments=segments,
            remove_empty_optional=True
        )
        print(f"✓ Generated with {len(segments)} tabs: {segments}")
    else:
        wikitext = lp_t.generate_team_participants_from_json(
            json_path,
            remove_empty_optional=True
        )
        print("✓ Generated without tabs")

    # Save output if requested
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(wikitext)
        print(f"✓ Saved wikitext to: {output_file}")

    print("\n" + "=" * 80)
    print("GENERATED WIKITEXT:")
    print("=" * 80)

    return wikitext


if __name__ == "__main__":
    # ========================================================================
    # CONFIGURATION
    # ========================================================================

    # The phase fallback mechanism will automatically fetch from ongoing phase groups

    # Monthly Cash Cup December MENA (ongoing tournament example)
    EVENT_SLUG = "tournament/3v3-december-apac-monthly-cash-cup/event/3v3-bracket"

    TOP_N = 32  # Fetch top 32 teams
    SEGMENTS = [12, 32]  # "Top 12" and "Places 13-32" tabs
    OUTPUT_FILE = os.path.join(DATA_DIR, "output_team_participants.txt")

    wikitext = generate_team_participants_wikitext(
        event_slug=EVENT_SLUG,
        top_n=TOP_N,
        segments=SEGMENTS,
        output_file=OUTPUT_FILE,
        save_json=True
    )

    # Print the output (limited to avoid console overflow)
    if wikitext:
        print(wikitext[:3000])  # Print first 3000 characters
        if len(wikitext) > 3000:
            print("\n... (output truncated, see full output in file)")
        print("\n" + "=" * 80)
        print(f"✓ Complete! Check '{OUTPUT_FILE}' for the full wikitext.")

    else:
        print("\n" + "=" * 80)
        print("[INFO] No wikitext generated. This may happen if:")
        print("  - The tournament has no completed data yet (upcoming/ongoing)")
        print("  - The event slug is incorrect")
        print("  - The API token is missing or invalid")
        print("\nTip: For upcoming tournaments, wait until they complete or use")
        print("     an existing JSON file with USE_EXISTING_JSON = True")
