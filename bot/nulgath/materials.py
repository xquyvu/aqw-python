"""Farm bounded Nulgath stocks: python -u -m bot.nulgath.materials."""

import json
from dataclasses import dataclass, replace

from bot.lord_of_order.runner import DailyRunner, Settings
from bot.relic_of_chaos import CONFIG as RELIC_CONFIG
from bot.relic_of_chaos import SUPPLIES, TURN_IN_MAP
from core.command import Command
from core.inventory import withdraw_from_bank
from core.item_farm import item_count
from core.leech import LeechUnavailable
from core.quest_farm import FarmConfig, Quest, QuestFarmer, Screen
from core.script_runner import run_script
from core.utils import normalize


@dataclass(frozen=True)
class StockGoal:
    item: str
    quantity: int
    reward_id: int


# Order also determines Swindle's reward priority.
GOALS = (
    StockGoal("Blood Gem of the Archfiend", 20, 22332),
    StockGoal("Dark Crystal Shard", 200, 4770),
    StockGoal("Gem of Nulgath", 200, 6136),
)
SWINDLE = Quest(7551, "Swindle's Return Policy")
SWINDLE_PARTS = {
    4700: "Unidentified 1",
    4715: "Unidentified 6",
    4718: "Unidentified 9",
    4749: "Unidentified 16",
    4767: "Unidentified 20",
}
RUNE_ID = 15395
RUNE = "Dark Makai Rune"
RELIC = "Relic of Chaos"
CONFIG = replace(RELIC_CONFIG, name="Nulgath material stocks", quests=())
RUNE_CONFIG = FarmConfig(
    name=RUNE,
    quests=(),
    map_name="evilmarsh",
    screen=Screen(monsters={"Dark Makai": None}, cell="Field1"),
    mode="solo",
)


