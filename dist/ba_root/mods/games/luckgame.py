# ba_meta require api 9
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import random
import babase
import bascenev1 as bs
from bascenev1lib.actor.bomb import Bomb

if TYPE_CHECKING:
    from typing import Any, Type, List


class Player(bs.Player['Team']):
    pass


class Team(bs.Team[Player]):
    pass


# ba_meta export bascenev1.GameActivity
class LuckGame(bs.TeamGameActivity[Player, Team]):
    """Luck-based survival: floater drops impact bombs; last team alive wins."""

    name = 'luckgame'
    description = 'A floating dropper rains impact bombs; last team alive wins.'
    announce_player_deaths = True
    allow_mid_activity_joins = False

    @classmethod
    def get_available_settings(cls, sessiontype: Type[bs.Session]) -> list[babase.Setting]:
        return [
            bs.IntChoiceSetting(
                'Drop Interval',
                choices=[('Fast', 400), ('Normal', 700), ('Slow', 1100)],
                default=700,
            )
        ]

    @classmethod
    def supports_session_type(cls, sessiontype: Type[bs.Session]) -> bool:
        return issubclass(sessiontype, bs.DualTeamSession)

    @classmethod
    def get_supported_maps(cls, sessiontype: Type[bs.Session]) -> list[str]:
        # Restrict to our wooden floor map.
        return ['Wooden Floor']

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._drop_timer: Optional[bs.Timer] = None
        self._drop_interval = max(200, int(settings.get('Drop Interval', 700))) / 1000.0
        self._bounds = None
        self._running = False

    def on_begin(self) -> None:
        super().on_begin()
        # If we somehow start with a single team, call it a draw immediately.
        if len(self.teams) <= 1:
            self._end_draw()
            return

        # Cache map bounds box for random positions.
        try:
            self._bounds = bs.get_foreground_host_activity().map.get_def_bound_box('map_bounds')
        except Exception:
            # Fallback: generic box.
            self._bounds = (-10.0, 0.5, -10.0, 10.0, 5.0, 10.0)

        # Start periodic drops.
        self._running = True
        self._schedule_next_drop()

        # Watch for victory state.
        bs.timer(0.5, self._check_victory, repeat=True)

    def _rand_point_on_floor(self) -> tuple[float, float, float]:
        # Choose a random x/z within map bounds; y slightly above floor.
        x1, y1, z1, x2, y2, z2 = self._bounds
        x = random.uniform(min(x1, x2) + 1.0, max(x1, x2) - 1.0)
        z = random.uniform(min(z1, z2) + 1.0, max(z1, z2) - 1.0)
        y = max(min(y1, y2) + 2.0, 0.8)
        return (x, y, z)

    def _do_drop(self) -> None:
        if not self._running:
            return
        pos = self._rand_point_on_floor()
        try:
            b = Bomb(position=pos, bomb_type='impact').autoretain()
            b.node.sticky = False
            b.node.gravity_scale = 1.0
            # Small random nudge so they don't all stack perfectly.
            b.node.velocity = (random.uniform(-0.2, 0.2), -0.1, random.uniform(-0.2, 0.2))
        except Exception:
            pass
        self._schedule_next_drop()

    def _schedule_next_drop(self) -> None:
        if not self._running:
            return
        self._drop_timer = bs.Timer(self._drop_interval, self._do_drop)

    def _alive_teams(self) -> list[Team]:
        alive: list[Team] = []
        for team in self.teams:
            for p in team.players:
                if p.is_alive() and getattr(p, 'actor', None) and p.actor and p.actor.is_alive():
                    alive.append(team)
                    break
        return alive

    def _check_victory(self) -> None:
        if not self._running:
            return
        alive = self._alive_teams()
        # If at any time only one team remains, they win.
        unique = list(dict.fromkeys(alive))
        if len(unique) == 1:
            self._end_win(unique[0])
        elif len(unique) == 0:
            # Everyone dead: draw.
            self._end_draw()

    def _end_draw(self) -> None:
        if not self._running:
            return
        self._running = False
        self._stop_drops()
        self.end_game()

    def _end_win(self, team: Team) -> None:
        if not self._running:
            return
        self._running = False
        self._stop_drops()
        results = bs.GameResults()
        for t in self.teams:
            results.set_team_score(t, 1 if t is team else 0)
        self.end_game(results)

    def _stop_drops(self) -> None:
        try:
            if self._drop_timer is not None:
                # bs.Timer cannot be canceled; just stop scheduling.
                self._drop_timer = None
        except Exception:
            pass

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PlayerDiedMessage):
            # Allow normal death handling, then check victory.
            super().handlemessage(msg)
            bs.timer(0.01, self._check_victory)
            return bs.UNHANDLED
        return super().handlemessage(msg)
