"""Farm Embersea quests. Run with: python -u -m bot.embersea_quests."""

from core.command import Command
from core.quest_farm import FarmConfig, Quest, Screen, farm_quests, run_farm


CONFIG = FarmConfig(
    name="Embersea Blazebinders and Pikemen",
    quests=(
        Quest(4228, "Slay the Blazebinders"),
        Quest(4218, "Round 3: Firestorm Pikemen"),
    ),
    map_name="fireforge",
    screen=Screen(monsters={"Blazebinder": None, "Fire Pikeman": None}),
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
