# Released under the MIT License. See LICENSE for details.
#
"""Laser Tracer mini-game - dodge laser walls to survive."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import weakref
import logging
import random
from typing import TYPE_CHECKING, override

import babase
import bascenev1 as bs

from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.onscreentimer import OnScreenTimer
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence, Optional


class Icon(bs.Actor):
    """Creates in in-game icon on screen."""

    def __init__(
        self,
        player: Player,
        position: tuple[float, float],
        scale: float,
        *,
        show_lives: bool = True,
        show_death: bool = True,
        name_scale: float = 1.0,
        name_maxwidth: float = 115.0,
        flatness: float = 1.0,
        shadow: float = 1.0,
    ):
        super().__init__()

        self._player = weakref.ref(player)  # Avoid ref loops.
        self._show_lives = show_lives
        self._show_death = show_death
        self._name_scale = name_scale
        self._outline_tex = bs.gettexture('characterIconMask')

        icon = player.get_icon()
        self.node = bs.newnode(
            'image',
            delegate=self,
            attrs={
                'texture': icon['texture'],
                'tint_texture': icon['tint_texture'],
                'tint_color': icon['tint_color'],
                'vr_depth': 400,
                'tint2_color': icon['tint2_color'],
                'mask_texture': self._outline_tex,
                'opacity': 1.0,
                'absolute_scale': True,
                'attach': 'bottomCenter',
            },
        )
        self._name_text = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': bs.Lstr(value=player.getname()),
                'color': bs.safecolor(player.team.color),
                'h_align': 'center',
                'v_align': 'center',
                'vr_depth': 410,
                'maxwidth': name_maxwidth,
                'shadow': shadow,
                'flatness': flatness,
                'h_attach': 'center',
                'v_attach': 'bottom',
            },
        )
        if self._show_lives:
            self._lives_text = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': 'x0',
                    'color': (1, 1, 0.5),
                    'h_align': 'left',
                    'vr_depth': 430,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'h_attach': 'center',
                    'v_attach': 'bottom',
                },
            )
        self.set_position_and_scale(position, scale)

    def set_position_and_scale(
        self, position: tuple[float, float], scale: float
    ) -> None:
        """(Re)position the icon."""
        assert self.node
        self.node.position = position
        self.node.scale = [70.0 * scale]
        self._name_text.position = (position[0], position[1] + scale * 52.0)
        self._name_text.scale = 1.0 * scale * self._name_scale
        if self._show_lives:
            self._lives_text.position = (
                position[0] + scale * 10.0,
                position[1] - scale * 43.0,
            )
            self._lives_text.scale = 1.0 * scale

    def update_for_lives(self) -> None:
        """Update for the target player's current lives."""
        player = self._player()
        if player:
            lives = player.lives
        else:
            lives = 0
        if self._show_lives:
            if lives > 0:
                self._lives_text.text = 'x' + str(lives - 1)
            else:
                self._lives_text.text = ''
        if lives == 0:
            self._name_text.opacity = 0.2
            assert self.node
            self.node.color = (0.7, 0.3, 0.3)
            self.node.opacity = 0.2

    def handle_player_spawned(self) -> None:
        """Our player spawned; hooray!"""
        if not self.node:
            return
        self.node.opacity = 1.0
        self.update_for_lives()

    def handle_player_died(self) -> None:
        """Well poo; our player died."""
        if not self.node:
            return
        if self._show_death:
            bs.animate(
                self.node,
                'opacity',
                {
                    0.00: 1.0,
                    0.05: 0.0,
                    0.10: 1.0,
                    0.15: 0.0,
                    0.20: 1.0,
                    0.25: 0.0,
                    0.30: 1.0,
                    0.35: 0.0,
                    0.40: 1.0,
                    0.45: 0.0,
                    0.50: 1.0,
                    0.55: 0.2,
                },
            )
            player = self._player()
            lives = player.lives if player else 0
            if lives == 0:
                bs.timer(0.6, self.update_for_lives)

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            self.node.delete()
            return None
        return super().handlemessage(msg)


class Player(bs.Player['Team']):
    """Our player type for this game."""

    def __init__(self) -> None:
        self.lives = 0
        self.icons: list[Icon] = []
        self.death_time: Optional[float] = None


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.survival_seconds: int | None = None
        self.spawn_order: list[Player] = []


