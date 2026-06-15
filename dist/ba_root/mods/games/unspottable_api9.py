# Released under the MIT License. See LICENSE for details.
#
"""Unspottable - A social deduction deathmatch where players hide among bots."""

# ba_meta require api 9
# (see https://ballistica.net/wiki/meta-tag-system)

from __future__ import annotations

import math
import random
import weakref
import logging
from typing import TYPE_CHECKING, override

import bascenev1 as bs
import babase

from bascenev1lib.actor.spaz import Spaz
from bascenev1lib.actor.playerspaz import PlayerSpaz
from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.spazbot import SpazBot, SpazBotSet, SpazBotDiedMessage
from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence


# ============================================================================
# CONSTANTS
# ============================================================================

# The uniform grey color all characters share.
UNIFORM_COLOR = (0.3, 0.3, 0.33)
UNIFORM_HIGHLIGHT = (1.0, 0.5, 0.3)
UNIFORM_CHARACTER = 'Agent Johnson'

# The character bots morph into under the spotlight.
REVEALED_CHARACTER = 'B-9000'

# Punch cooldown duration in seconds (the look-around animation).
PUNCH_COOLDOWN_DURATION = 1.4

# Spotlight settings.
SPOTLIGHT_RADIUS = 2.8

# Game mode IDs.
MODE_NORMAL = 0
MODE_SPOTLIGHT = 1
MODE_PARTY = 2

# Party mode: DDR arrow system constants.
WAVE_MOVE_COUNT = 6             # Number of dance moves per wave.
WAVE_COOLDOWN = 32.0            # Seconds of free wandering between waves.
ARROW_SPAWN_X = 300.0           # Right side of screen.
ARROW_HIT_X = -250.0            # Left side hit zone.
ARROW_LANE_Y = -80.0            # Y offset from top.
BOT_DANCE_DURATION = 0.55       # How long bots hold a move.
ARROW_SPACING = 100.0           # Pixels between each icon in the train.
ARROW_SCROLL_SPEED = 120.0      # Pixels per second (train scroll speed).

# Arrow directions, texture names, and tint colors.
DANCE_MOVES = [
    ('left',    'leftButton',  (0.2, 0.8, 1.0)),   # cyan
    ('right',   'rightButton', (0.2, 1.0, 0.3)),   # green
    ('forward', 'downButton',   (1.0, 1.0, 0.2)),   # yellow
    ('jump',    'buttonJump',  (1.0, 0.3, 1.0)),   # magenta
]

# Disco light positions (for Football Stadium).
DISCO_LIGHT_POSITIONS = [
    (-7.0, 2.5, -3.0),
    ( 7.0, 2.5, -3.0),
    (-7.0, 2.5,  3.0),
    ( 7.0, 2.5,  3.0),
    ( 0.0, 3.5,  0.0),
    (-3.0, 2.5,  0.0),
    ( 3.0, 2.5,  0.0),
]

# Disco color cycle.
DISCO_COLORS = [
    (1.0, 0.1, 0.1),   # red
    (1.0, 0.8, 0.0),   # yellow
    (0.1, 1.0, 0.2),   # green
    (0.0, 0.8, 1.0),   # cyan
    (0.3, 0.2, 1.0),   # blue
    (1.0, 0.2, 0.8),   # magenta
]


# ============================================================================
# CROWD BOT - Neutral NPC that wanders around
# ============================================================================

