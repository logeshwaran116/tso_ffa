from .handlers import send
from tools import playlist
import random

import _babase
import _bascenev1
import setting
from playersdata import pdata
# from tools.whitelist import add_to_white_list, add_commit_to_logs
from serverdata import serverdata

from stats import mystats

import babase
import bascenev1 as bs
from tools import logger
from tools import coins
from bascenev1lib import gameutils


Commands = ['recents','banlist', 'info', 'createteam', 'showid', 'hideid', 'lm', 'gp',
            'party', 'quit', 'kickvote', 'maxplayers', 'playlist', 'ban',
            'kick', 'remove', 'end', 'quit', 'mute', 'unmute', 'slowmo', 'nv',
            'dv', 'pause', 'tint',
            'cameramode', 'createrole', 'addrole', 'removerole', 'addcommand',
            'addcmd', 'removecommand', 'getroles', 'removecmd', 'changetag',
            'customtag', 'customeffect', 'removeeffect', 'removetag', 'add',
            'spectators', 'lobbytime','acl', 'givecoins', 'unban', 'unkick',
            'hug','target','hugall','control','exchange','icy','spaz','spazall','zombie','zombieall','tex','texall','playsound','ooh','zm','vcl',
            'dbc','d_bomb_count','default_bomb_count','dbt','d_bomb_type','default_bomb_type','floater','healer','rmhealer','attack']
CommandAliases = ['pme','max', 'rm', 'next', 'restart', 'mutechat', 'unmutechat',
                  'sm',
                  'slow', 'night', 'day', 'pausegame', 'camera_mode',
                  'rotate_camera', 'exchange','control', 'effect','say','hug','hugall','control','exchange','icy','cc','spaz','ccall','spazall','box','boxall','mbox','imp','drop','superjump','gift','kickall','acl',
                  'prot','protect','zoommessage','admincmdlist','vipcmdlist']


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
    match command:
        case 'recents':
            get_recents(clientid)
        case 'info'|'i':
            get_player_info(arguments, clientid)
        case 'maxplayers' | 'max':
            changepartysize(arguments)
        case 'createteam':
            create_team(arguments)
        case 'playlist'|'p':
            changeplaylist(arguments)
        case 'kick'|'k':
            kick(arguments,clientid)
        case 'ban'|'b':
            ban(arguments, clientid)
        case 'end' | 'next'|'e':
            end(arguments)
        case 'kickvote':
            kikvote(arguments, clientid)
        case 'hideid':
            hide_player_spec()
        case 'showid':
            show_player_spec()
        case 'lm':
            last_msgs(clientid)
        case 'gp':
            get_profiles(arguments, clientid)
        case 'party':
            party_toggle(arguments)
        case 'quit' | 'restart'|'r':
            quit(arguments)
        case 'mute' | 'mutechat'|'m':
            mute(arguments,clientid)
        case 'unmute' | 'unmutechat'| 'um':
            un_mute(arguments, clientid)
        case 'remove' | 'rm' |'r':
            remove(arguments)
        case 'sm' | 'slow' | 'slowmo' |'s':
            slow_motion()
        case 'control' | 'exchange':
            control(arguments, clientid)
        case 'nv' | 'night'|'n':
            nv(arguments)
        case 'tint':
            tint(arguments)
        case 'pause' | 'pausegame'|'p':
            pause()
        case 'cameraMode' | 'camera_mode' | 'rotate_camera':
            rotate_camera()
        case 'createrole':
            create_role(arguments)
        case 'addrole':
            add_role_to_player(arguments)
        case 'removerole':
            remove_role_from_player(arguments)
        case 'getroles':
            get_roles_of_player(arguments, clientid)
        case 'addcommand' | 'addcmd'|'ac':
            add_command_to_role(arguments)
        case 'removecommand' | 'removecmd'|'rc':
            remove_command_to_role(arguments)
        case 'changetag':
            change_role_tag(arguments)
        case 'customtag'|'ct':
            set_custom_tag(arguments)
        case 'customeffect' | 'effect'|'ce':
            set_custom_effect(arguments)
        case 'removetag':
            remove_custom_tag(arguments)
        case 'removeeffect':
            remove_custom_effect(arguments)
        case 'spectators':
            spectators(arguments)
        case 'lobbytime':
            change_lobby_check_time(arguments)
        case 'pme':
            stats_to_clientid(arguments, clientid, accountid)
        case 'say':
            server_chat(arguments, clientid)
        case 'hug':
            hug(arguments, clientid)
        case 'hugall':
            hugall(arguments, clientid)
        case 'icy':
            icy(arguments, clientid)
        case 'spaz' | 'cc':
            spaz(arguments, clientid)
        case 'ccall' | 'spazall':
            spazall(arguments, clientid)
        case 'box':
            box(arguments, clientid)
        case 'boxall':
            boxall(arguments, clientid)
        case 'mbox':
            mbox(arguments, clientid)
        case 'imp':
            imp(arguments, clientid)
        case 'drop':
            drop(arguments, clientid)
        case 'superjump':
            superjump(arguments, clientid)
        case 'gift':
            gift(arguments, clientid)
        case 'kickall':
            kickall(arguments, clientid)
        case 'acl':
            acl(arguments, clientid)
        case 'control' | 'exchange':
            control(arguments, clientid)
        case 'unban':
            unban_command(arguments, clientid)
        case 'unkick':
            unkick_command(arguments, clientid)
        case 'givecoins':
            give_coins(arguments, clientid, accountid)
        case 'hug':
            hug(arguments, clientid)
        case 'hugall':
            hugall(arguments, clientid)
        case 'control' | 'exchange':
            control(arguments, clientid)
        case 'icy':
            icy(arguments, clientid)
        case 'spaz' | 'cc':
            spaz(arguments, clientid)
        case 'spazall' | 'ccall':
            spazall(arguments, clientid)
        case 'zombie':
            zombie(arguments, clientid)
        case 'zombieall':
            zombieall(arguments, clientid)
        case 'tex':
            tex(arguments, clientid)
        case 'texall':
            texall(arguments, clientid)
        case 'playsound':
            play_sound(arguments, clientid)
        case 'ooh':
            play_ooh_sound(arguments)
        case 'zm' | 'zoommessage':
            zm(arguments, clientid)
        case 'vcl' | 'vipcmdlist':
            vcl(arguments, clientid)
        case 'prot' | 'protect':
            protect_players(arguments, clientid)
        case 'dbc' | 'd_bomb_count' | 'default_bomb_count':
            d_bomb_count(arguments, clientid)
        case 'dbt' | 'd_bomb_type' | 'default_bomb_type':
            d_bomb_type(arguments, clientid)
        case 'banlist':
            ban_list(arguments, clientid)
        case 'floater':
            floater_command(arguments, clientid)
        case 'healer':
            healer(arguments, clientid)
        case 'rmhealer':
            rmhealer(arguments, clientid)
        case 'attack':
            attack(arguments, clientid)
        case 'target':
            target(arguments, clientid)
        case _:
            pass





def control(arguments, clientid):
 activity = bs.get_foreground_host_activity()
 a = arguments
 with activity.context:
    try:
        if len(a) < 2:
            send("Usage: /exchange <clientId1> <clientId2>", clientid)
            return
        cid1 = int(a[0]); cid2 = int(a[1])
        p1 = p2 = None
        for pl in activity.players:
            cid = pl.sessionplayer.inputdevice.client_id
            if cid == cid1:
                p1 = pl
            elif cid == cid2:
                p2 = pl
        if not p1 or not p2 or not p1.actor or not p2.actor:
            send("Client id not found.", clientid)
            return
        node1 = p1.actor.node
        node2 = p2.actor.node
        p1.actor.node = node2
        p2.actor.node = node1
    except Exception:
        send("Usage: /exchange <clientId1> <clientId2>", clientid)



