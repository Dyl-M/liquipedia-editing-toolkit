# -*- coding: utf-8 -*-

# Built-in and third-party imports
import json

# Local imports
from src.tournament_page_filler import liquipedia_tools as lp_t, startgg_tools as sgg_t

"""File Information
@file_name: _sandbox.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions.
"""

if __name__ == "__main__":
    event_slug = "tournament/unirocketeers-winter-2025/event/open-qualifier-4"
    top_teams = sgg_t.get_event_top_teams(event_slug, top_n=16)

    with open(f'_data/{event_slug.split('/')[1]}.json', 'w', encoding='utf-8') as json_file:
        json.dump(top_teams, json_file, indent=4, ensure_ascii=False)

    print(lp_t.generate_team_cards_tabs_from_json("../_data/unirocketeers-winter-2025.json",
                                                  [16],
                                                  remove_empty_optional=True))
