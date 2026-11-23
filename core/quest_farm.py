"""Configuration-driven, single-screen quest and combat farming."""

import asyncio
import json
import time
from collections import Counter, defaultdict
from collections.abc import Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Literal

from core.command import Command
from core.leech import LeechRooms
from core.reputation import ReputationTracker
from core.script_runner import run_script
from core.utils import normalize
from model.monster import Monster

Combo = Callable[[Command, str, int], Awaitable[int]]


@dataclass(frozen=True)
class Quest:
    id: int
    name: str
    requirement: str = "Check its story prerequisites."
    optional: bool = False
    repeat: bool = True

    def __post_init__(self):
        if self.id <= 0 or not self.name.strip():
            raise ValueError("A quest needs a positive ID and a name.")


@dataclass(frozen=True)
class Screen:
    """Count all spawns; an empty roster targets every monster in a fixed cell."""

    monsters: Mapping[str, int | None]
    cell: str | None = None
    pad: str = "Left"

    def __post_init__(self):
        names = [normalize(name) for name in self.monsters]
        if not all(names) or len(names) != len(set(names)):
            raise ValueError("Screen monster names must be nonempty and unique.")
        if not names and self.cell is None:
            raise ValueError("Configure screen monsters or a fixed cell.")
        if any(count is not None and count <= 0 for count in self.monsters.values()):
            raise ValueError("Screen monster counts must be positive or None.")
        if not self.pad.strip() or (self.cell is not None and not self.cell.strip()):
            raise ValueError("Screen cell and pad names must not be empty.")

    def select(self, monsters: Iterable[Monster]) -> str:
        cells = defaultdict(Counter)
        for monster in monsters:
            if monster.frame:
                cells[monster.frame][normalize(monster.mon_name)] += 1
        for cell, roster in sorted(cells.items()):
            if self.cell is not None and normalize(cell) != normalize(self.cell):
                continue
            if all(
                roster[normalize(name)] >= 1
                if count is None
                else roster[normalize(name)] == count
                for name, count in self.monsters.items()
            ):
                return cell
        wanted = (
            ", ".join(
                name if count is None else f"{name} x{count}"
                for name, count in self.monsters.items()
            )
            or "any monsters"
        )
        raise RuntimeError(
            f"No matching farming screen for {wanted}"
            f"{f' in cell {self.cell}' if self.cell else ''}."
        )


@dataclass(frozen=True)
class FarmConfig:
    name: str
    quests: tuple[Quest, ...]
    map_name: str
    screen: Screen
    class_name: str = "Blaze Binder"
    combo: Literal["ready"] | Combo = "ready"
    auto_attack: bool = False
    reputation: str | None = None
    drops: tuple[str, ...] = ()
    server: str = "Alteon"
    room_number: int = 1
    mode: Literal["solo", "leech"] = "leech"
    solo_room_number: int = 90999
    track_exp: bool = False
    quest_timeout: float = 30
    map_timeout: float = 30
    report_interval: float = 60

    def __post_init__(self):
        ids = [quest.id for quest in self.quests]
        if len(ids) != len(set(ids)):
            raise ValueError("Configured quest IDs must be unique.")
        if not all(
            value.strip()
            for value in (self.name, self.class_name, self.map_name, self.server)
        ):
            raise ValueError("Farm, class, map and server names must not be empty.")
        if self.combo != "ready" and not callable(self.combo):
            raise ValueError("Combo must be 'ready' or an async combo function.")
        if self.mode not in ("solo", "leech"):
            raise ValueError("Farming mode must be 'solo' or 'leech'.")
        if (
            min(self.room_number, self.solo_room_number) <= 0
            or min(self.quest_timeout, self.map_timeout, self.report_interval) <= 0
        ):
            raise ValueError(
                "Room number, timeouts and report interval must be positive."
            )

    @property
    def effective_room_number(self) -> int:
        return self.room_number if self.mode == "leech" else self.solo_room_number

    @property
    def room_name(self) -> str:
        return f"{self.map_name}-{self.effective_room_number}"


