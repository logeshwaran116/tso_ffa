# -*- coding: utf-8 -*-
# Notification manager - sends browser push via external Deno service (no Python cffi)
# Optimized to avoid server lag:
# - All network calls are async via threads
# - Short, bounded HTTP timeouts
# - Cooldown set to 7 minutes
# - dump_cache interval set to 5 minutes

import ecdsa
import _babase
import base64
import json
import os
import random
import shutil
import string
import time
import urllib.request
import urllib.error
import threading
from datetime import datetime

# Timestamp format stored for last notification per PBID.
date_format = '%Y-%m-%d %H:%M:%S'

# External push sender endpoint (Deno service).
# Override via env: export DENO_PUSH_URL="https://your-deno-domain/send"
DENO_PUSH_URL = os.environ.get('DENO_PUSH_URL', 'https://share-toad-65.deno.dev/send')

# Cooldown: 7 minutes (420s) between notifications per PBID.
COOLDOWN_SECONDS = int(os.environ.get('PUSH_COOLDOWN_SECONDS', '420'))

# Network timeout for push calls (keep small so threads finish quickly).
PUSH_HTTP_TIMEOUT = float(os.environ.get('PUSH_HTTP_TIMEOUT', '3.0'))

# dump_cache write interval: 5 minutes (300s).
DUMP_INTERVAL_SECONDS = int(os.environ.get('DUMP_INTERVAL_SECONDS', '300'))

vapidkeys = {}
subscriptions = {}
subscribed_players = {}
PLAYERS_DATA_PATH = os.path.join(
    _babase.env()["python_directory_user"], "playersdata" + os.sep
)


def _async(fn, *args, **kwargs) -> None:
    """Run fn(*args, **kwargs) in a detached daemon thread."""
    threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True).start()


def get_vapid_keys():
    """Generate or load VAPID keys (writes to .keys in working dir)."""
    global vapidkeys
    if vapidkeys:
        return vapidkeys
    try:
        with open(".keys", "r") as f:
            vapidkeys = json.load(f)
        return vapidkeys
    except Exception:
        pk = ecdsa.SigningKey.generate(curve=ecdsa.NIST256p)
        vk = pk.get_verifying_key()
        vapidkeys = {
            'private_key': base64.urlsafe_b64encode(pk.to_string()).rstrip(b'=').decode('utf-8'),
            'public_key': base64.urlsafe_b64encode(b'\x04' + vk.to_string()).rstrip(b'=').decode('utf-8'),
        }
        with open(".keys", "w") as f:
            json.dump(vapidkeys, f)
        return vapidkeys


def _send_push_sync(subscription, payload):
    """Synchronous HTTP call to Deno push endpoint (run in thread)."""
    try:
        keys = get_vapid_keys()
        body = json.dumps({
            "subscription": subscription,
            "payload": payload,
            "vapid": {
                "public_key": keys["public_key"],
                "private_key": keys["private_key"],
            }
        }).encode("utf-8")
        req = urllib.request.Request(
            DENO_PUSH_URL,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=PUSH_HTTP_TIMEOUT) as resp:
            _ = resp.read()
        # Keep logs light to avoid spam.
        # print("Push notification sent via Deno")
    except Exception as e:
        # Log but never raise (prevent stutter/crash).
        print("Push via Deno failed:", e)


def send_push_notification(subscription, payload):
    """Public API: queue async send so we never block the server thread."""
    _async(_send_push_sync, subscription, payload)


def get_subscriber_id(sub):
    """Return an existing subscriber id for endpoint or create a new one."""
    subscriber_id = None
    endpoint = sub.get("endpoint")
    for key, value in subscriptions.items():
        if value.get("endpoint") == endpoint:
            subscriber_id = key
            break
    if not subscriber_id:
        subscriber_id = generate_random_string(6)
        subscriptions[subscriber_id] = sub
    return subscriber_id


def generate_random_string(length):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


