# -*- coding: utf-8 -*-

# import json
import requests

import tools as sgg_t  # start.gg tools

"""File Information
@file_name: _sandbox2.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions.
"""

'Functions'


def find_nested_value(input_dict: dict, keys: list):
    """Return the nested value inside a dictionary
    :param input_dict: initial Python dictionary
    :param keys: list of keys
    :return: the nested value.
    """
    try:
        for key in keys:
            input_dict = input_dict[key]
        return input_dict

    except (KeyError, TypeError):  # Return None if any key is missing or invalid
        return None


def get_standing(event_id: str):
    """
    :param event_id: start.gg ID of the event
    :return:
    """
    current_page = 1
    nb_pages = 999
    # teams = []

    while current_page <= nb_pages:
        print(f'Current Page: {current_page} / {nb_pages}')

        try:

            r_body = {
                'query': """
                query EventStandings($eventId: ID!, $page: Int!, $perPage: Int!) {
                  event(id: $eventId) {
                    id
                    name
                    standings(query: {
                      perPage: $perPage,
                      page: $page
                    }){
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
                    'eventId': event_id,
                    'perPage': 50,
                    'page': current_page
                }
            }

            response = requests.post(url=sgg_t.API_URL, json=r_body, headers=sgg_t.QUERIES_HEADER)
            print(response.json())
            current_page += 1

            if nb_pages is None:
                print('Error while requesting results.')
                break

        except AttributeError:  # End of the road I guess
            pass

    return None


'Main'

if __name__ == '__main__':
    comp = 'tournament/rlcs-2025-europe-open-6/event/eu-open-6'  # Competition slug
    ev_id, ev_name = sgg_t.get_event_id(comp_slug=comp)
    get_standing(ev_id)