class CrowdBot(SpazBot):
    """A neutral bot that wanders aimlessly, mimicking player-like behavior.

    Does not attack, does not chase players - just walks, pauses,
    and occasionally runs to look natural in the crowd.

    In Party Mode, bots can do freestyle dancing during cooldown
    and synchronized dance moves during waves.
    """

    character = UNIFORM_CHARACTER
    color = UNIFORM_COLOR
    highlight = UNIFORM_HIGHLIGHT
    punchiness = 0.0
    throwiness = 0.0
    run = False
    static = False
    charge_dist_min = 9999.0
    charge_dist_max = 9999.0
    throw_dist_min = 9999.0
    throw_dist_max = 9999.0
    default_bomb_count = 0
    default_bomb_type = 'normal'

    # Freestyle dance styles available during cooldown.
    FREESTYLE_STYLES = ['wiggle', 'bounce', 'sway', 'crazy', 'groove']

    def __init__(self) -> None:
        super().__init__()
        self._wander_timer: bs.Timer | None = None
        self._move_dir: tuple[float, float] = (0.0, 0.0)
        self._wander_state: str = 'idle'
        self._state_timer: float = 0.0
        self._is_revealed: bool = False
        self._reveal_count: int = 0  # Reference count for overlapping spotlights.
        self._original_media: dict[str, Any] | None = None
        self._is_dancing: bool = False
        self._dance_mode_active: bool = False  # True during wave.

        # Freestyle dancing (Party Mode cooldown).
        self._freestyle_active: bool = False
        self._freestyle_on_break: bool = False
        self._freestyle_style: str = 'wiggle'
        self._freestyle_phase: float = 0.0
        self._freestyle_timer: bs.Timer | None = None
        self._freestyle_style_timer: float = 0.0

        # Grab map bounds for edge avoidance.
        self._map_bounds: tuple[float, ...] | None = None
        try:
            activity = bs.getactivity()
            bounds = activity.map.get_def_bound_box('map_bounds')
            if bounds is not None:
                self._map_bounds = bounds
        except Exception:
            pass

    def on_bot_spawned(self) -> None:
        """Called after the bot is placed in the world. Start wandering."""
        self._start_wandering()

    def _start_wandering(self) -> None:
        """Begin the idle wandering AI loop."""
        self._pick_new_wander_state()
        self._wander_timer = bs.Timer(
            0.25, bs.WeakCall(self._wander_update), repeat=True
        )

    def _pick_new_wander_state(self) -> None:
        """Choose a new wander behavior."""
        roll = random.random()
        if roll < 0.35:
            self._wander_state = 'walk'
            angle = random.uniform(0.0, math.tau)
            self._move_dir = (math.sin(angle), math.cos(angle))
            self._state_timer = random.uniform(1.0, 3.0)
        elif roll < 0.55:
            self._wander_state = 'run'
            angle = random.uniform(0.0, math.tau)
            self._move_dir = (math.sin(angle), math.cos(angle))
            self._state_timer = random.uniform(0.5, 1.5)
        elif roll < 0.75:
            self._wander_state = 'idle'
            self._move_dir = (0.0, 0.0)
            self._state_timer = random.uniform(1.0, 3.5)
        else:
            self._wander_state = 'walk'
            angle = random.uniform(0.0, math.tau)
            speed = random.uniform(0.2, 0.5)
            self._move_dir = (math.sin(angle) * speed,
                              math.cos(angle) * speed)
            self._state_timer = random.uniform(0.5, 1.2)

    def _wander_update(self) -> None:
        """Periodic wandering update."""
        if not self.node:
            return

        # If in dance mode (wave active) or doing a synced move, skip.
        if self._dance_mode_active or self._is_dancing:
            return

        # If freestyle is active and NOT on break, the freestyle
        # timer handles movement — skip wandering.
        if self._freestyle_active and not self._freestyle_on_break:
            return

        self._state_timer -= 0.25

        if self._state_timer <= 0:
            self._pick_new_wander_state()

        # --- Edge avoidance ---
        pos = self.node.position
        if self._map_bounds is not None:
            min_x, _min_y, min_z, max_x, _max_y, max_z = self._map_bounds
            margin_x = (max_x - min_x) * 0.20
            margin_z = (max_z - min_z) * 0.20
            safe_min_x = min_x + margin_x
            safe_max_x = max_x - margin_x
            safe_min_z = min_z + margin_z
            safe_max_z = max_z - margin_z

            center_x = (min_x + max_x) * 0.5
            center_z = (min_z + max_z) * 0.5

            near_edge = False
            if pos[0] < safe_min_x or pos[0] > safe_max_x:
                near_edge = True
            if pos[2] < safe_min_z or pos[2] > safe_max_z:
                near_edge = True

            if near_edge:
                dx = center_x - pos[0]
                dz = center_z - pos[2]
                dist = math.sqrt(dx * dx + dz * dz)
                if dist > 0.01:
                    self._move_dir = (dx / dist, dz / dist)
                    self._wander_state = 'walk'
                    self._state_timer = random.uniform(1.0, 2.0)

        # Fell off the map — die immediately.
        if pos[1] < -5.0:
            self.handlemessage(bs.DieMessage(immediate=True))
            return

        # Apply movement.
        if self._wander_state == 'run':
            self.node.move_left_right = self._move_dir[0]
            self.node.move_up_down = -self._move_dir[1]
            self.node.run = 1.0
        elif self._wander_state == 'walk':
            self.node.move_left_right = self._move_dir[0] * 0.5
            self.node.move_up_down = -self._move_dir[1] * 0.5
            self.node.run = 0.0
        else:
            self.node.move_left_right = 0.0
            self.node.move_up_down = 0.0
            self.node.run = 0.0

        # Occasionally do a random jump to look more player-like.
        if random.random() < 0.005 and self._wander_state == 'run':
            self.node.jump_pressed = True
            self.node.jump_pressed = False

    # --- Dance mode control (Party Mode) ---

    def set_dance_mode(self, active: bool) -> None:
        """Enable/disable dance mode. When active, bot stands still
        and only moves in response to execute_dance_move() calls.
        When deactivated, normal wandering resumes."""
        self._dance_mode_active = active
        if active and self.node and not self._dead:
            # Stop freestyle and all movement immediately.
            self.stop_freestyle()
            self.node.move_left_right = 0.0
            self.node.move_up_down = 0.0
            self.node.run = 0.0

    # --- Synchronized dance move execution (Party Mode) ---

    def execute_dance_move(self, direction: str) -> None:
        """Execute a synchronized dance move."""
        if not self.node or self._dead:
            return
        self._is_dancing = True
        if direction == 'left':
            self.node.move_left_right = -1.0
            self.node.move_up_down = 0.0
            self.node.run = 0.0
        elif direction == 'right':
            self.node.move_left_right = 1.0
            self.node.move_up_down = 0.0
            self.node.run = 0.0
        elif direction == 'forward':
            self.node.move_left_right = 0.0
            self.node.move_up_down = -1.0
            self.node.run = 0.0
        elif direction == 'jump':
            self.node.move_left_right = 0.0
            self.node.move_up_down = 0.0
            self.node.run = 0.0
            self.node.jump_pressed = True
            self.node.jump_pressed = False
        bs.timer(BOT_DANCE_DURATION,
                 bs.WeakCall(self._end_dance_move))

    def _end_dance_move(self) -> None:
        """Return to standing after a synced dance move."""
        self._is_dancing = False
        if self.node and not self._dead:
            self.node.move_left_right = 0.0
            self.node.move_up_down = 0.0

    # --- Freestyle dancing (Party Mode cooldown) ---

    def start_freestyle(self) -> None:
        """Start the freestyle dance loop during cooldown.
        Each bot randomly decides to dance or take a break,
        so only a portion of bots are dancing at any time."""
        if self._dead or not self.node:
            return
        self._freestyle_active = True
        self._freestyle_phase = random.uniform(0.0, math.tau)
        # Randomly decide: dance or break first.
        if random.random() < 0.1:
            self._pick_freestyle_style()
            self._freestyle_on_break = False
        else:
            self._freestyle_on_break = True
            self._freestyle_style_timer = random.uniform(3.0, 8.0)
        self._freestyle_timer = bs.Timer(
            0.1, bs.WeakCall(self._freestyle_update), repeat=True
        )

    def _pick_freestyle_style(self) -> None:
        """Pick a random freestyle dance style and set duration."""
        self._freestyle_style = random.choice(self.FREESTYLE_STYLES)
        self._freestyle_on_break = False
        # Dance for a short burst, then break.
        self._freestyle_style_timer = random.uniform(2.0, 5.0)

    def _start_break(self) -> None:
        """Take a break from dancing — stand still or wander."""
        self._freestyle_on_break = True
        self._freestyle_style_timer = random.uniform(4.0, 12.0)
        if self.node and not self._dead:
            self.node.move_left_right = 0.0
            self.node.move_up_down = 0.0
            self.node.run = 0.0

    def stop_freestyle(self) -> None:
        """Stop freestyle dancing entirely."""
        self._freestyle_active = False
        self._freestyle_timer = None
        self._freestyle_on_break = False
        if self.node and not self._dead:
            self.node.move_left_right = 0.0
            self.node.move_up_down = 0.0
            self.node.run = 0.0

    def _freestyle_update(self) -> None:
        """Fast-ticking update for freestyle dance animations."""
        if not self.node or self._dead or self._dance_mode_active:
            self._freestyle_active = False
            self._freestyle_timer = None
            return

        dt = 0.1
        self._freestyle_phase += dt
        self._freestyle_style_timer -= dt

        # Timer expired — switch between dancing and break.
        if self._freestyle_style_timer <= 0:
            if self._freestyle_on_break:
                self._pick_freestyle_style()
            else:
                self._start_break()
            return

        # On break — just idle (wander_update handles normal movement).
        if self._freestyle_on_break:
            return

        style = self._freestyle_style
        p = self._freestyle_phase

        if style == 'wiggle':
            wiggle = math.sin(p * 12.0)
            self.node.move_left_right = wiggle * 0.8
            self.node.move_up_down = math.sin(p * 6.0) * 0.15
            self.node.run = 0.0

        elif style == 'bounce':
            self.node.move_left_right = math.sin(p * 3.0) * 0.3
            self.node.move_up_down = math.cos(p * 2.0) * 0.2
            self.node.run = 0.0
            if int(p * 10) % 8 == 0 and random.random() < 0.5:
                self.node.jump_pressed = True
                self.node.jump_pressed = False

        elif style == 'sway':
            self.node.move_left_right = math.sin(p * 2.5) * 0.6
            self.node.move_up_down = math.sin(p * 1.2) * 0.1
            self.node.run = 0.0

        elif style == 'crazy':
            if int(p * 10) % 3 == 0:
                self.node.move_left_right = random.uniform(-1.0, 1.0)
                self.node.move_up_down = random.uniform(-1.0, 1.0)
            self.node.run = 1.0
            if random.random() < 0.15:
                self.node.jump_pressed = True
                self.node.jump_pressed = False

        elif style == 'groove':
            self.node.move_up_down = math.sin(p * 5.0) * 0.6
            self.node.move_left_right = math.sin(p * 2.5) * 0.4
            self.node.run = 0.3 + 0.3 * abs(math.sin(p * 4.0))
            if int(p * 10) % 12 == 0 and random.random() < 0.3:
                self.node.jump_pressed = True
                self.node.jump_pressed = False

    # --- Celebrate ---

    def celebrate(self, duration: float = 2.0) -> None:
        """Make this bot do a celebration animation."""
        if self.node and not self._dead:
            self.node.handlemessage('celebrate', int(duration * 1000))

    # --- Reveal / appearance ---

    def set_revealed(self, revealed: bool) -> None:
        """Adjust the spotlight reference count and update appearance.
        Multiple spotlights can overlap — the bot only reverts when
        ALL spotlights have moved away."""
        if not self.node:
            return

        if revealed:
            self._reveal_count += 1
            if self._reveal_count == 1 and not self._is_revealed:
                # First spotlight on this bot — morph to revealed.
                self._is_revealed = True
                self._apply_appearance(REVEALED_CHARACTER)
        else:
            self._reveal_count = max(0, self._reveal_count - 1)
            if self._reveal_count == 0 and self._is_revealed:
                # Last spotlight left — revert to normal.
                self._is_revealed = False
                self._apply_appearance(UNIFORM_CHARACTER)

    def _apply_appearance(self, character: str) -> None:
        """Apply a character's meshes and textures to this bot."""
        if not self.node:
            return
        factory = SpazFactory.get()
        media = factory.get_media(character)
        self.node.color_texture = media['color_texture']
        self.node.color_mask_texture = media['color_mask_texture']
        self.node.head_mesh = media['head_mesh']
        self.node.torso_mesh = media['torso_mesh']
        self.node.pelvis_mesh = media['pelvis_mesh']
        self.node.upper_arm_mesh = media['upper_arm_mesh']
        self.node.forearm_mesh = media['forearm_mesh']
        self.node.hand_mesh = media['hand_mesh']
        self.node.upper_leg_mesh = media['upper_leg_mesh']
        self.node.lower_leg_mesh = media['lower_leg_mesh']
        self.node.toes_mesh = media['toes_mesh']
        self.node.style = factory.get_style(character)

    @override
    def update_ai(self) -> None:
        """Override the combat AI completely - we just wander."""
        pass

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.HitMessage):
            if msg.hit_type != 'punch':
                return None
            source_player = msg.get_source_player(bs.Player)
            if source_player:
                self.last_player_attacked_by = source_player
                self.last_attacked_time = bs.time()
                self.last_attacked_type = (msg.hit_type, msg.hit_subtype)
            self.handlemessage(bs.DieMessage())
        elif isinstance(msg, bs.DieMessage):
            if self.node and not msg.immediate:
                try:
                    factory = SpazFactory.get()
                    media = factory.get_media('B-9000')
                    self.node.color_texture = media['color_texture']
                    self.node.color_mask_texture = media['color_mask_texture']
                    self.node.head_mesh = media['head_mesh']
                    self.node.torso_mesh = media['torso_mesh']
                    self.node.pelvis_mesh = media['pelvis_mesh']
                    self.node.upper_arm_mesh = media['upper_arm_mesh']
                    self.node.forearm_mesh = media['forearm_mesh']
                    self.node.hand_mesh = media['hand_mesh']
                    self.node.upper_leg_mesh = media['upper_leg_mesh']
                    self.node.lower_leg_mesh = media['lower_leg_mesh']
                    self.node.toes_mesh = media['toes_mesh']
                    self.node.style = factory.get_style('B-9000')
                    self.node.jump_sounds = media['jump_sounds']
                    self.node.attack_sounds = media['attack_sounds']
                    self.node.impact_sounds = media['impact_sounds']
                    self.node.death_sounds = media['death_sounds']
                    self.node.pickup_sounds = media['pickup_sounds']
                    self.node.fall_sounds = media['fall_sounds']
                except Exception:
                    pass
            self._wander_timer = None
            self._is_dancing = False
            super().handlemessage(msg)
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self._wander_timer = None
            self.handlemessage(bs.DieMessage(immediate=True))
        else:
            super().handlemessage(msg)


