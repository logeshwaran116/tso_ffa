from __future__ import annotations

import random
from typing import Any
import bascenev1 as bs
from bascenev1lib.actor import powerupbox as pupbox
from bascenev1lib.actor.bomb import Bomb, ImpactMessage
from bascenev1lib.actor.spaz import POWERUP_WEAR_OFF_TIME
from bascenev1lib.actor.spaz import BombDiedMessage, Spaz
from bascenev1lib.gameutils import SharedObjects
try:
    import setting
except Exception:
    setting = None  # type: ignore[assignment]

_applied = False
_original_drop_bomb = None
_original_on_punch_press = None
_original_on_pickup_press = None
_original_on_bomb_press = None
_original_handlemessage = None
_original_get_bomb_type_tex = None
_base_on_punch_press = None
_base_on_pickup_press = None
_base_on_bomb_press = None
_active_silence_zones: list["SilenceZone"] = []
_GRAVITY_BOMB_DURATION = 1.3
_GRAVITY_BOMB_SCALE = 0.0
_GRAVITY_BOMB_MIN_UP_VEL = 6.0
_GRAVITY_BOMB_IMPULSE_INTERVAL = 0.05
_GRAVITY_BOMB_RADIUS = 1.75
_CUSTOM_BOMB_MAX_COUNT = 3
_CUSTOM_BOMB_DEFAULTS = {
    "silence": {
        "enable": True,
        "spawn_from_boxes": True,
        "spawn_chance": 0.08,
    },
    "gravity": {
        "enable": True,
        "spawn_from_boxes": True,
        "spawn_chance": 0.06,
    },
}
_custom_bomb_settings = {
    name: dict(values) for name, values in _CUSTOM_BOMB_DEFAULTS.items()
}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _load_custom_bomb_settings() -> None:
    global _custom_bomb_settings
    settings_data = {
        name: dict(values) for name, values in _CUSTOM_BOMB_DEFAULTS.items()
    }
    if setting is not None:
        try:
            raw = setting.get_settings_data().get("customBombs", {})
            if isinstance(raw, dict):
                for bomb_name in ("silence", "gravity"):
                    values = raw.get(bomb_name)
                    if not isinstance(values, dict):
                        continue
                    if "enable" in values:
                        settings_data[bomb_name]["enable"] = bool(values["enable"])
                    if "spawn_from_boxes" in values:
                        settings_data[bomb_name]["spawn_from_boxes"] = bool(
                            values["spawn_from_boxes"]
                        )
                    if "spawn_chance" in values:
                        try:
                            settings_data[bomb_name]["spawn_chance"] = _clamp01(
                                float(values["spawn_chance"])
                            )
                        except Exception:
                            pass
        except Exception:
            pass
    _custom_bomb_settings = settings_data


def _custom_bomb_enabled(bomb_name: str) -> bool:
    return bool(_custom_bomb_settings.get(bomb_name, {}).get("enable", True))


def _custom_bomb_spawns_from_boxes(bomb_name: str) -> bool:
    return bool(
        _custom_bomb_settings.get(bomb_name, {}).get("spawn_from_boxes", True)
    )


def _custom_bomb_spawn_chance(bomb_name: str) -> float:
    try:
        chance = float(
            _custom_bomb_settings.get(bomb_name, {}).get("spawn_chance", 0.0)
        )
    except Exception:
        return 0.0
    return _clamp01(chance)


def _silence_powerup_texture() -> bs.Texture:
    return bs.gettexture("powerupCurse")


def _silence_spawn_box_texture() -> bs.Texture:
    return bs.gettexture("backIcon")


def _gravity_spawn_box_texture() -> bs.Texture:
    return bs.gettexture("achievementOffYouGo")


def _gravity_bomb_texture() -> bs.Texture:
    return bs.gettexture("achievementOffYouGo")


def _set_custom_bomb_count(spaz: Spaz, count: int, tex: bs.Texture) -> None:
    """Store limited custom-bomb count and show it like land-mine counters."""
    count = max(0, int(count))
    setattr(spaz, "_custom_bomb_uses_left", count)
    if not spaz.node:
        return
    try:
        if count > 0:
            spaz.node.counter_text = "x" + str(count)
            spaz.node.counter_texture = tex
        else:
            spaz.node.counter_text = ""
    except Exception:
        pass


def _get_custom_bomb_count(spaz: Spaz) -> int | None:
    raw = getattr(spaz, "_custom_bomb_uses_left", None)
    if raw is None:
        return None
    try:
        return max(0, int(raw))
    except Exception:
        return 0


