"""Farm 999 Archfiend's Favor: python -u -m bot.archfiend_favor."""

from core.command import Command
from core.item_farm import farm_item
from core.quest_farm import FarmConfig, Screen
from core.script_runner import run_script

TARGET_ITEM = "Archfiend's Favor"
TARGET_QTY = 999

CONFIG = FarmConfig(
    name=TARGET_ITEM,
    quests=(),
    map_name="evilwarnul",
    screen=Screen(monsters={}, cell="r9"),
    class_name="Blaze Binder",
    drops=(TARGET_ITEM,),
    server="Alteon",
    mode="solo",
)


async def main(cmd: Command):
    await farm_item(cmd, CONFIG, TARGET_ITEM, TARGET_QTY)


def run():
    run_script(
        main,
        class_name=CONFIG.class_name,
        server=CONFIG.server,
        room_number=CONFIG.effective_room_number,
    )


if __name__ == "__main__":
    run()
