"""Single-account script startup with bounded login retries."""

import asyncio
import time
from pathlib import Path
from typing import Awaitable, Callable

from dotenv import dotenv_values

from core.bot import Bot
from core.leech import LeechUnavailable, ServerUnavailableError


class StartupError(RuntimeError):
    pass


async def start_session(bot: Bot, main: Callable[..., Awaitable[None]]):
    login_rejected = False

    def check_login(message):
        nonlocal login_rejected
        if message.startswith("%xt%loginResponse%"):
            if bot.leech_mode and "full" in message.lower():
                return
            login_rejected = message.split("%")[4].lower() not in ("true", "1")

    bot.subscribe(check_login)
    task = asyncio.create_task(bot.start_bot(main))
    try:
        deadline = time.monotonic() + (240 if bot.leech_mode else 60)
        while not bot.is_char_load_complete:
            if task.done():
                await task
                raise StartupError("Login ended before the character loaded.")
            if login_rejected:
                raise StartupError("The game server rejected this login session.")
            if time.monotonic() >= deadline:
                raise StartupError("Character loading timed out after 60 seconds.")
            await asyncio.sleep(0.2)
        bot.unsubscribe(check_login)
        await task
    finally:
        bot.unsubscribe(check_login)
        if not task.done():
            bot.stop_bot(user_triggered=True)
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)


def run_script(
    main: Callable[..., Awaitable[None]],
    *,
    class_name: str,
    server: str,
    room_number: int,
    leech: bool = False,
):
    config = dotenv_values(Path(__file__).resolve().parents[1] / ".env")
    settings = {}
    for key in ("USERNAME_AQW", "PASSWORD_AQW"):
        entries = (config.get(key) or "").strip().strip("[]").split(",")
        if len(entries) != 1 or not entries[0].strip():
            raise SystemExit(f"Configure exactly one account in .env ({key}).")
        settings[key] = entries[0].strip()
    for attempt in range(3):
        bot = Bot(
            roomNumber=room_number,
            isScriptable=True,
            autoRelogin=True,
            autoAdjustSkillDelay=True,
            farmClass=class_name,
            showLog=False,
            showDebug=False,
            showChat=False,
        )
        bot.set_login_info(
            settings["USERNAME_AQW"], settings["PASSWORD_AQW"], server
        )
        bot.leech_mode = leech
        try:
            asyncio.run(start_session(bot, main))
            return
        except (LeechUnavailable, ServerUnavailableError) as error:
            print(f"LEECH SKIPPED: {error}", flush=True)
            bot.stop_bot(user_triggered=True)
            return
        except StartupError as error:
            print(f"STARTUP ERROR ({attempt + 1}/3): {error}", flush=True)
            if attempt == 2:
                raise SystemExit("Unable to start farming after 3 attempts.")
            print("Retrying login in 35 seconds.", flush=True)
            time.sleep(35)
        except KeyboardInterrupt:
            bot.stop_bot(user_triggered=True)
            return
