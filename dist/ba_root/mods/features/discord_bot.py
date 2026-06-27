import asyncio
import logging
from threading import Thread, Lock
import time
import psutil
import json
import os
import datetime
from stats import mystats

import _babase
import discord
from discord.ext.commands import Bot
from playersdata import pdata as pdata

import babase
import bascenev1 as bs

try:
    from features import leaderboard as _leaderboard
except Exception as e:
    print(f'[leaderboard] Import failed: {e}')
    _leaderboard = None
from babase._general import Call

# Import BombSquad service to read pre-collected team/roster info
try:
    from plugins import bombsquad_service as bss
except Exception:
    # Fallback: direct import if plugins isn't a package
    import bombsquad_service as bss  # type: ignore

logging.getLogger('asyncio').setLevel(logging.WARNING)

def _bs_log_callback(entry: object) -> None:
    """Callback hooked into BombSquad's efro LogHandler for ERROR/WARNING."""
    try:
        from efro.logging import LogLevel
        if not hasattr(entry, 'level') or not hasattr(entry, 'message'):
            return
        if entry.level in (LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL):
            ts = datetime.datetime.now().strftime('%H:%M:%S')
            level = entry.level.name
            push_error_log(f"[{ts}] [{level}] {entry.message.strip()}")
    except Exception:
        pass

def _install_bs_log_callback() -> None:
    """Hook into BombSquad's logging system after app starts."""
    try:
        import baenv
        cfg = baenv.get_config()
        if cfg.log_handler is not None:
            cfg.log_handler.add_callback(_bs_log_callback, feed_existing_logs=False)
            print("Discord error log callback installed.")
        else:
            print("Warning: log_handler not available yet.")
    except Exception as e:
        print(f"Failed to install BS log callback: {e}")

intents = discord.Intents().all()

client = Bot(command_prefix='!', intents=intents)

# Event loop used by the Discord bot; captured in init().
_BOT_LOOP = None

stats = {
    'roster': {},
    'chats': [],
    'playlist': {'current': 'Unknown', 'next': 'Unknown'}
}
livestatsmsgs = []
# Channel IDs - loaded from setting.json (see _load_channel_ids() in init())
LOGS_CHANNEL_ID = 1467401251561017384
ERROR_LOG_CHANNEL_ID = 1502641543193038848  # Channel for errors/warnings
LIVE_STATS_CHANNEL_ID = 1467399612288471162
DIRECT_CMD_CHANNEL_ID = 1467402520828706817
ROLE_CMD_CHANNEL_IDS = [1467421373617143985]
ROLE_CMD_CHANNEL_NAMES = {"roles", "role-commands"}
GAME_INFO_CHANNEL_ID = 1518869292479807530
COMPLAINTS_CHANNEL_ID = 1468269892925915166
COMPLAINT_STAFF_ROLE_ID = 1468270279716245709
CHATLIST_CHANNEL_ID = 0

liveChat = True
errorLogs = False
token = ''
logs = []
_logs_lock = Lock()
_error_logs = []
_error_logs_lock = Lock()  
_send_logs_running = False
_send_error_logs_running = False
_refresh_stats_task = None
_send_logs_task = None
_send_error_logs_task = None
_refresh_game_info_task = None

# Cache for messages in game-info channel: { key -> discord.Message }
game_info_msgs = {}

# Maximum number of chat messages to display
MAX_CHAT_MESSAGES = 40

# Command prefix for Discord bot
DISCORD_COMMAND_PREFIX = 's?'
ROLE_COMMAND_PREFIX = 'sr?'

# JSON file for storing allowed users
ALLOWED_USERS_FILE = 'allowed_users.json'

# Allowed users who can use commands (will be loaded from JSON file)
ALLOWED_USER_IDS = []

def load_allowed_users():
    """Load allowed users from JSON file"""
    global ALLOWED_USER_IDS
    try:
        if os.path.exists(ALLOWED_USERS_FILE):
            with open(ALLOWED_USERS_FILE, 'r') as f:
                data = json.load(f)
                ALLOWED_USER_IDS = data.get('allowed_users', [873566310183878696])
                print(f"Loaded {len(ALLOWED_USER_IDS)} allowed users from {ALLOWED_USERS_FILE}")
        else:
            # Create default file with initial user
            ALLOWED_USER_IDS = [873566310183878696]
            save_allowed_users()
            print(f"Created new {ALLOWED_USERS_FILE} with default user")
    except Exception as e:
        print(f"Error loading allowed users: {e}")
        ALLOWED_USER_IDS = [873566310183878696]
        save_allowed_users()

def save_allowed_users():
    """Save allowed users to JSON file"""
    try:
        data = {
            'allowed_users': ALLOWED_USER_IDS,
            'last_updated': time.time(),
            'total_users': len(ALLOWED_USER_IDS)
        }
        with open(ALLOWED_USERS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(ALLOWED_USER_IDS)} allowed users to {ALLOWED_USERS_FILE}")
    except Exception as e:
        print(f"Error saving allowed users: {e}")

def push_log(msg):
    global logs
    with _logs_lock:
        logs.append(msg)

def push_error_log(msg):
    if not errorLogs:
        return
    if 'WARNING' in msg:  # ← skip warnings
        return
    if 'owner' in msg:
        return
    global _error_logs
    with _error_logs_lock:
        _error_logs.append(msg)

def _load_channel_ids():
    """Load all Discord channel IDs from setting.json."""
    global LOGS_CHANNEL_ID, LIVE_STATS_CHANNEL_ID, DIRECT_CMD_CHANNEL_ID
    global ROLE_CMD_CHANNEL_IDS, GAME_INFO_CHANNEL_ID, COMPLAINTS_CHANNEL_ID
    global COMPLAINT_STAFF_ROLE_ID, CHATLIST_CHANNEL_ID
    try:
        import setting
        setting.refresh_cache()
        data = setting.get_settings_data()
        db = data.get("discordbot", {})
        if db.get("logsChannelID"):
            LOGS_CHANNEL_ID = int(db["logsChannelID"])
        if db.get("liveStatsChannelID"):
            LIVE_STATS_CHANNEL_ID = int(db["liveStatsChannelID"])
        if db.get("directCmdChannelID"):
            DIRECT_CMD_CHANNEL_ID = int(db["directCmdChannelID"])
        if db.get("roleCmdChannelIds"):
            ids = db["roleCmdChannelIds"]
            ROLE_CMD_CHANNEL_IDS = [int(x) for x in ids] if isinstance(ids, list) else [int(ids)]
        if db.get("gameInfoChannelID"):
            GAME_INFO_CHANNEL_ID = int(db["gameInfoChannelID"])
        if db.get("complaintsChannelID"):
            COMPLAINTS_CHANNEL_ID = int(db["complaintsChannelID"])
        if db.get("complaintStaffRoleID"):
            COMPLAINT_STAFF_ROLE_ID = int(db["complaintStaffRoleID"])
        if "chatlistChannelID" in db:
            CHATLIST_CHANNEL_ID = int(db.get("chatlistChannelID") or 0)
    except Exception as e:
        print(f"Discord bot: Could not load channel IDs from setting.json: {e}")

def init():
    # Load allowed users from JSON file
    load_allowed_users()
    # Load all channel IDs from setting.json
    _load_channel_ids()

    global _BOT_LOOP

    _BOT_LOOP = asyncio.new_event_loop()
    asyncio.set_event_loop(_BOT_LOOP)
    _BOT_LOOP.create_task(client.start(token))
    Thread(target=_BOT_LOOP.run_forever, daemon=True).start()

channel = None


