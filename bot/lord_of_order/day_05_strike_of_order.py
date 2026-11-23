"""Day 5: python -u -m bot.lord_of_order.day_05_strike_of_order."""

from bot.lord_of_order.runner import execute_day, run_day
from core.command import Command


async def main(cmd: Command):
    await execute_day(cmd, 5)


if __name__ == "__main__":
    run_day(5)
