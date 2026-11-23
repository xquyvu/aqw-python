"""Farm DragonSlayer General Class. Run: python -u -m bot.dragonslayer_general."""

from core.command import Command
from core.quest_farm import FarmConfig, Quest, Screen, farm_quests, run_farm

CONFIG = FarmConfig(
    name="DragonSlayer General Class",
    quests=(
        Quest(
            5294,
            "DragonSlayer General Class",
        ),
    ),
    map_name="dragontown",
    # Verified Tempest Dracolich farming cell:
    # https://github.com/BrenoHenrike/Scripts/blob/master/Other/Classes/DragonslayerGeneral.cs
    screen=Screen(monsters={"Tempest Dracolich": None}, cell="r4", pad="Right"),
    drops=("Enchanted Scale", "Dragon Claw"),
    server="Alteon",
    room_number=1,
)


async def main(cmd: Command):
    await farm_quests(cmd, CONFIG)


def run():
    run_farm(CONFIG)


if __name__ == "__main__":
    run()
