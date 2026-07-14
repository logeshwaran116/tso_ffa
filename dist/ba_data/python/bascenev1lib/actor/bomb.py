# Released under the MIT License. See LICENSE for details.
#
"""Various classes for bombs, mines, tnt, etc."""

# FIXME
# pylint: disable=too-many-lines

from __future__ import annotations

import random
from typing import TYPE_CHECKING, override

import babase
import bascenev1 as bs

from bascenev1lib.gameutils import SharedObjects

if TYPE_CHECKING:
    from typing import Any, Sequence, Callable

# --- BLAST EFFECT TEST ---

_BLAST_COLORS = {
    "electric": (0.4, 0.8, 1.0), #working
    "stars": (1.0, 0.9, 0.3), #working
    "darkmagic":(0.5, 0.0, 1.0), #working
    "colorful": (1.0, 1.0, 1.0), #working
    "egg": (1.0, 0.4, 0.7), #working
    "void": (0.25, 0.25, 0.25), #needs fix
    "snow": (1.0, 1.0, 1.0), #working
    "heart": (0.0, 0.0, 1.0), #working
    "gift": (1.0, 0.0, 0.0),
    "lightning": (0.4, 0.8, 1.0),
    "skull": (1.0, 1.0, 1.0)
}


_BLAST_EFFECTS = {
    "pb-IF4OU0UkLw==": "colorful",
    "pb-IF4rUVIBMQ==": "darkmagic"
}


def _get_source_effect(source_player: bs.Player | None) -> str | None:
    try:
        if source_player is None or not source_player.exists():
            return None
        pb_id = source_player.sessionplayer.get_v1_account_id()
        return _BLAST_EFFECTS.get(pb_id)
    except Exception:
        return None

def _get_blast_color(effect: str | None) -> tuple[float, float, float] | None:
    if effect and effect in _BLAST_COLORS:
        return _BLAST_COLORS[effect]
    return None

def _emit_blast_effect(
    position: tuple[float, float, float],
    velocity: tuple[float, float, float],
    effect: str | None,
    source_player: bs.Player | None = None
) -> None:
    try:
        if not effect:
            return

        if effect == 'electric':
            _blast_electric(position, velocity)
        elif effect == 'stars':
            _blast_stars(position, velocity)
        elif effect == 'darkmagic':
            _blast_darkmagic(position, velocity)
        elif effect == 'colorful':
            _blast_colorful(position, velocity)
        elif effect == 'egg':
            _blast_egg(position, velocity)
        elif effect == 'void':
            _blast_void(position, velocity)
        elif effect == "snow":
            _blast_snow(position, velocity)
        elif effect == "heart":
            _blast_heart(position, velocity)
        elif effect == "gift":
            _blast_gift(position, velocity)
        elif effect == 'lightning':
            _blast_lightning_strike(position, velocity)
        elif effect == 'skull':
            _blast_skull(position, velocity)
        
        #if source_player is not None:
                #_shower_on_player_ref(source_player, effect)
    except Exception as e:
        print(f"[BLAST EFFECT ERROR] {e}")


def _blast_electric(
    position: tuple[float, float, float],
    velocity: tuple[float, float, float],
) -> None:
    # Initial big spark burst
    for _ in range(3):
        bs.emitfx(
            position=position,
            velocity=(
                velocity[0] + random.uniform(-4, 4),
                velocity[1] + random.uniform(-1, 4),
                velocity[2] + random.uniform(-4, 4),
            ),
            count=random.randint(8, 15),
            scale=random.uniform(0.3, 0.6),
            spread=0.8,
            chunk_type='spark',
        )
    bs.emitfx(position=position, spread=1.0, emit_type='distortion')

    elight = bs.newnode(
        'light',
        attrs={
            'position': position,
            'color': (0.4, 0.8, 1.0),
            'radius': 2.5,
            'intensity': 2.0,
            'height_attenuated': False,
        },
    )
    bs.animate(elight, 'intensity', {
        0.0: 2.0, 0.05: 0.5, 0.1: 1.8, 0.15: 0.3, 0.2: 0.0,
    })
    bs.timer(0.25, elight.delete)

    crackle_light = bs.newnode(
        'light',
        attrs={
            'position': position,
            'color': (0.3, 0.7, 1.0),
            'radius': 0.6,
            'intensity': 0.0,
            'height_attenuated': False,
        },
    )

    def _crackle(elapsed: float = 0.0) -> None:
        if elapsed >= 1:
            crackle_light.delete()
            return
        bs.emitfx(
            position=position,
            velocity=(random.uniform(-2, 2), random.uniform(0, 2), random.uniform(-2, 2)),
            count=random.randint(3, 8),
            scale=random.uniform(0.2, 0.4),
            spread=0.4,
            chunk_type='spark',
        )
        if random.random() < 0.3:
            bs.emitfx(position=position, spread=0.5, emit_type='distortion')
        crackle_light.intensity = random.uniform(0.0, 0.6)
        crackle_light.color = (
            random.uniform(0.2, 0.5),
            random.uniform(0.6, 1.0),
            1.0,
        )
        bs.timer(0.08, babase.Call(_crackle, elapsed + 0.08))

    _crackle()

def _blast_stars(
    position: tuple[float, float, float],
    velocity: tuple[float, float, float],
) -> None:
    texs = ['bombStickyColor', 'aliColor', 'aliColorMask', 'eggTex3']
    mesh = bs.getmesh('flash')

    def _spawn_stars(count: int, speed: float) -> None:
        for _ in range(count):
            m = speed
            pos = (
                position[0] + random.uniform(-0.3, 0.3),
                position[1] + random.uniform(-0.3, 0.3),
                position[2] + random.uniform(-0.3, 0.3),
            )
            vel = (
                velocity[0] + random.uniform(-m, m),
                velocity[1] + random.uniform(1.0, m * 2),
                velocity[2] + random.uniform(-m, m),
            )
            tex = bs.gettexture(random.choice(texs))
            node = bs.newnode('prop',
                attrs={
                    'body': 'sphere',
                    'position': pos,
                    'velocity': vel,
                    'mesh': mesh,
                    'mesh_scale': random.uniform(0.08, 0.18),
                    'body_scale': 0.0,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.4,
                    'color_texture': tex,
                    'reflection': 'soft',
                    'reflection_scale': [1.5],
                })
            light = bs.newnode('light',
                owner=node,
                attrs={
                    'intensity': 1,
                    'volume_intensity_scale': 0.5,
                    'color': (
                        random.uniform(0.5, 1.5),
                        random.uniform(0.5, 1.5),
                        random.uniform(0.5, 1.5),
                    ),
                    'radius': 0.035,
                })
            node.connectattr('position', light, 'position')
            lifetime = random.uniform(0.3, 0.6)
            bs.timer(lifetime, node.delete)
            bs.timer(lifetime, light.delete)

    # Initial big burst
    _spawn_stars(count=15, speed=3.0)

    # Golden flash light
    slight = bs.newnode(
        'light',
        attrs={
            'position': position,
            'color': (1.0, 0.9, 0.2),
            'radius': 1,
            'intensity': 0.8,
            'height_attenuated': False,
        },
    )
    bs.animate(slight, 'intensity', {
        0.0: 0.8, 0.1: 0.3, 0.2: 0.6, 0.35: 0.1, 0.5: 0.0,
    })
    bs.timer(0.6, slight.delete)