def spazall(arguments, clientid):
    activity = bs.get_foreground_host_activity()
    a = arguments
    with activity.context:
       for i in activity.players:
           try:
              if arguments != []:
                  appearance_name = a[0].lower()  # Convert to lowercase for case-insensitive comparison
                  valid_appearance_names = ['ali', 'wizard', 'cyborg', 'penguin', 'agent', 'pixie', 'bear', 'bunny']
                  # Check if the appearance name is valid
                  if appearance_name in valid_appearance_names:               
                      i.actor.node.color_texture = bs.gettexture(appearance_name + "Color")
                      i.actor.node.color_mask_texture = bs.gettexture(appearance_name + "ColorMask")
                      i.actor.node.head_model = bs.getmodel(appearance_name + "Head")
                      i.actor.node.torso_model = bs.getmodel(appearance_name + "Torso")
                      i.actor.node.pelvis_model = bs.getmodel(appearance_name + "Pelvis")
                      i.actor.node.upper_arm_model = bs.getmodel(appearance_name + "UpperArm")
                      i.actor.node.forearm_model = bs.getmodel(appearance_name + "ForeArm")
                      i.actor.node.hand_model = bs.getmodel(appearance_name + "Hand")
                      i.actor.node.upper_leg_model = bs.getmodel(appearance_name + "UpperLeg")
                      i.actor.node.lower_leg_model = bs.getmodel(appearance_name + "LowerLeg")
                      i.actor.node.toes_model = bs.getmodel(appearance_name + "Toes")
                      i.actor.node.style = appearance_name
                  else:
                      # If the appearance name is not valid, inform the user
                      send("Invalid CharacterName.\nPlease choose from: ali, wizard, cyborg, penguin, agent, pixie, bear, bunny", clientid)
              else:
                  send("Using: /spazall [CharacterName]", clientid)
           except Exception as e:
               print(f"Error in spaz command: {e}")
               send("An error occurred. Please try again.", clientid)

_target_states: dict[int, dict] = {}

def target(arguments, clientid):
    activity = bs.get_foreground_host_activity()
    if activity is None:
        send("No active activity", clientid)
        return

    # Helpers
    def _resolve_player_by_cid(cid: int):
        act = bs.get_foreground_host_activity()
        if act is None:
            return None
        for pl in act.players:
            try:
                if pl.sessionplayer.inputdevice.client_id == cid:
                    return pl
            except Exception:
                pass
        return None

    # Stop logic
    if arguments and arguments[0].lower() == 'stop':
        target = arguments[1] if len(arguments) > 1 else 'all'
        if target == 'all':
            for _cid, state in list(_target_states.items()):
                try:
                    if state.get('follow_timer'):
                        state['follow_timer'].cancel()
                except Exception:
                    pass
                try:
                    if state.get('drop_timer'):
                        state['drop_timer'].cancel()
                except Exception:
                    pass
                try:
                    node = state.get('node')
                    if node is not None and node.exists():
                        node.delete()
                except Exception:
                    pass
                try:
                    flo = state.get('flo_actor')
                    if flo is not None:
                        flo.handlemessage(bs.DieMessage())
                except Exception:
                    pass
                _target_states.pop(_cid, None)
            send("All targets stopped.", clientid)
            return
        try:
            stop_cid = int(target)
        except Exception:
            send("Usage: /target stop [clientId|all]", clientid)
            return
        state = _target_states.pop(stop_cid, None)
        if state is not None:
            try:
                if state.get('follow_timer'):
                    state['follow_timer'].cancel()
            except Exception:
                pass
            try:
                if state.get('drop_timer'):
                    state['drop_timer'].cancel()
            except Exception:
                pass
            try:
                node = state.get('node')
                if node is not None and node.exists():
                    node.delete()
            except Exception:
                pass
            try:
                flo = state.get('flo_actor')
                if flo is not None:
                    flo.handlemessage(bs.DieMessage())
            except Exception:
                pass
            send(f"Target stopped for {stop_cid}.", clientid)
        else:
            send(f"No active target for {stop_cid}.", clientid)
        return

    # Start logic
    if not arguments:
        send("Usage: /target <clientId>", clientid)
        return
    try:
        target_cid = int(arguments[0])
    except Exception:
        send("clientId must be an integer.", clientid)
        return

    # Clear existing
    if target_cid in _target_states:
        try:
            st = _target_states.pop(target_cid)
            if st.get('follow_timer'):
                st['follow_timer'].cancel()
            if st.get('drop_timer'):
                st['drop_timer'].cancel()
            n = st.get('node')
            if n is not None and n.exists():
                n.delete()
            flo = st.get('flo_actor')
            if flo is not None:
                flo.handlemessage(bs.DieMessage())
        except Exception:
            pass

    # Create Floater
    with activity.context:
        flo_actor = None
        landmine = None
        try:
            from chathandle.chatcommands import floater as _flo
            try:
                bounds = activity.map.get_def_bound_box('map_bounds')
            except Exception:
                center = (0.0, 3.0, 0.0)
                size = 20.0
                bounds = (center[0]-size, center[1]-size, center[2]-size,
                          center[0]+size, center[1]+size, center[2]+size)
            flo_actor = _flo.Floater(bounds)
            landmine = flo_actor.node
        except Exception:
            # Fallback to a prop skinned as landmine
            try:
                landmine = bs.newnode('prop', attrs={
                    'position': (0, 15.0, 0),
                    'mesh': bs.getmesh('landMine'),
                    'color_texture': bs.gettexture('landMine'),
                    'body': 'landMine',
                    'gravity_scale': 0.0,
                })
            except Exception:
                landmine = bs.newnode('locator', attrs={
                    'shape': 'circleOutline', 'color': (1,0.2,0.2), 'opacity': 0.9,
                    'size': [0.8], 'draw_beauty': True, 'additive': False,
                    'position': (0, 15.0, 0),
                })

    # Initialize at player's position
    tgt = _resolve_player_by_cid(target_cid)
    if tgt and tgt.actor and tgt.actor.node.exists():
        try:
            landmine.position = (tgt.actor.node.position[0], tgt.actor.node.position[1] + 0.5, tgt.actor.node.position[2])
        except Exception:
            pass

    # Follow params: slow but steady
    speed = 5.0
    dt = 0.05

    def _follow_tick() -> None:
        act = bs.get_foreground_host_activity()
        if act is None:
            return
        if landmine is None or not landmine.exists():
            return
        pl = _resolve_player_by_cid(target_cid)
        if pl is None or not pl.actor or not pl.actor.node.exists():
            return
        try:
            lx, ly, lz = landmine.position
            px, py, pz = pl.actor.node.position
            vx, vy, vz = (px - lx), (py - ly), (pz - lz)
            dist2 = vx*vx + vy*vy + vz*vz
            if dist2 <= 1e-6:
                return
            step = speed * dt
            import math
            d = math.sqrt(dist2)
            if d <= step:
                newpos = (px, py, pz)
            else:
                s = step / d
                newpos = (lx + vx * s, ly + vy * s, lz + vz * s)
            landmine.position = newpos
        except Exception:
            pass

    from bascenev1lib.actor.bomb import Bomb

    def _drop_tick() -> None:
        act = bs.get_foreground_host_activity()
        if act is None:
            return
        if landmine is None or not landmine.exists():
            return
        try:
            x, y, z = landmine.position
        except Exception:
            return
        with act.context:
            try:
                # Only impact bombs, dropped from above
                b = Bomb(position=(x, y + 8.0, z), bomb_type='impact').autoretain()
                b.node.velocity = (0.0, -18.0, 0.0)
            except Exception:
                pass

    # Start timers
    with activity.context:
        follow_timer = bs.Timer(dt, bs.Call(_follow_tick), repeat=True)
        drop_timer = bs.Timer(0.5, bs.Call(_drop_tick), repeat=True)

    _target_states[target_cid] = {
        'node': landmine,
        'flo_actor': flo_actor,
        'follow_timer': follow_timer,
        'drop_timer': drop_timer,
    }

    send(f"Targeting client {target_cid} with floater.", clientid)


