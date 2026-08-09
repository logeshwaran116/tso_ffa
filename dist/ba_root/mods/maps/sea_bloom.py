# ba_meta require api 9

"""
Discord: SANJI
ID: 1328582439685062709
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import bascenev1 as bs
from bascenev1 import _map
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.maps import *

if TYPE_CHECKING:
    from typing import List, Any, Dict


map_scale = 0.6
region_scale = (24, 1.0, 22.55)
mesh_scale = 24

class SEADEFs:
    boxes = {}
    points = {}
    boxes['area_of_interest_bounds'] = (0.0, 1.185751251, 0.4326226188) + (0.0, 0.0, 0.0) + (29.8180273 * map_scale, 11.57249038, 29.89134176 * map_scale)
    boxes['map_bounds'] = (0.0, 1.185751251, 0.4326226188) + (0.0, 0.0, 0.0) + (29.8180273 * map_scale, 11.57249038, 29.89134176 * map_scale)
    points['spawn1'] = (-8.02 * map_scale, 1.10, 0.0)
    points['spawn2'] = (8.02 * map_scale, 1.10, 0.0)
    points['ffa_spawn1'] = (-8.02 * map_scale, 1.10, 6.02 * map_scale)
    points['ffa_spawn2'] = (-8.02 * map_scale, 1.10, -6.02 * map_scale)
    points['ffa_spawn3'] = (8.02 * map_scale, 1.10, 6.02 * map_scale)
    points['ffa_spawn4'] = (8.02 * map_scale, 1.10, -6.02 * map_scale)
    points['powerup_spawn1'] = (-10.1 * map_scale, 1.10, -5 * map_scale)
    points['powerup_spawn2'] = (10.1 * map_scale, 1.10, 5 * map_scale)
    points['powerup_spawn3'] = (-10.1 * map_scale, 1.10, 5 * map_scale)
    points['powerup_spawn4'] = (10.1 * map_scale, 1.10, -5 * map_scale)
    points['flag1'] = (-10.01 * map_scale, 1.0, 0.0)
    points['flag2'] = (10.01 * map_scale, 1.0, 0.0)
    points['flag_default'] = (0.0, 1.0, 0.0)


class SeaBloom(bs.Map):
    defs = SEADEFs()
    name = 'Sea Bloom'
    
    @classmethod
    def get_play_types(cls) -> List[str]:
        return ['team_flag', 'melee', 'keep_away']
    
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'ouyaUButton'
    
    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'mesh': bs.getmesh('image1x1'),
            'mesh_obs': bs.getmesh('tnt'),
            'color_texture': bs.gettexture('bombColorIce'),
            'bgmesh': bs.getmesh('thePadBG'),
            'bgtex': bs.gettexture('menuBG')
        }
        return data
    
    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        
        self.collide_material = bs.Material()
        self.collide_material.add_actions(
            conditions=('we_are_older_than', 1),
            actions=('modify_part_collision', 'collide', True))
        
        self.non_collide_material = bs.Material()
        self.non_collide_material.add_actions(
            conditions=('they_are_different_node_than_us', ),
            actions=('modify_part_collision', 'collide', False))
        
        self.background = bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'color_texture': self.preloaddata['bgtex'],
                'background': True
            })
        
        self.visible_platform = bs.newnode(
            'prop',
            attrs={
                'position': (0.0, 0.15, 0.0),
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['color_texture'],
                'mesh_scale': mesh_scale * map_scale,
                'body': 'puck',
                'body_scale': 0.1,
                'gravity_scale': 0.0,
                'shadow_size': 0.0,
                'reflection': 'soft',
                'reflection_scale': [0.45],
                'materials': [self.non_collide_material]
            })
        
        
        self.collision_region = bs.newnode(
            'region',
            attrs={
                'position': (0.0, -0.34, 0.0),
                'type': 'box',
                'scale':(region_scale[0] * map_scale, region_scale[1], region_scale[2] * map_scale) ,
                'materials': [self.collide_material,
                              shared.footing_material]
            })
        
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.1, 1.05, 1.17)
        gnode.happy_thoughts_mode = False
        gnode.ambient_color = (1.2, 1.17, 1.1)
        gnode.vignette_outer = (0.9, 0.9, 0.96)
        gnode.vignette_inner = (0.95, 0.95, 0.93)


# ba_meta export babase.Plugin
class Sanji(bs.Plugin):
    _map.register_map(SeaBloom)