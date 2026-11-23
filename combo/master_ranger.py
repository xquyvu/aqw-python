"""Keyboard combo 2, 3, 2, 2, 2, 2, 3, 4 with key 5 taking priority.

Repository skill slots are one lower than keyboard keys.
"""

from core.command import Command

SKILL_SEQUENCE = (1, 2)
PRIORITY_SKILL = 4


async def attack_next_skill(cmd: Command, monster_name: str, skill_index: int) -> int:
    if await cmd.use_skill(PRIORITY_SKILL, monster_name):
        return skill_index

    if await cmd.use_skill(SKILL_SEQUENCE[skill_index], monster_name):
        return (skill_index + 1) % len(SKILL_SEQUENCE)

    return skill_index
