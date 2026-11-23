"""Bounded item farming that returns without disconnecting the session."""

from core.command import Command
from core.quest_farm import FarmConfig, QuestFarmer
from core.utils import normalize


def item_count(cmd: Command, item_name: str) -> int:
    player = cmd.get_player()
    return sum(
        int(item.qty)
        for item in (
            player.get_item_inventory(item_name),
            player.get_item_bank(item_name),
        )
        if item is not None
    )


async def farm_item(
    cmd: Command, config: FarmConfig, item_name: str, quantity: int = 1
):
    cmd.bot.accept_all_drops = True
    if not cmd.is_still_connected():
        return
    count = item_count(cmd, item_name)
    if count >= quantity:
        print(
            f"FARM COMPLETE: {item_name} already owned ({count}/{quantity}).",
            flush=True,
        )
        return

    farmer = QuestFarmer(cmd, config)
    try:
        cmd.bot.farmClass = config.class_name
        cmd.bot.auto_adjust_skill_delay = True
        if not await cmd.equip_item(config.class_name):
            raise RuntimeError(f"{config.class_name} must be in inventory or bank.")
        if not cmd.is_still_connected():
            return
        equipped = cmd.get_equipped_class()
        if equipped is None or normalize(equipped.item_name) != normalize(
            config.class_name
        ):
            raise RuntimeError(f"{config.class_name} equipment was not confirmed.")
        cmd.add_drop(item_name)
        print(
            f"Farming {item_name} on {cmd.bot.server}, "
            f"{config.room_name} ({config.mode}) with {config.class_name} | "
            f"{count}/{quantity} (inventory + bank).",
            flush=True,
        )
        while cmd.is_still_connected() and item_count(cmd, item_name) < quantity:
            await farmer.ensure_room()
            if not cmd.is_still_connected():
                return
            if item_count(cmd, item_name) >= quantity:
                break
            await farmer.attack(farmer.select_screen())
            await cmd.sleep(100)
        if cmd.is_still_connected():
            await cmd.leave_combat()
            print(
                f"FARM COMPLETE: {item_name} "
                f"{item_count(cmd, item_name)}/{quantity}.",
                flush=True,
            )
    except (RuntimeError, TimeoutError) as error:
        print(f"FARM ERROR [{config.name}]: {error}", flush=True)
        cmd.bot.stop_bot(user_triggered=True)
        raise
