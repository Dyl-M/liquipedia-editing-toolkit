# -*- coding: utf-8 -*-

import requests

"""File Information
@file_name: tools.py
@author: Dylan "dyl-m" Monfret
Collection of "start.gg tools" and useful functions
"""

'GLOBAL VARIABLES'

API_URL = 'https://api.start.gg/gql/alpha'  # API URL

# Read the token and set up the header with Authorization
with open('../token/start.gg-token.txt', 'r', encoding='utf8') as token_file:
    QUERIES_HEADER = {"Authorization": f"Bearer {token_file.read()}"}

'TOOLS'

def get_event_id(comp_slug: str) -> tuple:
    """Return identifiers for a competition on start.gg
    :param comp_slug: URL slug for a competition
    :return: return the identifiers and the name of the event.
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
    ids = response.json().get('data').get('event')

    if ids:
        return ids.get('id'), ids.get('name')

    raise Exception(f'Error getting event identifiers: {ids}')