# ============================================================================
# CROWD BOT SET
# ============================================================================

class CrowdBotSet(SpazBotSet):
    """Extended bot-set that spawns bots without the usual fanfare."""

    def spawn_crowd_bot(
        self,
        pos: Sequence[float],
        on_spawn_call: Any | None = None,
    ) -> None:
        """Spawn a CrowdBot quietly at the given position."""
        spaz = CrowdBot()
        assert spaz.node
        spaz.node.handlemessage('flash')
        spaz.node.color = UNIFORM_COLOR
        spaz.node.highlight = UNIFORM_HIGHLIGHT
        spaz.node.name = ''
        spaz.node.name_color = (0.0, 0.0, 0.0)
        spaz._bomb_cooldown = 9999
        spaz._pickup_cooldown = 9999
        spaz.handlemessage(
            bs.StandMessage(pos, random.uniform(0, 360))
        )
        self.add_bot(spaz)
        spaz.on_bot_spawned()
        if on_spawn_call is not None:
            on_spawn_call(spaz)


# ============================================================================
# SPOTLIGHT ACTOR
# ============================================================================

class Spotlight(bs.Actor):
    """A persistent light that wanders across the map revealing bots."""

    def __init__(
        self,
        game: UnspottableGame,
        speed: float = 0.12,
    ):
        super().__init__()
        self._game_ref = weakref.ref(game)
        self._speed = speed
        self._revealed_bots: set[int] = set()

        bounds = game.map.get_def_bound_box('map_bounds')
        if bounds is None:
            bounds = (-10, 0, -10, 10, 10, 10)
        min_x, _min_y, min_z, max_x, _max_y, max_z = bounds
        margin_x = (max_x - min_x) * 0.15
        margin_z = (max_z - min_z) * 0.15
        self._safe_min_x = min_x + margin_x
        self._safe_max_x = max_x - margin_x
        self._safe_min_z = min_z + margin_z
        self._safe_max_z = max_z - margin_z

        pts = game.map.ffa_spawn_points
        self._y = pts[0][1] if pts else (_min_y + _max_y) * 0.5

        self._cx = random.uniform(self._safe_min_x, self._safe_max_x)
        self._cz = random.uniform(self._safe_min_z, self._safe_max_z)

        angle = random.uniform(0.0, math.tau)
        self._dx = math.cos(angle)
        self._dz = math.sin(angle)

        self._turn_cooldown = random.uniform(2.0, 5.0)

        self._light = bs.newnode(
            'light',
            attrs={
                'position': (self._cx, self._y, self._cz),
                'color': (1.0, 1.0, 0.8),
                'intensity': 0.6,
                'radius': SPOTLIGHT_RADIUS * 0.15,
                'volume_intensity_scale': 0.0,
                'height_attenuated': False,
            },
        )

        self._ring = bs.newnode(
            'locator',
            attrs={
                'shape': 'circle',
                'position': (self._cx, self._y, self._cz),
                'color': (1.0, 1.0, 0.5),
                'opacity': 0.1,
                'draw_beauty': True,
                'additive': True,
                'size': [SPOTLIGHT_RADIUS * 0.9],
            },
        )

        bs.animate(self._light, 'intensity', {0.0: 0.0, 0.5: 0.6})

        self._update_timer = bs.Timer(
            0.05, bs.WeakCall(self._update), repeat=True
        )

    def _update(self) -> None:
        """Move the spotlight and check for bots in range."""
        if not self._light or not self._ring:
            return

        dt = 0.05

        self._cx += self._dx * self._speed
        self._cz += self._dz * self._speed

        bounced = False
        if self._cx < self._safe_min_x:
            self._cx = self._safe_min_x
            self._dx = abs(self._dx)
            bounced = True
        elif self._cx > self._safe_max_x:
            self._cx = self._safe_max_x
            self._dx = -abs(self._dx)
            bounced = True

        if self._cz < self._safe_min_z:
            self._cz = self._safe_min_z
            self._dz = abs(self._dz)
            bounced = True
        elif self._cz > self._safe_max_z:
            self._cz = self._safe_max_z
            self._dz = -abs(self._dz)
            bounced = True

        if bounced:
            angle = math.atan2(self._dz, self._dx)
            angle += random.uniform(-0.5, 0.5)
            self._dx = math.cos(angle)
            self._dz = math.sin(angle)

        self._turn_cooldown -= dt
        if self._turn_cooldown <= 0.0:
            angle = math.atan2(self._dz, self._dx)
            angle += random.uniform(-0.8, 0.8)
            self._dx = math.cos(angle)
            self._dz = math.sin(angle)
            self._turn_cooldown = random.uniform(2.0, 5.0)

        self._light.position = (self._cx, self._y, self._cz)
        self._ring.position = (self._cx, self._y, self._cz)

        game = self._game_ref()
        if game is None:
            return

        spot_pos = babase.Vec3(self._cx, self._y, self._cz)
        living_bots = game.get_crowd_bots()

        currently_in_range: set[int] = set()

        for bot in living_bots:
            if not bot.node:
                continue
            bot_pos = babase.Vec3(bot.node.position)
            dist = (bot_pos - spot_pos).length()
            bot_id = id(bot)

            if dist < SPOTLIGHT_RADIUS:
                currently_in_range.add(bot_id)
                if bot_id not in self._revealed_bots:
                    bot.set_revealed(True)
                    self._revealed_bots.add(bot_id)
            else:
                if bot_id in self._revealed_bots:
                    bot.set_revealed(False)
                    self._revealed_bots.discard(bot_id)

        stale = self._revealed_bots - currently_in_range
        for bot_id in stale:
            self._revealed_bots.discard(bot_id)

    def _unrevel_all(self) -> None:
        """Decrement reveal count for all bots this spotlight was tracking."""
        game = self._game_ref()
        if game is not None:
            bots_by_id = {id(b): b for b in game.get_crowd_bots()}
            for bot_id in self._revealed_bots:
                bot = bots_by_id.get(bot_id)
                if bot and bot.node:
                    bot.set_revealed(False)
        self._revealed_bots.clear()

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.DieMessage):
            self._unrevel_all()
            self._update_timer = None
            if self._light:
                self._light.delete()
            if self._ring:
                self._ring.delete()
        else:
            super().handlemessage(msg)


