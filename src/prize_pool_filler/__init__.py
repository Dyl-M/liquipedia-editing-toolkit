# -*- coding: utf-8 -*-

"""Prize pool Filler Module

This module provides tools to automatically fill Liquipedia prize pool wikitext
with tournament results from start.gg.
"""

from .fill_prize_pool import (
    parse_placement_range,
    extract_prize_pool_slots,
    calculate_required_teams,
    get_teams_with_placements,
    get_elimination_details,
    format_score
)

from . import get_phase_results

__all__ = [
    "parse_placement_range",
    "extract_prize_pool_slots",
    "calculate_required_teams",
    "get_teams_with_placements",
    "get_elimination_details",
    "format_score",
    "get_phase_results",
]
