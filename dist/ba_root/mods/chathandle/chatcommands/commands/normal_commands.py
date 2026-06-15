import _thread

import _babase
import _bascenev1
from stats import mystats
from tools import coins
from playersdata import pdata

import bascenev1 as bs
from babase._general import Call
from .handlers import send
import setting

Commands = [
    'me', 'list', 'uniqeid', 'ping', 'efflist', 'cmdlist', 'pme', 'help',
    'coins', 'wallet', 'claim', 'convert', 'transfer', 'shop', 'coinhelp',
    'tag', 'save', 'savelist', 'rmsave', 'chatlist', 'setmsg', 'sap',
    'comp', 'la',
]
CommandAliases = ['stats', 'score', 'rank',
                  'myself', 'l', 'id', 'pb-id', 'pb', 'accountid',
                  'linkedaccount', 'linkedaccounts']


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

    elif command in ['help']:
        show_normal_help(clientid)

        
    elif command in ['pme']:
        stats_to_clientid(arguments, clientid, accountid)

    # Coin economy (everyone)
    elif command in ['coins', 'wallet']:
        show_wallet(accountid, clientid)

    elif command in ['claim']:
        claim_daily(accountid, clientid)

    elif command in ['convert']:
        convert_score(arguments, accountid, clientid)

    elif command in ['transfer']:
        transfer_coins(arguments, accountid, clientid)

    elif command in ['shop']:
        shop_command(arguments, accountid, clientid)

    elif command in ['coinhelp']:
        coin_help(clientid)

    elif command in ['tag']:
        tag_command(arguments, accountid, clientid)

    elif command in ['save']:
        save_friend(arguments, accountid, clientid)

    elif command in ['savelist']:
        savelist_command(accountid, clientid)

    elif command in ['chatlist']:
        chatlist_command(arguments, clientid)

    elif command in ['rmsave']:
        rmsave_command(arguments, accountid, clientid)

    elif command in ['setmsg']:
        set_join_message_command(arguments, accountid, clientid)

    elif command in ['sap']:
        show_available_playlists(clientid)

    elif command in ['comp']:
        complaint_command(arguments, clientid, accountid)

    elif command in ['la', 'linkedaccount', 'linkedaccounts']:
        linked_accounts_command(arguments, clientid)


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
    try:
        balance = coins.get_balance(ac_id)
    except Exception:
        balance = 0
    if stats:
        reply = (
            f"Coins: {balance}\n"
            f"Score:{stats['scores']}\n"
            f"Games:{stats['games']}\n"
            f"Kills:{stats['kills']}\n"
            f"Deaths:{stats['deaths']}\n"
            f"Avg.:{stats['avg_score']}"
        )
    else:
        reply = f"Coins: {balance}\nNot played any match yet."

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


def _get_linked_accounts_summary(pbid: str) -> str:
    """Build linked-account summary using shared IP/device + aliases."""
    if not pbid:
        return "No PBID available."
    try:
        info = pdata.get_info(pbid)
        if not isinstance(info, dict):
            return f"No profile data found for {pbid}."

        aliases_raw = info.get("display_string", [])
        if isinstance(aliases_raw, str):
            aliases = [aliases_raw]
        elif isinstance(aliases_raw, list):
            aliases = [str(x).strip() for x in aliases_raw if str(x).strip()]
        else:
            aliases = []

        last_ip = info.get("lastIP")
        device_uuid = info.get("deviceUUID")
        linked_rows = []
        profiles = pdata.get_profiles() or {}

        for other_pbid, other in profiles.items():
            if other_pbid == pbid or not isinstance(other, dict):
                continue
            same_ip = bool(last_ip) and other.get("lastIP") == last_ip
            same_device = bool(device_uuid) and other.get("deviceUUID") == device_uuid
            if not (same_ip or same_device):
                continue
            other_name = other.get("name")
            if not other_name:
                ds = other.get("display_string")
                if isinstance(ds, list) and ds:
                    other_name = ds[0]
                elif isinstance(ds, str):
                    other_name = ds
            linked_rows.append(f"{other_name or 'Unknown'} ({other_pbid})")

        linked_rows = list(dict.fromkeys(linked_rows))
        if len(linked_rows) > 8:
            shown = ", ".join(linked_rows[:8]) + f", +{len(linked_rows) - 8} more"
        else:
            shown = ", ".join(linked_rows) if linked_rows else "None"
        alias_text = ", ".join(aliases[:8]) if aliases else "None"

        return f"Aliases: {alias_text}\nOther linked PBIDs: {shown}"
    except Exception as exc:
        return f"Could not load linked accounts: {exc}"


