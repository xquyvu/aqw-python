"""Day 6: python -u -m bot.lord_of_order.day_06_harmony."""

from bot.lord_of_order.runner import execute_day, run_day
from core.command import Command


async def main(cmd: Command):
    await execute_day(cmd, 6)


if __name__ == "__main__":
    run_day(6)
