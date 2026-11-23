"""Day 3: python -u -m bot.lord_of_order.day_03_purification_of_chaos."""

from bot.lord_of_order.runner import execute_day, run_day
from core.command import Command


async def main(cmd: Command):
    await execute_day(cmd, 3)


if __name__ == "__main__":
    run_day(3)