def linked_accounts_command(arguments, clientid: int) -> None:
    """Usage: /la <clientid>."""
    if not arguments:
        send("Usage: /la <clientid>", clientid)
        return
    try:
        target_cid = int(arguments[0])
    except Exception:
        send("First argument must be a client id number.", clientid)
        return

    target_ros = None
    try:
        for ros in bs.get_game_roster():
            if ros.get("client_id") == target_cid:
                target_ros = ros
                break
    except Exception:
        pass

    if target_ros is None:
        send("Player with that client id was not found in roster.", clientid)
        return

    target_name = target_ros.get("display_string") or "Unknown"
    target_pbid = target_ros.get("account_id")
    if not target_pbid:
        send(f"Could not resolve PBID for {target_name}.", clientid)
        return

    summary = _get_linked_accounts_summary(target_pbid)
    send(f"{target_name} ({target_pbid})\n{summary}", clientid)


def show_effect_list(clientid):
    """Display all available effect names to the client."""
    effect_names = [
        "spark", "sparkground", "sweat", "sweatground", "distortion",
        "glow", "shine", "highlightshine", "scorch", "ice", "iceground",
        "slime", "metal", "splinter", "rainbow", "fairydust", "firespark",
        "noeffect", "footprint", "fire", "darkmagic", "darksn", "stars",
        "aure", "orbguard", "chispitas", "surrounderhead",
        "randblink", "randomcharacter"
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
                "kickall","me", "list", "uniqeid", "ping", "efflist", "pme",
                "coins","wallet","claim","convert","transfer","shop","la"]
    
    # Format the message with effects - 7 per line
    msg = "\ue046______________|COMMANDS LIST|________________\ue046\n"
    for i, effect in enumerate(effect_names, 1):
        if i % 7 == 1:  # Start new line every 7 effects
            msg += "\n\ue046 || " + effect
        else:
            msg += ', ' + effect
    
    send(msg, clientid)


def show_normal_help(clientid):
    """Show all normal_commands (Commands list) nicely formatted."""
    try:
        from . import normal_commands as _nc
        cmds = list(_nc.Commands)
    except Exception:
        cmds = []
    if not cmds:
        send("No commands available.", clientid)
        return
    # 7 per line formatting similar to efflist
    msg = "\ue046______________|HELP - NORMAL COMMANDS|________________\ue046\n"
    for i, name in enumerate(cmds, 1):
        if i % 7 == 1:
            msg += "\n\ue046 || " + name
        else:
            msg += ", " + name
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
                    # Resolve roles
                    try:
                        from playersdata import pdata
                        roles = pdata.get_player_roles(pbid)
                        role_text = ",".join(roles) if roles else "none"
                    except Exception:
                        role_text = "none"
                    reply = (
                        f"\ue048| Name: {fname}\n"
                        f"\ue048| PB-ID: {stats['aid']}\n"
                        f"\ue048| Role: {role_text}\n"
                        f"\ue048| Rank: {stats['rank']}\n"
                        f"\ue048| Score: {stats['scores']}\n"
                        f"\ue048| Games: {stats['games']}\n"
                        f"\ue048| Kills: {stats['kills']}\n"
                        f"\ue048| Deaths: {stats['deaths']}\n"
                        f"\ue048| Avg.: {stats['avg_score']}\n"
                        f"\ue048| Coins: {coins.get_balance(pbid)}\n"
                    )
                    send(reply, clid)
                else:
                    areply = "Not played any match yet."
                    send(areply, clid)


