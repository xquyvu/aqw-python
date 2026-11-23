"""Farm Chaos reputation. Run: python -u -m bot.chaos_rep."""

from core.command import Command
from core.quest_farm import FarmConfig, Quest, Screen, farm_quests, run_farm

CONFIG = FarmConfig(
    name="Chaos reputation",
    quests=(
        # Both quests consume the same item, so complete the daily first.
        Quest(3596, "Embrace Your Chaos (Daily)", optional=True, repeat=False),
        Quest(3594, "Embrace Your Chaos"),
    ),
    map_name="mountdoomskull",
    screen=Screen(monsters={}, cell="b1", pad="Left"),
    reputation="Chaos",
    mode="leech",
)


async def main(cmd: Command):
    await farm_quests(cmd, CONFIG)


def run():
    run_farm(CONFIG)


if __name__ == "__main__":
    run()
