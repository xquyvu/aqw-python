"""Spam ready Dragonslayer General skills, prioritizing key 5 (slot 4)."""

from core.command import Command


PRIORITY_SKILL = 4
SKILL_SEQUENCE = (0, 1, 2, 3)


async def attack_next_skill(cmd: Command, monster_name: str, skill_index: int) -> int:
    if await cmd.use_skill(PRIORITY_SKILL, monster_name):
        return skill_index

    for offset in range(len(SKILL_SEQUENCE)):
        index = (skill_index + offset) % len(SKILL_SEQUENCE)
        if await cmd.use_skill(SKILL_SEQUENCE[index], monster_name):
            return (index + 1) % len(SKILL_SEQUENCE)

    return skill_index