def show_wallet(account_id: str, clientid: int) -> None:
    try:
        bal = coins.get_balance(account_id)
        custom = coins.pdata.get_custom()
        banked = int(custom.get('score_bank', {}).get(account_id, 0))
        active = coins.get_active_effect(account_id) or 'None'
        reply = (
            f"\ue048 Coins: {bal}\n"
            f"\ue048 Banked score: {banked}\n"
            f"\ue048 Active effect: {active}"
        )
        send(reply, clientid)
    except Exception:
        send("Wallet unavailable right now.", clientid)


def claim_daily(account_id: str, clientid: int) -> None:
    res = coins.claim_daily_join(account_id, reward=50)
    send(res.message, clientid)


def convert_score(arguments, account_id: str, clientid: int) -> None:
    # Business rule: when a number is provided, convert that many 'points' at 20% yield from banked score.
    # If omitted, default to convert all at 20%.
    custom = coins.pdata.get_custom()
    banked = int(custom.get('score_bank', {}).get(account_id, 0))
    if arguments and arguments[0] not in ['', None]:
        try:
            requested = int(float(arguments[0]))
        except Exception:
            requested = 0
        if requested <= 0 or banked < requested:
            send(f"insufficient score. your score is {banked}", clientid)
            return
        # Convert exactly 'requested' from banked at 20% yield
        # Temporarily adjust bank then convert that slice only
        custom['score_bank'][account_id] = banked - requested
        coins.pdata.CacheData.custom = custom
        added, new_bal = coins.convert_score_to_coins(account_id, ratio=0.2)
        send(f"Converted {added}. New balance: {new_bal}", clientid)
        return
    # No argument: convert all banked at 20%
    added, new_bal = coins.convert_score_to_coins(account_id, ratio=0.2)
    send(f"Converted {added}. New balance: {new_bal}", clientid)


def _resolve_account_id_from_arg(arg: str) -> str | None:
    # Accept direct pb-id
    if isinstance(arg, str) and arg.startswith('pb-'):
        return arg
    # Try as client-id
    try:
        cid = int(arg)
        for ros in bs.get_game_roster():
            if int(ros.get('client_id', -1)) == cid:
                return ros.get('account_id')
    except Exception:
        pass
    # Try as session index
    try:
        idx = int(arg)
        session = bs.get_foreground_host_session()
        player = session.sessionplayers[idx]
        return player.get_v1_account_id()
    except Exception:
        return None


def transfer_coins(arguments, from_account: str, clientid: int) -> None:
    if not arguments or len(arguments) < 2:
        send("Usage: transfer <pb-id|clientid|index> <amount>", clientid)
        return
    to_arg, amount_arg = arguments[0], arguments[1]
    to_acc = _resolve_account_id_from_arg(to_arg)
    if not to_acc:
        send("Could not resolve recipient. Use pb-id or client id.", clientid)
        return
    try:
        amount = int(amount_arg)
    except Exception:
        send("Amount must be a number.", clientid)
        return
    res = coins.transfer(from_account, to_acc, amount)
    send(res.message, clientid)


def shop_command(arguments, account_id: str, clientid: int) -> None:
    EFFECT_PRICES = {
        'stars': 1500,
        'rainbow': 1200,
        'surrounder': 1800,
        'surrounderhead': 2500,
        'tagpass': 2000,
        'spark': 600,
        'glow': 600,
        'shine': 550,
        'metal': 500,
        'iceground': 600,
    }
    if not arguments or arguments[0] in ['', None, 'list']:
        lines = [f"\ue048 {k}: {v}" for k, v in EFFECT_PRICES.items()]
        msg = "\ue048 Shop (1-day items):\n" + "\n".join(lines)
        send(msg, clientid)
        return
    if arguments[0] == 'buy':
        if len(arguments) < 2:
            send("Usage: shop buy <effect|tagpass>", clientid)
            return
        eff = arguments[1].lower()
        if eff not in EFFECT_PRICES:
            send("Unknown effect. Try 'shop list'", clientid)
            return
        if eff == 'tagpass':
            res = coins.buy_tag_pass(account_id, price=EFFECT_PRICES[eff], days=1.0)
            if res.ok:
                send("Tag pass purchased. Use /tag <text> once within 1 day.", clientid)
            else:
                send(res.message, clientid)
        else:
            res = coins.buy_effect(account_id, eff, price=EFFECT_PRICES[eff], days=1.0)
            if res.ok:
                send(f"Effect '{eff}' added for 1 day.", clientid)
            else:
                send(res.message, clientid)
        return
    send("Usage: shop list | shop buy <effect|tagpass>", clientid)


