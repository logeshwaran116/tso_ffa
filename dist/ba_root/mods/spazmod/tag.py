import setting
from playersdata import pdata
from tools import coins
from stats import mystats
import babase
import bascenev1 as bs
import math
from _bascenev1 import get_client_ping as _get_ping

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

    # Priority 1: temporary paid tag from coins
    paid_tag = coins.get_active_tag(account_id)
    if paid_tag:
        tag = paid_tag
    elif account_id in customtag:
        tag = customtag[account_id]
    elif p_roles != []:
        for role in roles:
            if role in p_roles:
                tag = roles[role]['tag']
                col = (0.7, 0.7, 0.7) if 'tagcolor' not in roles[role] else roles[role]['tagcolor']
                break

    if tag:
        Tag(node, tag, col)
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
    def __init__(self, owner=None, tag="something", col=(1, 1, 1)):
        self.node = owner
        self.tag = self._replace_codes(tag)
        self._char_nodes = []

        # Position math node
        self.base = bs.newnode('math', owner=self.node, attrs={'input1': (0, 1.5, 0), 'operation': 'add'})
        self.node.connectattr('torso_position', self.base, 'input2')

        # Process tag text and create shimmer effect
        self._make_shimmer_text(self.tag, col)

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

    def _make_shimmer_text(self, tag_text, base_color):
        TAG_SCALE = 0.01
        TAG_SPACING = 0.15
        ENABLE_TAG_ANIM = sett["enableTagAnimation"]
        WAVE_COLOR_1 = (2, 0, 2)  # Purple
        WAVE_COLOR_2 = (0, 2, 2)  # Cyan
        WAVE_COLOR_3 = (2, 2, 0)  # Yellow
        WAVE_PERIOD = 2.5
        WAVE_DELAY = 0.08
        TICK_MS = 50

        n = max(1, len(tag_text))
        center_index = (n - 1) * 0.5

        for i, ch in enumerate(tag_text):
            char_node = bs.newnode(
                'text',
                owner=self.node,
                attrs={
                    'text': ch,
                    'in_world': True,
                    'shadow': 1.0,
                    'flatness': 1.0,
                    'color': tuple(base_color),
                    'scale': TAG_SCALE,
                    'h_align': 'center'
                }
            )

            dx = TAG_SPACING * (i - center_index)
            mchar = bs.newnode(
                'math',
                owner=self.node,
                attrs={'input1': (dx, 0.0, 0.0), 'operation': 'add'}
            )
            self.base.connectattr('output', mchar, 'input2')
            mchar.connectattr('output', char_node, 'position')
            self._char_nodes.append((char_node, i))

        # One-time per-respawn fade-in (staggered) similar to top message text.
        try:
            # Slow, staggered reveal per character.
            base_delay = 0.0
            step = 0.12
            for idx, (cnode, _) in enumerate(self._char_nodes):
                try:
                    cnode.opacity = 0.0
                except Exception:
                    pass

                def _reveal(n=cnode):
                    try:
                        # Slower fade: take ~0.75s to fade in each character.
                        bs.animate(n, 'opacity', {0.0: 0.0, 0.75: 1.0})
                    except Exception:
                        pass

                bs.apptimer(base_delay + idx * step, _reveal)
        except Exception:
            pass

        if ENABLE_TAG_ANIM:
            t = {'v': 0.0}

            def _tick():
                try:
                    t['v'] = (t['v'] + TICK_MS / 1000.0) % max(0.5, WAVE_PERIOD)
                    for char_node, idx in self._char_nodes:
                        local_time = (t['v'] + idx * WAVE_DELAY) % WAVE_PERIOD
                        phase = local_time / WAVE_PERIOD

                        if phase < 1/3:
                            u = phase * 3
                            r = WAVE_COLOR_1[0] + (WAVE_COLOR_2[0] - WAVE_COLOR_1[0]) * u
                            g = WAVE_COLOR_1[1] + (WAVE_COLOR_2[1] - WAVE_COLOR_1[1]) * u
                            b = WAVE_COLOR_1[2] + (WAVE_COLOR_2[2] - WAVE_COLOR_1[2]) * u
                        elif phase < 2/3:
                            u = (phase - 1/3) * 3
                            r = WAVE_COLOR_2[0] + (WAVE_COLOR_3[0] - WAVE_COLOR_2[0]) * u
                            g = WAVE_COLOR_2[1] + (WAVE_COLOR_3[1] - WAVE_COLOR_2[1]) * u
                            b = WAVE_COLOR_2[2] + (WAVE_COLOR_3[2] - WAVE_COLOR_2[2]) * u
                        else:
                            u = (phase - 2/3) * 3
                            r = WAVE_COLOR_3[0] + (WAVE_COLOR_1[0] - WAVE_COLOR_3[0]) * u
                            g = WAVE_COLOR_3[1] + (WAVE_COLOR_1[1] - WAVE_COLOR_3[1]) * u
                            b = WAVE_COLOR_3[2] + (WAVE_COLOR_1[2] - WAVE_COLOR_3[2]) * u

                        char_node.color = (r, g, b)
                except:
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
