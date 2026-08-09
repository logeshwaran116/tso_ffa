"""Module to manage players data."""

# ba_meta require api 8
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import _thread
import copy
import json
import os
import shutil
import time
from datetime import datetime, timedelta

import _bascenev1
import setting
from serverdata import serverdata
from tools.server_update import checkSpammer
from tools.file_handle import OpenJson
from typing import TYPE_CHECKING

import babase
# pylint: disable=import-error
import bascenev1 as bs

if TYPE_CHECKING:
    pass

settings = setting.get_settings_data()

PLAYERS_DATA_PATH = os.path.join(
    babase.env()["python_directory_user"], "playersdata" + os.sep
)


class CacheData:  # pylint: disable=too-few-public-methods
    """Stores the cache data."""

    roles: dict = {}
    data: dict = {}
    custom: dict = {}
    profiles: dict = {}
    whitelist: list[str] = []
    blacklist: dict = {}

def get_info(account_id: str) -> dict | None:
    """Returns the information about player.

    Parameters
    ----------
    account_id : str
        account_id of the client

    Returns
    -------
    dict | None
        information of client
    """
    profiles = get_profiles()
    if account_id in profiles:
        return profiles[account_id]
    return None


def get_profiles() -> dict:
    """Returns the profiles of all players.

    Returns
    -------
    dict
        profiles of the players
    """
    if CacheData.profiles == {}:
        try:
            if os.stat(PLAYERS_DATA_PATH + "profiles.json").st_size > 5000000:
                newpath = f'{PLAYERS_DATA_PATH}profiles-{str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))}.json'
                shutil.copyfile(PLAYERS_DATA_PATH + "profiles.json", newpath)
                profiles = {"pb-sdf": {}}
                print("Resetting Profiles.")
            else:
                f = open(PLAYERS_DATA_PATH + "profiles.json", "r")
                profiles = json.load(f)
                f.close()
                print("Loading old profiles.json")
            CacheData.profiles = profiles

        except Exception as e:
            f = open(PLAYERS_DATA_PATH + "profiles.json.backup", "r")
            profiles = json.load(f)
            print(e)
            print("Exception occurred, falling back to profiles.json.backup")
            CacheData.profiles = profiles
            f.close()
            return profiles
    else:
        return CacheData.profiles


def get_profiles_archive_index():
    return [x for x in os.listdir(PLAYERS_DATA_PATH) if
            x.startswith("profiles")]


def get_old_profiles(filename):
    try:
        f = open(PLAYERS_DATA_PATH + filename, "r")
        profiles = json.load(f)
        return profiles
    except:
        return {}


def get_blacklist() -> dict:
    if CacheData.blacklist == {}:
        try:
            with open(PLAYERS_DATA_PATH + "blacklist.json", "r") as f:
                CacheData.blacklist = json.load(f)
        except:
            print('Error opening blacklist.json')
            return {
                "ban": {
                    "ids": {},
                    "ips": {},
                    "deviceids": {}
                },
                "muted-ids": {},
                "kick-vote-disabled": {}
            }

    return CacheData.blacklist


def update_blacklist():
    with open(PLAYERS_DATA_PATH + "blacklist.json", "w") as f:
        json.dump(CacheData.blacklist, f, indent=4)


def commit_profiles(data={}) -> None:
    """Commits the given profiles in the database.

    Parameters
    ----------
        profiles of all players
    """
    # with OpenJson(PLAYERS_DATA_PATH + "profiles.json") as profiles_file:
    #     profiles_file.dump(CacheData.profiles, indent=4)


def get_detailed_info(pbid):
    main_account = get_info(pbid)
    if main_account == None:
        return "No info"
    linked_accounts = ' '.join(main_account["display_string"])
    ip = main_account["lastIP"]
    deviceid = main_account["deviceUUID"]
    otheraccounts = ""
    dob = main_account["accountAge"]
    profiles = get_profiles()
    for key, value in profiles.items():
        if ("lastIP" in value and value["lastIP"] == ip) or (
                "deviceUUID" in value and value["deviceUUID"] == deviceid):
            otheraccounts += ' '.join(value["display_string"])
    return f"Accounts:{linked_accounts} \n other accounts {otheraccounts} \n created on {dob}"