def coin_help(clientid: int) -> None:
    lines = [
        "/coins — Show coins, banked score, effect",
        "/claim — Claim daily reward",
        "/convert [ratio] — Convert banked score",
        "/transfer <pb-id|clientid|index> <amount>",
        "/shop list — View items",
        "/shop buy tagpass — Buy 1-day tag pass",
        "/shop buy <effect> — Buy 1-day effect",
        "/tag <text> — Use tag pass once",
    ]
    reply = "\n".join([f"\ue048 {s}" for s in lines])
    send(reply, clientid)


def tag_command(arguments, account_id: str, clientid: int) -> None:
    if not arguments:
        send("Usage: /tag <text>", clientid)
        return
    tag_text = " ".join([a for a in arguments if a is not None]).strip()
    if not tag_text:
        send("Usage: /tag <text>", clientid)
        return
    res = coins.consume_tag_pass(account_id, tag_text)
    if res.ok:
        send("Tag added successfully for 1 day.", clientid)
    else:
        send(res.message, clientid)


def save_friend(arguments, account_id: str, clientid: int) -> None:
    # Usage: /save <any-name> <pbid>
    if not arguments or len(arguments) < 2:
        send("Usage: /save <name> <pb-id>", clientid)
        return
    name = arguments[0]
    pbid = arguments[1]
    try:
        from playersdata import pdata
        custom = pdata.get_custom()
        custom.setdefault('saves', {})
        custom['saves'].setdefault(account_id, {})
        custom['saves'][account_id][name] = pbid
        pdata.CacheData.custom = custom
        send(f"Saved {name} => {pbid}", clientid)
    except Exception:
        send("Failed to save.", clientid)


def savelist_command(account_id: str, clientid: int) -> None:
    try:
        from playersdata import pdata
        custom = pdata.get_custom()
        profiles = pdata.get_profiles()
        entries = custom.get('saves', {}).get(account_id, {})
        if not entries:
            send("No saved entries.", clientid)
            return
        lines = []
        for name, pbid in entries.items():
            player_name = profiles.get(pbid, {}).get('name', pbid)
            lines.append(f"{name}: {player_name} ({pbid})")
        send("\n".join(lines), clientid)
    except Exception:
        send("Failed to fetch savelist.", clientid)


def show_available_playlists(clientid: int) -> None:
    try:
        playlists = setting.get_settings_data().get('playlists', {}) or {}
        names = sorted(playlists.keys())
    except Exception:
        names = []
    if not names:
        send("No playlists configured in settings.json (playlists).", clientid)
        return
    msg = "\ue046______________|AVAILABLE PLAYLISTS|________________\ue046\n"
    for i, name in enumerate(names, 1):
        if i % 7 == 1:
            msg += "\n\ue046 || " + name
        else:
            msg += ", " + name
    msg += "\nUse: vp <name> to start a vote."
    send(msg, clientid)


