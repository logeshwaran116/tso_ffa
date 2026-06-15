# ba_meta require api 9

# Mega Mine map converted from API 7 to API 9
# Original mod by Froshlee14, updated by SEBASTIAN2059
# Modified to use TNT texture and mesh

from typing import TYPE_CHECKING, Any

import babase
import bascenev1 as bs
from bascenev1lib.gameutils import SharedObjects
from bascenev1lib.actor.powerupbox import PowerupBox, PowerupBoxFactory

if TYPE_CHECKING:
    from typing import List, Dict


class mega_mine_defs:
    boxes = {}
    points = {}
    boxes['area_of_interest_bounds'] = (0, 1, 0) + (0, 0, 0) + (0, 0, 0)
    boxes['map_bounds'] = (0, 0, 0) + (0, 0, 0) + (20, 20, 20)
    points['ffa_spawn1'] = (3, 4, -2)
    points['ffa_spawn2'] = (-3, 4, -2)
    points['ffa_spawn3'] = (3, 4, 2)
    points['ffa_spawn4'] = (-3, 4, 2)
    points['powerup_spawn1'] = (-2.8, 5, 0)
    points['powerup_spawn2'] = (2.8, 5, 0)
    points['powerup_spawn3'] = (0, 5, -2.8)
    points['powerup_spawn4'] = (0, 5, 2.8)
    # Add more spawn points for players with slightly reduced height
    points['spawn1'] = (2.5, 5, -2.0) + (0.5, 1.0, 2.0)  # Reduced Y from 8 to 7
    points['spawn2'] = (-2.5, 5, -2.0) + (0.5, 1.0, 2.0)  # Reduced Y from 8 to 7


class TNTBOX(bs.Map):
    """A giant TNT mine!"""

    defs = mega_mine_defs

    name = 'Mega TNT Mine'

    @classmethod
    def get_play_types(cls) -> list[str]:
        """Return valid play types for this map."""
        return ['melee']

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'tnt'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'mesh': bs.getmesh('tnt'),
            'tex': bs.gettexture('ouyaAButton'),
            'bg_mesh': bs.getmesh('thePadBG'),
            'bg_tex': bs.gettexture('menuBG'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        shared = SharedObjects.get()
        self.node = bs.newnode('prop',
                               delegate=self,
                               attrs={'position': (0, -3.5, 0),
                                      'velocity': (0, 0, 0),
                                      'mesh': self.preloaddata['mesh'],
                                      'mesh_scale': 14.6,
                                      'body_scale': 14.3,
                                      'size':[25,13,4],
                                      'density': 999999999999999999999,
                                      'damping': 999999999999999999999,
                                      'gravity_scale': 0,
                                      'body': 'crate',
                                      'reflection': 'powerup',
                                      'reflection_scale': [1.0],
                                      'color_texture': self.preloaddata['tex'],
                                      'materials': [shared.footing_material]})

        self.background = bs.newnode('terrain',
                                     attrs={
                                         'mesh': self.preloaddata['bg_mesh'],
                                         'lighting': False,
                                         'background': True,
                                         'color_texture': self.preloaddata['bg_tex']
                                     })

        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.2, 1.17, 1.1)
        gnode.ambient_color = (1.2, 1.17, 1.1)
        gnode.vignette_outer = (0.6, 0.6, 0.64)
        gnode.vignette_inner = (0.95, 0.95, 0.93)


# Register the map
bs._map.register_map(TNTBOX)