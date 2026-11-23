"""Server-confirmed inventory transfers for multi-stage scripts."""

import asyncio
import json
import time

from core.command import Command


async def withdraw_from_bank(cmd: Command, item_name: str, timeout: float = 30):
    item = cmd.get_player().get_item_bank(item_name)
    if item is None:
        raise RuntimeError(f"{item_name} is not in the bank.")
    result: dict | None = None

    def on_message(message: str):
        nonlocal result
        if message.startswith("{"):
            data = json.loads(message).get("b", {}).get("o", {})
            if (
                isinstance(data, dict)
                and data.get("cmd") == "bankToInv"
                and str(data.get("ItemID")) == str(item.item_id)
            ):
                result = data

    cmd.bot.subscribe(on_message)
    try:
        deadline = time.monotonic() + timeout
        await asyncio.wait_for(cmd.bank_to_inv(item_name), timeout=timeout)
        while cmd.is_still_connected():
            if result is not None:
                if int(result.get("bSuccess", 1)) != 1:
                    reason = result.get("msg") or result.get("sMsg") or "request rejected"
                    raise RuntimeError(f"Could not unbank {item_name}: {reason}.")
                return
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Unbanking {item_name} was not confirmed by the server.")
            await cmd.sleep(100)
        raise ConnectionError(f"Disconnected while unbanking {item_name}.")
    finally:
        cmd.bot.unsubscribe(on_message)
