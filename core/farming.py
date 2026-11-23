"""Quest-item screen coverage using verified drop sources and live map spawns.

The minimum-screen cover is exact. Progress-per-HP scores only break ties;
without drop rates, respawn times, and damage data they are not time estimates.
"""

from dataclasses import dataclass
from typing import AbstractSet, Iterable, Mapping, TYPE_CHECKING

from core.utils import normalize

if TYPE_CHECKING:
    from model.monster import Monster


@dataclass(frozen=True)
class FarmingScreen:
    cell: str
    item_ids: frozenset[int]
    useful_spawns: int
    live_spawns: int
    score: float
    live_score: float


@dataclass(frozen=True)
class FarmingPlan:
    screens: tuple[FarmingScreen, ...]
    unmapped_items: frozenset[int]
    unavailable_items: frozenset[int]


def _wanted_items(remaining):
    if any(quantity < 0 for quantity in remaining.values()):
        raise ValueError("Remaining item quantities cannot be negative.")
    return {item_id for item_id, quantity in remaining.items() if quantity > 0}


def _plan_key(screens, current_cell):
    return (
        len(screens),
        -sum(screen.live_score for screen in screens),
        -sum(screen.score for screen in screens),
        -sum(screen.useful_spawns for screen in screens),
        not any(screen.cell.lower() == current_cell.lower() for screen in screens),
        tuple(screen.cell for screen in screens),
    )


def plan_screens(
    remaining: Mapping[int, int],
    monsters: Iterable["Monster"],
    monster_drops: Mapping[str, AbstractSet[int]],
    current_cell: str = "",
) -> FarmingPlan:
    """Cover every obtainable missing item with the fewest screens.

    Dead spawns still provide coverage, so respawning cannot make an objective
    disappear. Unknown drop sources and absent source monsters are reported
    separately instead of being mistaken for completed objectives.
    """
    wanted = _wanted_items(remaining)
    sources = {normalize(name): frozenset(items) for name, items in monster_drops.items()}
    mapped = set().union(*sources.values())
    grouped = {}
    for monster in monsters:
        items = sources.get(normalize(monster.mon_name), frozenset()) & wanted
        if monster.frame and items:
            grouped.setdefault(monster.frame, []).append((monster, items))

    screens = []
    for cell, spawns in sorted(grouped.items()):
        items = set()
        score = 0.0
        live_score = 0.0
        live_spawns = 0
        for monster, drops in spawns:
            if monster.max_hp <= 0:
                raise ValueError(f"Invalid maximum HP for monster {monster.mon_map_id}.")
            items.update(drops)
            progress = sum(1 / remaining[item_id] for item_id in drops) / monster.max_hp
            score += progress
            if monster.is_alive and monster.current_hp > 0:
                live_spawns += 1
                live_score += progress
        screens.append(FarmingScreen(
            cell, frozenset(items), len(spawns), live_spawns, score, live_score
        ))

    obtainable = set().union(*(screen.item_ids for screen in screens))
    bits = {item_id: 1 << index for index, item_id in enumerate(sorted(obtainable))}
    best: dict[int, tuple[FarmingScreen, ...]] = {0: ()}
    for screen in screens:
        screen_mask = sum(bits[item_id] for item_id in screen.item_ids)
        for mask, selected in tuple(best.items()):
            combined = mask | screen_mask
            if combined == mask:
                continue
            candidate = selected + (screen,)
            previous = best.get(combined)
            if previous is None or _plan_key(candidate, current_cell) < _plan_key(
                previous, current_cell
            ):
                best[combined] = candidate
    return FarmingPlan(
        screens=best[(1 << len(bits)) - 1],
        unmapped_items=frozenset(wanted - mapped),
        unavailable_items=frozenset((wanted & mapped) - obtainable),
    )


def targets_for_cell(
    cell: str,
    remaining: Mapping[int, int],
    monsters: Iterable["Monster"],
    monster_drops: Mapping[str, AbstractSet[int]],
) -> tuple[str, ...]:
    """Prioritize useful live spawns by remaining-item progress per current HP."""
    sources = {normalize(name): frozenset(items) for name, items in monster_drops.items()}
    wanted = _wanted_items(remaining)
    ranked = []
    for monster in monsters:
        if (
            str(monster.frame or "").lower() != cell.lower()
            or not monster.is_alive
            or monster.current_hp <= 0
        ):
            continue
        items = sources.get(normalize(monster.mon_name), frozenset()) & wanted
        if items:
            score = sum(1 / remaining[item_id] for item_id in items) / monster.current_hp
            ranked.append((-score, monster.mon_map_id))
    return tuple(spawn_id for _, spawn_id in sorted(ranked))
