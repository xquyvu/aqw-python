"""Run dailies and bounded item, Nulgath material, and gold farms."""

from collections.abc import Awaitable

from bot import archfiend_favor, dirtlicker_demoted, gold_farming, void_aura
from bot.daily import DAILIES, run_dailies
from bot.lord_of_order.progression import run_next_daily
from bot.nulgath import larvae as contract_script
from bot.nulgath import materials as farming_script
from bot.nulgath.core_nulgath import TARGET_ITEM, TARGET_QTY, contract_count
from core.command import Command
from core.leech import LeechUnavailable
from core.script_runner import run_script


async def run_task(name: str, operation: Awaitable[None]) -> bool:
    try:
        await operation
        return True
    except LeechUnavailable as error:
        print(f"ORCHESTRATOR: skipping {name}: {error}", flush=True)
        return False


async def main(cmd: Command):
    cmd.bot.accept_all_drops = True
    print("ORCHESTRATOR: starting dailies.", flush=True)
    await run_dailies(cmd)
    if not cmd.is_still_connected():
        return
    print("ORCHESTRATOR: checking Lord of Order daily progression.", flush=True)
    await run_next_daily(cmd, skip_unavailable=True)
    if not cmd.is_still_connected():
        return
    print("ORCHESTRATOR: retrieving Void Auras until more than 2 are owned.", flush=True)
    await run_task("Void Auras", void_aura.main(cmd))
    if not cmd.is_still_connected():
        return
    print("ORCHESTRATOR: farming Dirtlicker Demoted.", flush=True)
    await run_task("Dirtlicker Demoted", dirtlicker_demoted.main(cmd))
    if not cmd.is_still_connected():
        return
    print("ORCHESTRATOR: farming Archfiend's Favor x999 (solo).", flush=True)
    await archfiend_favor.main(cmd)
    if not cmd.is_still_connected():
        return
    print(
        f"ORCHESTRATOR: starting {contract_script.CONFIG.name} "
        f"until {TARGET_ITEM} x{TARGET_QTY}.",
        flush=True,
    )
    contracts_finished = await run_task(
        contract_script.CONFIG.name,
        contract_script.main(cmd, stop_on_complete=False),
    )
    if cmd.is_still_connected():
        count = contract_count(cmd)
        if contracts_finished and count < TARGET_QTY:
            cmd.bot.stop_bot(user_triggered=True)
            raise RuntimeError(
                f"{contract_script.CONFIG.name} ended before its goal: "
                f"{TARGET_ITEM} {count}/{TARGET_QTY}."
            )
        print(
            f"ORCHESTRATOR: {'contract farm skipped; ' if not contracts_finished else ''}"
            f"{TARGET_ITEM} {count}/{TARGET_QTY}; "
            f"starting {farming_script.CONFIG.name}.",
            flush=True,
        )
        await run_task(farming_script.CONFIG.name, farming_script.main(cmd))
    if not cmd.is_still_connected():
        return
    print(
        f"ORCHESTRATOR: farming Seven Circles War to a "
        f"{gold_farming.TARGET_GOLD:,} gold balance.",
        flush=True,
    )
    await run_task(gold_farming.CONFIG.name, gold_farming.main(cmd))
    if cmd.is_still_connected():
        print(
            "ORCHESTRATOR: task list finished; see above for completed or skipped goals.",
            flush=True,
        )
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