def spaz(arguments, clientid):
    activity = bs.get_foreground_host_activity()
    a = arguments
    with bs.Context(activity):
        try:
            if arguments != []:
                n = int(a[0])
                appearance_name = a[1].lower()  # Convert to lowercase for case-insensitive comparison
                valid_appearance_names = ['ali', 'wizard', 'cyborg', 'penguin', 'agent', 'pixie', 'bear', 'bunny']
                # Check if the appearance name is valid
                if appearance_name in valid_appearance_names:               
                    activity.players[n].actor.node.color_texture = bs.gettexture(appearance_name + "Color")
                    activity.players[n].actor.node.color_mask_texture = bs.gettexture(appearance_name + "ColorMask")
                    activity.players[n].actor.node.head_model = bs.getmodel(appearance_name + "Head")
                    activity.players[n].actor.node.torso_model = bs.getmodel(appearance_name + "Torso")
                    activity.players[n].actor.node.pelvis_model = bs.getmodel(appearance_name + "Pelvis")
                    activity.players[n].actor.node.upper_arm_model = bs.getmodel(appearance_name + "UpperArm")
                    activity.players[n].actor.node.forearm_model = bs.getmodel(appearance_name + "ForeArm")
                    activity.players[n].actor.node.hand_model = bs.getmodel(appearance_name + "Hand")
                    activity.players[n].actor.node.upper_leg_model = bs.getmodel(appearance_name + "UpperLeg")
                    activity.players[n].actor.node.lower_leg_model = bs.getmodel(appearance_name + "LowerLeg")
                    activity.players[n].actor.node.toes_model = bs.getmodel(appearance_name + "Toes")
                    activity.players[n].actor.node.style = appearance_name
                else:
                    # If the appearance name is not valid, inform the user
                    send("Invalid CharacterName.\nPlease choose from: ali, wizard, cyborg, penguin, agent, pixie, bear, bunny", clientid)
            else:
                send("Using: /spaz [PLAYER-ID] [CharacterName]", clientid)
        except Exception as e:
            print(f"Error in spaz command: {e}")
            send("An error occurred. Please try again.", clientid)



def box(arguments, clientid):
    activity = bs.get_foreground_host_activity()
    if activity is None:
        send("No active activity", clientid)
        return
    with activity.context:
        try:
            if not arguments:
                send("Usage: /box <clientId>", clientid)
                return
            target_cid = int(arguments[0])
            player = None
            for pl in activity.players:
                if pl.sessionplayer.inputdevice.client_id == target_cid:
                    player = pl
                    break
            if player is None:
                send("Client id not found.", clientid)
                return
            if not player or not player.actor or not player.actor.node.exists():
                send("Player not available", clientid)
                return
            # Match baCheatMax: set player's own meshes/textures to TNT
            try:
                node = player.actor.node
                node.torso_mesh = bs.getmesh('tnt')
                node.head_mesh = None
                node.pelvis_mesh = None
                node.forearm_mesh = None
                node.color_texture = node.color_mask_texture = bs.gettexture('tnt')
                node.color = node.highlight = (1, 1, 1)
                node.style = 'cyborg'
            except Exception:
                pass
            send("Box applied.", clientid)
        except Exception:
            send("Usage: /box <clientId>", clientid)

         #BOXALL
def boxall(arguments, clientid):
    activity = bs.get_foreground_host_activity()
    if activity is None:
        send("No active activity", clientid)
        return
    with activity.context:
        try:
            for p in activity.players:
                try:
                    if not p or not p.actor or not p.actor.node.exists():
                        continue
                    try:
                        node = p.actor.node
                        node.torso_mesh = bs.getmesh('tnt')
                        node.head_mesh = None
                        node.pelvis_mesh = None
                        node.forearm_mesh = None
                        node.color_texture = node.color_mask_texture = bs.gettexture('tnt')
                        node.color = node.highlight = (1, 1, 1)
                        node.style = 'cyborg'
                    except Exception:
                        pass
                except Exception:
                    pass
            send("Box applied to all players.", clientid)
        except Exception:
            pass

_attack_states: dict[int, dict] = {}

def attack(arguments, clientid):
    activity = bs.get_foreground_host_activity()
    if activity is None:
        send("No active activity", clientid)
        return

    # Helpers
    def _resolve_player_by_cid(cid: int):
        act = bs.get_foreground_host_activity()
        if act is None:
            return None
        for pl in act.players:
            try:
                if pl.sessionplayer.inputdevice.client_id == cid:
                    return pl
            except Exception:
                pass
        return None

    # Stop logic
    if arguments and arguments[0].lower() == 'stop':
        target = arguments[1] if len(arguments) > 1 else 'all'
        if target == 'all':
            # cancel all
            for _cid, state in list(_attack_states.items()):
                try:
                    if state.get('follow_timer'):
                        state['follow_timer'].cancel()
                except Exception:
                    pass
                try:
                    if state.get('drop_timer'):
                        state['drop_timer'].cancel()
                except Exception:
                    pass
                try:
                    n = state.get('node')
                    if n is not None and n.exists():
                        n.delete()
                except Exception:
                    pass
                _attack_states.pop(_cid, None)
            send("All attacks stopped.", clientid)
            return
        try:
            stop_cid = int(target)
        except Exception:
            send("Usage: /attack stop [clientId|all]", clientid)
            return
        state = _attack_states.pop(stop_cid, None)
        if state is not None:
            try:
                if state.get('follow_timer'):
                    state['follow_timer'].cancel()
            except Exception:
                pass
            try:
                if state.get('drop_timer'):
                    state['drop_timer'].cancel()
            except Exception:
                pass
            try:
                n = state.get('node')
                if n is not None and n.exists():
                    n.delete()
            except Exception:
                pass
            send(f"Attack stopped for {stop_cid}.", clientid)
        else:
            send(f"No active attack for {stop_cid}.", clientid)
        return

    # Start logic
    if not arguments:
        send("Usage: /attack <clientId>", clientid)
        return
    try:
        target_cid = int(arguments[0])
    except Exception:
        send("clientId must be an integer.", clientid)
        return

    # If attack already exists for this cid, stop it first.
    if target_cid in _attack_states:
        try:
            st = _attack_states.pop(target_cid)
            if st.get('follow_timer'):
                st['follow_timer'].cancel()
            if st.get('drop_timer'):
                st['drop_timer'].cancel()
            n = st.get('node')
            if n is not None and n.exists():
                n.delete()
        except Exception:
            pass

    # Create the landmine visual (landmine texture) and timers under this activity.
    with activity.context:
        landmine = None
        # Preferred: a non-physical prop using landmine model/texture.
        try:
            landmine = bs.newnode('prop', attrs={
                'position': (0, 1.0, 0),
                'mesh': bs.getmesh('landMine'),
                'color_texture': bs.gettexture('landMine'),
                'body': 'puck',
                'gravity_scale': 0.0,
            })
            # Make it mostly decorative: no collisions/forces.
            try:
                landmine.extra_acceleration = (0, 0, 0)
                landmine.velocity = (0, 0, 0)
            except Exception:
                pass
        except Exception:
            # Fallback: spawn a Bomb node and reskin it to landmine.
            try:
                from bascenev1lib.actor.bomb import Bomb as _BombForSkin
                _b = _BombForSkin(position=(0, 1.0, 0), bomb_type='impact').autoretain()
                _b.node.mesh = bs.getmesh('landMine')
                _b.node.color_texture = bs.gettexture('landMine')
                _b.node.gravity_scale = 0.0
                _b.node.fuse_length = 0.0
                landmine = _b.node
            except Exception:
                # Last resort: locator ring
                landmine = bs.newnode('locator', attrs={
                    'shape': 'circleOutline',
                    'color': (1, 0.2, 0.2),
                    'opacity': 0.9,
                    'size': [0.8],
                    'draw_beauty': True,
                    'additive': False,
                    'position': (0, 1.0, 0),
                })

    # Initialize at target's current position if possible
    tgt = _resolve_player_by_cid(target_cid)
    if tgt and tgt.actor and tgt.actor.node.exists():
        try:
            landmine.position = (tgt.actor.node.position[0], tgt.actor.node.position[1] + 0.5, tgt.actor.node.position[2])
        except Exception:
            pass

    # Follow parameters
    speed = 5.0  # world units per second (slow, but not too slow)
    dt = 0.05    # follow tick seconds

    def _follow_tick() -> None:
        act = bs.get_foreground_host_activity()
        if act is None:
            return
        if landmine is None or not landmine.exists():
            return
        pl = _resolve_player_by_cid(target_cid)
        if pl is None or not pl.actor or not pl.actor.node.exists():
            return
        try:
            lx, ly, lz = landmine.position
            px, py, pz = pl.actor.node.position
            # Move toward player
            vx, vy, vz = (px - lx), (py - ly), (pz - lz)
            dist2 = vx*vx + vy*vy + vz*vz
            if dist2 <= 1e-6:
                return
            # step distance per tick
            step = speed * dt
            import math
            d = math.sqrt(dist2)
            if d <= step:
                newpos = (px, py, pz)
            else:
                s = step / d
                newpos = (lx + vx * s, ly + vy * s, lz + vz * s)
            landmine.position = newpos
        except Exception:
            pass

    from bascenev1lib.actor.bomb import Bomb

    def _drop_tick() -> None:
        act = bs.get_foreground_host_activity()
        if act is None:
            return
        if landmine is None or not landmine.exists():
            return
        try:
            x, y, z = landmine.position
        except Exception:
            return
        with act.context:
            try:
                # Drop from above the landmine for a "from top" feel
                b = Bomb(position=(x, y + 8.0, z), bomb_type='impact').autoretain()
                b.node.velocity = (0.0, -18.0, 0.0)
            except Exception:
                pass

    # Start timers
    with activity.context:
        follow_timer = bs.Timer(dt, bs.Call(_follow_tick), repeat=True)
        drop_timer = bs.Timer(0.5, bs.Call(_drop_tick), repeat=True)

    _attack_states[target_cid] = {
        'node': landmine,
        'follow_timer': follow_timer,
        'drop_timer': drop_timer,
    }

    send(f"Landmine deployed on client {target_cid}.", clientid)