def subscribe(sub, account_id, name):
    """Register a browser subscription to receive notifications for account_id."""
    sid = get_subscriber_id(sub)
    if account_id in subscribed_players:
        if sid not in subscribed_players[account_id]["subscribers"]:
            subscribed_players[account_id]["subscribers"].append(sid)
            subscribed_players[account_id]["name"] = name
    else:
        subscribed_players[account_id] = {"subscribers": [sid], "name": name}

    # Immediate test push sent asynchronously (non-blocking).
    send_push_notification(
        sub,
        {"notification": {"title": "Notification working!", "body": f"Subscribed {name}"}}
    )


def player_joined(pb_id):
    """Notify followers of pb_id when they join (respects cooldown)."""
    now = datetime.now()
    data = subscribed_players.get(pb_id)
    if not data:
        return

    last = data.get("last_notification")
    if last:
        try:
            delta_sec = (now - datetime.strptime(last, date_format)).total_seconds()
        except Exception:
            delta_sec = COOLDOWN_SECONDS + 1
        if delta_sec < COOLDOWN_SECONDS:
            return  # still in cooldown window; skip

    # Update last notification timestamp and send to all subscribers in background.
    data["last_notification"] = now.strftime(date_format)
    name = data.get("name", pb_id)
    players = list(data.get("subscribers", []))  # copy to avoid mutation issues

    def _broadcast():
        for subscriber_id in players:
            sub = subscriptions.get(subscriber_id)
            if not sub:
                continue
            send_push_notification(
                sub,
                {
                    "notification": {
                        "title": f'{name} is playing now',
                        "body": (
                            f'Join {_babase.app.classic.server._config.party_name} '
                            f'server - {name} is waiting for you'
                        ),
                        "icon": "assets/icons/icon-96x96.png",
                        "vibrate": [100, 50, 100],
                        "requireInteraction": True,
                        "data": {"dateOfArrival": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                        "actions": [{"action": "nothing", "title": "Launch Bombsquad"}],
                    }
                }
            )

    _async(_broadcast)


def loadCache():
    """Load subscriptions and subscribed players from disk."""
    global subscriptions, subscribed_players
    try:
        with open(PLAYERS_DATA_PATH + "subscriptions.json", "r") as f:
            subscriptions = json.load(f)
    except Exception:
        try:
            with open(PLAYERS_DATA_PATH + "subscriptions.json.backup", "r") as f:
                subscriptions = json.load(f)
        except Exception:
            subscriptions = {}
    try:
        with open(PLAYERS_DATA_PATH + "subscribed_players.json", "r") as f:
            subscribed_players = json.load(f)
    except Exception:
        try:
            with open(PLAYERS_DATA_PATH + "subscribed_players.json.backup", "r") as f:
                subscribed_players = json.load(f)
        except Exception:
            subscribed_players = {}


def dump_cache():
    """Persist subscription data periodically (should be started in a background thread)."""
    try:
        if subscriptions:
            try:
                shutil.copyfile(
                    PLAYERS_DATA_PATH + "subscriptions.json",
                    PLAYERS_DATA_PATH + "subscriptions.json.backup",
                )
            except Exception:
                pass
            try:
                with open(PLAYERS_DATA_PATH + "subscriptions.json", "w") as f:
                    json.dump(subscriptions, f, indent=4)
            except Exception:
                pass
        if subscribed_players:
            try:
                shutil.copyfile(
                    PLAYERS_DATA_PATH + "subscribed_players.json",
                    PLAYERS_DATA_PATH + "subscribed_players.json.backup",
                )
            except Exception:
                pass
            try:
                with open(PLAYERS_DATA_PATH + "subscribed_players.json", "w") as f:
                    json.dump(subscribed_players, f, indent=4)
            except Exception:
                pass
    finally:
        time.sleep(DUMP_INTERVAL_SECONDS)
        dump_cache()


# Initialize on import.
loadCache()