class ComplaintView(discord.ui.View):
    """Buttons for complaint staff to mark a complaint as Accepted or Complete."""

    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)
        self._staff_role_id = COMPLAINT_STAFF_ROLE_ID or 1468270279716245709

    def _has_staff_role(self, user) -> bool:
        if not hasattr(user, "roles") or not user.roles:
            return False
        return any(getattr(r, "id", None) == self._staff_role_id for r in user.roles)

    def _copy_embed_update_status(self, embed: discord.Embed, status_value: str) -> discord.Embed:
        new_embed = discord.Embed(
            title=embed.title,
            description=embed.description,
            color=embed.color,
            timestamp=embed.timestamp,
        )
        for f in embed.fields:
            if f.name == "Status":
                continue
            new_embed.add_field(name=f.name, value=f.value, inline=f.inline)
        new_embed.add_field(name="Status", value=status_value, inline=False)
        return new_embed

    def _get_reporter_name_from_embed(self, embed: discord.Embed) -> str:
        for f in embed.fields:
            if f.name != "Reporter":
                continue
            for line in f.value.split("\n"):
                if "**Name:**" in line:
                    name = line.replace("**Name:**", "").strip()
                    name = name.replace("\n", " ").strip()[:90]
                    return name or "Unknown"
        return "Unknown"

    def _get_thread_id_from_embed(self, embed: discord.Embed) -> int | None:
        for f in embed.fields:
            if f.name != "Thread":
                continue
            val = str(f.value or "").strip()
            # Supports Discord thread mention format: <#1234567890>
            if val.startswith("<#") and val.endswith(">"):
                raw = val[2:-1].strip()
                if raw.isdigit():
                    return int(raw)
            # Fallback: first integer-looking token in field value.
            for token in val.replace("<", " ").replace(">", " ").replace("#", " ").split():
                if token.isdigit():
                    return int(token)
        return None

    async def _find_thread_for_message(self, message: discord.Message):
        # Prefer explicit thread reference stored in embed.
        thread_id = None
        if message.embeds:
            thread_id = self._get_thread_id_from_embed(message.embeds[0])
        if thread_id is not None:
            thread = None
            if message.guild is not None:
                thread = message.guild.get_thread(thread_id)
            if thread is None:
                thread = client.get_channel(thread_id)
            if thread is None and message.guild is not None:
                try:
                    thread = await message.guild.fetch_channel(thread_id)
                except Exception:
                    thread = None
            if isinstance(thread, discord.Thread):
                return thread

        parent = message.channel.parent if isinstance(message.channel, discord.Thread) else message.channel
        try:
            threads = await parent.fetch_threads()
        except Exception:
            threads = getattr(parent, "threads", []) or []
        for thread in threads:
            if getattr(thread, "starter_message_id", None) == message.id:
                return thread
        # Try archived threads as a fallback.
        try:
            async for thread in parent.archived_threads(limit=100):
                if getattr(thread, "starter_message_id", None) == message.id:
                    return thread
        except Exception:
            pass
        return None

    @discord.ui.button(label="Complaint Accepted", style=discord.ButtonStyle.success, custom_id="complaint_accepted")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._has_staff_role(interaction.user):
            await interaction.response.send_message("Only Complaint Staff can use this button.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=False)
        embed = interaction.message.embeds[0]
        reporter_name = self._get_reporter_name_from_embed(embed)
        thread_name = f"{reporter_name} complaint"[:100] or "Complaint thread"
        try:
            thread = await interaction.message.create_thread(name=thread_name, auto_archive_duration=10080)
        except Exception as e:
            await interaction.followup.send(f"Could not create thread: {e}", ephemeral=True)
            return
        new_embed = self._copy_embed_update_status(embed, f"Accepted by **{interaction.user.display_name}**")
        new_embed.add_field(name="Thread", value=thread.mention, inline=False)
        for child in self.children:
            if getattr(child, "custom_id", None) == "complaint_accepted":
                child.disabled = True
                break
        await interaction.message.edit(embed=new_embed, view=self)
        try:
            await interaction.followup.send(f"Thread created: {thread.mention}", ephemeral=True)
        except Exception:
            pass

    @discord.ui.button(label="Complaint Complete", style=discord.ButtonStyle.primary, custom_id="complaint_complete")
    async def complete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._has_staff_role(interaction.user):
            await interaction.response.send_message("Only Complaint Staff can use this button.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=False)
        if not interaction.message.embeds:
            await interaction.followup.send("Complaint embed not found on this message.", ephemeral=True)
            return
        embed = interaction.message.embeds[0]
        new_embed = self._copy_embed_update_status(embed, f"Closed by **{interaction.user.display_name}**")
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(embed=new_embed, view=self)
        thread = await self._find_thread_for_message(interaction.message)
        result_msg = "Complaint marked complete."
        if thread:
            try:
                await thread.edit(
                    archived=True,
                    locked=True,
                    reason=f"Complaint closed by {interaction.user.display_name}",
                )
                result_msg = f"Complaint marked complete and thread closed: {thread.mention}"
            except discord.Forbidden:
                result_msg = (
                    "Complaint marked complete, but I could not close the thread. "
                    "Check bot permissions (`Manage Threads`)."
                )
            except Exception as e:
                result_msg = f"Complaint marked complete, but failed to close thread: {e}"
        else:
            result_msg = "Complaint marked complete, but no linked thread was found."
        try:
            await interaction.followup.send(result_msg, ephemeral=True)
        except Exception:
            pass


def send_complaint_embed(
    reporter_name,
    reporter_pbid,
    target_name,
    target_client_id,
    target_pbid,
    reason,
    server_name: str = "",
) -> None:
    """Queue a nicely formatted complaint embed to Discord.

    Safe to call from the BombSquad logic thread; dispatches the
    actual Discord work onto the bot's event loop.
    server_name: name of the BombSquad server (e.g. party name) so you can tell which server sent the complaint.
    """

    # Fallback: if we don't have a loop or bot yet, drop to logs.
    if _BOT_LOOP is None or not getattr(client, "user", None):
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        lines = [
            f"[COMPLAINT] {ts}",
            f"Server: {server_name or 'Unknown'}",
            f"From: {reporter_name} ({reporter_pbid or 'unknown pbid'})",
            f"Target: {target_name or 'Unknown'} "
            f"(cid={target_client_id if target_client_id is not None else 'n/a'}, "
            f"pbid={target_pbid or 'unknown'})",
            f"Reason: {reason}",
        ]
        push_log("\n".join(lines))
        return

    def _trim_for_embed(text: str, limit: int = 1000) -> str:
        val = str(text or "").strip()
        if len(val) <= limit:
            return val
        return val[: limit - 3] + "..."

    def _get_linked_accounts_text(pbid: str | None) -> str:
        if not pbid:
            return "Unknown PBID"
        try:
            info = pdata.get_info(pbid)
            if not isinstance(info, dict):
                return "No linked account data found."

            aliases_raw = info.get("display_string", [])
            if isinstance(aliases_raw, str):
                aliases = [aliases_raw]
            elif isinstance(aliases_raw, list):
                aliases = [str(x).strip() for x in aliases_raw if str(x).strip()]
            else:
                aliases = []

            last_ip = info.get("lastIP")
            device_uuid = info.get("deviceUUID")
            related: list[str] = []
            try:
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
                    other_name = str(other_name or "Unknown")
                    related.append(f"{other_name} (`{other_pbid}`)")
            except Exception:
                pass

            # Preserve order while deduplicating.
            deduped_related = list(dict.fromkeys(related))

            aliases_txt = ", ".join(aliases[:6]) if aliases else "None"
            related_txt = ", ".join(deduped_related[:5]) if deduped_related else "None"
            if len(deduped_related) > 5:
                related_txt += f" (+{len(deduped_related) - 5} more)"

            return _trim_for_embed(
                f"**Aliases:** {aliases_txt}\n"
                f"**Other Linked PBIDs:** {related_txt}"
            )
        except Exception as exc:
            return _trim_for_embed(f"Could not load linked accounts: {exc}")

    async def _send() -> None:
        try:
            channel_id = COMPLAINTS_CHANNEL_ID or LOGS_CHANNEL_ID
            ch = client.get_channel(channel_id)
            if ch is None:
                # Fall back to logs channel if explicit complaints
                # channel is not configured or cannot be found.
                ch = client.get_channel(LOGS_CHANNEL_ID)
            if ch is None:
                # Nowhere to send; bail silently.
                return

            staff_mention = f"<@&{COMPLAINT_STAFF_ROLE_ID}>" if COMPLAINT_STAFF_ROLE_ID else "Complaint Staff"
            title = "New In‑Game Complaint"
            if server_name and server_name.strip():
                title = f"{title} · **{server_name.strip()[:80]}**"
            embed = discord.Embed(
                title=title,
                description=(
                    "A player submitted a complaint from the server.\n\n"
                    f"{staff_mention} please review this report."
                ),
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow(),
            )

            if server_name and server_name.strip():
                embed.add_field(
                    name="Server",
                    value=f"**{server_name.strip()[:256]}**",
                    inline=True,
                )

            embed.add_field(
                name="Reporter",
                value=f"**Name:** {reporter_name}\n"
                f"**PBID:** `{reporter_pbid or 'unknown'}`",
                inline=False,
            )
            embed.add_field(
                name="Reporter Linked Accounts",
                value=_get_linked_accounts_text(reporter_pbid),
                inline=False,
            )

            target_lines = []
            if target_name:
                target_lines.append(f"**Name:** {target_name}")
            if target_client_id is not None:
                target_lines.append(f"**Client ID:** `{target_client_id}`")
            if target_pbid:
                target_lines.append(f"**PBID:** `{target_pbid}`")
            if not target_lines:
                target_lines.append("No target information was available.")

            embed.add_field(
                name="Accused Player",
                value="\n".join(target_lines),
                inline=False,
            )
            embed.add_field(
                name="Accused Linked Accounts",
                value=_get_linked_accounts_text(target_pbid),
                inline=False,
            )

            embed.add_field(
                name="Reason",
                value=reason or "_No reason provided_",
                inline=False,
            )

            view = ComplaintView()
            mention = f"<@&{COMPLAINT_STAFF_ROLE_ID}>" if COMPLAINT_STAFF_ROLE_ID else ""
            await ch.send(embed=embed, view=view, content=mention)
        except Exception as exc:
            # As a last resort, push to text logs so staff can still see it.
            push_log(f"[COMPLAINT-ERROR] Failed to send embed: {exc!r}")

    try:
        asyncio.run_coroutine_threadsafe(_send(), _BOT_LOOP)
    except Exception as exc:
        push_log(f"[COMPLAINT-ERROR] Scheduling failure: {exc!r}")

def _is_role_channel(ch: discord.abc.GuildChannel) -> bool:
    try:
        if ch.id in ROLE_CMD_CHANNEL_IDS:
            return True
    except Exception:
        pass
    try:
        if str(getattr(ch, 'name', '')).lower() in {n.lower() for n in ROLE_CMD_CHANNEL_NAMES}:
            return True
    except Exception:
        pass
    return False

@client.event
async def on_message(message):
    global channel
    
    # Ignore messages from the bot itself
    if message.author == client.user:
        return
        
    channel = message.channel

    # Handle Discord commands with t? prefix - ONLY in direct command channel
    if (message.content.startswith(DISCORD_COMMAND_PREFIX) and 
        message.channel.id == DIRECT_CMD_CHANNEL_ID):
        await handle_discord_command(message)
        return  # Don't process as regular chat message

    # Handle role management commands with r? prefix - ONLY in role channel(s)
    if message.content.startswith(ROLE_COMMAND_PREFIX) and _is_role_channel(message.channel):
        await handle_role_command(message)
        return

    # Regular chat message handling (for logs channel)
    if message.channel.id == LOGS_CHANNEL_ID:
        display_name = message.author.display_name if hasattr(message.author, 'display_name') else message.author.name
        text = f"[DC] {display_name}: {message.content}"
        _babase.pushcall(Call(bs.chatmessage, text), from_other_thread=True)

async def handle_discord_command(message):
    """Handle Discord bot commands with t? prefix in dedicated command channel"""
    content = message.content[len(DISCORD_COMMAND_PREFIX):].strip()
    parts = content.split()
    
    if not parts:
        return
        
    command = parts[0].lower()
    
    # Handle help command first (no authorization required)
    if command == 'help':
        await handle_help_command(message)
        return
    
    # Check if user is allowed to use other commands
    if message.author.id not in ALLOWED_USER_IDS:
        await message.channel.send(f"You are not authorized to use commands. Your ID: {message.author.id}")
        return
        
    arguments = parts[1:] if len(parts) > 1 else []
    
    # Special case for user management commands
    if command == 'adduser' and arguments:
        await handle_add_user_command(message, arguments)
        return
    elif command == 'removeuser' and arguments:
        await handle_remove_user_command(message, arguments)
        return
    elif command == 'userlist':
        await handle_userlist_command(message)
        return
    elif command == 'help':
        await handle_help_command(message)
        return
    
    # Special case: say (broadcast custom speaker name: text to game)
    if command == 'say':
        if not arguments or len(arguments) < 2:
            await message.channel.send("Usage: t?say <name> <message>")
            return
        speaker = arguments[0]
        text = " ".join(arguments[1:])
        try:
            _babase.pushcall(Call(bs.chatmessage, f"{speaker}: {text}"), from_other_thread=True)
            await message.channel.send(f"Sent: {speaker}: {text}")
        except Exception as e:
            await message.channel.send(f"Failed to send say: {e}")
        return

    # Special case: chatlist (view a player's recent chat from logs)
    if command == 'chatlist':
        await handle_chatlist_command(message, arguments)
        return

    # === Moderation lists + pb-id actions (Discord UI) ===
    if command == 'banlist':
        await handle_banlist_command(message)
        return

    if command == 'mutelist':
        await handle_mutelist_command(message)
        return

    if command == 'unban':
        await handle_unban_pbid_command(message, arguments)
        return

    if command == 'unmute':
        await handle_unmute_pbid_command(message, arguments)
        return


    # Map Discord commands to management functions (in-game)
    command_map = {
        'sm': 'slow_motion',
        'pause': 'pause',
        'customeffect': 'set_custom_effect',
        'removeeffect': 'remove_custom_effect',
        'customtag': 'set_custom_tag',
        'addcmd': 'add_command_to_role',
        'kick': 'kick',
        'ban': 'ban',
        'nv': 'nv',
        'recents': 'get_recents',
        'restart': 'quit',
        'end': 'end',
        'mute': 'mute',
        'unmute': 'unmute',
        'pme': 'stats_to_clientid',
        'rm': 'remove',
        'slowmo': 'slow_motion',
        'slow': 'slow_motion',
        'next': 'end',
        'quit': 'quit',
        'mutechat': 'mute',
        'unmutechat': 'un_mute',
        'remove': 'remove',
        'control': 'control',
        'exchange': 'control',
        'say': 'server_chat',
        'hug': 'hug',
        'hugall': 'hugall',
        'icy': 'icy',
        'spaz': 'spaz',
        'cc': 'spaz',
        'spazall': 'spazall',
        'ccall': 'spazall',
        'box': 'box',
        'boxall': 'boxall',
        'kickall': 'kickall',
        'acl': 'acl',
        'adduser': 'add_user',
        'removeuser': 'remove_user',
        'userlist': 'user_list'
    }
    
    # Get the actual function name
    func_name = command_map.get(command)
    if not func_name:
        await message.channel.send(f"Unknown command: `{command}`")
        return
    
    try:
        # Execute the command in BombSquad thread
        _babase.pushcall(
            Call(execute_management_command, func_name, arguments, message.author.name, message.author.id), 
            from_other_thread=True
        )
        
        await message.channel.send(f"Command `{command}` executed successfully by {message.author.mention}!")
        
    except Exception as e:
        await message.channel.send(f"Error executing command `{command}`: {str(e)}")


async def handle_chatlist_command(message, arguments):
    """Show a player's recent chat from server chat logs.

    Usage from Discord (in your chatlist channel):
      t?chatlist <pb-id> [days]

    Example:
      t?chatlist pb-123 1   -> last 1 day
      t?chatlist pb-123 2   -> last 2 days
    """
    # Restrict this command to a specific channel if configured.
    if CHATLIST_CHANNEL_ID and message.channel.id != CHATLIST_CHANNEL_ID:
        return

    if not arguments:
        await message.channel.send("Usage: `t?chatlist <pb-id> [days]`")
        return

    pbid = arguments[0]
    # Default to 1 day if not provided.
    days = 1
    if len(arguments) >= 2:
        try:
            days = max(1, int(arguments[1]))
        except Exception:
            await message.channel.send("Days must be a number (e.g. `1` or `2`).")
            return

    # Hard cap to avoid huge scans.
    if days > 7:
        days = 7

    # Locate chat log file; reuse same path logic as in normal_commands.chatlist_command.
    try:
        base = _babase.env().get('python_directory_user')
        if not base:
            raise RuntimeError("python_directory_user not set")
        log_path = os.path.join(base, 'serverdata', 'Chat Logs.log')
    except Exception as exc:
        await message.channel.send(f"Could not locate chat log file: `{exc}`")
        return

    if not os.path.exists(log_path):
        await message.channel.send("Chat log file not found on server.")
        return

    # Threshold time.
    now = datetime.datetime.now()
    threshold = now - datetime.timedelta(days=days)

    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as exc:
        await message.channel.send(f"Failed to read chat log: `{exc}`")
        return

    matched: list[str] = []

    for ln in lines:
        if pbid not in ln:
            continue

        # Try to parse timestamp from the beginning of the line.
        # Common format: "[YYYY-MM-DD HH:MM:SS] ..." or "YYYY-MM-DD HH:MM:SS ..."
        ts_ok = False
        try:
            raw = ln.strip()
            if raw.startswith('[') and len(raw) >= 21:
                ts_str = raw[1:20]
            else:
                ts_str = raw[:19]
            dt = datetime.datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
            if dt >= threshold:
                ts_ok = True
        except Exception:
            # If we can't parse the timestamp, keep the line (better too many than missing).
            ts_ok = True

        if ts_ok:
            matched.append(ln.strip())

    if not matched:
        await message.channel.send(f"No chat messages found for `{pbid}` in the last {days} day(s).")
        return

    # Only show the most recent 50 matching lines to avoid spam.
    matched = matched[-50:]

    # Build one or more messages respecting Discord 2000-char limit.
    header = f"Chat list for `{pbid}` (last {days} day(s))\n"
    block = ""
    messages = []
    for ln in matched:
        line = ln + "\n"
        if len(header) + len(block) + len(line) > 1900:
            messages.append(header + "```text\n" + block + "```")
            block = ""
        block += line
    if block:
        messages.append(header + "```text\n" + block + "```")

    # Send paginated messages with short delay to avoid rate limits.
    for idx, content in enumerate(messages, start=1):
        if len(messages) > 1:
            content_with_page = content + f"\n_Page {idx}/{len(messages)}_"
        else:
            content_with_page = content
        await message.channel.send(content_with_page)
        await asyncio.sleep(1.0)

def _format_mod_entries(entries: list[tuple[str, str, str, str]]) -> list[str]:
    """Return markdown lines for embed descriptions."""
    lines: list[str] = []
    for name, pbid, reason, till in entries:
        lines.append(
            f"- **{name}**  (`{pbid}`)\n"
            f"  - **reason**: {reason}\n"
            f"  - **until**: {till}"
        )
    return lines


def _chunk_text_blocks(lines: list[str], limit: int = 3500) -> list[str]:
    """Chunk lines for Discord embed description limits."""
    chunks: list[str] = []
    cur = ""
    for ln in lines:
        add = (ln + "\n")
        if len(cur) + len(add) > limit and cur:
            chunks.append(cur.rstrip())
            cur = add
        else:
            cur += add
    if cur.strip():
        chunks.append(cur.rstrip())
    return chunks


def _get_ban_entries() -> list[tuple[str, str, str, str]]:
    bl = pdata.get_blacklist()
    ids = (bl.get("ban") or {}).get("ids") or {}
    if not isinstance(ids, dict) or not ids:
        return []
    profiles = pdata.get_profiles()
    out: list[tuple[str, str, str, str]] = []
    for pbid in sorted(ids.keys()):
        entry = ids.get(pbid) or {}
        name = profiles.get(pbid, {}).get("name") or pbid
        reason = entry.get("reason", "N/A")
        till = entry.get("till", "N/A")
        out.append((str(name), str(pbid), str(reason), str(till)))
    return out


def _get_mute_entries() -> list[tuple[str, str, str, str]]:
    bl = pdata.get_blacklist()
    ids = bl.get("muted-ids") or {}
    if not isinstance(ids, dict) or not ids:
        return []
    profiles = pdata.get_profiles()
    out: list[tuple[str, str, str, str]] = []
    for pbid in sorted(ids.keys()):
        entry = ids.get(pbid) or {}
        name = profiles.get(pbid, {}).get("name") or pbid
        reason = entry.get("reason", "N/A")
        till = entry.get("till", "N/A")
        out.append((str(name), str(pbid), str(reason), str(till)))
    return out


async def _send_list_embeds(channel, *, title: str, entries: list[tuple[str, str, str, str]], empty_msg: str):
    if not entries:
        emb = discord.Embed(title=title, description=empty_msg, color=discord.Color.blurple())
        await channel.send(embed=emb)
        return
    lines = _format_mod_entries(entries)
    pages = _chunk_text_blocks(lines, limit=3500)
    for i, page in enumerate(pages, start=1):
        emb = discord.Embed(
            title=title,
            description=page,
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        if len(pages) > 1:
            emb.set_footer(text=f"Page {i}/{len(pages)}")
        await channel.send(embed=emb)
        if len(pages) > 1:
            await asyncio.sleep(0.6)


async def handle_banlist_command(message):
    entries = _get_ban_entries()
    await _send_list_embeds(
        message.channel,
        title="🚫 Ban List",
        entries=entries,
        empty_msg="No players are currently banned.",
    )


async def handle_mutelist_command(message):
    entries = _get_mute_entries()
    await _send_list_embeds(
        message.channel,
        title="🔇 Mute List",
        entries=entries,
        empty_msg="No players are currently muted.",
    )


def _resolve_pbid_from_arg(arg: str) -> str | None:
    if not arg:
        return None
    if arg.startswith("pb-"):
        return arg
    # Optional: allow numeric client-id too
    try:
        cid = int(arg)
    except Exception:
        return None
    try:
        for ros in bs.get_game_roster():
            if ros.get("client_id") == cid:
                return ros.get("account_id")
    except Exception:
        pass
    return None


async def handle_unban_pbid_command(message, arguments):
    if not arguments:
        await message.channel.send("Usage: `t?unban pb-...`")
        return
    pbid = _resolve_pbid_from_arg(arguments[0].strip())
    if not pbid:
        await message.channel.send("Please provide a valid PB-ID like `pb-xxxx`.")
        return
    try:
        pdata.unban_player(pbid)
        await message.channel.send(f"✅ Unbanned `{pbid}`")
    except Exception as e:
        await message.channel.send(f"❌ Failed to unban `{pbid}`: `{e}`")


async def handle_unmute_pbid_command(message, arguments):
    if not arguments:
        await message.channel.send("Usage: `t?unmute pb-...`")
        return
    pbid = _resolve_pbid_from_arg(arguments[0].strip())
    if not pbid:
        await message.channel.send("Please provide a valid PB-ID like `pb-xxxx`.")
        return
    try:
        pdata.unmute(pbid)
        await message.channel.send(f"✅ Unmuted `{pbid}`")
    except Exception as e:
        await message.channel.send(f"❌ Failed to unmute `{pbid}`: `{e}`")

async def handle_role_command(message):
    """Handle role management commands with r? prefix in role channel(s)."""
    content = message.content[len(ROLE_COMMAND_PREFIX):].strip()
    parts = content.split()
    if not parts:
        return

    command = parts[0].lower()

    # Help for role commands is allowed for everyone in the channel
    if command in {"help", "h"}:
        await handle_role_help(message)
        return

    # Authorization check
    if message.author.id not in ALLOWED_USER_IDS:
        await message.channel.send(f"You are not authorized to use role commands. Your ID: {message.author.id}")
        return

    args = parts[1:]

    if command == 'addrole' and len(args) >= 2:
        role, pbid = args[0], args[1]
        await cmd_addrole(message, role, pbid)
        return
    if command in {"rmrole", "removerole", "delrole"} and len(args) >= 2:
        role, pbid = args[0], args[1]
        await cmd_rmrole(message, role, pbid)
        return
    if command in {"crole", "changerole"} and len(args) >= 2:
        role, pbid = args[0], args[1]
        await cmd_crole(message, role, pbid)
        return
    if command in {"list", "listroles", "show"}:
        await cmd_list_roles(message)
        return

    await message.channel.send("Unknown or invalid usage. Try `r?help`.")

async def handle_help_command(message):
    """Display help for all available commands"""
    # Create main help embed
    embed = discord.Embed(
        title="BombSquad Discord Bot Commands",
        description=f"All commands use the prefix `{DISCORD_COMMAND_PREFIX}`\n\n"
                   f"**User Management Commands:**",
        color=discord.Color.blue()
    )
    
    # User management commands (4 fields)
    user_commands = [
        ("`adduser <user_id>`", "Add a user to the allowed list"),
        ("`removeuser <user_id>`", "Remove a user from the allowed list"),
        ("`userlist`", "Show all allowed users"),
        ("`help`", "Show this help message")
    ]
    
    for cmd, desc in user_commands:
        embed.add_field(name=cmd, value=desc, inline=False)
    
    # Game management commands (grouped to reduce field count)
    game_commands_text = "`sm`, `slowmo`, `slow` - Toggle slow motion\n"
    game_commands_text += "`pause` - Pause the game\n"
    game_commands_text += "`end`, `next` - End current game\n"
    game_commands_text += "`restart`, `quit` - Restart server\n"
    game_commands_text += "`kick <player>` - Kick a player\n"
    game_commands_text += "`kickall` - Kick all players\n"
    game_commands_text += "`ban <player>` - Ban a player\n"
    game_commands_text += "`mute`, `mutechat` - Mute chat\n"
    game_commands_text += "`unmute`, `unmutechat` - Unmute chat\n"
    game_commands_text += "`say <message>` - Send server message\n"
    game_commands_text += "`recents` - Show recent players\n"
    game_commands_text += "`nv` - Toggle night vision\n"
    game_commands_text += "`acl` - Access control list"
    
    embed.add_field(
        name="Game Management Commands:",
        value=game_commands_text,
        inline=False
    )
    
    # Player effects commands (grouped to reduce field count)
    effect_commands_text = "`hug <player>` - Hug a player\n"
    effect_commands_text += "`hugall` - Hug all players\n"
    effect_commands_text += "`spaz`, `cc <player>` - Make player spaz\n"
    effect_commands_text += "`spazall`, `ccall` - Make all players spaz\n"
    effect_commands_text += "`box <player>` - Put player in box\n"
    effect_commands_text += "`boxall` - Put all players in box\n"
    effect_commands_text += "`icy <player>` - Freeze player\n"
    effect_commands_text += "`customeffect <effect>` - Set custom effect\n"
    effect_commands_text += "`removeeffect` - Remove custom effect\n"
    effect_commands_text += "`customtag <tag>` - Set custom tag\n"
    effect_commands_text += "`pme <player>` - Get player stats\n"
    effect_commands_text += "`control`, `exchange` - Control player"
    
    embed.add_field(
        name="Player Effect Commands:",
        value=effect_commands_text,
        inline=False
    )
    
    # Additional info
    embed.add_field(
        name="Additional Information:",
        value=f"Commands only work in <#{DIRECT_CMD_CHANNEL_ID}>\n"
              f"You must be in the allowed users list\n"
              f"Your user ID: `{message.author.id}`\n"
              f"Total allowed users: `{len(ALLOWED_USER_IDS)}`",
        inline=False
    )
    
    embed.set_footer(
        text=f"Requested by {message.author.name}",
        icon_url=message.author.display_avatar.url
    )
    
    try:
        await message.channel.send(embed=embed)
    except discord.errors.HTTPException as e:
        # Fallback: send as regular message if embed fails
        help_text = f"""
**BombSquad Discord Bot Commands**

All commands use the prefix `{DISCORD_COMMAND_PREFIX}`

**User Management Commands:**
- `adduser <user_id>` - Add a user to the allowed list
- `removeuser <user_id>` - Remove a user from the allowed list  
- `userlist` - Show all allowed users
- `help` - Show this help message

**Game Management Commands:**
- `sm`, `slowmo`, `slow` - Toggle slow motion
- `pause` - Pause the game
- `end`, `next` - End current game
- `restart`, `quit` - Restart server
- `kick <player>` - Kick a player
- `kickall` - Kick all players
- `ban <player>` - Ban a player
- `mute`, `mutechat` - Mute chat
- `unmute`, `unmutechat` - Unmute chat
- `say <message>` - Send server message
- `recents` - Show recent players
- `nv` - Toggle night vision
- `acl` - Access control list

**Player Effect Commands:**
- `hug <player>` - Hug a player
- `hugall` - Hug all players
- `spaz`, `cc <player>` - Make player spaz
- `spazall`, `ccall` - Make all players spaz
- `box <player>` - Put player in box
- `boxall` - Put all players in box
- `icy <player>` - Freeze player
- `customeffect <effect>` - Set custom effect
- `removeeffect` - Remove custom effect
- `customtag <tag>` - Set custom tag
- `pme <player>` - Get player stats
- `control`, `exchange` - Control player

**Additional Information:**
- Commands only work in <#{DIRECT_CMD_CHANNEL_ID}>
- You must be in the allowed users list
- Your user ID: `{message.author.id}`
- Total allowed users: `{len(ALLOWED_USER_IDS)}`
"""
        # Split into chunks if too long
        if len(help_text) > 2000:
            chunks = [help_text[i:i+2000] for i in range(0, len(help_text), 2000)]
            for chunk in chunks:
                await message.channel.send(chunk)
                await asyncio.sleep(1)  # Avoid rate limiting
        else:
            await message.channel.send(help_text)

async def handle_add_user_command(message, arguments):
    """Handle adding users to the allowed list"""
    if not arguments:
        await message.channel.send("Usage: `t?adduser <discord_user_id>`")
        return
    
    try:
        user_id = int(arguments[0])
        global ALLOWED_USER_IDS
        
        if user_id in ALLOWED_USER_IDS:
            await message.channel.send(f"User ID `{user_id}` is already in the allowed list.")
            return
        
        ALLOWED_USER_IDS.append(user_id)
        save_allowed_users()  # Save to JSON file
        
        # Create a nice embed for the response
        embed = discord.Embed(
            title="User Added Successfully",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
        embed.add_field(name="Added by", value=message.author.mention, inline=True)
        embed.add_field(name="Total Users", value=f"`{len(ALLOWED_USER_IDS)}`", inline=True)
        embed.set_footer(text="User management system")
        
        await message.channel.send(embed=embed)
        
        # Log the action
        print(f"User {message.author.name} ({message.author.id}) added user {user_id} to allowed list")
        
    except ValueError:
        embed = discord.Embed(
            title="Invalid User ID",
            description="Please provide a valid numeric user ID.",
            color=discord.Color.red()
        )
        await message.channel.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="Error Adding User",
            description=f"Error: {str(e)}",
            color=discord.Color.red()
        )
        await message.channel.send(embed=embed)

async def handle_remove_user_command(message, arguments):
    """Handle removing users from the allowed list"""
    if not arguments:
        await message.channel.send("Usage: `t?removeuser <discord_user_id>`")
        return
    
    try:
        user_id = int(arguments[0])
        global ALLOWED_USER_IDS
        
        if user_id not in ALLOWED_USER_IDS:
            embed = discord.Embed(
                title="User Not Found",
                description=f"User ID `{user_id}` is not in the allowed list.",
                color=discord.Color.orange()
            )
            await message.channel.send(embed=embed)
            return
        
        # Prevent removing yourself
        if user_id == message.author.id:
            embed = discord.Embed(
                title="Cannot Remove Yourself",
                description="You cannot remove your own access. Ask another admin to do it.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
            return
        
        ALLOWED_USER_IDS.remove(user_id)
        save_allowed_users()  # Save to JSON file
        
        # Create a nice embed for the response
        embed = discord.Embed(
            title="User Removed Successfully",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
        embed.add_field(name="Removed by", value=message.author.mention, inline=True)
        embed.add_field(name="Remaining Users", value=f"`{len(ALLOWED_USER_IDS)}`", inline=True)
        embed.set_footer(text="User management system")
        
        await message.channel.send(embed=embed)
        
        # Log the action
        print(f"User {message.author.name} ({message.author.id}) removed user {user_id} from allowed list")
        
    except ValueError:
        embed = discord.Embed(
            title="Invalid User ID",
            description="Please provide a valid numeric user ID.",
            color=discord.Color.red()
        )
        await message.channel.send(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="Error Removing User",
            description=f"Error: {str(e)}",
            color=discord.Color.red()
        )
        await message.channel.send(embed=embed)

async def handle_userlist_command(message):
    """Handle displaying the list of allowed users"""
    global ALLOWED_USER_IDS
    
    if not ALLOWED_USER_IDS:
        embed = discord.Embed(
            title="Allowed Users List",
            description="No users are currently allowed to use commands.",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Use t?adduser <user_id> to add users")
        await message.channel.send(embed=embed)
        return
    
    # Create a beautiful embed for the user list
    embed = discord.Embed(
        title="Allowed Users List",
        description=f"Total **{len(ALLOWED_USER_IDS)}** users can use commands in this channel.",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )
    
    # Format user list with mentions and IDs
    user_list = []
    for i, user_id in enumerate(ALLOWED_USER_IDS, 1):
        try:
            # Try to get user object for better display
            user = await client.fetch_user(user_id)
            user_list.append(f"**{i}.** {user.mention} (`{user_id}`) - {user.name}")
        except:
            # If we can't fetch user details, just show the ID
            user_list.append(f"**{i}.** `{user_id}` - *User not found*")
    
    # Split user list into chunks if too long
    if len(user_list) > 0:
        # Discord field value limit is 1024 characters
        chunk_size = 10  # Show 10 users per field
        for i in range(0, len(user_list), chunk_size):
            chunk = user_list[i:i + chunk_size]
            field_name = f"Users {i+1}-{min(i+chunk_size, len(ALLOWED_USER_IDS))}"
            embed.add_field(
                name=field_name,
                value="\n".join(chunk),
                inline=False
            )
    
    # Add statistics
    embed.add_field(
        name="Statistics",
        value=f"Total allowed users: **{len(ALLOWED_USER_IDS)}**\n"
              f"Your access: **{'Granted' if message.author.id in ALLOWED_USER_IDS else 'Denied'}**\n"
              f"Your user ID: `{message.author.id}`",
        inline=False
    )
    
    embed.set_footer(
        text=f"Requested by {message.author.name} | Use t?adduser/removeuser to manage",
        icon_url=message.author.display_avatar.url
    )
    
    await message.channel.send(embed=embed)

def execute_management_command(func_name, arguments, author_name, author_id):
    """Execute management commands in the BombSquad thread"""
    try:
        # Import management module
        from chathandle.chatcommands.commands.management import ExcelCommand
        
        # Create a mock clientid and accountid for Discord commands
        # Using negative values to distinguish from real game clients
        discord_client_id = -abs(hash(author_name)) % 100000
        discord_account_id = f"discord_{author_name}_{author_id}"
        
        # Execute the command
        ExcelCommand(func_name, arguments, discord_client_id, discord_account_id)
        
        # Log the command execution
        print(f"Discord command executed: {func_name} {arguments} by {author_name} (ID: {author_id})")
        
    except Exception as e:
        print(f"Error executing Discord command {func_name}: {e}")

@client.event
async def on_ready():
    print(f"Discord bot logged in as: {client.user.name}, {client.user.id}")
    print(f"Allowed users: {ALLOWED_USER_IDS}")
    print(f"Command channel ID: {DIRECT_CMD_CHANNEL_ID}")
    client.add_view(ComplaintView())
    await verify_channel()

async def verify_channel():
    global livestatsmsgs
    # Verify live stats channel
    stats_channel = client.get_channel(LIVE_STATS_CHANNEL_ID)
    if not stats_channel:
        print(f"Error: Could not find live stats channel with ID {LIVE_STATS_CHANNEL_ID}")
    else:
        await setup_live_stats(stats_channel)
        # Setup game-info channel in the same guild/category
        try:
            await setup_game_info(stats_channel)
        except Exception as e:
            print(f"Error setting up game-info channel: {e}")
    
    # Verify command channel
    cmd_channel = client.get_channel(DIRECT_CMD_CHANNEL_ID)
    if not cmd_channel:
        print(f"Error: Could not find command channel with ID {DIRECT_CMD_CHANNEL_ID}")
    else:
        print(f"Command channel ready: #{cmd_channel.name}")
    
    # Verify role channels
    try:
        for cid in ROLE_CMD_CHANNEL_IDS:
            ch = client.get_channel(cid)
            if ch:
                print(f"Role channel ready: #{ch.name} ({cid})")
            else:
                print(f"Warning: Role channel not found for ID {cid}")
    except Exception as e:
        print(f"Role channel verification error: {e}")

async def setup_live_stats(stats_channel):
    """Setup live stats messages in the stats channel"""
    global livestatsmsgs
    global _refresh_stats_task, _send_logs_task, _send_error_logs_task
    
    # Get messages (updated method)
    botmsg_count = 0
    livestatsmsgs.clear()
    
    async for msg in stats_channel.history(limit=5):
        if msg.author.id == client.user.id:
            botmsg_count += 1
            livestatsmsgs.append(msg)

    livestatsmsgs.reverse()
    while botmsg_count < 2:
        try:
            # Create initial embeds
            stats_embed = discord.Embed(title="", description="### Fetching server data...")
            chat_embed = discord.Embed(title="Live Chat", description="Fetching chat messages...")
            
            stats_msg = await stats_channel.send(embed=stats_embed)
            chat_msg = await stats_channel.send(embed=chat_embed)
            
            livestatsmsgs.extend([stats_msg, chat_msg])
            botmsg_count += 2
        except discord.Forbidden:
            print("Error: Bot doesn't have permission to send messages in the channel")
            break
        except Exception as e:
            print(f"Error sending message: {e}")
            break
    
    if len(livestatsmsgs) >= 2:
        if _refresh_stats_task is None or _refresh_stats_task.done():
            _refresh_stats_task = asyncio.create_task(refresh_stats())
        if _send_logs_task is None or _send_logs_task.done():
            _send_logs_task = asyncio.create_task(send_logs())
        if _send_error_logs_task is None or _send_error_logs_task.done():
            _send_error_logs_task = asyncio.create_task(send_error_logs())
        # Hook into BombSquad's log system
        _install_bs_log_callback()
        # Start leaderboard loop
        if _leaderboard is not None:
            global _leaderboard_task
            if _leaderboard._leaderboard_task is None or _leaderboard._leaderboard_task.done():
                _leaderboard._leaderboard_task = asyncio.create_task(
                    _leaderboard.run_leaderboard_loop(client, discord)
                )

async def setup_game_info(stats_channel: discord.TextChannel):
    """Get game-info channel by ID and start updater task."""
    global _refresh_game_info_task
    target = client.get_channel(GAME_INFO_CHANNEL_ID)
    if target is None:
        print(f"Error: Could not find game-info channel with ID {GAME_INFO_CHANNEL_ID}")
        return

    # Seed message cache with recent bot messages (optional)
    global game_info_msgs
    game_info_msgs = {}
    async for msg in target.history(limit=20):
        if msg.author.id == client.user.id and isinstance(msg.embeds, list) and msg.embeds:
            # Try to detect label from embed title
            title = (msg.embeds[0].title or '').lower()
            if title.startswith('team:'):
                # Extract after 'team: '
                label = 'team_' + title[6:].strip()
                game_info_msgs[label] = msg
            elif 'lobby' in title:
                game_info_msgs['lobby'] = msg

    # Start background updater
    if _refresh_game_info_task is None or _refresh_game_info_task.done():
        _refresh_game_info_task = asyncio.create_task(refresh_game_info(target))

def _discord_color_from_rgb(rgb):
    try:
        r, g, b = rgb[0], rgb[1], rgb[2]
        # Handle floats 0..1 or ints 0..255
        if r <= 1 and g <= 1 and b <= 1:
            r, g, b = int(r * 255), int(g * 255), int(b * 255)
        else:
            r, g, b = int(r), int(g), int(b)
        r = max(0, min(255, r)); g = max(0, min(255, g)); b = max(0, min(255, b))
        return discord.Color.from_rgb(r, g, b)
    except Exception:
        return discord.Color.blurple()

def _build_team_embed(team_name: str, team_color, team_score, players: list) -> discord.Embed:
    emb = discord.Embed(
        title=f"Team: {team_name}",
        color=_discord_color_from_rgb(team_color)
    )
    emb.add_field(name="Score", value=str(team_score), inline=True)
    if players:
        lines = []
        for p in players:
            in_game = '' if p.get('inGame') else ''
            pname = p.get('name') or 'Unknown'
            account_name = p.get('device_id') or 'N/A'
            client_id = p.get('client_id') or 'N/A'
            lines.append(f"{in_game} {pname} | {account_name} | {client_id}")
        value = "\n".join(lines)
    else:
        value = "No players"
    emb.add_field(name="Players", value=value, inline=False)
    emb.set_footer(text="Auto-updating")
    return emb

def _build_lobby_embed(lobby_list: list) -> discord.Embed:
    emb = discord.Embed(title="Lobby", color=discord.Color.dark_grey())
    if lobby_list:
        lines = []
        for item in lobby_list:
            # Use device_id as the display name if name is <in-lobby>
            name = item.get('name') or '<in-lobby>'
            if name == '<in-lobby>':
                name = item.get('device_id') or '<in-lobby>'
            account_name = item.get('device_id') or 'N/A'
            client_id = item.get('client_id') or 'N/A'
            lines.append(f"• {name} | {account_name} | {client_id}")
        emb.add_field(name="Players", value="\n".join(lines), inline=False)
    else:
        emb.add_field(name="Players", value="Nobody in lobby", inline=False)
    emb.set_footer(text="Auto-updating")
    return emb

async def refresh_game_info(channel: discord.TextChannel):
    await client.wait_until_ready()
    global game_info_msgs
    while not client.is_closed():
        try:
            # Read precomputed stats from bombsquad_service
            s = {}
            try:
                s = bss.get_stats()
            except Exception:
                s = {}
            team_info = (s.get('teamInfo') or {}) if isinstance(s, dict) else {}
            roster = (s.get('roster') or {}) if isinstance(s, dict) else {}

            # Build a set of account_ids currently in teams and enrich team players with client_id and device_id from roster
            team_account_ids = set()
            for t in team_info.values():
                for p in t.get('players', []):
                    aid = p.get('account_id')
                    if aid:
                        team_account_ids.add(aid)
                        # Enrich with client_id and device_id from roster if not already present
                        if aid in roster:
                            if 'client_id' not in p or p.get('client_id') is None:
                                p['client_id'] = roster[aid].get('client_id')
                            if 'device_id' not in p or p.get('device_id') is None:
                                p['device_id'] = roster[aid].get('device_id')

            # Lobby: from roster entries not present in any team or explicitly named <in-lobby>
            lobby_entries = []
            for aid, pdata_ in roster.items():
                if pdata_.get('name') == '<in-lobby>' or aid not in team_account_ids:
                    lobby_entries.append({
                        'name': pdata_.get('name') or '<in-lobby>',
                        'account_id': aid,
                        'client_id': pdata_.get('client_id'),
                        'device_id': pdata_.get('device_id')
                    })

            # Ensure and update one message per team, plus one for lobby
            active_labels = set()
            # Stable ordering by team id
            for tid in sorted(list(team_info.keys()), key=lambda x: int(x) if str(x).isdigit() else str(x)):
                t = team_info.get(tid) or {}
                emb = _build_team_embed(
                    t.get('name') or f"Team {tid}",
                    t.get('color') or [0.3, 0.3, 0.9],
                    t.get('score') if t.get('score') is not None else 0,
                    t.get('players') or []
                )
                label = f"team_{tid}"
                active_labels.add(label)
                msg = game_info_msgs.get(label)
                if msg is None:
                    try:
                        msg = await channel.send(embed=emb)
                        game_info_msgs[label] = msg
                    except Exception as e:
                        print(f"Failed to send team embed: {e}")
                else:
                    try:
                        await msg.edit(embed=emb)
                        await asyncio.sleep(3)  # Gap between edits to avoid rate limit
                    except discord.NotFound:
                        try:
                            msg = await channel.send(embed=emb)
                            game_info_msgs[label] = msg
                        except Exception as e:
                            print(f"Failed to resend team embed: {e}")
                    except Exception as e:
                        print(f"Failed to edit team embed: {e}")

            # Lobby embed
            lobby_emb = _build_lobby_embed(lobby_entries)
            active_labels.add('lobby')
            lmsg = game_info_msgs.get('lobby')
            if lmsg is None:
                try:
                    lmsg = await channel.send(embed=lobby_emb)
                    game_info_msgs['lobby'] = lmsg
                except Exception as e:
                    print(f"Failed to send lobby embed: {e}")
            else:
                try:
                    await asyncio.sleep(1)  # Gap before lobby edit
                    await lmsg.edit(embed=lobby_emb)
                except discord.NotFound:
                    try:
                        lmsg = await channel.send(embed=lobby_emb)
                        game_info_msgs['lobby'] = lmsg
                    except Exception as e:
                        print(f"Failed to resend lobby embed: {e}")
                except Exception as e:
                    print(f"Failed to edit lobby embed: {e}")

            # Clean up messages for teams that no longer exist
            stale = [k for k in list(game_info_msgs.keys()) if k not in active_labels]
            for k in stale:
                try:
                    m = game_info_msgs.pop(k)
                    await m.delete()
                except Exception:
                    pass

        except Exception as e:
            print(f"Error in refresh_game_info: {e}")
        await asyncio.sleep(10)  # Increased to 30s to avoid rate limits

async def refresh_stats():
    await client.wait_until_ready()
    
    # Initialize BsDataThread to start collecting stats
    bs_data_collector = BsDataCollector()
    
    while not client.is_closed():
        try:
            # Update stats from the collector
            stats_channel = client.get_channel(LIVE_STATS_CHANNEL_ID)

            # Handle stats embed (index 0)
            stats_embed = await get_stats_embed()
            if len(livestatsmsgs) >= 1:
                try:
                    await livestatsmsgs[0].edit(embed=stats_embed)
                except discord.errors.NotFound:
                    if stats_channel:
                        msg = await stats_channel.send(embed=stats_embed)
                        livestatsmsgs[0] = msg  # replace only index 0
            else:
                if stats_channel:
                    msg = await stats_channel.send(embed=stats_embed)
                    livestatsmsgs.insert(0, msg)

            await asyncio.sleep(5)  # Stagger chat embed update to avoid rate limit

            # Handle chat embed (index 1)
            chat_embed = await get_chat_embed()
            if chat_embed.description != 'disabled':
                if len(livestatsmsgs) >= 2:
                    try:
                        await livestatsmsgs[1].edit(embed=chat_embed)
                    except discord.errors.NotFound:
                        if stats_channel:
                            msg = await stats_channel.send(embed=chat_embed)
                            livestatsmsgs[1] = msg  # replace only index 1
                else:
                    if stats_channel:
                        msg = await stats_channel.send(embed=chat_embed)
                        livestatsmsgs.insert(1, msg)
                    
        except Exception as e:
            import traceback
            print(f"Error updating stats: {e}")
            traceback.print_exc()
        await asyncio.sleep(15)  # Increased from 3s to 15s to avoid Discord rate limits

async def send_logs():
    global logs, _send_logs_running
    if _send_logs_running:
        return
    _send_logs_running = True

    channel = client.get_channel(LOGS_CHANNEL_ID)
    if not channel:
        print(f"Error: Could not find channel with ID {LOGS_CHANNEL_ID}")
        _send_logs_running = False
        return
        
    try:
        await client.wait_until_ready()
        while not client.is_closed():
            batch = []
            with _logs_lock:
                if logs:
                    total_len = 0
                    take_count = 0
                    for msg_ in logs:
                        add_len = len(msg_) + 1
                        if total_len + add_len >= 2000:  # Discord message limit
                            break
                        batch.append(msg_)
                        total_len += add_len
                        take_count += 1
                    if take_count > 0:
                        del logs[:take_count]

            if batch:
                msg = "\n".join(batch)
                try:
                    await channel.send(msg)
                except Exception as e:
                    # Put unsent logs back at the front of the queue.
                    with _logs_lock:
                        logs = batch + logs
                    print(f"Error sending logs: {e}")

            await asyncio.sleep(10)
    finally:
        _send_logs_running = False

async def send_error_logs():
    """Send ERROR and WARNING messages to the error log channel."""
    global _error_logs, _send_error_logs_running
    if _send_error_logs_running:
        return
    _send_error_logs_running = True
    channel = client.get_channel(ERROR_LOG_CHANNEL_ID)
    if not channel:
        print(f"Error: Could not find error log channel with ID {ERROR_LOG_CHANNEL_ID}")
        _send_error_logs_running = False
        return
    try:
        await client.wait_until_ready()
        while not client.is_closed():
            batch = []
            with _error_logs_lock:
                if _error_logs:
                    total_len = 0
                    take_count = 0
                    for msg_ in _error_logs:
                        add_len = len(msg_) + 1
                        if total_len + add_len >= 1900:
                            break
                        batch.append(msg_)
                        total_len += add_len
                        take_count += 1
                    if take_count > 0:
                        del _error_logs[:take_count]
            if batch:
                msg = "\n".join(batch)
                try:
                    await channel.send(f"```\n{msg}\n```")
                except Exception as e:
                    with _error_logs_lock:
                        _error_logs = batch + _error_logs
                    print(f"Error sending error logs: {e}")
            await asyncio.sleep(10)
    finally:
        _send_error_logs_running = False


async def get_stats_embed():
    global stats
    stats = bss.get_stats() or {}
    stats.setdefault('roster', {})
    stats.setdefault('chats', [])
    stats.setdefault('playlist', {'current': 'Unknown', 'next': 'Unknown'})
    # Get system info
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    
    # Get server IP/Port using values set by servercontroller (fallback to API calls)
    try:
        ip = getattr(_babase, 'our_ip', None)
        if not ip:
            ip = "Unknown"
    except Exception:
        ip = "Unknown"

    try:
        port = getattr(_babase, 'our_port', None)
        if not port:
            try:
                port = bs.get_game_port()
            except Exception:
                port = "Unknown"
    except Exception:
        try:
            port = bs.get_game_port()
        except Exception:
            port = "Unknown"

    # Season reset days (match text_on_map behavior via _babase.season_ends_in_days)
    try:
        reset_val = getattr(_babase, 'season_ends_in_days', None)
        if reset_val is None:
            # Initialize from stats if needed
            try:
                if mystats.seasonStartDate is None:
                    _ = mystats.get_all_stats()
                days_passed = (datetime.datetime.now() - mystats.seasonStartDate).days
                reset_val = max(0, int(mystats.our_settings["statsResetAfterDays"]) - int(days_passed))
            except Exception:
                reset_val = 0
        reset = int(reset_val)
    except Exception:
        reset = 0
    
    # Server/party name (prefer actual party_name; fallback to settings HostName)
    try:
        server = babase.app.classic.server._config.party_name
        if not server:
            raise RuntimeError("empty party name")
    except Exception:
        try:
            import setting  # local settings module used elsewhere
            server = setting.get_settings_data().get("HostName", "Unknown")
        except Exception:
            server = "Unknown"
    
    # Build players message
    msg = ''
    try:
        if 'roster' in stats and stats['roster']:
            for player_id, player_data in stats['roster'].items():
                client_id = player_data.get('client_id', 'Unknown')
                name = player_data.get('name', 'Unknown')
                device_id = player_data.get('device_id', 'Unknown')
                msg += f"{client_id} [{player_id}] {name} {device_id}\n"
        else:
            msg = 'I am alone.. :('
    except Exception as e:
        print(f"Error generating player list: {e}")
        msg = 'Error loading players'
    
    # Get max players (you'll need to replace this with API 9 equivalent)
    try:
        max_players = bs.get_max_players() if hasattr(bs, 'get_max_players') else 8
    except:
        max_players = 8
    
    # Get ping (you'll need to implement this for API 9)
    pingss = "N/A"  # Replace with actual ping measurement
    
    # Create embed with API 7 design
    current_game = stats.get('playlist', {}).get('current', 'N/A')
    next_game = stats.get('playlist', {}).get('next', 'N/A')
    embed = discord.Embed(
        title="", 
        description= f"### {server} \n\n\n```ocaml\nCurrent Game: {current_game}\nNext Game: {next_game}```"
    )
    
    embed.set_author(
        name="LIVE SERVER STATUS | NODE #1", 
        icon_url="https://cdn.discordapp.com/emojis/878301194865508422.gif?size=512"
    )
    
    # Add fields with API 7 styling
    # Registered members count (profiles.json); fallback to current roster size
    try:
        members_count = 0
        try:
            from playersdata import pdata
            profiles = pdata.get_profiles()
            members_count = len(profiles) if isinstance(profiles, dict) else 0
        except Exception:
            members_count = len(stats.get('roster', {}))

        embed.add_field(
            name=" **Players Registered**",
            value=f"```py\nMEMBERS_COUNT = {members_count} ```",
            inline=False
        )
    except Exception:
        embed.add_field(
            name=" **Players Registered**",
            value=f"```py\nMEMBERS_COUNT = {len(stats.get('roster', {}))} ```",
            inline=False
        )
    
    embed.add_field(
        name=" **Server's Reset**", 
        value=f"```py\nSEASON ENDS IN {reset} DAYS```", 
        inline=True
    )
    
    embed.add_field(
        name=" **Server's Info**", 
        value=f"```py\nIP = {ip} \nPORT = {port} ```", 
        inline=False
    )
    
    embed.add_field(
        name=" **Players**", 
        value=f"```py\n{len(stats['roster'])}/{max_players} ```", 
        inline=True
    )
    
    # Public status from server config
    try:
        is_public = bool(babase.app.classic.server._config.party_is_public)
    except Exception:
        is_public = True
    embed.add_field(
        name=" **Public**", 
        value=f"```py\n{is_public} ```",
        inline=True
    )
    
    embed.add_field(
        name=" **Ping**", 
        value=f"```yaml\n{pingss}```", 
        inline=True
    )
    
    embed.add_field(
        name="**PLAYERS IN SERVER:**", 
        value=f"```\n{msg}```", 
        inline=False
    )
    
    embed.add_field(
        name="RAM", 
        value=f"```\n{ram}%```", 
        inline=True
    )
    
    embed.add_field(
        name="CPU", 
        value=f"```\n{cpu}%```", 
        inline=True
    )
    
    # Top 5 players (you'll need to implement this for API 9)
    top5_names = ["Player1", "Player2", "Player3", "Player4", "Player5"]
    top5 = mystats.top5Name + ["N/A"] * 5  # Replace with actual top players
    embed.add_field(name="TOP 5 PLAYERS", value=f"1.{top5[0]}\n2.{top5[1]}\n3.{top5[2]}\n4.{top5[3]}\n5.{top5[4]}", inline=False)    
    embed.set_footer(
        text="Auto updates every 10 seconds!", 
        icon_url='https://cdn.discordapp.com/emojis/842886491533213717.gif?size=96&quality=lossless'
    )
    
    return embed

async def get_chat_embed():
    embed = discord.Embed(title="Live Chat - Last 40 Messages")
    
    try:
        if 'chats' in stats and stats['chats']:
            # Limit the number of displayed messages to MAX_CHAT_MESSAGES
            chat_messages = stats['chats'][-MAX_CHAT_MESSAGES:]
            
            # Build fields respecting Discord 1024-char limit per field
            lines = [f"{i:02d}. {m}" for i, m in enumerate(chat_messages, start=1)]
            fields = []
            cur = ""
            for ln in lines:
                # +1 for newline
                if len(cur) + len(ln) + 1 > 1000:  # keep margin
                    fields.append(cur)
                    cur = ln + "\n"
                else:
                    cur += ln + "\n"
            if cur:
                fields.append(cur)

            if fields:
                for idx, block in enumerate(fields, start=1):
                    name = f"Recent Messages ({len(chat_messages)} total) [{idx}/{len(fields)}]"
                    embed.add_field(name=name, value=block or "\u200b", inline=False)
            else:
                embed.add_field(name="Empty", value="No chat messages available", inline=False)
                
    except Exception as e:
        print(f"Error while fetching chat messages: {e}")
        embed.add_field(name="Error", value="Could not load chat messages", inline=False)

    if not embed.fields:
        embed.add_field(name="Empty", value="No chat messages available", inline=False)

    if not liveChat:
        embed = discord.Embed(description='disabled')

    return embed

# ===== Role management helpers =====
from playersdata import pdata as _pdata

def _profile_name_for(pbid: str) -> str:
    try:
        profs = _pdata.get_profiles()
        if pbid in profs:
            name = profs[pbid].get("name") or profs[pbid].get("display_string")
            if isinstance(name, list):
                return name[0]
            return str(name)
    except Exception:
        pass
    return "Unknown"

async def cmd_addrole(message, role: str, pbid: str):
    try:
        _pdata.create_role(role)
        _pdata.add_player_role(role, pbid)
        name = _profile_name_for(pbid)
        embed = discord.Embed(title="Role Added", color=discord.Color.green())
        embed.add_field(name="Player", value=f"{name}", inline=True)
        embed.add_field(name="PBID", value=f"{pbid}", inline=True)
        embed.add_field(name="Role", value=f"{role}", inline=True)
        await message.channel.send(embed=embed)
    except Exception as e:
        await message.channel.send(f"Failed to add role: {e}")

async def cmd_rmrole(message, role: str, pbid: str):
    try:
        status = _pdata.remove_player_role(role, pbid)
        name = _profile_name_for(pbid)
        embed = discord.Embed(title="Role Removed", color=discord.Color.orange())
        embed.add_field(name="Player", value=f"{name}", inline=True)
        embed.add_field(name="PBID", value=f"{pbid}", inline=True)
        embed.add_field(name="Role", value=f"{role}", inline=True)
        embed.set_footer(text=status)
        await message.channel.send(embed=embed)
    except Exception as e:
        await message.channel.send(f"Failed to remove role: {e}")

async def cmd_crole(message, new_role: str, pbid: str):
    try:
        # Remove from all roles, then add to new_role
        roles = _pdata.get_roles()
        for rname, rdata in roles.items():
            if pbid in rdata.get("ids", []):
                try:
                    _pdata.remove_player_role(rname, pbid)
                except Exception:
                    pass
        _pdata.create_role(new_role)
        _pdata.add_player_role(new_role, pbid)
        name = _profile_name_for(pbid)
        embed = discord.Embed(title="Role Changed", color=discord.Color.blurple())
        embed.add_field(name="Player", value=f"{name}", inline=True)
        embed.add_field(name="PBID", value=f"{pbid}", inline=True)
        embed.add_field(name="New Role", value=f"{new_role}", inline=True)
        await message.channel.send(embed=embed)
    except Exception as e:
        await message.channel.send(f"Failed to change role: {e}")

async def cmd_list_roles(message):
    try:
        roles = _pdata.get_roles()
        profs = _pdata.get_profiles()
        # Build a flat list of (name, pbid, role)
        entries = []
        for rname, rdata in roles.items():
            for pbid in rdata.get("ids", []):
                name = profs.get(pbid, {}).get("name") or profs.get(pbid, {}).get("display_string")
                if isinstance(name, list):
                    name = name[0]
                name = name or "Unknown"
                entries.append((str(name), str(pbid), rname))

        if not entries:
            await message.channel.send("No players have roles yet.")
            return

        # Sort by role then name
        entries.sort(key=lambda x: (x[2].lower(), x[0].lower()))

        # Create paginated embeds if needed
        page = []
        char_count = 0
        pages = []
        for name, pbid, role in entries:
            line = f"Name: {name} | PBID: {pbid} | Role: {role}\n"
            if char_count + len(line) > 1000 and page:
                pages.append("".join(page))
                page, char_count = [], 0
            page.append(line)
            char_count += len(line)
        if page:
            pages.append("".join(page))

        for i, block in enumerate(pages, start=1):
            embed = discord.Embed(title="Players With Roles", color=discord.Color.blue())
            embed.add_field(name=f"Page {i}/{len(pages)}", value=block or "\u200b", inline=False)
            await message.channel.send(embed=embed)
            await asyncio.sleep(0.5)
    except Exception as e:
        await message.channel.send(f"Failed to list roles: {e}")

async def handle_role_help(message):
    embed = discord.Embed(title="Role Commands", color=discord.Color.blue())
    embed.add_field(name="Prefix", value=f"{ROLE_COMMAND_PREFIX}", inline=True)
    embed.add_field(name="Allowed Users Only", value="Yes", inline=True)
    embed.add_field(name="Commands", value=(
        "addrole <role> <pbid> - Add role to PBID\n"
        "rmrole <role> <pbid> - Remove role from PBID\n"
        "crole <role> <pbid> - Make this the only role for PBID\n"
        "list - Show players with roles"
    ), inline=False)
    embed.set_footer(text=f"Requested by {message.author.name}")
    await message.channel.send(embed=embed)

class BsDataCollector:
    """Collects BombSquad data safely from the logic thread."""
    
    def __init__(self):
        self.last_update = 0
        self.update_interval = 3  # seconds
        
    def update_discord_stats(self):
        """Called from Discord thread to trigger stats update."""
        current_time = time.time()
        if current_time - self.last_update >= self.update_interval:
            _babase.pushcall(self._collect_stats, from_other_thread=True)
            self.last_update = current_time
    
    def _collect_stats(self):
        """Actually collect stats - runs in BombSquad logic thread."""
        global stats
        liveplayers = {}
        nextMap = 'Unknown'
        currentMap = 'Unknown'
        
        try:
            # Check if we can safely access game roster
            if hasattr(bs, 'get_game_roster'):
                roster = bs.get_game_roster()
                for i in roster:
                    try:
                        liveplayers[i['account_id']] = {
                            'name': i['players'][0]['name_full'] if i.get('players') else "<in-lobby>",
                            'client_id': i['client_id'],
                            'device_id': i['display_string']
                        }
                    except (KeyError, IndexError):
                        liveplayers[i['account_id']] = {
                            'name': "<in-lobby>", 
                            'client_id': i['client_id'],
                            'device_id': i['display_string']
                        }
        except Exception as e:
            print(f"Error getting game roster: {e}")

        try:
            # Check if we can safely access session information
            session = bs.get_foreground_host_session()
            if session:
                try:
                    nextMap = session.get_next_game_description().evaluate()
                except:
                    nextMap = 'Unknown'
                
                try:
                    current_game_spec = getattr(session, '_current_game_spec', None)
                    if current_game_spec:
                        gametype = current_game_spec.get('resolved_type')
                        if gametype:
                            currentMap = gametype.get_settings_display_string(current_game_spec).evaluate()
                except:
                    currentMap = 'Unknown'
        except Exception as e:
            print(f"Error getting session info: {e}")

        try:
            # Safely get chat messages with error handling
            chats = bs.get_chat_messages() if hasattr(bs, 'get_chat_messages') else []

            # Keep a rolling window of the last MAX_CHAT_MESSAGES messages
            # If new messages arrive beyond this size, drop from the front
            if len(chats) > MAX_CHAT_MESSAGES:
                chats = chats[-MAX_CHAT_MESSAGES:]

        except RuntimeError:
            # ClassicAppMode is inactive, use empty chat list
            chats = []
        except Exception as e:
            print(f"Error getting chat messages: {e}")
            chats = []

        # Update global stats
        stats['roster'] = liveplayers
        stats['chats'] = chats
        stats['playlist'] = {'current': currentMap, 'next': nextMap}

# Legacy compatibility
class BsDataThread:
    def __init__(self):
        self.collector = BsDataCollector()
