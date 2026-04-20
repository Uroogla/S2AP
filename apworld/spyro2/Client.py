import logging
import math
import pkgutil
import random

import orjson

import Utils
import time

from BaseClasses import ItemClassification
from NetUtils import ClientStatus, NetworkItem

from typing import TYPE_CHECKING, Optional, Dict, Set, ClassVar, Any, Tuple, Union

import worlds._bizhawk as bizhawk

from worlds._bizhawk.client import BizHawkClient

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext, BizHawkClientCommandProcessor

from .Addresses import RAM
from .Enums import GameStatus, LevelInGameIDs, SpyroColor
from .LevelData import GetLevelData

from .Options import GoalOptions, MoneybagsOptions, GemsanityOptions, LevelLockOptions, AbilityOptions

logger = logging.getLogger("Client")

def cmd_s2_commands(self: "BizHawkClientCommandProcessor") -> None:
    """Show what commands are available for Spyro 2 Archipelago"""
    from worlds._bizhawk.context import BizHawkClientContext
    if self.ctx.game != "Spyro 2":
        logger.warning("This command can only be used when playing Spyro 2: Ripto's Rage.")
        return
    return
    # TODO: Support this
    logger.info(f"----------------------------------------------\n"
                f"Commands for Spyro 2\n"
                f"----------------------------------------------\n"
                f"  /ae_commands\n"
                f"      Description: Show this list\n"
                f"  /bh_itemdisplay [On/Off]\n"
                f"      Description: Display items directly in the Bizhawk client\n"
                f"      [Optional] Status (On/Off): Toggle or Enable/Disable the option\n"
                f"  /prevent_kickout [On/Off]\n"
                f"      Description: If on, prevents Spike from being ejected \n"
                f"                    after catching all monkeys in a level\n"
                f"      [Optional] Status (On/Off): Toggle or Enable/Disable the option\n"
                f"  /deathlink [On/Off]\n"
                f"      Description: Enable/Disable the deathlink option\n"
                f"      [Optional] Status (On/Off): Toggle or Enable/Disable the option\n"
                f"  /auto_equip [On/Off]\n"
                f"      Description: When on, will equip gadgets if there is a free face button\n"
                f"      [Optional] Status (On/Off): Toggle or Enable/Disable the option\n"
                f"  /syncprogress \n"
                f"      Description: Fetch the server's state of monkeys and sync it into the game\n"
                f"      [Optional] \"cancel\": If prompted, cancel the currently pending sync\n"
                f"  /spikecolor \n"
                f"      Description: Display/Change Spike's color palette according to presets\n"
                f"      or RGB Hex values (\"000000\" to \"FFFFFF\")\n"
                f"      Presets: {presetColors}\n"
                f"  \n")

def cmd_deathlink(self: "BizHawkClientCommandProcessor", status = "") -> None:
    """Toggle Deathlink on and off"""
    from worlds._bizhawk.context import BizHawkClientContext
    if self.ctx.game != "Spyro 2":
        logger.warning("This command can only be used when playing Spyro 2: Ripto's Rage.")
        return
    if not self.ctx.server or not self.ctx.slot:
        logger.warning("You must be connected to a server to use this command.")
        return

    ctx = self.ctx
    assert isinstance(ctx, BizHawkClientContext)
    client = ctx.client_handler
    assert isinstance(client, Spyro2Client)
    if status == "":
        if client.deathlink == 0:
            msg = "ON"
        else:
            msg = "OFF"
        logger.info(f"Deathlink: {msg}\n"
                    f"    To change the status, use the command like so: /deathlink [on/off]")
        return
    elif status.lower() == "on":
        client.deathlink = 1
    elif status.lower() == "off":
        client.deathlink = 0
    else:
        logger.info(f"Invalid argument for function ""deathlink""\n")
        return

    client.changeDeathlink = True
    if client.deathlink == 1:
        Utils.async_start(ctx.update_death_link(True))
        msg = "ON"
    else:
        Utils.async_start(ctx.update_death_link(False))
        msg = "OFF"
    client.DeathLink_DS = client.deathlink

    logger.info(f"Deathlink is now {msg}\n")


