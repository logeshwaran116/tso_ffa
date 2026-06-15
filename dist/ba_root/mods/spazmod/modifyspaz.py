from random import randint

import setting
from spazmod import tag
from spazmod import silence_bomb
import babase
import bascenev1 as bs

_setting = setting.get_settings_data()
silence_bomb.apply()

if _setting['enableeffects']:
    from spazmod import spaz_effects

    spaz_effects.apply()


def _is_the_spaz_game(activity) -> bool:
    """Return True when current activity is TheSpazGame."""
    if activity is None:
        return False
    try:
        if activity.__class__.__name__ == "TheSpazGame":
            return True
    except Exception:
        pass
    try:
        return getattr(activity, "name", None) == "TheSpazGame"
    except Exception:
        return False


def update_name():
    from stats import mystats
    stat = mystats.get_all_stats()
    ros = bs.get_game_roster()
    for i in ros:
        if i['account_id']:
            name = i['display_string']
            aid = i['account_id']
            if aid in stat:
                stat[aid]['name'] = name
    mystats.dump_stats(stat)


# all activites related to modify spaz by any how will be here


def main(spaz, node, player):
    # Re-apply to survive plugins replacing spaz/powerup methods at runtime.
    silence_bomb.apply()

    activity = None
    try:
        activity = spaz._activity()
    except Exception:
        try:
            activity = bs.get_foreground_host_activity()
        except Exception:
            activity = None

    hide_rank_tag = _is_the_spaz_game(activity)

    if _setting['enablehptag']:
        tag.addhp(node, spaz)
    if _setting['enabletags'] and not hide_rank_tag:
        tag.addtag(node, player)
    if _setting['enablerank'] and not hide_rank_tag:
        tag.addrank(node, player)
    if _setting["playermod"]['default_boxing_gloves']:
        spaz.equip_boxing_gloves()
    if _setting['playermod']['default_shield']:
        spaz.equip_shields()
    default_bomb = _setting['playermod']['default_bomb']
    custom_bombs = _setting.get("customBombs", {})
    if (
        default_bomb == "silence"
        and not custom_bombs.get("silence", {}).get("enable", True)
    ):
        default_bomb = "normal"
    if (
        default_bomb == "gravity"
        and not custom_bombs.get("gravity", {}).get("enable", True)
    ):
        default_bomb = "normal"
    spaz.bomb_type = default_bomb
    spaz.bomb_count = _setting['playermod']['default_bomb_count']
    # update_name()  will add threading here later . it was adding delay on game start


def getCharacter(player, character):
    if _setting["sameCharacterForTeam"]:

        if "character" in player.team.sessionteam.customdata:
            return player.team.sessionteam.customdata["character"]

    return character


def getRandomCharacter(otherthen):
    characters = list(babase.app.classic.spaz_appearances.keys())
    invalid_characters = ["Snake Shadow", "Lee", "Zola", "Butch", "Witch",
                          "Middle-Man", "Alien", "OldLady", "Wrestler",
                          "Gretel", "Robot"]

    while True:
        val = randint(0, len(characters) - 1)
        ch = characters[val]
        if ch not in invalid_characters and ch not in otherthen:
            return ch


def setTeamCharacter():
    if not _setting["sameCharacterForTeam"]:
        return
    used = []
    teams = bs.get_foreground_host_session().sessionteams
    if len(teams) < 10:
        for team in teams:
            character = getRandomCharacter(used)
            used.append(character)
            team.name = character
            team.customdata["character"] = character
