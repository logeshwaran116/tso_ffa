# -*- coding: utf-8 -*-
# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to player-controlled Spazzes."""

from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, overload
import babase
import bascenev1 as bs
import babase._mgen.enums as enums
import random
import math
import time
import weakref
from bascenev1lib.actor import spaz, playerspaz
from bascenev1lib.actor.spazfactory import SpazFactory
from bascenev1lib.actor.popuptext import PopupText
from bascenev1lib.actor import bomb as stdbomb
from bascenev1lib.actor.powerupbox import PowerupBoxFactory
from bascenev1lib import gameutils
import setting
from playersData import pdata
from stats import mystats

PlayerType = TypeVar('PlayerType', bound=bs.Player)
TeamType = TypeVar('TeamType', bound=bs.Team)
tt = bs.TimeType.SIM
tf = bs.TimeFormat.MILLISECONDS

multicolor = {0: ((0+random.random()*3.0), (0+random.random()*3.0), (0+random.random()*3.0)),
              250: ((0+random.random()*3.0), (0+random.random()*3.0), (0+random.random()*3.0)),
              500: ((0+random.random()*3.0), (0+random.random()*3.0), (0+random.random()*3.0)),
              750: ((0+random.random()*3.0), (0+random.random()*3.0), (0+random.random()*3.0)),
              1000: ((0+random.random()*3.0), (0+random.random()*3.0), (0+random.random()*3.0)),
              1250: ((0+random.random()*3.0), (0+random.random()*3.0), (0+random.random()*3.0)),
              1500: ((0+random.random()*3.0), (0+random.random()*3.0), (0+random.random()*3.0)),
              1750: ((0+random.random()*3.0), (0+random.random()*3.0), (0+random.random()*3.0)),
              2000: ((0+random.random()*3.0), (0+random.random()*3.0), (0+random.random()*3.0)),
              2250: ((0+random.random()*3.0), (0+random.random()*3.0), (0+random.random()*3.0)),
              2500: ((0+random.random()*3.0), (0+random.random()*3.0), (0+random.random()*3.0))}


class SurroundBallFactory(object):
    def __init__(self):
        self.bonesTex = bs.gettexture("powerupCurse")
        self.bonesModel = bs.getmodel("bonesHead")
        self.bearTex = bs.gettexture("bearColor")
        self.bearModel = bs.getmodel("bearHead")
        self.aliTex = bs.gettexture("aliColor")
        self.aliModel = bs.getmodel("aliHead")
        self.b9000Tex = bs.gettexture("cyborgColor")
        self.b9000Model = bs.getmodel("cyborgHead")
        self.frostyTex = bs.gettexture("frostyColor")
        self.frostyModel = bs.getmodel("frostyHead")
        self.cubeTex = bs.gettexture("crossOutMask")
        self.cubeModel = bs.getmodel("powerup")
        try:
            self.mikuModel = bs.getmodel("operaSingerHead")
            self.mikuTex = bs.gettexture("operaSingerColor")
        except:
            babase.print_exception()
        self.ballMaterial = bs.Material()
        self.impactSound = bs.getsound("impactMedium")
        self.ballMaterial.add_actions(
            actions=("modify_node_collision", "collide", False))


