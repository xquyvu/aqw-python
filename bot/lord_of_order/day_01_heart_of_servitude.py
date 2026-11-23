"""Day 1: python -u -m bot.lord_of_order.day_01_heart_of_servitude."""

from bot.lord_of_order.runner import execute_day, run_day
from core.command import Command


async def main(cmd: Command):
    await execute_day(cmd, 1)


if __name__ == "__main__":
    run_day(1)
