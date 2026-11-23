# AQW Python Bot

A comprehensive automation toolkit for AdventureQuest Worlds (AQW) that enables automated farming, questing, and combat operations.

> **Notice**: This software is designed for educational purposes and to assist with repetitive in-game tasks. Users are responsible for ensuring compliance with AQW's terms of service.

## Features

- **Dual Automation Modes**: Simple command queue system and advanced Python scripting capabilities
- **Quest Management**: Automated quest acceptance and completion
- **Combat System**: Intelligent monster targeting and skill execution
- **Inventory Control**: Automated item purchasing, selling, equipping, and management
- **Bank Integration**: Seamless item transfers between inventory and bank storage
- **Navigation System**: Automated map and location movement
- **Safety Mechanisms**: Built-in error handling and connection management

## System Requirements

- **Python 3.9 or higher** - [Download Python](https://www.python.org/downloads/)

## Installation Guide

### Step 1: Repository Acquisition

1. Open your terminal or command prompt interface
2. Clone the repository using Git:
   ```bash
   git clone https://github.com/Froztt13/aqw-python.git
   ```
3. Navigate to the project directory:
   ```bash
   cd aqw-python
   ```

### Step 2: Dependency Installation

Install the required Python packages:
```bash
pip install -r requirements.txt
```

Installation is now complete. You may proceed to the usage section.

## Usage Instructions

### Mode 1: Sequential Command Execution

This mode is suitable for users requiring simple automation tasks.

**Functionality**: Executes predefined commands in sequential order

**Example execution**:
```bash
python -m bot_cmds.bot_tes
```

**Process**:
1. Locate script files in the `bot_cmds/` directory
2. Each script contains ordered command sequences
3. The bot processes commands systematically
4. Scripts are easily modified and comprehensible

**Creating Custom Sequential Command Bots**:

To create your own sequential command execution bot:

1. **Available Commands**: Navigate to `D:\Python\aqw-python\commands` directory to access all available commands
2. **Command Structure**: Each command file contains predefined automation functions
3. **Create Custom Script**: Create a new Python file in the `bot_cmds/` directory
4. **Import Commands**: Import the required commands from the commands directory
5. **Sequence Execution**: Arrange commands in the desired execution order
6. **Configuration**: Modify parameters and settings as needed

**Example Custom Bot Structure**:

Refer to `D:\Python\aqw-python\bot_cmds\bot_tes.py` for a complete working example:

```python
from core.bot import Bot
import commands as cmd
from templates.attack import attack_monster
from templates.general import un_bank_items
import asyncio

# Initialize variables
drop_whitelist = [
    "Unidentified 19",
    "Unidentified 13",
    "Tainted Gem",
    "Dark Crystal Shard",
    "Diamond of Nulgath",
    "Voucher of Nulgath",
    "Voucher of Nulgath (non-mem)",
    "Random Weapon of Nulgath",
    "Gem of Nulgath",
    "Relic of Chaos"
]

# Initialize bot
b = Bot(
    roomNumber=9099,
    itemsDropWhiteList=drop_whitelist,
    cmdDelay=1000,
    showLog=True,
    showDebug=False,
    showChat=True
)
b.set_login_info("username", "password", "server")

# Arrange commands
b.add_cmds([
    *un_bank_items(items=drop_whitelist),
    cmd.RegisterQuestCmd(2857),
    cmd.JoinMapCmd("escherion"),
    cmd.JumpCmd("Boss", "Left"),
    cmd.LabelCmd("ATK"),
    *attack_monster(monster_name="Staff of Inversion,Escherion"),
    cmd.ToLabelCmd("ATK"),
    cmd.StopBotCmd()
])

# Start bot
asyncio.run(b.start_bot())
```

**Bot Structure Explanation**:
- **Import Required Modules**: Bot class, commands, templates
- **Initialize Variables**: Define drop whitelist and bot settings
- **Create Bot Instance**: Configure room, delay, logging preferences
- **Set Login Credentials**: Provide username, password, and server
- **Add Command Sequence**: Arrange commands in execution order
- **Start Bot Execution**: Run the bot asynchronously

### Mode 2: Advanced Python Scripting

This mode provides comprehensive control over bot behavior for experienced users.

**Functionality**: Custom Python code implementation for complex automation scenarios

**Example execution**:
```bash
python start.py
```

**Process**:
1. Utilize the `bot/` package to access bot functionalities
2. Develop custom Python scripts
3. Implement sophisticated farming and questing routines
4. Complete customization and flexibility

**Advanced Command Integration**:

For advanced Python scripting, you can access the comprehensive command class located at `D:\Python\aqw-python\core\command.py`:

1. **Command Class**: The `Command` class in `core/command.py` provides access to all bot functionalities
2. **Complete API**: Access to quest management, item operations, combat system, and navigation
3. **Method Integration**: Direct method calls for precise control over bot behavior
4. **Error Handling**: Built-in error handling and safety mechanisms
5. **Asynchronous Support**: Full async/await support for complex operations

**Example Advanced Script Structure**:
```python
from core.command import Command
from core.bot import Bot

# Initialize bot and command instances
bot = Bot()
cmd = Command(bot)

# Advanced automation with full control
async def advanced_farming_routine():
    await cmd.join_map("escherion")
    await cmd.jump_cell("Boss", "Left")

    # Complex logic and conditions
    skills = [0,1,2,0,3,4]
    skill_index = 0
    while cmd.is_player_alive():
        await cmd.use_skill(skills[skill_index], "Staff of Inversion,Escherion")
        skill_index = skill_index + 1
        if skill_index >= len(skills):
            skill_index = 0
        await cmd.sleep(100)
```

**Key Command Class Features**:
- **Quest Operations**: `accept_quest()`, `turn_in_quest()`, `ensure_accept_quest()`
- **Item Management**: `buy_item()`, `sell_item()`, `equip_item()`, `bank_to_inv()`
- **Combat Control**: `use_skill()`, `start_aggro()`, `leave_combat()`
- **Navigation**: `join_map()`, `jump_cell()`, `goto_player()`
- **Player Information**: `get_player()`, `is_player_alive()`, `get_monster_hp()`

### Configuration-driven quest farming

For repeatable quests farmed on one screen, define a `FarmConfig` instead of
writing another combat/quest loop. Existing scripts keep their one-command launch:

```powershell
python -u -m bot.embersea_rep
python -u -m bot.embersea_quests
python -u -m bot.dragonslayer_general
python -u -m bot.exp_farming
python -u -m bot.chaos_rep
python -u -m bot.arcangrove_rep
python -u -m bot.arcangrove_rep_solo
```

For the Elder's Blood and Glacera Ice Token dailies, run:

```powershell
python -u -m bot.daily
```

This farms the three-Gorillaphant screen in `arcangrove` with Blaze Binder,
then Frost Invaders in `frozenruins` with Dragonslayer General. Each quest
is turned in once, and the bot stops after both steps. Server-rejected quests
(already done today or locked) are logged and skipped; unlock Syrrus's daily
quests beforehand. Both classes must be in inventory or bank.

These read one account from `USERNAME_AQW` and `PASSWORD_AQW` in the repository's
`.env`. The configuration selects the server and room. For example:

```python
from core.command import Command
from core.quest_farm import FarmConfig, Quest, Screen, farm_quests, run_farm

CONFIG = FarmConfig(
    name="Embersea reputation",
    quests=(
        Quest(4218, "Round 3: Firestorm Pikemen"),
        Quest(4219, "Round 4: Firestorm Knights"),
        Quest(4229, "Take out the Firestorm Knights"),
    ),
    map_name="fireforge",
    screen=Screen(monsters={"Fire Pikeman": 2, "Firestorm Knight": 2}),
    combo="ready",
    reputation="Embersea",
    server="Alteon",
    mode="leech",
    room_number=1,
)

async def main(cmd: Command):
    await farm_quests(cmd, CONFIG)

if __name__ == "__main__":
    run_farm(CONFIG)
```

Save a new configuration as a module under `bot`, then launch it with
`python -u -m bot.your_module`. `main` also preserves compatibility with `start.py`.

Every `FarmConfig` defaults to `mode="leech"`: it uses the configured common
server (`Alteon` by default) and requests public `room_number=1` when joining
the map. Once in the map, any room is accepted, including server substitutions;
the bot stays there instead of forcing a transfer back to room 1.
Set `mode="solo"` to use `solo_room_number=90999` instead and enforce that exact
room. Server and room choices are configurable; a public room is not guaranteed
to contain other farmers.

The default class is **Blaze Binder**, with the ready-skill rotation. Existing
quest-farming configurations inherit this default; set `class_name` and, if
needed, `combo` to override it. The EXP farm's explicit class and the selectable
class-ranking script are unchanged.

All bots default to accepting every non-member drop using the existing
`accept_non_member_drops` policy, including non-member AC items. Member-only
items are skipped even if named in a drop whitelist. To restore whitelist-only
pickup for a specialized script, set `cmd.bot.accept_non_member_drops = False`.

Per-drop temporary-item messages are hidden by default. To show them for
debugging, use `Bot(showDebug=True)` or set `cmd.bot.showDebug = True`.
Temporary inventory quantities and quest progress still update normally;
regular item-drop logs and periodic farming progress remain visible.

`bot.chaos_rep` farms `mountdoomskull`, cell `b1`, on Alteon in leech mode.
It attempts Embrace Your Chaos (Daily), quest 3596, once per run and completes
it before repeating Embrace Your Chaos, quest 3594. A server rejection of the
optional daily is logged and skipped, as is a `Missing Badge` rejection when
turning it in. Other turn-in errors and missing responses still raise errors.
It logs Chaos reputation rank, total points and session gains. Restart the
script after the daily reset to attempt the daily again.

`bot.arcangrove_rep` equips Dragonslayer General and farms the Mafic Dragon in
`mafic` on Alteon in leech mode. It repeats Feed Me (quest 848), turning in one
Burning Heart at a time, and logs Arcangrove reputation rank and session gains.
The boss screen is selected from the map's monster roster.

`bot.arcangrove_rep_solo` equips Blaze Binder and farms `arcangrove-90999` in
solo mode. It finds the screen with exactly three Gorillaphant spawns, including
respawning monsters, and repeats Gorillaphant Poaching (795), Pleased to Meat
You (799), and Ebony and Ivory Tusks (801). It uses all ready skills and logs
Arcangrove reputation rank, points and session gains. The Mafic leech farm
remains available as `bot.arcangrove_rep`.

Quest names are descriptive labels; **IDs must be looked up and verified**.
Screen counts are exact and include dead/respawning monsters. Use `None` instead
of a count to require at least one, or specify `cell="r4", pad="Right"` alongside
the expected monsters to select and validate a known cell.

For combat-only farming, set `quests=()`. Use an empty monster roster with a
fixed cell to attack all monsters there, for example
`Screen(monsters={}, cell="Enter", pad="Spawn")`. `bot.exp_farming` uses this
setup with Dragonslayer General in `sevencircleswar`, initially requesting room 1; it
also accepts and repeats War Medals (7980) and Mega War Medals (7981), turning
them in whenever their medal requirements are met.
`track_exp=True` logs EXP gained from the live server-updated counter at the
configured `report_interval` (60 seconds by default).

`combo="ready"` uses any ready class skill or auto-attack, respecting cooldowns
and server pacing. For the existing Master Ranger combo, import
`attack_next_skill` from `combo.master_ranger` and set `combo=attack_next_skill,
auto_attack=True` (keys 2/3, key 5 priority, plus key 1). Custom async combo
functions take `(cmd, targets, skill_index)` and return the next index.
For Dragonslayer General, import `attack_next_skill` from
`combo.dragonslayer_general`. It prioritizes key 5 whenever ready, then cycles
through other ready skills including auto-attack, using the existing cooldown,
mana and server-pacing checks.
For optional daily quests, use `Quest(..., optional=True, repeat=False)`.

The shared flow verifies the equipped class and map (also the exact room in
solo mode), accepts and
repeats all configured quests, confirms server turn-ins, and logs the selected
screen, quest-item progress and session completion counts. Optional `reputation`
logs current points, rank and session gains from live faction data and stops
the bot permanently at rank 10 (including if already maxed on startup); `drops`
adds named items to the pickup whitelist. Missing factions or screens, rejected
quests, solo-mode room substitutions and timeouts are reported as errors, not success.
It never changes rooms to find a quieter/private instance.

This pattern covers single-screen farms. Doomwood's multi-map drop planner and
Sandsea's per-monster route remain specialized scripts.

### Ranking a class to 10

```powershell
python -u -m bot.farm_melee --class "Dragonslayer General"
python -u -m bot.farm_melee --class "Blaze Binder"
```

This script equips the named class from inventory or bank, joins Seven Circles
War on Alteon (requests room 1 but accepts whichever room it lands in), and uses
the hunt-helper attack loop tested with melee classes. It logs class rank,
class points (CP), CP gained this session and EXP gains. It stops automatically
at class rank 10, including when the class was already maxed, and disables
relogin on completion.

Class rank is separate from faction reputation. Progress uses the class's
server-loaded CP total and actual CP awards, not an estimate from EXP.
Omitting `--class` keeps Dragonslayer General as the default. To run a bounded
combat check that stops on the first CP gain:

```powershell
python -u -m bot.farm_melee --class "Dragonslayer General" --test-seconds 90
```

## Command Documentation

For detailed function documentation and method references, please refer to the official documentation:

**Documentation Website**: [https://froztt13.github.io/aqw-python/](https://froztt13.github.io/aqw-python/)

**Currently Available**:
- Complete function documentation for the Command class
- Method parameters and return values
- Usage examples for individual functions
- API reference documentation

**For Complete Examples and Templates**:
- Sequential command examples: `D:\Python\aqw-python\bot_cmds\bot_tes.py`
- Command templates: `D:\Python\aqw-python\templates\`
- Available commands: `D:\Python\aqw-python\commands\`

## Docker Deployment (Optional)

For users familiar with containerized applications:

1. **Build and initialize**:
   ```bash
   docker-compose up --build -d
   ```

2. **Terminate containers**:
   ```bash
   docker-compose down
   ```

3. **Access container logs**:
   ```bash
   docker-compose logs
   ```

---

For detailed documentation and advanced usage instructions, visit: [https://froztt13.github.io/aqw-python/](https://froztt13.github.io/aqw-python/)
