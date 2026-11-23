"""Requirements from Mirror Drakath's wiki; see README for sources and gates."""

from bot.lord_of_order.runner import Daily, Hunt, Pickup, Purchase, SideQuest


DAILIES = (
    Daily(
        7156,
        "Heart of Servitude",
        (
            Hunt(
                "Pristine Blades of Order",
                "watchtower",
                "Chaorrupted Knight,Chaos Knight",
                boss=False,
            ),
            Purchase("Dreadrock Donation Receipt", "dreadrock", 1221),
            Hunt("Deadmoor Spirits Helped", "deadmoor", "Banshee Mallora"),
            SideQuest(
                "Mage's Gratitude",
                "citadelruins",
                6182,
                (Hunt("Enn'tr\u00f6py Defeated", "citadelruins", "Enn'tr\u00f6py"),),
                "Finish Murry's Citadel and Polish's Citadel Ruins story through "
                "quest 6181 before repeating Defeat Enn'tropy.",
            ),
            Purchase("Ravenscar's Truth", "ravenscar", 614),
        ),
        ("Lord of Order Wrap", "Lord of Order Bladed Wrap"),
    ),
    Daily(
        7157,
        "Spirit of Justice",
        (
            Hunt("Warden Elfis Detained", "dwarfprison", "Warden Elfis"),
            Hunt("Piggy Drake Punished", "prison", "Piggy Drake"),
            Hunt(
                "Mysterious Stranger Foiled",
                "mysteriousdungeon",
                "Mysterious Stranger",
            ),
            Hunt("Calico Cobby Crushed", "dreammaster", "Calico Cobby"),
        ),
        ("Lord Of Order Wings", "Lord of Order Wings + Wrap"),
    ),
    Daily(
        7158,
        "Purification of Chaos",
        (
            Hunt("Chaoroot", "hydra", "Hydra Head", 15),
            Hunt("Chaotic War Essence", "chaosboss", "Ultra Chaos Warlord", 15),
            Hunt("Chaorrupting Particles", "shadowgates", "Chaorruption", 15),
            Hunt("Purified Raindrop", "stormtemple", "Chaos Lord Lionfang", 45),
        ),
        ("Lord of Order Double Wings + Wrap",),
    ),
    Daily(
        7159,
        "Steadfast Will",
        (
            Hunt("Gaiazor's Cornerstone", "gaiazor", "Gaiazor"),
            Hunt("Dakka's Crystal", "treetitanbattle", "Dakka the Dire Dragon"),
            Hunt("Andre's Necklace Fragment", "andre", "Giant Necklace"),
            Hunt("Desolich's Skull", "desolich", "Desolich"),
        ),
        ("Lord of Order Helm",),
    ),
    Daily(
        7160,
        "Strike of Order",
        (
            Hunt(
                "Hanzamune Dragon Koi Blade", "kitsune", "Kitsune",
                strategy="kitsune",
            ),
            Hunt("The Supreme Arcane Staff", "ledgermayne", "Ledgermayne"),
            Hunt("Dragonoid of Hours", "mqlesson", "Dragonoid"),
            Pickup("Safiria's Spirit Orb", "maxius", 5470),
            SideQuest(
                "Ice Katana",
                "drakonnan",
                6319,
                (Hunt("Inferno Heart", "drakonnan", "Living Fire", boss=False),),
                "Finish the DragonFable Origins story to unlock Inferno Heart.",
            ),
        ),
        ("Lord of Order Horns",),
    ),
    Daily(
        7161,
        "Harmony",
        (
            Hunt("Unity of Life", "elemental", "Tree of Destiny"),
            Hunt("Harmony of Solace", "orchestra", "Faust"),
            Hunt("Teamwork Observed", "cathedral", "Pactagonal Knight", 100, False),
            Hunt("Scroll of Enchantment", "goose", "Queen's Archsage"),
        ),
        ("High Lord of Order Helm",),
    ),
    Daily(
        7162,
        "Ordinance",
        (
            Hunt("Acolyte's Braille", "newfinale", "Alliance Healer", boss=False),
            Hunt("Suppressed Drows", "wardwarf", "Drow Assassin", 50, False),
            Hunt("Suppressed Undead", "warundead", "Skeletal Fire Mage", 50, False),
            Hunt("Suppressed Horcs", "warhorc", "Horc Warrior", 50, False),
            Hunt(
                "Suppressed Weavers", "weaverwar", "Weaver Queen's Hound", 50, False
            ),
            Hunt("Strength of Resilience", "extriki", "Extriki"),
        ),
        ("Lord of Order Blade",),
    ),
    Daily(
        7163,
        "Axiom",
        (
            Hunt("Law of Nature", "elfhame", "Guardian Spirit"),
            Hunt("Law of Time", "deepchaos", "Kathool"),
            Hunt("Law of Gravity", "necrocavern", "ShadowStone Support"),
            Hunt("Law of Relativity", "blackholesun", "Reflecteract"),
            Hunt("Law of Conservation of Energy", "thunderfang", "Tonitru"),
            Hunt("Law of Low Drop Rates", "lair", "Red Dragon", 100),
        ),
        ("Lord of Order Polearm",),
    ),
    Daily(
        7164,
        "Blessing of Order",
        (
            Hunt("Weapon Imprint", "doomvaultb", "Undead Raxgore", 15),
            Purchase("Lure of Order", "greenguardwest", 363),
            Hunt(
                "Quixotic Mana Essence", "mirrorportal", "Ultra Xiang", 10,
                strategy="xiang",
            ),
            Hunt("Inversion Infusion", "yasaris", "Serepthys", 5),
        ),
        ("Lord Of Order Armor",),
    ),
    Daily(
        7165,
        "The Final Challenge",
        (
            Hunt(
                "Champion of Chaos Confronted", "ultradrakath", "Champion of Chaos"
            ),
        ),
        ("Lord Of Order",),
        choice="Lord Of Order",
        reward_id=50741,
    ),
)
