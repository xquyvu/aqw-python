"""Farm 4 Unidentified 13. Run: python -u -m bot.nulgath.larvae."""

from bot.nulgath.core_nulgath import TARGET_ITEM, Material, farm_contracts
from core.command import Command
from core.quest_farm import FarmConfig, Quest, Screen
from core.script_runner import run_script

QUEST = Quest(2566, "Nulgath (Larvae)")
MATERIALS = (
    Material("Mana Energy for Nulgath", 1, "elemental", "Mana Golem"),
    Material("Charged Mana Energy for Nulgath", 5, "elemental", "Mana Falcon,Mana Imp"),
)
CONFIG = FarmConfig(
    name="Nulgath (Larvae)",
    quests=(QUEST,),
    class_name="Chaos Slayer Berserker",
    map_name="elemental",
    screen=Screen(monsters={"Mana Golem": None}),
    drops=(TARGET_ITEM, *(material.item for material in MATERIALS)),
    server="Alteon",
    mode="leech",
)


async def main(cmd: Command, *, stop_on_complete: bool = True):
    await farm_contracts(cmd, CONFIG, MATERIALS, stop_on_complete=stop_on_complete)


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
