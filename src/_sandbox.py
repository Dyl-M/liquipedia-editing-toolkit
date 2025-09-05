# -*- coding: utf-8 -*-

import json
import requests
import startgg_tools as sgg_t

"""File Information
@file_name: _sandbox.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions.
"""

if __name__ == "__main__":
    from startgg_tools import get_event_top_teams
    from liquipedia_tools import generate_team_cards_tabs_from_json

    event_slug = "tournament/3v3-sam-champions-road-2025/event/3v3-bracket"
    top_teams = get_event_top_teams(event_slug, top_n=32)

    with open(f'../data/{event_slug.split('/')[1]}.json', 'w', encoding='utf-8') as json_file:
        json.dump(top_teams, json_file, indent=4, ensure_ascii=False)

    print(generate_team_cards_tabs_from_json("../data/3v3-sam-champions-road-2025.json",
                                             [12, 32],
                                             remove_empty_optional=True))
