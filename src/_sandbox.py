# -*- coding: utf-8 -*-

import json

import requests

"""File Information
@file_name: _sandbox.py
@author: Dylan "dyl-m" Monfret
To test things / backup functions.
"""

# Read the token and set up the header with Authorization
with open('../token/start.gg-token.txt', 'r', encoding='utf8') as token_file:
    q_headers = {"Authorization": f"Bearer {token_file.read()}"}

api_url = 'https://api.start.gg/gql/alpha'  # API URL
comp = 'tournament/rlcs-2025-europe-open-2/event/eu-open-2'  # Competition slug

'Functions'


def find_nested_value(input_dict: dict, keys: list, def_val=None):
    """Return the nested value inside a dictionary
    :param input_dict: initial Python dictionary
    :param keys: list of keys
    :param def_val: default value in case of missing value
    :return: the nested value.
    """
    try:
        for key in keys:
            input_dict = input_dict[key]
        return input_dict

    except (KeyError, TypeError):  # Return None if any key is missing or invalid
        return def_val


def get_event_entrants(event_id: str, export_name: str = None) -> list:
    """Return entrants list and optionally saved it as JSON file
    :param event_id:
    :param export_name:
    :return:
    """
    current_page = 1
    nb_pages = 999
    teams = []

    while current_page <= nb_pages:
        print(f'Current Page: {current_page} / {nb_pages}')

        try:

            r_body = {
                'query': """
                query EventEntrants($eventId: ID!, $page: Int!, $perPage: Int!) {
                  event(id: $eventId) {
                    id
                    name
                    entrants(query: {
                      page: $page
                      perPage: $perPage
                    }) {
                      pageInfo {
                        total
                        totalPages
                      }
                      nodes {
                        id
                        name
                        standing {
                          standing
                        }
                        participants {
                          id
                          gamerTag
                          user {
                          location {
                            country
                            }
                          }
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

            response = requests.post(url=api_url, json=r_body, headers=q_headers)

            print(response.json())

            teams += response.json().get('data').get('event').get('entrants').get('nodes')
            nb_pages = response.json().get('data').get('event').get('entrants').get('pageInfo').get('totalPages')
            current_page += 1

            if nb_pages is None:
                print('Error while requesting results.')
                break

        except AttributeError:  # End of the road I guess
            pass

    teams = [{'team_id': team['id'],
              'team_name': team['name'],
              'team_placement': find_nested_value(team, ['standing', 'standing'], 0),  # FIXME
              'members': [{'player_id': player['id'],
                           'player_tag': player['gamerTag'],
                           'player_country': find_nested_value(player, ['user', 'location', 'country'])}
                          for player in team['participants']]} for team in teams]

    teams_sorted = sorted(teams, key=lambda d: d['team_placement'])

    if export_name:
        with open(f'../data/{export_name.lower().replace(" ", "_")}.json', 'w', encoding='utf8') as j_file:
            # noinspection PyTypeChecker
            json.dump(teams_sorted, j_file, ensure_ascii=False, indent=4)

    return teams_sorted


'Main'

if __name__ == '__main__':
    ev_id, ev_name = get_event_id(comp_slug=comp)
    entrants = get_event_entrants(ev_id, ev_name)
