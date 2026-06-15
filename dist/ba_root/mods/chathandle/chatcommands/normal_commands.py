import _thread

import _babase
import _bascenev1
from stats import mystats

import bascenev1 as bs
from babase._general import Call
from .handlers import send

Commands = ['me', 'list', 'uniqeid', 'ping', 'efflist','cmdlist', 'pme']
CommandAliases = ['stats', 'score', 'rank',
                  'myself', 'l', 'id', 'pb-id', 'pb', 'accountid']


def ExcelCommand(command, arguments, clientid, accountid):
    """
    Checks The Command And Run Function

    Parameters:
        command : str
        arguments : str
        clientid : int
        accountid : int

    Returns:
        None
    """
    if command in ['me', 'stats', 'score', 'rank', 'myself']:
        fetch_send_stats(accountid, clientid)

    elif command in ['list', 'l']:
        list(clientid)

    elif command in ['uniqeid', 'id', 'pb-id', 'pb', 'accountid']:
        accountid_request(arguments, clientid, accountid)

    elif command in ['ping']:
        get_ping(arguments, clientid)
        
    elif command in ['efflist']:
        show_effect_list(clientid)

    elif command in ['cmdlist']:
        show_command_list(clientid)

        
    elif command in ['pme']:
        stats_to_clientid(arguments, clientid, accountid)


def get_ping(arguments, clientid):
    if arguments == [] or arguments == ['']:
        send(f"Your ping {_bascenev1.get_client_ping(clientid)}ms ", clientid)
    elif arguments[0] == 'all':
        pingall(clientid)
    else:
        try:
            session = bs.get_foreground_host_session()

            for index, player in enumerate(session.sessionplayers):
                name = player.getname(full=True, icon=False),
                if player.inputdevice.client_id == int(arguments[0]):
                    ping = _bascenev1.get_client_ping(int(arguments[0]))
                    send(f" {name}'s ping {ping}ms", clientid)
        except:
            return


def stats(ac_id, clientid):
    stats = mystats.get_stats_by_id(ac_id)
    if stats:
        reply = "Score:" + str(stats["scores"]) + "\nGames:" + str(
            stats["games"]) + "\nKills:" + str(
            stats["kills"]) + "\nDeaths:" + str(
            stats["deaths"]) + "\nAvg.:" + str(stats["avg_score"])
    else:
        reply = "Not played any match yet."

    _babase.pushcall(Call(send, reply, clientid), from_other_thread=True)


def fetch_send_stats(ac_id, clientid):
    _thread.start_new_thread(stats, (ac_id, clientid,))


def pingall(clientid):
    """Returns The List Of Players Clientid and index"""

    p = u'{0:^16}{1:^34}ms'
    seprator = '\n______________________________\n'

    list = p.format('Name', 'Ping (ms)') + seprator
    session = bs.get_foreground_host_session()

    for index, player in enumerate(session.sessionplayers):
        list += p.format(player.getname(icon=True),
                         _bascenev1.get_client_ping(
                             int(player.inputdevice.client_id))) + "\n"

    send(list, clientid)


def list(clientid):
    """Returns The List Of Players Clientid and index"""

    p = u'{0:^16}{1:^15}{2:^10}'
    seprator = '\n______________________________\n'

    list = p.format('Name', 'Client ID', 'Player ID') + seprator
    session = bs.get_foreground_host_session()

    for index, player in enumerate(session.sessionplayers):
        list += p.format(player.getname(icon=False),
                         player.inputdevice.client_id, index) + "\n"

    send(list, clientid)


def accountid_request(arguments, clientid, accountid):
    """Returns The Account Id Of Players"""

    if arguments == [] or arguments == ['']:
        send(f"Your account id is {accountid} ", clientid)

    else:
        try:
            session = bs.get_foreground_host_session()
            player = session.sessionplayers[int(arguments[0])]

            name = player.getname(full=True, icon=True)
            accountid = player.get_v1_account_id()

            send(f" {name}'s account id is '{accountid}' ", clientid)
        except:
            return


def show_effect_list(clientid):
    """Display all available effect names to the client"""
    effect_names = [
        "spark", "sparkground", "sweat", "sweatground", "distortion", 
        "glow", "shine", "highlightshine", "scorch", "ice", "iceground",
        "slime", "metal", "splinter", "rainbow", "fairydust", "firespark",
        "noeffect", "footprint", "fire", "darkmagic", "darksn", "stars",
        "aure", "orbguard", "chispitas", "surrounderhead"
    ]
    
    # Format the message with effects - 7 per line
    msg = "\ue046______________|AVAILABLE EFFECTS|________________\ue046\n"
    for i, effect in enumerate(effect_names, 1):
        if i % 7 == 1:  # Start new line every 7 effects
            msg += "\n\ue046 || " + effect
        else:
            msg += ', ' + effect
    
    send(msg, clientid)

def show_command_list(clientid):
    """Display all available effect names to the client"""
    effect_names = [
                 "kick",
                "remove", "rm", "end", "quit", "restart", "mute",
                 "unmute", "sm",
                "nv", "pause",
                "kill", "heal",
                "curse", "sleep", "gloves",
                "shield", "freeze", "thaw", "gm",
                "fly", "inv", "hl", "headless",
                "creep", "celeb","pme","say",
                "kickall","me", "list", "uniqeid", "ping", "efflist", "pme"]
    
    # Format the message with effects - 7 per line
    msg = "\ue046______________|COMMANDS LIST|________________\ue046\n"
    for i, effect in enumerate(effect_names, 1):
        if i % 7 == 1:  # Start new line every 7 effects
            msg += "\n\ue046 || " + effect
        else:
            msg += ', ' + effect
    
    send(msg, clientid)



def stats_to_clientid(arguments, clid, acid):
    activity = bs.get_foreground_host_activity()
    if arguments == [] or arguments == ['']:
        with bs.Context(activity):
         send(f"Using: /pme [Clientid of player]", clid)
    else:
        cl_id = int(arguments[0])
        for pla in bs.get_foreground_host_session().sessionplayers:
             if pla.inputdevice.client_id == cl_id:
                fname = pla.getname(full=True, icon=True)
        for roe in bs.get_game_roster():
             if roe["client_id"] == cl_id:
                pbid = roe["account_id"]
                stats = mystats.get_stats_by_id(pbid)  
                if stats:
                    reply = (
                        f"\ue048| Name: {fname}\n"
                        f"\ue048| PB-ID: {stats['aid']}\n"
                        f"\ue048| Rank: {stats['rank']}\n"
                        f"\ue048| Score: {stats['scores']}\n"
                        f"\ue048| Games: {stats['games']}\n"
                        f"\ue048| Kills: {stats['kills']}\n"
                        f"\ue048| Deaths: {stats['deaths']}\n"
                        f"\ue048| Avg.: {stats['avg_score']}\n"
                    )
                    send(reply, clid)
                else:
                    areply = "Not played any match yet."
                    send(areply, clid)