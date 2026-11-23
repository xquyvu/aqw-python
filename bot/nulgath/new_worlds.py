"""Farm 4 Unidentified 13. Run: python -u -m bot.nulgath.new_worlds."""

from bot.nulgath.core_nulgath import TARGET_ITEM, Material, farm_contracts
from core.command import Command
from core.quest_farm import FarmConfig, Quest, Screen
from core.script_runner import run_script

QUEST = Quest(6183, "New Worlds, New Opportunities")
MATERIALS = (
    Material("Slugfit Horn", 5, "mobius", "Slugfit"),
    Material("Imp Flame", 3, "mobius", "Fire Imp"),
    Material("Makai Fang", 5, "evilmarsh", "Dark Makai"),
    Material("Cyclops Horn", 3, "faerie", "Cyclops Warlord"),
    Material("Wereboar Tusk", 2, "greenguardwest", "Big Bad Boar"),
)
CONFIG = FarmConfig(
    name=QUEST.name,
    quests=(QUEST,),
    class_name="Chaos Slayer Berserker",
    map_name="mobius",
    screen=Screen(monsters={"Slugfit": None}),
    drops=(TARGET_ITEM, *(material.item for material in MATERIALS)),
    server="Alteon",
    mode="leech",
)


async def main(cmd: Command, *, stop_on_complete: bool = True):
    await farm_contracts(
        cmd, CONFIG, MATERIALS, stop_on_complete=stop_on_complete
    )


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
