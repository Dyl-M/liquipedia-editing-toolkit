# -*- coding: utf-8 -*-

"""Run the prize pool filler on the actual wikitext"""

import sys
from pathlib import Path

# Handle both direct execution and module imports
try:
    from .fill_prize_pool import process_prizepool_from_event

except ImportError:
    # Add parent directory to path for direct execution
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from prizepool_filler.fill_prize_pool import process_prizepool_from_event

if __name__ == "__main__":
    # Event details
    EVENT_SLUG = "tournament/rlcs-2026-north-america-open-1/event/3v3-bracket"

    # File paths
    script_dir = Path(__file__).parent
    WIKITEXT_INPUT = script_dir / "wikitext_input.txt"
    WIKITEXT_OUTPUT = script_dir / "wikitext_output.txt"

    # Run the complete workflow
    process_prizepool_from_event(
        event_slug=EVENT_SLUG,
        wikitext_path=str(WIKITEXT_INPUT),
        output_path=str(WIKITEXT_OUTPUT),
        top_n=None,  # Auto-calculate from wikitext
        phase_name=None  # Auto-detect best phase
    )
