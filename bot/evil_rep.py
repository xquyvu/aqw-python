"""Farm the Evil reputation required by Retrieve Void Auras."""

import asyncio
from collections import Counter
from dataclasses import replace

from core.command import Command
from core.quest_farm import FarmConfig, Quest, QuestFarmer, Screen
from core.script_runner import run_script
from core.utils import normalize

STARTER_CONFIG = FarmConfig(
    name="Evil reputation to rank 4",
    quests=(Quest(364, "Youthanize"),),
    map_name="swordhavenbridge",
    screen=Screen(monsters={"Slime": None}),
    reputation="Evil",
    drops=("Youthanize",),
)

CONFIG = FarmConfig(
    name="Evil reputation to rank 10",
    quests=(Quest(367, "Bone-afide", requirement="Requires Evil rank 4 and alignment."),),
    map_name="castleundead",
    screen=Screen(monsters={"Skeletal Warrior": None}),
    reputation="Evil",
    drops=("Replacement Tibia", "Phalanges"),
)


class EvilFarmer(QuestFarmer):
    def __init__(self, cmd: Command, config: FarmConfig, target_rank: int):
        super().__init__(cmd, config)
        self.target_rank = target_rank

    def select_screen(self) -> str:
        if self.config.map_name == "castleundead":
            skeletons = [
                monster for monster in self.bot.monsters
                if monster.frame and normalize(monster.mon_name) in (
                    "skeletal warrior", "skeletal viking"
                )
            ]
            counts = Counter(monster.frame for monster in skeletons)
            if not counts:
                raise RuntimeError("No Skeletal Warriors or Vikings found in castleundead.")
            cell = max(sorted(counts), key=lambda cell: counts[cell])
            self.config = replace(
                self.config,
                screen=Screen(
                    monsters={
                        monster.mon_name: None
                        for monster in skeletons if monster.frame == cell
                    },
                    cell=cell,
                ),
            )
        return super().select_screen()

    def stop_if_reputation_max(self) -> bool:
        if self.cmd.get_player().getFactionRank("Evil") < self.target_rank:
            return False
        if self.reputation is not None:
            self.reputation.log()
        return True


async def main(cmd: Command):
    player = cmd.get_player()
    if player.getFactionRank("Evil") >= 10:
        return
    print(
        f"VOID AURA PREREQUISITE: Evil rank {player.getFactionRank('Evil')}/10; "
        "farming reputation before collecting essences.",
        flush=True,
    )
    previous = (
        cmd.bot.accept_all_drops,
        cmd.bot.accept_non_member_drops,
        list(cmd.bot.items_drop_whitelist),
    )
    cmd.bot.accept_all_drops = False
    cmd.bot.accept_non_member_drops = False
    cmd.bot.items_drop_whitelist[:] = (*STARTER_CONFIG.drops, *CONFIG.drops)
    try:
        if player.getFactionRank("Evil") < 4:
            await asyncio.wait_for(EvilFarmer(cmd, STARTER_CONFIG, 4).run(), timeout=7200)
        if cmd.is_still_connected() and player.getFactionRank("Evil") < 10:
            await asyncio.wait_for(EvilFarmer(cmd, CONFIG, 10).run(), timeout=7200)
        if not cmd.is_still_connected():
            raise ConnectionError("Disconnected while farming Evil reputation.")
        if player.getFactionRank("Evil") < 10:
            raise RuntimeError("Evil reputation farming ended before rank 10.")
        print("VOID AURA PREREQUISITE COMPLETE: Evil rank 10.", flush=True)
    except (RuntimeError, TimeoutError, ConnectionError) as error:
        print(f"EVIL REPUTATION ERROR: {error}", flush=True)
        cmd.bot.stop_bot(user_triggered=True)
        raise
    finally:
        cmd.bot.accept_all_drops = previous[0]
        cmd.bot.accept_non_member_drops = previous[1]
        cmd.bot.items_drop_whitelist[:] = previous[2]


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