def _consume_custom_bomb_count(spaz: Spaz, tex: bs.Texture) -> bool:
    """Consume one custom bomb use; returns True if now exhausted."""
    remaining = _get_custom_bomb_count(spaz)
    if remaining is None:
        return False
    remaining = max(0, remaining - 1)
    _set_custom_bomb_count(spaz, remaining, tex)
    return remaining == 0


def _revert_to_normal_bombs(spaz: Spaz) -> None:
    setattr(spaz, "_custom_bomb_uses_left", None)
    spaz.bomb_type = "normal"
    try:
        if spaz.node:
            spaz.node.counter_text = ""
    except Exception:
        pass


def _start_bomb_type_wearoff(spaz: Spaz, tex: bs.Texture) -> None:
    """Force bomb-type wear-off timer regardless of activity defaults."""
    if spaz._dead or not spaz.node:
        return
    try:
        t_ms = int(bs.time() * 1000.0)
        spaz.node.mini_billboard_2_texture = tex
        spaz.node.mini_billboard_2_start_time = t_ms
        spaz.node.mini_billboard_2_end_time = t_ms + POWERUP_WEAR_OFF_TIME
        spaz._bomb_wear_off_flash_timer = bs.Timer(
            (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
            bs.WeakCall(spaz._bomb_wear_off_flash),
        )
        spaz._bomb_wear_off_timer = bs.Timer(
            POWERUP_WEAR_OFF_TIME / 1000.0,
            bs.WeakCall(spaz._bomb_wear_off),
        )
    except Exception:
        pass


def _start_multi_bomb_wearoff(spaz: Spaz) -> None:
    """Force triple-bomb wear-off timer regardless of activity defaults."""
    if spaz._dead or not spaz.node:
        return
    try:
        tex = pupbox.PowerupBoxFactory.get().tex_bomb
        t_ms = int(bs.time() * 1000.0)
        spaz.node.mini_billboard_1_texture = tex
        spaz.node.mini_billboard_1_start_time = t_ms
        spaz.node.mini_billboard_1_end_time = t_ms + POWERUP_WEAR_OFF_TIME
        spaz._multi_bomb_wear_off_flash_timer = bs.Timer(
            (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
            bs.WeakCall(spaz._multi_bomb_wear_off_flash),
        )
        spaz._multi_bomb_wear_off_timer = bs.Timer(
            POWERUP_WEAR_OFF_TIME / 1000.0,
            bs.WeakCall(spaz._multi_bomb_wear_off),
        )
    except Exception:
        pass


def _start_gloves_wearoff(spaz: Spaz) -> None:
    """Force punch-gloves wear-off timer regardless of activity defaults."""
    if spaz._dead or not spaz.node:
        return
    try:
        tex = pupbox.PowerupBoxFactory.get().tex_punch
        t_ms = int(bs.time() * 1000.0)
        spaz.node.boxing_gloves_flashing = False
        spaz.node.mini_billboard_3_texture = tex
        spaz.node.mini_billboard_3_start_time = t_ms
        spaz.node.mini_billboard_3_end_time = t_ms + POWERUP_WEAR_OFF_TIME
        spaz._boxing_gloves_wear_off_flash_timer = bs.Timer(
            (POWERUP_WEAR_OFF_TIME - 2000) / 1000.0,
            bs.WeakCall(spaz._gloves_wear_off_flash),
        )
        spaz._boxing_gloves_wear_off_timer = bs.Timer(
            POWERUP_WEAR_OFF_TIME / 1000.0,
            bs.WeakCall(spaz._gloves_wear_off),
        )
    except Exception:
        pass


def _start_speed_wearoff(spaz: Spaz, tex: bs.Texture) -> None:
    """Force speed wear-off timer to POWERUP_WEAR_OFF_TIME."""
    if spaz._dead or not spaz.node:
        return
    try:
        t_ms = int(bs.time() * 1000.0)
        spaz.node.mini_billboard_2_texture = tex
        spaz.node.mini_billboard_2_start_time = t_ms
        spaz.node.mini_billboard_2_end_time = t_ms + POWERUP_WEAR_OFF_TIME
    except Exception:
        pass

    def _flash() -> None:
        try:
            if spaz.node and spaz.node.exists():
                spaz.node.billboard_texture = tex
                spaz.node.billboard_opacity = 1.0
                spaz.node.billboard_cross_out = True
        except Exception:
            pass

    def _wear_off() -> None:
        try:
            if spaz.node and spaz.node.exists():
                spaz.node.hockey = False
                spaz.node.billboard_opacity = 0.0
                bs.getsound("powerdown01").play()
        except Exception:
            pass

    try:
        bs.Timer((POWERUP_WEAR_OFF_TIME - 2000) / 1000.0, _flash)
        bs.Timer(POWERUP_WEAR_OFF_TIME / 1000.0, _wear_off)
    except Exception:
        pass


def _start_ice_man_wearoff(spaz: Spaz, tex: bs.Texture) -> None:
    """Force ice-man wear-off timer to POWERUP_WEAR_OFF_TIME."""
    if spaz._dead or not spaz.node:
        return
    try:
        t_ms = int(bs.time() * 1000.0)
        spaz.node.mini_billboard_2_texture = tex
        spaz.node.mini_billboard_2_start_time = t_ms
        spaz.node.mini_billboard_2_end_time = t_ms + POWERUP_WEAR_OFF_TIME
    except Exception:
        pass

    def _flash() -> None:
        try:
            if spaz.node and spaz.node.exists():
                spaz.node.billboard_texture = tex
                spaz.node.billboard_opacity = 1.0
                spaz.node.billboard_cross_out = True
        except Exception:
            pass

    def _wear_off() -> None:
        try:
            if spaz.node and spaz.node.exists():
                previous_bomb = None
                bmb_color = getattr(spaz, "bmb_color", None)
                if isinstance(bmb_color, list) and bmb_color:
                    previous_bomb = bmb_color[0]
                if previous_bomb and previous_bomb != "ice_bubble":
                    spaz.bomb_type = previous_bomb
                else:
                    spaz.bomb_type = "normal"
                setattr(spaz, "freeze_punch", False)
                spaz.node.billboard_opacity = 0.0
                bs.getsound("powerdown01").play()
        except Exception:
            pass

    try:
        bs.Timer((POWERUP_WEAR_OFF_TIME - 2000) / 1000.0, _flash)
        bs.Timer(POWERUP_WEAR_OFF_TIME / 1000.0, _wear_off)
    except Exception:
        pass


def _apply_gravity_bomb_effect(spaz: Spaz) -> None:
    """Temporarily remove gravity from a touched player."""
    if spaz.node is None or not spaz.node.exists() or not spaz.is_alive():
        return

    def _push_up() -> None:
        if spaz.node is None or not spaz.node.exists():
            return
        try:
            p = spaz.node.position
            spaz.node.handlemessage(
                "impulse",
                p[0],
                p[1] + 0.5,
                p[2],
                0,
                5,
                0,
                3,
                10,
                0,
                0,
                0,
                5,
                0,
            )
        except Exception:
            try:
                velocity = spaz.node.velocity
                spaz.node.velocity = (
                    velocity[0],
                    max(velocity[1], _GRAVITY_BOMB_MIN_UP_VEL),
                    velocity[2],
                )
            except Exception:
                pass

    now = bs.time()
    previous_end = float(getattr(spaz, "_gravity_bomb_end_time", 0.0))
    if previous_end <= now:
        try:
            setattr(spaz, "_gravity_bomb_saved_scale", float(spaz.node.gravity_scale))
        except Exception:
            setattr(spaz, "_gravity_bomb_saved_scale", 1.0)

    setattr(
        spaz,
        "_gravity_bomb_end_time",
        max(previous_end, now + _GRAVITY_BOMB_DURATION),
    )

    try:
        spaz.node.gravity_scale = _GRAVITY_BOMB_SCALE
    except Exception:
        pass
    _push_up()

    if getattr(spaz, "_gravity_bomb_timer_running", False):
        return
    setattr(spaz, "_gravity_bomb_timer_running", True)

    def _tick() -> None:
        try:
            if spaz.node is None or not spaz.node.exists() or not spaz.is_alive():
                setattr(spaz, "_gravity_bomb_timer_running", False)
                return

            end_time = float(getattr(spaz, "_gravity_bomb_end_time", 0.0))
            if bs.time() >= end_time:
                saved_scale = float(getattr(spaz, "_gravity_bomb_saved_scale", 1.0))
                spaz.node.gravity_scale = saved_scale
                setattr(spaz, "_gravity_bomb_end_time", 0.0)
                setattr(spaz, "_gravity_bomb_timer_running", False)
                return
            try:
                spaz.node.gravity_scale = _GRAVITY_BOMB_SCALE
            except Exception:
                pass
            _push_up()
        except Exception:
            setattr(spaz, "_gravity_bomb_timer_running", False)
            return
        bs.timer(_GRAVITY_BOMB_IMPULSE_INTERVAL, _tick)

    bs.timer(_GRAVITY_BOMB_IMPULSE_INTERVAL, _tick)


def _apply_powerup_patches() -> None:
    # Patch whichever PowerupBoxFactory class is currently active
    # (base game or plugin-replaced one).
    factory_cls = pupbox.PowerupBoxFactory
    current_get_random = factory_cls.get_random_powerup_type
    if not getattr(current_get_random, "_silence_patch", False):
        original_get_random = current_get_random

        def _patched_get_random_powerup_type(
            self, forcetype=None, excludetypes=None
        ):
            force = forcetype
            if force in ("silence", "silence_bombs"):
                if _custom_bomb_enabled("silence"):
                    return "silence_bombs"
                force = "impact_bombs"
            elif force in ("gravity", "gravity_bombs"):
                if _custom_bomb_enabled("gravity"):
                    return "gravity_bombs"
                force = "impact_bombs"
            excluded = [] if excludetypes is None else list(excludetypes)
            if force is None:
                if (
                    _custom_bomb_enabled("silence")
                    and _custom_bomb_spawns_from_boxes("silence")
                    and "silence_bombs" not in excluded
                    and random.random() < _custom_bomb_spawn_chance("silence")
                ):
                    return "silence_bombs"
                if (
                    _custom_bomb_enabled("gravity")
                    and _custom_bomb_spawns_from_boxes("gravity")
                    and "gravity_bombs" not in excluded
                    and random.random() < _custom_bomb_spawn_chance("gravity")
                ):
                    return "gravity_bombs"
            try:
                return original_get_random(
                    self, forcetype=force, excludetypes=excludetypes
                )
            except TypeError:
                return original_get_random(self, force, excludetypes)

        _patched_get_random_powerup_type._silence_patch = True  # type: ignore[attr-defined]
        factory_cls.get_random_powerup_type = _patched_get_random_powerup_type

    # Patch PowerupBox init so custom silence type behaves like built-ins.
    current_pbx_init = pupbox.PowerupBox.__init__
    if not getattr(current_pbx_init, "_silence_patch", False):
        original_pbx_init = current_pbx_init

        def _patched_pbx_init(
            self,
            position: tuple[float, float, float] = (0.0, 1.0, 0.0),
            poweruptype: str = "triple_bombs",
            expire: bool = True,
        ):
            wants_silence = (
                poweruptype in ("silence", "silence_bombs")
                and _custom_bomb_enabled("silence")
            )
            wants_gravity = (
                poweruptype in ("gravity", "gravity_bombs")
                and _custom_bomb_enabled("gravity")
            )
            wrapped_type = poweruptype
            if poweruptype in (
                "silence",
                "silence_bombs",
                "gravity",
                "gravity_bombs",
            ):
                wrapped_type = "impact_bombs"
            try:
                original_pbx_init(
                    self, position=position, poweruptype=wrapped_type, expire=expire
                )
            except TypeError:
                original_pbx_init(self, position, wrapped_type, expire)

            if wants_silence:
                self.poweruptype = "silence_bombs"
                try:
                    if self.node and self.node.exists():
                        self.node.color_texture = _silence_spawn_box_texture()
                except Exception:
                    pass
                # Plugin powerup-name labels, if present.
                try:
                    texts = getattr(self, "texts", None)
                    if isinstance(texts, dict) and "Name" in texts:
                        texts["Name"].text = "Silence Bombs"
                except Exception:
                    pass
            elif wants_gravity:
                self.poweruptype = "gravity_bombs"
                try:
                    if self.node and self.node.exists():
                        self.node.color_texture = _gravity_spawn_box_texture()
                except Exception:
                    pass
                try:
                    texts = getattr(self, "texts", None)
                    if isinstance(texts, dict) and "Name" in texts:
                        texts["Name"].text = "Gravity Bombs"
                except Exception:
                    pass

        _patched_pbx_init._silence_patch = True  # type: ignore[attr-defined]
        pupbox.PowerupBox.__init__ = _patched_pbx_init


def _is_silenced(spaz: Spaz) -> bool:
    _refresh_silence_lock(spaz)
    return getattr(spaz, "_silence_lock_count", 0) > 0


def _refresh_silence_lock(spaz: Spaz) -> None:
    """Fail-safe: if spaz is outside all active zones, clear stale lock."""
    if int(getattr(spaz, "_silence_lock_count", 0)) <= 0:
        return
    if spaz.node is None or not spaz.node.exists() or not spaz.is_alive():
        setattr(spaz, "_silence_lock_count", 0)
        return
    _prune_active_silence_zones()
    for zone in _active_silence_zones:
        if zone.contains_spaz(spaz):
            return
    setattr(spaz, "_silence_lock_count", 0)


def _prune_active_silence_zones() -> None:
    _active_silence_zones[:] = [
        z for z in _active_silence_zones if z is not None and not z._expired
    ]


def _lock_spaz_controls(spaz: Spaz) -> None:
    count = int(getattr(spaz, "_silence_lock_count", 0))
    setattr(spaz, "_silence_lock_count", count + 1)
    try:
        if spaz.node:
            spaz.node.punch_pressed = False
            spaz.node.pickup_pressed = False
            spaz.node.bomb_pressed = False
    except Exception:
        pass


def _unlock_spaz_controls(spaz: Spaz) -> None:
    count = int(getattr(spaz, "_silence_lock_count", 0))
    if count <= 1:
        setattr(spaz, "_silence_lock_count", 0)
    else:
        setattr(spaz, "_silence_lock_count", count - 1)


class SilenceZone(bs.Actor):
    """Temporary zone where players cannot punch, pickup, or bomb."""

    def __init__(
        self,
        *,
        position: tuple[float, float, float],
        radius: float = 3.2,
        duration: float = 4.5,
    ):
        super().__init__()
        self._position = position
        self._radius = radius
        self._duration = duration
        self._inside: dict[int, Spaz] = {}
        self._expired = False
        _active_silence_zones.append(self)

        self._ring = bs.newnode(
            "locator",
            attrs={
                "shape": "circleOutline",
                "position": position,
                "size": (radius * 2.0, 0.0, radius * 2.0),
                "color": (0.15, 0.3, 0.4),
                "opacity": 0.3,
                "draw_beauty": True,
                "additive": False,
            },
        )

        # Fast polling makes leaving/entering feel immediate.
        self._scan_timer = bs.Timer(
            0.02, bs.WeakCall(self._scan_players), repeat=True
        )
        self._expire_timer = bs.Timer(duration, bs.WeakCall(self._expire))

    def contains_spaz(self, spaz: Spaz) -> bool:
        # Use XZ distance so behavior matches the visible circle.
        if self._expired:
            return False
        if spaz.node is None or not spaz.node.exists():
            return False
        dx = spaz.node.position[0] - self._position[0]
        dz = spaz.node.position[2] - self._position[2]
        return (dx * dx) + (dz * dz) <= (self._radius * self._radius)

    def _scan_players(self) -> None:
        if self._expired:
            return
        activity = self._activity()
        if activity is None:
            self._expire()
            return

        current_inside: dict[int, Spaz] = {}

        for player in list(activity.players):
            actor = getattr(player, "actor", None)
            if not isinstance(actor, Spaz):
                continue
            try:
                if not actor.is_alive() or actor.node is None or not actor.node.exists():
                    continue
                if self.contains_spaz(actor):
                    current_inside[id(actor)] = actor
            except Exception:
                continue

        # Entered zone.
        for actor_id, actor in current_inside.items():
            if actor_id not in self._inside:
                _lock_spaz_controls(actor)

        # Exited zone.
        for actor_id, actor in list(self._inside.items()):
            if actor_id not in current_inside:
                _unlock_spaz_controls(actor)

        self._inside = current_inside

    def _expire(self) -> None:
        if self._expired:
            return
        self._expired = True
        try:
            while self in _active_silence_zones:
                _active_silence_zones.remove(self)
        except Exception:
            pass

        for actor in list(self._inside.values()):
            _unlock_spaz_controls(actor)
        self._inside.clear()

        try:
            if self._ring:
                self._ring.delete()
        except Exception:
            pass


class SilenceBomb(Bomb):
    """Impact-like bomb that creates a no-combat zone on trigger."""

    def __init__(
        self,
        *,
        position: tuple[float, float, float],
        velocity: tuple[float, float, float],
        source_player: bs.Player | None = None,
        owner: bs.Node | None = None,
        blast_radius: float = 1.5,
    ):
        super().__init__(
            position=position,
            velocity=velocity,
            bomb_type="impact",
            blast_radius=blast_radius,
            source_player=source_player,
            owner=owner,
        )
        try:
            if self.node:
                self.node.mesh = bs.getmesh("bomb")
                self.node.color_texture = bs.gettexture("egg2")
        except Exception:
            pass
        self._silence_radius = max(1.0, float(blast_radius))
        self._touch_anything_material = bs.Material()
        shared = SharedObjects.get()
        self._touch_anything_material.add_actions(
            conditions=(
                ("we_are_older_than", 80),
                "and",
                ("they_are_older_than", 80),
                "and",
                ("eval_colliding",),
                "and",
                (
                    ("they_have_material", shared.player_material),
                    "or",
                    ("they_have_material", shared.object_material),
                    "or",
                    ("they_have_material", shared.footing_material),
                ),
            ),
            actions=("message", "our_node", "at_connect", ImpactMessage()),
        )
        self._add_material(self._touch_anything_material)

    def explode(self) -> None:
        """Create zone instead of normal damage blast."""
        if getattr(self, "_exploded", False):
            return
        self._exploded = True

        if self.node and self.node.exists():
            pos = self.node.position
            SilenceZone(
                position=(pos[0], pos[1], pos[2]),
                radius=self._silence_radius,
                duration=4.5,
            ).autoretain()

        bs.timer(0.001, bs.WeakCall(self.handlemessage, bs.DieMessage()))


class _GravityTouchMessage:
    """Internal message fired when gravity-bomb touches a player."""


class GravityBomb(Bomb):
    """Impact-style bomb that removes touched player's gravity temporarily."""

    def __init__(
        self,
        *,
        position: tuple[float, float, float],
        velocity: tuple[float, float, float],
        source_player: bs.Player | None = None,
        owner: bs.Node | None = None,
    ):
        super().__init__(
            position=position,
            velocity=velocity,
            bomb_type="impact",
            blast_radius=1.0,
            source_player=source_player,
            owner=owner,
        )
        self._held = False
        self._gravity_radius = _GRAVITY_BOMB_RADIUS
        try:
            if self.node:
                self.node.mesh = bs.getmesh("bomb")
                self.node.color_texture = bs.gettexture("egg1")
        except Exception:
            pass

        self._touch_player_material = bs.Material()
        shared = SharedObjects.get()
        self._touch_player_material.add_actions(
            conditions=(
                ("we_are_older_than", 1),
                "and",
                ("they_are_older_than", 1),
                "and",
                ("eval_colliding",),
                "and",
                ("they_have_material", shared.player_material),
            ),
            actions=(
                ("modify_part_collision", "physical", False),
                ("message", "our_node", "at_connect", _GravityTouchMessage()),
            ),
        )
        self._add_material(self._touch_player_material)

    def explode(self) -> None:
        # No blast/damage; apply gravity effect in small impact-like range.
        if getattr(self, "_exploded", False):
            return
        self._exploded = True
        if self.node and self.node.exists():
            impact_pos = self.node.position
            activity = self._activity()
            if activity is not None:
                radius_sq = float(self._gravity_radius) * float(self._gravity_radius)
                for player in list(activity.players):
                    actor = getattr(player, "actor", None)
                    if not isinstance(actor, Spaz):
                        continue
                    try:
                        if (
                            not actor.is_alive()
                            or actor.node is None
                            or not actor.node.exists()
                        ):
                            continue
                        dx = actor.node.position[0] - impact_pos[0]
                        dy = actor.node.position[1] - impact_pos[1]
                        dz = actor.node.position[2] - impact_pos[2]
                        if (dx * dx) + (dy * dy) + (dz * dz) <= radius_sq:
                            _apply_gravity_bomb_effect(actor)
                    except Exception:
                        continue
        bs.timer(0.001, bs.WeakCall(self.handlemessage, bs.DieMessage()))

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, bs.PickedUpMessage):
            self._held = True
            return super().handlemessage(msg)

        if isinstance(msg, bs.DroppedMessage):
            self._held = False
            return super().handlemessage(msg)

        if isinstance(msg, _GravityTouchMessage):
            if getattr(self, "_exploded", False):
                return None
            # Ignore while actively held to prevent in-hand triggering.
            try:
                if self.node is not None and self.node.hold_node is not None:
                    return None
            except Exception:
                pass
            try:
                if (
                    self._held
                    and self.node is not None
                    and self.node.hold_node is None
                ):
                    self._held = False
            except Exception:
                pass
            if self._held:
                return None

            target_node = None
            try:
                target_node = bs.getcollision().opposingnode
            except Exception:
                target_node = None

            # Don't trigger on the bomb owner (same safeguard as impact bomb).
            if (
                target_node is not None
                and self.owner is not None
                and target_node is self.owner
            ):
                return None

            self.explode()
            return None
        return super().handlemessage(msg)


def _patched_drop_bomb(self: Spaz) -> Bomb | None:
    bomb_type = getattr(self, "bomb_type", "normal")
    if bomb_type in ("silence", "gravity") and not _custom_bomb_enabled(bomb_type):
        _revert_to_normal_bombs(self)
        return _original_drop_bomb(self)
    if bomb_type not in ("silence", "gravity"):
        return _original_drop_bomb(self)

    uses_left = _get_custom_bomb_count(self)
    if uses_left is not None and uses_left <= 0:
        _revert_to_normal_bombs(self)
        return _original_drop_bomb(self)

    if self.land_mine_count > 0:
        return _original_drop_bomb(self)

    if self.bomb_count <= 0 or self.frozen:
        return None
    if not self.node:
        return None

    pos = self.node.position_forward
    vel = self.node.velocity
    if bomb_type == "silence":
        bomb = SilenceBomb(
            position=(pos[0], pos[1], pos[2]),
            velocity=(vel[0], vel[1], vel[2]),
            source_player=self.source_player,
            owner=self.node,
        ).autoretain()
    else:
        bomb = GravityBomb(
            position=(pos[0], pos[1], pos[2]),
            velocity=(vel[0], vel[1], vel[2]),
            source_player=self.source_player,
            owner=self.node,
        ).autoretain()

    if bomb.node:
        self.bomb_count -= 1
        bomb.node.add_death_action(bs.WeakCall(self.handlemessage, BombDiedMessage()))
        self._pick_up(bomb.node)
        custom_tex = (
            _silence_powerup_texture()
            if bomb_type == "silence"
            else _gravity_bomb_texture()
        )
        if _consume_custom_bomb_count(self, custom_tex):
            _revert_to_normal_bombs(self)

    for callback in self._dropped_bomb_callbacks:
        callback(self, bomb)
    return bomb


def _patched_on_punch_press(self: Spaz) -> None:
    if _is_silenced(self):
        try:
            if self.node:
                self.node.punch_pressed = False
        except Exception:
            pass
        return
    target = _original_on_punch_press or _base_on_punch_press
    if target is not None:
        target(self)


def _patched_on_pickup_press(self: Spaz) -> None:
    if _is_silenced(self):
        try:
            if self.node:
                self.node.pickup_pressed = False
        except Exception:
            pass
        return
    target = _original_on_pickup_press or _base_on_pickup_press
    if target is not None:
        target(self)


def _patched_on_bomb_press(self: Spaz) -> None:
    if _is_silenced(self):
        try:
            if self.node:
                self.node.bomb_pressed = False
        except Exception:
            pass
        return
    target = _original_on_bomb_press or _base_on_bomb_press
    if target is not None:
        target(self)


def _grant_custom_bomb_powerup(
    spaz: Spaz,
    bomb_type: str,
    tex: bs.Texture,
    msg: bs.PowerupMessage,
) -> bool:
    if spaz._dead or not spaz.node:
        return True
    if spaz.pick_up_powerup_callback is not None:
        spaz.pick_up_powerup_callback(spaz)

    spaz.bomb_type = bomb_type
    _set_custom_bomb_count(spaz, _CUSTOM_BOMB_MAX_COUNT, tex)
    try:
        spaz._flash_billboard(tex)
    except Exception:
        pass
    spaz.node.handlemessage("flash")
    if msg.sourcenode:
        msg.sourcenode.handlemessage(bs.PowerupAcceptMessage())
    return True


def _patched_handlemessage(self: Spaz, msg: Any) -> Any:
    if isinstance(msg, bs.PowerupMessage):
        if msg.poweruptype in ("silence", "silence_bombs"):
            if _custom_bomb_enabled("silence"):
                return _grant_custom_bomb_powerup(
                    self, "silence", _silence_powerup_texture(), msg
                )
            if msg.sourcenode:
                msg.sourcenode.handlemessage(bs.PowerupAcceptMessage())
            return True
        if msg.poweruptype in ("gravity", "gravity_bombs"):
            if _custom_bomb_enabled("gravity"):
                return _grant_custom_bomb_powerup(
                    self, "gravity", _gravity_bomb_texture(), msg
                )
            if msg.sourcenode:
                msg.sourcenode.handlemessage(bs.PowerupAcceptMessage())
            return True
        result = _original_handlemessage(self, msg)
        # Ensure spawned bomb powerups always wear off with POWERUP_WEAR_OFF_TIME.
        if msg.poweruptype in (
            "impact_bombs",
            "sticky_bombs",
            "ice_bombs",
            "fly_bombs",
            "fire_bombs",
            "impairment_bombs",
        ):
            try:
                tex = self._get_bomb_type_tex()
            except Exception:
                tex = None
            if tex is not None:
                _start_bomb_type_wearoff(self, tex)
        elif msg.poweruptype == "triple_bombs":
            _start_multi_bomb_wearoff(self)
        elif msg.poweruptype == "punch":
            _start_gloves_wearoff(self)
        elif msg.poweruptype == "speed":
            try:
                speed_tex = getattr(
                    pupbox.PowerupBoxFactory.get(), "tex_speed", None
                ) or bs.gettexture("powerupCurse")
            except Exception:
                speed_tex = bs.gettexture("powerupCurse")
            _start_speed_wearoff(self, speed_tex)
        elif msg.poweruptype == "ice_man":
            try:
                ice_man_tex = getattr(
                    pupbox.PowerupBoxFactory.get(), "tex_ice_man", None
                ) or bs.gettexture("powerupIceBombs")
            except Exception:
                ice_man_tex = bs.gettexture("powerupIceBombs")
            _start_ice_man_wearoff(self, ice_man_tex)
        return result
    return _original_handlemessage(self, msg)


def _patched_get_bomb_type_tex(self: Spaz):
    bomb_type = getattr(self, "bomb_type", "normal")
    if bomb_type == "silence":
        if not _custom_bomb_enabled("silence"):
            self.bomb_type = "normal"
            return _original_get_bomb_type_tex(self)
        return _silence_powerup_texture()
    if bomb_type == "gravity":
        if not _custom_bomb_enabled("gravity"):
            self.bomb_type = "normal"
            return _original_get_bomb_type_tex(self)
        return _gravity_bomb_texture()
    return _original_get_bomb_type_tex(self)


def apply() -> None:
    global _applied
    global _original_drop_bomb
    global _original_on_punch_press
    global _original_on_pickup_press
    global _original_on_bomb_press
    global _original_handlemessage
    global _original_get_bomb_type_tex
    global _base_on_punch_press
    global _base_on_pickup_press
    global _base_on_bomb_press

    _load_custom_bomb_settings()
    _apply_powerup_patches()

    # Preserve base input handlers once so future re-patches stay safe.
    if _base_on_punch_press is None and not getattr(
        Spaz.on_punch_press, "_silence_patch", False
    ):
        _base_on_punch_press = Spaz.on_punch_press
    if _base_on_pickup_press is None and not getattr(
        Spaz.on_pickup_press, "_silence_patch", False
    ):
        _base_on_pickup_press = Spaz.on_pickup_press
    if _base_on_bomb_press is None and not getattr(
        Spaz.on_bomb_press, "_silence_patch", False
    ):
        _base_on_bomb_press = Spaz.on_bomb_press

    # Fix compatibility with powerup plugins that store a super punch handler.
    if (
        hasattr(Spaz, "_super_on_punch_press")
        and getattr(Spaz._super_on_punch_press, "_silence_patch", False)
        and _base_on_punch_press is not None
    ):
        Spaz._super_on_punch_press = _base_on_punch_press

    if not getattr(Spaz.drop_bomb, "_silence_patch", False):
        _original_drop_bomb = Spaz.drop_bomb
        _patched_drop_bomb._silence_patch = True  # type: ignore[attr-defined]
        Spaz.drop_bomb = _patched_drop_bomb

    if not getattr(Spaz.on_punch_press, "_silence_patch", False):
        _original_on_punch_press = _base_on_punch_press or Spaz.on_punch_press
        _patched_on_punch_press._silence_patch = True  # type: ignore[attr-defined]
        Spaz.on_punch_press = _patched_on_punch_press

    if not getattr(Spaz.on_pickup_press, "_silence_patch", False):
        _original_on_pickup_press = _base_on_pickup_press or Spaz.on_pickup_press
        _patched_on_pickup_press._silence_patch = True  # type: ignore[attr-defined]
        Spaz.on_pickup_press = _patched_on_pickup_press

    if not getattr(Spaz.on_bomb_press, "_silence_patch", False):
        _original_on_bomb_press = _base_on_bomb_press or Spaz.on_bomb_press
        _patched_on_bomb_press._silence_patch = True  # type: ignore[attr-defined]
        Spaz.on_bomb_press = _patched_on_bomb_press

    if not getattr(Spaz.handlemessage, "_silence_patch", False):
        _original_handlemessage = Spaz.handlemessage
        _patched_handlemessage._silence_patch = True  # type: ignore[attr-defined]
        Spaz.handlemessage = _patched_handlemessage

    if not getattr(Spaz._get_bomb_type_tex, "_silence_patch", False):
        _original_get_bomb_type_tex = Spaz._get_bomb_type_tex
        _patched_get_bomb_type_tex._silence_patch = True  # type: ignore[attr-defined]
        Spaz._get_bomb_type_tex = _patched_get_bomb_type_tex

    _applied = True
