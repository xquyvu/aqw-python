"""Day 7: python -u -m bot.lord_of_order.day_07_ordinance."""

from bot.lord_of_order.runner import execute_day, run_day
from core.command import Command


async def main(cmd: Command):
    await execute_day(cmd, 7)


if __name__ == "__main__":
    run_day(7)
