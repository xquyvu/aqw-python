"""Farm Arcangrove reputation. Run: python -u -m bot.arcangrove_rep."""

from combo.dragonslayer_general import attack_next_skill
from core.command import Command
from core.quest_farm import FarmConfig, Quest, Screen, farm_quests, run_farm


CONFIG = FarmConfig(
    name="Arcangrove reputation",
    quests=(Quest(848, "Feed Me"),),
    class_name="Dragonslayer General",
    map_name="mafic",
    screen=Screen(monsters={"Mafic Dragon": None}),
    combo=attack_next_skill,
    reputation="Arcangrove",
    mode="leech",
)


async def main(cmd: Command):
    await farm_quests(cmd, CONFIG)


def run():
    run_farm(CONFIG)


if __name__ == "__main__":
    run()