# ba_meta export bascenev1.GameActivity
class LaserTracerGame(bs.TeamGameActivity[Player, Team]):
    """Game type where last player(s) left alive win while dodging lasers."""

    name = 'Laser Tracer'
    description = 'Dodge the laser walls to survive.'
    scoreconfig = bs.ScoreConfig(
        label='Survived',
        scoretype=bs.ScoreType.MILLISECONDS,
        version='B',
    )
    # Show messages when players die since it's meaningful here.
    announce_player_deaths = True

    allow_mid_activity_joins = False

    @override
    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[bs.Setting]:
        settings = [
            bs.IntSetting(
                'Lives Per Player',
                default=1,
                min_value=1,
                max_value=10,
                increment=1,
            ),
            bs.IntChoiceSetting(
                'Time Limit',
                choices=[
                    ('None', 0),
                    ('1 Minute', 60),
                    ('2 Minutes', 120),
                    ('5 Minutes', 300),
                    ('10 Minutes', 600),
                    ('20 Minutes', 1200),
                ],
                default=0,
            ),
            bs.FloatChoiceSetting(
                'Respawn Times',
                choices=[
                    ('Shorter', 0.25),
                    ('Short', 0.5),
                    ('Normal', 1.0),
                    ('Long', 2.0),
                    ('Longer', 4.0),
                ],
                default=1.0,
            ),
            bs.BoolSetting('Epic Mode', default=False),
        ]
        if issubclass(sessiontype, bs.DualTeamSession):
            settings.append(bs.BoolSetting('Solo Mode', default=False))
            settings.append(
                bs.BoolSetting('Balance Total Lives', default=False)
            )
        return settings

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return (
            issubclass(sessiontype, bs.DualTeamSession)
            or issubclass(sessiontype, bs.FreeForAllSession)
            or issubclass(sessiontype, babase.CoopSession)
        )

    # We're currently hard-coded for one map.
    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Courtyard']

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._start_time: float | None = None
        self._vs_text: bs.Actor | None = None
        self._round_end_timer: bs.Timer | None = None
        self._epic_mode = bool(settings.get('Epic Mode', False))
        self._lives_per_player = int(settings.get('Lives Per Player', 1))
        self._time_limit = float(settings.get('Time Limit', 0))
        self._balance_total_lives = bool(
            settings.get('Balance Total Lives', False)
        )
        self._solo_mode = bool(settings.get('Solo Mode', False))
        self._last_player_death_time: Optional[float] = None
        self._timer: OnScreenTimer | None = None

        # Base class overrides:
        self.slow_motion = self._epic_mode
        self.default_music = (
            bs.MusicType.EPIC if self._epic_mode else bs.MusicType.SURVIVAL
        )

        # Set up laser material - kills players on contact
        shared = SharedObjects.get()
        self.laser_material = bs.Material()
        self.laser_material.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('message', 'their_node', 'at_connect', bs.DieMessage()),
            ),
        )

    @override
    def get_instance_description(self) -> str | Sequence:
        return (
            'Dodge lasers, last team standing wins.'
            if isinstance(self.session, bs.DualTeamSession)
            else 'Dodge the lasers and survive!'
        )

    @override
    def get_instance_description_short(self) -> str | Sequence:
        return 'dodge lasers, survive'

    @override
    def on_player_join(self, player: Player) -> None:
        player.lives = self._lives_per_player

        # In coop mode, handle joining like Memory Game does.
        if isinstance(self.session, bs.CoopSession):
            if self.has_begun():
                bs.broadcastmessage(
                    babase.Lstr(
                        resource='playerDelayedJoinText',
                        subs=[
                            ('${PLAYER}', player.getname(full=True))
                        ],
                    ),
                    color=(0, 1, 0),
                    transient=True,
                    clients=[
                        player.sessionplayer.inputdevice.client_id
                    ],
                )
                assert self._start_time is not None
                player.death_time = self._start_time
                return
            self.spawn_player(player)
            return

        if self._solo_mode:
            player.team.spawn_order.append(player)
            self._update_solo_mode()
        else:
            # Create our icon and spawn.
            player.icons = [Icon(player, position=(0, 50), scale=0.8)]
            if player.lives > 0:
                self.spawn_player(player)

        # Don't waste time doing this until begin.
        if self.has_begun():
            self._update_icons()

    @override
    def on_begin(self) -> None:
        super().on_begin()
        self._start_time = bs.time()
        self.setup_standard_time_limit(self._time_limit)

        # Start the on-screen survival stopwatch.
        self._timer = OnScreenTimer()
        self._timer.start()

        # No powerup drops in this mode - pure dodge game.
        if isinstance(self.session, bs.CoopSession):
            pass
        else:
            if self._solo_mode:
                self._vs_text = bs.NodeActor(
                    bs.newnode(
                        'text',
                        attrs={
                            'position': (0, 105),
                            'h_attach': 'center',
                            'h_align': 'center',
                            'maxwidth': 200,
                            'shadow': 0.5,
                            'vr_depth': 390,
                            'scale': 0.6,
                            'v_attach': 'bottom',
                            'color': (0.8, 0.8, 0.3, 1.0),
                            'text': bs.Lstr(resource='vsText'),
                        },
                    )
                )

            # If balance-team-lives is on, add lives to the smaller team
            # until total lives match.
            if (
                isinstance(self.session, bs.DualTeamSession)
                and self._balance_total_lives
                and self.teams[0].players
                and self.teams[1].players
            ):
                if self._get_total_team_lives(
                    self.teams[0]
                ) < self._get_total_team_lives(self.teams[1]):
                    lesser_team = self.teams[0]
                    greater_team = self.teams[1]
                else:
                    lesser_team = self.teams[1]
                    greater_team = self.teams[0]
                add_index = 0
                while self._get_total_team_lives(
                    lesser_team
                ) < self._get_total_team_lives(greater_team):
                    lesser_team.players[add_index].lives += 1
                    add_index = (add_index + 1) % len(lesser_team.players)

            self._update_icons()

        # Add walls and start lasers
        self.add_wall()
        self.create_laser()

        # Poll for game-over conditions.
        bs.timer(1.0, self._update, repeat=True)

    def _update_solo_mode(self) -> None:
        # For both teams, find the first player on the spawn order list with
        # lives remaining and spawn them if they're not alive.
        for team in self.teams:
            # Prune dead players from the spawn order.
            team.spawn_order = [p for p in team.spawn_order if p]
            for player in team.spawn_order:
                assert isinstance(player, Player)
                if player.lives > 0:
                    if not player.is_alive():
                        self.spawn_player(player)
                    break

    def _update_icons(self) -> None:
        # pylint: disable=too-many-branches

        # In coop, we don't use the icon system.
        if isinstance(self.session, bs.CoopSession):
            return

        # In free-for-all mode, everyone is just lined up along the bottom.
        if isinstance(self.session, bs.FreeForAllSession):
            count = len(self.teams)
            x_offs = 85
            xval = x_offs * (count - 1) * -0.5
            for team in self.teams:
                if len(team.players) == 1:
                    player = team.players[0]
                    for icon in player.icons:
                        icon.set_position_and_scale((xval, 30), 0.7)
                        icon.update_for_lives()
                    xval += x_offs

        # In teams mode we split up teams.
        else:
            if self._solo_mode:
                # First off, clear out all icons.
                for player in self.players:
                    player.icons = []

                # Now for each team, cycle through our available players
                # adding icons.
                for team in self.teams:
                    if team.id == 0:
                        xval = -60
                        x_offs = -78
                    else:
                        xval = 60
                        x_offs = 78
                    is_first = True
                    test_lives = 1
                    while True:
                        players_with_lives = [
                            p
                            for p in team.spawn_order
                            if p and p.lives >= test_lives
                        ]
                        if not players_with_lives:
                            break
                        for player in players_with_lives:
                            player.icons.append(
                                Icon(
                                    player,
                                    position=(
                                        xval,
                                        (40 if is_first else 25),
                                    ),
                                    scale=1.0 if is_first else 0.5,
                                    name_maxwidth=(
                                        130 if is_first else 75
                                    ),
                                    name_scale=(
                                        0.8 if is_first else 1.0
                                    ),
                                    flatness=0.0 if is_first else 1.0,
                                    shadow=0.5 if is_first else 1.0,
                                    show_death=is_first,
                                    show_lives=False,
                                )
                            )
                            xval += x_offs * (
                                0.8 if is_first else 0.56
                            )
                            is_first = False
                        test_lives += 1
            # Non-solo mode.
            else:
                for team in self.teams:
                    if team.id == 0:
                        xval = -50
                        x_offs = -85
                    else:
                        xval = 50
                        x_offs = 85
                    for player in team.players:
                        for icon in player.icons:
                            icon.set_position_and_scale((xval, 30), 0.7)
                            icon.update_for_lives()
                        xval += x_offs

    def _get_solo_spawn_point(self) -> bs.Vec3 | None:
        """In solo-mode, spawn farthest from existing live player."""
        living_player_pos = None
        for team in self.teams:
            for tplayer in team.players:
                if tplayer.is_alive():
                    assert tplayer.node
                    living_player_pos = tplayer.node.position
                    break
        if living_player_pos is not None:
            player_pos = bs.Vec3(living_player_pos)
            points: list[tuple[float, bs.Vec3]] = []
            for team in self.teams:
                start_pos = bs.Vec3(
                    self.map.get_start_position(team.id)
                )
                points.append(
                    ((start_pos - player_pos).length(), start_pos)
                )
            points.sort(key=lambda x: x[0])
            return points[-1][1]
        return None

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        """Spawn a player at normal map spawn positions."""
        if self._solo_mode:
            # In solo-mode, spawn farthest from existing live player.
            position = self._get_solo_spawn_point()
            if position is not None:
                actor = self.spawn_player_spaz(player, position)
            else:
                actor = self.spawn_player_spaz(player)
        else:
            # Use default map spawn positions.
            actor = self.spawn_player_spaz(player)

        # Reconnect controls: jump only, no punch/bomb/pickup.
        actor.connect_controls_to_player(
            enable_punch=False,
            enable_bomb=False,
            enable_pickup=False,
        )

        if not self._solo_mode:
            bs.timer(0.3, bs.Call(self._print_lives, player))

        # If we have any icons, update their state.
        for icon in player.icons:
            icon.handle_player_spawned()
        return actor

    def _print_lives(self, player: Player) -> None:
        from bascenev1lib.actor import popuptext

        # We get called in a timer so it's possible our player
        # has left/etc.
        if not player or not player.is_alive() or not player.node:
            return

        popuptext.PopupText(
            'x' + str(player.lives - 1),
            color=(1, 1, 0, 1),
            offset=(0, -0.8, 0),
            random_offset=0.0,
            scale=1.8,
            position=player.node.position,
        ).autoretain()

    @override
    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)
        player.icons = []

        # Remove us from spawn-order.
        if self._solo_mode:
            if player in player.team.spawn_order:
                player.team.spawn_order.remove(player)

        # Update icons in a moment since our team will be gone
        # from the list then.
        bs.timer(0, self._update_icons)

        # If the player to leave was the last in spawn order and had
        # their final turn currently in-progress, mark the survival
        # time for their team.
        if self._get_total_team_lives(player.team) == 0:
            assert self._start_time is not None
            player.team.survival_seconds = int(
                bs.time() - self._start_time
            )

    def _get_total_team_lives(self, team: Team) -> int:
        return sum(player.lives for player in team.players)

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            # Augment standard behavior.
            super().handlemessage(msg)
            player: Player = msg.getplayer(Player)

            player.lives -= 1
            if player.lives < 0:
                logging.exception(
                    "Got lives < 0 in Laser Tracer;"
                    " this shouldn't happen. solo: %s",
                    self._solo_mode,
                )
                player.lives = 0

            # If we have any icons, update their state.
            for icon in player.icons:
                icon.handle_player_died()

            # Play big death sound on our last death
            # or for every one in solo mode.
            if self._solo_mode or player.lives == 0:
                SpazFactory.get().single_player_death_sound.play()

            curtime = bs.time()

            # Record death time for scoring.
            player.death_time = curtime

            # Record this for final setting of the clock.
            self._last_player_death_time = curtime

            # Handle coop session: end game when everyone is dead.
            if isinstance(self.session, bs.CoopSession):
                # Check in the next cycle so teams still show up.
                babase.pushcall(self._check_end_game)
            else:
                # If we hit zero lives, we're dead (and our team
                # might be too).
                if player.lives == 0:
                    if self._get_total_team_lives(player.team) == 0:
                        assert self._start_time is not None
                        player.team.survival_seconds = int(
                            bs.time() - self._start_time
                        )
                else:
                    # Otherwise, in regular mode, respawn.
                    if not self._solo_mode:
                        self.respawn_player(player)

                # In solo, put ourself at the back of the spawn order.
                if self._solo_mode:
                    if player in player.team.spawn_order:
                        player.team.spawn_order.remove(player)
                        player.team.spawn_order.append(player)
        else:
            return super().handlemessage(msg)
        return None

    def _check_end_game(self) -> None:
        """Check if the game should end (used in coop mode)."""
        living_team_count = 0
        for team in self.teams:
            for player in team.players:
                if player.is_alive():
                    living_team_count += 1
                    break

        if isinstance(self.session, bs.CoopSession):
            # In coop, end when everyone is dead.
            if living_team_count <= 0:
                self.end_game()
        else:
            if living_team_count <= 1:
                self.end_game()

    def _update(self) -> None:
        if isinstance(self.session, bs.CoopSession):
            # In coop, just poll for all-dead condition.
            self._check_end_game()
            return

        if self._solo_mode:
            # For both teams, find the first player on the spawn order
            # list with lives remaining and spawn them if they're
            # not alive.
            for team in self.teams:
                # Prune dead players from the spawn order.
                team.spawn_order = [
                    p for p in team.spawn_order if p
                ]
                for player in team.spawn_order:
                    assert isinstance(player, Player)
                    if player.lives > 0:
                        if not player.is_alive():
                            self.spawn_player(player)
                            self._update_icons()
                        break

        # If we're down to 1 or fewer living teams, start a timer
        # to end the game.
        if len(self._get_living_teams()) < 2:
            self._round_end_timer = bs.Timer(0.5, self.end_game)

    def _get_living_teams(self) -> list[Team]:
        return [
            team
            for team in self.teams
            if len(team.players) > 0
            and any(player.lives > 0 for player in team.players)
        ]

    def add_wall(self) -> None:
        """Add invisible collision walls."""
        shared = SharedObjects.get()
        pwm = bs.Material()
        pwm.add_actions(
            actions=('modify_part_collision', 'friction', 0.0)
        )
        pwm.add_actions(
            conditions=('they_have_material', shared.player_material),
            actions=('modify_part_collision', 'collide', True),
        )
        cmesh = bs.getcollisionmesh('courtyardPlayerWall')
        self.player_wall = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': cmesh,
                'affect_bg_dynamics': False,
                'materials': [pwm],
            },
        )

    def create_laser(self) -> None:
        """Create repeating laser pattern."""
        bs.timer(6, bs.Call(self.LRlaser, True))
        bs.timer(7, bs.Call(self.UDlaser, True))
        bs.timer(30, self.create_laser)

    def LRlaser(self, left: bool) -> None:
        """Create a left-right moving laser."""
        ud_1_r = bs.newnode(
            'region',
            attrs={
                'position': (-5, 2.6, 0),
                'scale': (0.1, 0.6, 15),
                'type': 'box',
                'materials': [self.laser_material],
            },
        )
        x = -6
        for i in range(0, 30):
            x = x + 0.4
            node = bs.newnode(
                'shield',
                owner=ud_1_r,
                attrs={
                    'color': (1.5, 0.0, 0.0),
                    'radius': 0.28,
                    'hurt': 0,
                },
            )
            mnode = bs.newnode(
                'math',
                owner=ud_1_r,
                attrs={
                    'input1': (0, 0.0, x),
                    'operation': 'add',
                },
            )
            ud_1_r.connectattr('position', mnode, 'input2')
            mnode.connectattr('output', node, 'position')

        _rcombine = bs.newnode(
            'combine',
            owner=ud_1_r,
            attrs={'input1': 2.6, 'input2': -2, 'size': 3},
        )
        if left:
            x1 = -10
            x2 = 10
        else:
            x1 = 10
            x2 = -10
        bs.animate(_rcombine, 'input0', {0: x1, 20: x2})
        _rcombine.connectattr('output', ud_1_r, 'position')

        bs.timer(20, ud_1_r.delete)
        t = random.randrange(7, 13)
        bs.timer(
            t,
            bs.Call(
                self.LRlaser, bool(random.randrange(0, 2))
            ),
        )

    def UDlaser(self, up: bool) -> None:
        """Create an up-down moving laser."""
        ud_2_r = bs.newnode(
            'region',
            attrs={
                'position': (-3, 2.6, -6),
                'scale': (20, 0.6, 0.1),
                'type': 'box',
                'materials': [self.laser_material],
            },
        )
        x = -6
        for i in range(0, 40):
            x = x + 0.4
            node = bs.newnode(
                'shield',
                owner=ud_2_r,
                attrs={
                    'color': (1.5, 0.0, 0.0),
                    'radius': 0.28,
                    'hurt': 0,
                },
            )
            mnode = bs.newnode(
                'math',
                owner=ud_2_r,
                attrs={
                    'input1': (x, 0.0, 0),
                    'operation': 'add',
                },
            )
            ud_2_r.connectattr('position', mnode, 'input2')
            mnode.connectattr('output', node, 'position')

        _rcombine = bs.newnode(
            'combine',
            owner=ud_2_r,
            attrs={'input0': -2, 'input1': 2.6, 'size': 3},
        )
        if up:
            x1 = -9
            x2 = 6
        else:
            x1 = 6
            x2 = -9
        bs.animate(_rcombine, 'input2', {0: x1, 17: x2})
        _rcombine.connectattr('output', ud_2_r, 'position')

        bs.timer(17, ud_2_r.delete)
        t = random.randrange(6, 13)
        bs.timer(
            t,
            bs.Call(
                self.UDlaser, bool(random.randrange(0, 2))
            ),
        )

    @override
    def end_game(self) -> None:
        """End the game."""
        if self.has_ended():
            return

        cur_time = bs.time()
        assert self._timer is not None
        start_time = self._timer.getstarttime()

        self._vs_text = None  # Kill our 'vs' if its there.

        # Mark death-time as now for any still-living players
        # and award players points for how long they lasted.
        # (these per-player scores are only meaningful in team-games)
        for team in self.teams:
            for player in team.players:
                survived = False

                # Throw an extra fudge factor in so teams that
                # didn't die come out ahead of teams that did.
                if player.death_time is None:
                    survived = True
                    player.death_time = cur_time + 1

                # Award a per-player score depending on how many
                # seconds they lasted (per-player scores only affect
                # teams mode; everywhere else just looks at the
                # per-team score).
                score = int(player.death_time - self._timer.getstarttime())
                if survived:
                    score += 50  # A bit extra for survivors.
                self.stats.player_scored(
                    player, score, screenmessage=False
                )

        # Stop updating our time text, and set the final time to
        # match exactly when our last guy died.
        self._timer.stop(endtime=self._last_player_death_time)

        # Ok now calc game results: set a score for each team and
        # then tell the game to end.
        results = bs.GameResults()

        # Remember that 'free-for-all' mode is simply a special form
        # of 'teams' mode where each player gets their own team, so
        # we can just always deal in teams and have all cases covered.
        for team in self.teams:
            # Set the team score to the max time survived by any
            # player on that team.
            longest_life = 0.0
            for player in team.players:
                assert player.death_time is not None
                longest_life = max(
                    longest_life,
                    player.death_time - start_time,
                )

            # Submit the score value in milliseconds.
            results.set_team_score(team, int(1000.0 * longest_life))

        self.end(results=results)


# ba_meta export babase.Plugin
class LaserTracerCoopPlugin(babase.Plugin):
    """Plugin to register Laser Tracer as a coop practice level."""

    def __init__(self) -> None:
        babase.app.classic.add_coop_practice_level(
            bs.Level(
                name='Laser Tracer',
                displayname='${GAME}',
                gametype=LaserTracerGame,
                settings={},
                preview_texture_name='courtyardPreview',
            )
        )
