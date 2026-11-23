"""Run both daily quests once. Run: python -u -m bot.daily."""

from combo.dragonslayer_general import attack_next_skill
from core.command import Command
from core.quest_farm import FarmConfig, Quest, Screen, farm_quests
from core.script_runner import run_script

# Quest IDs: https://www.aqwworld.com/2017/01/quest-id-aqw-latest-and-updated.html
DAILIES = (
    FarmConfig(
        name="Elder's Blood daily",
        quests=(
            Quest(
                802,
                "Experiment 107: Elder's Blood Potion",
                optional=True,
                repeat=False,
            ),
        ),
        map_name="arcangrove",
        screen=Screen(monsters={"Gorillaphant": 3}),
        class_name="Blaze Binder",
        drops=("Elders' Blood",),
        mode="solo",
    ),
    FarmConfig(
        name="Glacera Ice Token daily",
        quests=(Quest(3966, "Glacera Ice Token", optional=True, repeat=False),),
        map_name="frozenruins",
        screen=Screen(monsters={"Frost Invader": None}),
        class_name="Dragonslayer General",
        combo=attack_next_skill,
        drops=("Glacera Ice Token",),
        mode="solo",
    ),
)


async def run_dailies(cmd: Command):
    for config in DAILIES:
        if not cmd.is_still_connected():
            return
        await farm_quests(cmd, config)
    if cmd.is_still_connected():
        print(
            "Daily routine finished; see above for completed or skipped quests.",
            flush=True,
        )


async def main(cmd: Command):
    await run_dailies(cmd)
    if cmd.is_still_connected():
        cmd.bot.stop_bot(user_triggered=True)


def run():
    first = DAILIES[0]
    run_script(
        main,
        class_name=first.class_name,
        server=first.server,
        room_number=first.effective_room_number,
    )


if __name__ == "__main__":
    run()