# ============================================================================
# DANCE ARROW - A single sliding DDR-style arrow cue
# ============================================================================

class DanceArrow:
    """A screen-space button icon that is part of a sliding train.

    All 6 arrows in a wave spawn at once, spaced out horizontally.
    The whole train scrolls left at ARROW_SCROLL_SPEED. Each arrow
    triggers its dance move when it crosses the hit zone.
    """

    def __init__(
        self,
        direction: str,
        tex_name: str,
        color: tuple[float, float, float],
        game: UnspottableGame,
        index: int = 0,
        sound_name: str = 'bellLow',
    ):
        self._direction = direction
        self._game_ref = weakref.ref(game)
        self._triggered = False
        self._sound = bs.getsound(sound_name)

        img_size = 64.0

        # Position in the train: index 0 is leftmost (hits first).
        start_x = ARROW_SPAWN_X + index * ARROW_SPACING

        # Calculate how long it takes THIS arrow to reach the hit zone.
        distance_to_hit = start_x - ARROW_HIT_X
        hit_time = distance_to_hit / ARROW_SCROLL_SPEED

        # How far past the hit zone before cleanup.
        overshoot = 80.0
        end_x = ARROW_HIT_X - overshoot
        total_distance = start_x - end_x
        total_time = total_distance / ARROW_SCROLL_SPEED

        # Create the image node at the top of the screen.
        self._node = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture(tex_name),
                'absolute_scale': True,
                'position': (start_x, ARROW_LANE_Y),
                'scale': (img_size, img_size),
                'color': color,
                'opacity': 0.0,
                'attach': 'topCenter',
            },
        )

        # Animate position: constant-speed scroll from start to end.
        self._combine = bs.newnode(
            'combine',
            owner=self._node,
            attrs={'size': 2},
        )
        self._combine.connectattr('output', self._node, 'position')
        self._combine.input1 = ARROW_LANE_Y

        bs.animate(self._combine, 'input0', {
            0.0: start_x,
            hit_time: ARROW_HIT_X,
            total_time: end_x,
        })

        # Trigger the beat when arrow reaches hit zone.
        bs.timer(hit_time,
                 bs.WeakCall(self._on_beat))

        # Opacity: fade in quickly, hold, flash at beat, fade out.
        fade_in_time = min(0.4, hit_time * 0.15)
        bs.animate(self._node, 'opacity', {
            0.0: 0.0,
            fade_in_time: 0.8,
            hit_time - 0.05: 0.8,
            hit_time: 1.0,
            hit_time + 0.15: 1.0,
            total_time - 0.1: 0.3,
            total_time: 0.0,
        })

        # Scale pulse at beat moment.
        s = img_size
        self._scale_combine = bs.newnode(
            'combine',
            owner=self._node,
            attrs={'size': 2},
        )
        self._scale_combine.connectattr('output', self._node, 'scale')
        bs.animate(self._scale_combine, 'input0', {
            0.0: s,
            hit_time - 0.05: s,
            hit_time: s * 1.4,
            hit_time + 0.2: s,
            total_time: s * 0.5,
        })
        bs.animate(self._scale_combine, 'input1', {
            0.0: s,
            hit_time - 0.05: s,
            hit_time: s * 1.4,
            hit_time + 0.2: s,
            total_time: s * 0.5,
        })

        # Clean up after animation completes.
        bs.timer(total_time + 0.1,
                 bs.WeakCall(self._cleanup))

    def _on_beat(self) -> None:
        """Arrow reached the hit zone - trigger dance move on all bots."""
        if self._triggered:
            return
        self._triggered = True
        game = self._game_ref()
        if game is None:
            return
        for bot in game.get_crowd_bots():
            bot.execute_dance_move(self._direction)
        # Play the assigned bell chime.
        self._sound.play(volume=0.8)

    def _cleanup(self) -> None:
        """Delete our nodes."""
        if self._node:
            self._node.delete()