class MaterialsRunner(DailyRunner):
    def __init__(self, cmd: Command):
        super().__init__(cmd, Settings())
        self.pickup_error: str | None = None
        self.required_drops = {
            normalize(goal.item): goal.quantity for goal in GOALS
        } | {normalize(name): 1 for name in (*SWINDLE_PARTS.values(), RELIC, RUNE)}
        self.relic_farmer = QuestFarmer(
            cmd, CONFIG, stop_when=lambda: self.collected(RELIC)
        )
        self.rune_farmer = QuestFarmer(
            cmd, RUNE_CONFIG, stop_when=lambda: self.collected(RUNE)
        )

    def connected(self):
        if not self.cmd.is_still_connected():
            raise ConnectionError("Disconnected during Nulgath material farming.")
        if self.pickup_error is not None:
            raise RuntimeError(self.pickup_error)

    def collected(self, item: str) -> bool:
        self.connected()
        return self.next_goal() is None or self.has(item)

    def on_message(self, message: str):
        super().on_message(message)
        if not message.startswith("{"):
            return
        data = json.loads(message).get("b", {}).get("o", {})
        if (
            not isinstance(data, dict)
            or data.get("cmd") != "getDrop"
            or int(data.get("bSuccess", 0)) == 1
        ):
            return
        pending = self.bot.pending_drops.get(str(data["ItemID"]))
        if pending is None:
            return
        needed = self.required_drops.get(normalize(pending.item_name))
        if (
            needed is not None
            and item_count(self.cmd, pending.item_name) < needed
            and not self.has(pending.item_name, needed)
        ):
            self.pickup_error = (
                f"Could not collect {pending.item_name}: "
                f"{data.get('sMsg') or data.get('msg') or 'pickup rejected'}. "
                "Check free inventory space."
            )

    def next_goal(self) -> StockGoal | None:
        return next(
            (goal for goal in GOALS if item_count(self.cmd, goal.item) < goal.quantity),
            None,
        )

    def report(self):
        print(
            "NULGATH STOCKS (inventory + bank): "
            + " | ".join(
                f"{goal.item} {item_count(self.cmd, goal.item)}/{goal.quantity}"
                for goal in GOALS
            ),
            flush=True,
        )

    async def restore(self, item: str, qty: int = 1):
        if self.cmd.is_in_bank(item):
            await withdraw_from_bank(self.cmd, item, self.settings.request_timeout)
            if not self.has(item, qty):
                raise RuntimeError(
                    f"Unbanking {item} did not provide {qty} for farming."
                )

    def validate_requirements(self, quest: Quest, expected: dict[int, int]) -> dict:
        data = self.quest_data(quest.id)
        if data is None:
            raise RuntimeError(f"Quest {quest.id} metadata did not load.")
        actual = {int(item["ItemID"]): int(item["iQty"]) for item in data["turnin"]}
        if actual != expected:
            raise RuntimeError(
                f"Quest {quest.id} requirements changed: {actual}; "
                "stopping instead of consuming an unverified recipe."
            )
        for required in data.get("reqd") or ():
            item = self.cmd.get_player().get_item_inventory_by_id(required["ItemID"])
            if item is None or int(item.qty) < int(required["iQty"]):
                raise RuntimeError(
                    f"Quest {quest.id} requires inventory item "
                    f"{required['ItemID']} x{required['iQty']}."
                )
        return data

    def validate_choice(self, data: dict, goal: StockGoal):
        if not any(
            int(item["ItemID"]) == goal.reward_id
            and normalize(item["sName"]) == normalize(goal.item)
            and int(item["iQty"]) > 0
            for item in data["oRewards"]["itemsC"].values()
        ):
            raise RuntimeError(
                f"{goal.item} is not a selectable reward for quest {SWINDLE.id}."
            )

    async def exchange(self, goal: StockGoal):
        await self.enter(TURN_IN_MAP)
        await self.accept(SWINDLE.id, SWINDLE.requirement)
        data = self.validate_requirements(
            SWINDLE, {item_id: 1 for item_id in (*SWINDLE_PARTS, RUNE_ID)}
        )
        self.validate_choice(data, goal)
        for name in SWINDLE_PARTS.values():
            await self.restore(name)
        await self.bounded(
            self.rune_farmer.run(),
            "farming Dark Makai Rune in solo /evilmarsh",
            self.settings.item_timeout,
        )
        await self.enter(TURN_IN_MAP)
        current_goal = self.next_goal()
        if current_goal is None:
            return
        self.validate_choice(data, current_goal)
        before = item_count(self.cmd, current_goal.item)
        await self.turn_in(SWINDLE.id, current_goal.reward_id)
        await self.wait(
            lambda: item_count(self.cmd, current_goal.item) > before,
            f"receiving {current_goal.item} after Swindle's confirmed turn-in",
        )

    async def supplies(self):
        await self.enter(TURN_IN_MAP)
        await self.accept(SUPPLIES.id, SUPPLIES.requirement)
        self.validate_requirements(SUPPLIES, {67266: 1})
        await self.restore(RELIC)
        await self.bounded(
            self.relic_farmer.run(),
            "leeching Relic of Chaos from Ultra Chaos Alteon",
            self.settings.item_timeout,
        )
        await self.enter(TURN_IN_MAP)
        if self.next_goal() is None:
            return
        await self.turn_in(SUPPLIES.id)
        await self.wait(
            lambda: (
                not any(
                    normalize(item.item_name) in self.required_drops
                    for item in self.bot.pending_drops.values()
                )
            ),
            "confirming required Supplies reward pickups",
        )

    async def run(self):
        previous_relogin = self.bot.auto_relogin
        completed = skipped = False
        self.bot.auto_relogin = False
        self.bot.accept_all_drops = True
        self.bot.subscribe(self.on_message)
        try:
            self.connected()
            self.report()
            if self.next_goal() is not None:
                # Keep incomplete goal stacks out of the bank while earning rewards.
                for goal in GOALS:
                    if item_count(self.cmd, goal.item) < goal.quantity:
                        await self.restore(goal.item)
            while (goal := self.next_goal()) is not None:
                self.connected()
                if all(
                    item_count(self.cmd, name) >= 1 for name in SWINDLE_PARTS.values()
                ):
                    await self.exchange(goal)
                else:
                    await self.supplies()
                self.report()
            print("FARM COMPLETE: all Nulgath material stock goals met.", flush=True)
            completed = True
        except LeechUnavailable:
            skipped = True
            raise
        except (RuntimeError, TimeoutError, ConnectionError) as error:
            print(f"NULGATH MATERIAL ERROR: {error}", flush=True)
            raise
        finally:
            self.bot.unsubscribe(self.on_message)
            if completed or skipped:
                self.bot.auto_relogin = previous_relogin
            else:
                self.bot.stop_bot(user_triggered=True)


async def main(cmd: Command):
    await MaterialsRunner(cmd).run()


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
