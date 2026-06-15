from .Handlers import handlemsg, handlemsg_all, send, clientid_to_myself
from playersData import pdata
from bascenev1lib.actor.zoomtext import ZoomText
# from tools.whitelist import add_to_white_list, add_commit_to_logs
from serverData import serverdata
from chathandle.chatcommands.commands import normal_commands as nc
import babase
import bascenev1 as bs
import os, json
import time
import setting
import babase.internal
import _thread
import random
from stats import mystats
from bascenev1lib.gameutils import SharedObjects
from tools import playlist
from tools import logger

Commands = ['hug', 'icy', 'spaz', 'zombieall', 'boxall', 'texall', 'kickall', 'ooh', 'spazall', 'vcl', 'acl']
CommandAliases = ['cc', 'ccall', 'control', 'prot', 'protect', 'zoommessage', 'zm','say', 'pme', 'zombie', 'rainbow', 'ooh', 'playsound', 'tex', 'hugall', 'box', 'ac', 'exchange', 'tint', 'say', 'playsound', 'admincmdlist', 'vipcmdlist']


def NewCommands(command, arguments, clientid, accountid):
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
    if command == 'hug':
        hug(arguments, clientid)
        
    elif command == 'hugall':
        hugall(arguments, clientid)
    
    elif command in ['control', 'exchange']:
        control(arguments, clientid)

    elif command == 'icy':
        icy(arguments, clientid)
        
    elif command in ['cc', 'spaz']:
        spaz(arguments, clientid)

    elif command in ['ccall', 'spazall']:
        spazall(arguments, clientid)
        
    elif command == 'ac':
        ac(arguments, clientid)
        
    elif command == 'tint':
        tint(arguments, clientid)

    elif command == 'box':
        box(arguments, clientid)

    elif command == 'boxall':
        boxall(arguments, clientid)
        
    elif command == 'kickall':
        kickall(arguments, clientid)

    elif command == 'tex':
        tex(arguments, clientid)

    elif command == 'zombie':
        zombie(arguments, clientid)

    elif command == 'zombieall':
        zombieall(arguments, clientid)
 
    elif command == 'texall':
        texall(arguments, clientid)
        
    elif command == 'say':
        server_chat(arguments, clientid)
        
    elif command in ['acl', 'admincmdlist']:
        acl(arguments, clientid)
        
    elif command == 'ooh':
        play_ooh_sound(arguments)

    elif command in ['zm', 'zoommessage']:
        zm(arguments, clientid)

    elif command == 'playsound':
        play_sound(arguments, clientid)

    elif command in ['vcl', 'vipcmdlist']:
        vcl(arguments, clientid)     

    elif command in ['prot', 'protect']:
        protect_players(arguments, clientid)     
       
    elif command == 'pme':
        stats_to_clientid(arguments, clientid, accountid)        


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
                     tickets = nc.getcoins(pbid)
                     reply = (
                         f"\ue048| Name: {fname}\n"
                         f"\ue048| PB-ID: {stats['aid']}\n"
                         f"\ue048| Tickets: {tickets}\U0001FA99\n"
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
         
                    
def hug(arguments, clientid):
    activity = bs.get_foreground_host_activity()
    if arguments == [] or arguments == ['']:
     with bs.Context(activity):
        send(f"Using: /hugall [or] /hug [player1Index] [player2Index]", clientid)
    else:
        try:
            activity.players[int(arguments[0])].actor.node.hold_node = activity.players[int(arguments[1])].actor.node
        except:
            pass
            
            
def hugall(arguments, clientid):
    activity = bs.get_foreground_host_activity()
    with bs.Context(activity):    
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
            if i['client_id'] != clientid:
                bs.disconnect_client(i['client_id'])
    except:
        pass
        
        
def server_chat(arguments, clientid):
    if arguments == []:
        bs.broadcastmessage('Usage: /say <text to send>', transient=True, clients=[clientid])
    else:
        message = " ".join(arguments)
        bs.chatmessage(message)
        
  
def box(arguments, clientid):
   activity = bs.get_foreground_host_activity()
   with bs.Context(activity):
    try:
        try:
            if arguments != []:
                n = int(arguments[0])      
            activity.players[n].actor.node.torso_model = bs.getmodel("tnt");
            activity.players[n].actor.node.color_mask_texture = bs.gettexture("tnt");
            activity.players[n].actor.node.color_texture = bs.gettexture("tnt") 
            activity.players[n].actor.node.highlight = (1,1,1)
            activity.players[n].actor.node.color = (1,1,1);
            activity.players[n].actor.node.head_model = None;
            activity.players[n].actor.node.style = "cyborg";
        except:
            send(f"Using: /boxall [or] /box [PlayerID]", clientid)
    except:
        send(f"Using: /boxall [or] /box [PlayerID]", clientid)

         #BOXALL
def boxall(arguments, clientid):
   activity = bs.get_foreground_host_activity()
   with bs.Context(activity):    
    try:
        for i in activity.players:
            try:
                i.actor.node.torso_model = bs.getmodel("tnt")
                i.actor.node.color_mask_texture = bs.gettexture("tnt")
                i.actor.node.color_texture = bs.gettexture("tnt")
                i.actor.node.highlight = (1,1,1)
                i.actor.node.color = (1,1,1)
                i.actor.node.head_model = None
                i.actor.node.style = "cyborg"
            except:
                pass
    except:
        pass


def ac(arguments, clientid):
   activity = bs.get_foreground_host_activity()
   a = arguments
   with bs.Context(activity):
    try:
        if arguments[0] == 'r':
            m = 1.3 if a[1] is None else float(a[1])
            s = 1000 if a[2] is None else float(a[2])
            bs.animate_array(activity.globalsnode, 'ambient_color',3, {0: (1*m,0,0), s: (0,1*m,0),s*2:(0,0,1*m),s*3:(1*m,0,0)},True)
        else:
            try:
                if a[1] is not None:
                    activity.globalsnode.ambient_color = (float(a[0]),float(a[1]),float(a[2]))
            except:
                pass
    except:
        send(f"Using: '/ac [Red] [Green] [Blue]' or '/ac r [brightness] [speed]'", clientid)


def tint(arguments, clientid):
   activity = bs.get_foreground_host_activity()
   a = arguments
   with bs.Context(activity):
    try:
        if arguments[0] == 'r':
            m = 1.3 if a[1] is None else float(a[1])
            s = 1000 if a[2] is None else float(a[2])
            bs.animate_array(activity.globalsnode, 'tint',3, {0: (1*m,0,0), s: (0,1*m,0),s*2:(0,0,1*m),s*3:(1*m,0,0)},True)
        else:
            try:
                if a[1] is not None:
                    activity.globalsnode.tint = (float(a[0]),float(a[1]),float(a[2]))
            except:
                pass
    except:
        send(f"Using: '/tint [Red] [Green] [Blue]' or '/tint r [brightness] [speed]'", clientid)


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


def spazall(arguments, clientid):
    activity = bs.get_foreground_host_activity()
    a = arguments
    with bs.Context(activity):
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


def zombie(arguments, clientid):
 activity = bs.get_foreground_host_activity()
 a = arguments
 with bs.Context(activity):
    try:
        try:
            if arguments != []:
                n = int(a[0])
            activity.players[n].actor.node.color_texture = bs.gettexture("agentColor")
            activity.players[n].actor.node.color_mask_texture = bs.gettexture("pixieColorMask")
            activity.players[n].actor.node.head_model = bs.getmodel("zoeHead")
            activity.players[n].actor.node.torso_model = bs.getmodel("bonesTorso")
            activity.players[n].actor.node.pelvis_model = bs.getmodel("pixiePelvis")
            activity.players[n].actor.node.upper_arm_model = bs.getmodel("frostyUpperArm")
            activity.players[n].actor.node.forearm_model = bs.getmodel("frostyForeArm")
            activity.players[n].actor.node.hand_model = bs.getmodel("bonesHand")
            activity.players[n].actor.node.upper_leg_model = bs.getmodel("bonesUpperLeg")
            activity.players[n].actor.node.lower_leg_model = bs.getmodel("pixieLowerLeg")
            activity.players[n].actor.node.toes_model = bs.getmodel("bonesToes")
            activity.players[n].actor.node.color = (0,1,0)
            activity.players[n].actor.node.highlight = (0.6,0.6,0.6)
            activity.players[n].actor.node.style = "spaz"
        except:
            send(f"Using: /zombieall [or] /zombie [PlayerID]", clientid)
    except:
        send(f"Using: /zombieall [or] /zombie [PlayerID]", clientid)


def zombieall(arguments, clientid):
 activity = bs.get_foreground_host_activity()
 a = arguments
 with bs.Context(activity):
    for i in activity.players:
        try:
            i.actor.node.color_texture = bs.gettexture("agentColor")
            i.actor.node.color_mask_texture = bs.gettexture("pixieColorMask")
            i.actor.node.head_model = bs.getmodel("zoeHead")
            i.actor.node.torso_model = bs.getmodel("bonesTorso")
            i.actor.node.pelvis_model = bs.getmodel("pixiePelvis")
            i.actor.node.upper_arm_model = bs.getmodel("frostyUpperArm")
            i.actor.node.forearm_model = bs.getmodel("frostyForeArm")
            i.actor.node.hand_model = bs.getmodel("bonesHand")
            i.actor.node.upper_leg_model = bs.getmodel("bonesUpperLeg")
            i.actor.node.lower_leg_model = bs.getmodel("pixieLowerLeg")
            i.actor.node.toes_model = bs.getmodel("bonesToes")
            i.actor.node.color = (0,1,0)
            i.actor.node.highlight = (0.6,0.6,0.6)
            i.actor.node.style = "spaz"
        except:
            send(f"Using: /zombieall [or] /zombie [PlayerID]", clientid)


def tex(arguments, clientid):
 activity = bs.get_foreground_host_activity()
 a = arguments
 with bs.Context(activity):
    try:
        if len(a) > 1: n = int(a[0])
        color = None
        if (len(a) > 1) and (str(a[1]) == 'kronk'): color = str(a[1])
        else:color = str(a[1]) + 'Color'
        try:
            activity.players[n].actor.node.color_mask_texture= bs.gettexture(str(a[1]) + 'ColorMask')
            activity.players[n].actor.node.color_texture= bs.gettexture(color)
        except:
            send(f"Using: /texall [texture] [or] /tex [PlayerID] [texture]", clientid)
    except:
        send(f"Using: /texall [texture] [or] /tex [PlayerID] [texture]", clientid)


def texall(arguments, clientid):
 activity = bs.get_foreground_host_activity()
 a = arguments
 with bs.Context(activity):
    try:
        color = None
        if str(a[0]) == 'kronk':
            color = str(a[0])
        else:color = str(a[0]) + 'Color'
        for i in activity.players:
            try:
                i.actor.node.color_mask_texture= bs.gettexture(str(a[0]) + 'ColorMask')
                i.actor.node.color_texture= bs.gettexture(color)
            except:
                pass
    except:
        send(f"Using: /texall [texture] [or] /tex [PlayerID] [texture]", clientid)


def control(arguments, clientid):
 activity = bs.get_foreground_host_activity()
 a = arguments
 with bs.Context(activity):
    try:
        if True:
            try:
                player1 = int(a[0])
            except:
                pass
            try:
                player2 = int(a[1])
            except:
                pass
        node1 = activity.players[player1].actor.node
        node2 = activity.players[player2].actor.node
        activity.players[player1].actor.node = node2
        activity.players[player2].actor.node = node1         
    except:
        send(f"Using: /exchange [PlayerID1] [PlayerID2]", clientid)
 
       
def zm(arguments, clientid):
    if len(arguments) == 0:
        bs.broadcastmessage("Special Chat Only For Main", color=(1,1,1), transient=True, clients=[clientid])
    else:
        k = ' '.join(arguments)
        with bs.Context(bs.get_foreground_host_activity()):
            ZoomText(
                k,
                position=(0, 180),
                maxwidth=800,
                lifespan=1,
                color=(0.93*1.25, 0.9*1.25, 1.0*1.25),
                trailcolor=(0.15, 0.05, 1.0, 0.0),
                flash=False,             
                jitter=3.0
            ).autoretain()


def icy(arguments, clientid):
 activity = bs.get_foreground_host_activity()
 a = arguments
 with bs.Context(activity):
    try:
        if True:
            try:
                player1 = int(a[0])
            except:
                pass
            try:
                player2 = int(a[1])
            except:
                pass
        node1 = activity.players[player2].actor.node
        activity.players[player1].actor.node = node1         
    except:
        send(f"Using: /icy [PlayerID1] [PlayerID2]", clientid)
        
        
def play_ooh_sound(arguments):
  activity = bs.get_foreground_host_activity()
  with bs.Context(activity):  
    try:
        a = arguments
        if a is not None and len(a) > 0:
            times = int(a[0])
            def ooh_recursive(c):
                bs.playsound(bs.getsound('ooh'), volume=2)
                c -= 1
                if c > 0:
                    bs.Timer(int(a[1]) if len(a) > 1 and a[1] is not None else 1000, bs.Call(ooh_recursive, c=c))
            ooh_recursive(c=times)
        else:
            bs.playsound(bs.getsound('ooh'), volume=2)
    except Exception as e:
        pass


def play_sound(arguments, clientid):
  activity = bs.get_foreground_host_activity()
  with bs.Context(activity):  
    try:
        a = arguments  # Assign arguments to 'a'
        if a is not None and len(a) > 0:
            sound_name = str(a[0])
            times = int(a[1]) if len(a) > 1 else 1  # Set default times to 1 if not provided
            volume = float(a[2]) if len(a) > 2 else 2.0  # Set default volume to 2.0 if not provided
            def play_sound_recursive(c):
                bs.playsound(bs.getsound(sound_name), volume=volume)
                c -= 1
                if c > 0:
                    bs.Timer(int(a[3]) if len(a) > 3 and a[3] is not None else 1000, bs.Call(play_sound_recursive, c=c))
            play_sound_recursive(c=times)
        else:
            send(f"Using: /playsound [music sound] [time] [volume]", clientid)
    except Exception as e:
        send(f"Using: /playsound [music sound] [time] [volume]", clientid)
        

def protect_players(arguments, clientid):
    if arguments == [] or arguments == ['']:
        myself = clientid_to_myself(clientid)
        activity = bs.get_foreground_host_activity()
        player = activity.players[myself].actor
        
        if player.node.invincible != True:
            player.node.invincible = True 
        else:
            player.node.invincible = False 
    
    elif arguments[0] == 'all':
        activity = bs.get_foreground_host_activity()
        for i in activity.players:
            if i.actor.node.invincible != True:
                i.actor.node.invincible = True 
            else:
                i.actor.node.invincible = False 
    
    else:
        activity = bs.get_foreground_host_activity()
        req_player = int(arguments[0])
        player = activity.players[req_player].actor
        
        if player.node.invincible != True: 
            player.node.invincible = True 
        else:
            player.node.invincible = False

        
def acl(arguments, client_id):
    role = "admin"
    admin_commands = pdata.roles_cmdlist(role)
    if not admin_commands:
        send("Error: Admin role not found.", client_id)
        return
    msg = "\ue046______________|ADMIN-CMDS-LISTS|________________\ue046\n"
    admin_commands_list = admin_commands.split(', ')
    for i, cmd in enumerate(admin_commands_list, 1):
        if i % 10 == 0:
            msg += "\n\ue046 || " + cmd
        elif i == 1:  # Add \ue046 || only to the first command of each line
            msg += "\ue046 || " + cmd
        else:
            msg += ', ' + cmd
    send(msg, client_id)


def vcl(arguments, client_id):
    role = "vip"
    admin_commands = pdata.roles_cmdlist(role)
    if not admin_commands:
        send("Error: Vip role not found.", client_id)
        return
    msg = "\ue046______________|VIP-CMDS-LISTS|________________\ue046\n"
    admin_commands_list = admin_commands.split(', ')
    for i, cmd in enumerate(admin_commands_list, 1):
        if i % 10 == 0:
            msg += "\n\ue046 || " + cmd
        elif i == 1:  # Add \ue046 || only to the first command of each line
            msg += "\ue046 || " + cmd
        else:
            msg += ', ' + cmd
    send(msg, client_id)