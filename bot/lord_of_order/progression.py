"""Persist one confirmed Lord of Order daily per server reset."""

import json
from dataclasses import dataclass, replace
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from bot.lord_of_order.quests import DAILIES
from bot.lord_of_order.runner import DailyRunner, Settings
from core.command import Command

STATE_DIR = Path(__file__).resolve().parents[2] / ".aqw_state"
SERVER_TIMEZONE = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class Progress:
    completed_day: int = 0
    completed_on: date | None = None
    pending_day: int | None = None


def load_progress(path: Path) -> Progress:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return Progress()
    if not isinstance(data, dict):
        raise ValueError(f"Invalid Lord of Order progress in {path}.")
    day = data.get("completed_day")
    completed_on = data.get("completed_on")
    pending = data.get("pending_day")
    if (
        type(day) is not int
        or not 0 <= day <= len(DAILIES)
        or (day == 0 and completed_on is not None)
        or (day > 0 and not isinstance(completed_on, str))
        or (
            pending is not None
            and (type(pending) is not int or pending != day + 1 or pending > len(DAILIES))
        )
    ):
        raise ValueError(f"Invalid Lord of Order progress in {path}.")
    return Progress(
        day,
        date.fromisoformat(completed_on) if completed_on is not None else None,
        pending,
    )


def save_progress(path: Path, progress: Progress):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(
            {
                "completed_day": progress.completed_day,
                "completed_on": (
                    progress.completed_on.isoformat()
                    if progress.completed_on is not None
                    else None
                ),
                "pending_day": progress.pending_day,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


class ProgressRunner(DailyRunner):
    def __init__(
        self, cmd: Command, settings: Settings, path: Path, progress: Progress
    ):
        super().__init__(cmd, settings)
        self.path = path
        self.progress = progress
        self.day = progress.completed_day + 1

    async def turn_in(self, quest_id: int, reward_id: int = -1):
        if quest_id != DAILIES[self.day - 1].id or not self.cmd.can_turnin_quest(
            quest_id
        ):
            await super().turn_in(quest_id, reward_id)
            return
        save_progress(self.path, replace(self.progress, pending_day=self.day))
        try:
            await super().turn_in(quest_id, reward_id)
        except (RuntimeError, TimeoutError, ConnectionError):
            result = self.results.get(("ccqr", quest_id))
            if result is not None and int(result.get("bSuccess", 0)) == 0:
                save_progress(self.path, self.progress)
            raise
        self.progress = Progress(self.day, datetime.now(SERVER_TIMEZONE).date())
        save_progress(self.path, self.progress)


async def run_next_daily(
    cmd: Command, settings: Settings | None = None, *, state_dir: Path = STATE_DIR,
    skip_unavailable: bool = False,
):
    try:
        character_id = int(cmd.get_player().CHARID)
        if character_id <= 0:
            raise RuntimeError("Character ID is unavailable; cannot track daily progress.")
        path = state_dir / f"lord_of_order_{character_id}.json"
        progress = load_progress(path)
        if progress.pending_day is not None:
            raise RuntimeError(
                f"Day {progress.pending_day} has an unconfirmed turn-in. "
                f"Check completion in-game before correcting {path}; not retrying."
            )
        if progress.completed_day == len(DAILIES):
            print("LORD OF ORDER: all 10 days are complete; skipping.", flush=True)
            return
        today = datetime.now(SERVER_TIMEZONE).date()
        if progress.completed_on is not None and progress.completed_on >= today:
            print(
                "LORD OF ORDER: today's daily is complete; "
                f"day {progress.completed_day + 1} waits for the next daily reset.",
                flush=True,
            )
            return
        daily = DAILIES[progress.completed_day]
        print(
            f"LORD OF ORDER: starting day {progress.completed_day + 1}/10: "
            f"{daily.name}.",
            flush=True,
        )
        await ProgressRunner(cmd, settings or Settings(), path, progress).run(
            daily, stop_on_complete=False, skip_unavailable=skip_unavailable
        )
    except (OSError, ValueError, RuntimeError, TimeoutError, ConnectionError) as error:
        print(f"LORD OF ORDER PROGRESSION ERROR: {error}", flush=True)
        cmd.bot.stop_bot(user_triggered=True)
        raise