def mbox(arguments, clientid):
    """Spawn a magic box that can be picked up. Usage: /mbox <clientId|all>"""
    activity = bs.get_foreground_host_activity()
    if activity is None:
        send("No active activity", clientid)
        return
    with activity.context:
        try:
            def spawn_box_at(node):
                # Use Bomb node with sticky off to allow pickup/carrying
                import bascenev1 as _bs
                from bascenev1lib.actor import bomb as _stdbomb
                position = (node.position[0], node.position[1] + 1.5, node.position[2])
                b = _stdbomb.Bomb(position=position, bomb_type='impact').autoretain()
                # Reskin to look like a box/powerup and disable fuse/explosion
                b.node.mesh = _bs.getmesh('powerup')
                b.node.color_texture = _bs.gettexture('rgbStripes')
                b.node.fuse_length = 0.0
                b.node.sticky = False
                b.node.gravity_scale = 1.0
                return b.node

            if not arguments:
                send("Usage: /mbox <clientId|all>", clientid)
                return
            if arguments[0] == 'all':
                for p in activity.players:
                    if p.actor and p.actor.node.exists():
                        spawn_box_at(p.actor.node)
                send("Magic boxes spawned for all players.", clientid)
                return
            target_cid = int(arguments[0])
            p = None
            for pl in activity.players:
                if pl.sessionplayer.inputdevice.client_id == target_cid:
                    p = pl
                    break
            if p is None:
                send("Client id not found.", clientid)
                return
            if p and p.actor and p.actor.node.exists():
                spawn_box_at(p.actor.node)
                send("Magic box spawned.", clientid)
        except Exception:
            send("Usage: /mbox <clientId|all>", clientid)

_HEALERS: dict[int, bool] = {}

def healer(arguments, clientid):
    """Continuously heal a client until they die or rmhealer is used.
    Usage: /healer <clientId>
    """
    activity = bs.get_foreground_host_activity()
    if activity is None:
        send("No active activity", clientid)
        return
    with activity.context:
        try:
            if not arguments:
                send("Usage: /healer <clientId>", clientid)
                return
            target_cid = int(arguments[0])
            # Find target player by client-id
            target = None
            for pl in activity.players:
                if pl.sessionplayer.inputdevice.client_id == target_cid:
                    target = pl
                    break
            if target is None or not target.actor or not target.actor.node.exists():
                send("Client id not found.", clientid)
                return

            # Mark healer active
            _HEALERS[target_cid] = True

            def tick():
                # Stop if disabled or player gone
                if not _HEALERS.get(target_cid):
                    return
                try:
                    if not target.actor or not target.actor.node.exists():
                        _HEALERS.pop(target_cid, None)
                        return
                    # Apply a health powerup
                    target.actor.handlemessage(bs.PowerupMessage('health'))
                except Exception:
                    pass
                # Reschedule in 4 seconds
                bs.timer(4.0, tick)

            tick()
            send("Healer enabled.", clientid)
        except Exception:
            send("Usage: /healer <clientId>", clientid)

def rmhealer(arguments, clientid):

    activity = bs.get_foreground_host_activity()
    if activity is None:
        send("No active activity", clientid)
        return
    with activity.context:
        try:
            if not arguments:
                send("Usage: /rmhealer <clientId>", clientid)
                return
            target_cid = int(arguments[0])
            if _HEALERS.pop(target_cid, None) is not None:
                send("Healer disabled.", clientid)
            else:
                send("Healer was not enabled for that client.", clientid)
        except Exception:
            send("Usage: /rmhealer <clientId>", clientid)


def imp(arguments, clientid):
    """Apply an impulse at player's position. Usage: /imp <clientId|all>"""
    activity = bs.get_foreground_host_activity()
    if activity is None:
        send("No active activity", clientid)
        return
    with activity.context:
        try:
            def do_imp(node):
                msg = bs.HitMessage(pos=node.position,
                                    velocity=node.velocity,
                                    magnitude=500 * 4,
                                    hit_subtype='imp',
                                    radius=7840)
                if isinstance(msg, bs.HitMessage):
                    for _ in range(2):
                        node.handlemessage('impulse',
                                           msg.pos[0], msg.pos[1], msg.pos[2],
                                           msg.velocity[0], msg.velocity[1] + 2.0, msg.velocity[2], msg.magnitude,
                                           msg.velocity_magnitude, msg.radius, 0,
                                           msg.force_direction[0], msg.force_direction[1], msg.force_direction[2])

            if not arguments:
                send("Usage: /imp <clientId|all>", clientid)
                return
            if arguments[0] == 'all':
                for p in activity.players:
                    if p.actor and p.actor.node.exists():
                        do_imp(p.actor.node)
                send("Impulse applied to all players.", clientid)
                return
            target_cid = int(arguments[0])
            p = None
            for pl in activity.players:
                if pl.sessionplayer.inputdevice.client_id == target_cid:
                    p = pl
                    break
            if p is None:
                send("Client id not found.", clientid)
                return
            if p and p.actor and p.actor.node.exists():
                do_imp(p.actor.node)
                send("Impulse applied.", clientid)
        except Exception:
            send("Usage: /imp <clientId|all>", clientid)


def drop(arguments, clientid):
    """Drop sticky bombs around player like CheatMax /drop. Usage: /drop <clientId|all>"""
    activity = bs.get_foreground_host_activity()
    if activity is None:
        send("No active activity", clientid)
        return
    from bascenev1lib.actor.bomb import Bomb
    with activity.context:
        try:
            def do_drop(node):
                pos = node.position
                positions = [
                    (pos[0] - 1, pos[1] + 4, pos[2] + 1),
                    (pos[0] + 1, pos[1] + 4, pos[2] + 1),
                    (pos[0], pos[1] + 4, pos[2] - 1),
                    (pos[0] - 2, pos[1] + 4, pos[2]),
                    (pos[0] + 2, pos[1] + 4, pos[2]),
                    (pos[0] + 2, pos[1] + 4, pos[2] - 1),
                    (pos[0] - 2, pos[1] + 4, pos[2] - 1),
                    (pos[0], pos[1] + 4, pos[2] + 2),
                ]
                for p in positions:
                    b = Bomb(position=p, bomb_type='sticky').autoretain()
                    b.node.gravity_scale = 4.0
                    b.node.color_texture = bs.gettexture('bombStickyColor')

            if not arguments:
                send("Usage: /drop <clientId|all>", clientid)
                return
            if arguments[0] == 'all':
                for p in activity.players:
                    if p.actor and p.actor.node.exists():
                        bs.timer(0.0, bs.Call(do_drop, p.actor.node))
                        bs.timer(0.308, bs.Call(do_drop, p.actor.node))
                send("Dropped bombs for all players.", clientid)
                return
            target_cid = int(arguments[0])
            p = None
            for pl in activity.players:
                if pl.sessionplayer.inputdevice.client_id == target_cid:
                    p = pl
                    break
            if p is None:
                send("Client id not found.", clientid)
                return
            if p and p.actor and p.actor.node.exists():
                bs.timer(0.0, bs.Call(do_drop, p.actor.node))
                bs.timer(0.308, bs.Call(do_drop, p.actor.node))
                send("Dropped bombs.", clientid)
        except Exception:
            send("Usage: /drop <clientId|all>", clientid)