class QuestFarmer:
    def __init__(
        self,
        cmd: Command,
        config: FarmConfig,
        stop_when: Callable[[], bool] | None = None,
    ):
        self.cmd = cmd
        self.bot = cmd.bot
        self.config = config
        self.stop_when = stop_when
        self.completed = dict.fromkeys((quest.id for quest in config.quests), 0)
        self.inactive_quests: set[int] = set()
        self.accept_results: dict[int, dict] = {}
        self.turn_in_results: dict[int, dict] = {}
        self.reputation: ReputationTracker | None = None
        self.skill_index = 0
        self.last_report: float | None = None
        self.last_screen: tuple[str, str] | None = None
        self.starting_exp = 0
        self.leech_rooms = LeechRooms(cmd, config.name)

    def goal_reached(self) -> bool:
        return self.stop_when is not None and self.stop_when()

    def quest_data(self, quest_id: int) -> dict | None:
        return next(
            (
                quest
                for quest in self.bot.loaded_quest_datas
                if str(quest["QuestID"]) == str(quest_id)
            ),
            None,
        )

    def on_message(self, message: str):
        if not message.startswith("{"):
            return
        data = json.loads(message).get("b", {}).get("o", {})
        if isinstance(data, dict) and data.get("cmd") in ("acceptQuest", "ccqr"):
            quest_id = int(data["QuestID"])
            if quest_id in self.completed:
                results = (
                    self.accept_results
                    if data["cmd"] == "acceptQuest"
                    else self.turn_in_results
                )
                results[quest_id] = data

    async def ensure_room(self):
        config, cmd, bot = self.config, self.cmd, self.bot
        if config.mode == "leech":
            await self.leech_rooms.ensure(config.map_name, config.map_timeout)
            return
        if not bot.is_joining_map:
            if cmd.is_not_in_map(config.map_name):
                await cmd.join_map(
                    config.map_name, roomNumber=config.effective_room_number
                )
            elif config.mode == "solo" and normalize(bot.areaName) != normalize(
                config.room_name
            ):
                # join_map skips transfers to a different room of the same map.
                await cmd.leave_combat()
                if not cmd.is_still_connected():
                    return
                bot.is_joining_map = True
                bot.write_message(
                    f"%xt%zm%cmd%1%tfer%{bot.player.USER}%{config.room_name}%"
                )
        deadline = time.monotonic() + config.map_timeout
        while cmd.is_still_connected():
            if cmd.is_in_map(config.map_name) and not bot.is_joining_map:
                if config.mode == "solo" and normalize(bot.areaName) != normalize(
                    config.room_name
                ):
                    raise RuntimeError(
                        f"Requested {config.room_name}, but joined {bot.areaName}. "
                        "Stopping instead of farming in another room."
                    )
                if bot.monsters and all(
                    monster.mon_name and monster.frame for monster in bot.monsters
                ):
                    return
            if time.monotonic() >= deadline:
                raise TimeoutError(f"{config.room_name} did not load in time.")
            await cmd.sleep(200)

    def stop_if_reputation_max(self) -> bool:
        if self.reputation is None or not self.reputation.is_max:
            return False
        self.reputation.log()
        print(
            f"FARM COMPLETE: {self.config.reputation} reputation is rank 10.",
            flush=True,
        )
        self.bot.stop_bot(user_triggered=True)
        return True

    def select_screen(self) -> str:
        cell = self.config.screen.select(self.bot.monsters)
        location = (self.bot.areaName, cell)
        if location != self.last_screen:
            roster = Counter(
                monster.mon_name
                for monster in self.bot.monsters
                if normalize(monster.frame or "") == normalize(cell)
            )
            monsters = ", ".join(
                f"{name} x{count}" for name, count in sorted(roster.items())
            )
            print(
                f"SCREEN {location[0]}:{cell}, pad={self.config.screen.pad} | {monsters}",
                flush=True,
            )
            self.last_screen = location
        return cell

    def skip_optional(self, quest: Quest, reason: str):
        self.inactive_quests.add(quest.id)
        print(
            f"SKIPPING optional quest {quest.id}: {quest.name} | {reason}",
            flush=True,
        )

    async def accept_optional(self, quest: Quest):
        if self.quest_data(quest.id) is not None:
            return
        await self.cmd.accept_quest(quest.id)
        while self.cmd.is_still_connected() and self.quest_data(quest.id) is None:
            result = self.accept_results.get(quest.id)
            if result is not None and int(result.get("bSuccess", -1)) == 0:
                self.skip_optional(
                    quest,
                    result.get("msg")
                    or "Server rejected it; it may already be completed or locked.",
                )
                return
            await self.cmd.sleep(100)

    async def accept(self, quest: Quest):
        if (
            self.goal_reached()
            or self.stop_if_reputation_max()
            or quest.id in self.inactive_quests
        ):
            return
        self.accept_results.pop(quest.id, None)
        try:
            await asyncio.wait_for(
                self.accept_optional(quest)
                if quest.optional
                else self.cmd.ensure_accept_quest(quest.id),
                timeout=self.config.quest_timeout,
            )
        except TimeoutError as error:
            raise TimeoutError(
                f"Accepting {quest.name} ({quest.id}) timed out."
            ) from error
        if (
            self.cmd.is_still_connected()
            and quest.id not in self.inactive_quests
            and self.quest_data(quest.id) is None
        ):
            raise RuntimeError(
                f"Could not accept {quest.name} ({quest.id}). {quest.requirement}"
            )

    async def turn_in(self, quest: Quest):
        if self.goal_reached():
            return
        self.turn_in_results.pop(quest.id, None)
        try:
            await asyncio.wait_for(
                self.cmd.turn_in_quest(quest.id), timeout=self.config.quest_timeout
            )
        except TimeoutError as error:
            raise TimeoutError(
                f"Turning in {quest.name} ({quest.id}) timed out."
            ) from error
        deadline = time.monotonic() + self.config.quest_timeout
        while self.cmd.is_still_connected():
            result = self.turn_in_results.get(quest.id)
            if result is not None:
                if int(result.get("bSuccess", 0)) != 1:
                    reason = result.get("msg") or "no reason supplied"
                    if (
                        quest.optional
                        and not quest.repeat
                        and normalize(reason) == "missing badge"
                    ):
                        self.skip_optional(quest, f"Turn-in rejected: {reason}")
                        return
                    raise RuntimeError(
                        f"Turn-in rejected for {quest.name} ({quest.id}): {reason}"
                    )
                self.completed[quest.id] += 1
                print(
                    f"COMPLETED {quest.id}: {quest.name} | "
                    f"session turn-ins: {self.completed[quest.id]}",
                    flush=True,
                )
                if self.goal_reached() or self.stop_if_reputation_max():
                    return
                if quest.repeat:
                    await self.accept(quest)
                else:
                    self.inactive_quests.add(quest.id)
                return
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"No turn-in confirmation for {quest.name} ({quest.id})."
                )
            await self.cmd.sleep(100)

    def report(self):
        if self.reputation is not None:
            self.reputation.log()
        now = time.monotonic()
        if (
            self.last_report is not None
            and now - self.last_report < self.config.report_interval
        ):
            return
        self.last_report = now
        if self.config.track_exp:
            gained = self.bot.player.EXPFARMED - self.starting_exp
            print(f"EXP farmed this session: {gained:,}", flush=True)
        for quest in self.config.quests:
            if quest.id in self.inactive_quests:
                continue
            data = self.quest_data(quest.id)
            if data is None:
                continue
            progress = []
            for item in data["turnin"]:
                item_id = int(item["ItemID"])
                held = self.bot.player.get_item_inventory_by_id(
                    item_id
                ) or self.bot.player.get_item_temp_inventory_by_id(item_id)
                name = data["oItems"][str(item_id)]["sName"]
                progress.append(
                    f"{name}: {int(held.qty) if held else 0}/{item['iQty']}"
                )
            print(
                f"PROGRESS {quest.id}: {quest.name} | {', '.join(progress)} | "
                f"session turn-ins: {self.completed[quest.id]}",
                flush=True,
            )

    async def attack(self, cell: str):
        if self.config.mode == "leech":
            await self.leech_rooms.guard(
                self.config.map_name,
                self.config.map_timeout,
                lambda: self.attack_screen(self.select_screen()),
            )
        else:
            await self.attack_screen(cell)

    async def attack_screen(self, cell: str):
        if self.goal_reached():
            return
        if self.cmd.is_not_in_cell(cell):
            await self.cmd.jump_cell(cell, self.config.screen.pad)
        if (
            not self.cmd.is_still_connected()
            or self.goal_reached()
            or self.stop_if_reputation_max()
        ):
            return
        targets = ",".join(self.config.screen.monsters) or "*"
        combo = self.config.combo
        if callable(combo):
            self.skill_index = await combo(self.cmd, targets, self.skill_index)
        else:
            await self.cmd.use_next_skill([0, 1, 2, 3, 4], targets)
        if (
            self.config.auto_attack
            and self.cmd.is_still_connected()
            and not self.goal_reached()
            and not self.stop_if_reputation_max()
        ):
            await self.cmd.use_skill(0, targets)

    async def run(self):
        config, cmd = self.config, self.cmd
        if self.goal_reached():
            return
        if config.reputation:
            self.reputation = ReputationTracker(self.bot.player, config.reputation)
            self.reputation.log()
            if self.stop_if_reputation_max():
                return
        self.bot.farmClass = config.class_name
        self.bot.auto_adjust_skill_delay = True
        if not await cmd.equip_item(config.class_name):
            raise RuntimeError(f"{config.class_name} must be in inventory or bank.")
        equipped = cmd.get_equipped_class()
        if equipped is None or normalize(equipped.item_name) != normalize(
            config.class_name
        ):
            raise RuntimeError(f"{config.class_name} equipment was not confirmed.")
        if not cmd.is_still_connected():
            return
        if config.track_exp:
            self.starting_exp = self.bot.player.EXPFARMED
        whitelist = self.bot.items_drop_whitelist
        for name in config.drops:
            if normalize(name) not in {normalize(item) for item in whitelist}:
                whitelist.append(name)
        self.bot.subscribe(self.on_message)
        try:
            await self.ensure_room()
            if not cmd.is_still_connected() or self.goal_reached():
                return
            self.select_screen()
            for quest in config.quests:
                await self.accept(quest)
                if not cmd.is_still_connected() or self.goal_reached():
                    return
            print(
                f"Farming {config.name} on {self.bot.server}, "
                f"{self.bot.areaName} ({config.mode}) with {config.class_name}. "
                "Press Ctrl+C to stop.",
                flush=True,
            )
            self.report()
            while cmd.is_still_connected() and (
                not config.quests
                or any(quest.id not in self.inactive_quests for quest in config.quests)
            ):
                if self.goal_reached() or self.stop_if_reputation_max():
                    return
                await self.ensure_room()
                if not cmd.is_still_connected() or self.goal_reached():
                    return
                cell = self.select_screen()
                for quest in config.quests:
                    if self.goal_reached() or self.stop_if_reputation_max():
                        return
                    if quest.id in self.inactive_quests:
                        continue
                    if self.quest_data(quest.id) is None:
                        await self.accept(quest)
                    if not cmd.is_still_connected() or self.goal_reached():
                        return
                    if cmd.can_turnin_quest(quest.id):
                        await self.turn_in(quest)
                    if not cmd.is_still_connected() or self.goal_reached():
                        return
                if config.quests and all(
                    quest.id in self.inactive_quests for quest in config.quests
                ):
                    return
                self.report()
                await self.attack(cell)
                await cmd.sleep(100)
        finally:
            self.bot.unsubscribe(self.on_message)


async def farm_quests(cmd: Command, config: FarmConfig):
    try:
        await QuestFarmer(cmd, config).run()
    except (RuntimeError, TimeoutError) as error:
        print(f"FARM ERROR [{config.name}]: {error}", flush=True)
        cmd.bot.stop_bot(user_triggered=True)
        raise


def run_farm(config: FarmConfig):
    async def main(cmd: Command):
        await farm_quests(cmd, config)

    run_script(
        main,
        class_name=config.class_name,
        server=config.server,
        room_number=config.effective_room_number,
        leech=config.mode == "leech",
    )
