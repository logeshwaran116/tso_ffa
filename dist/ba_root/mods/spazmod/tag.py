import setting
from playersdata import pdata
from tools import coins
from stats import mystats
import babase
import bascenev1 as bs
import math
from _bascenev1 import get_client_ping as _get_ping
import random

sett = setting.get_settings_data()


# -------------------- PING SYSTEM --------------------

class PingDisplay:
    def __init__(self, owner, player):
        self.node = owner
        try:
            self.client_id = player.sessionplayer.inputdevice.client_id
        except Exception:
            self.client_id = None

        m = bs.newnode('math', owner=self.node,
                       attrs={'input1': (0, -1.0, 0), 'operation': 'add'})
        self.node.connectattr('torso_position', m, 'input2')

        self.txt = bs.newnode('text', owner=self.node, attrs={
            'text': '',
            'in_world': True,
            'shadow': 1.0,
            'flatness': 1.0,
            'scale': 0.009,
            'h_align': 'center'
        })
        m.connectattr('output', self.txt, 'position')
        self._update()

    def _update(self):
        if not self.node.exists(): return
        try:
            ping = _get_ping(self.client_id) if self.client_id is not None else 0
        except Exception: ping = 0

        if isinstance(ping, (float, int)):
            if ping < 80: col = (0, 1, 0)
            elif ping < 150: col = (1, 1, 0)
            else: col = (1, 0, 0)

            self.txt.text = f"{ping} ms"
            self.txt.color = col
            bs.timer(1.0, self._update)

def addtag(node, player):
    session_player = player.sessionplayer
    account_id = session_player.get_v1_account_id()
    customtag_ = pdata.get_custom()
    customtag = customtag_['customtag']
    roles = pdata.get_roles()
    p_roles = pdata.get_player_roles(account_id)

    tag = None
    col = (0.5, 0.5, 1)  # default color for custom tags

    anim_id = 1 #default anim_id

    # Priority 1: temporary paid tag from coins
    paid_tag, anim_id = pdata.get_paid_tag(account_id)
    
    if paid_tag:
        tag = paid_tag
        anim_id = anim_id
    elif account_id in customtag:
        tag = customtag[account_id].get('tag', "tag")
        anim_id = customtag[account_id].get('anim_id', 1)
    elif p_roles != []:
        for role in roles:
            if role in p_roles:
                tag = roles[role].get("tag","")
                anim_id = roles[role].get("anim_id", 1)
                col = tuple(roles[role].get("tagcolor",(0.7, 0.7, 0.7)))
                break

    if tag:
        Tag(node, tag, col, anim_id)
    PingDisplay(node, player)


def addrank(node, player):
    session_player = player.sessionplayer
    account_id = session_player.get_v1_account_id()
    rank = mystats.getRank(account_id)

    if rank:
        Rank(node, rank)


def addhp(node, spaz):
    def showHP():
        hp = spaz.hitpoints
        if spaz.node.exists():
            HitPoint(owner=node, prefix=str(int(hp)), position=(0, 1.75, 0), shad=1.4)
        else:
            spaz.hptimer = None

    spaz.hptimer = bs.Timer(0.1, babase.Call(showHP), repeat=True)


