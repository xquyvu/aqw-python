"""Retrieve Void Auras until more than two are owned: python -u -m bot.void_aura.

Source: https://aqwwiki.wikidot.com/braeus-quests
Requires Evil rank 10 and 20 permanent essences from each of the ten sources.
"""

import json
import time
from dataclasses import dataclass, replace

from bot.evil_rep import main as ensure_evil_rank
from bot.lord_of_order.runner import DailyRunner, Settings
from combo.dragonslayer_general import attack_next_skill
from core.command import Command
from core.inventory import withdraw_from_bank
from core.leech import LeechUnavailable
from core.item_farm import item_count
from core.quest_farm import FarmConfig, Quest, QuestFarmer, Screen
from core.script_runner import run_script
from core.utils import normalize

TARGET_ITEM = "Void Aura"
TARGET_QTY = 3
QUEST = Quest(4432, "Retrieve Void Auras", requirement="Requires Evil rank 10.")
ESSENCE_QTY = 20


@dataclass(frozen=True)
class Essence:
    item: str
    map_name: str
    monster: str


ESSENCES = (
    Essence("Astral Ephemerite Essence", "timespace", "Astral Ephemerite"),
    Essence("Belrot the Fiend Essence", "citadel", "Belrot the Fiend"),
    Essence("Black Knight Essence", "greenguardwest", "Black Knight"),
    Essence("Tiger Leech Essence", "mudluk", "Tiger Leech"),
    Essence("Carnax Essence", "aqlesson", "Carnax"),
    Essence("Chaos Vordred Essence", "necrocavern", "Chaos Vordred"),
    Essence("Dai Tengu Essence", "hachiko", "Dai Tengu"),
    Essence("Unending Avatar Essence", "timevoid", "Unending Avatar"),
    Essence("Void Dragon Essence", "dragonchallenge", "Void Dragon"),
    Essence("Creature Creation Essence", "maul", "Creature Creation"),
)

CONFIG = FarmConfig(
    name=QUEST.name,
    quests=(QUEST,),
    map_name="shadowfall",
    screen=Screen(monsters={"Astral Ephemerite": None}),
    class_name="Dragonslayer General",
    combo=attack_next_skill,
    drops=(TARGET_ITEM, *(essence.item for essence in ESSENCES)),
    server="Alteon",
    mode="leech",
)