class Spyro2Client(BizHawkClient):
    game = "Spyro 2"
    system = "PSX"
    patch_suffix = ".apspyro2"

    apworld_manifest = orjson.loads(pkgutil.get_data(__name__, "archipelago.json").decode("utf-8"))
    client_version = apworld_manifest["world_version"]
    supported_versions = ["2.0.0", "2.0.0-rc"]

    local_checked_locations: Set[int]
    local_set_events: Dict[str, bool]
    local_found_key_items: Dict[str, bool]
    goal_flag: int

    boolsyncprogress = False
    syncWaitConfirm = False
    changeDeathlink = False
    DeathLink_DS = -1
    deathlink = -1
    resetClient = False
    gotDatastorage = False

    def __init__(self) -> None:
        super().__init__()
        self.local_checked_locations = set()
        self.local_set_events = {}
        self.local_found_key_items = {}
        self.riptoDefeated = False
        self.hasDoubleJumpItem = False
        self.hasFireballItem = False

    def initialize_client(self):
        self.messagequeue = []
        # TODO: Make Spyro values
        self.boolsyncprogress = False
        self.syncWaitConfirm = False
        self.changeDeathlink = False
        self.killPlayer = True
        self.death_counter = None
        self.previous_death_link = 0
        self.pending_death_link: bool = False
        self.locations_list = {}
        # default to true, as we don't want to send a deathlink until playing
        self.sending_death_link: bool = True
        self.ignore_next_death_link = False
        self.specialitem_queue = []
        self.priority_trap_queue = []
        self.gotDatastorage = False
        self.initDatastorage = False
        self.cosmeticQueue = []
        self.lastCosmeticUpdate = 0
        self.moneybagsUnlocks = set()
        self.riptoDefeated = False
        self.hasDoubleJumpItem = False
        self.hasFireballItem = False

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        s2_identifier_ram_address: int = 0x9244
        # SCUS_944.25 in ASCII = Spyro 2
        bytes_expected: bytes = bytes.fromhex("534355535F393434")
        # TODO: Fix this.
        #Commands_List = list(Commands_Dict.keys())
        Commands_List = list()
        try:
            bytes_actual: bytes = (await bizhawk.read(ctx.bizhawk_ctx, [(
                s2_identifier_ram_address, len(bytes_expected), "MainRAM"
            )]))[0]
            if bytes_actual != bytes_expected:
                # Remove commands from client from list in Strings.py
                for command in Commands_List:
                    if command in ctx.command_processor.commands:
                        ctx.command_processor.commands.pop(command)
                return False
        except Exception:
            # Remove commands from client from list in Strings.py
            for command in Commands_List:
                if command in ctx.command_processor.commands:
                    ctx.command_processor.commands.pop(command)
            return False

        if not self.game == "Spyro 2":
            # Remove commands from client from list in Strings.py
            for command in Commands_List:
                if command in ctx.command_processor.commands:
                    ctx.command_processor.commands.pop(command)
            return False
        ctx.game = self.game
        ctx.items_handling = 0b111
        ctx.want_slot_data = True
        ctx.watcher_timeout = 0.125
        # Add custom commands to client from list in Strings.py
        # TODO: Do this.
        #for command in Commands_List:
        #    if command not in ctx.command_processor.commands:
        #        functionName = Commands_Dict[command]
        #        linkedfunction = globals()[functionName]
        #        ctx.command_processor.commands[command] = linkedfunction
        self.initialize_client()
        return True

    def on_package(self, ctx: "BizHawkClientContext", cmd: str, args: Dict[str, Any]) -> None:
        if cmd == "Connected":
            host_version = "Unknown"
            if "apworldVersion" in ctx.slot_data:
                host_version = ctx.slot_data["apworldVersion"]
            if host_version in self.supported_versions:
                compatibility = "These versions are compatible"
            else:
                compatibility = "These versions may not be compatible"

            logger.info(f"================================================\n"
                        f"    -- Connected to Bizhawk successfully! --    \n"
                        f"      Archipelago Spyro 2 version {self.client_version}      \n"
                        f"      Host Spyro 2 version {host_version}                    \n"
                        f"      {compatibility}      \n"
                        #f"================================================\n"
                        #f"Custom commands are available for this game.    \n"
                        #f"Type /ae_commands for the full list.            \n"
                        f"================================================\n")
            self.initialize_client()
        if cmd == "Bounced":
            if "tags" in args:
                assert ctx.slot is not None
                if "DeathLink" in args["tags"] and args["data"]["source"] != ctx.slot_info[ctx.slot].name:
                    self.on_deathlink(ctx)

        if cmd in {"PrintJSON"} and "type" in args:
            # When a message is received
            if args["type"] == "ItemSend":
                item = args["item"]
                networkItem = NetworkItem(*item)
                recieverID = args["receiving"]
                senderID = networkItem.player
                locationID = networkItem.location
                relevant = (recieverID == ctx.slot or senderID == ctx.slot)
                message = ""
                itemName = ctx.item_names.lookup_in_slot(networkItem.item, recieverID)
                itemCategory = networkItem.flags
                if relevant:
                    if itemCategory == ItemClassification.progression + ItemClassification.useful:
                        itemClass = "Prog. Useful"
                    elif itemCategory == ItemClassification.progression + ItemClassification.trap:
                        itemClass = "Prog. Trap"
                    elif itemCategory == ItemClassification.useful + ItemClassification.trap:
                        itemClass = "Useful Trap"
                    elif itemCategory == ItemClassification.progression:
                        itemClass = "Progression"
                    elif itemCategory == ItemClassification.useful:
                        itemClass = "Useful"
                    elif itemCategory == ItemClassification.trap:
                        itemClass = "Trap"
                    elif itemCategory == ItemClassification.filler:
                        itemClass = "Filler"
                    else:
                        itemClass = "Other"

                    recieverName = ctx.player_names[recieverID]
                    senderName = ctx.player_names[senderID]

                    if recieverID != ctx.slot and senderID == ctx.slot:
                        message = f"Sent '{itemName}' ({itemClass}) to {recieverName}"
                    elif recieverID == ctx.slot and senderID != ctx.slot:
                        message = f"Received '{itemName}' ({itemClass}) from {senderName}"
                    elif recieverID == ctx.slot and senderID == ctx.slot:
                        message =  f"You found your own '{itemName}' ({itemClass})"

                    self.messagequeue.append(message)
        if cmd == "Retrieved":
            if "keys" not in args:
                print(f"invalid Retrieved packet to Spyro2Client: {args}")
                return
            keys = dict(args["keys"])
            if f"S2_deathlink_{ctx.team}_{ctx.slot}" in args["keys"]:
                self.DeathLink_DS = keys.get(f"S2_deathlink_{ctx.team}_{ctx.slot}", None)
                self.gotDatastorage = True
            #if f"AE_DIButton_{ctx.team}_{ctx.slot}" in args["keys"]:
            #    self.DIButton = keys.get(f"AE_DIButton_{ctx.team}_{ctx.slot}", None)
            #    self.gotDatastorage = True

    async def set_auth(self, ctx: "BizHawkClientContext") -> None:
        # TODO: ?
        x = 3

    async def ds_options_handling(self, ctx: "BizHawkClientContext", context):
        if context == "init":
            if ctx.team is None:
                self.initDatastorage = False
                return
            keys = [f"S2_{Option}_{ctx.team}_{ctx.slot}" for Option in ["deathlink"]]
            await ctx.send_msgs([{"cmd": "Get", "keys": keys}])

            if not self.gotDatastorage:
                return

            self.initDatastorage = True

            # Deathlink
            if self.DeathLink_DS is None:
                # Used slotdata
                self.deathlink = int(ctx.slot_data["options"]["death_link"])
            else:
                # Got valid Datastorage, take this instead of slot_data
                self.deathlink = self.DeathLink_DS

            loggermessage = "\n--Options Status--\n"
            loggermessage += f"DeathLink: {"ON" if self.deathlink == 1 else "OFF"}\n"
            logger.info(loggermessage)
        elif context == "change":
            if self.changeDeathlink:
                await ctx.send_msgs(
                    [
                        {
                            "cmd": "Set",
                            "key": f"S2_deathlink_{ctx.team}_{ctx.slot}",
                            "default": 0,
                            "want_reply": False,
                            "operations": [{"operation": "replace", "value": self.deathlink}],
                        }
                    ]
                )
                msg = f"Deathlink {"Enabled" if self.deathlink == 1 else "Disabled"}"
                await self.send_bizhawk_message(ctx, msg, "Passthrough", "")
                self.changeDeathlink = False

    async def syncprogress(self, ctx: "BizHawkClientContext") -> None:
        if self.boolsyncprogress:
            self.boolsyncprogress = False

    async def process_bizhawk_messages(self, ctx: "BizHawkClientContext") -> None:
        for message in self.messagequeue:
            await self.send_bizhawk_message(ctx, message, "Custom", "")
            self.messagequeue.pop(0)

    async def send_bizhawk_message(self, ctx: "BizHawkClientContext", message, msgtype, data) -> None:
        if msgtype == "Custom":
            strMessage = message
            await bizhawk.display_message(ctx.bizhawk_ctx, strMessage)
        elif msgtype == "Passthrough":
            strMessage = message
            await bizhawk.display_message(ctx.bizhawk_ctx, strMessage)

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        # Detects if the AP connection is made.
        # If not, "return" immediately to not send anything while not connected
        if ctx.server is None or ctx.server.socket.closed or ctx.slot_data is None or ctx.auth is None:
            self.initClient = False
            return
        # Detection for triggering "initialize_client()" when Disconnecting/Reconnecting to AP (only once per connection)
        if self.initClient is False:
            self.initClient = True
            self.initialize_client()
            await self.ds_options_handling(ctx,"init")

            strMessage = "Connected to Bizhawk Client - Spyro 2 Archipelago v" + str(self.client_version)
            await self.send_bizhawk_message(ctx, strMessage, "Passthrough", "")
        try:
            if self.gotDatastorage:
                # Last init to write the status
                if not self.initDatastorage:
                    await self.ds_options_handling(ctx, "init")

                if  self.changeDeathlink:
                    await self.ds_options_handling(ctx, "change")
                if self.boolsyncprogress:
                    await self.syncprogress(ctx)
            else:
                # Not send anything before having the options set
                await self.ds_options_handling(ctx, "init")
                return

            # Set locations list to use within functions
            self.locations_list = ctx.checked_locations

            # Game state, locations and items read
            readsDict = {
                "recv_index": (RAM.lastReceivedArchipelagoID, 4, "MainRAM"),
                "gameStatus": (RAM.GameStatus, 1, "MainRAM"),
                "talismanCount": (RAM.TotalTalismanAddress, 1, "MainRAM"),
                "orbCount": (RAM.TotalOrbAddress, 1, "MainRAM"),
                "talismanBitArray": (RAM.TalismanStartAddress, 29, "MainRAM"),
                "orbBitArray": (RAM.OrbStartAddress, 29, "MainRAM"),
                "currentLevel": (RAM.CurrentLevelAddress, 1, "MainRAM"),
                "demoMode": (RAM.IsInDemoMode, 1, "MainRAM"),
                "guidebookText": (RAM.GuidebookText, 9, "MainRAM"),
                "resetCheck": (RAM.ResetCheckAddress, 4, "MainRAM"),
                "moneybagsFlags": (RAM.MoneybagsUnlocks, 0x4c, "MainRAM"),
                "skillPointFlags": (RAM.SkillPointAddresses, 0x11, "MainRAM"),
                "spiritParticles": (RAM.SpiritParticlesAddress, 1, "MainRAM"),
                "shoresTokens": (RAM.TokenAddress, 40, "MainRAM"),
                "totalGems": (RAM.TotalGemAddress, 4, "MainRAM"),
                "currentGems": (RAM.LevelGemsAddress, 29 * 4, "MainRAM"),
                "collectiblesMask": (RAM.GemMaskAddress, 0x0006b000 - 0x0006ac84, "MainRAM"),
                "lifeCount": (RAM.PlayerLives, 2, "MainRAM"),
                "sparxHealth": (RAM.PlayerHealth, 1, "MainRAM"),
                "localGemIncrement": (RAM.localGemIncrementAddress, 4, "MainRAM"),
                "globalGemIncrement": (RAM.globalGemIncrementAddress, 4, "MainRAM"),
                "globalGemRespawnFix": (RAM.globalGemRespawnFixAddress, 4, "MainRAM"),
                "localGemRespawnFix": (RAM.localGemRespawnFixAddress, 4, "MainRAM"),
                "playBeep": (RAM.playBeepAddress, 4, "MainRAM"),
                "doubleJumpLine1": (RAM.DoubleJumpAddress1, 4, "MainRAM"),
                "doubleJumpLine2": (RAM.DoubleJumpAddress2, 4, "MainRAM"),
                "permanentFireball": (RAM.PermanentFireballAddress, 1, "MainRAM"),
                "colossusHockeyScore": (RAM.ColossusSpyroHockeyScore, 1, "MainRAM"),
                "idolFishThrowUp": (RAM.IdolFishThrowUp, 4, "MainRAM"),
                "idolFishIncludeReds": (RAM.IdolFishIncludeReds, 4, "MainRAM"),
                "idolFishIncludeRedsHUD": (RAM.IdolFishIncludeRedsHUD, 4, "MainRAM"),
            }

            readTuples = [Value for Value in readsDict.values()]

            reads = await bizhawk.read(ctx.bizhawk_ctx, readTuples)
            reads = [int.from_bytes(reads[i], byteorder = "little") for i,x in enumerate(reads)]
            readValues = dict(zip(readsDict.keys(), reads))

            recv_index = readValues["recv_index"]
            gameStatus = readValues["gameStatus"]
            talismanCount = readValues["talismanCount"]
            orbCount = readValues["orbCount"]
            talismanBitArray = readValues["talismanBitArray"]
            orbBitArray = readValues["orbBitArray"]
            currentLevel = readValues["currentLevel"]
            demoMode = readValues["demoMode"]
            try:
                guidebookText = readValues["guidebookText"].to_bytes(9, byteorder = "little").decode("ascii")
            except Exception:
                guidebookText = ""
            resetCheck = readValues["resetCheck"]
            moneybagsFlags = readValues["moneybagsFlags"]
            skillPointFlags = readValues["skillPointFlags"]
            spiritParticles = readValues["spiritParticles"]
            shoresTokens = readValues["shoresTokens"]
            totalGems = readValues["totalGems"]
            currentGems = readValues["currentGems"]
            collectiblesMask = readValues["collectiblesMask"]
            lifeCount = readValues["lifeCount"]
            sparxHealth = readValues["sparxHealth"]
            localGemIncrement = readValues["localGemIncrement"]
            globalGemIncrement = readValues["globalGemIncrement"]
            globalGemRespawnFix = readValues["globalGemRespawnFix"]
            localGemRespawnFix = readValues["localGemRespawnFix"]
            playBeep = readValues["playBeep"]
            doubleJumpLine1 = readValues["doubleJumpLine1"]
            doubleJumpLine2 = readValues["doubleJumpLine2"]
            permanentFireball = readValues["permanentFireball"]
            colossusHockeyScore = readValues["colossusHockeyScore"]
            idolFishThrowUp = readValues["idolFishThrowUp"]
            idolFishIncludeReds = readValues["idolFishIncludeReds"]
            idolFishIncludeRedsHUD = readValues["idolFishIncludeRedsHUD"]

            # Write tables
            itemsWrites = []

            # Set Initial received_ID
            # TODO: I don't think this works for Spyro.
            if (recv_index == 0xFFFFFFFF) or (recv_index == 0x00FF00FF):
                recv_index = 0

            START_recv_index = recv_index

            # Prevent sending items when connecting early (Sony, Menu or Intro Cutscene)
            firstBootStates = {GameStatus.TitleScreen, GameStatus.Loading}
            boolIsFirstBoot = guidebookText != "Guidebook" or demoMode == 1 or gameStatus in firstBootStates or resetCheck == 0
            if recv_index <= (len(ctx.items_received)) and not boolIsFirstBoot:
                increment = 0
                orbCountFromServer = 0
                sfTalismansFromServer = 0
                apTalismansFromServer = 0
                skillPointsFromServer = 0
                shoresTokensFromServer = 0
                newLives = 0
                gemsanityItems = {}
                currentHealth = sparxHealth
                for item in ctx.items_received:
                    # Increment to already received address first before sending
                    itemName = ctx.item_names.lookup_in_slot(item.item, ctx.slot)
                    if itemName == "Orb":
                        orbCountFromServer += 1
                    elif itemName == "Summer Forest Talisman":
                        sfTalismansFromServer += 1
                    elif itemName == "Autumn Plains Talisman":
                        apTalismansFromServer += 1
                    elif itemName == "Ripto Defeated":
                        self.riptoDefeated = True
                    elif itemName == "Skill Point":
                        skillPointsFromServer += 1
                    elif itemName == "Dragon Shores Token":
                        shoresTokensFromServer += 1
                    elif itemName.endswith("Gem") or itemName.endswith("Gems"):
                        if itemName in gemsanityItems:
                            gemsanityItems[itemName] += 1
                        else:
                            gemsanityItems[itemName] = 1
                    elif itemName.startswith("Moneybags Unlock"):
                        if ctx.slot_data["options"]["moneybags_settings"] == MoneybagsOptions.MONEYBAGSSANITY or \
                            ctx.slot_data["options"]["start_with_abilities"] and \
                            (
                                itemName.endswith("Swim") or itemName.endswith("Climb") or itemName.endswith("Headbash")
                            ):
                            #if itemName not in self.moneybagsUnlocks:
                            #    logger.info("If you are in the same zone as Moneybags, you can talk to him to complete the unlock for free.")
                            self.moneybagsUnlocks.add(itemName)
                    elif itemName == "Double Jump Ability":
                        self.hasDoubleJumpItem = True
                    elif itemName == "Permanent Fireball Ability":
                        self.hasFireballItem = True
                    if increment < START_recv_index:
                        increment += 1
                    else:
                        if itemName == "Extra Life":
                            newLives += 1
                        elif itemName == "Damage Sparx Trap":
                            if 0 < currentHealth < 128:
                                currentHealth -= 1
                        elif itemName == "Sparxless Trap":
                            if 0 < currentHealth < 128:
                                currentHealth = 0
                        elif itemName == "Heal Sparx":
                            # TODO: Use Progressive Sparx Health items
                            if 0 <= currentHealth < 3:
                                currentHealth += 1
                        elif itemName in ["Big Head Mode", "Flat Spyro Mode", "Turn Spyro Red", "Turn Spyro Blue", "Turn Spyro Pink", "Turn Spyro Yellow", "Turn Spyro Green", "Turn Spyro Black", "Normal Spyro"]:
                            self.cosmeticQueue.append(itemName)
                        recv_index += 1

                # Writes to memory if there is a new item, after the loop
                # If the increment is different from recv_index this means we received items
                if increment != recv_index:
                    itemsWrites += [(RAM.lastReceivedArchipelagoID, recv_index.to_bytes(4, "little"), "MainRAM")]
                    itemsWrites += [(RAM.tempLastReceivedArchipelagoID, recv_index.to_bytes(4, "little"), "MainRAM")]
                if orbCountFromServer != orbCount:
                    itemsWrites += [(RAM.TotalOrbAddress, orbCountFromServer.to_bytes(1, "little"), "MainRAM")]
                if currentLevel != LevelInGameIDs.SummerForest and talismanCount != sfTalismansFromServer + apTalismansFromServer:
                    itemsWrites += [(RAM.TotalTalismanAddress, (sfTalismansFromServer + apTalismansFromServer).to_bytes(1, "little"), "MainRAM")]
                elif currentLevel == LevelInGameIDs.SummerForest and talismanCount != sfTalismansFromServer:
                    itemsWrites += [(RAM.TotalTalismanAddress, sfTalismansFromServer.to_bytes(1, "little"), "MainRAM")]
                if newLives != 0:
                    itemsWrites += [(RAM.PlayerLives, min(99, lifeCount + newLives).to_bytes(2, "little"), "MainRAM")]
                # TODO: Ideally, delay 3 seconds.
                if sparxHealth != currentHealth:
                    itemsWrites += [(RAM.PlayerHealth, currentHealth.to_bytes(1, "little"), "MainRAM")]

                if ctx.slot_data["options"]["enable_gemsanity"]:
                    itemsWrites += self.calculateCurrentGems(gemsanityItems, currentGems, totalGems)

                cosmeticTimestamp = time.time()
                if len(self.cosmeticQueue) > 0 and cosmeticTimestamp > self.lastCosmeticUpdate + 5:
                    self.lastCosmeticUpdate = cosmeticTimestamp
                    cosmeticChange = self.cosmeticQueue.pop(0)
                    cosmeticWrites = self.processCosmeticChange(cosmeticChange)
                    if len(cosmeticWrites) > 0:
                        itemsWrites += cosmeticWrites

                # Check for victory conditions
                currentgoal = ctx.slot_data["options"]["goal"]
                if not ctx.finished_game:
                    has_goaled = False
                    if currentgoal == GoalOptions.RIPTO and orbCountFromServer >= ctx.slot_data["options"]["ripto_door_orbs"] and self.riptoDefeated:
                        has_goaled = True
                    elif currentgoal == GoalOptions.SIXTY_FOUR_ORB and orbCountFromServer >= 64 and self.riptoDefeated:
                        has_goaled = True
                    elif currentgoal == GoalOptions.HUNDRED_PERCENT and orbCountFromServer >= 64 and \
                            (ctx.slot_data["options"]["enable_open_world"] or sfTalismansFromServer + apTalismansFromServer >= 14) and \
                            totalGems >= 10000 and self.riptoDefeated:
                        has_goaled = True
                    elif currentgoal == GoalOptions.ALL_SKILLPOINTS and skillPointsFromServer >= 16:
                        has_goaled = True
                    elif currentgoal == GoalOptions.EPILOGUE and skillPointsFromServer >= 16 and self.riptoDefeated:
                        has_goaled = True
                    elif currentgoal == GoalOptions.TEN_TOKENS and shoresTokensFromServer >= 10 and orbCountFromServer >= 55 and totalGems >= 8000:
                        has_goaled = True
                    if has_goaled:
                        await ctx.send_msgs([{
                            "cmd": "StatusUpdate",
                            "status": ClientStatus.CLIENT_GOAL
                        }])
                        await self.send_bizhawk_message(ctx, "You have completed your goal", "Passthrough", "")
                        ctx.finished_game = True

            if len(itemsWrites) > 0:
                await bizhawk.write(ctx.bizhawk_ctx, itemsWrites)

            # ======== Locations handling =========
            if not boolIsFirstBoot:
                Locations_Reads = [
                    currentLevel,
                    talismanBitArray,
                    orbBitArray,
                    moneybagsFlags,
                    skillPointFlags,
                    spiritParticles,
                    shoresTokens,
                    totalGems,
                    currentGems,
                    collectiblesMask
                ]
                await self.locations_handling(ctx, Locations_Reads)

            if not boolIsFirstBoot and gameStatus not in [GameStatus.Paused, GameStatus.LoadingWorld]:
                # ======== Gemsanity Code Handling ========
                if ctx.slot_data["options"]["enable_gemsanity"]:
                    gemsanity_reads = [localGemIncrement, globalGemIncrement, globalGemRespawnFix, localGemRespawnFix, playBeep]
                    gemsanityWrites = self.handleGemsanity(gemsanity_reads)
                    if len(gemsanityWrites) > 0:
                        await bizhawk.write(ctx.bizhawk_ctx, gemsanityWrites)

                # ======== Moneybags Unlock Handling ========
                moneybagsWrites = self.handleMoneybags(ctx, self.moneybagsUnlocks, moneybagsFlags)
                if len(moneybagsWrites) > 0:
                    await bizhawk.write(ctx.bizhawk_ctx, moneybagsWrites)

                # ======== Ability Handling ========
                abilityReads = [doubleJumpLine1, doubleJumpLine2, permanentFireball]
                abilityWrites = self.handleAbilities(ctx, abilityReads)
                if len(abilityWrites) > 0:
                    await bizhawk.write(ctx.bizhawk_ctx, abilityWrites)

                # ======== Easy Challenge Handling ========
                easyChallengeReads = [
                    currentLevel,
                    colossusHockeyScore,
                    idolFishThrowUp,
                    idolFishIncludeReds,
                    idolFishIncludeRedsHUD
                ]
                easyChallengeWrites = self.handleEasyChallenge(ctx, easyChallengeReads)
                if len(easyChallengeWrites) > 0:
                    await bizhawk.write(ctx.bizhawk_ctx, easyChallengeWrites)

            # If there is messages waiting in the queue, print them to Bizhawk
            if self.messagequeue is not None and self.messagequeue != []:
                await self.process_bizhawk_messages(ctx)
            return

            # ======== Handle Death Link =========
            DL_Reads = [cookies, gameRunning, gameState, menuState2, spikeState2]
            await self.handle_death_link(ctx, DL_Reads)

            # ======== Update tags (DeathLink) =========
            await self.update_tags(ctx)

        except bizhawk.RequestFailedError:
            # Exit handler and return to main loop to reconnect
            pass

    async def locations_handling(self, ctx: "BizHawkClientContext", Locations_Reads) -> None:
        current_level = Locations_Reads[0]
        talisman_bit_array = Locations_Reads[1].to_bytes(29, "little")
        orb_bit_array = Locations_Reads[2].to_bytes(29, "little")
        moneybags_flags = Locations_Reads[3].to_bytes(0x4c, "little")
        skill_point_flags = Locations_Reads[4].to_bytes(0x11, "little")
        spirit_particles = Locations_Reads[5]
        shores_tokens = Locations_Reads[6].to_bytes(40, "little")
        total_gems = Locations_Reads[7]
        current_gems = Locations_Reads[8].to_bytes(29 * 4, "little")
        collectibles_mask = Locations_Reads[9].to_bytes(0x0006b000 - 0x0006ac84, "little")

        gemsanity_ids = ctx.slot_data["gemsanity_ids"]

        talismansToSend = set()
        orbsToSend = set()
        bossesToSend = set()
        moneybagsUnlocksToSend = set()
        skillPointUnlocksToSend = set()
        spiritParticlesToSend = set()
        tokensToSend = set()
        totalGemsToSend = set()
        levelGemsToSend = set()
        bottlesToSend = set()
        gemsToSend = set()

        base_id = 1230000
        level_offset = 1000
        level_index = 0
        levels = GetLevelData()
        for level in levels:
            location_offset = 0
            if level.HasTalisman:
                id = base_id + level_offset * level.LevelId + location_offset
                if talisman_bit_array[level_index] != 0 and id not in self.locations_list:
                    talismansToSend.add(id)
                location_offset += 1
            for i in range(level.OrbCount):
                id = base_id + level_offset * level.LevelId + location_offset
                orb_bit = pow(2, i)
                if orb_bit_array[level_index] & orb_bit != 0 and id not in self.locations_list:
                    orbsToSend.add(id)
                location_offset += 1
            if level.IsBoss:
                id = base_id + level_offset * level.LevelId + location_offset
                if talisman_bit_array[level_index] != 0 and id not in self.locations_list:
                    bossesToSend.add(id)
                location_offset += 1
            for i in range(len(level.MoneybagsAddresses)):
                id = base_id + level_offset * level.LevelId + location_offset
                if ctx.slot_data["options"]["moneybags_settings"] != MoneybagsOptions.MONEYBAGSSANITY:
                    # First 2 bytes are price.
                    if moneybags_flags[level.MoneybagsAddresses[i] + 2] != 0 and id not in self.locations_list:
                        moneybagsUnlocksToSend.add(id)
                location_offset += 1
            for i in range(len(level.SkillPointAddresses)):
                id = base_id + level_offset * level.LevelId + location_offset
                if ctx.slot_data["options"]["enable_skillpoint_checks"]:
                    if skill_point_flags[level.SkillPointAddresses[i]] != 0 and id not in self.locations_list:
                        skillPointUnlocksToSend.add(id)
                location_offset += 1
                id = base_id + level_offset * level.LevelId + location_offset
                if ctx.slot_data["options"]["goal"] in [GoalOptions.ALL_SKILLPOINTS, GoalOptions.EPILOGUE]:
                    if skill_point_flags[level.SkillPointAddresses[i]] != 0 and id not in self.locations_list:
                        skillPointUnlocksToSend.add(id)
                location_offset += 1
            for i in range(len(level.LifeBottleAddresses)):
                id = base_id + level_offset * level.LevelId + location_offset
                if ctx.slot_data["options"]["enable_life_bottle_checks"]:
                    bottle_bit = pow(2, level.LifeBottleAddresses[i][1])
                    if collectibles_mask[level.LifeBottleAddresses[i][0]] & bottle_bit != 0 and id not in self.locations_list:
                        bottlesToSend.add(id)
                location_offset += 1
            gem_index = 1
            for i in range(level.TotalGemCount + len(level.GemSkipIndices)):
                if i + 1 not in level.GemSkipIndices:
                    location_id = base_id + level_offset * level.LevelId + location_offset
                    if current_level == level.LevelId:
                        if ctx.slot_data["options"]["enable_gemsanity"] and (len(gemsanity_ids) == 0 or location_id in gemsanity_ids):
                            gem_bit = pow(2, i % 8)
                            if collectibles_mask[level.GemMaskAddress + math.floor(i / 8)] & gem_bit != 0 and location_id not in self.locations_list:
                                gemsToSend.add(location_id)
                    location_offset += 1
                    gem_index += 1
            if level.SpiritParticles > 0:
                id = base_id + level_offset * level.LevelId + location_offset
                if current_level == level.LevelId and ctx.slot_data["options"]["enable_spirit_particle_checks"]:
                    send_check = False
                    if ctx.slot_data["options"]["fracture_easy_earthshapers"] and level.Name == "Fracture Hills":
                        if spirit_particles >= level.SpiritParticles - 7:
                            send_check = True
                    else:
                        if spirit_particles >= level.SpiritParticles:
                            send_check = True
                    if send_check and id not in self.locations_list:
                        spiritParticlesToSend.add(id)
                location_offset += 1
            if level.Name == "Dragon Shores":
                for i in range(10):
                    id = base_id + level_offset * level.LevelId + i
                    if ctx.slot_data["options"]["goal"] == GoalOptions.TEN_TOKENS:
                        if shores_tokens[4 * i] != 0 and id not in self.locations_list:
                            tokensToSend.add(id)
                    location_offset += 1
            level_index += 1

        base_id = 1259000
        for i in range(20):
            id = base_id + i
            if ctx.slot_data["options"]["enable_total_gem_checks"] and \
                    int(ctx.slot_data["options"]["max_total_gem_checks"]) >= 500 * (i + 1):
                if total_gems >= 500 * (i + 1) and id not in self.locations_list:
                    totalGemsToSend.add(id)
        current_gem_address = 0
        offset = 20
        for level in levels:
            if not level.IsBoss:
                if ctx.slot_data["options"]["enable_25_pct_gem_checks"]:
                    id = base_id + offset
                    if int.from_bytes(current_gems[current_gem_address:current_gem_address+3], "little") >= 100 and id not in self.locations_list:
                        levelGemsToSend.add(id)
                offset += 1
                if ctx.slot_data["options"]["enable_50_pct_gem_checks"]:
                    id = base_id + offset
                    if int.from_bytes(current_gems[current_gem_address:current_gem_address+3], "little") >= 200 and id not in self.locations_list:
                        levelGemsToSend.add(id)
                offset += 1
                if ctx.slot_data["options"]["enable_75_pct_gem_checks"]:
                    id = base_id + offset
                    if int.from_bytes(current_gems[current_gem_address:current_gem_address+3], "little") >= 300 and id not in self.locations_list:
                        levelGemsToSend.add(id)
                offset += 1
                if ctx.slot_data["options"]["enable_gem_checks"]:
                    id = base_id + offset
                    if int.from_bytes(current_gems[current_gem_address:current_gem_address+3], "little") >= 400 and id not in self.locations_list:
                        levelGemsToSend.add(id)
                offset += 1
            current_gem_address += 4

        locationsToSend = (talismansToSend | orbsToSend | bossesToSend | moneybagsUnlocksToSend |
                           skillPointUnlocksToSend | spiritParticlesToSend | tokensToSend | totalGemsToSend |
                           levelGemsToSend | bottlesToSend | gemsToSend)
        if locationsToSend != "" and locationsToSend != set():
             await ctx.check_locations(locationsToSend)

    def processCosmeticChange(self, cosmeticChange):
        cosmeticWrites = []
        if cosmeticChange == "Normal Spyro":
            cosmeticWrites += [
                (RAM.SpyroColorAddress, (SpyroColor.SpyroColorDefault).to_bytes(4, "little"), "MainRAM"),
                (RAM.BigHeadMode, (0).to_bytes(2, "little"), "MainRAM")
            ]
        elif cosmeticChange == "Turn Spyro Red":
            cosmeticWrites += [
                (RAM.SpyroColorAddress, (SpyroColor.SpyroColorRed).to_bytes(4, "little"), "MainRAM")
            ]
        elif cosmeticChange == "Turn Spyro Blue":
            cosmeticWrites += [
                (RAM.SpyroColorAddress, (SpyroColor.SpyroColorBlue).to_bytes(4, "little"), "MainRAM")
            ]
        elif cosmeticChange == "Turn Spyro Yellow":
            cosmeticWrites += [
                (RAM.SpyroColorAddress, (SpyroColor.SpyroColorYellow).to_bytes(4, "little"), "MainRAM")
            ]
        elif cosmeticChange == "Turn Spyro Pink":
            cosmeticWrites += [
                (RAM.SpyroColorAddress, (SpyroColor.SpyroColorPink).to_bytes(4, "little"), "MainRAM")
            ]
        elif cosmeticChange == "Turn Spyro Green":
            cosmeticWrites += [
                (RAM.SpyroColorAddress, (SpyroColor.SpyroColorGreen).to_bytes(4, "little"), "MainRAM")
            ]
        elif cosmeticChange == "Turn Spyro Black":
            cosmeticWrites += [
                (RAM.SpyroColorAddress, (SpyroColor.SpyroColorBlack).to_bytes(4, "little"), "MainRAM")
            ]
        elif cosmeticChange == "Big Head Mode":
            cosmeticWrites += [
                (RAM.SpyroHeight, (32).to_bytes(1, "little"), "MainRAM"),
                (RAM.SpyroLength, (32).to_bytes(1, "little"), "MainRAM"),
                (RAM.SpyroWidth, (32).to_bytes(1, "little"), "MainRAM"),
                (RAM.BigHeadMode, (1).to_bytes(2, "little"), "MainRAM")
            ]
        elif cosmeticChange == "Flat Spyro Mode":
            cosmeticWrites += [
                (RAM.SpyroHeight, (16).to_bytes(1, "little"), "MainRAM"),
                (RAM.SpyroLength, (16).to_bytes(1, "little"), "MainRAM"),
                (RAM.SpyroWidth, (2).to_bytes(1, "little"), "MainRAM"),
                (RAM.BigHeadMode, (0x100).to_bytes(2, "little"), "MainRAM")
            ]
        return cosmeticWrites

    def calculateCurrentGems(self, gemsanityItems, currentGems, totalGems):
        gemItems = []
        currentGemsArr = currentGems.to_bytes(29 * 4, "little")
        newTotalGems = 0
        levels = GetLevelData()
        level_index = 0
        for level in levels:
            current_gems = int.from_bytes(currentGemsArr[level_index * 4 : level_index * 4 + 3], "little")
            newCurrentGems = 0
            if "Speedway" in level.Name:
                newTotalGems += current_gems
            else:
                if f"{level.Name} Red Gem" in gemsanityItems.keys():
                    newCurrentGems += 1 * gemsanityItems[f"{level.Name} Red Gem"]
                if f"{level.Name} Green Gem" in gemsanityItems.keys():
                    newCurrentGems += 2 * gemsanityItems[f"{level.Name} Green Gem"]
                if f"{level.Name} Blue Gem" in gemsanityItems.keys():
                    newCurrentGems += 5 * gemsanityItems[f"{level.Name} Blue Gem"]
                if f"{level.Name} Gold Gem" in gemsanityItems.keys():
                    newCurrentGems += 10 * gemsanityItems[f"{level.Name} Gold Gem"]
                if f"{level.Name} Pink Gem" in gemsanityItems.keys():
                    newCurrentGems += 25 * gemsanityItems[f"{level.Name} Pink Gem"]
                if f"{level.Name} 50 Gems" in gemsanityItems.keys():
                    newCurrentGems += 50 * gemsanityItems[f"{level.Name} 50 Gems"]
                if newCurrentGems != current_gems:
                    gemItems += [(RAM.LevelGemsAddress + 4 * level_index, newCurrentGems.to_bytes(4, "little"), "MainRAM")]
                newTotalGems += newCurrentGems
            level_index += 1
        if newTotalGems != totalGems:
            gemItems += [(RAM.TotalGemAddress, newTotalGems.to_bytes(4, "little"), "MainRAM")]
        return gemItems

    def handleGemsanity(self, gemsanity_reads):
        localGemIncrement = gemsanity_reads[0]
        globalGemIncrement = gemsanity_reads[1]
        globalGemRespawnFix = gemsanity_reads[2]
        localGemRespawnFix = gemsanity_reads[3]
        playBeep = gemsanity_reads[4]
        gemsanity_writes = []

        # Disable updating local and global gem counts on collecting a gem, loading into a level, and respawning.
        if localGemIncrement != 0:
            gemsanity_writes += [(RAM.localGemIncrementAddress, (0).to_bytes(4, "little"), "MainRAM")]
        if globalGemIncrement != 0:
            gemsanity_writes += [(RAM.globalGemIncrementAddress, (0).to_bytes(4, "little"), "MainRAM")]
        if globalGemRespawnFix != 0:
            gemsanity_writes += [(RAM.globalGemRespawnFixAddress, (0).to_bytes(4, "little"), "MainRAM")]
        if localGemRespawnFix != 0:
            gemsanity_writes += [(RAM.localGemRespawnFixAddress, (0).to_bytes(4, "little"), "MainRAM")]
        if playBeep != 0:
            gemsanity_writes += [(RAM.playBeepAddress, (0).to_bytes(4, "little"), "MainRAM")]

        return gemsanity_writes

    def handleMoneybags(self, ctx, moneybagsUnlocks, moneybagsFlags):
        moneybags_writes = []
        moneybagsFlagArr = moneybagsFlags.to_bytes(0x4c, "little")
        # Glimmer bridge is always free.
        if int.from_bytes(moneybagsFlagArr[RAM.GlimmerBridgeUnlock : RAM.GlimmerBridgeUnlock + 2], "little") != 0:
            moneybags_writes += [(RAM.MoneybagsUnlocks + RAM.GlimmerBridgeUnlock, (0).to_bytes(2, "little"), "MainRAM")]

        moneybags_dict = {
            "Moneybags Unlock - Crystal Glacier Bridge": RAM.CrystalBridgeUnlock,
            "Moneybags Unlock - Aquaria Towers Submarine": RAM.AquariaSubUnlock,
            "Moneybags Unlock - Magma Cone Elevator": RAM.MagmaElevatorUnlock,
            "Moneybags Unlock - Swim": RAM.SwimUnlock,
            "Moneybags Unlock - Climb": RAM.ClimbUnlock,
            "Moneybags Unlock - Headbash": RAM.HeadbashUnlock,
            "Moneybags Unlock - Wall by Aquaria Towers": RAM.WallToAquariaUnlock, # Name changed in 2.0.0.
            "Moneybags Unlock - Zephyr Portal": RAM.ZephyrPortalUnlock,
            "Moneybags Unlock - Shady Oasis Portal": RAM.ShadyPortalUnlock,
            "Moneybags Unlock - Icy Speedway Portal": RAM.IcyPortalUnlock,
            "Moneybags Unlock - Canyon Speedway Portal": RAM.CanyonPortalUnlock,
        }
        if ctx.slot_data["options"]["moneybags_settings"] == MoneybagsOptions.MONEYBAGSSANITY:
            for unlock in moneybags_dict.keys():
                unlock_address = moneybags_dict[unlock]
                if self.riptoDefeated or unlock in moneybagsUnlocks:
                    if int.from_bytes(moneybagsFlagArr[unlock_address : unlock_address + 4], "little") != 65536:
                        moneybags_writes += [(RAM.MoneybagsUnlocks + unlock_address, (65536).to_bytes(4, "little"), "MainRAM")]
                else:
                    if int.from_bytes(moneybagsFlagArr[unlock_address : unlock_address + 4], "little") != 20001:
                        moneybags_writes += [(RAM.MoneybagsUnlocks + unlock_address, (20001).to_bytes(4, "little"), "MainRAM")]
        elif ctx.slot_data["options"]["moneybags_settings"] == MoneybagsOptions.VANILLA and \
            (
                ctx.slot_data["options"]["enable_gemsanity"] != GemsanityOptions.OFF or
                ctx.slot_data["options"]["level_lock_options"] != LevelLockOptions.VANILLA
            ):
            for unlock in moneybags_dict.keys():
                unlock_address = moneybags_dict[unlock]
                if int.from_bytes(moneybagsFlagArr[unlock_address: unlock_address + 2], "little") != 0:
                    moneybags_writes += [(RAM.MoneybagsUnlocks + unlock_address, (0).to_bytes(2, "little"), "MainRAM")]
        elif ctx.slot_data["options"]["moneybags_settings"] == MoneybagsOptions.VANILLA and \
            ctx.slot_data["options"]["start_with_abilities"]:
            for unlock in moneybags_dict.keys():
                if not (unlock.endswith("Swim") or unlock.endswith("Climb") or unlock.endswith("Headbash")):
                    continue
                unlock_address = moneybags_dict[unlock]
                if int.from_bytes(moneybagsFlagArr[unlock_address: unlock_address + 4], "little") != 65536:
                    moneybags_writes += [(RAM.MoneybagsUnlocks + unlock_address, (65536).to_bytes(4, "little"), "MainRAM")]
        return moneybags_writes

    def handleAbilities(self, ctx, abilityReads):
        doubleJumpLine1 = abilityReads[0]
        doubleJumpLine2 = abilityReads[1]
        permanentFireball = abilityReads[2]
        ability_writes = []
        doubleJumpOption = ctx.slot_data["options"]["double_jump_ability"]
        fireballOption = ctx.slot_data["options"]["permanent_fireball_ability"]

        if doubleJumpOption == AbilityOptions.OFF or doubleJumpOption == AbilityOptions.IN_POOL and not self.hasDoubleJumpItem:
            if doubleJumpLine1 != 0x2402FE00:
                ability_writes += [(RAM.DoubleJumpAddress1, (0x2402FE00).to_bytes(4, "little"), "MainRAM")]
            if doubleJumpLine2 != 0xAC22A08C:
                ability_writes += [(RAM.DoubleJumpAddress2, (0xAC22A08C).to_bytes(4, "little"), "MainRAM")]
        else:
            if doubleJumpLine1 != 0x24020800:
                ability_writes += [(RAM.DoubleJumpAddress1, (0x24020800).to_bytes(4, "little"), "MainRAM")]
            if doubleJumpLine2 != 0xAC22A0A8:
                ability_writes += [(RAM.DoubleJumpAddress2, (0xAC22A0A8).to_bytes(4, "little"), "MainRAM")]

        if fireballOption == AbilityOptions.OFF or fireballOption == AbilityOptions.IN_POOL and not self.hasFireballItem:
            if permanentFireball != 0:
                ability_writes += [(RAM.PermanentFireballAddress, (0).to_bytes(1, "little"), "MainRAM")]
        elif fireballOption == AbilityOptions.START_WITH or fireballOption == AbilityOptions.IN_POOL and self.hasFireballItem:
            if permanentFireball != 1:
                ability_writes += [(RAM.PermanentFireballAddress, (1).to_bytes(1, "little"), "MainRAM")]
        # Else case is vanilla behavior, controlled by the game
        return ability_writes

    def handleEasyChallenge(self, ctx, easyChallengeReads):
        currentLevel = easyChallengeReads[0]
        colossusHockeyScore = easyChallengeReads[1]
        idolFishThrowUp = easyChallengeReads[2]
        idolFishIncludeReds = easyChallengeReads[3]
        idolFishIncludeRedsHUD =easyChallengeReads[4]
        easyChallengeWrites = []
        if currentLevel == LevelInGameIDs.Colossus:
            starting_goals = ctx.slot_data["options"]["colossus_starting_goals"]
            if colossusHockeyScore < starting_goals:
                easyChallengeWrites += [
                    (RAM.ColossusSpyroHockeyScore, starting_goals.to_bytes(1, "little"), "MainRAM"),
                    (RAM.spyroHUDScore, starting_goals.to_bytes(1, "little"), "MainRAM")
                ]
        elif currentLevel == LevelInGameIDs.IdolSprings:
            easy_fish = ctx.slot_data["options"]["idol_easy_fish"]
            if easy_fish:
                if idolFishThrowUp != 0x0802080c:
                    easyChallengeWrites += [(RAM.IdolFishThrowUp, (0x0802080c).to_bytes(4, "little"), "MainRAM")]
                if idolFishIncludeReds != 0x28820006:
                    easyChallengeWrites += [(RAM.IdolFishIncludeReds, (0x28820006).to_bytes(4, "little"), "MainRAM")]
                if idolFishIncludeRedsHUD != 0x28a20006:
                    easyChallengeWrites += [(RAM.IdolFishIncludeRedsHUD, (0x28a20006).to_bytes(4, "little"), "MainRAM")]
        # else if (currentLevel == LevelInGameIDs.Hurricos)
        # {
        #     bool easyLightningOrbs = int.Parse(Client.Options?.GetValueOrDefault("hurricos_easy_lightning_orbs", "0").ToString()) > 0;
        #     if (easyLightningOrbs)
        #     {
        #         foreach (uint thiefStatus in Addresses.HurricosLightningThiefStatuses)
        #         {
        #             Memory.WriteByte(thiefStatus, 253);
        #         }
        #         foreach (uint thiefZCoordinate in Addresses.HurricosLightningThiefZCoordinates)
        #         {
        #             Memory.Write(thiefZCoordinate, 0);
        #         }
        #     }
        # }
        # else if (currentLevel == LevelInGameIDs.BreezeHarbor)
        # {
        #     int requiredGears = int.Parse(Client.Options?.GetValueOrDefault("breeze_required_gears", "0").ToString());
        #     int currentGears = (int)Memory.ReadByte(Addresses.spyroHUDScore);
        #     if (currentGears > 50)
        #     {
        #         Memory.WriteByte(Addresses.spyroHUDScore, 50);
        #     }
        #     else if (currentGears < 50 - requiredGears)
        #     {
        #         Memory.WriteByte(Addresses.spyroHUDScore, (byte)(50 - requiredGears));
        #     }
        # }
        # else if (currentLevel == LevelInGameIDs.Scorch)
        # {
        #     // Nothing ever goes wrong in Scorch : )
        #     BomboOptions bomboSettings = (BomboOptions)int.Parse(Client.Options?.GetValueOrDefault("scorch_bombo_settings", "0").ToString());
        #     if (bomboSettings == BomboOptions.FirstOnly)
        #     {
        #         // Mark the other two bombos as complete, and move their models out of rendering range.
        #         // Otherwise, their models appear on the flagpoles.
        #         // -0x35 is the offset from status to z coordinate
        #         Memory.WriteByte(Addresses.secondBomboStatus, 11);
        #         Memory.Write(Addresses.secondBomboStatus - 0x35, 100000);
        #         Memory.WriteByte(Addresses.thirdBomboStatus, 11);
        #         Memory.Write(Addresses.thirdBomboStatus - 0x35, 100000);
        #     }
        #     else if (bomboSettings == BomboOptions.FirstOnlyNoAttack)
        #     {
        #         Memory.WriteByte(Addresses.secondBomboStatus, 11);
        #         Memory.Write(Addresses.secondBomboStatus - 0x35, 100000);
        #         Memory.WriteByte(Addresses.thirdBomboStatus, 11);
        #         Memory.Write(Addresses.thirdBomboStatus - 0x35, 100000);
        #         Memory.Write(Addresses.bomboAttackAddress, 0x0801E71E);
        #     }
        # }
        # else if (currentLevel == LevelInGameIDs.FractureHills)
        # {
        #     bool requireHeadbash = int.Parse(Client.Options?.GetValueOrDefault("fracture_require_headbash", "0").ToString()) > 0;
        #     bool easyEarthshapers = int.Parse(Client.Options?.GetValueOrDefault("fracture_easy_earthshapers", "0").ToString()) > 0;
        #     if (!requireHeadbash)
        #     {
        #         Memory.Write(Addresses.fractureHeadbashCheck, 0x0801E2A5);
        #     }
        #     if (easyEarthshapers)
        #     {
        #         foreach (uint earthshaperStatus in Addresses.FractureEarthshaperStatuses)
        #         {
        #             Memory.WriteByte(earthshaperStatus, 253);
        #         }
        #         foreach (uint earthshaperZCoordinate in Addresses.FractureEarthshaperZCoordinates)
        #         {
        #             Memory.Write(earthshaperZCoordinate, 0);
        #         }
        #         Memory.WriteByte(Addresses.maxFractureSpiritParticles, 22);
        #     }
        # }
        # else if (currentLevel == LevelInGameIDs.MagmaCone)
        # {
        #     int spyroStartingScore = int.Parse(Client.Options?.GetValueOrDefault("magma_spyro_starting_popcorn", "0").ToString());
        #     int hunterStartingScore = int.Parse(Client.Options?.GetValueOrDefault("magma_hunter_starting_popcorn", "0").ToString());
        #     int spyroScore = Memory.ReadByte(Addresses.spyroHUDScore);
        #     int hunterScore = Memory.ReadByte(Addresses.opponentHUDScore);
        #     if (spyroScore < spyroStartingScore)
        #     {
        #         Memory.WriteByte(Addresses.spyroHUDScore, (byte)spyroStartingScore);
        #     }
        #     if (hunterScore < hunterStartingScore)
        #     {
        #         Memory.WriteByte(Addresses.opponentHUDScore, (byte)hunterStartingScore);
        #     }
        # }
        # else if (currentLevel == LevelInGameIDs.ShadyOasis)
        # {
        #     bool requireHeadbash = int.Parse(Client.Options?.GetValueOrDefault("shady_require_headbash", "0").ToString()) > 0;
        #     if (!requireHeadbash)
        #     {
        #         Memory.Write(Addresses.ShadyHeadbashCheck, 0x00000000);
        #     }
        # }
        # else if (currentLevel == LevelInGameIDs.GulpsOverlook)
        # {
        #     bool easyGulp = int.Parse(Client.Options?.GetValueOrDefault("easy_gulp", "0").ToString()) > 0;
        #     if (easyGulp)
        #     {
        #         Memory.WriteByte(Addresses.GulpDoubleDamage, 1);
        #     }
        # }
        return easyChallengeWrites

    async def update_tags(self, ctx: "BizHawkClientContext") -> None:
        updateTags = False
        if ctx.slot_data["death_link"] or self.deathlink == 1:
            if "DeathLink" not in ctx.tags:
                ctx.tags.add("DeathLink")
                updateTags = True
        else:
            if "DeathLink" in ctx.tags:
                ctx.tags.remove("DeathLink")
                updateTags = True
        if updateTags:
            await ctx.send_msgs([{"cmd": "ConnectUpdate", "tags": ctx.tags}])

    async def handle_death_link(self, ctx: "BizHawkClientContext", DL_Reads) -> None:
        """
        Checks whether the player has died while connected and sends a death link if so.
        """
        # TODO: Handle this
        return
        # C# Code:
        # byte health = Memory.ReadByte(Addresses.PlayerHealth);
        # int zPos = Memory.ReadInt(Addresses.PlayerZPos);
        # int animationLength = Memory.ReadInt(Addresses.PlayerAnimationLength);
        # byte spyroState = Memory.ReadByte(Addresses.SpyroStateAddress);
        # byte spyroVelocityFlag = Memory.ReadByte(Addresses.PlayerVelocityStatus);
        # LevelInGameIDs[] deathLinkLevels = [
        #     LevelInGameIDs.SummerForest,
        # LevelInGameIDs.Glimmer,
        # LevelInGameIDs.Colossus,
        # LevelInGameIDs.IdolSprings,
        # LevelInGameIDs.Hurricos,
        # LevelInGameIDs.SunnyBeach,
        # LevelInGameIDs.AquariaTowers,
        # LevelInGameIDs.CrushsDungeon,
        # LevelInGameIDs.AutumnPlains,
        # LevelInGameIDs.BreezeHarbor,
        # LevelInGameIDs.SkelosBadlands,
        # LevelInGameIDs.CrystalGlacier,
        # LevelInGameIDs.Zephyr,
        # LevelInGameIDs.Scorch,
        # LevelInGameIDs.FractureHills,
        # LevelInGameIDs.MagmaCone,
        # LevelInGameIDs.ShadyOasis,
        # LevelInGameIDs.GulpsOverlook,
        # LevelInGameIDs.WinterTundra,
        # LevelInGameIDs.MysticMarsh,
        # LevelInGameIDs.CloudTemples,
        # LevelInGameIDs.RoboticaFarms,
        # LevelInGameIDs.Metropolis,
        # LevelInGameIDs.RiptosArena
        # ];
        #
        # if (
        #     !_justDied &&
        #     Helpers.IsInGame() &&
        #     Client.ItemState != null &&
        #     Client.CurrentSession != null &&
        #     deathLinkLevels.Contains(currentLevel) &&
        #     gameStatus != GameStatus.Cutscene &&
        #     gameStatus != GameStatus.Loading &&
        #     gameStatus != GameStatus.TitleScreen &&
        #     (
        #         health > 128 ||
        #         (zPos > 0 && zPos < 0x400) ||  // zPos is 0 on initial load into a save
        #         (spyroState == (byte)SpyroStates.Flop && spyroVelocityFlag == 1 && 0x3b < animationLength) ||
        #         spyroState == (byte)SpyroStates.DeathBurn ||
        #         spyroState == (byte)SpyroStates.DeathDrowning && animationLength >= 116 ||
        #         spyroState == (byte)SpyroStates.DeathSquash
        #     )
        # )
        cookies = DL_Reads[0]
        gameRunning = DL_Reads[1]
        gameState = DL_Reads[2]
        menuState2 = DL_Reads[3]
        spikestate2 = DL_Reads[4]

        OnTree = {56, 57, 58, 59, 60}

        DL_writes = []
        DL_writes2 = []
        if self.deathlink == 1:
            if "DeathLink" not in ctx.tags:
                #await ctx.update_death_link(True)
                self.previous_death_link = ctx.last_death_link
            if "DeathLink" in ctx.tags and ctx.last_death_link + 1 < time.time():
                if cookies == 0x00 and not self.sending_death_link and gameState in (RAM.gameState["InLevel"],RAM.gameState["TimeStation"]):
                    await self.send_deathlink(ctx)
                elif cookies != 0x00:
                    self.sending_death_link = False
            # Wait on exiting menu before sending deathlink
            if self.pending_death_link and menuState2 != 1:
                DL_writes += [(RAM.cookieAddress, 0x00.to_bytes(1, "little"), "MainRAM")]
                DL_writes += [(RAM.instakillAddress, 0xFF.to_bytes(1, "little"), "MainRAM")]
                if spikestate2 in OnTree:
                    DL_writes2 += [(RAM.Controls_TriggersShapes, 0xFD.to_bytes(1, "little"), "MainRAM")]
                self.pending_death_link = False
                self.sending_death_link = True
                await bizhawk.write(ctx.bizhawk_ctx, DL_writes)
                await bizhawk.write(ctx.bizhawk_ctx, DL_writes2)
        elif self.deathlink == 0:
            #await ctx.update_death_link(False)
            self.previous_death_link = ctx.last_death_link

    async def send_deathlink(self, ctx: "BizHawkClientContext") -> None:
        self.sending_death_link = True
        ctx.last_death_link = time.time()
        # TODO: Add cause.
        DeathText = ctx.player_names[ctx.slot] + " died in Spyro 2"
        await ctx.send_death(DeathText)

    def on_deathlink(self, ctx: "BizHawkClientContext") -> None:
        ctx.last_death_link = time.time()
        self.pending_death_link = True

# Text helper functions
def text_to_bytes(name):
    bytelist = []
    for x in name:
        bytelist.append(character_lookup(x))
    return bytelist


def character_lookup(byte):
    if byte.isspace():  # Space
        return 255
    if byte.isalpha():
        return ord(byte) - 49  # Both uppercase and lowercase letters
    if byte.isdecimal():
        if int(byte) < 6:
            return ord(byte) + 58  # 0-5
        else:
            return ord(byte) + 68  # 6-9
    if ord(byte) == 39:  # Single apostrophe
        return 187
    if ord(byte) == 46:  # Period
        return 172
    if ord(byte) == 47:  # Slash
        return 141
    if ord(byte) == 58:  # Colon
        return 174