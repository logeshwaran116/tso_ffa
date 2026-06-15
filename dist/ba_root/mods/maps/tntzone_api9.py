# ba_meta require api 9

"""
Discord: !   JETZ#5313
Please dont edit anything!
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import bascenev1 as ba
from bascenev1 import _map
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.maps import *

if TYPE_CHECKING:
    from typing import List, Any, Dict


class TNTZoneDefs:
    boxes = {}
    points = {}
    boxes['area_of_interest_bounds'] = (0.0, 1.185751251, 0.4326226188) + (
        0.0, 0.0, 0.0) + (29.8180273, 11.57249038, 29.89134176)
    boxes['map_bounds'] = (0.0, 1.185751251, 0.4326226188) + (
        0.0, 0.0, 0.0) + (29.8180273, 11.57249038, 29.89134176)
    points['spawn1'] = (-8.02, 1.10, 0.0)
    points['spawn2'] = (8.02, 1.10, 0.0)
    points['ffa_spawn1'] = (-8.02, 1.10, 6.02)
    points['ffa_spawn2'] = (-8.02, 1.10, -6.02)
    points['ffa_spawn3'] = (8.02, 1.10, 6.02)
    points['ffa_spawn4'] = (8.02, 1.10, -6.02)
    points['powerup_spawn1'] = (-10.1, 1.10, -5)
    points['powerup_spawn2'] = (10.1, 1.10, 5)
    points['powerup_spawn3'] = (-10.1, 1.10, 5)
    points['powerup_spawn4'] = (10.1, 1.10, -5)
    points['flag1'] = (-10.01, 1.0, 0.0)
    points['flag2'] = (10.01, 1.0, 0.0)
    points['flag_default'] = (0.0, 1.0, 0.0)


class TNTZoneMap(ba.Map):
    """New BombSquad Map!"""
    
    defs = TNTZoneDefs()
    name = u'\ue043TNTZone\ue043'
    
    @classmethod
    def get_play_types(cls) -> List[str]:
        return ['team_flag', 'melee', 'keep_away']
    
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'tnt'
    
    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'mesh': ba.getmesh('image1x1'),
            'mesh_obs': ba.getmesh('tnt'),
            'color_texture': ba.gettexture('tnt'),
            'tex_obs': ba.gettexture('eggTex2'),
            'bgmesh': ba.getmesh('thePadBG'),
            'bgtex': ba.gettexture('menuBG')
        }
        return data
    
    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        
        self.collide_material = ba.Material()
        self.collide_material.add_actions(
            conditions=('we_are_older_than', 1),
            actions=('modify_part_collision', 'collide', True))
        
        self.non_collide_material = ba.Material()
        self.non_collide_material.add_actions(
            conditions=('they_are_different_node_than_us', ),
            actions=('modify_part_collision', 'collide', False))
        
        self.background = ba.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmesh'],
                'color_texture': self.preloaddata['bgtex'],
                'background': True
            })
        
        self.visible_platform = ba.newnode(
            'prop',
            attrs={
                'position': (0.0, 0.15, 0.0),
                'mesh': self.preloaddata['mesh'],
                'color_texture': self.preloaddata['color_texture'],
                'mesh_scale': 24,
                'body': 'puck',
                'body_scale': 0.1,
                'gravity_scale': 0.0,
                'shadow_size': 0.0,
                'reflection': 'soft',
                'reflection_scale': [0.45],
                'materials': [self.non_collide_material]
            })
        
        self.obs_a = ba.newnode(
            'prop',
            attrs={
                'position': (0.0, 1.0, 10.0),
                'mesh': self.preloaddata['mesh_obs'],
                'color_texture': self.preloaddata['tex_obs'],
                'mesh_scale': 4.0,
                'body': 'crate',
                'body_scale': 3.95,
                'shadow_size': 0.0,
                'gravity_scale': 0.0,
                'reflection': 'soft',
                'reflection_scale': [0.95],
                'materials': [self.non_collide_material]
            })
        
        self.obs_b = ba.newnode(
            'prop',
            attrs={
                'position': (0.0, 1.0, -10.0),
                'mesh': self.preloaddata['mesh_obs'],
                'color_texture': self.preloaddata['tex_obs'],
                'mesh_scale': 4.0,
                'body': 'crate',
                'body_scale': 3.95,
                'shadow_size': 0.0,
                'gravity_scale': 0.0,
                'reflection': 'soft',
                'reflection_scale': [0.95],
                'materials': [self.non_collide_material]
            })
        
        self.obs_c = ba.newnode(
            'prop',
            attrs={
                'position': (2.0, 1.0, 10.0),
                'mesh': self.preloaddata['mesh_obs'],
                'color_texture': self.preloaddata['tex_obs'],
                'mesh_scale': 4.0,
                'body': 'crate',
                'body_scale': 3.95,
                'shadow_size': 0.0,
                'gravity_scale': 0.0,
                'reflection': 'soft',
                'reflection_scale': [0.95],
                'materials': [self.non_collide_material]
            })
        
        self.obs_d = ba.newnode(
            'prop',
            attrs={
                'position': (2.0, 1.0, -10.0),
                'mesh': self.preloaddata['mesh_obs'],
                'color_texture': self.preloaddata['tex_obs'],
                'mesh_scale': 4.0,
                'body': 'crate',
                'body_scale': 3.95,
                'shadow_size': 0.0,
                'gravity_scale': 0.0,
                'reflection': 'soft',
                'reflection_scale': [0.95],
                'materials': [self.non_collide_material]
            })
        
        self.obs_f = ba.newnode(
            'prop',
            attrs={
                'position': (-2.0, 1.0, 10.0),
                'mesh': self.preloaddata['mesh_obs'],
                'color_texture': self.preloaddata['tex_obs'],
                'mesh_scale': 4.0,
                'body': 'crate',
                'body_scale': 3.95,
                'shadow_size': 0.0,
                'gravity_scale': 0.0,
                'reflection': 'soft',
                'reflection_scale': [0.95],
                'materials': [self.non_collide_material]
            })
        
        self.obs_g = ba.newnode(
            'prop',
            attrs={
                'position': (-2.0, 1.0, -10.0),
                'mesh': self.preloaddata['mesh_obs'],
                'color_texture': self.preloaddata['tex_obs'],
                'mesh_scale': 4.0,
                'body': 'crate',
                'body_scale': 3.95,
                'shadow_size': 0.0,
                'gravity_scale': 0.0,
                'reflection': 'soft',
                'reflection_scale': [0.95],
                'materials': [self.non_collide_material]
            })
        
        self.collision_region = ba.newnode(
            'region',
            attrs={
                'position': (0.0, -0.34, 0.0),
                'type': 'box',
                'scale': (24, 1.0, 22.55),
                'materials': [self.collide_material,
                              shared.footing_material]
            })
        
        self.team_a_zone = ba.newnode(
            'locator',
            attrs={
                'position': (-8.01, 0.15, 0.0),
                'shape': 'box',
                'draw_beauty': True,
                'additive': False,
                'size': [5.0, 0.001, 5.0]
            })
        
        self.team_b_zone = ba.newnode(
            'locator',
            attrs={
                'position': (8.01, 0.15, 0.0),
                'shape': 'box',
                'draw_beauty': True,
                'additive': False,
                'size': [5.0, 0.001, 5.0]
            })
        
        gnode = ba.getactivity().globalsnode
        gnode.tint = (1.1, 1.05, 1.17)
        gnode.happy_thoughts_mode = False
        gnode.ambient_color = (1.2, 1.17, 1.1)
        gnode.vignette_outer = (0.9, 0.9, 0.96)
        gnode.vignette_inner = (0.95, 0.95, 0.93)


# ba_meta export babase.Plugin
class ByJetz(ba.Plugin):
    _map.register_map(TNTZoneMap)