def floater_command(arguments, clientid):
    """Control Floater using testing files/floater.py: /floater [clientId]
    If no clientId is provided, uses the caller's client id.
    """
    try:
        import os, importlib.util
        # Compute repo root from this file: dist/ba_root/mods/chathandle/chatcommands/commands/management.py
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '..'))
        fpath = os.path.join(base, 'testing files', 'floater.py')
        if not os.path.exists(fpath):
            send('Floater module not found in testing files.', clientid)
            return
        spec = importlib.util.spec_from_file_location('testing_floater', fpath)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        target = clientid
        if arguments and arguments[0] not in ['', None]:
            try:
                target = int(arguments[0])
            except Exception:
                pass
        # Use the original assignFloInputs from testing floater module
        if hasattr(mod, 'assignFloInputs'):
            mod.assignFloInputs(int(target))
        else:
            send('assignFloInputs not found in testing floater.', clientid)
    except Exception:
        try:
            send('Floater unavailable right now.', clientid)
        except Exception:
            pass


def superjump(arguments, clientid):
    """Toggle super jump on player's next jump. Usage: /superjump <clientId>"""
    activity = bs.get_foreground_host_activity()
    if activity is None:
        send("No active activity", clientid)
        return
    with activity.context:
        try:
            if not arguments:
                send("Usage: /superjump <clientId>", clientid)
                return
            target_cid = int(arguments[0])
            p = None
            for pl in activity.players:
                if pl.sessionplayer.inputdevice.client_id == target_cid:
                    p = pl
                    break
            if p is None:
                send("Client id not found.", clientid)
                return
            if p and p.actor and p.actor.node.exists():
                # Set a flag on the actor used by baCheatMax's logic; if not present, emulate via a one-shot impulse when jumping.
                setattr(p.actor, 'cm_superjump', not getattr(p.actor, 'cm_superjump', False))
                send(f"Superjump {'enabled' if getattr(p.actor, 'cm_superjump') else 'disabled'}.", clientid)
        except Exception:
            send("Usage: /superjump <clientId>", clientid)


def gift(arguments, clientid):
    """Spawn a non-destructive gift near player. Usage: /gift <playerIndex|all>"""
    activity = bs.get_foreground_host_activity()
    if activity is None:
        send("No active activity", clientid)
        return
    with activity.context:
        try:
            def spawn_gift(node):
                # Use an 'impact' bomb with no fuse to avoid explosions.
                from bascenev1lib.actor.bomb import Bomb
                b = Bomb(position=(node.position[0], node.position[1] + 1.47, node.position[2]),
                         velocity=(0.0, 4.0, 0.0), bomb_type='impact').autoretain()
                b.node.mesh = bs.getmesh('tnt')
                b.node.color_texture = bs.gettexture('crossOutMask')
                b.node.body_scale = 0.8
                b.node.gravity_scale = 1.0
                b.node.fuse_length = 0.0

            if not arguments:
                send("Usage: /gift <playerIndex|all>", clientid)
                return
            if arguments[0] == 'all':
                for p in activity.players:
                    if p.actor and p.actor.node.exists():
                        spawn_gift(p.actor.node)
                send("Gifts spawned for all players.", clientid)
                return
            idx = int(arguments[0])
            p = activity.players[idx]
            if p and p.actor and p.actor.node.exists():
                spawn_gift(p.actor.node)
                send("Gift spawned.", clientid)
        except Exception:
            send("Usage: /gift <playerIndex|all>", clientid)


def hug(arguments, clientid):
    activity = bs.get_foreground_host_activity()
    if arguments == [] or arguments == ['']:
     with activity.context:
        send(f"Using: /hugall [or] /hug [player1Index] [player2Index]", clientid)
    else:
        try:
            activity.players[int(arguments[0])].actor.node.hold_node = activity.players[int(arguments[1])].actor.node
        except:
            pass
            
            
def hugall(arguments, clientid):
    activity = bs.get_foreground_host_activity()
    with activity.context:    
     try:
         activity.players[0].actor.node.hold_node = activity.players[1].actor.node
     except:
         pass
     try:
         activity.players[1].actor.node.hold_node = activity.players[0].actor.node
     except:
         pass
     try:
         activity.players[2].actor.node.hold_node = activity.players[3].actor.node
     except:
         pass
     try:
         activity.players[3].actor.node.hold_node = activity.players[2].actor.node
     except:
         pass
     try:
          activity.players[4].actor.node.hold_node = activity.players[5].actor.node
     except:
         pass
     try:
         activity.players[5].actor.node.hold_node = activity.players[4].actor.node
     except:
         pass
     try:
         activity.players[6].actor.node.hold_node = activity.players[7].actor.node
     except:
         pass
     try:
         activity.players[7].actor.node.hold_node = activity.players[6].actor.node
     except:
         pass

#KICK ALL :)))))))))        
def kickall(arguments, clientid):
    try:
        for i in bs.get_game_roster():
            if i['client_id'] == clientid:
                continue
            try:
                if pdata.is_protected(i.get('account_id')):
                    continue
            except Exception:
                pass
            bs.disconnect_client(i['client_id'])
    except Exception:
        pass


def server_chat(arguments, clientid):
    # Modified: do NOT broadcast with server name; format as "name: text"
    # Only echo to the caller to avoid spamming everyone.
    if not arguments:
        send('Usage: /say <text to send>', clientid)
        return
    message = " ".join(arguments)
    # Resolve caller name from roster
    caller_name = None
    try:
        for me in bs.get_game_roster():
            if me.get("client_id") == clientid:
                caller_name = me.get("display_string")
                break
    except Exception:
        pass
    display = f"{caller_name or 'You'}: {message}"
    send(display, clientid)


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


def _resolve_account_id(arg: str) -> str | None:
    try:
        if arg.startswith('pb-'):
            return arg
    except Exception:
        pass
    try:
        cid = int(arg)
        for ros in bs.get_game_roster():
            if int(ros.get('client_id', -1)) == cid:
                return ros.get('account_id')
    except Exception:
        pass
    try:
        idx = int(arg)
        session = bs.get_foreground_host_session()
        player = session.sessionplayers[idx]
        return player.get_v1_account_id()
    except Exception:
        return None


def give_coins(arguments, clientid: int, caller_acc_id: str) -> None:
    """Owner-only: Give any amount of coins to any player by pb-id/clientid/index.
    Usage: /givecoins <pb-id|clientid|index> <amount>
    """
    roles = pdata.get_roles()
    is_owner = 'owner' in roles and caller_acc_id in roles['owner'].get('ids', [])
    if not is_owner:
        send("Only owner can use /givecoins", clientid)
        return
    if not arguments or len(arguments) < 2:
        send("Usage: /givecoins <pb-id|clientid|index> <amount>", clientid)
        return
    target_arg, amount_arg = arguments[0], arguments[1]
    target_acc = _resolve_account_id(target_arg)
    if not target_acc:
        send("Could not resolve target. Use pb-id or client id.", clientid)
        return
    try:
        amount = int(amount_arg)
    except Exception:
        send("Amount must be a number.", clientid)
        return
    new_bal = coins.add_coins(target_acc, amount)
    send(f"Gave {amount} coins. Target new balance: {new_bal}", clientid)