def _blast_darkmagic(
    position: tuple[float, float, float],
    velocity: tuple[float, float, float],
) -> None:
    mesh = bs.getmesh('impactBomb')
    tex = bs.gettexture('impactBombColor')

    def _spawn_darkmagic(count: int, speed: float) -> None:
        for _ in range(count):
            m = speed
            pos = (
                position[0] + random.uniform(-0.3, 0.3),
                position[1] + random.uniform(-0.3, 0.3),
                position[2] + random.uniform(-0.3, 0.3),
            )
            vel = (
                velocity[0] + random.uniform(-m, m),
                velocity[1] + random.uniform(5.0, 15.0),  # shoot upward like original
                velocity[2] + random.uniform(-m, m),
            )
            node = bs.newnode('prop',
                attrs={
                    'body': 'sphere',
                    'position': pos,
                    'velocity': vel,
                    'mesh': mesh,
                    'mesh_scale': random.uniform(0.3, 0.5),  # was 0.08-0.18, too small
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
            lifetime = random.uniform(0.3, 0.6)
            bs.timer(lifetime, node.delete)
            bs.timer(lifetime, light.delete)

    # Initial burst
    _spawn_darkmagic(count=15, speed=3.0)

    # Purple flash light
    slight = bs.newnode(
        'light',
        attrs={
            'position': position,
            'color': (0.5, 0.0, 1.0),
            'radius': 1,
            'intensity': 0.8,
            'height_attenuated': False,
        },
    )
    bs.animate(slight, 'intensity', {
        0.0: 0.8, 0.1: 0.3, 0.2: 0.6, 0.35: 0.1, 0.5: 0.0,
    })
    bs.timer(0.6, slight.delete)



def _blast_snow(
    position: tuple[float, float, float],
    velocity: tuple[float, float, float],
) -> None:
    mesh = bs.getmesh('snow')
    tex = bs.gettexture('white')

    def _spawn_snow(count: int, speed: float) -> None:
        for _ in range(count):
            m = speed
            pos = (
                position[0] + random.uniform(-0.3, 0.3),
                position[1] + random.uniform(-0.3, 0.3),
                position[2] + random.uniform(-0.3, 0.3),
            )
            vel = (
                velocity[0] + random.uniform(-m, m),
                velocity[1] + random.uniform(5.0, 15.0),  # shoot upward like original
                velocity[2] + random.uniform(-m, m),
            )
            node = bs.newnode('prop',
                attrs={
                    'body': 'sphere',
                    'position': pos,
                    'velocity': vel,
                    'mesh': mesh,
                    'mesh_scale': random.uniform(0.08, 0.2),  # was 0.08-0.18, too small
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
                    'color': (1.0, 1.0, 1.0),
                    'radius': 0.035,
                })
            node.connectattr('position', light, 'position')
            lifetime = random.uniform(0.3, 0.6)
            bs.timer(lifetime, node.delete)
            bs.timer(lifetime, light.delete)

    # Initial burst
    _spawn_snow(count=20, speed=3.0)

    # Purple flash light
    slight = bs.newnode(
        'light',
        attrs={
            'position': position,
            'color': (1.0, 1.0, 1.0),
            'radius': 1,
            'intensity': 0.8,
            'height_attenuated': False,
        },
    )
    bs.animate(slight, 'intensity', {
        0.0: 0.8, 0.1: 0.3, 0.2: 0.6, 0.35: 0.1, 0.5: 0.0,
    })
    bs.timer(0.6, slight.delete)

def _blast_void(
    position: tuple[float, float, float],
    velocity: tuple[float, float, float],
) -> None:
    # Multiple distortion pulses — void/black hole feel
    for i in range(4):
        bs.timer(i * 0.05, lambda: bs.emitfx(
            position=position,
            spread=random.uniform(0.5, 1.5),
            emit_type='distortion',
        ))

    # Dark void prop pieces — black rocks flying out
    mesh = bs.getmesh('heartOpaque')
    tex = bs.gettexture('heart')  # dark texture

    for _ in range(12):
        m = 3.0
        pos = (
            position[0] + random.uniform(-0.2, 0.2),
            position[1] + random.uniform(-0.2, 0.2),
            position[2] + random.uniform(-0.2, 0.2),
        )
        vel = (
            velocity[0] + random.uniform(-m, m),
            velocity[1] + random.uniform(1.0, m * 2),
            velocity[2] + random.uniform(-m, m),
        )
        node = bs.newnode('prop',
            attrs={
                'body': 'sphere',
                'position': pos,
                'velocity': vel,
                'mesh': mesh,
                'mesh_scale': random.uniform(0.1, 0.25),
                'body_scale': 0.0,
                'shadow_size': 0.0,
                'gravity_scale': 0.3,
                'color_texture': tex,
                'reflection': 'soft',
                'reflection_scale': [0.0],
            })
        # Dark purple/void light on each piece
        light = bs.newnode('light',
            owner=node,
            attrs={
                'intensity': 0.5,
                'volume_intensity_scale': 0.3,
                'color': (0.1, 0.0, 0.2),  # very dark purple
                'radius': 0.04,
            })
        node.connectattr('position', light, 'position')
        lifetime = random.uniform(0.3, 0.6)
        bs.timer(lifetime, node.delete)
        bs.timer(lifetime, light.delete)

    # Dark void flash — sucks light away
    elight = bs.newnode(
        'light',
        attrs={
            'position': position,
            'color': (0.05, 0.0, 0.1),  # near black purple
            'radius': 2.0,
            'intensity': 1.5,
            'height_attenuated': False,
        },
    )
    bs.animate(elight, 'intensity', {
        0.0: 1.5, 0.05: 0.3, 0.1: 1.2, 0.15: 0.2, 0.25: 0.0,
    })
    bs.timer(0.3, elight.delete)


def _blast_colorful(
    position: tuple[float, float, float],
    velocity: tuple[float, float, float],
) -> None:
    import colorsys
    # Different textures give different colors visually
    texs = [
        'bombStickyColor',
        'impactBombColor',
        'landMineLitColor',
        'eggTex3',
    ]
    mesh = bs.getmesh('bomb')

    def _spawn_colorful(count: int, speed: float) -> None:
        for _ in range(count):
            m = speed
            pos = (
                position[0] + random.uniform(-0.3, 0.3),
                position[1] + random.uniform(-0.3, 0.3),
                position[2] + random.uniform(-0.3, 0.3),
            )
            vel = (
                velocity[0] + random.uniform(-m, m),
                velocity[1] + random.uniform(1.0, m * 2),
                velocity[2] + random.uniform(-m, m),
            )
            tex = bs.gettexture(random.choice(texs))
            node = bs.newnode('prop',
                attrs={
                    'body': 'sphere',
                    'position': pos,
                    'velocity': vel,
                    'mesh': mesh,
                    'mesh_scale': random.uniform(0.15, 0.35),
                    'body_scale': 0.0,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.4,
                    'color_texture': tex,
                    'reflection': 'soft',
                    'reflection_scale': [1.5],
                })

            # Bright colored light per prop — this is what gives color
            h = random.random()
            r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
            light = bs.newnode('light',
                owner=node,
                attrs={
                    'intensity': 1.5,
                    'volume_intensity_scale': 1.0,
                    'color': (r, g, b),
                    'radius': 0.08,
                })
            node.connectattr('position', light, 'position')
            lifetime = random.uniform(0.3, 0.7)
            bs.timer(lifetime, node.delete)
            bs.timer(lifetime, light.delete)

    _spawn_colorful(count=15, speed=3)

    # Colorful locator rings on ground
    for _ in range(6):
        h = random.random()
        r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
        color = (r, g, b)
        jitter = (random.uniform(-0.4, 0.4), 0.0, random.uniform(-0.4, 0.4))
        loc = bs.newnode('locator',
            attrs={
                'position': (
                    position[0] + jitter[0],
                    position[1] + jitter[1],
                    position[2] + jitter[2],
                ),
                'shape': 'circle',
                'color': babase.safecolor(color),
                'size': [random.uniform(0.2, 0.6)],
                'draw_beauty': False,
                'additive': True,
            })
        h2 = random.random()
        c2 = colorsys.hsv_to_rgb(h2, 1.0, 1.0)
        h3 = random.random()
        c3 = colorsys.hsv_to_rgb(h3, 1.0, 1.0)
        bs.animate_array(loc, 'color', 3, {0.0: color, 0.3: c2, 0.6: c3})
        bs.animate(loc, 'opacity', {0.0: 1.0, 0.8: 0.0})
        bs.timer(0.8, loc.delete)

    # White flash — lets the colored lights pop
    slight = bs.newnode(
        'light',
        attrs={
            'position': position,
            'color': (1.0, 1.0, 1.0),
            'radius': 1,
            'intensity': 0.8,
            'height_attenuated': False,
        },
    )
    bs.animate(slight, 'intensity', {
        0.0: 0.8, 0.1: 0.3, 0.2: 0.6, 0.35: 0.1, 0.5: 0.0,
    })
    bs.timer(0.6, slight.delete)


def _blast_egg(
    position: tuple[float, float, float],
    velocity: tuple[float, float, float],
) -> None:
    mesh = bs.getmesh('egg')
    texs = [
        bs.gettexture('eggTex1'),
        bs.gettexture('eggTex2'),
        bs.gettexture('eggTex3'),
    ]

    def _spawn_eggs(count: int, speed: float) -> None:
        for _ in range(count):
            m = speed
            pos = (
                position[0] + random.uniform(-0.3, 0.3),
                position[1] + random.uniform(-0.1, 0.3),
                position[2] + random.uniform(-0.3, 0.3),
            )
            vel = (
                velocity[0] + random.uniform(-m, m),
                velocity[1] + random.uniform(2.0, m * 2),
                velocity[2] + random.uniform(-m, m),
            )
            node = bs.newnode('prop',
                attrs={
                    'body': 'capsule',
                    'position': pos,
                    'velocity': vel,
                    'mesh': mesh,
                    'mesh_scale': random.uniform(0.15, 0.35),
                    'body_scale': 0.0,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.5,
                    'color_texture': random.choice(texs),
                    'reflection': 'soft',
                    'reflection_scale': [0.2],
                })
            light = bs.newnode('light',
                owner=node,
                attrs={
                    'intensity': 1,
                    'volume_intensity_scale': 0.5,
                    'color': (1.0, 0.4, 0.7),  # pink
                    'radius': 0.03,
                })
            node.connectattr('position', light, 'position')
            lifetime = random.uniform(0.3, 0.7)
            bs.timer(lifetime, node.delete)
            bs.timer(lifetime, light.delete)

    _spawn_eggs(count=15, speed=3.0)

    # Pink flash light
    slight = bs.newnode(
        'light',
        attrs={
            'position': position,
            'color': (1.0, 0.4, 0.7),  # pink
            'radius': 1.0,
            'intensity': 0.8,
            'height_attenuated': False,
        },
    )
    bs.animate(slight, 'intensity', {
        0.0: 0.8, 0.1: 0.3, 0.2: 0.6, 0.35: 0.1, 0.5: 0.0,
    })
    bs.timer(0.6, slight.delete)


def _blast_heart(
    position: tuple[float, float, float],
    velocity: tuple[float, float, float],
) -> None:
    mesh = bs.getmesh('heartOpaque')
    tex = bs.gettexture('heart')

    def _spawn_heart(count: int, speed: float) -> None:
        for _ in range(count):
            m = speed
            pos = (
                position[0] + random.uniform(-0.3, 0.3),
                position[1] + random.uniform(-0.3, 0.3),
                position[2] + random.uniform(-0.3, 0.3),
            )
            vel = (
                velocity[0] + random.uniform(-m, m),
                velocity[1] + random.uniform(1.0, m * 2), 
                velocity[2] + random.uniform(-m, m),
            )
            node = bs.newnode('prop',
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
                    'color': _BLAST_COLORS.get('heart', (1.0, 0.0, 0.0)),
                    'radius': 0.035,
                })
            node.connectattr('position', light, 'position')
            lifetime = random.uniform(0.3, 0.6)
            bs.timer(lifetime, node.delete)
            bs.timer(lifetime, light.delete)

    # Initial burst
    _spawn_heart(count=30, speed=3.0)

    # Purple flash light
    slight = bs.newnode(
        'light',
        attrs={
            'position': position,
            'color': _BLAST_COLORS.get('heart', (1.0, 0.0, 0.0)),
            'radius': 1,
            'intensity': 0.8,
            'height_attenuated': False,
        },
    )
    bs.animate(slight, 'intensity', {
        0.0: 0.8, 0.1: 0.3, 0.2: 0.6, 0.35: 0.1, 0.5: 0.0,
    })
    bs.timer(0.6, slight.delete)

def _blast_gift(    
    position: tuple[float, float, float],
    velocity: tuple[float, float, float],
) -> None:
    mesh = bs.getmesh('giftBox')
    tex = bs.gettexture('eggTex2')

    def _spawn_gift(count: int, speed: float) -> None:
        for _ in range(count):
            m = speed
            pos = (
                position[0] + random.uniform(-0.3, 0.3),
                position[1] + random.uniform(-0.3, 0.3),
                position[2] + random.uniform(-0.3, 0.3),
            )
            vel = (
                velocity[0] + random.uniform(-m, m),
                velocity[1] + random.uniform(1.0, m * 2), 
                velocity[2] + random.uniform(-m, m),
            )
            node = bs.newnode('prop',
                attrs={
                    'body': 'sphere',
                    'position': pos,
                    'velocity': vel,
                    'mesh': mesh,
                    'mesh_scale': 0.2,
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
                    'color': _BLAST_COLORS.get('gift', (1.0, 0.0, 0.0)),
                    'radius': 0.035,
                })
            node.connectattr('position', light, 'position')
            lifetime = random.uniform(0.3, 0.6)
            bs.timer(lifetime, node.delete)
            bs.timer(lifetime, light.delete)

    # Initial burst
    _spawn_gift(count=10, speed=3.0)

    # Purple flash light
    slight = bs.newnode(
        'light',
        attrs={
            'position': position,
            'color': _BLAST_COLORS.get('gift', (1.0, 0.0, 0.0)),
            'radius': 1,
            'intensity': 0.8,
            'height_attenuated': False,
        },
    )
    bs.animate(slight, 'intensity', {
        0.0: 0.8, 0.1: 0.3, 0.2: 0.6, 0.35: 0.1, 0.5: 0.0,
    })
    bs.timer(0.6, slight.delete)

def _blast_lightning_strike(
    position: tuple[float, float, float],
    velocity: tuple[float, float, float],
) -> None:
    """A lightning bolt strikes down from above to the blast point."""

    strike_height = 8.0  # how high above blast the bolt starts
    segments = 18        # number of shield nodes forming the bolt
    duration = 1.0       # how long bolt stays visible

    # Top of bolt to blast point
    top_y = position[1] + strike_height
    bot_y = position[1]

    # Spawn shield nodes vertically forming the bolt
    nodes = []
    for i in range(segments):
        t = i / (segments - 1)  # 0.0 to 1.0
        y = top_y - t * (top_y - bot_y)
        # Slight zigzag for natural lightning look
        jitter_x = random.uniform(-0.08, 0.08) if 0 < i < segments - 1 else 0
        jitter_z = random.uniform(-0.08, 0.08) if 0 < i < segments - 1 else 0
        node = bs.newnode(
            'shield',
            attrs={
                'position': (
                    position[0] + jitter_x,
                    y,
                    position[2] + jitter_z,
                ),
                'color': (0.4, 0.8, 1.0),  # blue-white electric
                'radius': 0.18,
                'hurt': 0,
            },
        )
        nodes.append(node)

    # Bright electric light at blast point
    strike_light = bs.newnode(
        'light',
        attrs={
            'position': position,
            'color': (0.4, 0.8, 1.0),
            'radius': 2.0,
            'intensity': 3.0,
            'height_attenuated': False,
        },
    )
    bs.animate(strike_light, 'intensity', {
        0.0: 3.0,
        0.05: 0.5,
        0.1: 2.5,
        0.2: 1.0,
        duration: 0.0,
    })

    # Flicker the bolt — delete and recreate opacity effect via timer
    def _flicker(elapsed: float = 0.0) -> None:
        if elapsed >= duration:
            for n in nodes:
                try:
                    n.delete()
                except Exception:
                    pass
            strike_light.delete()
            return
        # Randomly hide/show all segments for flicker effect
        visible = random.random() > 0.3
        for n in nodes:
            try:
                n.color = (
                    random.uniform(0.3, 0.5),
                    random.uniform(0.7, 1.0),
                    1.0,
                ) if visible else (0.0, 0.0, 0.0)
            except Exception:
                pass
        bs.timer(0.05, babase.Call(_flicker, elapsed + 0.05))

    _flicker()

    # Electric sparks at ground hit point
    bs.emitfx(
        position=position,
        velocity=(0, 1, 0),
        count=20,
        scale=0.5,
        spread=0.5,
        chunk_type='spark',
    )
    bs.emitfx(position=position, spread=0.8, emit_type='distortion')

def _blast_skull(    
    position: tuple[float, float, float],
    velocity: tuple[float, float, float],
) -> None:
    mesh = bs.getmesh('bonesHead')
    tex = bs.gettexture('bonesColor')

    def _spawn_skull(count: int, speed: float) -> None:
        for _ in range(count):
            m = speed
            pos = (
                position[0] + random.uniform(-0.3, 0.3),
                position[1] + random.uniform(-0.3, 0.3),
                position[2] + random.uniform(-0.3, 0.3),
            )
            vel = (
                velocity[0] + random.uniform(-m, m),
                velocity[1] + random.uniform(1.0, m * 2), 
                velocity[2] + random.uniform(-m, m),
            )
            node = bs.newnode('prop',
                attrs={
                    'body': 'sphere',
                    'position': pos,
                    'velocity': vel,
                    'mesh': mesh,
                    'mesh_scale': 0.8,
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
                    'color': _BLAST_COLORS.get('skull', (1.0, 0.0, 0.0)),
                    'radius': 0.035,
                })
            node.connectattr('position', light, 'position')
            lifetime = random.uniform(0.3, 0.6)
            bs.timer(lifetime, node.delete)
            bs.timer(lifetime, light.delete)

    # Initial burst
    _spawn_skull(count=10, speed=3.0)

    # Purple flash light
    slight = bs.newnode(
        'light',
        attrs={
            'position': position,
            'color': _BLAST_COLORS.get('skull', (1.0, 0.0, 0.0)),
            'radius': 1,
            'intensity': 0.8,
            'height_attenuated': False,
        },
    )
    bs.animate(slight, 'intensity', {
        0.0: 0.8, 0.1: 0.3, 0.2: 0.6, 0.35: 0.1, 0.5: 0.0,
    })
    bs.timer(0.6, slight.delete)


def _shower_on_player(
    target_node: bs.Node,
    effect: str,
    duration: float = 2.0,
) -> None:
    """Spawn props/particles around a player node for duration seconds."""

    def _tick(elapsed: float = 0.0) -> None:
        if elapsed >= duration:
            return
        try:
            if not target_node.exists():
                return
            pos = target_node.position

            if effect == 'stars':
                texs = ['bombStickyColor', 'aliColor', 'aliColorMask', 'eggTex3']
                mesh = bs.getmesh('flash')
                tex = bs.gettexture(random.choice(texs))
                node = bs.newnode('prop', attrs={
                    'body': 'sphere',
                    'position': (
                        pos[0] + random.uniform(-0.4, 0.4),
                        pos[1] + random.uniform(1.5, 1.8),
                        pos[2] + random.uniform(-0.4, 0.4),
                    ),
                    'velocity': (
                        random.uniform(-1, 1),
                        random.uniform(-2, -0.5),
                        random.uniform(-1, 1),
                    ),
                    'mesh': mesh,
                    'mesh_scale': random.uniform(0.08, 0.15),
                    'body_scale': 0.0,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.3,
                    'color_texture': tex,
                    'reflection': 'soft',
                    'reflection_scale': [1.5],
                })
                light = bs.newnode('light', owner=node, attrs={
                    'intensity': 0.4,
                    'volume_intensity_scale': 0.3,
                    'color': (1.0, 0.9, 0.3),
                    'radius': 0.03,
                })
                node.connectattr('position', light, 'position')
                bs.timer(0.4, node.delete)
                bs.timer(0.4, light.delete)

            elif effect == 'darkmagic':
                mesh = bs.getmesh('impactBomb')
                tex = bs.gettexture('impactBombColor')
                node = bs.newnode('prop', attrs={
                    'body': 'sphere',
                    'position': (
                        pos[0] + random.uniform(-0.4, 0.4),
                        pos[1] + random.uniform(0.0, 1.0),
                        pos[2] + random.uniform(-0.4, 0.4),
                    ),
                    'velocity': (
                        random.uniform(-0.5, 0.5),
                        random.uniform(3, 8),
                        random.uniform(-0.5, 0.5),
                    ),
                    'mesh': mesh,
                    'mesh_scale': random.uniform(0.2, 0.35),
                    'body_scale': 0.0,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.4,
                    'color_texture': tex,
                    'reflection': 'soft',
                    'reflection_scale': [0.0],
                })
                light = bs.newnode('light', owner=node, attrs={
                    'intensity': 0.8,
                    'volume_intensity_scale': 0.4,
                    'color': (0.5, 0.0, 1.0),
                    'radius': 0.03,
                })
                node.connectattr('position', light, 'position')
                bs.timer(0.3, node.delete)
                bs.timer(0.3, light.delete)

            elif effect == 'electric':
                bs.emitfx(
                    position=(
                        pos[0] + random.uniform(-0.3, 0.3),
                        pos[1] + random.uniform(0.0, 1.2),
                        pos[2] + random.uniform(-0.3, 0.3),
                    ),
                    velocity=(random.uniform(-1, 1), random.uniform(0, 2), random.uniform(-1, 1)),
                    count=random.randint(2, 5),
                    scale=0.3,
                    spread=0.2,
                    chunk_type='spark',
                )

            elif effect == 'colorful':
                import colorsys
                h = random.random()
                r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
                mesh = bs.getmesh('bomb')
                tex = bs.gettexture('nub')
                node = bs.newnode('prop', attrs={
                    'body': 'sphere',
                    'position': (
                        pos[0] + random.uniform(-0.4, 0.4),
                        pos[1] + random.uniform(1.5, 1.8),
                        pos[2] + random.uniform(-0.4, 0.4),
                    ),
                    'velocity': (
                        random.uniform(-1, 1),
                        random.uniform(-2, -0.5),
                        random.uniform(-1, 1),
                    ),
                    'mesh': mesh,
                    'mesh_scale': random.uniform(0.1, 0.2),
                    'body_scale': 0.0,
                    'shadow_size': 0.0,
                    'gravity_scale': 0.3,
                    'color_texture': tex,
                    'reflection': 'soft',
                    'reflection_scale': [1.5],
                })
                light = bs.newnode('light', owner=node, attrs={
                    'intensity': 1.2,
                    'volume_intensity_scale': 0.8,
                    'color': (r, g, b),
                    'radius': 0.04,
                })
                node.connectattr('position', light, 'position')
                bs.timer(0.4, node.delete)
                bs.timer(0.4, light.delete)

        except Exception:
            pass

        bs.timer(0.15, babase.Call(_tick, elapsed + 0.15))

    _tick()


def _shower_on_player_ref(
    source_player: bs.Player,
    effect: str,
    duration: float = 2.0,
) -> None:
    try:
        if not source_player.exists():
            return
        actor = source_player.actor
        if actor is None or not actor.node or not actor.node.exists():
            return
        target_node = actor.node
        _shower_on_player(target_node, effect, duration)
    except Exception:
        pass

class BombFactory:
    """Wraps up media and other resources used by the
    :class:`~bascenev1lib.actor.bomb.Bomb` actor.

    A single instance of this is shared between all bombs and can be
    retrieved via the static :meth:`BombFactory.get()` method.
    """

    #: The mesh used for standard or ice bombs.
    bomb_mesh: bs.Mesh

    #: The mesh used for sticky-bombs.
    sticky_bomb_mesh: bs.Mesh

    #: The mesh used for impact-bombs.
    impact_bomb_mesh: bs.Mesh

    #: The mesh used for land-mines.
    land_mine_mesh: bs.Mesh

    #: The mesh used of a tnt box.
    tnt_mesh: bs.Mesh

    #: The texture used for regular bombs.
    regular_tex: bs.Texture

    #: The bs.Texture for ice bombs.
    ice_tex: bs.Texture

    #: The bs.Texture for sticky bombs.
    sticky_tex: bs.Texture

    #: The bs.Texture for impact bombs.
    impact_tex: bs.Texture

    #: The texture for impact bombs with lights lit.
    impact_lit_tex: bs.Texture

    #: The texture for land-mines.
    land_mine_tex: bs.Texture

    #: The texture for land-mines with the light lit.
    land_mine_lit_tex: bs.Texture

    #: The texture for tnt boxes.
    tnt_tex: bs.Texture

    #: The sound for the hiss sound an ice bomb makes.
    hiss_sound: bs.Sound

    #: The sound for random falling debris after an explosion.
    debris_fall_sound: bs.Sound

    #: A sound for random wood debris falling after an explosion.
    wood_debris_fall_sound: bs.Sound

    #: A tuple of sounds for explosions.
    explode_sounds: Sequence[bs.Sound]

    #: A sound of an ice bomb freezing something.
    freeze_sound: bs.Sound

    #: A sound of a burning fuse.
    fuse_sound: bs.Sound

    #: A sound for an activating impact bomb.
    activate_sound: bs.Sound

    #: A sound for an impact bomb about to explode due to time-out.
    warn_sound: bs.Sound

    #: A material applied to all bombs.
    bomb_material: bs.Material

    #: A material that generates standard bomb noises on impacts, etc.
    normal_sound_material: bs.Material

    #: A material that makes 'splat' sounds and makes collisions softer.
    sticky_material: bs.Material

    #: A material that keeps land-mines from blowing up. Applied to
    #: land-mines when they are created to allow land-mines to touch
    #: without exploding."""
    land_mine_no_explode_material: bs.Material

    #: A bs.Material applied to activated land-mines that causes them to
    #: explode on impact."""
    land_mine_blast_material: bs.Material

    #: A material applied to activated impact-bombs that causes them
    #: to explode on impact."""
    impact_blast_material: bs.Material

    blast_material: bs.Material
    #: A bs.Material applied to bomb blast geometry which triggers impact
    #: events with what it touches.

    #: A tuple of sounds for when bombs hit the ground.
    dink_sounds: Sequence[bs.Sound]

    #: The sound for a squish made by a sticky bomb hitting something.
    sticky_impact_sound: bs.Sound

    #: The sound for a rolling bomb.
    roll_sound: bs.Sound

    _STORENAME = bs.storagename()

    @classmethod
    def get(cls) -> BombFactory:
        """Create and/or return the single shared instance of this class."""
        activity = bs.getactivity()
        factory = activity.customdata.get(cls._STORENAME)
        if factory is None:
            factory = BombFactory()
            activity.customdata[cls._STORENAME] = factory
        assert isinstance(factory, BombFactory)
        return factory

    def random_explode_sound(self) -> bs.Sound:
        """Return a random explosion sound from the factory."""
        return self.explode_sounds[random.randrange(len(self.explode_sounds))]

    def __init__(self) -> None:
        """Instantiate a BombFactory.

        You shouldn't need to do this; call
        bascenev1lib.actor.bomb.get_factory() to get a shared instance.
        """
        shared = SharedObjects.get()

        self.bomb_mesh = bs.getmesh('bomb')
        self.sticky_bomb_mesh = bs.getmesh('aliHead')
        self.impact_bomb_mesh = bs.getmesh('impactBomb')
        self.land_mine_mesh = bs.getmesh('landMine')
        self.tnt_mesh = bs.getmesh('tnt')

        self.regular_tex = bs.gettexture('gameCircleIcon')
        self.ice_tex = bs.gettexture('ouyaUButton')
        self.sticky_tex = bs.gettexture('aliColor')
        self.impact_tex = bs.gettexture('egg2')
        self.impact_lit_tex = bs.gettexture('ouyaUButton')
        self.land_mine_tex = bs.gettexture('logo')
        self.land_mine_lit_tex = bs.gettexture('logo')
        self.tnt_tex = bs.gettexture('ouyaAButton')

        self.hiss_sound = bs.getsound('hiss')
        self.debris_fall_sound = bs.getsound('debrisFall')
        self.wood_debris_fall_sound = bs.getsound('woodDebrisFall')

        self.explode_sounds = (
            bs.getsound('explosion01'),
            bs.getsound('explosion02'),
            bs.getsound('explosion03'),
            bs.getsound('explosion04'),
            bs.getsound('explosion05'),
        )

        self.freeze_sound = bs.getsound('freeze')
        self.fuse_sound = bs.getsound('fuse01')
        self.activate_sound = bs.getsound('activateBeep')
        self.warn_sound = bs.getsound('warnBeep')

        # Set up our material so new bombs don't collide with objects
        # that they are initially overlapping.
        self.bomb_material = bs.Material()
        self.normal_sound_material = bs.Material()
        self.sticky_material = bs.Material()

        self.bomb_material.add_actions(
            conditions=(
                (
                    ('we_are_younger_than', 100),
                    'or',
                    ('they_are_younger_than', 100),
                ),
                'and',
                ('they_have_material', shared.object_material),
            ),
            actions=('modify_node_collision', 'collide', False),
        )

        # We want pickup materials to always hit us even if we're currently
        # not colliding with their node. (generally due to the above rule)
        self.bomb_material.add_actions(
            conditions=('they_have_material', shared.pickup_material),
            actions=('modify_part_collision', 'use_node_collide', False),
        )

        self.bomb_material.add_actions(
            actions=('modify_part_collision', 'friction', 0.3)
        )

        self.land_mine_no_explode_material = bs.Material()
        self.land_mine_blast_material = bs.Material()
        self.land_mine_blast_material.add_actions(
            conditions=(
                ('we_are_older_than', 200),
                'and',
                ('they_are_older_than', 200),
                'and',
                ('eval_colliding',),
                'and',
                (
                    (
                        'they_dont_have_material',
                        self.land_mine_no_explode_material,
                    ),
                    'and',
                    (
                        ('they_have_material', shared.object_material),
                        'or',
                        ('they_have_material', shared.player_material),
                    ),
                ),
            ),
            actions=('message', 'our_node', 'at_connect', ImpactMessage()),
        )

        self.impact_blast_material = bs.Material()
        self.impact_blast_material.add_actions(
            conditions=(
                ('we_are_older_than', 200),
                'and',
                ('they_are_older_than', 200),
                'and',
                ('eval_colliding',),
                'and',
                (
                    ('they_have_material', shared.footing_material),
                    'or',
                    ('they_have_material', shared.object_material),
                ),
            ),
            actions=('message', 'our_node', 'at_connect', ImpactMessage()),
        )

        self.blast_material = bs.Material()
        self.blast_material.add_actions(
            conditions=('they_have_material', shared.object_material),
            actions=(
                ('modify_part_collision', 'collide', True),
                ('modify_part_collision', 'physical', False),
                ('message', 'our_node', 'at_connect', ExplodeHitMessage()),
            ),
        )

        self.dink_sounds = (
            bs.getsound('bombDrop01'),
            bs.getsound('bombDrop02'),
        )
        self.sticky_impact_sound = bs.getsound('stickyImpact')
        self.roll_sound = bs.getsound('bombRoll01')

        # Collision sounds.
        self.normal_sound_material.add_actions(
            conditions=('they_have_material', shared.footing_material),
            actions=(
                ('impact_sound', self.dink_sounds, 2, 0.8),
                ('roll_sound', self.roll_sound, 3, 6),
            ),
        )

        self.sticky_material.add_actions(
            actions=(
                ('modify_part_collision', 'stiffness', 0.1),
                ('modify_part_collision', 'damping', 1.0),
            )
        )

        self.sticky_material.add_actions(
            conditions=(
                ('they_have_material', shared.player_material),
                'or',
                ('they_have_material', shared.footing_material),
            ),
            actions=('message', 'our_node', 'at_connect', SplatMessage()),
        )


class SplatMessage:
    """Tells an object to make a splat noise."""


class ExplodeMessage:
    """Tells an object to explode."""


class ImpactMessage:
    """Tell an object it touched something."""


class ArmMessage:
    """Tell an object to become armed."""


class WarnMessage:
    """Tell an object to issue a warning sound."""


class ExplodeHitMessage:
    """Tell an object it was hit by an explosion."""


class Blast(bs.Actor):
    """An explosion, as generated by a bomb or some other object.

    category: Gameplay Classes
    """

    def __init__(
        self,
        *,
        position: Sequence[float] = (0.0, 1.0, 0.0),
        velocity: Sequence[float] = (0.0, 0.0, 0.0),
        blast_radius: float = 2.0,
        blast_type: str = 'normal',
        source_player: bs.Player | None = None,
        hit_type: str = 'explosion',
        hit_subtype: str = 'normal',
    ):
        """Instantiate with given values."""

        # bah; get off my lawn!
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements

        super().__init__()

        shared = SharedObjects.get()
        factory = BombFactory.get()

        self.blast_type = blast_type
        self._source_player = source_player
        self.hit_type = hit_type
        self.hit_subtype = hit_subtype
        self.radius = blast_radius

        # Set our position a bit lower so we throw more things upward.
        rmats = (factory.blast_material, shared.attack_material)
        self.node = bs.newnode(
            'region',
            delegate=self,
            attrs={
                'position': (position[0], position[1] - 0.1, position[2]),
                'scale': (self.radius, self.radius, self.radius),
                'type': 'sphere',
                'materials': rmats,
            },
        )

        bs.timer(0.05, self.node.delete)

        # Throw in an explosion and flash.
        evel = (velocity[0], max(-1.0, velocity[1]), velocity[2])

        # Check if player has a custom effect that replaces explosion
        _custom_effect = _get_source_effect(source_player)
        
        _no_explosion = _custom_effect in ('stars', 'void','snow', 'darkmagic', 'skull', 'colorful')

        if not _no_explosion:
            explosion = bs.newnode(
                'explosion',
                attrs={
                    'position': position,
                    'velocity': evel,
                    'radius': self.radius,
                    'big': (self.blast_type == 'tnt'),
                },
            )
            if self.blast_type == 'ice':
                explosion.color = (0, 0.05, 0.4)
            else:
                pcolor = _get_blast_color(_custom_effect)
                if pcolor is not None:
                    explosion.color = pcolor
            bs.timer(1.0, explosion.delete)

        _emit_blast_effect(position, velocity, _custom_effect, source_player)

        if self.blast_type != 'ice':
            bs.emitfx(
                position=position,
                velocity=velocity,
                count=int(1.0 + random.random() * 4),
                emit_type='tendrils',
                tendril_type='thin_smoke',
            )
        bs.emitfx(
            position=position,
            velocity=velocity,
            count=int(4.0 + random.random() * 4),
            emit_type='tendrils',
            tendril_type='ice' if self.blast_type == 'ice' else 'smoke',
        )
        bs.emitfx(
            position=position,
            emit_type='distortion',
            spread=1.0 if self.blast_type == 'tnt' else 2.0,
        )

        # And emit some shrapnel.
        if self.blast_type == 'ice':

            def emit() -> None:
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=30,
                    spread=2.0,
                    scale=0.4,
                    chunk_type='ice',
                    emit_type='stickers',
                )

            # It looks better if we delay a bit.
            bs.timer(0.05, emit)

        elif self.blast_type == 'sticky':

            def emit() -> None:
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=int(4.0 + random.random() * 8),
                    spread=0.7,
                    chunk_type='slime',
                )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=int(4.0 + random.random() * 8),
                    scale=0.5,
                    spread=0.7,
                    chunk_type='slime',
                )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=15,
                    scale=0.6,
                    chunk_type='slime',
                    emit_type='stickers',
                )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=20,
                    scale=0.7,
                    chunk_type='spark',
                    emit_type='stickers',
                )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=int(6.0 + random.random() * 12),
                    scale=0.8,
                    spread=1.5,
                    chunk_type='spark',
                )

            # It looks better if we delay a bit.
            bs.timer(0.05, emit)

        elif self.blast_type == 'impact':

            def emit() -> None:
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=int(4.0 + random.random() * 8),
                    scale=0.8,
                    chunk_type='metal',
                )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=int(4.0 + random.random() * 8),
                    scale=0.4,
                    chunk_type='metal',
                )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=20,
                    scale=0.7,
                    chunk_type='spark',
                    emit_type='stickers',
                )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=int(8.0 + random.random() * 15),
                    scale=0.8,
                    spread=1.5,
                    chunk_type='spark',
                )

            # It looks better if we delay a bit.
            bs.timer(0.05, emit)

        else:  # Regular or land mine bomb shrapnel.

            def emit() -> None:
                if self.blast_type != 'tnt':
                    bs.emitfx(
                        position=position,
                        velocity=velocity,
                        count=int(4.0 + random.random() * 8),
                        chunk_type='rock',
                    )
                    bs.emitfx(
                        position=position,
                        velocity=velocity,
                        count=int(4.0 + random.random() * 8),
                        scale=0.5,
                        chunk_type='rock',
                    )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=30,
                    scale=1.0 if self.blast_type == 'tnt' else 0.7,
                    chunk_type='spark',
                    emit_type='stickers',
                )
                bs.emitfx(
                    position=position,
                    velocity=velocity,
                    count=int(18.0 + random.random() * 20),
                    scale=1.0 if self.blast_type == 'tnt' else 0.8,
                    spread=1.5,
                    chunk_type='spark',
                )

                # TNT throws splintery chunks.
                if self.blast_type == 'tnt':

                    def emit_splinters() -> None:
                        bs.emitfx(
                            position=position,
                            velocity=velocity,
                            count=int(20.0 + random.random() * 25),
                            scale=0.8,
                            spread=1.0,
                            chunk_type='splinter',
                        )

                    bs.timer(0.01, emit_splinters)

                # Every now and then do a sparky one.
                if self.blast_type == 'tnt' or random.random() < 0.1:

                    def emit_extra_sparks() -> None:
                        bs.emitfx(
                            position=position,
                            velocity=velocity,
                            count=int(10.0 + random.random() * 20),
                            scale=0.8,
                            spread=1.5,
                            chunk_type='spark',
                        )

                    bs.timer(0.02, emit_extra_sparks)

            # It looks better if we delay a bit.
            bs.timer(0.05, emit)

        if self.blast_type == 'ice':
            lcolor = (0.6, 0.6, 1.0)
        else:
            pcolor = _get_blast_color(_custom_effect)
            lcolor = pcolor if pcolor is not None else (1, 0.3, 0.1)
            

        _is_low_intensity = _custom_effect in ('stars', 'colorful', 'egg', 'darkmagic', 'snow', 'heart', 'gift', 'skull')

        light = bs.newnode(
            'light',
            attrs={
                'position': position,
                'volume_intensity_scale': 1 if _is_low_intensity else 10.0,
                'color': lcolor,
            },
        )

        scl = random.uniform(0.6, 0.9)
        scorch_radius = light_radius = self.radius
        if self.blast_type == 'tnt':
            light_radius *= 1.4
            scorch_radius *= 1.15
            scl *= 3.0

        iscale = 0.2 if _is_low_intensity else 1.6
        bs.animate(
            light,
            'intensity',
            {
                0: 2.0 * iscale,
                scl * 0.02: 0.1 * iscale,
                scl * 0.025: 0.2 * iscale,
                scl * 0.05: 17.0 * iscale,
                scl * 0.06: 5.0 * iscale,
                scl * 0.08: 4.0 * iscale,
                scl * 0.2: 0.6 * iscale,
                scl * 2.0: 0.00 * iscale,
                scl * 3.0: 0.0,
            },
        )
        bs.animate(
            light,
            'radius',
            {
                0: light_radius * 0.2,
                scl * 0.05: light_radius * 0.55,
                scl * 0.1: light_radius * 0.3,
                scl * 0.3: light_radius * 0.15,
                scl * 1.0: light_radius * 0.05,
            },
        )
        bs.timer(scl * 3.0, light.delete)

        # Make a scorch that fades over time.
        scorch = bs.newnode(
            'scorch',
            attrs={
                'position': position,
                'size': scorch_radius * 0.5,
                'big': (self.blast_type == 'tnt'),
            },
        )
        if self.blast_type == 'ice':
            scorch.color = (1, 1, 1.5)

        bs.animate(scorch, 'presence', {3.000: 1, 13.000: 0})
        bs.timer(13.0, scorch.delete)

        if self.blast_type == 'ice':
            factory.hiss_sound.play(position=light.position)

        lpos = light.position
        factory.random_explode_sound().play(position=lpos)
        factory.debris_fall_sound.play(position=lpos)

        bs.camerashake(intensity=5.0 if self.blast_type == 'tnt' else 1.0)

        # TNT is more epic.
        if self.blast_type == 'tnt':
            factory.random_explode_sound().play(position=lpos)

            def _extra_boom() -> None:
                factory.random_explode_sound().play(position=lpos)

            bs.timer(0.25, _extra_boom)

            def _extra_debris_sound() -> None:
                factory.debris_fall_sound.play(position=lpos)
                factory.wood_debris_fall_sound.play(position=lpos)

            bs.timer(0.4, _extra_debris_sound)

    @override
    def handlemessage(self, msg: Any) -> Any:
        assert not self.expired

        if isinstance(msg, bs.DieMessage):
            if self.node:
                self.node.delete()

        elif isinstance(msg, ExplodeHitMessage):
            node = bs.getcollision().opposingnode
            assert self.node
            nodepos = self.node.position
            mag = 2000.0
            if self.blast_type == 'ice':
                mag *= 0.5
            elif self.blast_type == 'land_mine':
                mag *= 2.5
            elif self.blast_type == 'tnt':
                mag *= 2.0

            node.handlemessage(
                bs.HitMessage(
                    pos=nodepos,
                    velocity=(0, 0, 0),
                    magnitude=mag,
                    hit_type=self.hit_type,
                    hit_subtype=self.hit_subtype,
                    radius=self.radius,
                    source_player=bs.existing(self._source_player),
                )
            )

            # --- KILL SHOWER ---
            try:
                source = bs.existing(self._source_player)
                effect = _get_source_effect(source)
                if effect and source is not None:
                    def _check_kill(
                        n: bs.Node = node,
                        s: bs.Player = source,
                        e: str = effect,
                    ) -> None:
                        try:
                            if n.exists() and n.hurt >= 1.0:
                                _shower_on_player_ref(s, e, duration=2.0)
                        except Exception:
                            pass
                    bs.timer(0.1, _check_kill)  # small delay for engine to process
            except Exception:
                pass
            # --- END KILL SHOWER ---

            if self.blast_type == 'ice':
                BombFactory.get().freeze_sound.play(10, position=nodepos)
                node.handlemessage(bs.FreezeMessage())

        else:
            return super().handlemessage(msg)
        return None