class Tag:
    def __init__(self, owner=None, tag="something", col=(1, 1, 1), anim_id: int = 1):
        self.node = owner
        self.tag = self._replace_codes(tag)
        self.anim_id = anim_id
        self._char_nodes = []  # each entry: (char_node, index, math_node, x_offset)

        self.base = bs.newnode('math', owner=self.node, attrs={'input1': (0, 1.5, 0), 'operation': 'add'})
        self.node.connectattr('torso_position', self.base, 'input2')

        self._build_tag(self.tag, col)

    def _replace_codes(self, tag: str) -> str:
        repl = {
            '\\d': '\ue048', '\\c': '\ue043', '\\h': '\ue049',
            '\\s': '\ue046', '\\n': '\ue04b', '\\f': '\ue04f',
            '\\g': '\ue027', '\\i': '\ue03a', '\\m': '\ue04d',
            '\\t': '\ue01f', '\\bs': '\ue01e', '\\j': '\ue010',
            '\\e': '\ue045', '\\l': '\ue047', '\\a': '\ue020',
            '\\b': '\ue00c'
        }
        for k, v in repl.items():
            tag = tag.replace(k, v)
        return tag

    def _build_tag(self, tag_text, base_color):
        TAG_SCALE = 0.01
        TAG_SPACING = 0.15
        ENABLE_TAG_ANIM = sett["enableTagAnimation"]

        n = max(1, len(tag_text))
        center_index = (n - 1) * 0.5

        for i, ch in enumerate(tag_text):
            char_node = bs.newnode(
                'text', owner=self.node,
                attrs={
                    'text': ch, 'in_world': True, 'shadow': 1.0, 'flatness': 1.0,
                    'color': tuple(base_color), 'scale': TAG_SCALE, 'h_align': 'center'
                }
            )
            dx = TAG_SPACING * (i - center_index)
            mchar = bs.newnode('math', owner=self.node, attrs={'input1': (dx, 0.0, 0.0), 'operation': 'add'})
            self.base.connectattr('output', mchar, 'input2')
            mchar.connectattr('output', char_node, 'position')
            self._char_nodes.append((char_node, i, mchar, dx))

        # Staggered fade-in reveal (from the newer version)
        try:
            step = 0.12
            for idx, (cnode, _, _, _) in enumerate(self._char_nodes):
                try:
                    cnode.opacity = 0.0
                except Exception:
                    pass

                def _reveal(n=cnode):
                    try:
                        bs.animate(n, 'opacity', {0.0: 0.0, 0.75: 1.0})
                    except Exception:
                        pass

                bs.apptimer(idx * step, _reveal)
        except Exception:
            pass

        if ENABLE_TAG_ANIM:
            self._apply_animation(base_color)

    def _apply_animation(self, col):
        anim_id = self.anim_id
        total_chars = max(1, len(self._char_nodes))

        # anim_id 1 (or anything unrecognized) -> the newer wave-shimmer default
        if anim_id not in range(1, 21):
            self._apply_wave_shimmer((2,0,2), (0,2,2), (2,2,0))
            return
        
        def _random_color():
            return (random.random()*2, random.random()*2, random.random()*2)
        
        def _animate_letter_color(node):
            if not node.exists():
                return
            duration = random.uniform(0.3, 1.0)
            start_color = node.color
            target_color = _random_color()
            bs.animate_array(node, 'color', 3, {0.0: start_color, duration: target_color})
            bs.timer(duration, babase.Call(_animate_letter_color, node))

        # anim_id 2-12 -> restored preset effects from the older version
        for char_node, i, mchar, curr_x in self._char_nodes:
            delay = i * 0.15

            if anim_id == 1:#blue - pink
                bs.animate_array(
                    char_node,
                    'color',
                    3,
                    {0.0:(0.0,0.8,1.7), 0.5:(2.0,0.0,1.0), 1.0:(0.0,0.8,1.7)},
                    loop= True,
                    offset= delay
                )

            elif anim_id ==2: #purple - green
                bs.animate_array(
                    char_node,
                    'color',
                    3,
                    {0.0:(0.4,2.0,0.0), 0.5:(1.49,0.322,1.85), 1.0:(0.4,2.0,0.0)},
                    loop= True,
                    offset= delay
                )

            elif anim_id == 3:#orange - dark blue
                bs.animate_array(
                    char_node,
                    'color',
                    3,
                    {0.0:(2.0,0.58,0.008), 0.25:(0.212,0.244,0.84), 0.5:(2.0,0.58,0.008), 1.0:(0.212,0.244,0.84)},
                    loop= True,
                    offset= delay
                )

            elif anim_id == 4:#red - white
                bs.animate_array(
                    char_node,
                    'color',
                    3,
                    {0.0:(2,0.0,0.0), 1.0:(0,2,2)},
                    loop= True,
                    offset= delay
                )

            elif anim_id == 5:#yellow - cyan
                bs.animate_array(
                    char_node,
                    'color',
                    3,
                    {0.0:(2.0,1.67,0.0), 1.0:(0.542,1.326,1.326)},
                    loop= True,
                    offset= delay
                )

            elif anim_id == 6: #red blue green
                bs.animate_array(
                    char_node, 
                    'color', 
                    3, 
                    {0.0:(2,0,0), 0.5:(0,2,0), 1.0:(0,0,2)}, 
                    loop=True, 
                    offset=delay
                )

            elif anim_id == 7: #purple cyan yellow
                bs.animate_array(
                    char_node, 
                    'color', 
                    3, 
                    {0.0:(2,0,2), 0.5:(0,2,2), 1.0:(2,2,0)}, 
                    loop=True, 
                    offset=delay
                )

            elif anim_id == 8: #yellow green blue
                bs.animate_array(
                    char_node, 
                    'color', 
                    3, 
                    {0.0:(2,1,0), 0.5:(0,2,0), 1.0:(0,0,2)}, 
                    loop=True, 
                    offset=delay
                )

            elif anim_id == 9: #Deep Navy, Cerulean Blue, Seafoam Mint
                bs.animate_array(
                    char_node, 
                    'color', 
                    3, 
                    {0.0:(0.1,0.3,0.6), 0.5:(0.3,1.2,1.5), 1.0:(1.4,1.9,1.7)}, 
                    loop=True, 
                    offset=delay
                )


            elif anim_id == 10: #Royal Violet, Magenta Rose, Soft Peach
                bs.animate_array(
                    char_node, 
                    'color', 
                    3, 
                    {0.0:(0.6,0.2,0.8), 0.5:(1.6,0.6,1.0), 1.0:(2.0,1.3,1.1), 1.5:(0.4,1.2,1.4)}, 
                    loop=True, 
                    offset=delay
                )

            elif anim_id == 11: #Brick Rust, Electric Cyan, Deep Maroon, Mustard Gold
                bs.animate_array(
                    char_node, 
                    'color', 
                    3, 
                   {0.0:(1.5,0.3,0.2), 0.33:(0.0,1.9,1.8), 0.66:(0.6,0.1,0.2), 1.0:(2.0,1.6,0.4)}, 
                    loop=True, 
                    offset=delay
                )

            elif anim_id == 12: #Retro Mustard, Sky Cyan, Dark Eggplant, Bright Mint
                bs.animate_array(
                    char_node, 
                    'color', 
                    3, 
                   {0.0:(1.8,0.0,0.8), 0.25:(0.0,1.6,0.4), 0.5:(1.2,0.4,1.6), 0.75:(0.6,1.2,0.0), 1.0:(0.0,0.8,1.8)}, 
                    loop=True, 
                    offset=delay
                )

            elif anim_id == 13: #Neon Coral, Forest Shadow, Bright Purple, Canary Yellow + Domino effect
                bs.animate_array(
                    char_node, 
                    'color', 
                    3, 
                   {0.0:(2.0,0.6,0.7), 0.33:(0.1,0.4,0.3), 0.66:(1.0,0.4,1.6), 1.0:(1.9,1.7,0.6)}, 
                    loop=True, 
                    offset=delay
                )
                bs.animate(char_node, 'rotate', {0.0: -20, 1.0: 20}, loop=True, offset=delay)


            elif anim_id == 14: #Burnt Bronze, Rich Amber, Sovereign Gold, Bright Canary, Platinum Cream + Domino Effect
                bs.animate_array(
                    char_node, 
                    'color', 
                    3, 
                   {0.0:(0.5,0.2,0.0), 0.25:(1.2,0.7,0.1), 0.5:(1.9,1.4,0.2), 0.75:(2.0,1.8,0.8), 1.0:(2.0,1.96,1.7)}, 
                    loop=True, 
                    offset=delay
                )
                bs.animate(char_node, 'rotate', {0.0: -20, 1.0: 20}, loop=True, offset=delay)

            elif anim_id == 15: #Red → White → Blue → Cyan‑Blue → Red + swing
                bs.animate_array(
                    char_node, 
                    'color', 
                    3, 
                    {0.0:(2.0,0.0,0.0), 0.25:(2.0,2.0,2.0), 0.5:(0.0,0.0,2.0), 0.75:(0.0,1.6,2.0), 1.0:(2.0,0.0,0.0)}, 
                    loop=True, 
                    offset=delay
                )
                bs.animate(char_node, 'rotate', {0.0: 0, 0.125: 7.5, 0.25: 15, 0.375: 7.5, 0.5: 0, 0.625: -7.5, 0.75: -15, 0.875: -7.5, 1.0: 0}, loop=True, offset=delay)

            elif anim_id == 16: ##midnight #amethyst #ochre #moss #lavender + swing
                bs.animate_array(
                    char_node, 
                    'color', 
                    3, 
                    {0.0:(0.0,0.0,0.8), 0.25:(1.2,0.0,1.2), 0.5:(1.6,1.2,0.4), 0.75:(0.0,1.0,0.4), 1.0:(1.4,1.4,1.8)}, 
                    loop=True, 
                    offset=delay
                )
                bs.animate(char_node, 'rotate', {0.0: 0, 0.125: 7.5, 0.25: 15, 0.375: 7.5, 0.5: 0, 0.625: -7.5, 0.75: -15, 0.875: -7.5, 1.0: 0}, loop=True, offset=delay)

            elif anim_id == 17: #Deep Crimson, Blaze Red, Plasma Orange, Solar Yellow, Radiant Sunburst + wave
                bs.animate_array(
                    char_node, 
                    'color', 
                    3, 
                    {0.0:(0.6,0.0,0.2), 0.25:(1.7,0.1,0.3), 0.5:(2.0,0.9,0.0), 0.75:(2.0,1.6,0.2), 1.0:(2.0,1.96,1.5)}, 
                    loop=True, 
                    offset=delay
                )
                bs.animate_array(mchar, 'input1', 3, {0.0: (curr_x,0,0), 0.5: (curr_x,0.05,0), 1.0: (curr_x,0,0)}, loop=True, offset=delay)

            elif anim_id == 18: #navy #turquoise #amethyst #seafoam #iceblue + wave
                bs.animate_array(
                    char_node, 
                    'color', 
                    3, 
                    {0.0:(0.0,0.4,1.0), 0.25:(0.4,1.0,1.4), 0.5:(1.0,0.0,1.0), 0.75:(0.2,1.4,1.2), 1.0:(1.4,1.8,2.0)}, 
                    loop=True, 
                    offset=delay
                )
                bs.animate_array(mchar, 'input1', 3, {0.0: (curr_x,0,0), 0.5: (curr_x,0.08,0), 1.0: (curr_x,0,0)}, loop=True, offset=delay)


            elif anim_id == 19:#multicolor
                char_node.color = _random_color()
                _animate_letter_color(char_node)

            elif anim_id == 20: #multicolor + wave
                char_node.color = _random_color()
                _animate_letter_color(char_node)
                bs.animate_array(mchar, 'input1', 3, {0.0: (curr_x,0,0), 0.5: (curr_x,0.08,0), 1.0: (curr_x,0,0)}, loop=True, offset=delay)

            ''' 
            if anim_id == 2:
                bs.animate_array(char_node, 'color', 3, {0.0: (1,0,0), 0.5: (1,1,0), 1.0: (1,0,0)}, loop=True, offset=delay)
                bs.animate_array(mchar, 'input1', 3, {0.0: (curr_x,0,0), 0.5: (curr_x,0.08,0), 1.0: (curr_x,0,0)}, loop=True, offset=delay)
            elif anim_id == 3:
                bs.animate(char_node, 'opacity', {0.0: 0.3, 0.5: 1.0, 1.0: 0.3}, loop=True, offset=delay)
            elif anim_id == 4:
                bs.animate(char_node, 'opacity', {0.0: 1.0, 0.2: 0.0, 0.4: 1.0}, loop=True, offset=delay)

            elif anim_id == 6:
                bs.animate_array(char_node, 'color', 3, {0.0: (1,0,0), 0.2: (0,1,0), 0.4: (0,0,1), 0.6: (1,1,0), 0.8: (0,1,1), 1.0: (1,0,0)}, loop=True, offset=delay)
            elif anim_id == 7:
                bs.animate_array(char_node, 'color', 3, {0.0: (1,0.8,0), 0.2: (1,1,0.6), 0.4: (1,0.8,0)}, loop=True, offset=delay)
            elif anim_id == 8:
                bs.animate_array(char_node, 'color', 3, {0.0: char_col, 0.5: (1,1,1), 1.0: char_col}, loop=True, offset=delay)
            elif anim_id == 9:
                bs.animate_array(mchar, 'input1', 3, {0.0: (curr_x,0,0), 0.5: (curr_x,0.15,0), 1.0: (curr_x,0,0)}, loop=True, offset=delay)
            elif anim_id == 10:
                idx_ratio = i / total_chars
                base_color = (1.0,0.5,0.0) if idx_ratio < 0.33 else (1.0,1.0,1.0) if idx_ratio < 0.66 else (0.0,0.5,0.0)
                bs.animate_array(char_node, 'color', 3, {0.0: base_color, 0.5: (0.0,0.0,0.5), 1.0: base_color}, loop=True, offset=delay)
            elif anim_id == 11:
                bs.animate_array(char_node, 'color', 3, {0.0: (1,0,0), 0.25: (1,1,1), 0.5: (0,0,1), 0.75: (0,0.8,1), 1.0: (1,0,0)}, loop=True, offset=delay)
                bs.animate_array(mchar, 'input1', 3, {0.0: (curr_x,0,0), 0.5: (curr_x,0.05,0), 1.0: (curr_x,0,0)}, loop=True, offset=delay)
            elif anim_id == 12:
                bs.animate_array(char_node, 'color', 3, {0.0: (1,1,1), 0.49: (1,1,1), 0.5: (1,1,0), 0.99: (1,1,0), 1.0: (1,1,1)}, loop=True, offset=delay)
                bs.animate_array(mchar, 'input1', 3, {0.0: (curr_x,0,0), 0.5: (curr_x,0.05,0), 1.0: (curr_x,0,0)}, loop=True, offset=delay)'''

        if anim_id == 21:
            self._apply_wave_shimmer((0.0039, 0.9922, 0.9647), (0.9608, 0.5216, 0.2863), (0.0, 0.8, 0.4))


    def _apply_wave_shimmer(self, color_1, color_2, color_3):
        WAVE_COLOR_1, WAVE_COLOR_2, WAVE_COLOR_3 = color_1, color_2, color_3
        WAVE_PERIOD, WAVE_DELAY, TICK_MS = 2.5, 0.08, 50

        t = {'v': 0.0}
        def _tick():
            try:
                t['v'] = (t['v'] + TICK_MS / 1000.0) % max(0.5, WAVE_PERIOD)
                for char_node, idx, _, _ in self._char_nodes:
                    phase = ((t['v'] + idx * WAVE_DELAY) % WAVE_PERIOD) / WAVE_PERIOD
                    if phase < 1/3:
                        u = phase * 3
                        c1, c2 = WAVE_COLOR_1, WAVE_COLOR_2
                    elif phase < 2/3:
                        u = (phase - 1/3) * 3
                        c1, c2 = WAVE_COLOR_2, WAVE_COLOR_3
                    else:
                        u = (phase - 2/3) * 3
                        c1, c2 = WAVE_COLOR_3, WAVE_COLOR_1
                    char_node.color = tuple(c1[k] + (c2[k]-c1[k])*u for k in range(3))
            except Exception:
                pass
        self._color_timer = bs.Timer(TICK_MS / 1000.0, babase.Call(_tick), repeat=True)


