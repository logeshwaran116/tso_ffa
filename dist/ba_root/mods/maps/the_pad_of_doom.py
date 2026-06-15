# ba_meta require api 9
from __future__ import annotations
from typing import TYPE_CHECKING

import bascenev1 as bs
import bauiv1 as bui
from bascenev1 import _map
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.maps import *

if TYPE_CHECKING:
    pass


class ThePadOfDoomMapData():
    points = {}
    boxes = {}

    boxes['area_of_interest_bounds'] = (
        (0.3544110667, 4.493562578, -2.518391331)
    + (0.0, 0.0, 0.0)
    + (16.64754831, 8.06138989, 18.5029888)
    )
    boxes['edge_box'] = (
        (-0.103873591, 0.4133341891, 0.4294651013)
        + (0.0, 0.0, 0.0)
        + (22.48295719, 1.290242794, 8.990252454)
    )
    points['ffa_spawn1'] = (-3.812275836, 4.380655495, -8.962074979) + (
    2.371946621,
    1.0,
    0.8737798622,
    )
    points['ffa_spawn2'] = (4.472503025, 4.406820459, -9.007239732) + (
    2.708525168,
    1.0,
    0.8737798622,
    )
    boxes['map_bounds'] = (
        (0.0, 1.185751251, 0.4326226188)
        + (0.0, 0.0, 0.0)
        + (42.09506485, 22.81173179, 29.76723155)
    )
    points['flag_default'] = (0.4611826686, 4.382076338, 3.680881802)
    points['flag1'] = (-7.026110145, 4.308759233, -6.302807727)
    points['flag2'] = (7.632557137, 4.366002373, -6.287969342)
    points['powerup_spawn1'] = (-4.166594349, 5.281834349, -6.427493781)
    points['powerup_spawn2'] = (4.426873526, 5.342460464, -6.329745237)
    points['powerup_spawn3'] = (-4.201686731, 5.123385835, 0.4400721376)
    points['powerup_spawn4'] = (4.758924722, 5.123385835, 0.3494054559)
    points['spawn1'] = (-3.902942148, 4.380655495, -8.962074979) + (
    1.66339533,
    1.0,
    0.8737798622,
)
    points['spawn2'] = (4.775040345, 4.406820459, -9.007239732) + (
    1.66339533,
    1.0,
    0.8737798622,
)
    points['tnt1'] = (0.4599593402, 4.044276501, -6.573537395)



class ThePadOfDoomMap(bs.Map):

    defs = ThePadOfDoomMapData()
    name = 'The pad of doom'

    @classmethod
    def get_play_types(cls) -> list[str]:
        return ['melee', 'keep_away']

    @classmethod
    def get_preview_texture_name(cls) -> list[str]:
        return 'thePadPreview'

    @classmethod
    def on_preload(cls) -> any:
        data: dict[str, any] = {
            'mesh': bs.getmesh('thePadLevel'),
            'mesh_bottom': bs.getmesh('thePadLevelBottom'),
            'tex': bs.gettexture('thePadLevelColor'),
            'tex2': bs.gettexture('doomShroomLevelColor'),
            'collision_mesh': bs.getcollisionmesh('thePadLevelCollide'),
            'stem_mesh': bs.getmesh('doomShroomStem'),
            'collide_bg': bs.getcollisionmesh('doomShroomStemCollide'),
            'bgtex': bs.gettexture('rampageBGColor'),
            'bgtex2': bs.gettexture('rampageBGColor2'),
            'bgmesh': bs.getmesh('rampageBG'),
            'bgmesh2': bs.getmesh('rampageBG2'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()

        self.node = bs.newnode(
            'terrain',
            delegate=self,
            attrs={
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['tex'],
                'collision_mesh': self.preloaddata['collision_mesh'],
                'materials': [shared.footing_material]
            }
        )
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'lighting': False,
                
                'color_texture': self.preloaddata['bgtex']
            }
        )
        self.stem = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['stem_mesh'],
                'lighting': False,
                'color_texture': self.preloaddata['tex2'],
            },
        )
        self.bg_collide = bs.newnode(
            'terrain',
            attrs={
                'collision_mesh': self.preloaddata['collide_bg'],
                'materials': [shared.death_material],
            },
        )
        self.bottom = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['mesh_bottom'],
                'lighting': False,
                'color_texture': self.preloaddata['tex'],
            },
        )
        self.bg2 = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh2'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex2'],
            },
        )

        gnode = bs.getactivity().globalsnode
        gnode.tint = (0.82, 1.10, 1.15)
        gnode.ambient_color = (0.9, 1.3, 1.1)
        gnode.shadow_ortho = False
        gnode.vignette_outer = (0.76, 0.76, 0.76)
        gnode.vignette_inner = (0.95, 0.95, 0.99)

    def is_point_near_edge(self,
                           point: bs.Vec3,
                           running: bool = False) -> bool:
        xpos = point.x
        zpos = point.z
        x_adj = xpos * 0.125
        z_adj = (zpos + 3.7) * 0.2
        if running:
            x_adj *= 1.4
            z_adj *= 1.4
        return x_adj * x_adj + z_adj * z_adj > 1.0


# ba_meta export plugin
class Startingbat(bs.Plugin):
    _map.register_map(ThePadOfDoomMap)
