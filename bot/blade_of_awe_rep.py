"""Farm Blade of Awe reputation. Run: python -u -m bot.blade_of_awe_rep."""

from combo.master_ranger import attack_next_skill
from core.command import Command
from core.quest_farm import FarmConfig, Quest, Screen, farm_quests, run_farm

CONFIG = FarmConfig(
    name="Blade of Awe reputation",
    quests=(
        Quest(
            2935,
            "Find the Hilt!",
            requirement="Complete Valencia's Find the Handle! quest in museum first.",
        ),
    ),
    class_name="Master Ranger",
    map_name="swordhavenundead",
    screen=Screen(monsters={}, cell="Enter", pad="Spawn"),
    combo=attack_next_skill,
    auto_attack=True,
    reputation="Blade of Awe",
    mode="solo",
)


async def main(cmd: Command):
    await farm_quests(cmd, CONFIG)


def run():
    run_farm(CONFIG)


if __name__ == "__main__":
    run()
