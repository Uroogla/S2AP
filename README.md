# Instructions:

[Click Here](https://github.com/ArsonAssassin/Archipelago.Core/wiki/How-to-start-playing-a-game-using-this-library) for
general instructions.

## Playing a Game with Spyro 2

### Required Software

Important: As the mandatory client runs only on Windows, no other systems are supported.

- [Duckstation](https://www.duckstation.org) - Detailed installation instructions for Duckstation can be found at the above link.
- Archipelago version 0.6.1 or later.
- The [Spyro 2 Archipelago Client and .apworld](https://github.com/Uroogla/S2AP/releases)
- A legal US Spyro 2: Ripto's Rage ROM.  We cannot help with this step.
### Create a Config (.yaml) File

#### What is a config file and why do I need one?

See the guide on setting up a basic YAML at the Archipelago setup guide: [Basic Multiworld Setup Guide](https://archipelago.gg/tutorial/Archipelago/setup_en)

This also includes instructions on generating and hosting the file.  The "On your local installation" instructions
are particularly important.

#### Where do I get a config file?

Run `ArchipelagoLauncher.exe` and generate template files.  Copy `Spyro 2.yaml`, fill it out, and place
it in the `players` folder.

### Generate and host your world

Run `ArchipelagoGenerate.exe` to build a world from the YAML files in your `players` folder.  This places
a `.zip` file in the `output` folder.

You may upload this to [the Archipelago website](https://archipelago.gg/uploads) or host the game locally with
`ArchipelagoHost.exe`.

### Setting Up Spyro 2 for Archipelago

1. Download the S2AP.zip and spyro2.apworld from the GitHub page linked above.
2. Double click the apworld to install to your Archipelago installation.
3. Extract S2AP.zip and note where S2AP.Desktop.exe is.
4. Open Duckstation and load into Spyro 2: Ripto's Rage.
5. In Duckstation, navigate to Settings > Game Properties > Console and select "Interpreter" under "Execution Mode".
6. Start a new game (or if continuing an existing seed, load into that save file).
7. Open S2AP.Desktop.exe, the Spyro 2 client.  You will likely want to do so as an administrator.
8. In the top left of the Spyro 2 client, click the "burger" menu to open the settings page.
9. Enter your host, slot, and optionally your password.
10. Click Connect. The first time you connect, a few error messages may appear - these are okay.
11. Start playing!

### Optional Setup

There is a [Poptracker](https://poptracker.github.io) package for this game, which can help you identify which checks are available.
It can be found at https://github.com/routhken/Spyro_2_tracker/releases.

[Universal Tracker](https://github.com/FarisTheAncient/Archipelago/releases) is partially supported as well, but you may encounter
issues with random settings, gemsanity, and world keys.

## What does randomization do to this game?

When the player completes a task (such as collecting a talisman or orb), an item is sent.
Collecting one of these may not increment the player's orb counter or count as a received talisman,
while a check received from another game may do so.

This does not randomize the location of orbs, talismans, or gems, shuffle entrances, or make large-scale cosmetic changes to the game.

Unlocking doors requires collecting the corresponding items through Archipelago.  Unlike the vanilla game, you may not need to complete
the talisman check for every level to advance.  The HUD's orb count
shows how many orb items you have received, while the in game Guidebook shows which checks you have completed.

## What items and locations get shuffled?
Talismans and orbs are always shuffled.  Based on the player's options, skill points and milestones for reaching certain numbers of gems
per level or overall may also release checks.

The item pool will always contain 6 Summer Forest talismans, 8 Autumn Plains talismans, and 64 orbs.
Depending on the player's options, Moneybags unlocks may
be shuffled into the pool, rather than having the player pay Moneybags.  Leftover items will be "filler", based on the player's
options.  Examples include giving extra lives, temporary invisibility, changing Spyro's color, or making the player Sparxless.

## Which items can be in another player's world?

Any of the items which can be shuffled may also be placed into another player's world.

## What does another world's item look like in Spyro 2?

The visuals of the game are unchanged by the Archipelago randomization.  The Spyro 2 Archipelago Client
will display the obtained item and to whom it belongs.

## When the player receives an item, what happens?

The player's game and HUD will update accordingly, provided that they are in their save file.  Some effects,
such as healing Sparx, may operate with a delay to avoid unintended interactions in game.

Talisman count is not displayed in game.  The `showTalismanCount` command can be entered into the client to see the current counts.

Receiving a Moneybags unlock will complete the unlock automatically.

If for any reason the player is not in their save file when items come in, there may be a temporary desync.
Talisman and orb count will update the next time the player completes a check or receives an item.  Missed Moneybags
unlocks require the `clearSpyroGameState` command to be entered into the client.

## Unique Local Commands

The following command (without a slash or exclamation point) is available when using the S2AP client to play with Archipelago.

- `clearSpyroGameState` Resync your save file's received items with the server.  This may result in duplicate filler items.
If playing on a new save file, you will still need to get to the end of each level and defeat the bosses to progress in the game.
- `showTalismanCount` Prints how many Summer Forest Talisman items and how many Autumn Plains Talisman items the player has received.
- `useQuietHints` Suppresses hints for found locations to make the client easier to read. On by default.
- `useVerboseHints` Include found locations in hint lists. Due to Archipelago Server limitations, only applies to hints requested after this change.
- `showUnlockedLevels` Show which levels the player has unlocked in open world mode.
- `showGoal` Show what your completion goal is.
