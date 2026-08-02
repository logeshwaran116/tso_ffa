# ba_meta require api 9

"""
Discord: SANJI
ID: 1328582439685062709
"""

from __future__ import annotations
from typing import TYPE_CHECKING

import bascenev1 as bs
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.maps import *

if TYPE_CHECKING:
    from typing import List, Any, Dict
    
class NeonDefs:
    boxes = {}
    points = {}
    boxes['area_of_interest_bounds'] = (0, 6, 0) + (0, 5, 0) + (17, 9, 5520)
    boxes['map_bounds'] = (0, 0, 0) + (0, 0, 0) + (20.0, 23, 7.25)
    points['flag_default'] = (0,5.1,0)
    points['flag1'] = (-6.5,5.79,0.4)
    points['spawn1'] = (-4.4,5,0)
    points['flag2'] = (6.5,5.79,0.4)
    points['spawn2'] = (4.4,5,0)
    points['ffa_spawn1'] = (3,5.2,0)
    points['ffa_spawn2'] = (-3,5.2,0)
    points['ffa_spawn3'] = (4,5.2,0)
    points['ffa_spawn4'] = (-4,5.2,0)   
    points['ffa_spawn5'] = (0,5.2,0)
    points['powerup_spawn1'] = (-5.5,7,0) 
    points['powerup_spawn2'] = (5.5,7,0)


class NeonBash(bs.Map):
    defs = NeonDefs 
    name = 'Neon Bash'
    
    @classmethod
    def get_play_types(cls) -> List[str]:
        """Return valid play types for this map."""
        return ['melee','king_of_the_hill','keep_away','team_flag']
    
    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'levelIcon'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'bottom_model': bs.getmesh('rampageLevelBottom'), 
            'tex': bs.gettexture('rampageLevelColor'),
            'bgmodel1': bs.getmesh('rampageBG'),
            'bgtex1': bs.gettexture('alwaysLandBGColor'),          
            'bgtex': bs.gettexture('shrapnel1Color'),
            'bgmodel': bs.getmesh('thePadBG'),
        }
        return data
        
    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        
        self._collide_with_player=bs.Material()
        self._collide_with_player.add_actions(conditions=('we_are_older_than', 1), actions=(('modify_part_collision', 'collide', True)))
        self.dont_collide=bs.Material()
        self.dont_collide.add_actions(conditions=('they_are_different_node_than_us', ),actions=(('modify_part_collision', 'collide', False)))
        
        self._map_model1 = bs.getmesh('image1x1')
        self._map_model2 = bs.getmesh('tnt')
        self._map_tex1 = bs.gettexture('bikiniBottomMapBGColor') 
        self._map_tex2 = bs.gettexture('bombColorIce') 
        self._map_tex3 = bs.gettexture('eggTex3')
        self._map_tex4 = bs.gettexture('levelIcon')
        
        self.background = bs.newnode('terrain',
                                    attrs={
                                    'mesh': self.preloaddata['bgmodel'],
                                    'lighting': False,
                                    'background': True,
                                    'color_texture': self.preloaddata['bgtex']
            })
            
        self.bg2 = bs.newnode('terrain',
                              attrs={
                                  'mesh': self.preloaddata['bgmodel1'],
                                  'lighting': False,
                                  'background': True,
                                  'color_texture': self.preloaddata['bgtex1']
                              })                              
         
        self.zone = bs.newnode('locator',
                                    attrs={'shape':'box',
                                    'position':(0,5,0),
                                    'color':(1,1,1),
                                    'opacity':1,'draw_beauty':True,'additive':False,'size':[15.5,0.05,5.3]})
        bs.animate_array(self.zone, 'color', 3,{0:(0,0,0), 1:(0.502, 1, 0.859)},loop= False)
                            
        self.zone = bs.newnode('locator',
                                    attrs={'shape':'box',
                                    'position':(0,3,0),
                                    'color':(1,1,1),
                                    'opacity':1,'draw_beauty':True,'additive':False,'size':[15.5,0.05,5.3]})                          
        bs.animate_array(self.zone, 'color', 3,{0:(0,0,0), 1:(0.502, 1, 0.859)},loop= False)
                                                
        self.zone = bs.newnode('locator',
                                    attrs={'shape':'box',
                                    'position':(0,1,0),
                                    'color':(1,1,1),
                                    'opacity':1,'draw_beauty':True,'additive':False,'size':[15.5,0.05,5.3]})
        bs.animate_array(self.zone, 'color', 3,{0:(0,0,0), 1:(0.502, 1, 0.859)},loop= False)

        for m_pos1 in [(-5,3,0),(0,3,0),(5,3,0)]:   
            self.mv_center = bs.newnode('prop',
                    attrs={'body': 'puck',
                           'position': m_pos1,
                           'mesh': self._map_model2,
                           'mesh_scale': 7.23,
                           'body_scale': 0.1,
                           'shadow_size': 0.0,
                           'gravity_scale':0.0,
                           'color_texture': self._map_tex3,
                           'reflection': 'soft',
                           'reflection_scale': [0.37],
                           'is_area_of_interest': True,
                           'materials': [self.dont_collide]})    
                           
        for m_pos1 in [(0,3,0)]:                              
            self.mc_center = bs.newnode('region',attrs={
                                        'position': m_pos1,
                                        'scale': (15,5,5),
                                        'type': 'box',
                                        'materials': (self._collide_with_player, shared.footing_material)})                                
                           
                           
        for m_pos1 in [(-5,5.4,0),(0,5.4,0),(5,5.4,0)]:    
            self.mv_center = bs.newnode('prop',
                    attrs={'body': 'puck',
                           'position': m_pos1,
                           'mesh': self._map_model1,
                           'mesh_scale': 4.00,
                           'body_scale': 0.1,
                           'shadow_size': 0.0,
                           'gravity_scale':0.0,
                           'color_texture': self._map_tex4,
                           'reflection': 'soft',
                           'reflection_scale': [0.0],
                           'is_area_of_interest': True,
                           'materials': [self.dont_collide]})                             
        
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.2,1.2,1.2)
        gnode.ambient_color = (1.15,1.25,1.6)
        gnode.vignette_outer = (0.5,-0.25,0.5)
        gnode.vignette_inner = (0.93,0.93,0.95)

# ba_meta export babase.Plugin
class Sanji(bs.Plugin):
    try:
        bs._map.register_map(NeonBash)
    except Exception:
        import traceback 
        traceback.print_exc()