# ============================================================================
# DANCE CUE SYSTEM - Manages the DDR arrow lane
# ============================================================================

class DanceCueSystem:
    """Manages waves of dance arrows in Party Mode.

    Each wave is preceded by a dramatic 3-2-1 countdown with
    color-changing numbers and voice callouts. Bots freeze and only
    move to the beat during a wave, then resume wandering during
    the cooldown between waves.

    Sound pattern per wave:
      Moves 1-2: bellLow
      Moves 3-4: bellMed
      Moves 5-6: bellHigh
    """

    # Sound assignments for each move index in a wave.
    WAVE_SOUNDS = [
        'bellLow', 'bellLow',
        'bellMed', 'bellMed',
        'bellHigh', 'bellHigh',
    ]

    # Countdown number colors (cycling per tick).
    COUNTDOWN_COLORS = [
        (1.0, 0.2, 0.2),   # red for 3
        (1.0, 0.8, 0.0),   # yellow for 2
        (0.2, 1.0, 0.3),   # green for 1
    ]

    def __init__(self, game: UnspottableGame):
        self._game_ref = weakref.ref(game)
        self._arrows: list[DanceArrow] = []
        self._wave_timer: bs.Timer | None = None
        self._in_wave: bool = False
        self._countdown_node: bs.Node | None = None

        # Preload bell sounds.
        self._sounds = {
            'bellLow': bs.getsound('bellLow'),
            'bellMed': bs.getsound('bellMed'),
            'bellHigh': bs.getsound('bellHigh'),
        }

        # Preload countdown announce sounds.
        self._announce_sounds = {
            3: bs.getsound('announceThree'),
            2: bs.getsound('announceTwo'),
            1: bs.getsound('announceOne'),
        }
        self._cheer_sound = bs.getsound('cheer')

        # Create the persistent hit-zone marker on the left.
        self._marker = bs.newnode(
            'image',
            attrs={
                'texture': bs.gettexture('nub'),
                'absolute_scale': True,
                'position': (ARROW_HIT_X, ARROW_LANE_Y),
                'scale': (16, 80),
                'color': (1.0, 1.0, 1.0),
                'opacity': 0.25,
                'attach': 'topCenter',
            },
        )

        # Start all bots freestyle dancing right away — it's a party!
        bs.timer(1.0, bs.WeakCall(self._start_all_freestyle))

        # Start with a cooldown so players have room to breathe
        # before the first dance wave.
        bs.timer(WAVE_COOLDOWN, bs.WeakCall(self._launch_wave))

    # --- Wave launch: arrows + synced countdown ---

    def _launch_wave(self) -> None:
        """Spawn the arrow train AND start a countdown synced so that
        '1' appears 1 second before the first arrow hits the beat zone.
        Bots keep freestyle dancing until the first beat actually hits."""
        game = self._game_ref()
        if game is None or game.has_ended():
            return

        self._in_wave = True

        # Pre-generate 6 random moves for this wave.
        wave_moves = []
        for _ in range(WAVE_MOVE_COUNT):
            direction, tex_name, color = random.choice(DANCE_MOVES)
            wave_moves.append((direction, tex_name, color))

        # Spawn ALL 6 arrows at once as a train.
        for idx in range(WAVE_MOVE_COUNT):
            direction, tex_name, color = wave_moves[idx]
            sound_name = self.WAVE_SOUNDS[idx]
            arrow = DanceArrow(
                direction=direction,
                tex_name=tex_name,
                color=color,
                game=game,
                index=idx,
                sound_name=sound_name,
            )
            self._arrows.append(arrow)

        # Calculate when the first arrow reaches the hit zone.
        first_hit_time = (ARROW_SPAWN_X - ARROW_HIT_X) / ARROW_SCROLL_SPEED

        # Schedule countdown: 3, 2, 1 — with "1" at 1s before beat.
        bs.timer(first_hit_time - 3.0,
                 bs.WeakCall(self._show_number_3))
        bs.timer(first_hit_time - 2.0,
                 bs.WeakCall(self._show_number_2))
        bs.timer(first_hit_time - 1.0,
                 bs.WeakCall(self._show_number_1))

        # Freeze bots when countdown hits "1" — gives them a sec to prep.
        bs.timer(first_hit_time - 1.0,
                 bs.WeakCall(self._freeze_bots))

        # Calculate when the last arrow finishes its beat.
        last_start_x = ARROW_SPAWN_X + (WAVE_MOVE_COUNT - 1) * ARROW_SPACING
        last_hit_time = (last_start_x - ARROW_HIT_X) / ARROW_SCROLL_SPEED
        wave_end_time = last_hit_time + BOT_DANCE_DURATION + 0.5
        bs.timer(wave_end_time, bs.WeakCall(self._end_wave))

        # Trim old arrows.
        if len(self._arrows) > 30:
            self._arrows = self._arrows[-12:]

    def _freeze_bots(self) -> None:
        """Freeze all bots for synchronized dance moves."""
        game = self._game_ref()
        if game is None or game.has_ended():
            return
        for bot in game.get_crowd_bots():
            bot.set_dance_mode(True)

    # --- Countdown display ---

    def _show_number_3(self) -> None:
        self._show_number(3)

    def _show_number_2(self) -> None:
        self._show_number(2)

    def _show_number_1(self) -> None:
        self._show_number(1)

    def _show_number(self, val: int) -> None:
        """Display a single countdown number with color, sound, and pop."""
        game = self._game_ref()
        if game is None or game.has_ended():
            return

        # Clean up previous number node.
        if self._countdown_node:
            self._countdown_node.delete()

        # Pick color: 3=red, 2=yellow, 1=green.
        color_idx = 3 - val
        r, g, b = self.COUNTDOWN_COLORS[color_idx]

        self._countdown_node = bs.newnode(
            'text',
            attrs={
                'text': str(val),
                'scale': 4.0,
                'flatness': 1.0,
                'shadow': 1.0,
                'h_align': 'center',
                'v_align': 'center',
                'h_attach': 'center',
                'v_attach': 'center',
                'position': (0, 0),
                'color': (r, g, b, 1.0),
            },
        )
        node = self._countdown_node

        # Color pulse: bright → normal → fade.
        cmb = bs.newnode(
            'combine',
            owner=node,
            attrs={'size': 4},
        )
        bs.animate(cmb, 'input0',
                   {0.0: min(r * 2.0, 1.0), 0.3: r})
        bs.animate(cmb, 'input1',
                   {0.0: min(g * 2.0, 1.0), 0.3: g})
        bs.animate(cmb, 'input2',
                   {0.0: min(b * 2.0, 1.0), 0.3: b})
        bs.animate(cmb, 'input3',
                   {0.0: 1.0, 0.7: 1.0, 0.95: 0.3})
        cmb.connectattr('output', node, 'color')

        # Scale pop: big → settle.
        bs.animate(node, 'scale',
                   {0.0: 6.0, 0.15: 4.0, 0.5: 3.8})

        # Play the announce voice.
        if val in self._announce_sounds:
            self._announce_sounds[val].play(volume=1.5)

        # Auto-cleanup after 1 second (next number replaces it,
        # or for "1" it fades before the beat).
        bs.timer(0.95, bs.WeakCall(self._cleanup_countdown))

    def _cleanup_countdown(self) -> None:
        """Remove the countdown text node."""
        if self._countdown_node:
            self._countdown_node.delete()
            self._countdown_node = None

    def _end_wave(self) -> None:
        """End the current wave — celebrate, then start freestyle."""
        game = self._game_ref()
        if game is None or game.has_ended():
            return

        self._in_wave = False

        # Celebrate! All bots and players party.
        self._cheer_sound.play(volume=1.2)
        for bot in game.get_crowd_bots():
            bot.set_dance_mode(False)
            bot.celebrate(3.0)
        for player in game.players:
            if player.actor and player.actor.node:
                player.actor.node.handlemessage(
                    'celebrate', 3000)

        # After celebration, start freestyle dancing.
        bs.timer(2.0, bs.WeakCall(self._start_all_freestyle))

        # Schedule the next wave after the cooldown.
        self._wave_timer = bs.Timer(
            WAVE_COOLDOWN,
            bs.WeakCall(self._launch_wave),
        )

    def _start_all_freestyle(self) -> None:
        """Start freestyle dancing on all crowd bots."""
        game = self._game_ref()
        if game is None or game.has_ended():
            return
        for bot in game.get_crowd_bots():
            bot.start_freestyle()

    def cleanup(self) -> None:
        """Stop all timers."""
        self._wave_timer = None
        self._cleanup_countdown()
        if self._marker:
            self._marker.delete()


