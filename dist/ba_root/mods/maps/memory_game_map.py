# ba_meta require api 9
from __future__ import annotations

from typing import TYPE_CHECKING

import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any, List, Dict


class MemoryGameMapDefs:
    points: Dict[str, tuple] = {}
    boxes: Dict[str, tuple] = {}
    points['flag_default'] = (0.17358, 3.75764, 1.99124)
    boxes['area_of_interest_bounds'] = (
        0.3544110667, 4.493562578, -2.518391331,
        0.0, 0.0, 0.0,
        16.64754831, 8.06138989, 18.5029888,
    )
    boxes['map_bounds'] = (
        0.2608783669, 4.899663734, -3.543675157,
        0.0, 0.0, 0.0,
        29.23565494, 14.19991443, 29.92689344,
    )


# ba_meta export bascenev1.Map
class MemoryGameMap(bs.Map):
    defs = MemoryGameMapDefs()
    name = 'Sky Tiles'

    @classmethod
    def get_play_types(cls) -> List[str]:
        return []

    @classmethod
    def get_preview_texture_name(cls) -> str:
        return 'achievementOffYouGo'

    @classmethod
    def on_preload(cls) -> Any:
        data: Dict[str, Any] = {
            'bgtex': bs.gettexture('menuBG'),
            'bgmodel': bs.getmesh('thePadBG'),
        }
        return data

    def __init__(self) -> None:
        super().__init__()
        # Background
        bs.newnode(
            'terrain',
            attrs={
                'mesh': self.preloaddata['bgmodel'],
                'lighting': False,
                'background': True,
                'color_texture': self.preloaddata['bgtex'],
            },
        )
        gnode = bs.getactivity().globalsnode
        gnode.tint = (1.3, 1.2, 1.0)
        gnode.ambient_color = (1.3, 1.2, 1.0)
        gnode.vignette_outer = (0.57, 0.57, 0.57)
        gnode.vignette_inner = (0.9, 0.9, 0.9)
        gnode.vr_camera_offset = (0, -0.8, -1.1)
        gnode.vr_near_clip = 0.5
