# Released under the MIT License. See LICENSE for details.

""" TODO need to set coordinates of text node , move timer values to settings.json """

import random
import math

import _babase
import setting
from stats import mystats

import babase
import bascenev1 as bs

setti = setting.get_settings_data()


class textonmap:

    def __init__(self):
        data = setti['textonmap']
        left = data['bottom left watermark']
        top = data['top watermark']  # This is the text that will be displayed
        nextMap = ""
        try:
            nextMap = bs.get_foreground_host_session().get_next_game_description().evaluate()
        except:
            pass
        try:
            top = top.replace("@IP", _babase.our_ip).replace("@PORT",
                                                             str(_babase.our_port))
        except:
            pass
        self.index = 0
        self.highlights = data['center highlights']["msg"]
        self.left_watermark(left)
        self.top_message(top)  # Pass the top message text here
        self.nextGame(nextMap)
        self.restart_msg()
        if hasattr(_babase, "season_ends_in_days"):
            if _babase.season_ends_in_days < 100:
                self.season_reset(_babase.season_ends_in_days)
        if setti["leaderboard"]["enable"]:
            self.leaderBoard()
        self.timer = bs.timer(8, babase.Call(self.highlights_), repeat=True)

    def highlights_(self):
        if setti["textonmap"]['center highlights']["randomColor"]:
            color = ((0 + random.random() * 1.0), (0 + random.random() * 1.0),
                     (0 + random.random() * 1.0))
        else:
            color = tuple(setti["textonmap"]["center highlights"]["color"])
        node = bs.newnode('text',
                          attrs={
                              'text': self.highlights[self.index],
                              'flatness': 1.0,
                              'h_align': 'center',
                              'v_attach': 'bottom',
                              'scale': 1,
                              'position': (0, 138),
                              'color': color
                          })

        self.delt = bs.timer(7, node.delete)
        self.index = int((self.index + 1) % len(self.highlights))

    def left_watermark(self, text):
        # First text node with rainbow animation
        node = bs.newnode('text',
                          attrs={
                              'text': text,
                              'flatness': 1.0,
                              'h_align': 'left',
                              'v_attach': 'bottom',
                              'h_attach': 'left',
                              'scale': 0.7,
                              'position': (25, 95),
                              'color': (1, 1, 1)
                          })
        
        # Add the rainbow color animation
        bs.animate_array(
            node,
            "color",
            3,
            {
                0: (1, 0, 0),
                0.2: (1, 0.5, 0),
                0.4: (1, 1, 0),
                0.6: (0, 1, 0),
                0.8: (0, 1, 1),
                1.0: (1, 0, 1),
                1.2: (1, 0, 0),
            },
            loop=True,
        )
        
        # Second text node with special characters
        node = bs.newnode('text',
                          attrs={
                              'text': u'\ue043[\U0001F451] OWNER : SANJI',
                              'flatness': 1.0,
                              'h_align': 'left',
                              'v_attach': 'bottom',
                              'h_attach': 'left',
                              'scale': 0.7,
                              'position': (25, 40),
                              'color': (1, 1, 1)
                          })

    def nextGame(self, text):
        node = bs.newnode('text',
                          attrs={
                              'text': "Next : " + text,
                              'flatness': 1.0,
                              'h_align': 'right',
                              'v_attach': 'bottom',
                              'h_attach': 'right',
                              'scale': 0.7,
                              'position': (-25, 16),
                              'color': (0.5, 0.5, 0.5)
                          })

    def season_reset(self, text):
        node = bs.newnode('text',
                          attrs={
                              'text': "Season ends in: " + str(text) + " days",
                              'flatness': 1.0,
                              'h_align': 'right',
                              'v_attach': 'bottom',
                              'h_attach': 'right',
                              'scale': 0.5,
                              'position': (-25, 34),
                              'color': (0.6, 0.5, 0.7)
                          })

    def restart_msg(self):
        if hasattr(_babase, 'restart_scheduled'):
            bs.get_foreground_host_activity().restart_msg = bs.newnode(
                'text',
                attrs={
                    'text': "Server going to restart after this series.",
                    'flatness': 1.0,
                    'h_align': 'right',
                    'v_attach': 'bottom',
                    'h_attach': 'right',
                    'scale': 0.5,
                    'position': (-25, 54),
                    'color': (1, 0.5, 0.7)
                })

    def top_message(self, text):
        # Restore shimmer top text but add a gentle staggered reveal at start
        self._char_nodes = []
        self._make_shimmer_text(text, (1, 1, 1))

        # Starting animation: fade letters in one-by-one
        base_delay = 0.0
        step = 0.06
        for idx, (node, _) in enumerate(getattr(self, '_char_nodes', [])):
            try:
                node.opacity = 0.0
            except Exception:
                pass

            def _reveal(n=node):
                try:
                    bs.animate(n, 'opacity', {0.0: 0.0, 0.18: 1.0})
                except Exception:
                    pass

            bs.apptimer(base_delay + idx * step, _reveal)

        # Re-run the fade animation every 10 seconds
        if not hasattr(self, '_top_fade_timer'):
            self._top_fade_timer = bs.timer(10.0, babase.Call(self._run_top_fade_animation), repeat=True)
    
    def _make_shimmer_text(self, tag_text, base_color):
        TAG_SCALE = 1.3  # Larger scale for top message
        TAG_SPACING = 20  # More spacing for larger text
        
        # Ocean Blue & Green Combination (beautiful colors)
        WAVE_COLOR_1 = (2, 1, 0)   # Deep Blue
        WAVE_COLOR_2 = (2, 0, 0)   # Cyan
        WAVE_COLOR_3 = (2, 2, 2)   # Emerald Green
        
        # Slower wave parameters
        WAVE_PERIOD = 4.0  # Increased from 2.5 to 4.0 (slower overall wave)
        WAVE_DELAY = 0.15  # Increased from 0.08 to 0.15 (more delay between characters)
        TICK_MS = 50

        n = max(1, len(tag_text))
        center_index = (n - 1) * 0.5

        # Create underline beam once
        try:
            if not hasattr(self, '_top_underline') or not self._top_underline.exists():
                self._top_underline = bs.newnode('image', attrs={
                    'texture': bs.gettexture('circleShadow'),
                    'position': (0, -82),
                    'scale': (280, 10),
                    'color': (0.25, 0.25, 0.25),
                    'opacity': 0.0,
                    'attach': 'topCenter'
                })
        except Exception:
            pass

        self._glow_nodes = []
        for i, ch in enumerate(tag_text):
            x = TAG_SPACING * (i - center_index)
            y = -70

            # Core letter node
            char_node = bs.newnode(
                'text',
                attrs={
                    'text': ch,
                    'flatness': 1.0,
                    'h_align': 'center',
                    'v_attach': 'top',
                    'scale': TAG_SCALE,
                    'position': (x, y),
                    'color': tuple(base_color),
                    'shadow': 0.8,
                    'vr_depth': -19
                }
            )
            self._char_nodes.append((char_node, i))

            # Soft glow behind the letter
            try:
                glow_node = bs.newnode(
                    'text',
                    attrs={
                        'text': ch,
                        'flatness': 1.0,
                        'h_align': 'center',
                        'v_attach': 'top',
                        'scale': TAG_SCALE * 1.15,
                        'position': (x, y),
                        'color': (1.0, 0.85, 0.3),
                        'shadow': 0.0,
                        'vr_depth': -21,
                        'opacity': 0.0,
                    }
                )
                self._glow_nodes.append((glow_node, i))
            except Exception:
                pass

        t = {'v': 0.0}

        def _tick():
            try:
                t['v'] = (t['v'] + TICK_MS / 1000.0) % max(0.5, WAVE_PERIOD)
                for idx, pair in enumerate(self._char_nodes):
                    char_node, _ = pair
                    if not char_node.exists():
                        continue
                        
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

                    # Subtle scale pulse
                    try:
                        pulse = 1.0 + 0.03 * math.sin(phase * 2.0 * math.pi)
                        char_node.scale = TAG_SCALE * pulse
                    except Exception:
                        pass

                # Animate glow opacity in sync
                try:
                    for idx, pair in enumerate(getattr(self, '_glow_nodes', [])):
                        glow_node, _ = pair
                        if not glow_node.exists():
                            continue
                        local_time = (t['v'] + idx * WAVE_DELAY) % WAVE_PERIOD
                        phase = local_time / WAVE_PERIOD
                        glow = 0.12 + 0.20 * max(0.0, math.sin(phase * 2.0 * math.pi))
                        glow_node.opacity = glow
                except Exception:
                    pass

                # Underline gentle pulse
                try:
                    if hasattr(self, '_top_underline') and self._top_underline.exists():
                        self._top_underline.opacity = 0.10 + 0.08 * (0.5 + 0.5 * math.sin(t['v'] * 2.0 * math.pi / WAVE_PERIOD))
                except Exception:
                    pass
            except:
                pass

        self._color_timer = bs.Timer(TICK_MS / 1000.0, babase.Call(_tick), repeat=True)

    def _run_top_fade_animation(self):
        # Safely re-apply per-letter fade on the existing top-message nodes
        try:
            nodes = getattr(self, '_char_nodes', [])
            if not nodes:
                return
            step = 0.06
            for idx, (node, _) in enumerate(nodes):
                try:
                    if not node.exists():
                        continue
                    node.opacity = 0.0
                except Exception:
                    continue

                def _reveal(n=node):
                    try:
                        bs.animate(n, 'opacity', {0.0: 0.0, 0.18: 1.0})
                    except Exception:
                        pass

                bs.apptimer(idx * step, _reveal)
        except Exception:
            pass

    def leaderBoard(self):
        if len(mystats.top5Name) > 2:
            self._create_shimmer_leaderboard()

    def _create_shimmer_leaderboard(self):
        """Create shimmer effect for leaderboard names; keep original positions.
        Slightly trim/pad names for a neater alignment without moving anchors.
        """
        def tidy(name: str, maxlen: int = 12) -> str:
            return (name[:maxlen] + "...") if len(name) > maxlen else name

        names = [
            "#1 " + tidy(mystats.top5Name[0] if len(mystats.top5Name) > 0 else "-"),
            "#2 " + tidy(mystats.top5Name[1] if len(mystats.top5Name) > 1 else "-"),
            "#3 " + tidy(mystats.top5Name[2] if len(mystats.top5Name) > 2 else "-")
        ]

        # Preserve original anchor positions
        positions = [(-140, -90), (-140, -125), (-140, -160)]
        base_colors = [(0.7, 0.4, 0.3), (0.8, 0.8, 0.8), (0.2, 0.6, 0.2)]

        self._leaderboard_nodes = []

        for i, (name, pos, base_color) in enumerate(zip(names, positions, base_colors)):
            self._make_leaderboard_shimmer_text(name, pos, base_color, i)

    def _make_leaderboard_shimmer_text(self, text, position, base_color, index):
        """Create shimmer text effect for leaderboard names"""
        TAG_SCALE = 0.8
        TAG_SPACING = 11
        
        # Different color waves for different positions
        if index == 0:  # 1st place - Gold theme
            WAVE_COLOR_1 = (1.0, 0.5, 0.0)   # Orange
            WAVE_COLOR_2 = (1.0, 0.8, 0.0)   # Yellow
            WAVE_COLOR_3 = (1.0, 0.9, 0.4)   # Light Yellow
        elif index == 1:  # 2nd place - Silver theme
            WAVE_COLOR_1 = (0.7, 0.7, 0.7)   # Gray
            WAVE_COLOR_2 = (0.9, 0.9, 0.9)   # Light Gray  
            WAVE_COLOR_3 = (0.8, 0.8, 1.0)   # Bluish Gray
        else:  # 3rd place - Bronze theme
            WAVE_COLOR_1 = (0.7, 0.4, 0.2)   # Brown
            WAVE_COLOR_2 = (0.8, 0.5, 0.3)   # Light Brown
            WAVE_COLOR_3 = (0.9, 0.6, 0.4)   # Orange Brown
        
        WAVE_PERIOD = 3.0
        WAVE_DELAY = 0.1
        TICK_MS = 50

        n = max(1, len(text))
        center_index = (n - 1) * 0.5

        char_nodes = []
        for i, ch in enumerate(text):
            char_node = bs.newnode(
                'text',
                attrs={
                    'text': ch,
                    'flatness': 1.0,
                    'h_align': 'left',
                    'h_attach': 'right',
                    'v_attach': 'top', 
                    'v_align': 'center',
                    'scale': TAG_SCALE,
                    'position': (position[0] + TAG_SPACING * (i - center_index), position[1]),
                    'color': tuple(base_color),
                    'shadow': 0.5,
                    'vr_depth': -10
                }
            )
            char_nodes.append((char_node, i))

        t = {'v': 0.0}

        def _tick():
            try:
                t['v'] = (t['v'] + TICK_MS / 1000.0) % max(0.5, WAVE_PERIOD)
                for char_node, idx in char_nodes:
                    if not char_node.exists():
                        continue
                        
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

        # Store the timer to keep it alive
        timer = bs.Timer(TICK_MS / 1000.0, babase.Call(_tick), repeat=True)
        self._leaderboard_nodes.append((char_nodes, timer))