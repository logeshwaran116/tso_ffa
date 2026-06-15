import functools
import random
import math
import colorsys
import setting
from playersdata import pdata
from stats import mystats
from tools import coins
from typing import Sequence
import babase
import bascenev1 as bs
import bascenev1lib
from bascenev1lib import gameutils
from bascenev1lib.actor.playerspaz import *

_settings = setting.get_settings_data()

RANK_EFFECT_MAP = {
    1: ["rainbow", "shine"],
    2: ["sweat"],
    3: ["metal"],
    4: ["iceground"],
}

def effect(repeat_interval=0):
    def _activator(method):
        @functools.wraps(method)
        def _inner_activator(self, *args, **kwargs):
            def _caller():
                try:
                    method(self, *args, **kwargs)
                except:
                    if self is None or not self.is_alive() or not self.node.exists():
                        self._activations = []
                    else:
                        raise
            effect_activation = bs.Timer(
                repeat_interval, babase.Call(_caller), repeat=repeat_interval > 0
            )
            self._activations.append(effect_activation)
        return _inner_activator
    return _activator

def node(check_interval=0):
    def _activator(method):
        @functools.wraps(method)
        def _inner_activator(self):
            node = method(self)
            def _caller():
                if self is None or not self.is_alive() or not self.node.exists():
                    node.delete()
                    self._activations = []
            node_activation = bs.Timer(
                check_interval, babase.Call(_caller), repeat=check_interval > 0
            )
            try:
                self._activations.append(node_activation)
            except AttributeError:
                pass
            return node
        return _inner_activator
    return _activator

