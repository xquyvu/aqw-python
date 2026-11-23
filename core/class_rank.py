"""Class progress from inventory class points and server-confirmed CP awards."""

import json

from core.utils import RANK_THRESHOLDS, rank_from_points
from model.inventory import ItemInventory


class ClassRankTracker:
    def __init__(self, equipped_class: ItemInventory):
        if not equipped_class.is_class or "iQty" not in equipped_class.raw:
            raise RuntimeError("The equipped class has no loaded class-point total.")
        self.item_id = equipped_class.item_id
        self.name = equipped_class.s_name
        # A class item's iQty is its accumulated CP, not an item stack count.
        try:
            self.points = int(equipped_class.raw["iQty"])
        except (TypeError, ValueError) as error:
            raise RuntimeError(
                "The equipped class has an invalid class-point total."
            ) from error
        if self.points < 0:
            raise RuntimeError("The equipped class has an invalid class-point total.")
        self.starting_points = self.points

    @property
    def rank(self) -> int:
        return rank_from_points(self.points)

    @property
    def is_max(self) -> bool:
        return self.rank == 10

    @property
    def gained(self) -> int:
        return self.points - self.starting_points

    def on_message(self, message: str):
        if not message.startswith("{"):
            return
        data = json.loads(message).get("b", {}).get("o", {})
        if not isinstance(data, dict) or data.get("cmd") != "addGoldExp":
            return
        if "iCP" not in data:
            return
        gained = int(data["iCP"])
        if gained < 0:
            raise RuntimeError("The server reported a negative class-point award.")
        # iCP is the credited award; bonusCP is informational, not another gain.
        self.points = min(RANK_THRESHOLDS[-1], self.points + gained)

    def log(self):
        print(
            f"CLASS {self.name} | rank={self.rank}/10 | "
            f"CP={self.points:,}/{RANK_THRESHOLDS[-1]:,} | "
            f"CP farmed this session={self.gained:+,}",
            flush=True,
        )
