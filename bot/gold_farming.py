"""Farm a 20-million gold balance: python -u -m bot.gold_farming."""

import json
from dataclasses import replace

from bot.exp_farming import CONFIG as EXP_CONFIG
from bot.lord_of_order.runner import DailyRunner, Settings
from core.command import Command
from core.quest_farm import QuestFarmer
from core.script_runner import run_script

TARGET_GOLD = 20_000_000
CONFIG = replace(EXP_CONFIG, name="Seven Circles War gold", track_exp=False)


class GoldFarmer(QuestFarmer):
    def __init__(self, cmd: Command):
        super().__init__(
            cmd, CONFIG, stop_when=lambda: self.bot.player.GOLD >= TARGET_GOLD
        )

    async def refresh_balance(self):
        received = False

        def on_message(message: str):
            nonlocal received
            if not message.startswith("{"):
                return
            data = json.loads(message).get("b", {}).get("o", {})
            if isinstance(data, dict) and data.get("cmd") == "initUserDatas":
                received = received or any(
                    user["data"]["strUsername"].lower() == self.bot.username.lower()
                    and "intGold" in user["data"]
                    for user in data["a"]
                )

        self.bot.subscribe(on_message)
        try:
            error = self.bot.write_message(
                f"%xt%zm%retrieveUserDatas%{self.bot.areaId}%{self.bot.username_id}%"
            )
            if error is not None:
                raise ConnectionError(error)
            await DailyRunner(
                self.cmd, Settings(request_timeout=CONFIG.quest_timeout)
            ).wait(lambda: received, "refreshing the server-confirmed gold balance")
        finally:
            self.bot.unsubscribe(on_message)

    def report(self):
        previous_report = self.last_report
        super().report()
        if self.last_report != previous_report:
            print(
                f"GOLD BALANCE: {self.bot.player.GOLD:,}/{TARGET_GOLD:,}.",
                flush=True,
            )


async def main(cmd: Command):
    cmd.bot.accept_all_drops = True
    farmer = GoldFarmer(cmd)
    try:
        await farmer.refresh_balance()
        await farmer.run()
        if not cmd.is_still_connected():
            raise ConnectionError("Disconnected before confirming the gold goal.")
        if not farmer.goal_reached():
            raise RuntimeError("Seven Circles War ended before the gold goal.")
        await cmd.leave_combat()
        print(
            f"FARM COMPLETE: gold balance {cmd.bot.player.GOLD:,}/{TARGET_GOLD:,}.",
            flush=True,
        )
    except (RuntimeError, TimeoutError, ConnectionError) as error:
        print(f"GOLD FARM ERROR: {error}", flush=True)
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
