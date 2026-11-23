"""Bounded, server-confirmed execution of one Lord of Order daily."""

import argparse
import asyncio
import json
import time
from dataclasses import dataclass
from typing import Callable, Literal

from core.command import Command
from core.script_runner import run_script
from core.utils import normalize
from templates.hunt import hunt_item


class QuestUnavailableError(RuntimeError):
    """The server explicitly rejected a quest's progress or daily access."""


@dataclass(frozen=True)
class Hunt:
    item: str
    map_name: str
    monster: str
    qty: int = 1
    boss: bool = True
    strategy: Literal["standard", "kitsune", "xiang"] = "standard"


@dataclass(frozen=True)
class Purchase:
    item: str
    map_name: str
    shop_id: int


@dataclass(frozen=True)
class Pickup:
    item: str
    map_name: str
    map_item_id: int
    qty: int = 1


@dataclass(frozen=True)
class SideQuest:
    item: str
    map_name: str
    quest_id: int
    steps: tuple[Hunt | Pickup, ...]
    requirement: str


Step = Hunt | Purchase | Pickup | SideQuest


@dataclass(frozen=True)
class Daily:
    id: int
    name: str
    steps: tuple[Step, ...]
    rewards: tuple[str, ...]
    choice: str | None = None
    reward_id: int = -1


@dataclass(frozen=True)
class Settings:
    farm_class: str = "Blaze Binder"
    solo_class: str = "Dragonslayer General"
    server: str = "Alteon"
    room_number: int = 1
    item_timeout: float = 3600
    request_timeout: float = 30
    xiang_class: str = "auto"


