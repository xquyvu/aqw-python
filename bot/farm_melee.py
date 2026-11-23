"""Rank any class to 10. Run: python -u -m bot.farm_melee --class "Class Name"."""

import argparse
import time

from core.class_rank import ClassRankTracker
from core.command import Command
from core.script_runner import run_script
from core.utils import normalize
from templates.hunt import attack_script

CLASS_NAME = "Dragonslayer General"
MAP_NAME = "sevencircleswar"
CELL = "Enter"
PAD = "Spawn"


async def position(cmd: Command):
    deadline = time.monotonic() + 30
    while cmd.is_still_connected():
        if cmd.is_not_in_map(MAP_NAME) and not cmd.bot.is_joining_map:
            await cmd.join_map(MAP_NAME, roomNumber=1)
        if cmd.is_in_map(MAP_NAME) and not cmd.bot.is_joining_map:
            if cmd.is_not_in_cell(CELL):
                await cmd.jump_cell(CELL, PAD)
            return
        if time.monotonic() >= deadline:
            raise TimeoutError(f"{MAP_NAME} did not load within 30 seconds.")
        await cmd.sleep(200)


async def main(
    cmd: Command, *, class_name: str = CLASS_NAME, test_seconds: int | None = None
):
    if test_seconds is not None:
        cmd.bot.auto_relogin = False
    tracker = None
    try:
        if not normalize(class_name):
            raise RuntimeError("Choose a nonempty class name.")
        cmd.bot.farmClass = class_name
        if not await cmd.equip_item(class_name):
            raise RuntimeError(f"{class_name} must be in inventory or bank.")
        equipped = cmd.get_equipped_class()
        if equipped is None or normalize(equipped.item_name) != normalize(class_name):
            raise RuntimeError(f"{class_name} equipment was not confirmed.")
        # Relogin appends inventory snapshots; use the newest class-point total.
        equipped = next(
            item
            for item in reversed(cmd.get_player().INVENTORY)
            if item.item_id == equipped.item_id
        )
        tracker = ClassRankTracker(equipped)
        tracker.log()
        if tracker.is_max:
            print(f"CLASS COMPLETE: {tracker.name} is already rank 10.", flush=True)
            cmd.bot.stop_bot(user_triggered=True)
            return
        cmd.bot.subscribe(tracker.on_message)
        await position(cmd)
        if not cmd.is_still_connected():
            if test_seconds is not None:
                raise RuntimeError("MELEE TEST INCOMPLETE: disconnected during setup.")
            return
        player = cmd.get_player()
        starting_exp = player.EXPFARMED
        started = last_report = time.monotonic()
        print(
            f"MELEE FARM {cmd.bot.server}, {cmd.bot.areaName}:{CELL} | "
            f"class={class_name} | hunt helper rotation, targets=*",
            flush=True,
        )
        for index, skill in enumerate(player.SKILLS[:5]):
            print(
                f"MELEE SKILL key={index + 1} name={skill.get('nam')} "
                f"target={skill.get('tgt')} range={skill.get('range')}",
                flush=True,
            )
        while cmd.is_still_connected():
            equipped = cmd.get_equipped_class()
            if equipped is None or equipped.item_id != tracker.item_id:
                raise RuntimeError("The equipped class changed during ranking.")
            if tracker.is_max:
                break
            await position(cmd)
            if not cmd.is_still_connected():
                break
            await attack_script(cmd)
            if tracker.is_max:
                break
            now = time.monotonic()
            gained = player.EXPFARMED - starting_exp
            if now - last_report >= 10:
                tracker.log()
                alive = sum(
                    monster.is_alive and monster.current_hp > 0
                    for monster in cmd.bot.monsters
                    if str(monster.frame or "").lower() == CELL.lower()
                )
                print(
                    f"MELEE PROGRESS elapsed={now - started:.1f}s "
                    f"exp_gained={gained:,} live_targets={alive} "
                    f"mana={player.MANA} in_combat={player.IS_IN_COMBAT}",
                    flush=True,
                )
                last_report = now
            if test_seconds is not None:
                if tracker.gained > 0:
                    print(
                        f"MELEE TEST PASSED: class points increased by {tracker.gained:,}; "
                        f"EXP increased by {gained:,} "
                        f"in {now - started:.1f}s.",
                        flush=True,
                    )
                    cmd.bot.stop_bot(user_triggered=True)
                    return
                if now - started >= test_seconds:
                    raise RuntimeError(
                        f"MELEE TEST FAILED: no class-point increase in {now - started:.1f}s."
                    )
        if tracker.is_max:
            tracker.log()
            print(f"CLASS COMPLETE: {tracker.name} reached rank 10.", flush=True)
            cmd.bot.stop_bot(user_triggered=True)
            return
        if test_seconds is not None:
            raise RuntimeError(
                "MELEE TEST INCOMPLETE: disconnected before class points increased."
            )
    except (RuntimeError, TimeoutError) as error:
        print(f"MELEE ERROR: {error}", flush=True)
        cmd.bot.stop_bot(user_triggered=True)
        raise
    finally:
        if tracker is not None:
            cmd.bot.unsubscribe(tracker.on_message)


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--class",
        dest="class_name",
        default=CLASS_NAME,
        help=f"Class to rank, from inventory or bank (default: {CLASS_NAME}).",
    )
    parser.add_argument(
        "--test-seconds",
        type=int,
        help="Test combat: stop on the first CP gain, or fail after this many seconds.",
    )
    args = parser.parse_args()
    if args.test_seconds is not None and args.test_seconds <= 0:
        parser.error("--test-seconds must be positive.")
    if not normalize(args.class_name):
        parser.error("--class must not be empty.")

    async def script(cmd: Command):
        await main(cmd, class_name=args.class_name, test_seconds=args.test_seconds)

    run_script(script, class_name=args.class_name, server="Alteon", room_number=1)


if __name__ == "__main__":
    run()
