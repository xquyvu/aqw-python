"""Farm Relic of Chaos. Run: python -u -m bot.relic_of_chaos."""

import time

from core.command import Command
from core.quest_farm import FarmConfig, Quest, QuestFarmer, Screen
from core.script_runner import run_script

SUPPLIES = Quest(555, "Supplies to spin The Wheel of Chance")
TURN_IN_MAP = "tercessuinotlim"

CONFIG = FarmConfig(
    name="Relic of Chaos",
    quests=(SUPPLIES,),
    class_name="Chaos Slayer Berserker",
    map_name="ultraalteon",
    screen=Screen(monsters={"Ultra Chaos Alteon": None}),
    drops=("Relic of Chaos",),
    server="Alteon",
    mode="leech",
)


class RelicFarmer(QuestFarmer):
    async def turn_in(self, quest: Quest):
        await self.cmd.join_map(TURN_IN_MAP, roomNumber=1)
        deadline = time.monotonic() + self.config.map_timeout
        while self.cmd.is_still_connected():
            if self.cmd.is_in_map(TURN_IN_MAP) and not self.bot.is_joining_map:
                break
            if time.monotonic() >= deadline:
                raise TimeoutError(f"{TURN_IN_MAP} did not load in time.")
            await self.cmd.sleep(200)
        while self.cmd.is_still_connected() and self.cmd.can_turnin_quest(quest.id):
            await super().turn_in(quest)
        if self.cmd.is_still_connected():
            await self.ensure_room()


async def main(cmd: Command):
    try:
        await RelicFarmer(cmd, CONFIG).run()
    except (RuntimeError, TimeoutError, ConnectionError) as error:
        print(f"FARM ERROR [{CONFIG.name}]: {error}", flush=True)
        cmd.bot.stop_bot(user_triggered=True)
        raise


def run():
    run_script(
        main,
        class_name=CONFIG.class_name,
        server=CONFIG.server,
        room_number=CONFIG.effective_room_number,
        leech=CONFIG.mode == "leech",
    )


if __name__ == "__main__":
    run()
