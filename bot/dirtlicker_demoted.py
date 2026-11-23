"""Farm Dirtlicker Demoted once: python -u -m bot.dirtlicker_demoted."""

from combo.dragonslayer_general import attack_next_skill
from core.command import Command
from core.item_farm import farm_item
from core.quest_farm import FarmConfig, Screen
from core.script_runner import run_script

TARGET_ITEM = "Dirtlicker Demoted"

CONFIG = FarmConfig(
    name=TARGET_ITEM,
    quests=(),
    map_name="fiendshard",
    screen=Screen(monsters={"Dirtlicker": None}),
    class_name="Dragonslayer General",
    combo=attack_next_skill,
    drops=(TARGET_ITEM,),
    server="Alteon",
    mode="leech",
    room_number=1,
)


async def main(cmd: Command):
    await farm_item(cmd, CONFIG, TARGET_ITEM)


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
