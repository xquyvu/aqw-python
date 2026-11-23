# Lord of Order: ten daily bots

Run **one script per server day**, in the order below, from the repository root.
Each script accepts only its own daily, collects its requirements, turns it in
once, and stops. There is deliberately no "run all" script. The game server
enforces the shared daily limit; use the next script only after the daily reset.

Configure exactly one account in the repository's `.env`, using the existing
`USERNAME_AQW` and `PASSWORD_AQW` settings. No credentials belong in these scripts.

| Day | Quest | Run |
| --- | --- | --- |
| 1 | Heart of Servitude | `python -u -m bot.lord_of_order.day_01_heart_of_servitude` |
| 2 | Spirit of Justice | `python -u -m bot.lord_of_order.day_02_spirit_of_justice` |
| 3 | Purification of Chaos | `python -u -m bot.lord_of_order.day_03_purification_of_chaos` |
| 4 | Steadfast Will | `python -u -m bot.lord_of_order.day_04_steadfast_will` |
| 5 | Strike of Order | `python -u -m bot.lord_of_order.day_05_strike_of_order` |
| 6 | Harmony | `python -u -m bot.lord_of_order.day_06_harmony` |
| 7 | Ordinance | `python -u -m bot.lord_of_order.day_07_ordinance` |
| 8 | Axiom | `python -u -m bot.lord_of_order.day_08_axiom` |
| 9 | Blessing of Order | `python -u -m bot.lord_of_order.day_09_blessing_of_order` |
| 10 | The Final Challenge | `python -u -m bot.lord_of_order.day_10_the_final_challenge` |

Defaults: **Blaze Binder** for mobs, **Dragonslayer General** for bosses,
**Alteon**, room **1**. Choose classes you own and a populated server/room for
difficult bosses. For example:

```powershell
python -u -m bot.lord_of_order.day_04_steadfast_will --solo-class "Void Highlord" --server Artix --room-number 1
```

Every script supports `--help`, `--farm-class`, `--solo-class`, `--server`,
`--room-number`, `--xiang-class`, and `--item-timeout` (seconds per farmed item;
default 3600).
Each also exposes `async main(cmd)` for the existing interactive launchers.

For Ultra Xiang on day 9, `--xiang-class auto` prefers Dragon of Time, then
Healer (Rare), then Healer, if owned; otherwise it warns and uses the selected
solo class. Override this with, for example, `--xiang-class "Dragon of Time"`.
Healer benefits from Xiang's HP buff. These scripts use the repository's normal
skill scheduler, not a bespoke optimized class rotation.

## Requirements and failure handling

The orchestrator (`python -u -m bot.orchestrator`) also runs this chain, starting
at day 1 and advancing through day 10 across daily resets. It runs only one
Lord of Order daily per reset, then continues to the contract and Ultra Alteon
farms without disconnecting. It never waits in a loop to run the next day's
quest; restart the orchestrator after the next reset.

Confirmed progress is saved per character in
`.aqw_state\lord_of_order_<character id>.json` (ignored by Git). The reset date
uses Eastern server time. Only server-confirmed turn-ins advance the day. An
uncertain turn-in leaves a pending marker and blocks retries until you check
the result in-game and correct that file. Standalone day scripts retain their
existing behavior and do not update this orchestrator progress.

- Be level 50 or higher and finish each preceding daily first.
- Unlock the required story maps and bosses before running their daily. These
  scripts do not complete unrelated story campaigns or bypass access gates.
- Keep free inventory space and sufficient gold for the required purchases.
  Quest materials are consumed by their turn-ins; normal equipment requirements
  are not protected from consumption.
- Bring help for bosses your chosen class cannot defeat. These are single-account
  farming scripts, not coordinated ultra-boss party rotations.

Existing inventory materials are reused and banked materials are retrieved.
Acceptance, purchases, navigation, and turn-ins have bounded waits; farming has
the configurable per-item timeout. A server rejection or missing requirement
stops the bot instead of skipping ahead. Daily completion is reported only after
the server confirms the turn-in. Day 10 selects the **Lord of Order class**, not
a cosmetic reward.

Automatic relogin is disabled once a daily starts to avoid replaying an uncertain
turn-in. If the connection drops or the turn-in acknowledgement times out, check
the quest's actual in-game completion before rerunning. Ordinary inventory
materials survive a restart; temporary quest items may not.

## Researched routes

The quest IDs are **7156–7165**, in daily order. Counts below are per daily;
everything without a count is required once.