# ============================================================================
# DISCO LIGHTS - Cycling colored lights for Party Mode
# ============================================================================

class DiscoLights:
    """Multiple colored lights that cycle through rainbow colors
    with phase offsets for a rolling disco effect."""

    def __init__(self) -> None:
        self._lights: list[bs.Node] = []
        num_colors = len(DISCO_COLORS)
        cycle_time = 3.0

        for i, pos in enumerate(DISCO_LIGHT_POSITIONS):
            light = bs.newnode(
                'light',
                attrs={
                    'position': pos,
                    'radius': 0.6,
                    'intensity': 0.8,
                    'height_attenuated': False,
                    'volume_intensity_scale': 0.0,
                },
            )
            self._lights.append(light)

            # Phase offset so each light is at a different color.
            phase = (i / len(DISCO_LIGHT_POSITIONS)) * cycle_time

            color_keys_r: dict[float, float] = {}
            color_keys_g: dict[float, float] = {}
            color_keys_b: dict[float, float] = {}
            step = cycle_time / num_colors
            for j, c in enumerate(DISCO_COLORS):
                t = j * step
                color_keys_r[t] = c[0]
                color_keys_g[t] = c[1]
                color_keys_b[t] = c[2]
            # Close the loop.
            color_keys_r[cycle_time] = DISCO_COLORS[0][0]
            color_keys_g[cycle_time] = DISCO_COLORS[0][1]
            color_keys_b[cycle_time] = DISCO_COLORS[0][2]

            cmb = bs.newnode(
                'combine',
                owner=light,
                attrs={'size': 3},
            )
            bs.animate(cmb, 'input0', color_keys_r,
                       loop=True, offset=phase)
            bs.animate(cmb, 'input1', color_keys_g,
                       loop=True, offset=phase)
            bs.animate(cmb, 'input2', color_keys_b,
                       loop=True, offset=phase)
            cmb.connectattr('output', light, 'color')

            # Pulse intensity for extra energy.
            bs.animate(
                light, 'intensity',
                {0.0: 0.5, 0.25: 1.0, 0.5: 0.5},
                loop=True,
                offset=phase * 0.7,
            )

    def cleanup(self) -> None:
        """Remove all disco lights."""
        for light in self._lights:
            if light:
                light.delete()
        self._lights.clear()


# ============================================================================
# CUSTOM PLAYER SPAZ - Only takes damage from punches
# ============================================================================

class UnspottablePlayerSpaz(PlayerSpaz):
    """A PlayerSpaz that is invincible to everything except punches.
    Any punch, no matter how weak, is an instant kill."""

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.HitMessage):
            if msg.hit_type != 'punch':
                return None
            source_player = msg.get_source_player(type(self._player))
            if source_player:
                self.last_player_attacked_by = source_player
                self.last_attacked_time = bs.time()
                self.last_attacked_type = (msg.hit_type, msg.hit_subtype)
            self.handlemessage(bs.DieMessage())
            return None
        return super().handlemessage(msg)


# ============================================================================
# PLAYER & TEAM
# ============================================================================

class Player(bs.Player['Team']):
    """Our player type for this game."""

    playerspaztype = UnspottablePlayerSpaz

    def __init__(self) -> None:
        super().__init__()
        self.punch_cooldown_active: bool = False


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0


# ============================================================================
# UNSPOTTABLE GAME
# ============================================================================