class DailyRunner:
    def __init__(self, cmd: Command, settings: Settings):
        self.cmd = cmd
        self.bot = cmd.bot
        self.settings = settings
        self.results: dict[tuple[str, int], dict] = {}

    def on_message(self, message: str):
        if not message.startswith("{"):
            return
        data = json.loads(message).get("b", {}).get("o", {})
        if isinstance(data, dict) and data.get("cmd") in ("acceptQuest", "ccqr"):
            self.results[(data["cmd"], int(data["QuestID"]))] = data

    def connected(self):
        if not self.cmd.is_still_connected():
            raise ConnectionError("Disconnected; this daily was not confirmed complete.")

    async def wait(self, predicate: Callable[[], bool], description: str):
        deadline = time.monotonic() + self.settings.request_timeout
        while True:
            self.connected()
            if predicate():
                return
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timed out {description}.")
            await self.cmd.sleep(100)

    async def bounded(self, operation, description: str, timeout: float | None = None):
        try:
            return await asyncio.wait_for(
                operation,
                timeout=timeout or self.settings.request_timeout,
            )
        except asyncio.TimeoutError as error:
            raise TimeoutError(f"Timed out {description}.") from error

    def quest_data(self, quest_id: int) -> dict | None:
        return next(
            (
                data
                for data in self.bot.loaded_quest_datas
                if int(data["QuestID"]) == quest_id
            ),
            None,
        )

    async def enter(self, map_name: str):
        self.connected()
        await self.bounded(
            self.cmd.join_map(map_name, roomNumber=self.settings.room_number),
            f"joining /{map_name}",
        )
        await self.wait(
            lambda: self.cmd.is_in_map(map_name) and not self.bot.is_joining_map,
            f"loading /{map_name}; check its story access requirements",
        )

    async def accept(self, quest_id: int, requirement: str):
        if self.quest_data(quest_id) is not None:
            return
        key = ("acceptQuest", quest_id)
        self.results.pop(key, None)
        await self.bounded(self.cmd.accept_quest(quest_id), f"accepting quest {quest_id}")
        await self.wait(
            lambda: key in self.results,
            f"waiting for acceptance of quest {quest_id}. {requirement}",
        )
        result = self.results[key]
        if int(result.get("bSuccess", 0)) != 1:
            raise RuntimeError(
                f"Cannot accept quest {quest_id}: "
                f"{result.get('msg') or 'server rejected the quest'}. {requirement}"
            )
        await self.wait(
            lambda: self.quest_data(quest_id) is not None,
            f"loading accepted quest {quest_id}",
        )

    async def turn_in(self, quest_id: int, reward_id: int = -1):
        if not self.cmd.can_turnin_quest(quest_id):
            raise RuntimeError(f"Quest {quest_id} still has missing turn-in requirements.")
        key = ("ccqr", quest_id)
        self.results.pop(key, None)
        await self.bounded(
            self.cmd.turn_in_quest(quest_id, reward_id),
            f"submitting quest {quest_id}",
        )
        await self.wait(
            lambda: key in self.results,
            f"waiting for turn-in confirmation for quest {quest_id}; "
            "check in-game before retrying",
        )
        result = self.results[key]
        if int(result.get("bSuccess", 0)) != 1:
            reason = result.get("msg") or "no reason supplied"
            error_type = (
                QuestUnavailableError
                if normalize(reason) in ("missing quest progress", "missing badge")
                else RuntimeError
            )
            raise error_type(
                f"Quest {quest_id} turn-in rejected: "
                f"{reason}."
            )

    def has(self, item: str, qty: int = 1) -> bool:
        return bool(
            self.cmd.is_in_inventory(item, qty)
            or self.cmd.is_in_inventory(item, qty, isTemp=True)
        )

    async def restore(self, item: str, qty: int = 1):
        if not self.has(item, qty) and self.cmd.is_in_bank(item):
            await self.bounded(self.cmd.bank_to_inv(item), f"unbanking {item}")
            await self.wait(
                lambda: self.has(item),
                f"confirming {item} moved from bank; check free inventory space",
            )

    async def equip(self, boss: bool, override: str | None = None):
        class_name = override or (
            self.settings.solo_class if boss else self.settings.farm_class
        )
        equipped = self.cmd.get_equipped_class()
        if equipped and normalize(equipped.item_name) == normalize(class_name):
            return
        success = await self.bounded(
            self.cmd.equip_item(class_name), f"equipping {class_name}"
        )
        if not success:
            raise RuntimeError(f"{class_name} must be in inventory or bank.")
        await self.wait(
            lambda: (
                (current := self.cmd.get_equipped_class()) is not None
                and normalize(current.item_name) == normalize(class_name)
            ),
            f"confirming {class_name} is equipped",
        )

    def xiang_class(self) -> str:
        if normalize(self.settings.xiang_class) != "auto":
            return self.settings.xiang_class
        for name in ("Dragon of Time", "Healer (Rare)", "Healer"):
            if self.cmd.is_in_inventory_or_bank(name):
                print(f"ULTRA XIANG: using {name}.", flush=True)
                return name
        print(
            "ULTRA XIANG WARNING: no Dragon of Time or Healer found; "
            f"using {self.settings.solo_class}. Bring a party if needed.",
            flush=True,
        )
        return self.settings.solo_class

    async def hunt(self, step: Hunt):
        if step.strategy != "kitsune":
            await hunt_item(
                self.cmd,
                item_name=step.item,
                item_qty=step.qty,
                map_name=step.map_name,
                room_number=self.settings.room_number,
                monster_name=step.monster,
                farming_logger=True,
            )
            return
        self.cmd.farming_logger(step.item, step.qty)
        while self.cmd.is_still_connected() and not self.has(step.item, step.qty):
            await self.cmd.jump_to_monster(step.monster)
            # Kitsune is invincible during its own Shapeshifted aura.
            if any(
                mon.hasAura("Shapeshifted")
                for mon in self.bot.monsters
                if normalize(mon.mon_name) == normalize(step.monster)
            ):
                await self.cmd.sleep(200)
                continue
            await self.cmd.use_next_skill([0, 1, 2, 3, 4], step.monster)
            await self.cmd.sleep(100)
        await self.cmd.leave_combat()

    async def perform(self, step: Step):
        qty = step.qty if isinstance(step, (Hunt, Pickup)) else 1
        self.cmd.add_drop(step.item)
        await self.restore(step.item, qty)
        if self.has(step.item, qty):
            return
        print(f"COLLECT {step.item} x{qty} | /{step.map_name}", flush=True)
        await self.enter(step.map_name)
        if isinstance(step, Hunt):
            await self.wait(
                lambda: bool(self.bot.monsters)
                and all(mon.mon_name and mon.frame for mon in self.bot.monsters),
                f"loading monsters in /{step.map_name}",
            )
            targets = {normalize(name) for name in step.monster.split(",")}
            if not any(
                normalize(mon.mon_name) in targets for mon in self.bot.monsters
            ):
                raise RuntimeError(
                    f"{step.monster} not found in /{step.map_name}; "
                    "check story progress or whether the map has changed."
                )
            await self.equip(
                step.boss,
                self.xiang_class() if step.strategy == "xiang" else None,
            )
            await self.bounded(
                self.hunt(step),
                f"farming {step.item} in /{step.map_name}; "
                "check prerequisites, inventory space, and party strength",
                self.settings.item_timeout,
            )
        elif isinstance(step, Purchase):
            await self.bounded(
                self.cmd.ensure_load_shop(step.shop_id),
                f"loading shop {step.shop_id}",
            )
            shop = self.cmd.get_loaded_shop(step.shop_id)
            if shop is None or not any(
                normalize(item.item_name) == normalize(step.item) for item in shop.items
            ):
                raise RuntimeError(f"{step.item} is not in shop {step.shop_id}.")
            await self.bounded(
                self.cmd.buy_item(step.shop_id, step.item),
                f"buying {step.item}",
            )
            await self.wait(
                lambda: self.has(step.item),
                f"confirming purchase of {step.item}; "
                "check gold, shop requirements, and free inventory space",
            )
        elif isinstance(step, Pickup):
            await self.bounded(
                self.cmd.get_map_item(step.map_item_id, step.qty),
                f"collecting map item {step.item}",
            )
            await self.wait(
                lambda: self.has(step.item, step.qty),
                f"receiving map item {step.item}",
            )
        else:
            await self.accept(step.quest_id, step.requirement)
            for requirement in step.steps:
                await self.perform(requirement)
            await self.enter(step.map_name)
            await self.turn_in(step.quest_id)
            await self.wait(
                lambda: self.has(step.item),
                f"receiving {step.item} from quest {step.quest_id}",
            )
        self.connected()
        if not self.has(step.item, qty):
            raise RuntimeError(f"Did not receive {step.item} x{qty}; stopping.")

    async def run(
        self, daily: Daily, *, stop_on_complete: bool = True,
        skip_unavailable: bool = False,
    ):
        # A disconnect must not restart a daily whose turn-in may have succeeded.
        auto_relogin = self.bot.auto_relogin
        completed = False
        unavailable = False
        self.bot.auto_relogin = False
        self.bot.subscribe(self.on_message)
        try:
            self.cmd.add_drop(list(daily.rewards))
            await self.enter("battleoff")
            await self.accept(
                daily.id,
                "Requires level 50, the previous daily completed, and no other "
                "Lord of Order daily completed since the server's daily reset.",
            )
            for step in daily.steps:
                await self.perform(step)
            await self.enter("battleoff")
            await self.turn_in(daily.id, daily.reward_id)
            if daily.choice is not None:
                await self.wait(
                    lambda: self.has(daily.choice),
                    f"receiving {daily.choice}; turn-in succeeded, so check "
                    "your inventory in-game before retrying",
                )
            print(
                f"COMPLETED {daily.id}: {daily.name}. "
                "This script will not start the next daily.",
                flush=True,
            )
            completed = True
        except QuestUnavailableError as error:
            print(f"LORD OF ORDER UNAVAILABLE [{daily.name}]: {error}", flush=True)
            if not skip_unavailable:
                raise
            unavailable = True
            print(
                "LORD OF ORDER: skipping this blocked daily; progress is unchanged. "
                "Complete the required story or wait for the next daily reset.",
                flush=True,
            )
        except (RuntimeError, TimeoutError, ConnectionError) as error:
            print(f"LORD OF ORDER ERROR [{daily.name}]: {error}", flush=True)
            raise
        finally:
            self.bot.unsubscribe(self.on_message)
            if (completed or unavailable) and not stop_on_complete:
                self.bot.auto_relogin = auto_relogin
            else:
                self.bot.stop_bot(user_triggered=True)