def complaint_command(arguments, reporter_client_id: int, reporter_pbid: str) -> None:
    """In‑game complaint command: /comp <clientId> <reason...>

    Sends a nicely formatted report to the configured Discord channel.
    """
    if not arguments or len(arguments) < 2:
        send("Usage: /comp <clientId> <reason>", reporter_client_id)
        return

    try:
        target_cid = int(arguments[0])
    except Exception:
        send("First argument must be a client id number.", reporter_client_id)
        return

    reason = " ".join(arguments[1:]).strip()
    if not reason:
        send("Please provide a reason after the client id.", reporter_client_id)
        return

    # Resolve reporter name from roster or profiles.
    reporter_name = "Unknown"
    try:
        for ros in bs.get_game_roster():
            if ros.get("client_id") == reporter_client_id:
                reporter_name = ros.get("display_string") or reporter_name
                break
    except Exception:
        pass

    # Resolve target player info from roster.
    target_name = None
    target_pbid = None
    try:
        for ros in bs.get_game_roster():
            if ros.get("client_id") == target_cid:
                target_name = ros.get("display_string")
                target_pbid = ros.get("account_id")
                break
    except Exception:
        pass

    # Resolve server name so complaints from multiple servers can be identified in one channel.
    server_name = "Unknown"
    try:
        import babase
        server_name = babase.app.classic.server._config.party_name or server_name
    except Exception:
        try:
            server_name = setting.get_settings_data().get("HostName", server_name) or server_name
        except Exception:
            pass

    # Forward to Discord bot (if available).
    try:
        from features import discord_bot

        discord_bot.send_complaint_embed(
            reporter_name=reporter_name,
            reporter_pbid=reporter_pbid,
            target_name=target_name,
            target_client_id=target_cid,
            target_pbid=target_pbid,
            reason=reason,
            server_name=server_name,
        )
        send("Your complaint has been sent to staff. Thank you.", reporter_client_id)
        # Notify the accused player in-game (if they are currently in roster).
        if target_pbid and target_cid >= 0 and target_cid != reporter_client_id:
            try:
                send(
                    f"Complaint notice: {reporter_name} reported you to staff.\nReason: {reason}",
                    target_cid,
                )
            except Exception:
                pass
    except Exception:
        # If Discord is unavailable, at least acknowledge.
        send("Could not send complaint to Discord right now.", reporter_client_id)

def chatlist_command(arguments, clientid: int) -> None:
    # Usage: /chatlist <pb-id>
    if not arguments:
        send("Usage: /chatlist <pb-id>", clientid)
        return
    target_pbid = arguments[0]
    try:
        import os
        import _babase
        log_path = os.path.join(_babase.env()['python_directory_user'], 'serverdata', 'Chat Logs.log')
        if not os.path.exists(log_path):
            send("Chat log not found.", clientid)
            return
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        # Filter lines containing the pbid
        matched = [ln.strip() for ln in lines if target_pbid in ln]
        if not matched:
            send("No messages found for that player.", clientid)
            return
        last20 = matched[-20:]
        send("\n".join(last20), clientid)
    except Exception:
        send("Failed to read chat list.", clientid)


def rmsave_command(arguments, account_id: str, clientid: int) -> None:
    # Usage: /rmsave <name>
    if not arguments:
        send("Usage: /rmsave <name>", clientid)
        return
    name = arguments[0]
    try:
        from playersdata import pdata
        custom = pdata.get_custom()
        saves = custom.get('saves', {}).get(account_id, {})
        if name in saves:
            del saves[name]
            custom['saves'][account_id] = saves
            pdata.CacheData.custom = custom
            send(f"Removed save '{name}'", clientid)
        else:
            send(f"No saved entry named '{name}'", clientid)
    except Exception:
        send("Failed to remove save.", clientid)


def set_join_message_command(arguments, from_account_id: str, clientid: int) -> None:
    # Usage: /setmsg <pb-id> <message...>
    if not arguments or len(arguments) < 2:
        send("Usage: /setmsg <pb-id> <message>", clientid)
        return
    target_pbid = arguments[0]
    message = " ".join(arguments[1:]).strip()
    if not message:
        send("Message cannot be empty.", clientid)
        return
    try:
        from playersdata import pdata
        profiles = pdata.get_profiles()
        from_name = profiles.get(from_account_id, {}).get('name', from_account_id)
        custom = pdata.get_custom()
        custom.setdefault('join_msgs', {})
        custom['join_msgs'].setdefault(target_pbid, [])
        custom['join_msgs'][target_pbid].append({'from': from_account_id, 'from_name': from_name, 'msg': message})
        pdata.CacheData.custom = custom
        send("Join message saved.", clientid)
    except Exception:
        send("Failed to save join message.", clientid)