def add_profile(
    account_id: str,
    display_string: str,
    current_name: str,
    account_age: int,
) -> None:
    """Adds the profile in database.

    Parameters
    ----------
    account_id : str
        account id of the client
    display_string : str
        display string of the client
    current_name : str
        name of the client
    account_age : int
        account_age of the account
    """
    profiles = get_profiles()
    profiles[account_id] = {
        "display_string": display_string,
        "profiles": [],
        "name": current_name,
        "accountAge": account_age,
        "registerOn": time.time(),
        "spamCount": 0,
        "lastSpam": time.time(),
        "totaltimeplayer": 0,
    }
    CacheData.profiles = profiles

    serverdata.clients[account_id] = profiles[account_id]
    serverdata.clients[account_id]["warnCount"] = 0
    serverdata.clients[account_id]["lastWarned"] = time.time()
    serverdata.clients[account_id]["verified"] = False
    serverdata.clients[account_id]["rejoincount"] = 1
    serverdata.clients[account_id]["lastJoin"] = time.time()
    cid = 113
    for ros in bs.get_game_roster():
        if ros['account_id'] == account_id:
            cid = ros['client_id']
    ip = _bascenev1.get_client_ip(cid)
    serverdata.clients[account_id]["lastIP"] = ip
    serverdata.recents.append(
        {"client_id": cid, "deviceId": display_string, "pbid": account_id})
    serverdata.recents = serverdata.recents[-20:]
    device_id = _bascenev1.get_client_public_device_uuid(cid)
    if (device_id == None):
        device_id = _bascenev1.get_client_device_uuid(cid)
    checkSpammer({'id': account_id, 'display': display_string,
                  'ip': ip, 'device': device_id})
    if device_id in get_blacklist()["ban"]["deviceids"] or account_id in \
            get_blacklist()["ban"]["ids"]:
        bs.disconnect_client(cid)
    serverdata.clients[account_id]["deviceUUID"] = device_id


def update_display_string(account_id: str, display_string: str) -> None:
    """Updates the display string of the account.

    Parameters
    ----------
    account_id : str
        account id of the client
    display_string : str
        new display string to be updated
    """
    profiles = get_profiles()
    if account_id in profiles:
        profiles[account_id]["display_string"] = display_string
        CacheData.profiles = profiles
        commit_profiles()


def update_profile(
    account_id: str,
    display_string: str = None,
    allprofiles: list[str] = None,
    name: str = None,
) -> None:
    """Updates the profile of client.

    Parameters
    ----------
    account_id : str
        account id of the client
    display_string : str, optional
        display string of the account, by default None
    allprofiles : list[str], optional
        all profiles of the client, by default None
    name : str, optional
        name to be updated, by default None
    """

    profiles = get_profiles()

    if profiles is None:
        return

    if account_id in profiles and display_string is not None:
        if display_string not in profiles[account_id]["display_string"]:
            profiles[account_id]["display_string"].append(display_string)

    if allprofiles is not None:
        for profile in allprofiles:
            if profile not in profiles[account_id]["profiles"]:
                profiles[account_id]["profiles"].append(profile)

    if name is not None:
        profiles[account_id]["name"] = name
    CacheData.profiles = profiles
    commit_profiles()


def ban_player(account_id: str, duration_in_days: float, reason: str) -> None:
    """Bans the player.

    Parameters
    ----------
    account_id : str
        account id of the player to be banned
    """
    # Do not allow banning protected accounts
    try:
        roles = get_roles()
        if account_id in roles.get("protected", {}).get("ids", []):
            return
    except Exception:
        pass

    # Do not allow banning protected players.
    try:
        roles = get_roles()
        if account_id in roles.get("protected", {}).get("ids", []):
            return
    except Exception:
        pass

    current_profiles = get_profiles()
    ip = ""
    device_id = ""
    if account_id in current_profiles:
        ip = current_profiles[account_id]["lastIP"]
        device_id = current_profiles[account_id]["deviceUUID"]

    ban_time = datetime.now() + timedelta(days=duration_in_days)

    CacheData.blacklist["ban"]["ips"][ip] = {"till": ban_time.strftime(
        "%Y-%m-%d %H:%M:%S"), "reason": f'linked with account {account_id}'}
    CacheData.blacklist["ban"]["ids"][account_id] = {
        "till": ban_time.strftime("%Y-%m-%d %H:%M:%S"), "reason": reason}
    CacheData.blacklist["ban"]["deviceids"][device_id] = {
        "till": ban_time.strftime(
            "%Y-%m-%d %H:%M:%S"), "reason": f'linked with account {account_id}'}
    _thread.start_new_thread(update_blacklist, ())