class Bomb(bs.Actor):
    """A standard bomb and its variants such as land-mines and tnt-boxes.

    category: Gameplay Classes
    """

    # Ew; should try to clean this up later.
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    def __init__(
        self,
        *,
        position: Sequence[float] = (0.0, 1.0, 0.0),
        velocity: Sequence[float] = (0.0, 0.0, 0.0),
        bomb_type: str = 'normal',
        blast_radius: float = 2.0,
        bomb_scale: float = 0.2,
        source_player: bs.Player | None = None,
        owner: bs.Node | None = None,
    ):
        """Create a new Bomb.

        bomb_type can be 'ice','impact','land_mine','normal','sticky', or
        'tnt'. Note that for impact or land_mine bombs you have to call arm()
        before they will go off.
        """
        super().__init__()

        shared = SharedObjects.get()
        factory = BombFactory.get()

        if bomb_type not in (
            'ice',
            'impact',
            'land_mine',
            'normal',
            'sticky',
            'tnt',
        ):
            raise ValueError('invalid bomb type: ' + bomb_type)
        self.bomb_type = bomb_type

        self._exploded = False
        self.scale = bomb_scale

        self.texture_sequence: bs.Node | None = None

        if self.bomb_type == 'sticky':
            self._last_sticky_sound_time = 0.0

        self.blast_radius = blast_radius
        if self.bomb_type == 'ice':
            self.blast_radius *= 1.2
        elif self.bomb_type == 'impact':
            self.blast_radius *= 0.7
        elif self.bomb_type == 'land_mine':
            self.blast_radius *= 0.7
        elif self.bomb_type == 'tnt':
            self.blast_radius *= 1.45

        self._explode_callbacks: list[Callable[[Bomb, Blast], Any]] = []

        # The player this came from.
        self._source_player = source_player

        # By default our hit type/subtype is our own, but we pick up types of
        # whoever sets us off so we know what caused a chain reaction.
        # UPDATE (July 2020): not inheriting hit-types anymore; this causes
        # weird effects such as land-mines inheriting 'punch' hit types and
        # then not being able to destroy certain things they normally could,
        # etc. Inheriting owner/source-node from things that set us off
        # should be all we need I think...
        self.hit_type = 'explosion'
        self.hit_subtype = self.bomb_type

        # The node this came from.
        # FIXME: can we unify this and source_player?
        self.owner = owner

        # Adding footing-materials to things can screw up jumping and flying
        # since players carrying those things and thus touching footing
        # objects will think they're on solid ground.. perhaps we don't
        # wanna add this even in the tnt case?
        materials: tuple[bs.Material, ...]
        if self.bomb_type == 'tnt':
            materials = (
                factory.bomb_material,
                shared.footing_material,
                shared.object_material,
            )
        else:
            materials = (factory.bomb_material, shared.object_material)

        if self.bomb_type == 'impact':
            materials = materials + (factory.impact_blast_material,)
        elif self.bomb_type == 'land_mine':
            materials = materials + (factory.land_mine_no_explode_material,)

        if self.bomb_type == 'sticky':
            materials = materials + (factory.sticky_material,)
        else:
            materials = materials + (factory.normal_sound_material,)

        if self.bomb_type == 'land_mine':
            fuse_time = None
            self.node = bs.newnode(
                'prop',
                delegate=self,
                attrs={
                    'position': position,
                    'velocity': velocity,
                    'mesh': factory.land_mine_mesh,
                    'light_mesh': factory.land_mine_mesh,
                    'body': 'landMine',
                    'body_scale': self.scale,
                    'shadow_size': 0.44,
                    'color_texture': factory.land_mine_tex,
                    'reflection': 'powerup',
                    'reflection_scale': [1.0],
                    'materials': materials,
                },
            )

        elif self.bomb_type == 'tnt':
            fuse_time = None
            self.node = bs.newnode(
                'prop',
                delegate=self,
                attrs={
                    'position': position,
                    'velocity': velocity,
                    'mesh': factory.tnt_mesh,
                    'light_mesh': factory.tnt_mesh,
                    'body': 'crate',
                    'body_scale': self.scale,
                    'shadow_size': 0.5,
                    'color_texture': factory.tnt_tex,
                    'reflection': 'soft',
                    'reflection_scale': [0.23],
                    'materials': materials,
                },
            )

        elif self.bomb_type == 'impact':
            fuse_time = 20.0
            self.node = bs.newnode(
                'prop',
                delegate=self,
                attrs={
                    'position': position,
                    'velocity': velocity,
                    'body': 'sphere',
                    'body_scale': self.scale,
                    'mesh': factory.impact_bomb_mesh,
                    'shadow_size': 0.3,
                    'color_texture': factory.impact_tex,
                    'reflection': 'powerup',
                    'reflection_scale': [1.5],
                    'materials': materials,
                },
            )
            self.arm_timer = bs.Timer(
                0.2, bs.WeakCall(self.handlemessage, ArmMessage())
            )
            self.warn_timer = bs.Timer(
                fuse_time - 1.7, bs.WeakCall(self.handlemessage, WarnMessage())
            )

        else:
            fuse_time = 3.0
            if self.bomb_type == 'sticky':
                sticky = True
                mesh = factory.sticky_bomb_mesh
                rtype = 'sharper'
                rscale = 1.8
            else:
                sticky = False
                mesh = factory.bomb_mesh
                rtype = 'sharper'
                rscale = 1.8
            if self.bomb_type == 'ice':
                tex = factory.ice_tex
            elif self.bomb_type == 'sticky':
                tex = factory.sticky_tex
            else:
                tex = factory.regular_tex
            self.node = bs.newnode(
                'bomb',
                delegate=self,
                attrs={
                    'position': position,
                    'velocity': velocity,
                    'mesh': mesh,
                    'body_scale': self.scale,
                    'shadow_size': 0.3,
                    'color_texture': tex,
                    'sticky': sticky,
                    'owner': owner,
                    'reflection': rtype,
                    'reflection_scale': [rscale],
                    'materials': materials,
                },
            )

            sound = bs.newnode(
                'sound',
                owner=self.node,
                attrs={'sound': factory.fuse_sound, 'volume': 0.25},
            )
            self.node.connectattr('position', sound, 'position')
            bs.animate(self.node, 'fuse_length', {0.0: 1.0, fuse_time: 0.0})

        # Light the fuse!!!
        if self.bomb_type not in ('land_mine', 'tnt'):
            assert fuse_time is not None
            bs.timer(
                fuse_time, bs.WeakCall(self.handlemessage, ExplodeMessage())
            )

        bs.animate(
            self.node,
            'mesh_scale',
            {0: 0, 0.2: 1.3 * self.scale, 0.26: self.scale},
        )

    def get_source_player[PlayerT: bs.Player](
        self, playertype: type[PlayerT]
    ) -> PlayerT | None:
        """Return the source-player if one exists and is the provided type."""
        player: Any = self._source_player
        return (
            player
            if isinstance(player, playertype) and player.exists()
            else None
        )

    @override
    def on_expire(self) -> None:
        super().on_expire()

        # Release callbacks/refs so we don't wind up with dependency loops.
        self._explode_callbacks = []

    def _handle_die(self) -> None:
        if self.node:
            self.node.delete()

    def _handle_oob(self) -> None:
        self.handlemessage(bs.DieMessage())

    def _handle_impact(self) -> None:
        node = bs.getcollision().opposingnode

        # If we're an impact bomb and we came from this node, don't explode.
        # (otherwise we blow up on our own head when jumping).
        # Alternately if we're hitting another impact-bomb from the same
        # source, don't explode. (can cause accidental explosions if rapidly
        # throwing/etc.)
        node_delegate = node.getdelegate(object)
        if node:
            if self.bomb_type == 'impact' and (
                node is self.owner
                or (
                    isinstance(node_delegate, Bomb)
                    and node_delegate.bomb_type == 'impact'
                    and node_delegate.owner is self.owner
                )
            ):
                return
            self.handlemessage(ExplodeMessage())

    def _handle_dropped(self) -> None:
        if self.bomb_type == 'land_mine':
            self.arm_timer = bs.Timer(
                1.25, bs.WeakCall(self.handlemessage, ArmMessage())
            )

        # Once we've thrown a sticky bomb we can stick to it.
        elif self.bomb_type == 'sticky':

            def _setsticky(node: bs.Node) -> None:
                if node:
                    node.stick_to_owner = True

            bs.timer(0.25, lambda: _setsticky(self.node))

    def _handle_splat(self) -> None:
        node = bs.getcollision().opposingnode
        if (
            node is not self.owner
            and bs.time() - self._last_sticky_sound_time > 1.0
        ):
            self._last_sticky_sound_time = bs.time()
            assert self.node
            BombFactory.get().sticky_impact_sound.play(
                2.0,
                position=self.node.position,
            )

    def add_explode_callback(self, call: Callable[[Bomb, Blast], Any]) -> None:
        """Add a call to be run when the bomb has exploded.

        The bomb and the new blast object are passed as arguments.
        """
        self._explode_callbacks.append(call)

    def explode(self) -> None:
        """Blows up the bomb if it has not yet done so."""
        if self._exploded:
            return
        self._exploded = True
        if self.node:
            blast = Blast(
                position=self.node.position,
                velocity=self.node.velocity,
                blast_radius=self.blast_radius,
                blast_type=self.bomb_type,
                source_player=bs.existing(self._source_player),
                hit_type=self.hit_type,
                hit_subtype=self.hit_subtype,
            ).autoretain()
            for callback in self._explode_callbacks:
                callback(self, blast)

        # We blew up so we need to go away.
        # NOTE TO SELF: do we actually need this delay?
        bs.timer(0.001, bs.WeakCall(self.handlemessage, bs.DieMessage()))

    def _handle_warn(self) -> None:
        if self.texture_sequence and self.node:
            self.texture_sequence.rate = 30
            BombFactory.get().warn_sound.play(0.5, position=self.node.position)

    def _add_material(self, material: bs.Material) -> None:
        if not self.node:
            return
        materials = self.node.materials
        if material not in materials:
            assert isinstance(materials, tuple)
            self.node.materials = materials + (material,)

    def arm(self) -> None:
        """Arm the bomb (for land-mines and impact-bombs).

        These types of bombs will not explode until they have been armed.
        """
        if not self.node:
            return
        factory = BombFactory.get()
        intex: Sequence[bs.Texture]
        if self.bomb_type == 'land_mine':
            intex = (factory.land_mine_lit_tex, factory.land_mine_tex)
            self.texture_sequence = bs.newnode(
                'texture_sequence',
                owner=self.node,
                attrs={'rate': 30, 'input_textures': intex},
            )
            bs.timer(0.5, self.texture_sequence.delete)

            # We now make it explodable.
            bs.timer(
                0.25,
                bs.WeakCall(
                    self._add_material, factory.land_mine_blast_material
                ),
            )
        elif self.bomb_type == 'impact':
            intex = (
                factory.impact_lit_tex,
                factory.impact_tex,
                factory.impact_tex,
            )
            self.texture_sequence = bs.newnode(
                'texture_sequence',
                owner=self.node,
                attrs={'rate': 100, 'input_textures': intex},
            )
            bs.timer(
                0.25,
                bs.WeakCall(
                    self._add_material, factory.land_mine_blast_material
                ),
            )
        else:
            raise RuntimeError(
                'arm() should only be called on land-mines or impact bombs'
            )
        self.texture_sequence.connectattr(
            'output_texture', self.node, 'color_texture'
        )
        factory.activate_sound.play(0.5, position=self.node.position)

    def _handle_hit(self, msg: bs.HitMessage) -> None:
        ispunched = msg.srcnode and msg.srcnode.getnodetype() == 'spaz'

        # Normal bombs are triggered by non-punch impacts;
        # impact-bombs by all impacts.
        if not self._exploded and (
            not ispunched or self.bomb_type in ['impact', 'land_mine']
        ):
            # Also lets change the owner of the bomb to whoever is setting
            # us off. (this way points for big chain reactions go to the
            # person causing them).
            source_player = msg.get_source_player(bs.Player)
            if source_player is not None:
                self._source_player = source_player

                # Also inherit the hit type (if a landmine sets off by a bomb,
                # the credit should go to the mine)
                # the exception is TNT.  TNT always gets credit.
                # UPDATE (July 2020): not doing this anymore. Causes too much
                # weird logic such as bombs acting like punches. Holler if
                # anything is noticeably broken due to this.
                # if self.bomb_type != 'tnt':
                #     self.hit_type = msg.hit_type
                #     self.hit_subtype = msg.hit_subtype

            bs.timer(
                0.1 + random.random() * 0.1,
                bs.WeakCall(self.handlemessage, ExplodeMessage()),
            )
        assert self.node
        self.node.handlemessage(
            'impulse',
            msg.pos[0],
            msg.pos[1],
            msg.pos[2],
            msg.velocity[0],
            msg.velocity[1],
            msg.velocity[2],
            msg.magnitude,
            msg.velocity_magnitude,
            msg.radius,
            0,
            msg.velocity[0],
            msg.velocity[1],
            msg.velocity[2],
        )

        if msg.srcnode:
            pass

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, ExplodeMessage):
            self.explode()
        elif isinstance(msg, ImpactMessage):
            self._handle_impact()
        elif isinstance(msg, bs.PickedUpMessage):
            # Change our source to whoever just picked us up *only* if it
            # is None. This way we can get points for killing bots with their
            # own bombs. Hmm would there be a downside to this?
            if self._source_player is None:
                self._source_player = msg.node.source_player
        elif isinstance(msg, SplatMessage):
            self._handle_splat()
        elif isinstance(msg, bs.DroppedMessage):
            self._handle_dropped()
        elif isinstance(msg, bs.HitMessage):
            self._handle_hit(msg)
        elif isinstance(msg, bs.DieMessage):
            self._handle_die()
        elif isinstance(msg, bs.OutOfBoundsMessage):
            self._handle_oob()
        elif isinstance(msg, ArmMessage):
            self.arm()
        elif isinstance(msg, WarnMessage):
            self._handle_warn()
        else:
            super().handlemessage(msg)


class TNTSpawner:
    """Regenerates TNT at a given point in space every now and then.

    category: Gameplay Classes
    """

    def __init__(self, position: Sequence[float], respawn_time: float = 20.0):
        """Instantiate with given position and respawn_time (in seconds)."""
        self._position = position
        self._tnt: Bomb | None = None
        self._respawn_time = random.uniform(0.8, 1.2) * respawn_time
        self._wait_time = 0.0
        self._update()

        # Go with slightly more than 1 second to avoid timer stacking.
        self._update_timer = bs.Timer(
            1.1, bs.WeakCall(self._update), repeat=True
        )

    def _update(self) -> None:
        tnt_alive = self._tnt is not None and self._tnt.node
        if not tnt_alive:
            # Respawn if its been long enough.. otherwise just increment our
            # how-long-since-we-died value.
            if self._tnt is None or self._wait_time >= self._respawn_time:
                self._tnt = Bomb(position=self._position, bomb_type='tnt')
                self._wait_time = 0.0
            else:
                self._wait_time += 1.1