class SurroundBall(bs.Actor):
    def __init__(self, spaz, shape="bones"):
        bs.Actor.__init__(self)
        self.spazRef = weakref.ref(spaz)
        factory = self.getFactory()
        s_model, s_texture = {
            "bones": (factory.bonesModel, factory.bonesTex),
            "bear": (factory.bearModel, factory.bearTex),
            "ali": (factory.aliModel, factory.aliTex),
            "b9000": (factory.b9000Model, factory.b9000Tex),
            "miku": (factory.mikuModel, factory.mikuTex),
            "frosty": (factory.frostyModel, factory.frostyTex),
            "RedCube": (factory.cubeModel, factory.cubeTex)
        }.get(shape, (factory.bonesModel, factory.bonesTex))
        self.node = bs.newnode("prop", attrs={"model": s_model, "body": "sphere", "color_texture": s_texture, "reflection": "soft", "model_scale": 0.5, "body_scale": 0.1, "density": 0.1, "reflection_scale": [
                               0.15], "shadow_size": 0.6, "position": spaz.node.position, "velocity": (0, 0, 0), "materials": [gameutils.get_shared_object('object_material'), factory.ballMaterial]}, delegate=self)
        self.surroundTimer = None
        self.surroundRadius = 1.0
        self.angleDelta = math.pi / 12.0
        self.curAngle = random.random() * math.pi * 2.0
        self.curHeight = 0.0
        self.curHeightDir = 1
        self.heightDelta = 0.2
        self.heightMax = 1.0
        self.heightMin = 0.1
        self.initTimer(spaz.node.position)

    def getTargetPosition(self, spazPos):
        p = spazPos
        pt = (p[0] + self.surroundRadius * math.cos(self.curAngle), p[1] +
              self.curHeight, p[2] + self.surroundRadius * math.sin(self.curAngle))
        self.curAngle += self.angleDelta
        self.curHeight += self.heightDelta * self.curHeightDir
        if (self.curHeight > self.heightMax) or (self.curHeight < self.heightMin):
            self.curHeightDir = -self.curHeightDir
        return pt

    def initTimer(self, p):
        self.node.position = self.getTargetPosition(p)
        self.surroundTimer = bs.Timer(
            0.03, self.circleMove, repeat=True, timetype=tt)

    def circleMove(self):
        spaz = self.spazRef()
        if spaz is None or not spaz.is_alive() or not spaz.node.exists():
            self.handlemessage(bs.DieMessage())
            return
        p = spaz.node.position
        pt = self.getTargetPosition(p)
        pn = self.node.position
        d = [pt[0] - pn[0], pt[1] - pn[1], pt[2] - pn[2]]
        speed = self.getMaxSpeedByDir(d)
        self.node.velocity = speed

    @staticmethod
    def getMaxSpeedByDir(direction):
        k = 7.0 / max((abs(x) for x in direction))
        return tuple(x * k for x in direction)

    def handlemessage(self, m):
        bs.Actor.handlemessage(self, m)
        if isinstance(m, bs.DieMessage):
            if self.surroundTimer is not None:
                self.surroundTimer = None
            self.node.delete()
        elif isinstance(m, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())

    def getFactory(cls):
        activity = bs.get_foreground_host_activity()
        if activity is None:
            raise Exception("no current activity")
        try:
            return activity._sharedSurroundBallFactory
        except Exception:
            f = activity._sharedSurroundBallFactory = SurroundBallFactory()
            return f