def unban_player(account_id):
    current_profiles = get_profiles()
    ip = ""
    device_id = ""
    if account_id in current_profiles:
        ip = current_profiles[account_id]["lastIP"]
        device_id = current_profiles[account_id]["deviceUUID"]
    else:
        for account in serverdata.recents:
            if account["pbid"] == account_id:
                ip = account["ip"]
                device_id = account["device_uuid"]

    CacheData.blacklist["ban"]["ips"].pop(ip, None)
    CacheData.blacklist["ban"]["deviceids"].pop(device_id, None)
    CacheData.blacklist["ban"]["ids"].pop(account_id, None)
    _thread.start_new_thread(update_blacklist, ())


def disable_kick_vote(account_id, duration, reason):
    ban_time = datetime.now() + timedelta(days=duration)
    CacheData.blacklist["kick-vote-disabled"][account_id] = {
        "till": ban_time.strftime(
            "%Y-%m-%d %H:%M:%S"), "reason": reason}
    _thread.start_new_thread(update_blacklist, ())


def enable_kick_vote(account_id):
    CacheData.blacklist["kick-vote-disabled"].pop(account_id, None)
    _thread.start_new_thread(update_blacklist, ())


def mute(account_id: str, duration_in_days: float, reason: str) -> None:
    """Mutes the player.

    Parameters
    ----------
    account_id : str
        acccount id of the player to be muted
    """
    # Do not allow muting protected accounts
    try:
        roles = get_roles()
        if account_id in roles.get("protected", {}).get("ids", []):
            return
    except Exception:
        pass
    # Do not allow muting protected players.
    try:
        roles = get_roles()
        if account_id in roles.get("protected", {}).get("ids", []):
            return
    except Exception:
        pass

    ban_time = datetime.now() + timedelta(days=duration_in_days)

    CacheData.blacklist["muted-ids"][account_id] = {"till": ban_time.strftime(
        "%Y-%m-%d %H:%M:%S"), "reason": reason}
    _thread.start_new_thread(update_blacklist, ())


def unmute(account_id: str) -> None:
    """Unmutes the player.

    Parameters
    ----------
    account_id : str
        acccount id of the player to be unmuted
    """
    CacheData.blacklist["muted-ids"].pop(account_id, None)
    _thread.start_new_thread(update_blacklist, ())


def update_spam(account_id: str, spam_count: int, last_spam: float) -> None:
    """Updates the spam time and count.

    Parameters
    ----------
    account_id : str
        account id of the client
    spam_count : int
        spam count to be added
    last_spam : float
        last spam time
    """
    profiles = get_profiles()
    if account_id in profiles:
        profiles[account_id]["spamCount"] = spam_count
        profiles[account_id]["lastSpam"] = last_spam
        CacheData.profiles = profiles
        commit_profiles(profiles)


def commit_roles(data: dict) -> None:
    """Commits the roles in database.

    Parameters
    ----------
    data : dict
        data to be commited
    """
    if not data:
        return

    # with OpenJson(PLAYERS_DATA_PATH + "roles.json") as roles_file:
    #     roles_file.format(data)


def get_roles() -> dict:
    """Returns the roles.

    Returns
    -------
    dict
        roles
    """
    if CacheData.roles == {}:
        try:
            f = open(PLAYERS_DATA_PATH + "roles.json", "r")
            roles = json.load(f)
            f.close()
            CacheData.roles = roles
        except Exception as e:
            print(e)
            f = open(PLAYERS_DATA_PATH + "roles.json.backup", "r")
            roles = json.load(f)
            f.close()
            CacheData.roles = roles

    try:
        #adding default roles
        default_roles = {
            'owner': ["\\c OWNER \\c", 20, [1,1,1],[],[]],
            'moderator': ["\\d MODERATOR \\d", 18, [1,1,1],[],[]],
            'cs': ["\\n COMPLIENT STAFF \\n", 16, [1,1,1],[],[]],
            'leadstaff': ["\\f LEAD STAFF \\f", 16, [1,1,1],[],[]],
            'admin': ["\\bs ADMIN \\bs", 13, [1,1,1],[],[]],
            'vip':["\\bs VIP \\bs", 11, [1,1,1],[],[]],
            'protected': ["\\l PROTECTED \\l", 11, [1,1,1],[],[]],
            "bypass-warn": ["", 1,[1,1,1],[],[]],
            "top5":["EliteFive", 15, [1,1,1],[],[]]
        }
        for role_name, values in default_roles.items():
            role_dict = CacheData.roles.setdefault(role_name, {})
            role_dict.setdefault("tag", values[0])
            role_dict.setdefault("anim_id", values[1])
            role_dict.setdefault("tagcolor", values[2])
            role_dict.setdefault("commands", values[3])
            role_dict.setdefault("ids", values[4])

    except Exception:
        pass
    return CacheData.roles