class NewPlayerSpaz(PlayerSpaz):
    def __init__(
        self,
        player: bs.Player,
        color: Sequence[float],
        highlight: Sequence[float],
        character: str,
        powerups_expire: bool = True,
        *args,
        **kwargs
    ):
        super().__init__(
            player=player,
            color=color,
            highlight=highlight,
            character=character,
            powerups_expire=powerups_expire,
            *args,
            **kwargs
        )
        self._activations = []
        self.effects = []
        self._pet_node = None
        # State for blink-invisible effect
        self._blink_invisible_state = False
        self._orig_meshes = None
        # State for random single-part blink effect
        self._random_blink_hidden_part = None
        babase._asyncio._asyncio_event_loop.create_task(self.set_effects())

    def _is_the_spaz_game(self) -> bool:
        """Return True when the current activity is TheSpazGame."""
        try:
            activity = self._activity()
        except Exception:
            activity = None
        if activity is None:
            return False
        try:
            if activity.__class__.__name__ == "TheSpazGame":
                return True
        except Exception:
            pass
        try:
            return getattr(activity, "name", None) == "TheSpazGame"
        except Exception:
            return False

    async def set_effects(self):
        # Hide premium/custom/rank effects specifically in TheSpazGame.
        if self._is_the_spaz_game():
            self.effects = []
            return

        try:
            account_id = self._player._sessionplayer.get_v1_account_id()
        except:
            return
        # Priority 1: paid/temporary effect via coin shop (with expiry)
        paid_effect = coins.get_active_effect(account_id)
        if paid_effect:
            self.effects = [paid_effect]
        else:
            # Priority 2: per-user custom effects configured by admins
            custom_effects = pdata.get_custom()['customeffects']
            if account_id in custom_effects:
                self.effects = [custom_effects[account_id]] if isinstance(custom_effects[account_id], str) else custom_effects[account_id]
            else:
                # Priority 3: Top rank-based effects
                if _settings['enablestats']:
                    stats = mystats.get_cached_stats()
                    if account_id in stats and _settings['enableTop5effects']:
                        rank = stats[account_id]["rank"]
                        self.effects = RANK_EFFECT_MAP.get(rank, [])
        if len(self.effects) == 0:
            return
        self._effect_mappings = {
            "spark": self._add_spark,
            "sparkground": self._add_sparkground,
            "sweat": self._add_sweat,
            "sweatground": self._add_sweatground,
            "distortion": self._add_distortion,
            "glow": self._add_glow,
            "shine": self._add_shine,
            "highlightshine": self._add_highlightshine,
            "scorch": self._add_scorch,
            "ice": self._add_ice,
            "iceground": self._add_iceground,
            "iceman": self._add_iceman,
            "slime": self._add_slime,
            "metal": self._add_metal,
            "splinter": self._add_splinter,
            "rainbow": self._add_rainbow,
            "fairydust": self._add_fairydust,
            "firespark": self._add_firespark,
            "noeffect": lambda: None,
            "footprint": self._add_footprint,
            "fire": self._add_fire,
            "darkmagic": self._add_darkmagic,
            "darksn": self._add_darksn,
            "stars": self._add_stars,
            "aure": self._add_aure,
            "orbguard": self._add_orbguard,
            "chispitas": self._add_chispitas,
            "surrounderhead": self._add_surrounderhead,  # Added new effect
            "pet": self._create_pet,  # Mini cosmetic character follower
            "minipet": self._create_pet,  # Alias for mini character pet
            #"blinkinvisible": self._add_blinkinvisible,  # Toggle full-body visibility every 1s
            "randblink": self._add_randblink,  # Randomly hide/show single body parts every 0.7s
            "randomcharacter": self._add_randomcharacter,  # Change character appearance every 5 seconds
            # ── New effects ──
            #"inferno": self._add_inferno,        # Raging fire trail with ember sparks
            #"ghostly": self._add_ghostly,        # Wispy ghost smoke + pale green glow
            #"electric": self._add_electric,      # Crackling electric sparks + lightning flashes
            "galaxy": self._add_galaxy,          # Star nodes orbiting in two interlocked rings
            #"toxiccloud": self._add_toxiccloud,  # Green poison slime cloud
            "aurora": self._add_aurora,          # Northern lights colored rings above head
            #"bloodmoon": self._add_bloodmoon,    # Crimson drips + red pulsing light
            #"demonwings": self._add_demonwings,  # Dark sweeping wings behind player
        }
        for effect in self.effects:
            trigger = self._effect_mappings.get(effect, lambda: None)
            activity = self._activity()
            if activity:
                with activity.context:
                    trigger()

    @effect(repeat_interval=0.1)
    def _add_spark(self):
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=random.randint(1, 10),
            scale=0.5,
            spread=0.2,
            chunk_type="spark"
        )

    @node(check_interval=0.2)
    def _create_pet(self):
        """Create a full-body mini cosmetic pet that follows without gameplay impact."""
        # Use a non-visual anchor (math node) to avoid any visible gizmo/angle marker.
        anchor = bs.newnode(
            'math',
            attrs={'input1': (0.0, 0.0, 0.0), 'input2': (0.0, 0.0, 0.0), 'operation': 'add'},
        )
        try:
            ghost = self._build_ghost_material()
            try:
                color_tex = getattr(self.node, 'color_texture')
            except Exception:
                color_tex = bs.gettexture('neoSpazColor')

            base_materials = [ghost] if ghost else []
            def _mesh_attr(attr_name: str, fallback_mesh: str):
                try:
                    return getattr(self.node, attr_name)
                except Exception:
                    return bs.getmesh(fallback_mesh)

            def _spawn_part(mesh, mesh_scale: float):
                return bs.newnode(
                    'prop',
                    owner=anchor,
                    attrs={
                        'body': 'sphere',
                        'mesh': mesh,
                        'color_texture': color_tex,
                        'mesh_scale': mesh_scale,
                        'body_scale': 0.0,
                        'shadow_size': 0.0,
                        'gravity_scale': 0.0,
                        'reflection': 'soft',
                        'reflection_scale': [0.0],
                        'is_area_of_interest': False,
                        'materials': base_materials,
                    },
                )

            pet_scale = 1.55
            parts = {
                'head': _spawn_part(_mesh_attr('head_mesh', 'neoSpazHead'), 0.27 * pet_scale),
                'torso': _spawn_part(_mesh_attr('torso_mesh', 'neoSpazTorso'), 0.30 * pet_scale),
                'pelvis': _spawn_part(_mesh_attr('pelvis_mesh', 'neoSpazPelvis'), 0.26 * pet_scale),
                'l_uarm': _spawn_part(_mesh_attr('upper_arm_mesh', 'neoSpazUpperArm'), 0.22 * pet_scale),
                'r_uarm': _spawn_part(_mesh_attr('upper_arm_mesh', 'neoSpazUpperArm'), 0.22 * pet_scale),
                'l_farm': _spawn_part(_mesh_attr('forearm_mesh', 'neoSpazForeArm'), 0.20 * pet_scale),
                'r_farm': _spawn_part(_mesh_attr('forearm_mesh', 'neoSpazForeArm'), 0.20 * pet_scale),
                'l_hand': _spawn_part(_mesh_attr('hand_mesh', 'neoSpazHand'), 0.18 * pet_scale),
                'r_hand': _spawn_part(_mesh_attr('hand_mesh', 'neoSpazHand'), 0.18 * pet_scale),
                'l_uleg': _spawn_part(_mesh_attr('upper_leg_mesh', 'neoSpazUpperLeg'), 0.22 * pet_scale),
                'r_uleg': _spawn_part(_mesh_attr('upper_leg_mesh', 'neoSpazUpperLeg'), 0.22 * pet_scale),
                'l_lleg': _spawn_part(_mesh_attr('lower_leg_mesh', 'neoSpazLowerLeg'), 0.20 * pet_scale),
                'r_lleg': _spawn_part(_mesh_attr('lower_leg_mesh', 'neoSpazLowerLeg'), 0.20 * pet_scale),
                'l_toe': _spawn_part(_mesh_attr('toes_mesh', 'neoSpazToes'), 0.16 * pet_scale),
                'r_toe': _spawn_part(_mesh_attr('toes_mesh', 'neoSpazToes'), 0.16 * pet_scale),
            }
            pet_follow_pos = None

            def _cleanup() -> None:
                for n in list(parts.values()) + [anchor]:
                    try:
                        if n.exists():
                            n.delete()
                    except Exception:
                        pass

            def _tick_follow() -> None:
                try:
                    if (
                        self is None
                        or not self.is_alive()
                        or not self.node.exists()
                        or not anchor.exists()
                        or not all(n.exists() for n in parts.values())
                    ):
                        _cleanup()
                        return

                    torso = self.node.torso_position
                    ppos = self.node.position
                    pfor = self.node.position_forward
                    fx = pfor[0] - ppos[0]
                    fz = pfor[2] - ppos[2]
                    flen = math.sqrt((fx * fx) + (fz * fz))
                    if flen < 0.001:
                        v = self.node.velocity
                        fx = v[0]
                        fz = v[2]
                        flen = math.sqrt((fx * fx) + (fz * fz))
                    if flen >= 0.001:
                        fx /= flen
                        fz /= flen
                        self._pet_last_forward = (fx, fz)
                    else:
                        fx, fz = getattr(self, "_pet_last_forward", (0.0, 1.0))

                    # Always follow behind facing direction so pet does not run in front.
                    dirx = fx
                    dirz = fz

                    # Right vector on the XZ plane.
                    rx = dirz
                    rz = -dirx

                    # Desired location is behind + slight right.
                    desired = (
                        torso[0] + (rx * 0.22) - (dirx * 1.35),
                        torso[1] - 0.03,
                        torso[2] + (rz * 0.22) - (dirz * 1.35),
                    )
                    # Smooth follow with lag for natural pet movement.
                    nonlocal pet_follow_pos
                    if pet_follow_pos is None:
                        pet_follow_pos = [desired[0], desired[1], desired[2]]
                    else:
                        dx = desired[0] - pet_follow_pos[0]
                        dy = desired[1] - pet_follow_pos[1]
                        dz = desired[2] - pet_follow_pos[2]
                        dist = math.sqrt((dx * dx) + (dy * dy) + (dz * dz))
                        if dist > 3.0:
                            pet_follow_pos[0], pet_follow_pos[1], pet_follow_pos[2] = desired
                        else:
                            smooth = 0.18
                            pet_follow_pos[0] += dx * smooth
                            pet_follow_pos[1] += dy * smooth
                            pet_follow_pos[2] += dz * smooth

                    # Hard-keep pet behind the player (never in front).
                    to_pet_x = pet_follow_pos[0] - torso[0]
                    to_pet_z = pet_follow_pos[2] - torso[2]
                    forward_dot = (to_pet_x * dirx) + (to_pet_z * dirz)
                    if forward_dot > -0.12:
                        correction = forward_dot + 0.12
                        pet_follow_pos[0] -= dirx * correction
                        pet_follow_pos[2] -= dirz * correction
                    base = (pet_follow_pos[0], pet_follow_pos[1], pet_follow_pos[2])

                    t = bs.time()
                    sway = 0.06 * math.sin(t * 2.4)
                    bob = 0.03 * math.sin(t * 4.5)
                    stride = 0.045 * math.sin(t * 6.0)

                    def _wpos(local_x: float, local_y: float, local_z: float) -> tuple[float, float, float]:
                        return (
                            base[0] + (rx * local_x) + (dirx * local_z),
                            base[1] + local_y,
                            base[2] + (rz * local_x) + (dirz * local_z),
                        )

                    positions = {
                        'torso': _wpos(sway, 0.34 + bob, 0.0),
                        'pelvis': _wpos(sway, 0.18 + bob, 0.0),
                        'head': _wpos(sway, 0.56 + bob, 0.0),
                        'l_uarm': _wpos(-0.18 + sway, 0.37 + bob, stride),
                        'r_uarm': _wpos(0.18 + sway, 0.37 + bob, -stride),
                        'l_farm': _wpos(-0.24 + sway, 0.30 + bob, stride * 1.25),
                        'r_farm': _wpos(0.24 + sway, 0.30 + bob, -stride * 1.25),
                        'l_hand': _wpos(-0.29 + sway, 0.22 + bob, stride * 1.35),
                        'r_hand': _wpos(0.29 + sway, 0.22 + bob, -stride * 1.35),
                        'l_uleg': _wpos(-0.09 + sway, 0.06 + bob, -stride),
                        'r_uleg': _wpos(0.09 + sway, 0.06 + bob, stride),
                        'l_lleg': _wpos(-0.09 + sway, -0.08 + bob, -stride * 1.1),
                        'r_lleg': _wpos(0.09 + sway, -0.08 + bob, stride * 1.1),
                        'l_toe': _wpos(-0.09 + sway, -0.19 + bob, 0.03 - stride),
                        'r_toe': _wpos(0.09 + sway, -0.19 + bob, 0.03 + stride),
                    }
                    for name, node in parts.items():
                        node.position = positions[name]
                        node.velocity = (0.0, 0.0, 0.0)
                    bs.timer(0.03, _tick_follow)
                except Exception:
                    _cleanup()

            bs.timer(0.03, _tick_follow)
            self._pet_node = anchor
            return anchor
        except Exception:
            return anchor

    @effect(repeat_interval=0.1)
    def _add_sparkground(self):
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=random.randint(1, 5),
            scale=0.2,
            spread=0.1,
            chunk_type="spark",
            emit_type="stickers"
        )

    @effect(repeat_interval=0.04)
    def _add_sweat(self):
        velocity = 4.0
        calculate_position = lambda torso_position: torso_position - 0.25 + random.uniform(0, 0.5)
        calculate_velocity = lambda node_velocity, multiplier: random.uniform(-velocity, velocity) + node_velocity * multiplier
        position = tuple(calculate_position(coordinate) for coordinate in self.node.torso_position)
        velocity = (
            calculate_velocity(self.node.velocity[0], 2),
            calculate_velocity(self.node.velocity[1], 4),
            calculate_velocity(self.node.velocity[2], 2),
        )
        bs.emitfx(
            position=position,
            velocity=velocity,
            count=10,
            scale=random.uniform(0.3, 1.4),
            spread=0.1,
            chunk_type="sweat"
        )

    @effect(repeat_interval=0.04)
    def _add_sweatground(self):
        velocity = 1.2
        calculate_position = lambda torso_position: torso_position - 0.25 + random.uniform(0, 0.5)
        calculate_velocity = lambda node_velocity, multiplier: random.uniform(-velocity, velocity) + node_velocity * multiplier
        position = tuple(calculate_position(coordinate) for coordinate in self.node.torso_position)
        velocity = (
            calculate_velocity(self.node.velocity[0], 2),
            calculate_velocity(self.node.velocity[1], 4),
            calculate_velocity(self.node.velocity[2], 2),
        )
        bs.emitfx(
            position=position,
            velocity=velocity,
            count=10,
            scale=random.uniform(0.1, 1.2),
            spread=0.1,
            chunk_type="sweat",
            emit_type="stickers"
        )

    @effect(repeat_interval=1.0)
    def _add_distortion(self):
        bs.emitfx(
            position=self.node.position,
            spread=1.0,
            emit_type="distortion"
        )
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=random.randint(1, 5),
            emit_type="tendrils",
            tendril_type="smoke"
        )

    @effect(repeat_interval=3.0)
    def _add_shine(self):
        shine_factor = 1.2
        dim_factor = 0.90
        default_color = self.node.color
        shiny_color = tuple(channel * shine_factor for channel in default_color)
        dimmy_color = tuple(channel * dim_factor for channel in default_color)
        animation = {
            0: default_color,
            1: dimmy_color,
            2: shiny_color,
            3: default_color
        }
        bs.animate_array(self.node, "color", 3, animation)

    @effect(repeat_interval=9.0)
    def _add_highlightshine(self):
        shine_factor = 1.2
        dim_factor = 0.90
        default_highlight = self.node.highlight
        shiny_highlight = tuple(channel * shine_factor for channel in default_highlight)
        dimmy_highlight = tuple(channel * dim_factor for channel in default_highlight)
        animation = {
            0: default_highlight,
            3: dimmy_highlight,
            6: shiny_highlight,
            9: default_highlight
        }
        bs.animate_array(self.node, "highlight", 3, animation)

    @effect(repeat_interval=1.0)
    def _add_rainbow(self):
        # Pick a vivid bright color and animate body/highlight to it over 1 second.
        h = random.random()
        s = random.uniform(0.85, 1.0)
        v = random.uniform(0.95, 1.0)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        target = (r, g, b)
        # Use current values as start; animate over 1s.
        try:
            start_color = self.node.color
            start_highlight = self.node.highlight
        except Exception:
            start_color = target
            start_highlight = target
        bs.animate_array(self.node, "color", 3, {0.0: start_color, 1.0: target})
        bs.animate_array(self.node, "highlight", 3, {0.0: start_highlight, 1.0: target})

    @node(check_interval=0.5)
    def _add_glow(self):
        glowing_light = bs.newnode(
            "light",
            attrs={
                "color": (1.0, 0.4, 0.5),
                "height_attenuated": False,
                "radius": 0.4
            }
        )
        self.node.connectattr("position", glowing_light, "position")
        bs.animate(glowing_light, "intensity", {0: 0.0, 1: 0.2, 2: 0.0}, loop=True)
        return glowing_light

    @node(check_interval=0.5)
    def _add_scorch(self):
        scorcher = bs.newnode(
            "scorch",
            attrs={
                "position": self.node.position,
                "size": 1.00,
                "big": True
            }
        )
        self.node.connectattr("position", scorcher, "position")
        animation = {
            0: (1, 0, 0),
            1: (0, 1, 0),
            2: (1, 0, 1),
            3: (0, 1, 1),
            4: (1, 0, 0)
        }
        bs.animate_array(scorcher, "color", 3, animation, loop=True)
        return scorcher

    @effect(repeat_interval=0.5)
    def _add_ice(self):
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=random.randint(2, 8),
            scale=0.4,
            spread=0.2,
            chunk_type="ice"
        )

    @effect(repeat_interval=0.05)
    def _add_iceground(self):
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=random.randint(1, 2),
            scale=random.uniform(0, 0.5),
            spread=1.0,
            chunk_type="ice",
            emit_type="stickers"
        )

    @effect(repeat_interval=0.15)
    def _add_iceman(self):
        """Iceman: replicate the frozen visual (shine) without immobilizing.

        - Forces node.frozen True for the visual icy shell and shimmer.
        - Adds subtle blue shimmering via highlight/color animation (loop).
        - Adds a faint cold light and occasional ice particles.
        """
        if self is None or not self.is_alive() or not self.node.exists():
            return

        # Ensure we never immobilize: never assert node.frozen here.
        # If some other system freezes you, we won't interfere.

        # One-time setup for shimmer + light.
        if not hasattr(self, '_iceman_setup_done'):
            try:
                # Subtle shimmering between current and icy tint.
                icy_color = (
                    min(1.0, self.node.color[0] * 0.85 + 0.15),
                    min(1.0, self.node.color[1] * 0.95 + 0.25),
                    min(1.0, self.node.color[2] * 1.10 + 0.30),
                )
                icy_highlight = (
                    min(1.0, self.node.highlight[0] * 0.80 + 0.20),
                    min(1.0, self.node.highlight[1] * 0.95 + 0.25),
                    min(1.0, self.node.highlight[2] * 1.10 + 0.30),
                )
                bs.animate_array(
                    self.node,
                    'color',
                    3,
                    {0.0: self.node.color, 1.0: icy_color, 2.0: self.node.color},
                    loop=True,
                )
                bs.animate_array(
                    self.node,
                    'highlight',
                    3,
                    {0.0: self.node.highlight, 1.0: icy_highlight, 2.0: self.node.highlight},
                    loop=True,
                )
            except Exception:
                pass

            try:
                # Cold light aura.
                self._iceman_light = bs.newnode(
                    'light',
                    owner=self.node,
                    attrs={
                        'color': (0.55, 0.75, 1.0),
                        'height_attenuated': False,
                        'radius': 0.5,
                        'intensity': 0.18,
                    },
                )
                self.node.connectattr('position', self._iceman_light, 'position')
                bs.animate(self._iceman_light, 'intensity', {0: 0.1, 0.6: 0.22, 1.2: 0.1}, loop=True)
            except Exception:
                self._iceman_light = None
            # Add an icy shell overlay (visual only; no collisions)
            try:
                if not hasattr(self, '_iceman_shell') or self._iceman_shell is None or not self._iceman_shell.exists():
                    self._iceman_shell = bs.newnode(
                        'prop',
                        owner=self.node,
                        attrs={
                            'body': 'sphere',
                            'mesh': bs.getmesh('shield'),
                            'mesh_scale': 1.35,
                            'body_scale': 0.0,
                            'shadow_size': 0.0,
                            'gravity_scale': 0.0,
                            'color_texture': bs.gettexture('eggTex3'),
                            'reflection': 'soft',
                            'reflection_scale': [0.25],
                        },
                    )
                    self.node.connectattr('position_center', self._iceman_shell, 'position')
                    # Gentle breathing animation for the shell size.
                    bs.animate(self._iceman_shell, 'mesh_scale', {0.0: 1.30, 0.8: 1.40, 1.6: 1.30}, loop=True)
            except Exception:
                self._iceman_shell = None
            self._iceman_setup_done = True

            # Note: Do not touch node.frozen to avoid any input lock.

        # Subtle floating ice particles to match freeze look.
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=random.randint(1, 4),
            scale=0.35,
            spread=0.2,
            chunk_type='ice',
        )

        # Chance to leave tiny ice sticker trails.
        if random.random() < 0.2:
            bs.emitfx(
                position=self.node.position,
                velocity=self.node.velocity,
                count=1,
                scale=random.uniform(0.08, 0.25),
                spread=0.7,
                chunk_type='ice',
                emit_type='stickers',
            )

    @effect(repeat_interval=0.25)
    def _add_slime(self):
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=random.randint(1, 10),
            scale=0.4,
            spread=0.2,
            chunk_type="slime"
        )

    @effect(repeat_interval=0.25)
    def _add_metal(self):
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=random.randint(1, 4),
            scale=0.4,
            spread=0.1,
            chunk_type="metal"
        )

    @effect(repeat_interval=0.75)
    def _add_splinter(self):
        bs.emitfx(
            position=self.node.position,
            velocity=self.node.velocity,
            count=random.randint(1, 5),
            scale=0.5,
            spread=0.2,
            chunk_type="splinter"
        )

    @effect(repeat_interval=0.25)
    def _add_fairydust(self):
        velocity = 2
        calculate_position = lambda torso_position: torso_position - 0.25 + random.uniform(0, 0.5)
        calculate_velocity = lambda node_velocity, multiplier: random.uniform(-velocity, velocity) + node_velocity * multiplier
        position = tuple(calculate_position(coordinate) for coordinate in self.node.torso_position)
        velocity = (
            calculate_velocity(self.node.velocity[0], 2),
            calculate_velocity(self.node.velocity[1], 4),
            calculate_velocity(self.node.velocity[2], 2)
        )
        bs.emitfx(
            position=position,
            velocity=velocity,
            count=random.randint(1, 10),
            spread=0.1,
            emit_type="fairydust"
        )

    @effect(repeat_interval=0.01)
    def _add_firespark(self):
        bs.emitfx(
            position=self.node.position,
            velocity=(0, 0, 0),
            count=900,
            spread=0.7,
            chunk_type="spark"
        )

    @effect(repeat_interval=0.15)
    def _add_footprint(self):
        # Spawn 5-7 colored footprints at current position
        count = random.randint(5, 7)
        base_pos = self.node.position
        for _ in range(count):
            # small jitter to avoid perfect overlap
            jitter = (random.uniform(-0.05, 0.05), 0.0, random.uniform(-0.05, 0.05))
            # Initial bright color (HSV -> RGB)
            h = random.random()
            s = random.uniform(0.85, 1.0)
            v = random.uniform(0.95, 1.0)
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            color = (r, g, b)
            loc = bs.newnode('locator', owner=self.node,
                             attrs={
                                 'position': (base_pos[0]+jitter[0], base_pos[1]+jitter[1], base_pos[2]+jitter[2]),
                                 'shape': 'circle',
                                 'color': babase.safecolor(color),
                                 'size': [0.12],
                                 'draw_beauty': False,
                                 'additive': False
                             })
            # Rotate through a few vivid colors, changing every 1 second.
            # Generate two more targets to cover ~2 seconds lifetime.
            h2 = random.random(); s2 = random.uniform(0.85, 1.0); v2 = random.uniform(0.95, 1.0)
            c2 = colorsys.hsv_to_rgb(h2, s2, v2)
            h3 = random.random(); s3 = random.uniform(0.85, 1.0); v3 = random.uniform(0.95, 1.0)
            c3 = colorsys.hsv_to_rgb(h3, s3, v3)
            bs.animate_array(loc, 'color', 3, {0.0: color, 1.0: c2, 2.0: c3})
            bs.animate(loc, 'opacity', {0: 1.0, 2.0: 0.0})
            bs.timer(2.0, loc.delete)

    @effect(repeat_interval=0.1)
    def _add_fire(self):
        bs.emitfx(
            position=self.node.position,
            scale=3,
            count=100,
            spread=0.3,
            chunk_type='sweat'
        )

    @effect(repeat_interval=0.1)
    def _add_darkmagic(self):
        c = 0.3
        pos_list = [(c, 0, 0), (0, 0, c), (-c, 0, 0), (0, 0, -c)]
        for p in pos_list:
            m = 1.5
            np = self.node.position
            pos = (np[0] + p[0], np[1] + p[1], np[2] + p[2])
            vel = (random.uniform(-m, m), 30.0, random.uniform(-m, m))
            tex = bs.gettexture('impactBombColor')
            mesh = bs.getmesh('impactBomb')
            node = bs.newnode('prop',
                              owner=self.node,
                              attrs={
                                  'body': 'sphere',
                                  'position': pos,
                                  'velocity': vel,
                                  'mesh': mesh,
                                  'mesh_scale': 0.4,
                                  'body_scale': 0.0,
                                  'shadow_size': 0.0,
                                  'gravity_scale': 0.5,
                                  'color_texture': tex,
                                  'reflection': 'soft',
                                  'reflection_scale': [0.0],
                              })
            light = bs.newnode('light',
                               owner=node,
                               attrs={
                                   'intensity': 1.0,
                                   'volume_intensity_scale': 0.5,
                                   'color': (0.5, 0.0, 1.0),
                                   'radius': 0.035,
                               })
            node.connectattr('position', light, 'position')
            bs.timer(0.25, bs.Call(node.delete))
            bs.timer(0.25, bs.Call(light.delete))

    @effect(repeat_interval=0.1)
    def _add_stars(self):
        c = 0.3
        pos_list = [(c, 0, 0), (0, 0, c), (-c, 0, 0), (0, 0, -c)]
        for p in pos_list:
            m = 1.5
            np = self.node.position
            pos = (np[0] + p[0], np[1] + p[1], np[2] + p[2])
            vel = (random.uniform(-m, m), random.uniform(0.5, 2.0), random.uniform(-m, m))
            texs = ['bombStickyColor', 'aliColor', 'aliColorMask', 'eggTex3']
            tex = bs.gettexture(random.choice(texs))
            mesh = bs.getmesh('flash')
            node = bs.newnode('prop',
                              owner=self.node,
                              attrs={
                                  'body': 'sphere',
                                  'position': pos,
                                  'velocity': vel,
                                  'mesh': mesh,
                                  'mesh_scale': 0.1,
                                  'body_scale': 0.0,
                                  'shadow_size': 0.0,
                                  'gravity_scale': 0.5,
                                  'color_texture': tex,
                                  'reflection': 'soft',
                                  'reflection_scale': [1.5],
                              })
            light = bs.newnode('light',
                               owner=node,
                               attrs={
                                   'intensity': 0.3,
                                   'volume_intensity_scale': 0.5,
                                   'color': (
                                       random.uniform(0.5, 1.5),
                                       random.uniform(0.5, 1.5),
                                       random.uniform(0.5, 1.5)
                                   ),
                                   'radius': 0.035,
                               })
            node.connectattr('position', light, 'position')
            bs.timer(0.25, bs.Call(node.delete))
            bs.timer(0.25, bs.Call(light.delete))

    @effect(repeat_interval=0.1)
    def _add_chispitas(self):
        c = 0.3
        pos_list = [(c, 0, 0), (0, 0, c), (-c, 0, 0), (0, 0, -c)]
        for p in pos_list:
            m = 1.5
            np = self.node.position
            pos = (np[0] + p[0], np[1] + p[1], np[2] + p[2])
            vel = (random.uniform(-m, m), random.uniform(0.5, 2.0), random.uniform(-m, m))
            tex = bs.gettexture('null')
            node = bs.newnode('bomb',
                              owner=self.node,
                              attrs={
                                  'body': 'sphere',
                                  'position': pos,
                                  'velocity': vel,
                                  'mesh': None,
                                  'mesh_scale': 0.1,
                                  'body_scale': 0.0,
                                  'color_texture': tex,
                                  'fuse_length': 0.1,
                              })
            light = bs.newnode('light',
                               owner=node,
                               attrs={
                                   'intensity': 0.3,
                                   'volume_intensity_scale': 0.5,
                                   'color': (
                                       random.uniform(0.5, 1.5),
                                       random.uniform(0.5, 1.5),
                                       random.uniform(0.5, 1.5)
                                   ),
                                   'radius': 0.035,
                               })
            node.connectattr('position', light, 'position')
            bs.timer(0.25, bs.Call(node.delete))
            bs.timer(0.25, bs.Call(light.delete))

    @effect(repeat_interval=1.0)
    def _add_blinkinvisible(self):
        """Toggle the player's meshes invisible/visible every second."""
        if self is None or not self.is_alive() or not self.node.exists():
            return
        body = self.node
        try:
            # Capture original meshes once.
            if self._orig_meshes is None:
                self._orig_meshes = {
                    "head": body.head_mesh,
                    "torso": body.torso_mesh,
                    "upper_arm": body.upper_arm_mesh,
                    "forearm": body.forearm_mesh,
                    "pelvis": body.pelvis_mesh,
                    "hand": body.hand_mesh,
                    "toes": body.toes_mesh,
                    "upper_leg": body.upper_leg_mesh,
                    "lower_leg": body.lower_leg_mesh,
                    "style": getattr(body, "style", None),
                }

            if not self._blink_invisible_state:
                # Hide all body meshes.
                body.head_mesh = None
                body.torso_mesh = None
                body.upper_arm_mesh = None
                body.forearm_mesh = None
                body.pelvis_mesh = None
                body.hand_mesh = None
                body.toes_mesh = None
                body.upper_leg_mesh = None
                body.lower_leg_mesh = None
                # Optionally set a neutral style to avoid glitches.
                if hasattr(body, "style"):
                    body.style = 'cyborg'
                self._blink_invisible_state = True
            else:
                # Restore original meshes.
                m = self._orig_meshes or {}
                body.head_mesh = m.get("head")
                body.torso_mesh = m.get("torso")
                body.upper_arm_mesh = m.get("upper_arm")
                body.forearm_mesh = m.get("forearm")
                body.pelvis_mesh = m.get("pelvis")
                body.hand_mesh = m.get("hand")
                body.toes_mesh = m.get("toes")
                body.upper_leg_mesh = m.get("upper_leg")
                body.lower_leg_mesh = m.get("lower_leg")
                if hasattr(body, "style") and m.get("style") is not None:
                    body.style = m.get("style")
                self._blink_invisible_state = False
        except Exception:
            pass

    @effect(repeat_interval=0.7)
    def _add_randblink(self):
        """Randomly hide/show a single body part every 0.7 seconds.

        One part is hidden at a time; each tick picks a new random part and
        restores the previous one.
        """
        if self is None or not self.is_alive() or not self.node.exists():
            return
        body = self.node
        try:
            # Snapshot original meshes once
            if self._orig_meshes is None:
                self._orig_meshes = {
                    "head": body.head_mesh,
                    "torso": body.torso_mesh,
                    "upper_arm": body.upper_arm_mesh,
                    "forearm": body.forearm_mesh,
                    "pelvis": body.pelvis_mesh,
                    "hand": body.hand_mesh,
                    "toes": body.toes_mesh,
                    "upper_leg": body.upper_leg_mesh,
                    "lower_leg": body.lower_leg_mesh,
                    "style": getattr(body, "style", None),
                }

            # Restore previously hidden part, if any
            if self._random_blink_hidden_part is not None:
                part = self._random_blink_hidden_part
                val = self._orig_meshes.get(part)
                if part == "head":
                    body.head_mesh = val
                elif part == "torso":
                    body.torso_mesh = val
                elif part == "upper_arm":
                    body.upper_arm_mesh = val
                elif part == "forearm":
                    body.forearm_mesh = val
                elif part == "pelvis":
                    body.pelvis_mesh = val
                elif part == "hand":
                    body.hand_mesh = val
                elif part == "toes":
                    body.toes_mesh = val
                elif part == "upper_leg":
                    body.upper_leg_mesh = val
                elif part == "lower_leg":
                    body.lower_leg_mesh = val
                self._random_blink_hidden_part = None

            parts = [
                "head",
                "torso",
                "upper_arm",
                "forearm",
                "pelvis",
                "hand",
                "toes",
                "upper_leg",
                "lower_leg",
            ]
            part = random.choice(parts)
            # Hide the selected part
            if part == "head":
                body.head_mesh = None
            elif part == "torso":
                body.torso_mesh = None
            elif part == "upper_arm":
                body.upper_arm_mesh = None
            elif part == "forearm":
                body.forearm_mesh = None
            elif part == "pelvis":
                body.pelvis_mesh = None
            elif part == "hand":
                body.hand_mesh = None
            elif part == "toes":
                body.toes_mesh = None
            elif part == "upper_leg":
                body.upper_leg_mesh = None
            elif part == "lower_leg":
                body.lower_leg_mesh = None
            self._random_blink_hidden_part = part
        except Exception:
            pass

    @effect(repeat_interval=3.0)
    def _add_randomcharacter(self):
        """Randomly change the player's appearance every 3 seconds (exclude Spaz)."""
        if self is None or not self.is_alive() or not self.node.exists():
            return
        try:
            # Prefer filtered appearances (excludes unpurchased when possible).
            try:
                from bascenev1lib.actor import spazappearance as _spazapp
                # Include locked appearances too so servers without purchases still rotate.
                names = _spazapp.get_appearances(include_locked=True)
            except Exception:
                names = list(bs.app.classic.spaz_appearances.keys())

            # Exclude default 'Spaz' (case-insensitive).
            names = [n for n in names if n.lower() != 'spaz']
            if not names:
                return

            app_name = random.choice(names)
            app = bs.app.classic.spaz_appearances.get(app_name)
            if app is None:
                return
            node = self.node
            # Apply appearance assets directly from Appearance definition.
            try:
                if getattr(app, 'color_texture', ''):
                    node.color_texture = bs.gettexture(app.color_texture)
                if getattr(app, 'color_mask_texture', ''):
                    node.color_mask_texture = bs.gettexture(app.color_mask_texture)
                if getattr(app, 'head_mesh', ''):
                    node.head_mesh = bs.getmesh(app.head_mesh)
                if getattr(app, 'torso_mesh', ''):
                    node.torso_mesh = bs.getmesh(app.torso_mesh)
                if getattr(app, 'pelvis_mesh', ''):
                    node.pelvis_mesh = bs.getmesh(app.pelvis_mesh)
                if getattr(app, 'upper_arm_mesh', ''):
                    node.upper_arm_mesh = bs.getmesh(app.upper_arm_mesh)
                if getattr(app, 'forearm_mesh', ''):
                    node.forearm_mesh = bs.getmesh(app.forearm_mesh)
                if getattr(app, 'hand_mesh', ''):
                    node.hand_mesh = bs.getmesh(app.hand_mesh)
                if getattr(app, 'upper_leg_mesh', ''):
                    node.upper_leg_mesh = bs.getmesh(app.upper_leg_mesh)
                if getattr(app, 'lower_leg_mesh', ''):
                    node.lower_leg_mesh = bs.getmesh(app.lower_leg_mesh)
                if getattr(app, 'toes_mesh', ''):
                    node.toes_mesh = bs.getmesh(app.toes_mesh)
                if getattr(app, 'style', ''):
                    node.style = app.style
            except Exception:
                pass
        except Exception:
            pass

    @effect(repeat_interval=0.01)
    def _add_aure(self):
        def anim(node):
            bs.animate_array(node, 'color', 3, {
                0: (1, 1, 0),
                0.1: (0, 1, 0),
                0.2: (1, 0, 0),
                0.3: (0, 0.5, 1),
                0.4: (1, 0, 1)
            }, loop=True)
            bs.animate_array(node, 'size', 1, {
                0: [1.0],
                0.2: [1.5],
                0.3: [1.0]
            }, loop=True)
        attrs = ['torso_position', 'position_center', 'position']
        for i, pos in enumerate(attrs):
            loc = bs.newnode('locator', owner=self.node,
                             attrs={'shape': 'circleOutline',
                                    'color': self.node.color,
                                    'opacity': 1.0,
                                    'draw_beauty': True,
                                    'additive': False})
            self.node.connectattr(pos, loc, 'position')
            bs.timer(0.1 * i, bs.Call(anim, loc))

    def _build_ghost_material(self):
        """Create and cache a non-colliding material for cosmetic props."""
        try:
            if hasattr(self, "_cached_ghost_material") and self._cached_ghost_material is not None:
                return self._cached_ghost_material
            from bascenev1lib.actor.spazfactory import SpazFactory
            from bascenev1lib.actor.powerupbox import PowerupBoxFactory
            from bascenev1lib.gameutils import SharedObjects as _SO
            factory = SpazFactory.get()
            shared = _SO.get()
            ghost = bs.Material()
            ghost.add_actions(
                conditions=(('they_have_material', factory.spaz_material), 'or',
                            ('they_have_material', shared.player_material), 'or',
                            ('they_have_material', shared.attack_material), 'or',
                            ('they_have_material', shared.pickup_material), 'or',
                            ('they_have_material', PowerupBoxFactory.get().powerup_accept_material)),
                actions=(('modify_part_collision', 'collide', False),
                         ('modify_part_collision', 'physical', False)))
            self._cached_ghost_material = ghost
            return ghost
        except Exception:
            return None

    @effect(repeat_interval=0.0035)
    def _add_orbguard(self):
        # Number of orbs and their spacing
        num_orbs = 3
        radius = 1.2

        orb_data = [
        {'mesh': 'aliHead', 'texture': 'aliColor', 'color': (0.5, 0.0, 1.0)},
        {'mesh': 'agentHead', 'texture': 'agentColor', 'color': (1.0, 0.5, 0.0)},
        {'mesh': 'bonesHead', 'texture': 'bonesColor', 'color': (0.0, 1.0, 0.5)}
    ]
        # Store nodes to re-use/delete as needed
        if not hasattr(self, "_orbguard_nodes"):
            self._orbguard_nodes = []
        if not self.is_alive() or not self.node.exists():
            for node in getattr(self, "_orbguard_nodes", []):
                if node.exists():
                    node.delete()
            self._orbguard_nodes = []
            return
        # Create static orbs only once
        if len(self._orbguard_nodes) == 0:
            for i in range(num_orbs):
                # Angle for even spacing
                data = orb_data[i % len(orb_data)]
                angle = 2 * math.pi * i / num_orbs
                node = bs.newnode('prop',
                                  owner=self.node,
                                  attrs={
                                      'body': 'sphere',
                                      'mesh': bs.getmesh(data['mesh']),
                                      'color_texture': bs.gettexture(data['texture']),
                                      'mesh_scale': 0.5,
                                      'body_scale': 0.0,
                                      'shadow_size': 0.0,
                                      'gravity_scale': 0.0,
                                  })
                light = bs.newnode('light',
                                   owner=node,
                                   attrs={
                                       'intensity': 0.8,
                                       'color': (0.5, 0.0, 1.0),
                                       'radius': 0.05,
                                       'volume_intensity_scale': 0.7,
                                   })
                node.connectattr('position', light, 'position')
                self._orbguard_nodes.append((node, angle))
        # Update positions to stay around player (no rotation)
        np = self.node.torso_position
        for node, angle in self._orbguard_nodes:
            # Orbs remain at fixed angles around player
            pos = (
                np[0] + radius * math.cos(angle),
                np[1] + 0.5,
                np[2] + radius * math.sin(angle)
            )
            node.position = pos

    @effect(repeat_interval=0.0035)
    def _add_premiumhalo(self):
        """Premium halo effect with orbiting heads, pulse light, and spark trail."""
        radius = 1.05
        num_orbs = 4

        if not hasattr(self, "_premiumhalo_nodes"):
            self._premiumhalo_nodes = []
        if not hasattr(self, "_premiumhalo_angle"):
            self._premiumhalo_angle = 0.0
        if not hasattr(self, "_premiumhalo_core_light"):
            self._premiumhalo_core_light = None

        if not self.is_alive() or not self.node.exists():
            for node, light, _, _ in getattr(self, "_premiumhalo_nodes", []):
                if node.exists():
                    node.delete()
                if light.exists():
                    light.delete()
            self._premiumhalo_nodes = []
            if self._premiumhalo_core_light is not None and self._premiumhalo_core_light.exists():
                self._premiumhalo_core_light.delete()
            self._premiumhalo_core_light = None
            return

        if len(self._premiumhalo_nodes) == 0:
            orb_data = [
                ("aliHead", "aliColor", (1.0, 0.5, 0.1)),
                ("frostyHead", "frostyColor", (0.2, 0.8, 1.0)),
                ("cyborgHead", "cyborgColor", (1.0, 0.9, 0.2)),
                ("bonesHead", "bonesColor", (0.9, 0.4, 1.0)),
            ]

            try:
                from bascenev1lib.actor.spazfactory import SpazFactory
                from bascenev1lib.actor.powerupbox import PowerupBoxFactory
                from bascenev1lib.gameutils import SharedObjects as _SO
                factory = SpazFactory.get()
                shared = _SO.get()
                ghost = bs.Material()
                ghost.add_actions(
                    conditions=(('they_have_material', factory.spaz_material), 'or',
                                ('they_have_material', shared.player_material), 'or',
                                ('they_have_material', shared.attack_material), 'or',
                                ('they_have_material', shared.pickup_material), 'or',
                                ('they_have_material', PowerupBoxFactory.get().powerup_accept_material)),
                    actions=(('modify_part_collision', 'collide', False),
                             ('modify_part_collision', 'physical', False)))
            except Exception:
                ghost = None

            for i in range(num_orbs):
                mesh_name, tex_name, light_color = orb_data[i % len(orb_data)]
                base_angle = i * (2 * math.pi / num_orbs)
                node = bs.newnode(
                    'prop',
                    owner=self.node,
                    attrs={
                        'body': 'sphere',
                        'mesh': bs.getmesh(mesh_name),
                        'color_texture': bs.gettexture(tex_name),
                        'mesh_scale': 0.45,
                        'body_scale': 0.0,
                        'shadow_size': 0.0,
                        'gravity_scale': 0.0,
                        'materials': ([ghost] if ghost else [])
                    }
                )
                light = bs.newnode(
                    'light',
                    owner=node,
                    attrs={
                        'intensity': 0.55,
                        'color': light_color,
                        'radius': 0.05,
                        'volume_intensity_scale': 0.6,
                    }
                )
                node.connectattr('position', light, 'position')
                self._premiumhalo_nodes.append((node, light, base_angle, light_color))

                def _freeze_node(n=node):
                    try:
                        if not self.is_alive() or not self.node.exists() or not n.exists():
                            return
                        n.velocity = (0.0, 0.0, 0.0)
                        bs.timer(0.1, _freeze_node)
                    except Exception:
                        return

                bs.timer(0.1, _freeze_node)

            self._premiumhalo_core_light = bs.newnode(
                'light',
                owner=self.node,
                attrs={
                    'color': (1.0, 0.7, 0.2),
                    'height_attenuated': False,
                    'radius': 0.65,
                    'intensity': 0.25,
                },
            )
            self.node.connectattr('position', self._premiumhalo_core_light, 'position')

        self._premiumhalo_angle += 0.03
        if self._premiumhalo_angle > 2 * math.pi:
            self._premiumhalo_angle -= 2 * math.pi

        t = bs.time()
        center = self.node.torso_position
        for i, (node, light, base_angle, _) in enumerate(self._premiumhalo_nodes):
            angle = base_angle + self._premiumhalo_angle
            bob = 0.62 + (0.12 * math.sin((t * 3.0) + i))
            pos = (
                center[0] + radius * math.cos(angle),
                center[1] + bob,
                center[2] + radius * math.sin(angle),
            )
            try:
                node.position = pos
                node.velocity = (0.0, 0.0, 0.0)
            except Exception:
                node.position = pos

            hue = (t * 0.12 + (i / max(1, num_orbs))) % 1.0
            light.color = colorsys.hsv_to_rgb(hue, 0.85, 1.0)
            light.intensity = 0.42 + (0.16 * (0.5 + 0.5 * math.sin((t * 6.0) + i)))

        if self._premiumhalo_core_light is not None and self._premiumhalo_core_light.exists():
            core_hue = (t * 0.08) % 1.0
            self._premiumhalo_core_light.color = colorsys.hsv_to_rgb(core_hue, 0.65, 1.0)
            self._premiumhalo_core_light.intensity = 0.22 + (0.12 * (0.5 + 0.5 * math.sin(t * 4.0)))

        bs.emitfx(
            position=(center[0], center[1] + 0.65, center[2]),
            velocity=(0.0, 0.15, 0.0),
            count=1,
            scale=0.22,
            spread=0.08,
            chunk_type="spark"
        )

    @effect(repeat_interval=0.02)
    def _add_solarcrown(self):
        """Radiant tri-ring crown with warm pulse and sparkle."""
        if not hasattr(self, "_solarcrown_nodes"):
            self._solarcrown_nodes = []
        if not hasattr(self, "_solarcrown_light"):
            self._solarcrown_light = None
        if not hasattr(self, "_solarcrown_tick"):
            self._solarcrown_tick = 0

        if not self.is_alive() or not self.node.exists():
            for loc, _, _, _ in getattr(self, "_solarcrown_nodes", []):
                if loc.exists():
                    loc.delete()
            self._solarcrown_nodes = []
            if self._solarcrown_light is not None and self._solarcrown_light.exists():
                self._solarcrown_light.delete()
            self._solarcrown_light = None
            return

        if len(self._solarcrown_nodes) == 0:
            ring_setup = [
                (0.88, 0.92, 0.0),
                (1.02, 1.18, 1.7),
                (1.16, 1.42, 3.2),
            ]
            for yoff, base_size, phase in ring_setup:
                loc = bs.newnode(
                    'locator',
                    owner=self.node,
                    attrs={
                        'shape': 'circleOutline',
                        'color': (1.0, 0.8, 0.2),
                        'opacity': 0.95,
                        'draw_beauty': True,
                        'additive': True,
                    },
                )
                self._solarcrown_nodes.append((loc, yoff, base_size, phase))
            self._solarcrown_light = bs.newnode(
                'light',
                owner=self.node,
                attrs={
                    'color': (1.0, 0.7, 0.3),
                    'height_attenuated': False,
                    'radius': 0.72,
                    'intensity': 0.24,
                },
            )
            self.node.connectattr('position', self._solarcrown_light, 'position')

        self._solarcrown_tick += 1
        t = bs.time()
        torso = self.node.torso_position

        for idx, data in enumerate(self._solarcrown_nodes):
            loc, yoff, base_size, phase = data
            if not loc.exists():
                continue
            loc.position = (
                torso[0],
                torso[1] + yoff + (0.04 * math.sin((t * 2.5) + phase)),
                torso[2],
            )
            hue = (0.10 + (t * 0.08) + (idx * 0.06)) % 1.0
            loc.color = colorsys.hsv_to_rgb(hue, 0.72, 1.0)
            loc.size = [base_size + (0.08 * math.sin((t * 4.1) + phase))]

        if self._solarcrown_light is not None and self._solarcrown_light.exists():
            self._solarcrown_light.intensity = 0.2 + (0.12 * (0.5 + 0.5 * math.sin(t * 5.0)))
            self._solarcrown_light.color = colorsys.hsv_to_rgb((0.10 + (t * 0.05)) % 1.0, 0.6, 1.0)

        if self._solarcrown_tick % 6 == 0:
            bs.emitfx(
                position=(torso[0], torso[1] + 1.18, torso[2]),
                velocity=(0.0, 0.2, 0.0),
                count=2,
                scale=0.18,
                spread=0.1,
                chunk_type='spark',
            )

    @effect(repeat_interval=0.01)
    def _add_nebulashards(self):
        """Dual-spin shard constellation with shifting cosmic colors."""
        if not hasattr(self, "_nebulashards_nodes"):
            self._nebulashards_nodes = []
        if not hasattr(self, "_nebulashards_angle"):
            self._nebulashards_angle = 0.0
        if not hasattr(self, "_nebulashards_tick"):
            self._nebulashards_tick = 0

        if not self.is_alive() or not self.node.exists():
            for node, light, _, _, _, _ in getattr(self, "_nebulashards_nodes", []):
                if node.exists():
                    node.delete()
                if light.exists():
                    light.delete()
            self._nebulashards_nodes = []
            return

        if len(self._nebulashards_nodes) == 0:
            ghost = self._build_ghost_material()
            shard_data = [
                ("aliHead", "aliColor"),
                ("agentHead", "agentColor"),
                ("frostyHead", "frostyColor"),
                ("cyborgHead", "cyborgColor"),
                ("bonesHead", "bonesColor"),
            ]
            for i in range(5):
                mesh_name, tex_name = shard_data[i % len(shard_data)]
                base_angle = i * (2 * math.pi / 5)
                radius = 0.88 + (0.12 * (i % 2))
                yoff = 0.35 + (0.08 * (i % 3))
                spin = 1.0 if i % 2 == 0 else -1.35
                node = bs.newnode(
                    'prop',
                    owner=self.node,
                    attrs={
                        'body': 'sphere',
                        'mesh': bs.getmesh(mesh_name),
                        'color_texture': bs.gettexture(tex_name),
                        'mesh_scale': 0.36,
                        'body_scale': 0.0,
                        'shadow_size': 0.0,
                        'gravity_scale': 0.0,
                        'materials': ([ghost] if ghost else []),
                    },
                )
                light = bs.newnode(
                    'light',
                    owner=node,
                    attrs={
                        'intensity': 0.5,
                        'color': (0.4, 0.7, 1.0),
                        'radius': 0.045,
                        'volume_intensity_scale': 0.6,
                    },
                )
                node.connectattr('position', light, 'position')
                self._nebulashards_nodes.append((node, light, base_angle, radius, yoff, spin))

                def _freeze_node(n=node):
                    try:
                        if not self.is_alive() or not self.node.exists() or not n.exists():
                            return
                        n.velocity = (0.0, 0.0, 0.0)
                        bs.timer(0.1, _freeze_node)
                    except Exception:
                        return

                bs.timer(0.1, _freeze_node)

        self._nebulashards_tick += 1
        self._nebulashards_angle += 0.05
        if self._nebulashards_angle > 2 * math.pi:
            self._nebulashards_angle -= 2 * math.pi

        t = bs.time()
        torso = self.node.torso_position
        for i, (node, light, base_angle, radius, yoff, spin) in enumerate(self._nebulashards_nodes):
            angle = base_angle + (self._nebulashards_angle * spin)
            pos = (
                torso[0] + radius * math.cos(angle),
                torso[1] + yoff + (0.1 * math.sin((t * 3.5) + i)),
                torso[2] + radius * math.sin(angle),
            )
            try:
                node.position = pos
                node.velocity = (0.0, 0.0, 0.0)
            except Exception:
                node.position = pos

            hue = ((t * 0.1) + (i * 0.17)) % 1.0
            light.color = colorsys.hsv_to_rgb(hue, 0.8, 1.0)
            light.intensity = 0.38 + (0.18 * (0.5 + 0.5 * math.sin((t * 5.0) + i)))

        if self._nebulashards_tick % 10 == 0:
            bs.emitfx(
                position=(torso[0], torso[1] + 0.75, torso[2]),
                velocity=(0.0, 0.2, 0.0),
                count=2,
                emit_type='tendrils',
                tendril_type='smoke',
            )

    @effect(repeat_interval=0.08)
    def _add_thunderaura(self):
        """Storm aura with electric flashes and crackling sparks."""
        if not hasattr(self, "_thunderaura_light"):
            self._thunderaura_light = None
        if not hasattr(self, "_thunderaura_tick"):
            self._thunderaura_tick = 0

        if not self.is_alive() or not self.node.exists():
            if self._thunderaura_light is not None and self._thunderaura_light.exists():
                self._thunderaura_light.delete()
            self._thunderaura_light = None
            return

        if self._thunderaura_light is None or not self._thunderaura_light.exists():
            self._thunderaura_light = bs.newnode(
                'light',
                owner=self.node,
                attrs={
                    'color': (0.45, 0.7, 1.0),
                    'height_attenuated': False,
                    'radius': 0.55,
                    'intensity': 0.2,
                },
            )
            self.node.connectattr('position', self._thunderaura_light, 'position')

        self._thunderaura_tick += 1
        t = bs.time()
        pos = self.node.torso_position
        flash = (self._thunderaura_tick % 6 == 0)

        if flash:
            self._thunderaura_light.color = (0.85, 0.92, 1.0)
            self._thunderaura_light.intensity = 0.85
            self._thunderaura_light.radius = 0.85
            bs.emitfx(
                position=(pos[0], pos[1] + 0.6, pos[2]),
                velocity=self.node.velocity,
                count=random.randint(8, 14),
                scale=0.4,
                spread=0.3,
                chunk_type='spark',
            )
            bs.emitfx(
                position=(pos[0], pos[1] + 0.6, pos[2]),
                spread=0.7,
                emit_type='distortion',
            )
        else:
            hue = (0.55 + 0.03 * math.sin(t * 0.8)) % 1.0
            self._thunderaura_light.color = colorsys.hsv_to_rgb(hue, 0.55, 1.0)
            self._thunderaura_light.intensity = 0.16 + (0.08 * random.random())
            self._thunderaura_light.radius = 0.52
            bs.emitfx(
                position=(pos[0], pos[1] + 0.5, pos[2]),
                velocity=self.node.velocity,
                count=2,
                scale=0.2,
                spread=0.18,
                chunk_type='spark',
            )

    @effect(repeat_interval=0.06)
    def _add_voidrift(self):
        """Dark rift orb with distortion pulses and cursed glow."""
        if not hasattr(self, "_voidrift_node"):
            self._voidrift_node = None
        if not hasattr(self, "_voidrift_light"):
            self._voidrift_light = None
        if not hasattr(self, "_voidrift_angle"):
            self._voidrift_angle = 0.0
        if not hasattr(self, "_voidrift_tick"):
            self._voidrift_tick = 0

        if not self.is_alive() or not self.node.exists():
            if self._voidrift_node is not None and self._voidrift_node.exists():
                self._voidrift_node.delete()
            if self._voidrift_light is not None and self._voidrift_light.exists():
                self._voidrift_light.delete()
            self._voidrift_node = None
            self._voidrift_light = None
            return

        if self._voidrift_node is None or not self._voidrift_node.exists():
            ghost = self._build_ghost_material()
            self._voidrift_node = bs.newnode(
                'prop',
                owner=self.node,
                attrs={
                    'body': 'sphere',
                    'mesh': bs.getmesh('bonesHead'),
                    'color_texture': bs.gettexture('powerupCurse'),
                    'mesh_scale': 0.58,
                    'body_scale': 0.0,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.0,
                    'materials': ([ghost] if ghost else []),
                },
            )
            self._voidrift_light = bs.newnode(
                'light',
                owner=self._voidrift_node,
                attrs={
                    'intensity': 0.52,
                    'color': (0.62, 0.18, 1.0),
                    'radius': 0.06,
                    'volume_intensity_scale': 0.7,
                },
            )
            self._voidrift_node.connectattr('position', self._voidrift_light, 'position')

        self._voidrift_tick += 1
        self._voidrift_angle += 0.09
        if self._voidrift_angle > 2 * math.pi:
            self._voidrift_angle -= 2 * math.pi

        t = bs.time()
        torso = self.node.torso_position
        pos = (
            torso[0] + 0.34 * math.cos(self._voidrift_angle),
            torso[1] + 1.05 + (0.12 * math.sin(t * 2.2)),
            torso[2] + 0.34 * math.sin(self._voidrift_angle),
        )
        try:
            self._voidrift_node.position = pos
            self._voidrift_node.velocity = (0.0, 0.0, 0.0)
        except Exception:
            self._voidrift_node.position = pos

        if self._voidrift_light is not None and self._voidrift_light.exists():
            hue = (0.78 + (0.05 * math.sin(t * 0.7))) % 1.0
            self._voidrift_light.color = colorsys.hsv_to_rgb(hue, 0.92, 1.0)
            self._voidrift_light.intensity = 0.42 + (0.16 * (0.5 + 0.5 * math.sin(t * 4.6)))

        if self._voidrift_tick % 4 == 0:
            bs.emitfx(
                position=pos,
                spread=0.9,
                emit_type='distortion',
            )
        if self._voidrift_tick % 3 == 0:
            bs.emitfx(
                position=pos,
                velocity=(0.0, 0.15, 0.0),
                count=2,
                emit_type='tendrils',
                tendril_type='smoke',
            )

    @effect(repeat_interval=0.02)
    def _add_crystalwings(self):
        """Animated crystal wing pair behind player with cold glow."""
        if not hasattr(self, "_crystalwings_nodes"):
            self._crystalwings_nodes = []
        if not hasattr(self, "_crystalwings_tick"):
            self._crystalwings_tick = 0

        if not self.is_alive() or not self.node.exists():
            for node, light, _, _ in getattr(self, "_crystalwings_nodes", []):
                if node.exists():
                    node.delete()
                if light.exists():
                    light.delete()
            self._crystalwings_nodes = []
            return

        if len(self._crystalwings_nodes) == 0:
            ghost = self._build_ghost_material()
            for i, side in enumerate((-1, 1)):
                node = bs.newnode(
                    'prop',
                    owner=self.node,
                    attrs={
                        'body': 'sphere',
                        'mesh': bs.getmesh('shield'),
                        'color_texture': bs.gettexture('frostyColor'),
                        'mesh_scale': 0.72,
                        'body_scale': 0.0,
                        'shadow_size': 0.0,
                        'gravity_scale': 0.0,
                        'materials': ([ghost] if ghost else []),
                    },
                )
                light = bs.newnode(
                    'light',
                    owner=node,
                    attrs={
                        'intensity': 0.44,
                        'color': (0.55, 0.9, 1.0),
                        'radius': 0.05,
                        'volume_intensity_scale': 0.65,
                    },
                )
                node.connectattr('position', light, 'position')
                self._crystalwings_nodes.append((node, light, side, i * math.pi))

                def _freeze_node(n=node):
                    try:
                        if not self.is_alive() or not self.node.exists() or not n.exists():
                            return
                        n.velocity = (0.0, 0.0, 0.0)
                        bs.timer(0.1, _freeze_node)
                    except Exception:
                        return

                bs.timer(0.1, _freeze_node)

        self._crystalwings_tick += 1
        t = bs.time()
        torso = self.node.torso_position
        for node, light, side, phase in self._crystalwings_nodes:
            flap = math.sin((t * 6.0) + phase)
            pos = (
                torso[0] + (side * (0.48 + (0.16 * flap))),
                torso[1] + 0.47 + (0.1 * abs(flap)),
                torso[2] - 0.38 - (0.1 * abs(flap)),
            )
            try:
                node.position = pos
                node.velocity = (0.0, 0.0, 0.0)
                node.mesh_scale = 0.68 + (0.16 * abs(flap))
            except Exception:
                node.position = pos
            light.intensity = 0.34 + (0.18 * abs(flap))
            light.color = (0.45 + 0.2 * abs(flap), 0.85, 1.0)

        if self._crystalwings_tick % 7 == 0:
            bs.emitfx(
                position=(torso[0], torso[1] + 0.45, torso[2] - 0.4),
                velocity=(0.0, 0.08, -0.05),
                count=2,
                scale=0.2,
                spread=0.08,
                chunk_type='ice',
            )

    @effect(repeat_interval=0.0035)
    def _add_darksn(self):
        radius = 0.9
        num_props = 1
        if not hasattr(self, "_darksn_nodes"):
            self._darksn_nodes = []
        if not hasattr(self, "_darksn_angle"):
            self._darksn_angle = 0.0
        if not self.is_alive() or not self.node.exists():
            for node in getattr(self, "_darksn_nodes", []):
                if node.exists():
                    node.delete()
            self._darksn_nodes = []
            return
        if len(self._darksn_nodes) == 0:
            tex = bs.gettexture('powerupCurse')
            mesh = bs.getmesh('bonesHead')
            # Build ghost material to avoid any interaction.
            try:
                from bascenev1lib.actor.spazfactory import SpazFactory
                from bascenev1lib.actor.powerupbox import PowerupBoxFactory
                from bascenev1lib.gameutils import SharedObjects as _SO
                factory = SpazFactory.get()
                shared = _SO.get()
                ghost = bs.Material()
                ghost.add_actions(
                    conditions=(('they_have_material', factory.spaz_material), 'or',
                                ('they_have_material', shared.player_material), 'or',
                                ('they_have_material', shared.attack_material), 'or',
                                ('they_have_material', shared.pickup_material), 'or',
                                ('they_have_material', PowerupBoxFactory.get().powerup_accept_material)),
                    actions=(('modify_part_collision', 'collide', False),
                             ('modify_part_collision', 'physical', False)))
            except Exception:
                ghost = None
            for _ in range(num_props):
                node = bs.newnode('prop',
                                  owner=self.node,
                                  attrs={
                                      'body': 'sphere',
                                      'mesh': mesh,
                                      'color_texture': tex,
                                      'mesh_scale': 0.45,
                                      'body_scale': 0.0,
                                      'shadow_size': 0.0,
                                      'gravity_scale': 0.0,
                                      'materials': ([ghost] if ghost else [])
                                  })
                light = bs.newnode('light',
                                   owner=node,
                                   attrs={
                                       'intensity': 0.8,
                                       'color': (0.6, 0, 0.8),
                                       'radius': 0.03,
                                       'volume_intensity_scale': 0.5,
                                   })
                node.connectattr('position', light, 'position')
                # Freeze velocity periodically to prevent drift on contact.
                def _freeze_node(n=node):
                    try:
                        if not self.is_alive() or not self.node.exists() or not n.exists():
                            return
                        n.velocity = (0.0, 0.0, 0.0)
                        bs.timer(0.1, _freeze_node)
                    except Exception:
                        return
                bs.timer(0.1, _freeze_node)
                self._darksn_nodes.append(node)
        self._darksn_angle += 0.05
        if self._darksn_angle > 2 * math.pi:
            self._darksn_angle -= 2 * math.pi
        np = self.node.torso_position
        for i, node in enumerate(self._darksn_nodes):
            angle = self._darksn_angle + 2 * math.pi * i / num_props
            target_pos = (
                np[0] + radius * math.cos(angle),
                np[1] + 0.5,
                np[2] + radius * math.sin(angle)
            )
            # Hard lock position and zero velocity to avoid disruption by contacts.
            try:
                node.position = target_pos
                node.velocity = (0.0, 0.0, 0.0)
            except Exception:
                node.position = target_pos

    @effect(repeat_interval=0.0035)
    def _add_surrounderhead(self):
        # Number of heads and their spacing
        num_heads = 3
        radius = 0.85
        
        # Different head meshes and textures for variety
        head_data = [
            {'mesh': 'aliHead', 'texture': 'aliColor', 'color': (1.0, 0.5, 0.0)},
            {'mesh': 'bunnyHead', 'texture': 'bunnyColor', 'color': (0.0, 1.0, 0.5)},
            {'mesh': 'bonesHead', 'texture': 'bonesColor', 'color': (0.5, 0.0, 1.0)}
        ]
        
        # Store nodes and their angles
        if not hasattr(self, "_surrounderhead_nodes"):
            self._surrounderhead_nodes = []
        if not hasattr(self, "_surrounderhead_angle"):
            self._surrounderhead_angle = 0.0
        if not hasattr(self, "_surrounderhead_bob_offset"):
            self._surrounderhead_bob_offset = 0.0
            
        # Clean up if player is gone
        if not self.is_alive() or not self.node.exists():
            for node, light in getattr(self, "_surrounderhead_nodes", []):
                if node.exists():
                    node.delete()
                if light.exists():
                    light.delete()
            self._surrounderhead_nodes = []
            return
            
        # Create heads only once
        if len(self._surrounderhead_nodes) == 0:
            # Build a ghost material so these heads never collide/pickup/punch.
            try:
                from bascenev1lib.actor.spazfactory import SpazFactory
                from bascenev1lib.actor.powerupbox import PowerupBoxFactory
                from bascenev1lib.gameutils import SharedObjects as _SO
                factory = SpazFactory.get()
                shared = _SO.get()
                ghost = bs.Material()
                ghost.add_actions(
                    conditions=(('they_have_material', factory.spaz_material), 'or',
                                ('they_have_material', shared.player_material), 'or',
                                ('they_have_material', shared.attack_material), 'or',
                                ('they_have_material', shared.pickup_material), 'or',
                                ('they_have_material', PowerupBoxFactory.get().powerup_accept_material)),
                    actions=(('modify_part_collision', 'collide', False),
                             ('modify_part_collision', 'physical', False)))
            except Exception:
                ghost = None
                shared = None
            for i in range(num_heads):
                data = head_data[i % len(head_data)]
                node = bs.newnode('prop',
                                  owner=self.node,
                                  attrs={
                                      'body': 'sphere',
                                      'mesh': bs.getmesh(data['mesh']),
                                      'color_texture': bs.gettexture(data['texture']),
                                      'mesh_scale': 0.6,
                                      'body_scale': 0.0,
                                      'shadow_size': 0.0,
                                      'gravity_scale': 0.0,
                                      'materials': ([ghost] if ghost else [])
                                  })
                light = bs.newnode('light',
                                   owner=node,
                                   attrs={
                                       'intensity': 0.6,
                                       'color': data['color'],
                                       'radius': 0.04,
                                       'volume_intensity_scale': 0.6,
                                   })
                node.connectattr('position', light, 'position')
                self._surrounderhead_nodes.append((node, i * (2 * math.pi / num_heads)))
                # Extra safety: zero out velocity each tick to avoid drift if anything touches it.
                def _freeze_node(n=node):
                    try:
                        if not self.is_alive() or not self.node.exists() or not n.exists():
                            return
                        n.velocity = (0.0, 0.0, 0.0)
                        bs.timer(0.1, _freeze_node)
                    except Exception:
                        return
                bs.timer(0.1, _freeze_node)
        
        # Update angle and bob offset for animation
        self._surrounderhead_angle += 0.03
        if self._surrounderhead_angle > 2 * math.pi:
            self._surrounderhead_angle -= 2 * math.pi
            
        # Bobbing motion (up and down)
        self._surrounderhead_bob_offset = math.sin(bs.time() * 3) * 0.1
        
        # Update positions
        np = self.node.torso_position
        for i, (node, base_angle) in enumerate(self._surrounderhead_nodes):
            # Calculate position with rotation and bobbing
            angle = base_angle + self._surrounderhead_angle
            bob_height = self._surrounderhead_bob_offset + 0.5
            target_pos = (
                np[0] + radius * math.cos(angle),
                np[1] + bob_height,
                np[2] + radius * math.sin(angle)
            )
            # Hard lock position and zero velocity to prevent any disruption.
            try:
                node.position = target_pos
                node.velocity = (0.0, 0.0, 0.0)
            except Exception:
                node.position = target_pos

    # ══════════════════════════════════════════════════════════
    #  NEW EFFECTS
    # ══════════════════════════════════════════════════════════

    @effect(repeat_interval=0.06)
    def _add_inferno(self):
        """Raging fire trail — intense flames, ember sparks, scorch ground marks."""
        if not self.is_alive() or not self.node.exists():
            return
        pos = self.node.position
        torso = self.node.torso_position
        vel = self.node.velocity

        # Rising fire tendrils from torso
        bs.emitfx(
            position=torso,
            velocity=(vel[0] * 0.3, vel[1] * 0.3 + 1.5, vel[2] * 0.3),
            count=random.randint(4, 8),
            scale=random.uniform(0.6, 1.4),
            spread=0.3,
            chunk_type='sweat',
        )
        # Ember sparks
        bs.emitfx(
            position=torso,
            velocity=(vel[0] + random.uniform(-2, 2), vel[1] + random.uniform(1, 4), vel[2] + random.uniform(-2, 2)),
            count=random.randint(3, 6),
            scale=0.35,
            spread=0.4,
            chunk_type='spark',
        )
        # Ground scorch stickers
        if random.random() < 0.4:
            bs.emitfx(
                position=pos,
                velocity=(0, 0, 0),
                count=2,
                scale=random.uniform(0.3, 0.7),
                spread=0.3,
                chunk_type='spark',
                emit_type='stickers',
            )
        # Dynamic fire light
        if not hasattr(self, '_inferno_light') or not self._inferno_light.exists():
            self._inferno_light = bs.newnode(
                'light', owner=self.node,
                attrs={'color': (1.0, 0.35, 0.0), 'height_attenuated': False,
                       'radius': 0.7, 'intensity': 0.0},
            )
            self.node.connectattr('position', self._inferno_light, 'position')
        self._inferno_light.intensity = random.uniform(0.4, 0.9)
        self._inferno_light.color = (
            random.uniform(0.9, 1.0),
            random.uniform(0.2, 0.45),
            0.0,
        )

    @effect(repeat_interval=0.08)
    def _add_ghostly(self):
        """Ghost effect — wispy smoke trails and eerie pale green glow."""
        if not self.is_alive() or not self.node.exists():
            return
        torso = self.node.torso_position
        vel = self.node.velocity

        # Wispy smoke upward trails
        bs.emitfx(
            position=torso,
            velocity=(vel[0] * 0.2, vel[1] * 0.2 + 0.8, vel[2] * 0.2),
            count=random.randint(2, 5),
            scale=random.uniform(0.5, 1.2),
            spread=0.2,
            emit_type='tendrils',
            tendril_type='thin_smoke',
        )
        # Occasional distortion pulse
        if random.random() < 0.15:
            bs.emitfx(position=torso, spread=0.5, emit_type='distortion')

        # Ghostly pale green light
        if not hasattr(self, '_ghost_light') or not self._ghost_light.exists():
            self._ghost_light = bs.newnode(
                'light', owner=self.node,
                attrs={'color': (0.5, 1.0, 0.6), 'height_attenuated': False,
                       'radius': 0.5, 'intensity': 0.15},
            )
            self.node.connectattr('position', self._ghost_light, 'position')
            bs.animate(self._ghost_light, 'intensity', {0: 0.05, 0.8: 0.25, 1.6: 0.05}, loop=True)

    @effect(repeat_interval=0.05)
    def _add_electric(self):
        """Electric storm — crackling sparks and blue-white lightning flashes."""
        if not self.is_alive() or not self.node.exists():
            return
        torso = self.node.torso_position
        vel = self.node.velocity

        # Electric spark burst
        bs.emitfx(
            position=torso,
            velocity=(vel[0] + random.uniform(-3, 3), vel[1] + random.uniform(-1, 3), vel[2] + random.uniform(-3, 3)),
            count=random.randint(5, 12),
            scale=random.uniform(0.2, 0.5),
            spread=0.5,
            chunk_type='spark',
        )
        # Electric distortion
        if random.random() < 0.2:
            bs.emitfx(position=torso, spread=0.6, emit_type='distortion')

        # Pulsing electric light
        if not hasattr(self, '_elec_light') or not self._elec_light.exists():
            self._elec_light = bs.newnode(
                'light', owner=self.node,
                attrs={'color': (0.5, 0.8, 1.0), 'height_attenuated': False,
                       'radius': 0.6, 'intensity': 0.3},
            )
            self.node.connectattr('position', self._elec_light, 'position')
        # Random flicker
        self._elec_light.intensity = random.uniform(0.1, 0.8)
        self._elec_light.color = (
            random.uniform(0.3, 0.7),
            random.uniform(0.7, 1.0),
            1.0,
        )

    @effect(repeat_interval=0.02)
    def _add_galaxy(self):
        """Galaxy orbit — tiny star nodes spiral around player in 3D rings."""
        if not hasattr(self, '_galaxy_nodes'):
            self._galaxy_nodes = []
        if not hasattr(self, '_galaxy_angle'):
            self._galaxy_angle = 0.0

        if not self.is_alive() or not self.node.exists():
            for n, l in getattr(self, '_galaxy_nodes', []):
                if n.exists(): n.delete()
                if l.exists(): l.delete()
            self._galaxy_nodes = []
            return

        STAR_COUNT = 8
        if len(self._galaxy_nodes) == 0:
            ghost = self._build_ghost_material()
            textures = ['aliColor', 'eggTex3', 'bombStickyColor', 'agentColor']
            for i in range(STAR_COUNT):
                n = bs.newnode('prop', owner=self.node, attrs={
                    'body': 'sphere',
                    'mesh': bs.getmesh('flash'),
                    'color_texture': bs.gettexture(textures[i % len(textures)]),
                    'mesh_scale': 0.12,
                    'body_scale': 0.0,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.0,
                    'materials': ([ghost] if ghost else []),
                })
                l = bs.newnode('light', owner=n, attrs={
                    'intensity': 0.3, 'radius': 0.03,
                    'color': (random.random(), random.random(), random.random()),
                    'volume_intensity_scale': 0.5,
                })
                n.connectattr('position', l, 'position')
                self._galaxy_nodes.append((n, l))

        self._galaxy_angle += 0.07
        t = bs.time()
        torso = self.node.torso_position
        for i, (n, l) in enumerate(self._galaxy_nodes):
            # Two interlocked rings at different tilts
            ring = i % 2
            angle = self._galaxy_angle + (i * math.pi * 2 / STAR_COUNT)
            radius = 0.75 + ring * 0.2
            tilt = math.pi / 4 * (1 if ring == 0 else -1)
            x = radius * math.cos(angle)
            y = radius * math.sin(angle) * math.sin(tilt)
            z = radius * math.sin(angle) * math.cos(tilt)
            try:
                n.position = (torso[0] + x, torso[1] + 0.5 + y, torso[2] + z)
                n.velocity = (0, 0, 0)
            except Exception:
                pass
            hue = (t * 0.15 + i * 0.13) % 1.0
            l.color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            l.intensity = 0.25 + 0.15 * math.sin(t * 4 + i)

    @effect(repeat_interval=0.07)
    def _add_toxiccloud(self):
        """Toxic slime cloud — green poison bubbles and dripping slime."""
        if not self.is_alive() or not self.node.exists():
            return
        pos = self.node.position
        torso = self.node.torso_position
        vel = self.node.velocity

        # Slime chunks floating around
        bs.emitfx(
            position=torso,
            velocity=(vel[0] * 0.2 + random.uniform(-1, 1),
                      vel[1] * 0.2 + random.uniform(0.5, 2),
                      vel[2] * 0.2 + random.uniform(-1, 1)),
            count=random.randint(2, 5),
            scale=random.uniform(0.3, 0.8),
            spread=0.35,
            chunk_type='slime',
        )
        # Dripping slime on ground
        bs.emitfx(
            position=pos,
            velocity=(0, 0, 0),
            count=random.randint(1, 3),
            scale=random.uniform(0.2, 0.5),
            spread=0.2,
            chunk_type='slime',
            emit_type='stickers',
        )
        # Toxic smoke
        if random.random() < 0.3:
            bs.emitfx(
                position=torso,
                velocity=(0, 1, 0),
                count=2,
                emit_type='tendrils',
                tendril_type='thin_smoke',
            )
        # Toxic green light
        if not hasattr(self, '_toxic_light') or not self._toxic_light.exists():
            self._toxic_light = bs.newnode(
                'light', owner=self.node,
                attrs={'color': (0.2, 1.0, 0.1), 'height_attenuated': False,
                       'radius': 0.55, 'intensity': 0.0},
            )
            self.node.connectattr('position', self._toxic_light, 'position')
            bs.animate(self._toxic_light, 'intensity', {0: 0.1, 0.5: 0.35, 1.0: 0.1}, loop=True)

    @effect(repeat_interval=0.02)
    def _add_aurora(self):
        """Aurora borealis — layered colored rings above the player's head."""
        if not hasattr(self, '_aurora_nodes'):
            self._aurora_nodes = []
        if not hasattr(self, '_aurora_tick'):
            self._aurora_tick = 0

        if not self.is_alive() or not self.node.exists():
            for loc in getattr(self, '_aurora_nodes', []):
                if loc.exists(): loc.delete()
            self._aurora_nodes = []
            return

        if len(self._aurora_nodes) == 0:
            for i in range(4):
                loc = bs.newnode('locator', owner=self.node, attrs={
                    'shape': 'circleOutline',
                    'color': (0.0, 1.0, 0.5),
                    'opacity': 0.8,
                    'draw_beauty': True,
                    'additive': True,
                })
                self._aurora_nodes.append(loc)
            if not hasattr(self, '_aurora_light') or not self._aurora_light.exists():
                self._aurora_light = bs.newnode(
                    'light', owner=self.node,
                    attrs={'color': (0.0, 1.0, 0.5), 'height_attenuated': False,
                           'radius': 0.6, 'intensity': 0.18},
                )
                self.node.connectattr('position', self._aurora_light, 'position')

        self._aurora_tick += 1
        t = bs.time()
        torso = self.node.torso_position

        for i, loc in enumerate(self._aurora_nodes):
            phase = i * (math.pi / 2)
            y_off = 0.85 + i * 0.28 + 0.06 * math.sin(t * 2.0 + phase)
            size = 0.55 + i * 0.22 + 0.08 * math.sin(t * 1.5 + phase)
            # Cycle through aurora colors: green → cyan → blue → purple
            hue = (0.33 + i * 0.1 + t * 0.04) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 0.85, 1.0)
            loc.position = (torso[0], torso[1] + y_off, torso[2])
            loc.color = (r, g, b)
            loc.size = [size]
            loc.opacity = 0.6 + 0.2 * math.sin(t * 3 + phase)

        if self._aurora_tick % 8 == 0:
            bs.emitfx(
                position=(torso[0], torso[1] + 1.5, torso[2]),
                velocity=(0, 0.3, 0),
                count=2, scale=0.15, spread=0.1,
                emit_type='tendrils', tendril_type='thin_smoke',
            )

    @effect(repeat_interval=0.04)
    def _add_bloodmoon(self):
        """Blood moon — dark crimson drips, red mist and ominous pulsing light."""
        if not self.is_alive() or not self.node.exists():
            return
        torso = self.node.torso_position
        pos = self.node.position
        vel = self.node.velocity

        # Blood drips downward
        bs.emitfx(
            position=torso,
            velocity=(vel[0] * 0.1 + random.uniform(-0.5, 0.5),
                      vel[1] * 0.1 - random.uniform(0.5, 2.0),
                      vel[2] * 0.1 + random.uniform(-0.5, 0.5)),
            count=random.randint(2, 5),
            scale=random.uniform(0.3, 0.7),
            spread=0.2,
            chunk_type='slime',
        )
        # Blood stain on ground
        if random.random() < 0.3:
            bs.emitfx(
                position=pos,
                count=2, scale=0.4, spread=0.15,
                chunk_type='slime', emit_type='stickers',
            )
        # Dark red mist
        if random.random() < 0.2:
            bs.emitfx(
                position=torso,
                velocity=(0, 0.4, 0),
                count=1, emit_type='tendrils', tendril_type='smoke',
            )
        # Pulsing blood light
        if not hasattr(self, '_bloodmoon_light') or not self._bloodmoon_light.exists():
            self._bloodmoon_light = bs.newnode(
                'light', owner=self.node,
                attrs={'color': (1.0, 0.0, 0.05), 'height_attenuated': False,
                       'radius': 0.65, 'intensity': 0.0},
            )
            self.node.connectattr('position', self._bloodmoon_light, 'position')
            bs.animate(self._bloodmoon_light, 'intensity',
                       {0: 0.15, 0.6: 0.55, 1.2: 0.15}, loop=True)

    @effect(repeat_interval=0.02)
    def _add_demonwings(self):
        """Dark demon wings — large sweeping dark wings behind the player."""
        if not hasattr(self, '_demonwings_nodes'):
            self._demonwings_nodes = []
        if not hasattr(self, '_demonwings_tick'):
            self._demonwings_tick = 0

        if not self.is_alive() or not self.node.exists():
            for n, l, _, _ in getattr(self, '_demonwings_nodes', []):
                if n.exists(): n.delete()
                if l.exists(): l.delete()
            self._demonwings_nodes = []
            return

        if len(self._demonwings_nodes) == 0:
            ghost = self._build_ghost_material()
            for side in (-1, 1):
                # Outer wing tip
                for seg in range(2):
                    n = bs.newnode('prop', owner=self.node, attrs={
                        'body': 'sphere',
                        'mesh': bs.getmesh('shield'),
                        'color_texture': bs.gettexture('powerupCurse'),
                        'mesh_scale': 0.55 - seg * 0.15,
                        'body_scale': 0.0,
                        'shadow_size': 0.0,
                        'gravity_scale': 0.0,
                        'materials': ([ghost] if ghost else []),
                    })
                    l = bs.newnode('light', owner=n, attrs={
                        'intensity': 0.3,
                        'color': (0.7, 0.0, 0.0),
                        'radius': 0.04,
                        'volume_intensity_scale': 0.5,
                    })
                    n.connectattr('position', l, 'position')
                    self._demonwings_nodes.append((n, l, side, seg))

                    def _freeze(nn=n):
                        try:
                            if not self.is_alive() or not self.node.exists() or not nn.exists():
                                return
                            nn.velocity = (0, 0, 0)
                            bs.timer(0.08, _freeze)
                        except Exception:
                            pass
                    bs.timer(0.08, _freeze)

        self._demonwings_tick += 1
        t = bs.time()
        torso = self.node.torso_position

        for n, l, side, seg in self._demonwings_nodes:
            flap = math.sin(t * 5.0 + seg * 0.5)
            spread_x = side * (0.55 + seg * 0.45 + 0.2 * abs(flap))
            pos = (
                torso[0] + spread_x,
                torso[1] + 0.35 - seg * 0.2 + 0.08 * flap,
                torso[2] - 0.4 - seg * 0.25,
            )
            try:
                n.position = pos
                n.velocity = (0, 0, 0)
            except Exception:
                n.position = pos
            hue = (0.95 + 0.05 * math.sin(t * 2)) % 1.0
            l.color = colorsys.hsv_to_rgb(hue, 1.0, 0.8)
            l.intensity = 0.2 + 0.15 * abs(flap)

        # Emit dark sparks from wing tips on flap
        if self._demonwings_tick % 12 == 0:
            for side in (-1, 1):
                bs.emitfx(
                    position=(torso[0] + side * 1.1, torso[1] + 0.2, torso[2] - 0.7),
                    velocity=(side * 0.5, -0.5, 0),
                    count=3, scale=0.3, spread=0.2, chunk_type='spark',
                )


def apply() -> None:
    bascenev1lib.actor.playerspaz.PlayerSpaz = NewPlayerSpaz