async def execute_day(cmd: Command, day: int, settings: Settings | None = None):
    from bot.lord_of_order.quests import DAILIES

    if not 1 <= day <= len(DAILIES):
        raise ValueError("Choose a Lord of Order day from 1 to 10.")
    await DailyRunner(cmd, settings or Settings()).run(DAILIES[day - 1])


def run_day(day: int):
    parser = argparse.ArgumentParser(description=f"Lord of Order daily {day}/10")
    parser.add_argument("--farm-class", default=Settings.farm_class)
    parser.add_argument("--solo-class", default=Settings.solo_class)
    parser.add_argument(
        "--xiang-class", default=Settings.xiang_class,
        help="Ultra Xiang class: auto prefers Dragon of Time, then Healer.",
    )
    parser.add_argument("--server", default=Settings.server)
    parser.add_argument("--room-number", type=int, default=Settings.room_number)
    parser.add_argument(
        "--item-timeout", type=float, default=Settings.item_timeout,
        help="Maximum seconds per farmed item (default: 3600).",
    )
    args = parser.parse_args()
    if (
        args.room_number <= 0
        or args.item_timeout <= 0
        or not all(
            value.strip()
            for value in (
                args.farm_class, args.solo_class, args.xiang_class, args.server
            )
        )
    ):
        parser.error("Room number and timeout must be positive; names must not be empty.")
    settings = Settings(
        farm_class=args.farm_class,
        solo_class=args.solo_class,
        server=args.server,
        room_number=args.room_number,
        item_timeout=args.item_timeout,
        xiang_class=args.xiang_class,
    )

    async def main(cmd: Command):
        await execute_day(cmd, day, settings)

    run_script(
        main,
        class_name=settings.farm_class,
        server=settings.server,
        room_number=settings.room_number,
    )
