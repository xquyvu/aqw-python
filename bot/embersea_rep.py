"""Farm Embersea reputation. Run with: python -u -m bot.embersea_rep."""

from core.command import Command
from core.quest_farm import FarmConfig, Quest, Screen, farm_quests, run_farm


# https://www.aqwworld.com/2017/01/quest-id-aqw-latest-and-updated.html
CONFIG = FarmConfig(
    name="Embersea reputation",
    quests=(
        Quest(4218, "Round 3: Firestorm Pikemen"),
        Quest(4219, "Round 4: Firestorm Knights"),
        Quest(4229, "Take out the Firestorm Knights"),
    ),
    map_name="fireforge",
    screen=Screen(monsters={"Fire Pikeman": 2, "Firestorm Knight": 2}),
    combo="ready",
    reputation="Embersea",
    server="Alteon",
    room_number=1,
)


async def main(cmd: Command):
    await farm_quests(cmd, CONFIG)


def run():
    run_farm(CONFIG)


if __name__ == "__main__":
    run()
