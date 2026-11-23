"""Shared session reputation reporting using the player's live faction data."""

from typing import TYPE_CHECKING

from core.utils import normalize

if TYPE_CHECKING:
    from core.player import Player
    from model.faction import Faction


class ReputationTracker:
    def __init__(self, player: "Player", faction_name: str):
        self.player = player
        self.faction_name = faction_name
        self.starting_points = self._faction().get_rep()
        self.last_points: int | None = None

    def _faction(self) -> "Faction":
        name = normalize(self.faction_name)
        for faction in self.player.FACTIONS:
            if normalize(faction.faction_name) == name:
                return faction
        raise RuntimeError(
            f"Reputation data for {self.faction_name} is not loaded."
        )

    @property
    def is_max(self) -> bool:
        return self._faction().is_max()

    def log(self, *, force: bool = False) -> None:
        faction = self._faction()
        points = faction.get_rep()
        if not force and points == self.last_points:
            return
        print(
            f"{self.faction_name} reputation: {points:,} points | "
            f"Rank {faction.get_rank()}/10 | "
            f"Farmed this session: {points - self.starting_points:+,} points",
            flush=True,
        )
        self.last_points = points
