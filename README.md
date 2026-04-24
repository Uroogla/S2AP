# Instructions:

## Playing a Game with Spyro 2

### Required Software

Important: At this time, Mac is not supported, since I do not have access to a device to test.
Want to help with testing for Mac support? Feel free to reach out!

- One of the following supported emulators:
  - [Duckstation](https://www.duckstation.org) - Detailed installation instructions for Duckstation can be found at [this link](https://github.com/ArsonAssassin/Archipelago.Core/wiki/How-to-start-playing-a-game-using-this-library). This option has been tested more for Spyro 2 by the community. Linux users will need the **Windows Portable** option.
  - [Bizhawk](https://tasvideos.org/BizHawk/ReleaseHistory) - Tested on versions 2.9.1 and 2.10; with less recent versions of Archipelago, you may need less recent versions.
- [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) version 0.6.1 or later.
- The [Spyro 2 Archipelago .apworld](https://github.com/Uroogla/S2AP/releases). If you are playing on Duckstation, you also need the Client (within the s2ap .zip file).
- A legal US Spyro 2: Ripto's Rage ROM.  We cannot help with this step.

Linux Duckstation users will need a recent version of Wine (tested with Winetricks version 20260125-1.1).

### Create a Config (.yaml) File

#### What is a config file and why do I need one?

See the guide on setting up a basic YAML at the Archipelago setup guide: [Basic Multiworld Setup Guide](https://archipelago.gg/tutorial/Archipelago/setup_en)

This also includes instructions on generating and hosting the file.  The "On your local installation" instructions
are particularly important.

#### Where do I get a config file?

Run `ArchipelagoLauncher.exe`.  You can run Generate Template Options, copy `Spyro 2.yaml`, fill it out, and place
it in the `players` folder. On newer versions of Archipelago, you can choose Options Creator for a more visual
approach.

### Generate and host your world

Run `ArchipelagoGenerate.exe` (or select Generate from the launcher) to build a world from the YAML files in your `players` folder.  This places
a `.zip` file in the `output` folder.

You may upload this to [the Archipelago website](https://archipelago.gg/uploads) or host the game locally with
`ArchipelagoHost.exe`. It's generally recommended to use the website.

### Setting Up Spyro 2 for Archipelago

Please follow the options below corresponding to your choice of emulator. Linux users, please note the amended instructions given below.

#### For Duckstation:

1. Download the s2ap .zip file and spyro2.apworld from the GitHub page linked above.
2. Double click the apworld to install to your Archipelago installation.
3. Extract the S2AP .zip file and note where S2AP.Desktop.exe is.
4. Open Duckstation and load into Spyro 2: Ripto's Rage.
5. In Duckstation, navigate to Settings > Game Properties > Console and select "Interpreter" under "Execution Mode".
6. Start a new game (or if continuing an existing seed, load into that save file).
7. Open S2AP.Desktop.exe, the Spyro 2 client.  You will likely want to do so as an administrator.
8. In the top left of the Spyro 2 client, click the "burger" menu to open the settings page.
9. Enter your host, slot, and optionally your password.
10. Click Connect.
11. Start playing!

#### For BizHawk:

1. Download spyro2.apworld from the GitHub page linked above. You do not need the s2ap .zip file.
2. Double click the apworld to install to your Archipelago installation.
4. Open Bizhawk and load into Spyro 2: Ripto's Rage.
5. If you're using BizHawk 2.7 or 2.8, go to Config > Customize. On the Advanced tab, switch the Lua Core from NLua+KopiLua to Lua+LuaInterface, then restart EmuHawk.
6. Under Config > Customize, check the "Run in background" option to prevent disconnecting from the client while you're tabbed out of the emulator.
7. Under Config > Preferred Cores > PSX, select NymaShock.
8. Within the Archipelago Launcher, select BizHawk Client.
9. In EmuHawk, go to Tools > Lua Console. This window must stay open while playing. Be careful to avoid clicking "TAStudio" below it in the menu, as this is known to delete your savefile.
10. In the Lua Console window, go to Script > Open Script.
11. Navigate to your Archipelago install folder and open data/lua/connector_bizhawk_generic.lua. The emulator and client will eventually connect to each other. The BizHawk Client window should indicate that it connected and recognized Spyro 2.
12. To connect the client to the server, enter your room's address and port (e.g. archipelago.gg:38281) into the top text field of the client and click Connect.
13. Enter your slot name when prompted.
14. Start a new game (or if continuing an existing seed, load into that save file).
15. Start playing!

#### Linux

For Duckstation:

Duckstation requires the **Windows portable** version of Duckstation, as well as Wine (tested successfully on Winetricks version 20260125-1.1).  Keep all relevant directories (such as your bios files and the client) within the same Wine prefix. Otherwise, setup matches the Windows version.

For BizHawk:

BizHawk works as a standalone option on Linux, meaning it does not require Wine.

### Optional Setup

There is a [Poptracker](https://poptracker.github.io) package for this game, which can help you identify which checks are available.
It can be found at https://github.com/routhken/Spyro_2_tracker/releases.

[Universal Tracker](https://github.com/FarisTheAncient/Archipelago/releases) is partially supported as well, but you may encounter
issues if you randomize your yaml settings file.

## What does randomization do to this game?

When the player completes a task (such as collecting a talisman or orb), an item is sent.

This does not randomize the location of orbs, talismans, or gems, or shuffle entrances.

Progression is based on items the player has received, not what they have completed in game.
It is possible to advance to the next world without having completed each level first,
if you are sent the right items to do so.

The following options significantly impact gameplay. All default to off or vanilla behavior.

- Moneybagssanity - Creates an item for each Moneybags unlock. Prevents paying for these unlocks.
- Open World mode - Removes talismans and talisman locks from the game. Typically best for playing with other open games.
- Level Locks - Adds keys to the item pool that are required to enter specific levels. Strongly encouraged with Open World mode. Increases the likelihood of becoming stuck.
- Ability options - The player can start with, shuffle into the item pool, or disable double jump and the permanent fireball ability. The player can also start with swim, climb, and headbash.
- Tricks - As of version 1.2.0, the player may pick specific speedrunning tricks to put into logic.
- Progressive Sparx Health - Start with a lower max health and unlock upgrades. Optionally, logically require sufficient max health for some levels.
- Easy challenges - The player may modify a number of challenges to make them easier than in vanilla, if desired.
- Death Link - Will not trigger in speedways or Dragon Shores to prevent softlocks and crashes.

Some small cosmetic randomization options are also available.

## What items and locations get shuffled?
The following locations always grant shuffled items.

- Talismans (14)
- Orbs (64)

The following locations may grant shuffled items based on player options.

- Individual gems (random 200 or all 2546) - Choosing all 2546 ("full gemsanity") requires host approval.
- Having total gem count reach a multiple of 500 (up to 20 locations)
- Collecting 100, 200, 300, and/or 400 gems in a given level (up to 4 checks per level, 25 levels)
- Skill Points (16)
- Life Bottles (23)
- Collecting every spirit particle in a level (18)

The following locations may be included in the multiworld but grant the same item each time.

- Defeating each boss (3)
- Dragon Shores token minigames (10)
- Moneybags Unlocks paid for with gems (11)
- Skill Points goal locations (16)

In addition to 64 orbs and, depending on settings, 6 Summer Forest Talismans and 8 Autumn Plains Talismans,
depending on the player's options, Moneybags unlocks may
be shuffled into the item pool, rather than having the player pay Moneybags.
Level Keys and Progressive Sparx Health Upgrades are also possible items.
Leftover items will be "filler", based on the player's
options.  Examples include giving extra lives, temporary invisibility, changing Spyro's color, or making the player Sparxless.

## Which items can be in another player's world?

Any of the items which can be shuffled may also be placed into another player's world.

## What does another world's item look like in Spyro 2?

The visuals of the game's items are unchanged by the Archipelago randomization.  The Spyro 2 Archipelago Client
will display the obtained item and to whom it belongs.

## When the player receives an item, what happens?

The player's game and HUD will update accordingly, provided that they are in their save file.  Some effects,
such as healing Sparx, may operate with a delay to avoid unintended interactions in game.

Talisman count is not displayed in game.  The `!talismans` command (Duckstation) or `/talismans` command (BizHawk) can be entered into the client to see the current counts.

Receiving a Moneybags unlock will complete the unlock automatically.

## Unique Local Commands

The following commands (starting with a / for BizHawk and an ! for Duckstation) are available when using the S2AP client to play with Archipelago.

- `talismans` Prints how many Summer Forest Talisman items and how many Autumn Plains Talisman items the player has received.
- `unlockedLevels` Show which levels the player has unlocked in open world mode.
- `goal` Show what your completion goal is.
- `options` Show some of your most important options.
- `debugInfo` Information that may be helpful when reporting bugs.
- `patch` (Duckstation only) Creates a patched version of your vanilla ROM for Archipelago. This is not seed-specific and is optional.

## Known Issues and Tentative Roadmap

As of v2.0.0, 24 Apr 2026:
### Known Issues
- Sharks in Aquaria Towers do not trigger Death Link.
- During Gemsanity, loading into an existing save may release some gem% checks incorrectly, based on what you've collected rather than received.
- Connecting to the client in a homeworld may warp Spyro or unlock doors based on your vanilla completion, not what you have received. This is fixed if using the game patch.
- Starting with Moneybags Unlocks when Moneybagssanity is vanilla will give you extra gems after beating Ripto.
- If your YAML file allows Archipelago to randomly pick settings, Universal Tracker may not track correctly.

Please report in the Spyro 2 thread of the Archipelago Discord, or here on GitHub, if you encounter any unexpected behavior!

### Current Roadmap:
- Sparx powerups as items (extended range, always point to nearest gem, extra hit point cheat code)
- Add locks around powerups
- Implement Entrance Randomizer
- Support PAL and NTSC-J
- Support Mac
- Client performance improvements

For latest list of known issues and desired features, see https://github.com/Uroogla/S2AP/issues.  Reporting issues in the Archipelago Discord thread for Spyro 2 is preferred, but reports to this link will be read as well.
