#  Electronic Voting Machine (EVM) by -mr.smoothy

import time

import _babase
import _bascenev1

import bascenev1 as bs
from tools import playlist as playlist_tools

game_started_on = 0

vote_machine = {
    "end": {
        "last_vote_start_time": 0,
        "vote_duration": 50,
        "min_game_duration_to_start_vote": 30,
        "voters": []
    },
    "sm": {
        "last_vote_start_time": 0,
        "vote_duration": 50,
        "min_game_duration_to_start_vote": 1,
        "voters": []
    },
    "nv": {
        "last_vote_start_time": 0,
        "vote_duration": 50,
        "min_game_duration_to_start_vote": 1,
        "voters": []
    },
    "dv": {
        "last_vote_start_time": 0,
        "vote_duration": 50,
        "min_game_duration_to_start_vote": 1,
        "voters": []
    },
    # playlist vote (vp)
    "vp": {
        "last_vote_start_time": 0,
        "vote_duration": 50,
        "min_game_duration_to_start_vote": 1,
        "voters": [],
        "target": None  # playlist key being voted on
    },
}


def vote(pb_id, client_id, vote_type, payload=None):
    global vote_machine
    voters = vote_machine[vote_type]["voters"]
    last_vote_start_time = vote_machine[vote_type]["last_vote_start_time"]
    vote_duration = vote_machine[vote_type]["vote_duration"]
    min_game_duration_to_start_vote = vote_machine[vote_type][
        "min_game_duration_to_start_vote"]

    now = time.time()

    # Handle playlist-vote target tracking/reset
    if vote_type == "vp":
        current_target = vote_machine["vp"].get("target")
        requested_target = payload
        # Expired vote window -> reset and set new target
        if now > last_vote_start_time + vote_duration:
            voters = []
            vote_machine[vote_type]["last_vote_start_time"] = now
            vote_machine[vote_type]["target"] = requested_target
        else:
            # If a different target is requested mid-vote, restart vote for new target
            if requested_target and current_target and requested_target != current_target and len(voters) > 0:
                voters = []
                vote_machine[vote_type]["last_vote_start_time"] = now
                vote_machine[vote_type]["target"] = requested_target
            elif requested_target and current_target is None:
                vote_machine[vote_type]["target"] = requested_target
    else:
        # Non-vp: expire window resets voters and start time
        if now > last_vote_start_time + vote_duration:
            voters = []
            vote_machine[vote_type]["last_vote_start_time"] = now

    if now < game_started_on + min_game_duration_to_start_vote:
        bs.broadcastmessage(
            "Seems game just started, Try again after some time",
            transient=True,
            clients=[client_id])
        return

    # Announce vote start
    if len(voters) == 0:
        if vote_type == "vp":
            tgt = vote_machine["vp"].get("target") or "unknown"
            bs.chatmessage(f"playlist vote started for '{tgt}'. Type 1 to vote")
        else:
            bs.chatmessage(f"{vote_type} vote started")

    # clean up voters list
    active_players = []
    for player in bs.get_game_roster():
        active_players.append(player['account_id'])
    for voter in list(voters):
        if voter not in active_players:
            voters.remove(voter)
    if pb_id not in voters:
        voters.append(pb_id)
        bs.broadcastmessage(
            f'Thanks for vote , encourage other players to type {vote_type} too.',
            transient=True,
            clients=[client_id])
        if vote_type == 'end':
            update_vote_text(max_votes_required(
                len(active_players)) - len(voters))
        else:
            activity = bs.get_foreground_host_activity()
            if activity is not None:
                with activity.context:
                    remaining = max_votes_required(len(active_players)) - len(voters)
                    # Custom message for playlist vote
                    if vote_type == 'vp':
                        tgt = vote_machine["vp"].get("target") or payload or "unknown"
                        msg = f"{remaining} more votes for playlist '{tgt}' (type 1)"
                    else:
                        msg = f"{remaining} votes required for {vote_type}"
                    bs.broadcastmessage(
                        msg,
                        image={"texture": bs.gettexture(
                            "achievementSharingIsCaring"),
                               "tint_texture": bs.gettexture(
                                   "achievementSharingIsCaring"),
                               "tint_color": (0.5, 0.5, 0.5),
                               "tint2_color": (0.7, 0.5, 0.9)},
                        top=True)
    vote_machine[vote_type]["voters"] = voters

    if len(voters) >= max_votes_required(len(active_players)):
        if vote_type == "vp":
            tgt = vote_machine["vp"].get("target") or payload or "unknown"
            bs.chatmessage(f"playlist vote succeed; applying '{tgt}'")
        else:
            bs.chatmessage(f"{vote_type} vote succeed")
        vote_machine[vote_type]["voters"] = []
        if vote_type == "end":
            try:
                activity = bs.get_foreground_host_activity()
                with activity.context:
                    bs.get_foreground_host_activity().end_game()
            except Exception:
                pass
        elif vote_type == "nv":
            _bascenev1.chatmessage("/nv")
        elif vote_type == "dv":
            _bascenev1.chatmessage("/dv")
        elif vote_type == "sm":
            _bascenev1.chatmessage("/sm")
        elif vote_type == "vp":
            try:
                # Apply selected playlist via tools.playlist helper
                tgt = vote_machine["vp"].get("target") or payload
                if tgt:
                    playlist_tools.setPlaylist(tgt)
            except Exception:
                pass


def reset_votes():
    global vote_machine
    for key, value in vote_machine.items():
        value["voters"] = []
        if key == "vp":
            value["target"] = None


def max_votes_required(players):
    if players == 2:
        return 1
    elif players == 3:
        return 2
    elif players == 4:
        return 2
    elif players == 5:
        return 3
    elif players == 6:
        return 3
    elif players == 7:
        return 4
    elif players == 8:
        return 4
    elif players == 10:
        return 5
    else:
        return players - 5


def update_vote_text(votes_needed):
    activity = bs.get_foreground_host_activity()
    try:
        activity.end_vote_text.node.text = "{} more votes to end this map\ntype 'end' to vote".format(
            votes_needed)
    except Exception:
        activity = bs.get_foreground_host_activity()
        with activity.context:
            node = bs.NodeActor(bs.newnode('text',
                                           attrs={
                                               'v_attach': 'top',
                                               'h_attach': 'center',
                                               'h_align': 'center',
                                               'color': (1, 1, 0.5, 1),
                                               'flatness': 0.5,
                                               'shadow': 0.5,
                                               'position': (-200, -30),
                                               'scale': 0.7,
                                               'text': '{} more votes to end this map \n type \'end\' to vote'.format(
                                                   votes_needed)
                                           })).autoretain()
            activity.end_vote_text = node
            bs.timer(20, remove_vote_text)


def remove_vote_text():
    activity = bs.get_foreground_host_activity()
    if hasattr(activity,
               "end_vote_text") and activity.end_vote_text.node.exists():
        activity.end_vote_text.node.delete()


def is_vp_vote_active() -> bool:
    """Return True if a playlist vote is currently active (not expired)."""
    info = vote_machine.get("vp", {})
    if not info or info.get("target") is None:
        return False
    now = time.time()
    return now <= info.get("last_vote_start_time", 0) + info.get("vote_duration", 0)


def get_vp_target() -> str | None:
    return vote_machine.get("vp", {}).get("target")
