import re
from enum import Enum


class StreamType(Enum):
    TWITCH = "twitch"
    YOUTUBE = "youtube"


class StreamConfig:
    """Configuration for a team's streaming channel"""

    def __init__(self, team_name, channel_name, stream_type: StreamType):
        self.team_name = team_name
        self.channel_name = channel_name
        self.stream_type = stream_type

    def get_field_name(self, position):
        """Returns the field name based on stream type and position (1 or 2)"""
        return f"{self.stream_type.value}{position}"


def add_stream_channel(wikitext_in, team_name, channel_name, stream_type=StreamType.TWITCH):
    """
    Insère dynamiquement un lien de stream pour une équipe donnée.
    Si le type est YouTube, remplace le champ twitch correspondant par youtube.

    Args:
        wikitext_in: Le texte wiki à modifier
        team_name: Nom de l'équipe (ex: "France")
        channel_name: Nom de la chaîne (ex: "RocketBaguette")
        stream_type: Type de stream (StreamType.TWITCH ou StreamType.YOUTUBE)

    Returns:
        Le wikitext modifié
    """

    # Pattern pour trouver les matchs - s'arrête à la fermeture du Match
    # On utilise un lookahead pour s'arrêter avant le prochain "|M" ou avant "}}" seul sur une ligne
    match_pattern = (r'(\|M\d+={{Match\s+\|opponent1={{TeamOpponent\|([^|]+)\|[^}]*}}\s+\|opponent2={{TeamOpponent\|([^'
                     r'|]+)\|[^}]*}})(.*?)(}}(?=\n(?:\n|\|M|}})))')

    def replace_stream(match):
        prefix = match.group(1)
        opponent1 = match.group(2).strip()
        opponent2 = match.group(3).strip()
        middle_section = match.group(4)
        closing = match.group(5)

        # Déterminer la position de l'équipe
        position = None
        if opponent1 == team_name:
            position = 1
        elif opponent2 == team_name:
            position = 2
        else:
            # L'équipe n'est pas dans ce match
            return match.group(0)

        # Construire le nom du champ à modifier/ajouter
        field_name = f"{stream_type.value}{position}"

        # Chercher la ligne twitch1/twitch2 combinée
        combined_twitch_pattern = r'(\t\|twitch1=)([^\|]*)(\|twitch2=)([^\n]*)'
        combined_twitch_match = re.search(combined_twitch_pattern, middle_section)

        if combined_twitch_match:
            # Gérer le cas spécial de la ligne combinée twitch1=|twitch2=
            if stream_type == StreamType.TWITCH:
                # Pour Twitch, on modifie directement la ligne combinée
                def update_combined(m):
                    twitch1_val = m.group(2).strip()
                    twitch2_val = m.group(4).strip()

                    if position == 1:
                        # On veut modifier twitch1
                        if not twitch1_val:
                            return f"{m.group(1)}{channel_name}{m.group(3)}{twitch2_val}"
                        # Si twitch1 a déjà une valeur, ne rien faire
                        return m.group(0)
                    elif position == 2:
                        # On veut modifier twitch2
                        if not twitch2_val:
                            return f"{m.group(1)}{twitch1_val}{m.group(3)}{channel_name}"
                        # Si twitch2 a déjà une valeur, ne rien faire
                        return m.group(0)
                    return m.group(0)

                middle_section = re.sub(combined_twitch_pattern, update_combined, middle_section)
            else:
                # Pour YouTube, on remplace la ligne combinée par youtube
                def replace_with_youtube(m):
                    twitch1_val = m.group(2).strip()
                    twitch2_val = m.group(4).strip()

                    if position == 1:
                        # Remplacer twitch1 par youtube1 seulement si twitch1 est vide
                        if not twitch1_val:
                            return f"\t|youtube1={channel_name}|twitch2={twitch2_val}"
                        return m.group(0)
                    elif position == 2:
                        # Remplacer twitch2 par youtube2 seulement si twitch2 est vide
                        if not twitch2_val:
                            return f"\t|twitch1={twitch1_val}|youtube2={channel_name}"
                        return m.group(0)
                    return m.group(0)

                middle_section = re.sub(combined_twitch_pattern, replace_with_youtube, middle_section)
        else:
            # Pas de ligne combinée trouvée
            # Chercher le champ individuel
            field_pattern = rf'(\t\|{field_name}=)([^\n]*)'

            if re.search(field_pattern, middle_section):
                # Le champ existe, on le remplace s'il est vide
                def update_field(field_match):
                    current_value = field_match.group(2).strip()
                    if not current_value:
                        return f"{field_match.group(1)}{channel_name}"
                    return field_match.group(0)

                middle_section = re.sub(field_pattern, update_field, middle_section)

        return prefix + middle_section + closing

    return re.sub(match_pattern, replace_stream, wikitext_in, flags=re.DOTALL)


def process_multiple_teams(wikitext_in, stream_configs_list):
    """
    Traite plusieurs équipes avec leurs configurations de stream.

    Args:
        wikitext_in: Le texte wiki à modifier
        stream_configs_list: Liste de StreamConfig

    Returns:
        Le wikitext modifié
    """
    result = wikitext_in
    for config in stream_configs_list:
        result = add_stream_channel(result, config.team_name, config.channel_name, config.stream_type)
    return result


# Exemple d'utilisation
if __name__ == "__main__":
    # Lire le fichier wikitext
    with open('wikitext_input.txt', 'r', encoding='utf-8') as f:
        wikitext = f.read()

    # Configuration des streams pour différentes équipes
    stream_configs = [
        StreamConfig("Bosnia and Herzegovina", "noids7", StreamType.TWITCH),
    ]

    # Traiter toutes les équipes
    updated_wikitext = process_multiple_teams(wikitext, stream_configs)

    # Sauvegarder le résultat
    with open('wikitext_updated.txt', 'w', encoding='utf-8') as f:
        f.write(updated_wikitext)

    print("✓ Wikitext mis à jour avec succès!")
    print(f"✓ {len(stream_configs)} équipes traitées")
