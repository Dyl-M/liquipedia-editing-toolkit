# -*- coding: utf-8 -*-

"""Start.gg to Liquipedia Tools

This package provides tools for data analysis and integration between start.gg
(esports tournament platform) and Liquipedia (gaming wiki) for Rocket League competitions.

Main modules:
- tournament_page_filler: Fetch data from start.gg and generate TeamCard wikitext
- stream_filler: Insert stream links into Liquipedia brackets
- prize_pool_filler: Auto-fill prize pool sections with placement data
"""

from . import tournament_page_filler
from . import stream_filler
from . import prize_pool_filler

__all__ = [
    "tournament_page_filler",
    "stream_filler",
    "prizepool_filler",
]

__version__ = "0.1.0"