def create_team(arguments):
    if len(arguments) == 0:
        bs.chatmessage("enter team name")
    else:
        from bascenev1._team import SessionTeam
        bs.get_foreground_host_session().sessionteams.append(SessionTeam(
            team_id=len(bs.get_foreground_host_session().sessionteams) + 1,
            name=str(arguments[0]),
            color=(random.uniform(0, 1.2), random.uniform(
                0, 1.2), random.uniform(0, 1.2))))
        from bascenev1._lobby import Lobby
        bs.get_foreground_host_session().lobby = Lobby()


def hide_player_spec():
    _babase.hide_player_device_id(True)


def show_player_spec():
    _babase.hide_player_device_id(False)


def get_player_info(arguments, client_id):
    if len(arguments) == 0:
        send("invalid client id", client_id)
    for account in serverdata.recents:
        if account['client_id'] == int(arguments[0]):
            send(pdata.get_detailed_info(account["pbid"]), client_id)


def get_recents(client_id):
    for players in serverdata.recents:
        send(
            f"{players['client_id']} {players['deviceId']} {players['pbid']}",
            client_id)


def unban_command(arguments, clientid):
    if not arguments:
        send("Usage: /unban <pb-id|clientid>", clientid)
        return
    target = arguments[0]
    pbid = None
    # Resolve pbid from pb-id or client id
    try:
        if target.startswith('pb-'):
            pbid = target
        else:
            cid = int(target)
            for ros in bs.get_game_roster():
                if ros.get('client_id') == cid:
                    pbid = ros.get('account_id')
                    break
            if pbid is None:
                for rec in serverdata.recents:
                    if rec.get('client_id') == cid:
                        pbid = rec.get('pbid')
                        break
    except Exception:
        # fallback: treat as pbid if format looks right
        if target.startswith('pb-'):
            pbid = target
    if not pbid:
        send("Could not resolve target. Use pb-id or client id.", clientid)
        return
    try:
        pdata.unban_player(pbid)
        logger.log(f"unbanned {pbid} by chat command")
        bs.chatmessage(f"Unbanned {pbid}")
    except Exception as e:
        logger.log(f"unban error: {e}")
        send("Failed to unban", clientid)


def unkick_command(arguments, clientid):
    if not arguments:
        send("Usage: /unkick <pb-id|clientid>", clientid)
        return
    target = arguments[0]
    pbid = None
    try:
        if target.startswith('pb-'):
            pbid = target
        else:
            cid = int(target)
            for ros in bs.get_game_roster():
                if ros.get('client_id') == cid:
                    pbid = ros.get('account_id')
                    break
            if pbid is None:
                for rec in serverdata.recents:
                    if rec.get('client_id') == cid:
                        pbid = rec.get('pbid')
                        break
    except Exception:
        if target.startswith('pb-'):
            pbid = target
    if not pbid:
        send("Could not resolve target. Use pb-id or client id.", clientid)
        return
    # There is no persistent kick list; inform status relative to ban list.
    try:
        bl = pdata.get_blacklist()
        if pbid in bl.get('ban', {}).get('ids', {}):
            send("Player is banned; use /unban <pb-id> to allow rejoin.", clientid)
        else:
            send("Player can rejoin now (no active kick list).", clientid)
    except Exception:
        send("Player can rejoin now.", clientid)


def ban_list(arguments, clientid):
    """Show banned players from blacklist.json with names from profiles.json."""
    try:
        bl = pdata.get_blacklist().get('ban', {})
    except Exception:
        bl = {}
    ids = bl.get('ids', {}) if isinstance(bl, dict) else {}
    if not ids:
        send("No banned players.", clientid)
        return
    profiles = pdata.get_profiles()
    lines = []
    for pbid, entry in ids.items():
        try:
            name = profiles.get(pbid, {}).get('name', pbid)
            reason = entry.get('reason', 'N/A')
            till = entry.get('till', 'N/A')
            lines.append(f"{name} ({pbid}) — {reason} — until {till}")
        except Exception:
            lines.append(f"{pbid} — entry error")
    send("\n".join(lines), clientid)


def changepartysize(arguments):
    if len(arguments) == 0:
        bs.chatmessage("enter number")
    else:
        bs.set_public_party_max_size(int(arguments[0]))


def changeplaylist(arguments):
    if len(arguments) == 0:
        bs.chatmessage("enter list code or name")
    else:
        if arguments[0] == 'coop':
            serverdata.coopmode = True
        else:
            serverdata.coopmode = False
        playlist.setPlaylist(arguments[0])
    return


def kick(arguments, clientid):
    cl_id = int(arguments[0])

    for me in bs.get_game_roster():
        if me["client_id"] == clientid:
            myself = me["display_string"]
            break

    for ros in bs.get_game_roster():
        if ros["client_id"] == cl_id:
            # Block kicking protected players
            try:
                if pdata.is_protected(ros.get('account_id')):
                    bs.broadcastmessage("Cannot kick a protected player", transient=True, clients=[clientid])
                    return
            except Exception:
                pass
            logger.log("kicked " + ros["display_string"])
            bs.chatmessage(f'{myself} kicked {ros["display_string"]} Goodbye ??')
    bs.disconnect_client(int(arguments[0]))
    return


def kikvote(arguments, clientid):
    if arguments == [] or arguments == [''] or len(arguments) < 2:
        send("Usage: /kickvote <enable|disable> <client-id>", clientid)
        return

    action = arguments[0].lower()
    if action not in ('enable', 'disable'):
        send("Usage: /kickvote <enable|disable> <client-id>", clientid)
        return

    try:
        cl_id = int(arguments[1])
    except ValueError:
        send("Invalid client-id", clientid)
        return

    for ros in bs.get_game_roster():
        if ros["client_id"] != cl_id:
            continue

        account_id = ros.get("account_id")
        if not account_id:
            send("Unable to resolve account-id for this player", clientid)
            return

        if action == 'disable':
            # This blocks the account from starting kick-votes.
            _babase.disable_kickvote(account_id)
            pdata.disable_kick_vote(account_id, 2, "by chat command")
            send("Kick-vote start disabled for this player", clientid)
            logger.log(
                f'kick vote start disabled for {account_id} {ros["display_string"]}')
            return

        pdata.enable_kick_vote(account_id)
        try:
            # Present in some builds; enables immediately without rejoin.
            _babase.enable_kickvote(account_id)
        except Exception:
            pass
        send("Kick-vote start enabled for this player", clientid)
        logger.log(
            f'kick vote start enabled for {account_id} {ros["display_string"]}')
        return

    send("Player not found for given client-id", clientid)


def last_msgs(clientid):
    for i in bs.get_chat_messages():
        send(i, clientid)


def get_profiles(arguments, clientid):
    try:
        playerID = int(arguments[0])
        num = 1
        for i in bs.get_foreground_host_session().sessionplayers[
                playerID].inputdevice.get_player_profiles():
            try:
                send(f"{num})-  {i}", clientid)
                num += 1
            except:
                pass
    except:
        pass


def party_toggle(arguments):
    if arguments == ['public']:
        bs.set_public_party_enabled(True)
        bs.chatmessage("party is public now")
    elif arguments == ['private']:
        bs.set_public_party_enabled(False)
        bs.chatmessage("party is private now")
    else:
        pass


def end(arguments):
    if arguments == [] or arguments == ['']:
        try:
            game = bs.get_foreground_host_activity()
            with game.context:
                game.end_game()
        except:
            pass


def ban(arguments,clientid):
    try:
        cl_id = int(arguments[0])
        duration = int(arguments[1]) if len(arguments) >= 2 else 0.5

        for me in bs.get_game_roster():
            if me["client_id"] == clientid:
                myself = me["display_string"]

        for ros in bs.get_game_roster():
            if ros["client_id"] == cl_id:
                try:
                    if pdata.is_protected(ros.get('account_id')):
                        bs.broadcastmessage("Cannot ban a protected player", transient=True, clients=[clientid])
                        return
                except Exception:
                    pass
                pdata.ban_player(ros['account_id'], duration,
                                 "by chat command")
                bs.chatmessage(f'{myself} banned {ros["display_string"]} Goodbye ')
                logger.log(f'banned {ros["display_string"]} by chat command')

        for account in serverdata.recents:  # backup case if player left the server
            if account['client_id'] == int(arguments[0]):
                try:
                    if pdata.is_protected(account.get('pbid')):
                        bs.broadcastmessage("Cannot ban a protected player", transient=True, clients=[clientid])
                        return
                except Exception:
                    pass
                pdata.ban_player(
                    account["pbid"], duration, "by chat command")
                logger.log(
                    f'banned {account["pbid"]} by chat command, recents')
        try:
            bs.disconnect_client(cl_id)
        except Exception:
            pass
    except:
        pass