def create_role(role: str) -> None:
    """Ceates the role.

    Parameters
    ----------
    role : str
        role to be created
    """
    roles = get_roles()

    if role in roles:
        return

    roles[role] = {
        "tag": role,
        "tagcolor": [1, 1, 1],
        "anim_id": 1,
        "commands": [],
        "ids": [],
    }
    CacheData.roles = roles
    commit_roles(roles)


def add_player_role(role: str, account_id: str) -> None:
    """Adds the player to the role.

    Parameters
    ----------
    role : str
        role to be added
    account_id : str
        account id of the client
    """
    roles = get_roles()

    if role in roles:
        if account_id not in roles[role]["ids"]:
            roles[role]["ids"].append(account_id)
            CacheData.roles = roles
            commit_roles(roles)

    else:
        bs.chatmessage(f"Role {role} doesn't exist")


def remove_player_role(role: str, account_id: str) -> str:
    """Removes the role from player.

    Parameters
    ----------
    role : str
        role to br removed
    account_id : str
        account id of the client

    Returns
    -------
    str
        status of the removing role
    """
    roles = get_roles()
    if role in roles:
        roles[role]["ids"].remove(account_id)
        CacheData.roles = roles
        commit_roles(roles)
        return "removed from " + role
    return "role not exists"


def add_command_role(role: str, command: str) -> str:
    """Adds the command to the role.

    Parameters
    ----------
    role : str
        role to add the command
    command : str
        command to be added

    Returns
    -------
    str
        status of the adding command
    """
    roles = get_roles()
    if role in roles:
        if command not in roles[role]["commands"]:
            roles[role]["commands"].append(command)
            CacheData.roles = roles
            commit_roles(roles)
            return "command added to " + role
    return "command not exists"


def remove_command_role(role: str, command: str) -> str:
    """Removes the command from the role.

    Parameters
    ----------
    role : str
        role to remove command from
    command : str
        command to be removed

    Returns
    -------
    str
        status of the removing command
    """
    roles = get_roles()
    if role in roles:
        if command in roles[role]["commands"]:
            roles[role]["commands"].remove(command)
            CacheData.roles = roles
            commit_roles(roles)
            return "command added to " + role
    return "command not exists"


def change_role_tag(role: str, tag: str, anim_id:int = None) -> str:
    """Changes the tag of the role.

    Parameters
    ----------
    role : str
        role to chnage the tag
    tag : str
        tag to be added

    Returns
    -------
    str
        status of the adding tag
    """
    roles = get_roles()
    if role in roles:
        roles[role]["tag"] = tag
        if anim_id:
            roles[role]["anim_id"] = anim_id
        CacheData.roles = roles
        commit_roles(roles)
        bs.chatmessage(f"role {role} tag changed to {tag}")
        return
    bs.chatmessage(f"Role {role} doesn't exist")
    return

def change_role_anim(role:str, anim_id:int) ->str:
    '''Changes the tag anim of a role
    returns status of job'''
    try:
        roles = get_roles()
        if role in roles:
            if anim_id in range(1,21):
                roles[role]["anim_id"] = anim_id
                CacheData.roles = roles
                commit_roles(roles)
                bs.chatmessage(f"role '{role}' animation changed to ID = {anim_id}")
            else:
                bs.chatmessage("Invalid input — anim ID should be 1 to 20.")
        else:
            bs.chatmessage(f"Role '{role}' does not exists")
    except Exception:
        import traceback
        traceback.print_exc()

