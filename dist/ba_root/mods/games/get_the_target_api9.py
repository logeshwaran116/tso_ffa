# Made by Froshlee14
# Updated to API 9 by Sydney
# ba_meta require api 9

from __future__ import annotations

from typing import TYPE_CHECKING

import bascenev1 as bs
import random

from bascenev1lib.actor.scoreboard import Scoreboard
from bascenev1lib.actor.playerspaz import PlayerSpaz

if TYPE_CHECKING:
    from typing import Any, Union, Type, List, Sequence, Optional


class Player(bs.Player['Team']):
    """Our player type for this game."""


class Team(bs.Team[Player]):
    """Our team type for this game."""

    def __init__(self) -> None:
        self.score = 0


# ba_meta export bascenev1.GameActivity
class GetTheTargetGame(bs.TeamGameActivity[Player, Team]):
    name = 'Get the Target'
    description = (
        'Kill target to get points (dont kill if teammate). If you\'re \n'
        'the Target, survive to get points, \nplayer/team that reached the\n'
        ' required points, wins.'
    )
    announce_player_deaths = True

    @classmethod
    def get_available_settings(
            cls, sessiontype: Type[bs.Session]) -> List[bs.Setting]:
        settings = [
            bs.IntSetting('Points to Win Per Player', min_value=1, default=5, increment=1),
            bs.IntSetting('Time to Kill', min_value=5, max_value=30, default=10, increment=1),
            bs.IntChoiceSetting('Time Limit', choices=[
                ('None', 0), ('1 Minute', 60), ('2 Minutes', 120),
                ('5 Minutes', 300), ('10 Minutes', 600), ('20 Minutes', 1200)
            ], default=0),
            bs.FloatChoiceSetting('Respawn Times', choices=[
                ('Shorter', 0.25), ('Short', 0.5), ('Normal', 1.0),
                ('Long', 2.0), ('Longer', 4.0)
            ], default=1.0),
            bs.BoolSetting('Epic Mode', default=False),
        ]
        return settings

    @classmethod
    def supports_session_type(cls, sessiontype: Type[bs.Session]) -> bool:
        return (issubclass(sessiontype, bs.DualTeamSession)
                or issubclass(sessiontype, bs.FreeForAllSession))

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> List[str]:
        assert bs.app.classic is not None
        return bs.app.classic.getmaps('melee')

    def __init__(self, settings: dict) -> None:
        super().__init__(settings)
        self._settings = settings
        if self._settings['Epic Mode']:
            self.slow_motion = True
        self._chosed_player: Optional[Player] = None
        self._score_to_win: Optional[int] = None
        self._dingsound = bs.getsound('dingSmall')
        self._chosing_sound = bs.getsound('scoreIncrease')
        self._chosed_sound = bs.getsound('cashRegister2')
        self._error_sound = bs.getsound('error')
        self._tick_sound = bs.getsound('tick')
        self._time_remaining = int(self._settings['Time to Kill'])
        self._time_limit = float(settings['Time Limit'])
        self._scoreboard = Scoreboard()
        self._chose_text: Optional[bs.Node] = None
        self._image: Optional[bs.NodeActor] = None
        self._name: Optional[bs.NodeActor] = None
        self._sound: Optional[bs.NodeActor] = None
        self._logo_effect: Optional[bs.Timer] = None
        self._timer_x: Optional[bs.Timer] = None
        self._time: Optional[bs.NodeActor] = None

        self.default_music = (bs.MusicType.EPIC if self.slow_motion
                              else bs.MusicType.TO_THE_DEATH)

    def get_instance_description(self) -> Union[str, Sequence]:
        return 'Kill enemy targets or Survive ${ARG1} times.', self._score_to_win

    def get_instance_scoreboard_display_string(self) -> str:
        return 'Kill target/Survive ' + str(self._score_to_win) + ' times.'

    def on_team_join(self, team: Team) -> None:
        if self.has_begun():
            self._update_scoreboard()

    def on_begin(self) -> None:
        super().on_begin()
        self.setup_standard_time_limit(self._time_limit)
        self.setup_standard_powerup_drops()
        self._score_to_win = (int(self._settings['Points to Win Per Player']) *
                              max(1, max(len(t.players) for t in self.teams)))
        self._update_scoreboard()
        bs.timer(3.0, self.star_chosing_player)

        self._chose_text = bs.newnode('text', attrs={
            'text': ' ',
            'v_attach': 'bottom',
            'h_attach': 'center',
            'h_align': 'center',
            'v_align': 'center',
            'maxwidth': 150,
            'shadow': 1.0,
            'flatness': 1.0,
            'color': (1, 1, 1),
            'scale': 1,
            'position': (0, 155),
        })

    def on_player_leave(self, player: Player) -> None:
        super().on_player_leave(player)
        if len(self.players) in [0, 1]:
            self.end_game()
        if player == self._chosed_player:
            self.star_chosing_player()

    def get_randomplayer(self) -> List[Player]:
        return list(self.players)

    def print_random_icon(self) -> Player:
        player = random.choice(self.get_randomplayer())
        icon = player.get_icon()

        outline_tex = bs.gettexture('characterIconMask')
        texture = icon['texture']
        self._image = bs.NodeActor(bs.newnode('image', attrs={
            'texture': texture,
            'tint_texture': icon['tint_texture'],
            'tint_color': icon['tint_color'],
            'tint2_color': icon['tint2_color'],
            'mask_texture': outline_tex,
            'position': (0, 80),
            'scale': (100, 100),
            'opacity': 1.0,
            'absolute_scale': True,
            'attach': 'bottomCenter',
        }))
        self._name = bs.NodeActor(bs.newnode('text', attrs={
            'v_attach': 'bottom',
            'h_attach': 'center',
            'text': bs.Lstr(value=player.getname()),
            'maxwidth': 100,
            'h_align': 'center',
            'v_align': 'center',
            'shadow': 1.0,
            'flatness': 1.0,
            'color': bs.safecolor(icon['tint_color']),
            'scale': 1,
            'position': (0, 20),
        }))
        return player

    def star_chosing_player(self) -> None:
        if len(self.players) in [0, 1]:
            self.end_game()
        self.stop_timer()
        self._chosed_player = None
        self._sound = bs.NodeActor(bs.newnode('sound', attrs={
            'sound': self._chosing_sound,
            'volume': 1.0,
        }))
        self._logo_effect = bs.Timer(0.08, bs.WeakCall(self.print_random_icon), repeat=True)
        bs.timer(3.0, bs.WeakCall(self.stopn_chose_player))
        if self._chose_text:
            self._chose_text.text = 'Chosing Player...'
            self._chose_text.color = (1, 1, 1)

    def stopn_chose_player(self) -> None:
        self._sound = None
        self._logo_effect = None
        self._chosed_sound.play()
        player = self.print_random_icon()
        self._chosed_player = player
        if self._chose_text:
            self._chose_text.text = 'Kill the Enemy!'
            self._chose_text.color = (1, 1, 0)
        self.start_timer()

    def start_timer(self) -> None:
        self._time_remaining = self._settings['Time to Kill']
        self._timer_x = bs.Timer(1.0, bs.WeakCall(self.tick), repeat=True)

    def stop_timer(self) -> None:
        self._time = None
        self._timer_x = None

    def tick(self) -> None:
        self.check_for_expire()
        self._time = bs.NodeActor(bs.newnode('text', attrs={
            'v_attach': 'top',
            'h_attach': 'center',
            'text': 'Kill Time: ' + str(self._time_remaining) + 's',
            'opacity': 0.8,
            'maxwidth': 100,
            'h_align': 'center',
            'v_align': 'center',
            'shadow': 1.0,
            'flatness': 1.0,
            'color': (1, 1, 1),
            'scale': 1.2,
            'position': (0, -50),
        }))
        self._time_remaining -= 1
        self._tick_sound.play()

    def check_for_expire(self) -> None:
        if self._time_remaining <= 0:
            self.stop_timer()
            if len(self.players) == 0:
                pass
            elif self._chosed_player is not None and self._chosed_player.is_alive():
                player = self._chosed_player
                player.team.score += 1
                self._dingsound.play()
                if any(team.score >= self._score_to_win for team in self.teams):
                    bs.timer(0.5, self.end_game)
                if self._chose_text:
                    self._chose_text.text = 'Survived!'
                    self._chose_text.color = (0, 1, 0)
            bs.timer(0.6, bs.WeakCall(self.star_chosing_player))

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            super().handlemessage(msg)
            player = msg.getplayer(Player)
            self.respawn_player(player)

            killer = msg.getkillerplayer(Player)
            assert self._score_to_win is not None

            if player == self._chosed_player:
                if killer is None:
                    pass
                elif killer.team is player.team:
                    if isinstance(self.session, bs.FreeForAllSession):
                        player.team.score = max(0, player.team.score - 1)
                    else:
                        self._dingsound.play()
                        for team in self.teams:
                            if team is not killer.team:
                                team.score += 1
                else:
                    killer.team.score += 1
                    self._dingsound.play()
                    try:
                        killer.actor.set_score_text(
                            str(killer.team.score) + '/' + str(self._score_to_win),
                            color=killer.team.color,
                            flash=True,
                        )
                    except Exception:
                        pass

                self._update_scoreboard()
                if any(team.score >= self._score_to_win for team in self.teams):
                    bs.timer(0.5, self.end_game)

                if self._chose_text:
                    if killer is not None and killer != self._chosed_player:
                        self._chose_text.text = 'Killed!'
                        self._chose_text.color = (1, 0.5, 0)
                    else:
                        self._chose_text.text = 'Dead!'
                        self._chose_text.color = (1.0, 0, 0)
                        self._error_sound.play()

                bs.timer(0.6, bs.WeakCall(self.star_chosing_player))

        else:
            super().handlemessage(msg)

    def _update_scoreboard(self) -> None:
        for team in self.teams:
            self._scoreboard.set_team_value(team, team.score, self._score_to_win)

    def end_game(self) -> None:
        results = bs.GameResults()
        for team in self.teams:
            results.set_team_score(team, team.score)
        self.end(results=results)