class Effect(bs.Actor):
    def __init__(self, spaz, player):
        bs.Actor.__init__(self)
        _settings = setting.get_settings_data()
        custom_effects = pdata.get_custom()['customeffects']
        paid_effects = pdata.get_custom()['paideffects']
        self.source_player = player
        self.spazRef = weakref.ref(spaz)
        self.spazNormalColor = spaz.node.color
        self.Decorations = []
        self.Enhancements = []
        self._powerScale = 1.0
        self._armorScale = 1.0
        self._lifeDrainScale = None
        self._damageBounceScale = None
        self._remoteMagicDamge = False
        self._MulitPunch = None
        self._AntiFreeze = 1.0
        self.fallWings = 0
        self.checkDeadTimer = None
        self._hasDead = False
        self.light = None

        node_id = self.source_player.node.playerID
        cl_str = None
        clID = None
        for c in bs.get_foreground_host_session().sessionplayers:
            if (c.activityplayer) and (c.activityplayer.node.playerID == node_id):
                profiles = c.inputdevice.get_player_profiles()
                clID = c.inputdevice.client_id
                cl_str = c.get_v1_account_id()

        try:
            if cl_str in paid_effects:
                effect = paid_effects[cl_str]['effect']
                if effect == 'icebdbdh': self.snowTimer = bs.Timer(0.5, babase.Call(self.emitIce), repeat=True, timetype=tt)
                elif effect == 'sweatdggs': self.smokeTimer = bs.Timer(0.04, babase.Call(self.emitSmoke), repeat=True, timetype=tt)
                elif effect == 'scorshshdhch': self.scorchTimer = bs.Timer(0.5, babase.Call(self.update_Scorch), repeat=True, timetype=tt)
                elif effect == 'glgsgsgsow': self.addLightColor((1, 0.6, 0.4));self.checkDeadTimer = bs.Timer(0.15, babase.Call(self.checkPlayerifDead), repeat=True, timetype=tt)
                elif effect == 'distogshshhsrtion': self.DistortionTimer = bs.Timer(1.0, babase.Call(self.emitDistortion), repeat=True, timetype=tt)
                elif effect == 'slihwhhwhsme': self.slimeTimer = bs.Timer(0.25, babase.Call(self.emitSlime), repeat=True, timetype=tt)
                elif effect == 'metgsgsgsal': self.metalTimer = bs.Timer(0.5, babase.Call(self.emitMetal), repeat=True, timetype=tt)
                elif effect == 'surrounder': self.surround = SurroundBall(spaz, shape="bones")
            elif cl_str in custom_effects:
                effects = custom_effects[cl_str]
                for effect in effects:
                    if effect == 'ichshshse':
                        self.emitIce()
                        self.snowTimer = bs.Timer(
                            0.5, self.emitIce, repeat=True, timetype=bs.TimeType.SIM)
                        return
                    elif effect == 'swehshshsheat':
                        self.smokeTimer = bs.Timer(
                            0.6, self.emitSmoke, repeat=True, timetype=bs.TimeType.SIM)
                        return
                    elif effect == 'scorhshshshch':
                        self.scorchTimer = bs.Timer(
                            0.5, self.update_Scorch, repeat=True, timetype=tt)
                        return
                    elif effect == 'glhshshshshshow':
                        self.addLightColor((1, 0.6, 0.4))
                        self.checkDeadTimer = bs.Timer(
                            0.15, self.checkPlayerifDead, repeat=True, timetype=tt)
                        return
                    elif effect == 'distohshshsrtion':
                        self.DistortionTimer = bs.Timer(
                            1.0, self.emitDistortion, repeat=True, timetype=tt)
                        return
                    elif effect == 'slihshehdhme':
                        self.slimeTimer = bs.Timer(
                            0.25, self.emitSlime, repeat=True, timetype=tt)
                        return
                    elif effect == 'methshshshsal':
                        self.metalTimer = bs.Timer(
                            0.5, self.emitMetal, repeat=True, timetype=tt)
                        return
                    elif effect == 'surrounder':
                        self.surround = SurroundBall(spaz, shape="bones")
                        return
                    elif effect == 'sphshshhsark':
                        self.sparkTimer = bs.Timer(
                            0.1, self.emitSpark, repeat=True, timetype=tt)
                        return
        except:
            pass

        if _settings['enablestats']:
            pats = mystats.get_all_stats()
            if cl_str in pats and _settings['enableTop5effects']:
                rank = pats[cl_str]["rank"]
                if rank < 1:
                    if rank == 1:
                        # self.neroLightTimer = bs.Timer(0.5, babase.Call(self.neonLightSwitch,("shine" in self.Decorations),("extra_Highlight" in self.Decorations),("extra_NameColor" in self.Decorations)),repeat = True, timetype=tt)
                        self.surround = SurroundBall(spaz, shape="bones")


        if "smoke" and "spark" and "snowDrops" and "slimeDrops" and "metalDrops" and "Distortion" and "neroLight" and "scorch" and "HealTimer" and "KamikazeCheck" not in self.Decorations:
            # self.checkDeadTimer = bs.Timer(0.15, babase.Call(self.checkPlayerifDead), repeat=True, timetype=tt)
            if self.source_player.is_alive() and self.source_player.actor.node.exists():
                # print("OK")
                self.source_player.actor.node.addDeathAction(
                    babase.Call(self.handlemessage, bs.DieMessage()))

    def add_multicolor_effect(self):
        if self.spazRef().node:
            bs.animate_array(self.spazRef().node, 'color', 3, multicolor,
                             True, timetype=tt)

    def checkPlayerifDead(self):
        spaz = self.spazRef()
        if spaz is None or not spaz.is_alive() or not spaz.node.exists():
            self.checkDeadTimer = None
            self.handlemessage(bs.DieMessage())
            return

    def update_Scorch(self):
        spaz = self.spazRef()
        if spaz is not None and spaz.is_alive() and spaz.node.exists():
            color = (random.random(), random.random(), random.random())
            if not hasattr(self, "scorchNode") or self.scorchNode == None:
                self.scorchNode = None
                self.scorchNode = bs.newnode("scorch", attrs={"position": (
                    spaz.node.position), "size": 1.17, "big": True})
                spaz.node.connectattr("position", self.scorchNode, "position")
            bs.animate_array(self.scorchNode, "color", 3, {
                             0: self.scorchNode.color, 0.5: color}, timetype=tt)
        else:
            self.scorchTimer = None
            if hasattr(self, "scorchNode"):
                self.scorchNode.delete()
            self.handlemessage(bs.DieMessage())

    def neonLightSwitch(self, shine, Highlight, NameColor):
        spaz = self.spazRef()
        if spaz is not None and spaz.is_alive() and spaz.node.exists():
            color = (random.random(), random.random(), random.random())
            if NameColor:
                bs.animate_array(spaz.node, "nameColor", 3, {
                                 0: spaz.node.nameColor, 0.5: bs.safecolor(color)}, timetype=tt)
            if shine:
                color = tuple([min(10., 10 * x) for x in color])
            bs.animate_array(spaz.node, "color", 3, {
                             0: spaz.node.color, 0.5: color}, timetype=tt)
            if Highlight:
                # print spaz.node.highlight
                color = (random.random(), random.random(), random.random())
                if shine:
                    color = tuple([min(10., 10 * x) for x in color])
                bs.animate_array(spaz.node, "highlight", 3, {
                                 0: spaz.node.highlight, 0.5: color}, timetype=tt)
        else:
            self.neroLightTimer = None
            self.handlemessage(bs.DieMessage())

    def addLightColor(self, color):
        self.light = bs.newnode(
            "light", attrs={"color": color, "height_attenuated": False, "radius": 0.4})
        self.spazRef().node.connectattr("position", self.light, "position")
        bs.animate(self.light, "intensity", {
                   0: 0.1, 0.25: 0.3, 0.5: 0.1}, loop=True, timetype=tt)

    def emitDistortion(self):
        spaz = self.spazRef()
        if spaz is None or not spaz.is_alive() or not spaz.node.exists():
            self.handlemessage(bs.DieMessage())
            return
        bs.emitfx(position=spaz.node.position,
                  emit_type="distortion", spread=1.0)
        bs.emitfx(position=spaz.node.position, velocity=spaz.node.velocity,
                  count=random.randint(1, 5), emit_type="tendrils", tendril_type="smoke")

    def emitSpark(self):
        spaz = self.spazRef()
        if spaz is None or not spaz.is_alive() or not spaz.node.exists():
            self.handlemessage(bs.DieMessage())
            return
        bs.emitfx(position=spaz.node.position, velocity=spaz.node.velocity,
                  count=random.randint(1, 10), scale=2, spread=0.2, chunk_type="spark")

    def emitIce(self):
        spaz = self.spazRef()

        if spaz is None or not spaz.is_alive() or not spaz.node.exists():
            self.handlemessage(bs.DieMessage())
            return
        bs.emitfx(position=spaz.node.position, velocity=spaz.node.velocity,
                  count=random.randint(2, 8), scale=0.4, spread=0.2, chunk_type="ice")

    def emitSmoke(self):
        spaz = self.spazRef()
        if spaz is None or not spaz.is_alive() or not spaz.node.exists():
            self.handlemessage(bs.DieMessage())
            return
        bs.emitfx(position=spaz.node.position, velocity=spaz.node.velocity,
                  count=random.randint(1, 10), scale=2, spread=0.2, chunk_type="sweat")

    def emitSlime(self):
        spaz = self.spazRef()
        if spaz is None or not spaz.is_alive() or not spaz.node.exists():
            self.handlemessage(bs.DieMessage())
            return
        bs.emitfx(position=spaz.node.position, velocity=spaz.node.velocity,
                  count=random.randint(1, 10), scale=0.4, spread=0.2, chunk_type="slime")

    def emitMetal(self):
        spaz = self.spazRef()
        if spaz is None or not spaz.is_alive() or not spaz.node.exists():
            self.handlemessage(bs.DieMessage())
            return
        bs.emitfx(position=spaz.node.position, velocity=spaz.node.velocity,
                  count=random.randint(2, 8), scale=0.4, spread=0.2, chunk_type="metal")

    def handlemessage(self, m):
        # self._handlemessageSanityCheck()
        if isinstance(m, bs.OutOfBoundsMessage):
            self.handlemessage(bs.DieMessage())
        elif isinstance(m, bs.DieMessage):
            if hasattr(self, "light") and self.light is not None:
                self.light.delete()
            if hasattr(self, "smokeTimer"):
                self.smokeTimer = None
            if hasattr(self, "surround"):
                self.surround = None
            if hasattr(self, "sparkTimer"):
                self.sparkTimer = None
            if hasattr(self, "snowTimer"):
                self.snowTimer = None
            if hasattr(self, "metalTimer"):
                self.metalTimer = None
            if hasattr(self, "DistortionTimer"):
                self.DistortionTimer = None
            if hasattr(self, "slimeTimer"):
                self.slimeTimer = None
            if hasattr(self, "KamikazeCheck"):
                self.KamikazeCheck = None
            if hasattr(self, "neroLightTimer"):
                self.neroLightTimer = None
            if hasattr(self, "checkDeadTimer"):
                self.checkDeadTimer = None
            if hasattr(self, "HealTimer"):
                self.HealTimer = None
            if hasattr(self, "scorchTimer"):
                self.scorchTimer = None
            if hasattr(self, "scorchNode"):
                self.scorchNode = None
            if not self._hasDead:
                spaz = self.spazRef()
                # print str(spaz) + "Spaz"
                if spaz is not None and spaz.is_alive() and spaz.node.exists():
                    spaz.node.color = self.spazNormalColor
                killer = spaz.last_player_attacked_by if spaz is not None else None
                try:
                    if killer in (None, bs.Player(None)) or killer.actor is None or not killer.actor.exists() or killer.actor.hitPoints <= 0:
                        killer = None
                except:
                    killer = None
                    # if hasattr(self,"hasDead") and not self.hasDead:
                self._hasDead = True

        bs.Actor.handlemessage(self, m)