class Rank:
    def __init__(self, owner=None, rank=99):
        self.node = owner
        mnode = bs.newnode('math', owner=self.node, attrs={'input1': (0, 1.2, 0), 'operation': 'add'})
        self.node.connectattr('torso_position', mnode, 'input2')

        if rank in [1, 2, 3]:
            rank = '\ue01f' + "#" + str(rank) + '\ue01f'
        else:
            rank = "#" + str(rank)

        self.rank_text = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': rank,
                'in_world': True,
                'shadow': 1.0,
                'flatness': 1.0,
                'color': (1, 1, 1),
                'scale': 0.01,
                'h_align': 'center'
            }
        )
        mnode.connectattr('output', self.rank_text, 'position')

        # Shimmer the rank color strictly between #ff0185 and #01faff
        try:
            color_a = (1.0, 0.0039, 0.5216)   # #ff0185
            color_b = (0.0039, 0.9804, 1.0)   # #01faff
            bs.animate_array(
                self.rank_text,
                'color',
                3,
                {
                    0.0: color_a,
                    1.25: color_b,
                    2.5: color_a,
                },
                loop=True,
            )
        except Exception:
            # Fallback to first color if animation not available
            try:
                self.rank_text.color = color_a
            except Exception:
                pass


class HitPoint:
    def __init__(self, position=(0, 1.5, 0), owner=None, prefix='0', shad=1.2):
        self.position = position
        self.node = owner
        m = bs.newnode('math', owner=self.node, attrs={'input1': self.position, 'operation': 'add'})
        self.node.connectattr('torso_position', m, 'input2')

        prefix = int(prefix) / 10
        preFix = u"\ue047" + str(prefix) + u"\ue047"

        self._Text = bs.newnode(
            'text',
            owner=self.node,
            attrs={
                'text': preFix,
                'in_world': True,
                'shadow': shad,
                'flatness': 1.0,
                'color': (1, 1, 1) if int(prefix) >= 20 else (1.0, 0.2, 0.2),
                'scale': 0.01,
                'h_align': 'center'
            }
        )
        m.connectattr('output', self._Text, 'position')

        def a():
            self._Text.delete()
            m.delete()

        self.timer = bs.Timer(0.1, babase.Call(a))