def quit(arguments):
    if arguments == [] or arguments == ['']:
        babase.quit()


def mute(arguments, clientid):
    if len(arguments) == 0:
        serverdata.muted = True
        bs.chatmessage("Global chat mute enabled")
        logger.log("Server muted by chat command")
        return
    
    try:
        cl_id = int(arguments[0])
        duration = int(arguments[1]) if len(arguments) >= 2 else 0.5

        for me in bs.get_game_roster():
            if me["client_id"] == clientid:
                myself = me["display_string"]

        player_name = "Unknown Player"
        
        # Find player name from game roster
        for ros in bs.get_game_roster():
            if ros["client_id"] == cl_id:
                player_name = ros["display_string"]
                ac_id = ros['account_id']
                try:
                    if pdata.is_protected(ac_id):
                        bs.broadcastmessage("Cannot mute a protected player", transient=True, clients=[clientid])
                        return
                except Exception:
                    pass
                logger.log(f'muted {player_name}')
                pdata.mute(ac_id, duration, "muted by chat command")
                bs.chatmessage(f"{myself} muted {player_name} for {duration} days")
                return
        
        # Backup case if player left the server - try to get name from recents
        for account in serverdata.recents:
            if account['client_id'] == cl_id:
                player_name = account.get('name', 'Unknown Player')
                try:
                    if pdata.is_protected(account.get('pbid')):
                        bs.broadcastmessage("Cannot mute a protected player", transient=True, clients=[clientid])
                        return
                except Exception:
                    pass
                pdata.mute(account["pbid"], duration, "muted by chat command, from recents")
                bs.chatmessage(f"{player_name} is muted for {duration} hours (from recents)")
                return
                
        bs.chatmessage(f"Player with client ID {cl_id} not found")
        
    except ValueError:
        bs.chatmessage("Invalid arguments. Usage: /mute [client_id] [duration_hours]")
    except Exception as e:
        logger.log(f"Error in mute command: {e}")
        bs.chatmessage("An error occurred while muting the player")


def un_mute(arguments, clientid):
    if len(arguments) == 0:
        serverdata.muted = False
        logger.log("Server unmuted by chat command")
        bs.chatmessage("Global chat mute disabled")
        return
    
    try:
        cl_id = int(arguments[0])

        for me in bs.get_game_roster():
            if me["client_id"] == clientid:
                myself = me["display_string"]

        player_name = "Unknown Player"
        
        # Find player name from game roster
        for ros in bs.get_game_roster():
            if ros["client_id"] == cl_id:
                player_name = ros["display_string"]
                pdata.unmute(ros['account_id'])
                logger.log(f'unmuted {player_name} by chat command')
                bs.chatmessage(f"{myself} unmuted {player_name}")
                return
        
        # Backup case if player left the server
        for account in serverdata.recents:
            if account['client_id'] == cl_id:
                player_name = account.get('name', 'Unknown Player')
                pdata.unmute(account["pbid"])
                logger.log(f'unmuted {player_name} by chat command, recents')
                bs.chatmessage(f"{myself} unmuted {player_name} is unmuted (from recents)")
                return
                
        bs.chatmessage(f"Player with client ID {cl_id} not found")
        
    except ValueError:
        bs.chatmessage("Invalid arguments. Usage: /unmute [client_id]")
    except Exception as e:
        logger.log(f"Error in unmute command: {e}")
        bs.chatmessage("An error occurred while unmuting the player")

def remove(arguments):
    if arguments == [] or arguments == ['']:
        return

    elif arguments[0] == 'all':
        session = bs.get_foreground_host_session()
        for i in session.sessionplayers:
            i.remove_from_game()

    else:
        try:
            session = bs.get_foreground_host_session()
            for i in session.sessionplayers:
                if i.inputdevice.client_id == int(arguments[0]):
                    i.remove_from_game()
        except:
            return


def slow_motion():
    activity = bs.get_foreground_host_activity()

    if not activity.globalsnode.slow_motion:
        activity.globalsnode.slow_motion = True
        try:
            host = setting.get_settings_data().get("HostName", "Server")
            bs.broadcastmessage(f"{host}: slow motion enabled")
        except Exception:
            pass

    else:
        activity.globalsnode.slow_motion = False
        try:
            host = setting.get_settings_data().get("HostName", "Server")
            bs.broadcastmessage(f"{host}: slow motion disabled")
        except Exception:
            pass


def nv(arguments):
    def is_close(a, b, tol=1e-5):
        return all(abs(x - y) < tol for x, y in zip(a, b))

    try:
        activity = bs.get_foreground_host_activity()
        nv_tint = (0.5, 0.5, 1.0)
        nv_ambient = (1.5, 1.5, 1.5)
        
        if is_close(activity.globalsnode.tint, nv_tint):
            activity.globalsnode.tint = (1, 1, 1)
            #adding ambient color to imitate moonlight reflection on objects
            activity.globalsnode.ambient_color = (1, 1, 1)
            #print(activity.globalsnode.tint)
            try:
                bs.chatmessage("night vision disabled")
            except Exception:
                pass
        else:
            activity.globalsnode.tint = nv_tint
            activity.globalsnode.ambient_color = nv_ambient
            #print(activity.globalsnode.tint)
            try:
                bs.chatmessage("night vision enabled")
            except Exception:
                pass
    except:
        return


def tint(arguments):
    
    if len(arguments) == 3:
        args = arguments
        r, g, b = float(args[0]), float(args[1]), float(args[2])
        try:
            # print(dir(activity.globalsnode))
            
            activity = bs.get_foreground_host_activity()
            activity.globalsnode.tint = (r, g, b)
        except:
            return


def pause():
    activity = bs.get_foreground_host_activity()

    if not activity.globalsnode.paused:
        activity.globalsnode.paused = True

    else:
        activity.globalsnode.paused = False


def rotate_camera():
    activity = _babase.get_foreground_host_activity()

    if activity.globalsnode.camera_mode != 'rotate':
        activity.globalsnode.camera_mode = 'rotate'

    else:
        activity.globalsnode.camera_mode = 'normal'


def create_role(arguments):
    try:
        pdata.create_role(arguments[0])
        try:
            bs.chatmessage(f"role '{arguments[0]}' created")
        except Exception:
            pass
    except:
        return


def add_role_to_player(arguments):
    try:

        session = bs.get_foreground_host_session()
        for i in session.sessionplayers:
            if i.inputdevice.client_id == int(arguments[1]):
                roles = pdata.add_player_role(
                    arguments[0], i.get_v1_account_id())
                try:
                    bs.chatmessage(f"added role '{arguments[0]}' to {i.getname(full=True, icon=True)}")
                except Exception:
                    pass
    except:
        return


def remove_role_from_player(arguments):
    try:
        session = bs.get_foreground_host_session()
        for i in session.sessionplayers:
            if i.inputdevice.client_id == int(arguments[1]):
                roles = pdata.remove_player_role(
                    arguments[0], i.get_v1_account_id())
                try:
                    bs.chatmessage(f"removed role '{arguments[0]}' from {i.getname(full=True, icon=True)}")
                except Exception:
                    pass

    except:
        return


def get_roles_of_player(arguments, clientid):
    try:
        session = bs.get_foreground_host_session()
        roles = []
        reply = ""
        for i in session.sessionplayers:
            if i.inputdevice.client_id == int(arguments[0]):
                roles = pdata.get_player_roles(i.get_v1_account_id())

        for role in roles:
            reply = reply + role + ","
        send(reply, clientid)
    except:
        return


def change_role_tag(arguments):
    try:
        pdata.change_role_tag(arguments[0], arguments[1])
        try:
            bs.chatmessage(f"role '{arguments[0]}' tag changed")
        except Exception:
            pass
    except:
        return


