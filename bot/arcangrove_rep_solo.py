"""Farm Gorillaphant quests. Run: python -u -m bot.arcangrove_rep_solo."""

from core.command import Command
from core.quest_farm import FarmConfig, Quest, Screen, farm_quests, run_farm


CONFIG = FarmConfig(
    name="Arcangrove Gorillaphant reputation",
    quests=(
        Quest(795, "Gorillaphant Poaching"),
        Quest(799, "Pleased to Meat You"),
        Quest(801, "Ebony and Ivory Tusks"),
    ),
    class_name="Blaze Binder",
    map_name="arcangrove",
    screen=Screen(monsters={"Gorillaphant": 3}, pad="Right"),
    combo="ready",
    reputation="Arcangrove",
    mode="solo",
)


async def main(cmd: Command):
    await farm_quests(cmd, CONFIG)


def run():
    run_farm(CONFIG)


if __name__ == "__main__":
    run()
