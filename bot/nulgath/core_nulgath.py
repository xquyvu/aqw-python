"""Shared material-quest loop for farming Unidentified 13."""

from dataclasses import dataclass, replace

from core.command import Command
from core.quest_farm import FarmConfig, QuestFarmer
from core.utils import normalize
from templates.hunt import hunt_item

TARGET_ITEM = "Unidentified 13"
TARGET_QTY = 4


@dataclass(frozen=True)
class Material:
    item: str
    qty: int
    map_name: str
    monsters: str


def contract_count(cmd: Command) -> int:
    player = cmd.get_player()
    return sum(
        int(item.qty)
        for item in (
            player.get_item_inventory(TARGET_ITEM),
            player.get_item_bank(TARGET_ITEM),
        )
        if item is not None
    )


def stop_if_complete(cmd: Command, *, stop_on_complete: bool = True) -> bool:
    count = contract_count(cmd)
    if count < TARGET_QTY:
        return False
    print(f"FARM COMPLETE: {TARGET_ITEM}: {count}/{TARGET_QTY}.", flush=True)
    if stop_on_complete:
        cmd.bot.stop_bot(user_triggered=True)
    return True


async def farm_contracts(
    cmd: Command,
    config: FarmConfig,
    materials: tuple[Material, ...],
    *,
    stop_on_complete: bool = True,
):
    quest, = config.quests
    farmer = QuestFarmer(cmd, config)
    cmd.bot.accept_all_drops = True
    try:
        if stop_if_complete(cmd, stop_on_complete=stop_on_complete):
            return
        cmd.bot.farmClass = config.class_name
        cmd.bot.auto_adjust_skill_delay = True
        if not await cmd.equip_item(config.class_name):
            raise RuntimeError(f"{config.class_name} must be in inventory or bank.")
        equipped = cmd.get_equipped_class()
        if equipped is None or normalize(equipped.item_name) != normalize(
            config.class_name
        ):
            raise RuntimeError(f"{config.class_name} equipment was not confirmed.")
        print(
            f"Farming {config.name} on {cmd.bot.server} ({config.mode}) "
            f"with {config.class_name} | "
            f"{TARGET_ITEM}: {contract_count(cmd)}/{TARGET_QTY} (inventory + bank).",
            flush=True,
        )
        cmd.bot.subscribe(farmer.on_message)
        try:
            while cmd.is_still_connected():
                if stop_if_complete(cmd, stop_on_complete=stop_on_complete):
                    return
                await farmer.accept(quest)
                if not cmd.is_still_connected():
                    return
                data = farmer.quest_data(quest.id)
                if data is None:
                    raise RuntimeError(f"Quest {quest.id} data is not loaded.")
                for required in data.get("reqd") or ():
                    item_id = str(required["ItemID"])
                    held = cmd.get_player().get_item_inventory_by_id(item_id)
                    qty = int(required["iQty"])
                    if held is None or int(held.qty) < qty:
                        name = data.get("oReqd", {}).get(item_id, {}).get(
                            "sName", f"item {item_id}"
                        )
                        raise RuntimeError(
                            f"Quest {quest.id} requires {name} x{qty} in inventory "
                            "to turn in; acceptance alone does not grant access."
                        )
                generation = cmd.bot.session_generation
                restart_materials = False
                for material in materials:
                    if not cmd.is_still_connected():
                        return
                    if cmd.is_in_inventory(
                        material.item, material.qty
                    ) or cmd.is_in_inventory(
                        material.item, material.qty, isTemp=True
                    ):
                        continue
                    farmer.config = replace(config, map_name=material.map_name)
                    await farmer.ensure_room()
                    if not cmd.is_still_connected():
                        return
                    if cmd.bot.session_generation != generation:
                        print(
                            "Server changed; rechecking all quest materials "
                            "because temporary items do not survive logout.",
                            flush=True,
                        )
                        restart_materials = True
                        break
                    sources = {
                        normalize(name) for name in material.monsters.split(",")
                    }
                    if not any(
                        normalize(mon.mon_name) in sources and mon.frame
                        for mon in cmd.bot.monsters
                    ):
                        raise RuntimeError(
                            f"No {material.monsters} found in {material.map_name}."
                        )
                    async def hunt():
                        await hunt_item(
                            cmd,
                            item_name=material.item,
                            item_qty=material.qty,
                            map_name=material.map_name,
                            room_number=config.effective_room_number,
                            monster_name=material.monsters,
                            farming_logger=True,
                        )

                    if config.mode == "leech":
                        finished = await farmer.leech_rooms.guard(
                            material.map_name, config.map_timeout, hunt
                        )
                        if not finished or cmd.bot.session_generation != generation:
                            restart_materials = True
                            break
                    else:
                        await hunt()
                if restart_materials:
                    continue
                if not cmd.is_still_connected():
                    return
                if stop_if_complete(cmd, stop_on_complete=stop_on_complete):
                    return
                if not cmd.can_turnin_quest(quest.id):
                    raise RuntimeError(
                        f"Quest {quest.id} still has missing turn-in requirements."
                    )
                await farmer.turn_in(quest)
                print(
                    f"PROGRESS {TARGET_ITEM}: {contract_count(cmd)}/{TARGET_QTY} "
                    "(inventory + bank).",
                    flush=True,
                )
                await cmd.sleep(200)
        finally:
            cmd.bot.unsubscribe(farmer.on_message)
    except (RuntimeError, TimeoutError) as error:
        print(f"FARM ERROR [{config.name}]: {error}", flush=True)
        cmd.bot.stop_bot(user_triggered=True)
        raise
