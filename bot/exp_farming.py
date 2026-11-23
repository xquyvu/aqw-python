"""Farm EXP with Dragonslayer General. Run: python -u -m bot.exp_farming."""

from core.command import Command
from core.quest_farm import FarmConfig, Quest, Screen, farm_quests, run_farm

CONFIG = FarmConfig(
    name="EXP farming",
    quests=(
        Quest(7980, "War Medals", requirement="Complete Ava-risky Business first."),
        Quest(
            7981, "Mega War Medals", requirement="Complete Ava-risky Business first."
        ),
    ),
    class_name="Blaze Binder",
    map_name="sevencircleswar",
    screen=Screen(monsters={}, cell="Enter", pad="Spawn"),
    combo="ready",
    mode="leech",
    server="Alteon",
    track_exp=True,
)


async def main(cmd: Command):
    await farm_quests(cmd, CONFIG)


def run():
    run_farm(CONFIG)


if __name__ == "__main__":
    run()
