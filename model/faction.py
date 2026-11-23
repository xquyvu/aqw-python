# {
#     'FactionID': '46',
#     'CharFactionID': '45578506',
#     'sName': 'Aegis',
#     'iRep': '302500'
#   }
from core.utils import normalize, rank_from_points

class Faction:
    def __init__(self, faction: dict):
        self.faction_id: int = int(faction.get('FactionID', 0))
        self.char_faction_id: str = str(faction.get('CharFactionID', ''))
        self.faction_name: str = normalize(faction.get('sName', ''))
        self.rep: int = int(faction.get('iRep', 0))
    
    def get_rep(self) -> int:
        return self.rep
    
    def add_rep(self, irep: int) -> None:
        self.rep += irep
    
    def is_max(self) -> bool:
        return self.get_rank() == 10
    
    def get_rank(self) -> int:
        return rank_from_points(self.rep)