# ba_meta export bascenev1.GameActivity
class UnspottableGame(bs.TeamGameActivity[Player, Team]):
    """Unspottable - Hide among the crowd, hunt other players!

    All players and bots look identical. Choose a game mode:
    Normal (pure crowd blending), Spotlight (dark map with
    roaming lights that reveal bots), or Party (disco lights
    and DDR-style dance cues that bots follow but players don't).
    """

    name = 'Unspottable'
    description = 'Blend in with the crowd. Hunt the other players!'
    announce_player_deaths = True

    @override
    @classmethod
    def get_available_settings(
        cls, sessiontype: type[bs.Session]
    ) -> list[bs.Setting]:
        settings = [
            bs.IntSetting(
                'Kills to Win Per Player',
                min_value=1,
                default=5,
                increment=1,
            ),
            bs.IntSetting(
                'Bot Count',
                min_value=5,
                default=20,
                increment=5,
            ),
            bs.IntChoiceSetting(
                'Time Limit',
                choices=[
                    ('None', 0),
                    ('1 Minute', 60),
                    ('2 Minutes', 120),
                    ('3 Minutes', 180),
                    ('5 Minutes', 300),
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
                ],
                default=1.0,
            ),
            bs.IntChoiceSetting(
                'Game Mode',
                choices=[
                    ('Normal', MODE_NORMAL),
                    ('Spotlight', MODE_SPOTLIGHT),
                    ('Party', MODE_PARTY),
                ],
                default=MODE_NORMAL,
            ),
            bs.IntSetting(
                'Spotlight Count',
                min_value=1,
                default=2,
                increment=1,
            ),
            bs.FloatChoiceSetting(
                'Spotlight Speed',
                choices=[
                    ('Fast', 0.18),
                    ('Normal', 0.12),
                    ('Slow', 0.08),
                    ('Very Slow', 0.05),
                ],
                default=0.12,
            ),
            bs.BoolSetting('Replenish Bots', default=False),
            bs.BoolSetting('Epic Mode', default=False),
        ]
        if issubclass(sessiontype, bs.FreeForAllSession):
            settings.append(
                bs.BoolSetting('Allow Negative Scores', default=False)
            )
        return settings

    @override
    @classmethod
    def supports_session_type(cls, sessiontype: type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession) or issubclass(
            sessiontype, bs.FreeForAllSession
        )

    @override
    @classmethod
    def get_supported_maps(cls, sessiontype: type[bs.Session]) -> list[str]:
        return ['Football Stadium']

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._scoreboard = Scoreboard()
        self._score_to_win: int | None = None
        self._dingsound = bs.getsound('dingSmall')
        self._epic_mode = bool(settings['Epic Mode'])
        self._kills_to_win_per_player = int(
            settings['Kills to Win Per Player']
        )
        self._time_limit = float(settings['Time Limit'])
        self._bot_count = int(settings['Bot Count'])
        self._game_mode = int(settings.get('Game Mode', MODE_NORMAL))
        self._spotlight_count = int(settings['Spotlight Count'])
        self._spotlight_speed = float(settings['Spotlight Speed'])
        self._replenish_bots = bool(settings.get('Replenish Bots', False))
        self._allow_negative_scores = bool(
            settings.get('Allow Negative Scores', False)
        )

        # Crowd management.
        self._crowd: CrowdBotSet | None = None
        self._spotlights: list[Spotlight] = []
        self._bot_replenish_timer: bs.Timer | None = None

        # Party mode systems.
        self._dance_cue_system: DanceCueSystem | None = None
        self._disco_lights: DiscoLights | None = None

        # Music selection.
        self.slow_motion = self._epic_mode
        if self._epic_mode:
            self.default_music = bs.MusicType.EPIC
        elif self._game_mode == MODE_SPOTLIGHT:
            self.default_music = bs.MusicType.SCARY
        elif self._game_mode == MODE_PARTY:
            self.default_music = bs.MusicType.FORWARD_MARCH
        else:
            self.default_music = bs.MusicType.GRAND_ROMP

    @override
    def get_instance_description(self) -> str | Sequence:
        return 'Hunt ${ARG1} players hiding in the crowd.', self._score_to_win

    @override
    def get_instance_description_short(self) -> str | Sequence:
        return 'get ${ARG1} player kills', self._score_to_win

    @override
    def on_team_join(self, team: Team) -> None:
        if self.has_begun():
            self._update_scoreboard()

    @override
    def on_begin(self) -> None:
        super().on_begin()

        self.setup_standard_time_limit(self._time_limit)

        # --- Apply mode-specific lighting ---
        gnode = self.globalsnode
        if self._game_mode == MODE_SPOTLIGHT:
            gnode.tint = (0.7, 0.75, 0.8)
            gnode.ambient_color = (0.75, 0.8, 0.85)
            gnode.vignette_outer = (0.45, 0.46, 0.53)
            gnode.vignette_inner = (0.91, 0.9, 0.92)
        elif self._game_mode == MODE_PARTY:
            gnode.tint = (0.85, 0.75, 0.9)
            gnode.ambient_color = (0.9, 0.85, 0.95)
            gnode.vignette_outer = (0.50, 0.48, 0.55)
            gnode.vignette_inner = (0.93, 0.9, 0.95)

        # Calculate score target.
        self._score_to_win = self._kills_to_win_per_player * max(
            1, max((len(t.players) for t in self.teams), default=0)
        )
        self._update_scoreboard()

        # Create crowd.
        self._crowd = CrowdBotSet()
        self._spawn_crowd()

        # --- Mode-specific setup ---
        if self._game_mode == MODE_SPOTLIGHT:
            for i in range(self._spotlight_count):
                def _make_spotlight(_idx: int = i) -> None:
                    if self.has_ended():
                        return
                    sl = Spotlight(
                        game=self,
                        speed=self._spotlight_speed,
                    )
                    sl.autoretain()
                    self._spotlights.append(sl)
                bs.timer(1.5 + i * 1.0, _make_spotlight)

        elif self._game_mode == MODE_PARTY:
            self._disco_lights = DiscoLights()
            self._dance_cue_system = DanceCueSystem(game=self)

        # Replenish dead bots periodically (only if enabled).
        if self._replenish_bots:
            self._bot_replenish_timer = bs.Timer(
                4.0,
                bs.WeakCall(self._replenish_crowd),
                repeat=True,
            )

    def _spawn_crowd(self) -> None:
        """Spawn the initial crowd of bots."""
        assert self._crowd is not None
        for _ in range(self._bot_count):
            pos = self._get_random_spawn_pos()
            self._crowd.spawn_crowd_bot(pos)

    def _replenish_crowd(self) -> None:
        """Top up the crowd to the target bot count."""
        if self._crowd is None:
            return
        living = len(self._crowd.get_living_bots())
        deficit = self._bot_count - living
        for _ in range(max(0, deficit)):
            pos = self._get_random_spawn_pos()
            self._crowd.spawn_crowd_bot(pos)

    def _get_random_spawn_pos(self) -> tuple[float, float, float]:
        """Get a random position from the map's FFA spawn points."""
        pts = self.map.ffa_spawn_points
        if not pts:
            pts = self.map.spawn_points
        if not pts:
            return (0.0, 5.0, -4.0)
        pt = pts[random.randrange(len(pts))]
        x_range = (-0.5, 0.5) if pt[3] == 0.0 else (-pt[3], pt[3])
        z_range = (-0.5, 0.5) if pt[5] == 0.0 else (-pt[5], pt[5])
        return (
            pt[0] + random.uniform(*x_range),
            pt[1],
            pt[2] + random.uniform(*z_range),
        )

    def get_crowd_bots(self) -> list[CrowdBot]:
        """Return a list of living CrowdBots."""
        if self._crowd is None:
            return []
        bots = self._crowd.get_living_bots()
        return [b for b in bots if isinstance(b, CrowdBot)]

    # --- Player Spawning ---

    @override
    def spawn_player(self, player: Player) -> bs.Actor:
        """Spawn a player disguised as part of the crowd."""
        pos = self._get_random_spawn_pos()

        spaz = self.spawn_player_spaz(
            player,
            position=pos,
            angle=random.uniform(0, 360),
        )

        assert spaz.node
        factory = SpazFactory.get()
        media = factory.get_media(UNIFORM_CHARACTER)

        spaz.node.color = UNIFORM_COLOR
        spaz.node.highlight = UNIFORM_HIGHLIGHT
        spaz.node.color_texture = media['color_texture']
        spaz.node.color_mask_texture = media['color_mask_texture']
        spaz.node.head_mesh = media['head_mesh']
        spaz.node.torso_mesh = media['torso_mesh']
        spaz.node.pelvis_mesh = media['pelvis_mesh']
        spaz.node.upper_arm_mesh = media['upper_arm_mesh']
        spaz.node.forearm_mesh = media['forearm_mesh']
        spaz.node.hand_mesh = media['hand_mesh']
        spaz.node.upper_leg_mesh = media['upper_leg_mesh']
        spaz.node.lower_leg_mesh = media['lower_leg_mesh']
        spaz.node.toes_mesh = media['toes_mesh']
        spaz.node.style = factory.get_style(UNIFORM_CHARACTER)

        spaz.node.jump_sounds = media['jump_sounds']
        spaz.node.attack_sounds = media['attack_sounds']
        spaz.node.impact_sounds = media['impact_sounds']
        spaz.node.death_sounds = media['death_sounds']
        spaz.node.pickup_sounds = media['pickup_sounds']
        spaz.node.fall_sounds = media['fall_sounds']

        spaz.node.name = ''
        spaz.node.name_color = (0.0, 0.0, 0.0)

        self._wrap_punch_controls(player, spaz)

        return spaz

    def _wrap_punch_controls(
        self, player: Player, spaz: PlayerSpaz
    ) -> None:
        """Rewire the punch input to add a cooldown with look animation."""
        p = player
        intp = bs.InputType

        def _custom_punch_press() -> None:
            if p.punch_cooldown_active:
                return
            if not spaz.node:
                return
            if not p.is_alive():
                return

            spaz.on_punch_press()
            spaz.on_punch_release()

            p.punch_cooldown_active = True

            p.assigninput(intp.LEFT_RIGHT, lambda x: None)
            p.assigninput(intp.UP_DOWN, lambda x: None)
            p.assigninput(intp.RUN, lambda x: None)
            p.assigninput(intp.JUMP_PRESS, lambda: None)
            p.assigninput(intp.JUMP_RELEASE, lambda: None)
            p.assigninput(intp.PICK_UP_PRESS, lambda: None)
            p.assigninput(intp.PICK_UP_RELEASE, lambda: None)
            p.assigninput(intp.BOMB_PRESS, lambda: None)
            p.assigninput(intp.BOMB_RELEASE, lambda: None)

            spaz.on_move_left_right(0)
            spaz.on_move_up_down(0)
            spaz.on_run(0.0)

            def _look_left() -> None:
                if spaz.node:
                    spaz.node.move_left_right = -0.3
                    bs.timer(0.05, _stop_move)

            def _look_right() -> None:
                if spaz.node:
                    spaz.node.move_left_right = 0.3
                    bs.timer(0.05, _stop_move)

            def _stop_move() -> None:
                if spaz.node:
                    spaz.node.move_left_right = 0.0

            def _end_cooldown() -> None:
                p.punch_cooldown_active = False
                if not p.is_alive() or not spaz.node:
                    return
                p.assigninput(intp.LEFT_RIGHT, spaz.on_move_left_right)
                p.assigninput(intp.UP_DOWN, spaz.on_move_up_down)
                p.assigninput(intp.RUN, spaz.on_run)
                p.assigninput(intp.JUMP_PRESS, spaz.on_jump_press)
                p.assigninput(intp.JUMP_RELEASE, spaz.on_jump_release)
                p.assigninput(intp.PICK_UP_PRESS, spaz.on_pickup_press)
                p.assigninput(intp.PICK_UP_RELEASE, spaz.on_pickup_release)
                p.assigninput(intp.BOMB_PRESS, spaz.on_bomb_press)
                p.assigninput(intp.BOMB_RELEASE, spaz.on_bomb_release)

            bs.timer(0.2, _look_left)
            bs.timer(0.5, _stop_move)
            bs.timer(0.7, _look_right)
            bs.timer(1.0, _stop_move)

            bs.timer(PUNCH_COOLDOWN_DURATION, _end_cooldown)

        p.assigninput(intp.PUNCH_PRESS, _custom_punch_press)
        p.assigninput(intp.PUNCH_RELEASE, lambda: None)

    # --- Scoring ---

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)

            player = msg.getplayer(Player)
            self.respawn_player(player)

            killer = msg.getkillerplayer(Player)
            if killer is None:
                return None

            if killer.team is player.team:
                if isinstance(self.session, bs.FreeForAllSession):
                    new_score = player.team.score - 1
                    if not self._allow_negative_scores:
                        new_score = max(0, new_score)
                    player.team.score = new_score
                else:
                    self._dingsound.play()
                    for team in self.teams:
                        if team is not killer.team:
                            team.score += 1
            else:
                killer.team.score += 1
                self._dingsound.play()

                if isinstance(killer.actor, PlayerSpaz) and killer.actor:
                    killer.actor.set_score_text(
                        str(killer.team.score)
                        + '/'
                        + str(self._score_to_win),
                        color=killer.team.color,
                        flash=True,
                    )

            self._update_scoreboard()

            assert self._score_to_win is not None
            if any(team.score >= self._score_to_win for team in self.teams):
                bs.timer(0.5, self.end_game)

        elif isinstance(msg, SpazBotDiedMessage):
            pass

        else:
            return super().handlemessage(msg)
        return None

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(
                team, team.score, self._score_to_win
            )

    @override
    def end_game(self) -> None:
        if self._dance_cue_system is not None:
            self._dance_cue_system.cleanup()
        if self._disco_lights is not None:
            self._disco_lights.cleanup()

        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)

    @override
    def on_continue(self) -> None:
        if self._replenish_bots:
            self._replenish_crowd()