class VoidAuraRunner(DailyRunner):
    def __init__(self, cmd: Command):
        super().__init__(
            cmd,
            Settings(
                solo_class=CONFIG.class_name,
                server=CONFIG.server,
                room_number=CONFIG.effective_room_number,
            ),
        )
        self.pickup_error: str | None = None

    def on_message(self, message: str):
        super().on_message(message)
        if not message.startswith("{"):
            return
        data = json.loads(message).get("b", {}).get("o", {})
        if not isinstance(data, dict):
            return
        if data.get("cmd") == "getDrop" and int(data.get("bSuccess", 0)) != 1:
            pending = self.bot.pending_drops.get(str(data["ItemID"]))
            if pending is not None and normalize(pending.item_name) in {
                normalize(name) for name in CONFIG.drops
            }:
                self.pickup_error = (
                    f"Could not collect {pending.item_name}: "
                    f"{data.get('sMsg') or data.get('msg') or 'pickup rejected'}. "
                    "Check free inventory space."
                )

    def connected(self):
        if not self.cmd.is_still_connected():
            raise ConnectionError("Disconnected during Retrieve Void Auras.")
        if self.pickup_error is not None:
            raise RuntimeError(self.pickup_error)

    async def restore(self, item: str, qty: int = 1):
        if not self.has(item, qty) and self.cmd.is_in_bank(item):
            await withdraw_from_bank(self.cmd, item, self.settings.request_timeout)
            if not self.has(item, qty):
                raise RuntimeError(
                    f"Unbanking {item} was not confirmed; check inventory space."
                )

    def validate_requirements(self):
        data = self.quest_data(QUEST.id)
        if data is None:
            raise RuntimeError(f"Quest {QUEST.id} metadata did not load.")
        requirements = {
            normalize(data["oItems"][str(item["ItemID"])]["sName"]): int(item["iQty"])
            for item in data["turnin"]
        }
        expected = {normalize(essence.item): ESSENCE_QTY for essence in ESSENCES}
        if requirements != expected:
            raise RuntimeError(
                f"Quest {QUEST.id} requirements changed: {requirements}; "
                "stopping instead of farming an unverified route."
            )
        for required in data.get("reqd") or ():
            item = self.cmd.get_player().get_item_inventory_by_id(required["ItemID"])
            if item is None or int(item.qty) < int(required["iQty"]):
                raise RuntimeError(
                    f"Quest {QUEST.id} requires inventory item "
                    f"{required['ItemID']} x{required['iQty']}."
                )

    async def farm_essence(self, essence: Essence):
        await self.restore(essence.item, ESSENCE_QTY)
        if self.has(essence.item, ESSENCE_QTY):
            print(f"VOID AURA: {essence.item} x20 already collected.", flush=True)
            return
        config = replace(
            CONFIG,
            map_name=essence.map_name,
            screen=Screen(monsters={essence.monster: None}),
        )
        farmer = QuestFarmer(self.cmd, config)
        last_report = None
        while not self.has(essence.item, ESSENCE_QTY):
            self.connected()
            await farmer.ensure_room()
            self.connected()
            now = time.monotonic()
            if last_report is None or now - last_report >= CONFIG.report_interval:
                self.cmd.farming_logger(essence.item, ESSENCE_QTY)
                last_report = now
            if self.has(essence.item, ESSENCE_QTY):
                break
            await farmer.attack(farmer.select_screen())
            await self.cmd.sleep(100)
        self.connected()
        await self.cmd.leave_combat()
        print(f"VOID AURA: collected {essence.item} x20.", flush=True)

    async def run(self):
        previous = (
            self.bot.accept_all_drops,
            self.bot.accept_non_member_drops,
            list(self.bot.items_drop_whitelist),
            self.bot.auto_relogin,
        )
        completed = False
        skipped = False
        self.bot.accept_all_drops = False
        self.bot.accept_non_member_drops = False
        self.bot.items_drop_whitelist[:] = CONFIG.drops
        self.bot.auto_relogin = False
        self.bot.subscribe(self.on_message)
        try:
            self.connected()
            if item_count(self.cmd, TARGET_ITEM) >= TARGET_QTY:
                print("VOID AURA: already own more than 2; skipping.", flush=True)
                completed = True
                return
            await ensure_evil_rank(self.cmd)
            self.bot.farmClass = CONFIG.class_name
            self.bot.auto_adjust_skill_delay = True
            await self.equip(boss=True)
            while item_count(self.cmd, TARGET_ITEM) < TARGET_QTY:
                self.connected()
                await self.enter("shadowfall")
                await self.accept(QUEST.id, QUEST.requirement)
                self.validate_requirements()
                for essence in ESSENCES:
                    await self.bounded(
                        self.farm_essence(essence),
                        f"farming {essence.item}; check map access and inventory space",
                        self.settings.item_timeout,
                    )
                await self.enter("shadowfall")
                before = item_count(self.cmd, TARGET_ITEM)
                await self.turn_in(QUEST.id)
                await self.wait(
                    lambda: item_count(self.cmd, TARGET_ITEM) > before,
                    "receiving Void Auras after the confirmed turn-in",
                )
                print(
                    f"VOID AURA: {item_count(self.cmd, TARGET_ITEM)}/{TARGET_QTY} "
                    "(inventory + bank).",
                    flush=True,
                )
            print("FARM COMPLETE: more than 2 Void Auras owned.", flush=True)
            completed = True
        except LeechUnavailable:
            skipped = True
            raise
        except (RuntimeError, TimeoutError, ConnectionError) as error:
            print(f"VOID AURA ERROR: {error}", flush=True)
            raise
        finally:
            self.bot.unsubscribe(self.on_message)
            self.bot.accept_all_drops = previous[0]
            self.bot.accept_non_member_drops = previous[1]
            self.bot.items_drop_whitelist[:] = previous[2]
            if completed or skipped:
                self.bot.auto_relogin = previous[3]
            else:
                self.bot.stop_bot(user_triggered=True)


async def main(cmd: Command):
    await VoidAuraRunner(cmd).run()


def run():
    run_script(
        main,
        class_name=CONFIG.class_name,
        server=CONFIG.server,
        room_number=CONFIG.effective_room_number,
        leech=CONFIG.mode == "leech",
    )


if __name__ == "__main__":
    run()
