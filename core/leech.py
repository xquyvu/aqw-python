"""Bounded public-room selection shared by leech farms."""

import asyncio
import json
import time
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.command import Command

SERVERS = ("Alteon", "Artix", "Twilly")
MAX_ATTEMPTS = 4
POLL_INTERVAL = 0.25


class ServerUnavailableError(ConnectionError):
    pass


class LeechUnavailable(Exception):
    pass


class LeechRooms:
    def __init__(self, cmd: "Command", task_name: str):
        self.cmd = cmd
        self.task_name = task_name
        self.server_index = 0
        bot = cmd.bot
        if bot.leech_mode and bot.session_generation == 1:
            self.server_index = next(
                (index for index, server in enumerate(SERVERS) if server.lower() == bot.server.lower()),
                0,
            )
        self.selected = False
        self.last_check_report: float | None = None

    def has_other_players(self) -> bool:
        bot = self.cmd.bot
        return bot.username_id is not None and any(
            str(user_id) != str(bot.username_id) for user_id in bot.user_ids
        )

    async def guard(
        self, map_name: str, timeout: float, action: Callable[[], Awaitable[None]]
    ) -> bool:
        await self.ensure(map_name, timeout)
        bot = self.cmd.bot
        previous_guard = bot.leech_combat_guard

        def populated() -> bool:
            return (
                self.cmd.is_in_map(map_name)
                and not bot.is_joining_map
                and self.has_other_players()
            )

        async def watch():
            while self.cmd.is_still_connected():
                if not populated():
                    return
                now = time.monotonic()
                if self.last_check_report is None or now - self.last_check_report >= 60:
                    others = len(
                        {
                            str(user_id) for user_id in bot.user_ids
                            if str(user_id) != str(bot.username_id)
                        }
                    )
                    print(
                        f"LEECH CHECK [{self.task_name}]: {bot.server}, "
                        f"{bot.areaName}; {others} other player(s) present.",
                        flush=True,
                    )
                    self.last_check_report = now
                await asyncio.sleep(POLL_INTERVAL)
            raise ConnectionError("Disconnected while monitoring the leech room.")

        async def fight():
            if populated():
                await action()
                return True
            return False

        bot.leech_combat_guard = populated
        worker = asyncio.create_task(fight())
        monitor = asyncio.create_task(watch())
        try:
            done, _ = await asyncio.wait(
                (worker, monitor), return_when=asyncio.FIRST_COMPLETED
            )
            if worker in done:
                if await worker:
                    return True
            else:
                await monitor
            worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)
            print(
                f"LEECH [{self.task_name}]: room is empty; "
                "stopping combat and searching again.",
                flush=True,
            )
            if not bot.player.ISDEAD:
                bot.jump_cell("Enter", "Spawn")
            self.selected = False
            self.server_index = 0
            await self.ensure(map_name, timeout)
            return False
        finally:
            for task in (worker, monitor):
                task.cancel()
            await asyncio.gather(worker, monitor, return_exceptions=True)
            bot.leech_combat_guard = previous_guard

    async def join(self, map_name: str, timeout: float, *, retry: bool = False):
        cmd, bot = self.cmd, self.cmd.bot
        rejected = False

        def on_message(message: str):
            nonlocal rejected
            text = ""
            if message.startswith(("%xt%warning%", "%xt%server%")):
                text = message.split("%")[4]
            elif message.startswith("{"):
                data = json.loads(message).get("b", {}).get("o", {})
                if isinstance(data, dict) and data.get("cmd") in ("warning", "server"):
                    text = data.get("msg") or data.get("sMsg") or ""
            text = text.lower()
            if "already" in text and ("room" in text or "map" in text):
                rejected = True

        bot.subscribe(on_message)
        try:
            if not bot.is_joining_map and (retry or cmd.is_not_in_map(map_name)):
                await cmd.leave_combat()
                if not cmd.is_still_connected():
                    raise ConnectionError("Disconnected while selecting a leech room.")
                bot.is_joining_map = True
                # A bare map name asks the server to allocate a public room.
                error = bot.write_message(
                    f"%xt%zm%cmd%1%tfer%{bot.player.USER}%{map_name}%"
                )
                if error is not None:
                    raise ConnectionError(error)
            deadline = time.monotonic() + timeout
            while cmd.is_still_connected():
                if rejected:
                    bot.is_joining_map = False
                    return
                if (
                    cmd.is_in_map(map_name)
                    and not bot.is_joining_map
                    and bot.username_id is not None
                    and bot.monsters
                    and all(mon.mon_name and mon.frame for mon in bot.monsters)
                ):
                    return
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Public room /{map_name} did not load in time.")
                await cmd.sleep(200)
            raise ConnectionError("Disconnected while selecting a leech room.")
        finally:
            bot.unsubscribe(on_message)

    async def ensure(self, map_name: str, timeout: float):
        cmd, bot = self.cmd, self.cmd.bot
        if (
            self.selected
            and cmd.is_in_map(map_name)
            and not bot.is_joining_map
            and self.has_other_players()
        ):
            return
        if self.selected and cmd.is_in_map(map_name) and not self.has_other_players():
            print(
                f"LEECH [{self.task_name}]: other players left; searching again.",
                flush=True,
            )
            self.selected = False
            self.server_index = 0
        attempts = 0
        origin = bot.server
        for index in range(self.server_index, len(SERVERS)):
            self.server_index = index
            server = SERVERS[index]
            # Only Alteon gets the extra /join; the other two are fallbacks.
            for retry in ((False, True) if index == 0 else (False,)):
                attempts += 1
                print(
                    f"LEECH [{self.task_name}]: attempt {attempts}/{MAX_ATTEMPTS}, "
                    f"{server} /{map_name}{' (rejoin)' if retry else ''}.",
                    flush=True,
                )
                try:
                    if (
                        bot.server.lower() != server.lower()
                        or not cmd.is_still_connected()
                        or bot.player.ISDEAD
                    ):
                        await bot.switch_server(server, timeout=timeout)
                    await self.join(map_name, timeout, retry=retry)
                except ServerUnavailableError as error:
                    print(f"LEECH: {server} unavailable: {error}", flush=True)
                    break
                if cmd.is_in_map(map_name) and self.has_other_players():
                    self.selected = True
                    print(
                        f"LEECH READY [{self.task_name}]: {bot.server}, {bot.areaName}.",
                        flush=True,
                    )
                    return
                print(f"LEECH: no populated /{map_name} room selected on {server}.", flush=True)
                if attempts >= MAX_ATTEMPTS:
                    break
        if not cmd.is_still_connected():
            # The next task still needs a session, even if none can host a leech.
            await bot.switch_server(origin, timeout=timeout)
        raise LeechUnavailable(
            f"{self.task_name}: no populated room after {attempts} attempts "
            f"(limit {MAX_ATTEMPTS}; server list exhausted)."
        )