def change_custom_anim(account_id, anim_id):
    try:
        custom = get_custom()
        p = custom.get('customtag', {}).get(account_id,{})
        if not p:
            bs.chatmessage(f"Player Doesn't have a custom tag. Add one with /ct")
            return
        if anim_id not in range(1,21):
            bs.chatmessage("Invalid input — anim ID should be 1 to 20.")
            return
        p["anim_id"] = anim_id
        CacheData.custom = custom
        commit_c()
        bs.chatmessage(f"Customtag animation changed successfully")
        return
    except Exception:
        bs.chatmessage(f"Error changing tag animation")
        return

def buy_tag_tagpass(client_id: int, account_id:str, tag: str, anim_id:int):
    try:
        custom = get_custom()
        tag_pass = custom["tagpass"]
        if not tag_pass.get(account_id, None):
            bs.chatmessage(f"You don't have valid tagpass buy one from shop use:/shop buy tagpass", clients=[client_id])
            return
        if tag_pass.get(account_id, {}).get("used", False):
            bs.chatmessage(f"Tag pass already used", clients=[client_id])
            return
        if anim_id not in range(1, 13):
            bs.chatmessage(f"Invalid input — tagpass anim ID should be 1 to 12.")
            return
        paid_tag = custom["paidtags"]
        paid_tag[account_id] = {
            "tag": tag,
            "anim_id": anim_id,
            "expires_at": tag_pass.get(account_id, {}).get("expires_at", time.time() + 24*60*60),
        }
        tag_pass[account_id]["used"] = True
        bs.chatmessage(f"Tag added successfully for 1 day", clients=[client_id])
        CacheData.custom = custom
        commit_c()
    except Exception:
        import traceback
        traceback.print_exc()

#reformed. use this in tag.py instead of function from coin.so
#reformed for adding anim_id
#edited by sanji
def get_paid_tag(account_id: str):
    custom = get_custom()
    paid_tag = custom.get("paidtags", {}).get(account_id)
    if not paid_tag:
        return None, None
    return paid_tag.get("tag"), paid_tag.get("anim_id")


def get_player_roles(account_id: str) -> list[str]:
    """Returns the avalibe roles of the account.

    Parameters
    ----------
    account_id : str
        account id of the client

    Returns
    -------
    list[str]
        list of the roles
    """

    roles = get_roles()
    have_roles = []
    for role in roles:
        if account_id in roles[role]["ids"]:
            have_roles.append(role)
    return have_roles


def is_protected(account_id: str) -> bool:
    """Return True if account has the 'protected' role.

    Protected players are immune to kick/ban/mute and kick-votes.
    """
    try:
        roles = get_roles()
        return account_id in roles.get("protected", {}).get("ids", [])
    except Exception:
        return False


def get_custom() -> dict:
    """Returns the custom effects.

    Returns
    -------
    dict
        custom effects
    """
    if CacheData.custom == {}:
        try:
            f = open(PLAYERS_DATA_PATH + "custom.json", "r")
            custom = json.load(f)
            f.close()
            CacheData.custom = custom
        except:
            f = open(PLAYERS_DATA_PATH + "custom.json.backup", "r")
            custom = json.load(f)
            f.close()
            CacheData.custom = custom
        # Ensure required keys exist
        CacheData.custom.setdefault("customeffects", {})
        CacheData.custom.setdefault("customtag", {})
        # Normalize any string entries to list
        for account_id in list(CacheData.custom["customeffects"].keys()):
            val = CacheData.custom["customeffects"][account_id]
            CacheData.custom["customeffects"][account_id] = [val] if isinstance(val, str) else val

        # Normalize customtag values (string → dict)
        for account_id, val in list(CacheData.custom["customtag"].items()):
            if isinstance(val, str):
                CacheData.custom["customtag"][account_id] = {
                    "tag": val,
                    "anim_id": 1 #default 1
                }

    return CacheData.custom


def set_effect(effect: str, account_id: str, username: str) -> None:
    """Sets the custom effect for the player.

    Parameters
    ----------
    effect : str
        Effect to be added to the player.
    account_id : str
        Account ID of the client.
    username : str
        Username of the client.
    """
    try:
        custom = get_custom()
        customeffects = custom.setdefault("customeffects", {})
        eff = customeffects.setdefault(account_id, [])

        if effect in eff:
            bs.chatmessage(f"Effect '{effect}' is already applied to {username}")
            return
        elif len(eff) >= 2:
            bs.chatmessage(f"Max 2 effects allowed; '{effect}' not added for {username}")
            return
        eff.append(effect)
        bs.chatmessage(f"Effect '{effect}' added to {username}")
        CacheData.custom = custom
        commit_c()
    except Exception:
        bs.chatmessage("Error adding custom effect")