| Day | Materials and sources |
| --- | --- |
| 1 | Pristine Blades of Order: Chaorrupted Knight/Chaos Knight, `/watchtower`; Dreadrock Donation Receipt: shop 1221, `/dreadrock`, **1,000,000 gold**; Deadmoor Spirits Helped: Banshee Mallora, `/deadmoor`; Mage's Gratitude: repeat **Defeat Enn'tropy**, quest 6182, `/citadelruins`; Ravenscar's Truth: shop 614, `/ravenscar`, **1,000 gold**. |
| 2 | Warden Elfis Detained: Warden Elfis, `/dwarfprison`; Piggy Drake Punished: Piggy Drake, `/prison`; Mysterious Stranger Foiled: Mysterious Stranger, `/mysteriousdungeon`; Calico Cobby Crushed: Calico Cobby, `/dreammaster`. |
| 3 | Chaoroot x15: Hydra Head, `/hydra`; Chaotic War Essence x15: Ultra Chaos Warlord, `/chaosboss`; Chaorrupting Particles x15: Chaorruption, `/shadowgates`; Purified Raindrop x45: Chaos Lord Lionfang, `/stormtemple`. |
| 4 | Gaiazor's Cornerstone: Gaiazor, `/gaiazor`; Dakka's Crystal: Dakka the Dire Dragon, `/treetitanbattle`; Andre's Necklace Fragment: Giant Necklace, `/andre`; Desolich's Skull: Desolich, `/desolich`. |
| 5 | Hanzamune Dragon Koi Blade: Kitsune, `/kitsune`; The Supreme Arcane Staff: Ledgermayne, `/ledgermayne`; Dragonoid of Hours: Dragonoid, `/mqlesson`; Safiria's Spirit Orb: map item 5470, `/maxius`; Ice Katana: **Inferno Heart**, quest 6319, `/drakonnan`. |
| 6 | Unity of Life: Tree of Destiny, `/elemental`; Harmony of Solace: Faust, `/orchestra`; Teamwork Observed x100: Pactagonal Knight, `/cathedral`; Scroll of Enchantment: Queen's Archsage, `/goose`. |
| 7 | Acolyte's Braille: **Alliance Healer**, `/newfinale`; Suppressed Drows x50: Drow Assassin, `/wardwarf`; Suppressed Undead x50: Skeletal Fire Mage, `/warundead`; Suppressed Horcs x50: Horc Warrior, `/warhorc`; Suppressed Weavers x50: Weaver Queen's Hound, `/weaverwar`; Strength of Resilience: Extriki, `/extriki`. |
| 8 | Law of Nature: Guardian Spirit, `/elfhame`; Law of Time: Kathool, `/deepchaos`; Law of Gravity: ShadowStone Support, `/necrocavern`; Law of Relativity: Reflecteract, `/blackholesun`; Law of Conservation of Energy: Tonitru, `/thunderfang`; Law of Low Drop Rates x100: Red Dragon, `/lair`. |
| 9 | Weapon Imprint x15: Undead Raxgore, `/doomvaultb`; Lure of Order: shop 363, `/greenguardwest`, **Fishing rank 7 required**; Quixotic Mana Essence x10: Ultra Xiang, `/mirrorportal`; Inversion Infusion x5: Serepthys, `/yasaris`. |
| 10 | Champion of Chaos Confronted: Champion of Chaos, `/ultradrakath`. Selects **Lord of Order**, not the cosmetic armor. |

### Important unlocks

- **Day 1:** Finish the Deadmoor story so Banshee Mallora is available. Complete
  Murry's Citadel story and Polish's Citadel Ruins chain through quest 6181;
  the bot repeats quest 6182 for Mage's Gratitude. Unlock Mina's Ghost's shop by
  completing **Blightbringer's Doom** in Ravenscar. The bot purchases Ravenscar's
  Truth; it is not a monster drop.
- **Days 2–4:** Unlock the Spookeasy/Dreammaster, Chaos saga/Shadowgates/Storm
  Temple, Gaiazor, Tree Titan and Giant/Andre bosses as applicable. The scripts
  do not forge story completion flags to enter locked maps.
- **Day 5:** Unlock the relevant Chaos Lords, Maxius and DragonFable Origins
  stories. The Supreme Arcane Staff has a low drop rate. Ice Katana is a
  **quest reward**, not a direct Living Fire drop; the bot farms Inferno Heart
  and completes its quest. Attacks pause while Kitsune is Shapeshifted; keep
  enough health to survive its Realm Shift damage.
- **Days 7–9:** Have access to New Finale, Weaver War, Elfhame, Deep Chaos,
  Necro Cavern, Black Hole Sun, Thunderfang, Doom Vault B and the Mirror Realm
  bosses. Raise **Fishing to rank 7** before day 9; the bot does not train Fishing.
  Ultra Xiang's screen requires **Ward Off the Beast** completed.
- **Day 10:** Complete **Defeat the 12 Lords of Chaos!** to enter `/ultradrakath`.
  This route targets **Champion of Chaos** there, not the different
  Champion Drakath fight used for weekly insignias.

## Sources

Primary source: [Mirror Drakath's Lord of Order quests](https://aqwwiki.wikidot.com/mirror-drakath-s-quests#3).

Numeric quest/shop/map-item IDs and final class item **50741** are corroborated
by [Skua's LordOfOrder script](https://github.com/BrenoHenrike/Scripts/blob/c394d60210884bfb76c288d391a6691e4a40a0c5/Dailies/LordOfOrder.cs).
The Python implementation uses this repository's own command and farming APIs.

Important item-specific references:
[Mage's Gratitude](https://aqwwiki.wikidot.com/mage-s-gratitude),
[Ravenscar's Truth](https://aqwwiki.wikidot.com/ravenscar-s-truth),
[Ice Katana](https://aqwwiki.wikidot.com/ice-katana-2),
[Safiria's Spirit Orb](https://aqwwiki.wikidot.com/safiria-s-spirit-orb),
[Lure of Order](https://aqwwiki.wikidot.com/lure-of-order),
[Champion of Chaos Confronted](https://aqwwiki.wikidot.com/champion-of-chaos-confronted),
[Ultra Xiang](https://aqwwiki.wikidot.com/ultra-xiang),
[Kitsune](https://aqwwiki.wikidot.com/kitsune-monster-1).