def set_custom_tag(arguments):
    try:
        if len(arguments) < 2:
            return  # Need at least client ID and some tag text
        
        client_id = arguments[0]
        tag_text = " ".join(arguments[1:])  # Combine all remaining arguments
        
        session = bs.get_foreground_host_session()
        for i in session.sessionplayers:
            if i.inputdevice.client_id == int(client_id):
                roles = pdata.set_tag(tag_text, i.get_v1_account_id())
                try:
                    bs.chatmessage(f"custom tag set for {i.getname(full=True, icon=True)}")
                except Exception:
                    pass
    except:
        return

def remove_custom_tag(arguments):
    try:
        session = bs.get_foreground_host_session()
        for i in session.sessionplayers:
            if i.inputdevice.client_id == int(arguments[0]):
                pdata.remove_tag(i.get_v1_account_id())
                try:
                    bs.chatmessage(f"custom tag removed for {i.getname(full=True, icon=True)}")
                except Exception:
                    pass
    except:
        return


def remove_custom_effect(arguments):
    try:
        session = bs.get_foreground_host_session()
        # Usage:
        # /removeeffect <client_id> -> remove all effects
        # /removeeffect <effect_name> <client_id> -> remove only that effect
        if not arguments:
            return
        if len(arguments) == 1:
            target_cid = int(arguments[0])
            for i in session.sessionplayers:
                if i.inputdevice.client_id == target_cid:
                    pdata.remove_effect(i.get_v1_account_id())
                    try:
                        bs.chatmessage(f"All custom effects removed for {i.getname(full=True, icon=True)}")
                    except Exception:
                        pass
                    return
        elif len(arguments) >= 2:
            eff_name = arguments[0]
            target_cid = int(arguments[1])
            for i in session.sessionplayers:
                if i.inputdevice.client_id == target_cid:
                    # Remove only this effect if present
                    try:
                        custom = pdata.get_custom()
                        acc = i.get_v1_account_id()
                        current = custom.get('customeffects', {}).get(acc, [])
                        if isinstance(current, str):
                            current = [current]
                        if eff_name in current:
                            current = [e for e in current if e != eff_name]
                            if current:
                                custom['customeffects'][acc] = current
                            else:
                                custom['customeffects'].pop(acc, None)
                            pdata.CacheData.custom = custom
                            try:
                                bs.chatmessage(f"Effect '{eff_name}' removed for {i.getname(full=True, icon=True)}")
                            except Exception:
                                pass
                        else:
                            try:
                                bs.chatmessage(f"Effect '{eff_name}' not found for {i.getname(full=True, icon=True)}")
                            except Exception:
                                pass
                    except Exception:
                        pass
                    return
    except Exception:
        return


VALID_EFFECTS = ['aure', 'aurora', 'chispitas', 'darkmagic', 'darksn', 'distortion', 'fairydust', 'fire', 'firespark', 'footprint', 'galaxy', 'glow', 'highlightshine', 'ice', 'iceground', 'iceman', 'metal', 'orbguard', 'rainbow', 'randblink', 'randomcharacter', 'scorch', 'shine', 'slime', 'spark', 'sparkground', 'splinter', 'stars', 'surrounderhead', 'sweat', 'sweatground', 'nebulashards', 'thunderaura', 'voidrift', 'crystalwings', 'premiumhalo', 'solarcrown', 'pet', 'minipet']

def set_custom_effect(arguments):
    try:
        effect_name = arguments[0]
        # Validate effect name
        if effect_name not in VALID_EFFECTS:
            bs.chatmessage(
                f"❌ Unknown effect '{effect_name}'."
            )
            return
        session = bs.get_foreground_host_session()
        for i in session.sessionplayers:
            if i.inputdevice.client_id == int(arguments[1]):
                acc = i.get_v1_account_id()
                custom = pdata.get_custom()
                effs = custom.get('customeffects', {}).get(acc, [])
                if isinstance(effs, str):
                    effs = [effs]
                if effect_name in effs:
                    try:
                        bs.chatmessage(f"⚠️ Effect '{effect_name}' is already applied to {i.getname(full=True, icon=True)}")
                    except Exception:
                        pass
                    return
                if len(effs) >= 2:
                    try:
                        bs.chatmessage(f"⚠️ Max 2 effects allowed; '{effect_name}' not added for {i.getname(full=True, icon=True)}")
                    except Exception:
                        pass
                    return
                pdata.set_effect(effect_name, acc)
                try:
                    bs.chatmessage(f"✅ Effect '{effect_name}' added to {i.getname(full=True, icon=True)}")
                except Exception:
                    pass
    except:
        return


all_commands = ["attack","target","changetag","banlist", "createrole", "addrole", "removerole",
                "addcommand", "addcmd", "removecommand", "removecmd", "kick",
                "remove", "rm", "end", "next", "quit", "restart", "mute",
                "mutechat", "unmute", "unmutechat", "sm", "slow", "slowmo",
                "nv", "night", "dv", "day", "pause", "pausegame", "cameraMode",
                "camera_mode", "rotate_camera", "kill", "die", "heal", "heath",
                "curse", "cur", "sleep", "sp", "superpunch", "gloves", "punch",
                "shield", "protect", "freeze", "ice", "unfreeze", "thaw", "gm",
                "godmode", "fly", "inv", "invisible", "hl", "headless",
                "creepy", "creep", "celebrate", "celeb", "spaz","pme","say","hug","hugall","cc","spaz"
                "ccall","spazall","acl","control","exchange","icy","box","boxall","kickall","floater"]


def add_command_to_role(arguments):
    try:
        if len(arguments) == 2:
            pdata.add_command_role(arguments[0], arguments[1])
        else:
            bs.chatmessage("invalid command arguments")
    except:
        return


def remove_command_to_role(arguments):
    try:
        if len(arguments) == 2:
            pdata.remove_command_role(arguments[0], arguments[1])
    except:
        return


# def whitelst_it(accountid : str, arguments):
#     settings = setting.get_settings_data()

#     if arguments[0] == 'on':
#         if settings["white_list"]["whitelist_on"]:
#             bs.chatmessage("Already on")
#         else:
#             settings["white_list"]["whitelist_on"] = True
#             setting.commit(settings)
#             bs.chatmessage("whitelist on")
#             from tools import whitelist
#             whitelist.Whitelist()
#         return

#     elif arguments[0] == 'off':
#         settings["white_list"]["whitelist_on"] = False
#         setting.commit(settings)
#         bs.chatmessage("whitelist off")
#         return

# else:
#     rost = bs.get_game_roster()

#     for i in rost:
#         if i['client_id'] == int(arguments[0]):
#             add_to_white_list(i['account_id'], i['display_string'])
#             bs.chatmessage(str(i['display_string'])+" whitelisted")
#             add_commit_to_logs(accountid+" added "+i['account_id'])


def spectators(arguments):
    if arguments[0] in ['on', 'off']:
        settings = setting.get_settings_data()

        if arguments[0] == 'on':
            settings["white_list"]["spectators"] = True
            setting.commit(settings)
            bs.chatmessage("spectators on")

        elif arguments[0] == 'off':
            settings["white_list"]["spectators"] = False
            setting.commit(settings)
            bs.chatmessage("spectators off")


def execute_discord_command(command, arguments, author_name):
    """
    Execute commands from Discord bot
    
    Parameters:
        command : str - The command name
        arguments : list - Command arguments
        author_name : str - Discord username who executed the command
    """
    # Create mock clientid and accountid for Discord commands
    discord_client_id = -abs(hash(author_name)) % 100000
    discord_account_id = f"discord_{author_name}"
    
    # Execute the command
    ExcelCommand(command, arguments, discord_client_id, discord_account_id)
    
    # Log the command execution
    print(f"Discord command executed: {command} {arguments} by {author_name}")

def change_lobby_check_time(arguments):
    try:
        argument = int(arguments[0])
    except:
        bs.chatmessage("must type number to change lobby check time")
        return
    settings = setting.get_settings_data()
    settings["white_list"]["lobbychecktime"] = argument
    setting.commit(settings)
    bs.chatmessage(f"lobby check time is {argument} now")