def set_tag(tag: str, account_id: str, anim_id: int) -> None:
    """Sets the custom tag to the player.

    Parameters
    ----------
    tag : str
        tag to be added to the player
    account_id : str
        account id of the client
    """
    custom = get_custom()
    custom["customtag"][account_id] = {'tag': tag, 'anim_id': anim_id}
    CacheData.custom = custom
    commit_c()


def update_roles(roles):
    CacheData.roles = roles


def get_custom_perks():
    return CacheData.custom


def update_custom_perks(custom):
    CacheData.custom = custom


def remove_effect(account_id: str, effect: str | None, username: str) -> None:
    """Removes the effect from a player."""
    try:
        custom = get_custom()
        ce = custom.get("customeffects", {})
        eff = ce.get(account_id, [])

        if not effect:
            ce.pop(account_id, None)
            bs.chatmessage(f"All effects removed from {username}")
        elif effect in eff:
            eff.remove(effect)
            bs.chatmessage(f"Effect '{effect}' removed from {username}")
        else:
            bs.chatmessage(f"{username} doesn't have the effect '{effect}'")

        CacheData.custom = custom
        commit_c()
    except Exception:
        bs.chatmessage(f"Error removing effect for {username}")

def show_effect(account_id: str, username: str) -> None:
    """Shows the effects of a player."""
    try:
        custom = get_custom()
        effects = custom.get("customeffects", {}).get(account_id, [])

        if not effects:
            bs.chatmessage(f"{username} doesn't have any effects")
            return

        bs.chatmessage(f"{username}'s effects: " + ", ".join(effects))
    except Exception as e:
        bs.chatmessage(f"Unable to fetch {username}'s effects")



def remove_tag(account_id: str) -> None:
    """Removes the tag from the player

    Parameters
    ----------
    account_id : str
        account id of the client
    """
    custom = get_custom()
    custom["customtag"].pop(account_id)
    CacheData.custom = custom


def commit_c():
    """Commits the custom data into the custom.json."""
    # with OpenJson(PLAYERS_DATA_PATH + "custom.json") as custom_file:
    #     custom_file.dump(CacheData.custom, indent=4)


def update_toppers(topper_list: list[str]) -> None:
    """Updates the topper list into top5 role.

    Parameters
    ----------
    topper_list : list[str]
        list of the topper players
    """
    roles = get_roles()
    if "top5" not in roles:
        create_role("top5")
    CacheData.roles["top5"]["ids"] = topper_list
    commit_roles(roles)


def load_white_list() -> None:
    """Loads the whitelist."""
    with OpenJson(PLAYERS_DATA_PATH + "whitelist.json") as whitelist_file:
        data = whitelist_file.load()
        for account_id in data:
            CacheData.whitelist.append(account_id)


def load_cache():
    """ to be called on server boot"""
    get_profiles()
    get_custom()
    get_roles()


def dump_cache():
    if CacheData.profiles != {}:
        shutil.copyfile(PLAYERS_DATA_PATH + "profiles.json",
                        PLAYERS_DATA_PATH + "profiles.json.backup")
        profiles = copy.deepcopy(CacheData.profiles)
        with open(PLAYERS_DATA_PATH + "profiles.json", "w") as f:
            json.dump(profiles, f, indent=4)
    if CacheData.roles != {}:
        shutil.copyfile(PLAYERS_DATA_PATH + "roles.json",
                        PLAYERS_DATA_PATH + "roles.json.backup")
        roles = copy.deepcopy(CacheData.roles)
        with open(PLAYERS_DATA_PATH + "roles.json", "w") as f:
            json.dump(roles, f, indent=4)
    if CacheData.custom != {}:
        shutil.copyfile(PLAYERS_DATA_PATH + "custom.json",
                        PLAYERS_DATA_PATH + "custom.json.backup")
        custom = copy.deepcopy(CacheData.custom)
        with open(PLAYERS_DATA_PATH + "custom.json", "w") as f:
            json.dump(custom, f, indent=4)
    time.sleep(60)
    dump_cache()

# ----- coin system ----

