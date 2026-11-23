from core.command import Command


SKILL_SEQUENCE = (0, 1, 2, 3, 4)


async def attack_next_skill(cmd: Command, monster_name: str, skill_index: int) -> int:
    if await cmd.use_skill(1, monster_name):
        return skill_index

    for offset in range(len(SKILL_SEQUENCE)):
        index = (skill_index + offset) % len(SKILL_SEQUENCE)
        skill = SKILL_SEQUENCE[index]
        if skill != 1 and await cmd.use_skill(skill, monster_name):
            return (index + 1) % len(SKILL_SEQUENCE)

    return skill_index
