# ba_meta require api 9
"""
Leaderboard Feature
===================
Posts and auto-updates a Top 10 leaderboard embed in Discord.

SETUP:
  1. Set LEADERBOARD_CHANNEL_ID to your Discord channel ID
  2. Place this file in mods/features/
  3. The leaderboard will auto-update every UPDATE_INTERVAL minutes

CATEGORIES:
  🏆 Top Kills         — most kills overall
  💀 Best K/D Ratio    — kills / deaths ratio (min 10 games)
  🎮 Most Games        — most games played
  ⏱  Most Time Played  — total time on server (from pdata)
  💥 Most Damage       — total damage dealt
  📈 Top Score         — highest cumulative score
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import sys
import os


import setting
data = setting.get_settings_data()
db = data.get("discordbot", {})
LEADERBOARD_CHANNEL_ID = db.get("leaderboardChannelID",None)



# ── CONFIG ──────────────────────────────────────────────────
UPDATE_INTERVAL        = 5    # minutes between auto-updates
TOP_N                  = 10    # how many players per category
MIN_GAMES_FOR_KD       = 50    # minimum games to appear in K/D board
# ────────────────────────────────────────────────────────────

# Add mods path so we can import stats/pdata
_mods_path = os.path.join(os.path.dirname(__file__), '..')
if _mods_path not in sys.path:
    sys.path.insert(0, _mods_path)


def _get_stats() -> dict:
    try:
        from stats import mystats
        return mystats.get_all_stats() or {}
    except Exception as e:
        print(f'[leaderboard] Failed to load stats: {e}')
        return {}


def _get_time_played() -> dict[str, float]:
    """Returns {account_id: totaltimeplayer_seconds}"""
    try:
        from playersdata import pdata
        profiles = pdata.get_profiles() or {}
        return {
            aid: float(p.get('totaltimeplayer', 0))
            for aid, p in profiles.items()
        }
    except Exception as e:
        print(f'[leaderboard] Failed to load pdata: {e}')
        return {}


def _fmt_time(seconds: float) -> str:
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    if h > 0:
        return f'{h}h {m}m'
    return f'{m}m'


def _medal(rank: int) -> str:
    return ['🥇', '🥈', '🥉'][rank] if rank < 3 else f'`#{rank + 1}`'


def _name(entry: dict, aid: str) -> str:
    n = entry.get('name', aid)
    if not n or n in ('default name', 'default'):
        n = aid[:12]
    # Strip to max 18 chars
    return n[:18]


def build_leaderboard_embed(import_discord: object) -> object:
    discord = import_discord
    stats   = _get_stats()
    times   = _get_time_played()
    

    embed = discord.Embed(
        title='🏆  Server Leaderboard',
        color=0xFFAA00,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_footer(
        text=f'Auto Updates Every {UPDATE_INTERVAL} minute{"s" if UPDATE_INTERVAL > 1 else ""} | Last updated at',
        icon_url = "https://upload.wikimedia.org/wikipedia/commons/3/3a/Gray_circles_rotate.gif?_=20110906194014"
    )

    if not stats:
        embed.description = '_No stats yet — play some games!_'
        return embed

    players = list(stats.values())

    # ── Top Kills ──────────────────────────────────────────
    top_kills = sorted(players, key=lambda p: p.get('kills', 0), reverse=True)[:TOP_N]
    kills_lines = []
    for i, p in enumerate(top_kills):
        kills = p.get('kills', 0)
        if kills == 0:
            break
        kills_lines.append(f"{_medal(i)} **{_name(p, p.get('aid','?'))}** — `{kills:,}` kills")
    embed.add_field(
        name='💀  Top Kills',
        value='\n'.join(kills_lines) or '_No data_',
        inline=False,
    )

    # ── Best K/D Ratio ─────────────────────────────────────
    kd_players = [p for p in players if p.get('games', 0) >= MIN_GAMES_FOR_KD]
    top_kd = sorted(kd_players, key=lambda p: float(p.get('kd', 0)), reverse=True)[:TOP_N]
    kd_lines = []
    for i, p in enumerate(top_kd):
        kd   = float(p.get('kd', 0))
        k    = p.get('kills', 0)
        d    = p.get('deaths', 0)
        if kd == 0:
            break
        kd_lines.append(f"{_medal(i)} **{_name(p, p.get('aid','?'))}** — `{kd:.2f}` KD  ({k}K/{d}D)")
    embed.add_field(
        name=f'⚡  Best K/D  *(min {MIN_GAMES_FOR_KD} games)*',
        value='\n'.join(kd_lines) or '_No data_',
        inline=False,
    )

    # ── Most Games Played ──────────────────────────────────
    top_games = sorted(players, key=lambda p: p.get('games', 0), reverse=True)[:TOP_N]
    games_lines = []
    for i, p in enumerate(top_games):
        g = p.get('games', 0)
        if g == 0:
            break
        games_lines.append(f"{_medal(i)} **{_name(p, p.get('aid','?'))}** — `{g:,}` games")
    embed.add_field(
        name='🎮  Most Games Played',
        value='\n'.join(games_lines) or '_No data_',
        inline=False,
    )

    '''# ── Most Time Played ───────────────────────────────────
    time_entries = []
    for p in players:
        aid = p.get('aid', '')
        secs = times.get(aid, 0)
        if secs > 0:
            time_entries.append((secs, p, aid))
    top_time = sorted(time_entries, key=lambda x: x[0], reverse=True)[:TOP_N]
    time_lines = []
    for i, (secs, p, aid) in enumerate(top_time):
        time_lines.append(f"{_medal(i)} **{_name(p, aid)}** — `{_fmt_time(secs)}`")
    embed.add_field(
        name='⏱  Most Time Played',
        value='\n'.join(time_lines) or '_No data_',
        inline=False,
    )

    # ── Most Damage ────────────────────────────────────────
    top_dmg = sorted(players, key=lambda p: float(p.get('total_damage', 0)), reverse=True)[:TOP_N]
    dmg_lines = []
    for i, p in enumerate(top_dmg):
        dmg = float(p.get('total_damage', 0))
        if dmg == 0:
            break
        dmg_lines.append(f"{_medal(i)} **{_name(p, p.get('aid','?'))}** — `{dmg:,.0f}` dmg")
    embed.add_field(
        name='💥  Most Damage Dealt',
        value='\n'.join(dmg_lines) or '_No data_',
        inline=False,
    )'''

    # ── Top Score ──────────────────────────────────────────
    top_score = sorted(players, key=lambda p: p.get('scores', 0), reverse=True)[:TOP_N]
    score_lines = []
    for i, p in enumerate(top_score):
        sc = p.get('scores', 0)
        if sc == 0:
            break
        avg = p.get('avg_score', 0)
        score_lines.append(f"{_medal(i)} **{_name(p, p.get('aid','?'))}** — `{sc:,}` pts  *(avg {avg:.1f})*")
    embed.add_field(
        name='📈  Top Score',
        value='\n'.join(score_lines) or '_No data_',
        inline=False,
    )

    return embed


# ── Discord bot integration ────────────────────────────────
_leaderboard_msg_id: int | None = None
_leaderboard_task = None
_leaderboard_running = False


async def run_leaderboard_loop(client: object, discord: object) -> None:
    global _leaderboard_msg_id, _leaderboard_running
    if _leaderboard_running:
        return
    _leaderboard_running = True

    await client.wait_until_ready()
    channel = client.get_channel(LEADERBOARD_CHANNEL_ID)
    if not channel:
        print(f'[leaderboard] Channel {LEADERBOARD_CHANNEL_ID} not found.')
        _leaderboard_running = False
        return
    
    async for msg in channel.history(limit=5):
        if msg.author.id == client.user.id:
            if msg.embeds and msg.embeds[0].title == '🏆  Server Leaderboard':
                print(f"found old stat message id: {msg.id}")
                _leaderboard_msg_id = msg.id
                break



    while not client.is_closed():
        try:
            embed = build_leaderboard_embed(discord)

            if _leaderboard_msg_id:
                try:
                    msg = await channel.fetch_message(_leaderboard_msg_id)
                    await msg.edit(embed=embed)
                except discord.NotFound:
                    _leaderboard_msg_id = None

            if not _leaderboard_msg_id:
                msg = await channel.send(embed=embed)
                _leaderboard_msg_id = msg.id
                print(f'[leaderboard] Posted new leaderboard (msg {msg.id})')

        except Exception as e:
            print(f'[leaderboard] Error updating leaderboard: {e}')

        await asyncio.sleep(UPDATE_INTERVAL * 60)

    _leaderboard_running = False