#add coin to a account
def add_coins(account_id, amount):
    custom = get_custom()
    coins:dict = custom.setdefault("coins",{})
    p_coin = coins.setdefault(account_id, 0)
    p_coin += int(amount)
    if p_coin < 0:
        p_coin = 0
    CacheData.custom = custom
    commit_c()



#match winning reward
def reward_for_winning(session, winning_team):
    try:
        if winning_team is None:
            return

        reward = 20
        announcement = "\ue043 🎉 Victory Rewards 🎉 \ue043\n"
        reward_sent = False

        for player in winning_team.players:
            acc_id = player.get_v1_account_id()

            if acc_id:
                add_coins(acc_id, reward)
                name = player.getname(icon=False)
                announcement += f"✨ {name} earned {reward} coins! ✨\n"
                reward_sent = True

        if reward_sent:
            bs.broadcastmessage(announcement, color=(0, 1, 0))

    except Exception as e:
        print(f"Coin Reward Error: {e}")
        import traceback
        traceback.print_exc()

def top_cashers(limit:int = 10):
    custom = get_custom()
    coins_data = custom.get("coins", {})
    if not coins_data:
        return "No data to show"
    profiles = get_profiles()
    top_list = sorted(coins_data.items(),key= lambda x: x[1], reverse= True)[:limit]

    lines = [f"\ue01d ---- RICHEST PLAYERS ---- \ue01d"]
    for i, (aid, coins) in enumerate(top_list):
        if coins == 0:
            break
        name = profiles.get(aid,{}).get("name",aid)
        lines.append(f"{i+1}. {name} -- \ue01d {coins}")
    if len(lines) > 1:
        msg = "\n".join(lines)
        return msg
    return "No data to show"


def _medal(rank: int) -> str:
    return ['🥇', '🥈', '🥉'][rank] if rank < 3 else f'#{rank + 1}'


def _name(entry: dict, aid: str) -> str:
    n = entry.get('name', aid)
    if not n or n in ('default name', 'default'):
        n = aid[:12]
    # Strip to max 18 chars
    return n[:18]


def top_players(limit: int = 10):
    try:
        from stats.mystats import get_all_stats
    except Exception:
        import traceback
        traceback.print_exc()
        return "Error fetching player stats."

    stats = get_all_stats()
    if not stats:
        return "No data to show"

    players = list(stats.values())
    top_kills = sorted(players, key=lambda p: p.get('kills', 0), reverse=True)[:limit]
    lines = [f"\ue048 ---- TOP PLAYERS ---- \ue048"]
    for i, p in enumerate(top_kills):
        kills = p.get('kills', 0)
        if kills == 0:
            break
        lines.append(f"{_medal(i)}. {_name(p, p.get('aid','?'))} -- {kills:,} kills")

    if len(lines) > 1:
        return "\n".join(lines)
    return "No data to show"



def rank_zone(aid: str):
    try:
        from stats.mystats import get_all_stats
    except Exception:
        import traceback
        traceback.print_exc()
        return "Error fetching rankings."

    stats = get_all_stats()
    players = list(stats.values())

    sorted_players = sorted(players, key=lambda p: p.get('kills', 0), reverse=True)

    idx = next((i for i, p in enumerate(sorted_players) if p.get('aid') == aid), None)
    if idx is None:
        return "You are not yet played"

    start = max(0, idx - 3)
    end = min(len(sorted_players), idx + 4)

    window = sorted_players[start:end]

    lines = ["🏆 ---- PLAYER RANK WINDOW ---- 🏆"]
    for i, p in enumerate(window, start=start + 1):
        kills = p.get('kills', 0)
        lines.append(f"{i}. {_name(p, p.get('aid','?'))} -- {kills:,} kills")

    return "\n".join(lines)


def player_info(account_id:str):
    data = get_info(account_id)
    if data:
        linked_accounts = data['name']
        dob = data["accountAge"]
        ts = datetime.strptime(dob, "%Y-%m-%d %H:%M:%S").timestamp()       
        otheraccounts = ', '.join(data["display_string"])
        return f"Accounts:{linked_accounts} \nother accounts {otheraccounts} \ncreated on <t:{int(ts)}:f>"
    return None


def player_noeffect(account_id:str):
    custom = get_custom()
    ce:dict = custom.get("paideffects",{})
    ce.pop(account_id)
    CacheData.custom = custom
    commit_c()