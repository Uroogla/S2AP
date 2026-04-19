import logging
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
#else:
    #BizHawkClientContext = object

from .Addresses import RAM
from .Enums import GameStatus, LevelInGameIDs
from .LevelData import GetLevelData

from .Locations import location_dictionary
from .Items import item_dictionary
from .Options import GoalOptions

logger = logging.getLogger("Client")

def cmd_s2_commands(self: "BizHawkClientCommandProcessor") -> None:
    """Show what commands are available for Spyro 2 Archipelago"""
    from worlds._bizhawk.context import BizHawkClientContext
    if self.ctx.game != "Spyro 2":
        logger.warning("This command can only be used when playing Spyro 2: Ripto's Rage.")
        return
    return
    # TODO: Support this
    #presetColors = list(RAM.colortable.keys())
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

    local_checked_locations: Set[int]
    local_set_events: Dict[str, bool]
    local_found_key_items: Dict[str, bool]
    goal_flag: int

    offset = 0 #128000000
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

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        s2_identifier_ram_address: int = 0x9244
        # SCUS_944.25 in ASCII = Spyro 2
        bytes_expected: bytes = bytes.fromhex("534355535F393434")
        #Commands_List = list(Commands_Dict.keys())
        Commands_List = list()
        try:
            bytes_actual: bytes = (await bizhawk.read(ctx.bizhawk_ctx, [(
                self.offset + s2_identifier_ram_address, len(bytes_expected), "MainRAM"
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
            logger.info(f"================================================\n"
                        f"    -- Connected to Bizhawk successfully! --    \n"
                        f"      Archipelago Spyro 2 version {self.client_version}      \n"
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
                            "key": f"AE_deathlink_{ctx.team}_{ctx.slot}",
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
        if self.initClient == False:
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
                "recv_index": (self.offset + RAM.lastReceivedArchipelagoID, 4, "MainRAM"),
                "gameStatus": (self.offset + RAM.GameStatus, 1, "MainRAM"),
                "talismanCount": (self.offset + RAM.TotalTalismanAddress, 1, "MainRAM"),
                "orbCount": (self.offset + RAM.TotalOrbAddress, 1, "MainRAM"),
                "talismanBitArray": (self.offset + RAM.TalismanStartAddress, 29, "MainRAM"),
                "orbBitArray": (self.offset + RAM.OrbStartAddress, 29, "MainRAM"),
                "currentLevel": (self.offset + RAM.CurrentLevelAddress, 1, "MainRAM"),
                "demoMode": (self.offset + RAM.IsInDemoMode, 1, "MainRAM"),
                "guidebookText": (self.offset + RAM.GuidebookText, 9, "MainRAM"),
                "resetCheck": (self.offset + RAM.ResetCheckAddress, 4, "MainRAM"),
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
            guidebookText = readValues["guidebookText"].to_bytes(9, byteorder = "little").decode("ascii")
            resetCheck = readValues["resetCheck"]


            # Write tables
            itemsWrites = []

            # Set Initial received_ID
            if (recv_index == 0xFFFFFFFF) or (recv_index == 0x00FF00FF):
                recv_index = 0

            START_recv_index = recv_index

            # Prevent sending items when connecting early (Sony, Menu or Intro Cutscene)
            firstBootStates = {GameStatus.TitleScreen, GameStatus.Loading}
            # TODO: This doesn't work, I'd imagine?
            boolIsFirstBoot = guidebookText != "Guidebook" or demoMode == 1 or gameStatus in firstBootStates or resetCheck == 0
            if recv_index <= (len(ctx.items_received)) and not boolIsFirstBoot:
                increment = 0
                orbCountFromServer = 0
                sfTalismansFromServer = 0
                apTalismansFromServer = 0
                for item in ctx.items_received:
                    # Increment to already received address first before sending
                    itemName = ctx.item_names.lookup_in_slot(item.item, ctx.slot)
                    if itemName == "Orb":
                        orbCountFromServer += 1
                    elif itemName == "Summer Forest Talisman":
                        sfTalismansFromServer += 1
                    elif itemName == "Autumn Plains Talisman":
                        apTalismansFromServer += 1
                    if increment < START_recv_index:
                        increment += 1
                    else:
                        recv_index += 1

                    #if ctx.slot_data["goal"] == GoalOption.option_tokenhunt and tokenCountFromServer == min(ctx.slot_data["requiredtokens"], ctx.slot_data["totaltokens"]):
                    #    await ctx.send_msgs([{
                    #        "cmd": "StatusUpdate",
                    #        "status": ClientStatus.CLIENT_GOAL
                    #    }])
                    #    await self.send_bizhawk_message(ctx, "You have completed your goal o[8(|)", "Passthrough", "")
                    #    ctx.finished_game = True

                # Writes to memory if there is a new item, after the loop
                #If the increment is different from recv_index this means we received items
                if increment != recv_index:
                    itemsWrites += [(RAM.lastReceivedArchipelagoID, recv_index.to_bytes(4, "little"), "MainRAM")]
                    itemsWrites += [(RAM.tempLastReceivedArchipelagoID, recv_index.to_bytes(4, "little"), "MainRAM")]
                if orbCountFromServer != orbCount:
                    itemsWrites += [(RAM.TotalOrbAddress, orbCountFromServer.to_bytes(1, "little"), "MainRAM")]
                if currentLevel != LevelInGameIDs.SummerForest and talismanCount != sfTalismansFromServer + apTalismansFromServer:
                    itemsWrites += [(RAM.TotalTalismanAddress, (sfTalismansFromServer + apTalismansFromServer).to_bytes(1, "little"), "MainRAM")]
                elif currentLevel == LevelInGameIDs.SummerForest and talismanCount != sfTalismansFromServer:
                    itemsWrites += [(RAM.TotalTalismanAddress, sfTalismansFromServer.to_bytes(1, "little"), "MainRAM")]

            #await bizhawk.write(ctx.bizhawk_ctx, writes)
            # await bizhawk.guarded_write(ctx.bizhawk_ctx, TR_writes, TR_guards)
            await bizhawk.write(ctx.bizhawk_ctx, itemsWrites)
            return
            # ======== Locations handling =========
            Locations_Reads = [currentLevel,gameState,currentRoom,previousCoinStateRoom,currentCoinStateRoom,gameRunning,TVT_BossPhase,gotMail,mailboxID,jakeVictory,S1_P2_State,S1_P2_Life,S2_isCaptured,levelselect_coinlock_Address,CoinTable,TempCoinTable,monkeylevelcounts,currentApes,transitionPhase]
            await self.locations_handling(ctx, Locations_Reads)


            # Write Array
            # Training Room, set to 0xFF to mark as complete

            # Gadgets unlocked
            # Required apes (to match hundo)
            writes = [
                #(RAM.trainingRoomProgressAddress, 0xFF.to_bytes(1, "little"), "MainRAM"),
                (RAM.unlockedGadgetsAddress, gadgetStateFromServer.to_bytes(2, "little"), "MainRAM"),
                (RAM.requiredApesAddress, localhundoCount.to_bytes(1, "little"), "MainRAM"),
            ]
            GadgetTrainingsUnlock = 0x00000000
            trainingRoomProgress = 0xFF
            # Training Room Unlock state checkup: Set to 0x00000000 to prevent all buttons from working
            varGoal = ctx.slot_data["goal"]
            varFastTokenGoal = ctx.slot_data["fasttokengoal"]
            boolActivateFastGoalWarp = (varFastTokenGoal == FastTokenGoalOption.option_on and varGoal in (GoalOption.option_mmtoken,GoalOption.option_ppmtoken) and tokenCountFromServer >= min(ctx.slot_data["requiredtokens"], ctx.slot_data["totaltokens"]))
            # **Going into the room**
            if (transitionPhase == RAM.transitionPhase["InTransition"] and NearbyRoom == 90):
                # If the FastGoal warp needs to be activated,needs to be done in transition
                if boolActivateFastGoalWarp:
                    GadgetTrainingsUnlock = 0x8C63FDCC
                    trainingRoomProgress = 0x01
                else:
                    GadgetTrainingsUnlock = 0x00000000
                    trainingRoomProgress  = 0xFF
            elif currentRoom == 90:
                # **After the transition or while in room**
                # Check for FastTokenGoal + enough tokens
                if boolActivateFastGoalWarp:
                    GadgetTrainingsUnlock = 0x8C63FDCC
                    trainingRoomProgress = 0x01
                    # Check which door needs to be redirected to
                    if varGoal == GoalOption.option_mmtoken:
                        doorTransition = doorTransitions.get(AEDoor.MM_SPECTER1_ROOM.value)
                        targetRoom = doorTransition[0]
                        targetDoor = doorTransition[1]
                    else:
                        doorTransition = doorTransitions.get(AEDoor.PPM_ENTRY.value)
                        targetRoom = doorTransition[0]
                        targetDoor = doorTransition[1]
                    # Change Transition2 to the desired transitions as needed
                    TR2_Adresses = list(RAM.transitionAddresses.get(2))
                    writes += [(TR2_Adresses[0], targetRoom.to_bytes(1, "little"), "MainRAM")]
                    writes += [(TR2_Adresses[1], targetDoor.to_bytes(1, "little"), "MainRAM")]
                else:
                    # You are in the room, but FastToken is not on OR you do not have enough tokens
                    GadgetTrainingsUnlock = 0x00000000
                    trainingRoomProgress = 0xFF
            else:
                # Not going into the Training Room NOR being into it, set these values to normal
                GadgetTrainingsUnlock = 0x8C63FDCC
                trainingRoomProgress = 0xFF

            InFastTokenWarp = RAM.gameState["TimeStation"] == gameState and boolActivateFastGoalWarp and currentRoom in {83,86,87}
            if InFastTokenWarp:
                writes += [(RAM.gameStateAddress, RAM.gameState["InLevel"].to_bytes(1, "little"), "MainRAM")]
            writes += [(RAM.GadgetTrainingsUnlockAddress, GadgetTrainingsUnlock.to_bytes(4, "little"), "MainRAM")]
            writes += [(RAM.trainingRoomProgressAddress, trainingRoomProgress.to_bytes(1, "little"), "MainRAM")]

            # Flag to mark MM as completed for goal check if needed
            if self.MM_Completed == True and Specter1CompleteAddress == 0:
                Specter1CompleteAddress = 1
                #print(f"Wrote value to Specter2CompleteAddress : 1")
                writes += [(RAM.Specter1CompleteAddress, Specter1CompleteAddress.to_bytes(1, "little"), "MainRAM")]
                writes += [(RAM.tempSpecter1CompleteAddress, Specter1CompleteAddress.to_bytes(1, "little"), "MainRAM")]

            # PPM_Completed flag for "100% Complete" label on PPM level
            if self.PPM_Completed == True and Specter2CompleteAddress == 0:
                Specter2CompleteAddress = 1
                #print(f"Wrote value to Specter2CompleteAddress : 1")
                writes += [(RAM.Specter2CompleteAddress, Specter2CompleteAddress.to_bytes(1, "little"), "MainRAM")]
                writes += [(RAM.tempSpecter2CompleteAddress, Specter2CompleteAddress.to_bytes(1, "little"), "MainRAM")]

            # If there is messages waiting in the queue, print them to Bizhawk
            if self.messagequeue is not None and self.messagequeue != []:
                await self.process_bizhawk_messages(ctx)

            # ======== Handle Death Link =========
            DL_Reads = [cookies, gameRunning, gameState, menuState2, spikeState2]
            await self.handle_death_link(ctx, DL_Reads)

            # ======== Update tags (DeathLink) =========
            await self.update_tags(ctx)

            # ======== Spike Color handling =========
            # For checking if the chosen color currently needs to be applied.
            Color_Reads = [gameState, spikeColor, spikeState2]
            await self.Spike_Color_handling(ctx, Color_Reads, "")
            # ================================

            # ======== Special Items Handling =========
            # For Traps and Special Items.
            currentGadgets = await self.check_gadgets(ctx, gadgetStateFromServer)
            SpecialItems_Reads = [gameState, gotMail, spikeState, spikeState2, menuState, menuState2, currentGadgets, currentRoom, gameRunning, self.DS_spikecolor,heldGadget,CatchingState,cookies]
            await self.specialitems_handling(ctx, SpecialItems_Reads)
            # ================================

            # ======== Monkey Mashing =========
            if self.ape_handler.is_active:
                await self.ape_handler.send_monkey_inputs()
            else:
                if self.ape_handler.sentMessage == False:
                    message = "Monkey Mash Trap finished"
                    await self.send_bizhawk_message(ctx, message, "Passthrough", "")
                    self.ape_handler.sentMessage = True
            # ================================

            # ======== Rainbow Cookie =========
            if self.rainbow_cookie.is_active:
                await self.rainbow_cookie.update_state_and_deactivate()
            else:
                if self.rainbow_cookie.sentMessage == False:
                    message = "Rainbow Cookie finished"
                    await self.send_bizhawk_message(ctx, message, "Passthrough", "")
                    self.rainbow_cookie.sentMessage = True
            # ================================

            # ======== Stun Trap =========
            if self.stun_trap.is_active:
                await self.stun_trap.update_state_and_deactivate(currentRoom)
            else:
                if self.stun_trap.sentMessage == False:
                    message = "Stun Trap finished"
                    await self.send_bizhawk_message(ctx, message, "Passthrough", "")
                    self.stun_trap.sentMessage = True
            # ================================

            # ======== Camera Rotate Trap =========
            if self.camera_rotate_trap.is_active:
                await self.camera_rotate_trap.update_state_and_deactivate(currentRoom)
            else:
                if self.camera_rotate_trap.sentMessage == False:
                    message = "Camera Rotate Trap finished"
                    await self.send_bizhawk_message(ctx, message, "Passthrough", "")
                    self.camera_rotate_trap.sentMessage = True
            # ================================
            # ======= Credits skipping =======
            # Credits skipping function for S1 and S2
            Credits_Reads = [currentRoom, gameState, S1_Cutscene_Redirection, S2_Cutscene_Redirection]
            await self.Credits_handling(ctx, Credits_Reads)
            # ================================

            # ======= PPM Optimizations =======
            # Execute the code segment for PPM fight locking
            PPM_Reads = [currentRoom, currentLevel, gameState,S2_CutsceneState,S2_GlobalCutsceneState]
            await self.PPM_Optimizations(ctx, PPM_Reads)
            # ================================

            # ======= MM Optimizations =======
            # Execute the code segment for MM Double Door and related optimizations
            MM_Reads = [currentRoom, currentLevel, gameState, NearbyRoom, transitionPhase, MM_Jake_Defeated, MM_Lobby_DoubleDoor, MM_Lobby_DoorDetection, MM_Lobby_DoubleDoor_Open, MM_Jake_DefeatedAddress, MM_Natalie_RescuedAddress, MM_Natalie_Rescued, MM_Natalie_Rescued_Local, MM_Professor_Rescued, S1_P1_FightTrigger, MM_Clown_State,MM_AlertRoom_ButtonPressed]
            await self.MM_Optimizations(ctx, MM_Reads)
            # ================================

            # ====== Permanent Buttons =======
            # Execute the Button handling code segment
            Button_Reads = [currentRoom, gameState, DI_Button_Pressed, CrC_Water_ButtonPressed, CrC_Basement_ButtonPressed, TVT_Lobby_ButtonPressed, MM_MonkeyHead_ButtonPressed, MM_Painting_ButtonPressed, DR_Block_Pushed, transitionPhase]
            await self.permanent_buttons_handling(ctx, Button_Reads)
            # ================================

            localLampsUpdate = {20: CBLampState, 53: CPLampState, 79: MMLampState}
            globalLampsUpdate = {26: DILampState, 46: CrCLampState, 57: SFLampState, 65: TVTLobbyLampState, 66: TVTTankLampState}

            # ========= Lamp Unlocks =========
            # Tables for Lamp updates
            # Execute the Lamp unlocking code segment
            Lamps_Reads = [gameState, currentRoom, NearbyRoom, localLampsUpdate, globalLampsUpdate, transitionPhase,WSW_RoomState,lockCamera]
            await self.lamps_unlocks_handling(ctx, Lamps_Reads)
            # ================================

            # ========== Water Net ===========
            # Swim/Dive Prevention code
            WN_Reads = [gameState, waternetState, gameRunning, spikeState2, swim_oxygenLevel, cookies, isUnderwater, watercatchState]
            await self.water_net_handling(ctx, WN_Reads)
            # ================================

            # ====== Monkey count sync ========
            # ** There is a vanilla bug that Monkey count RAM addresses can be wrong sometimes. **
            # For checking if the Monkey count is correct. (Mainly for PPM unlock)
            MonkeyCount_Reads = [currentLevel, gameState, monkeylevelcounts]
            await self.syncMonkeycount(ctx, MonkeyCount_Reads)
            # ================================

            # ====== Gadgets handling ========
            # For checking which gadgets should be equipped
            # Also apply Magic Punch visual correction
            Gadgets_Reads = [currentLevel, currentRoom, heldGadget, gadgetStateFromServer, crossGadget, squareGadget, circleGadget, triangleGadget, menuState, menuState2, punchVisualAddress, gameState, currentGadgets]
            await self.gadgets_handler(ctx, Gadgets_Reads, temp_SA_Completed, temp_GA_Completed)
            # ================================

            # == Level Select Optimization ===
            # Execute the Level Select optimization code segment
            LSO_Reads = [gameState, CoinTable, TempCoinTable, SA_Completed, temp_SA_Completed, GA_Completed, temp_GA_Completed, LS_currentLevel, LS_currentWorld, worldIsScrollingRight,levelselect_coinlock_Address]
            await self.level_select_optimization(ctx, LSO_Reads)
            # ================================


            # Unlock levels
            writes += self.unlockLevels(ctx, monkeylevelcounts, gameState, hundoMonkeysCount, ctx.slot_data["reqkeys"], ctx.slot_data["newpositions"], temp_SA_Completed, temp_GA_Completed, Specter2CompleteAddress)
            # ===== Text Replacements ======
            # Replace text Time Station mailbox here.
            # ==============================
            if self.mailboxTextReplaced == False:
                if currentRoom == 88 and gotMail == 0x02 and mailboxID == 0x71:
                    self.mailboxTextReplaced = True
                    mailboxtext = ""
                    mailboxbytes = []

                    mailboxbytes += text_to_bytes("World settings")
                    mailboxbytes += [13] # New line

                    # Add goal to mailbox text
                    if ctx.slot_data["goal"] == GoalOption.option_mm or ctx.slot_data["goal"] == GoalOption.option_mmtoken:
                        mailboxtext = "Goal: Specter 1"
                    elif ctx.slot_data["goal"] == GoalOption.option_ppm or ctx.slot_data["goal"] == GoalOption.option_ppmtoken:
                        mailboxtext = "Goal: Specter 2"
                    else:
                        mailboxtext = "Goal: Token Hunt"
                    mailboxbytes += text_to_bytes(mailboxtext)
                    mailboxbytes += [13]

                    # Pad the text with zeroes to overwrite all pre-existing text
                    while len(mailboxbytes) < 600:
                        mailboxbytes += [0]

                    for x in range(0, 600):
                        writes += [(RAM.timeStationMailboxStart + x, mailboxbytes[x].to_bytes(1, "little"), "MainRAM")]
            else:
                if not (currentRoom == 88 and gotMail == 0x02 and mailboxID == 0x71):
                    self.mailboxTextReplaced = False

            await bizhawk.write(ctx.bizhawk_ctx, writes)
            #await bizhawk.guarded_write(ctx.bizhawk_ctx, TR_writes, TR_guards)
            await bizhawk.write(ctx.bizhawk_ctx, itemsWrites)

            self.levelglobal = currentLevel

        except bizhawk.RequestFailedError:
            # Exit handler and return to main loop to reconnect
            pass

    async def locations_handling(self, ctx: "BizHawkClientContext", Locations_Reads) -> None:
        pass
        # currentLevel = Locations_Reads[0]
        # gameState = Locations_Reads[1]
        # currentRoom = Locations_Reads[2]
        # previousCoinStateRoom = Locations_Reads[3]
        # currentCoinStateRoom = Locations_Reads[4]
        # gameRunning = Locations_Reads[5]
        # TVT_BossPhase = Locations_Reads[6]
        # gotMail = Locations_Reads[7]
        # mailboxID = Locations_Reads[8]
        # jakeVictory = Locations_Reads[9]
        # S1_P2_State = Locations_Reads[10]
        # S1_P2_Life = Locations_Reads[11]
        # S2_isCaptured = Locations_Reads[12]
        # levelselect_coinlock_Address = Locations_Reads[13]
        # CoinTable = Locations_Reads[14]
        # TempCoinTable = Locations_Reads[15]
        # monkeylevelcounts = Locations_Reads[16]
        # currentApes = Locations_Reads[17]
        # transitionPhase = Locations_Reads[18]
        #
        # locationsToSend = []
        # monkeysToSend = set()
        # coinsToSend = set()
        # mailToSend = set()
        # bossesToSend = set()
        # racesToSend = set()
        # allowcollect = 1 if self.allowcollect == 0x01 or self.forcecollect == True else 0
        # SyncCount = 0
        # # Replace levelID if in Monkey Madness
        # if 0x18 < currentLevel <= 0x1D:
        #     level = 0x18
        # else:
        #     level = currentLevel
        #
        # # Local update conditions
        # # Condition to not update on first pass of client (self.roomglobal is 0 on first pass)
        # if self.roomglobal == 0:
        #     localcondition = False
        #     return
        # else:
        #     localcondition = (currentLevel == self.levelglobal)
        #
        # # Stock BossRooms in a variable (For excluding these rooms in local monkeys sending)
        # locationWrites = []
        # levelsToSync = []
        # bossRooms = RAM.bossListLocal.keys()
        # mailboxesRooms = RAM.mailboxListLocal.keys()
        # redmailboxesRooms = RAM.redMailboxes.keys()
        # keyList = list(RAM.monkeyListGlobal.keys())
        # valList = list(RAM.monkeyListGlobal.values())
        #
        # addresses = []
        # for val in valList:
        #     tuple1 = (val, 1, "MainRAM")
        #     addresses.append(tuple1)
        # globalMonkeys = await bizhawk.read(ctx.bizhawk_ctx, addresses)
        # GlobalIDToValueTable  = dict(zip(keyList,globalMonkeys))
        # # localmonkeys = await bizhawk.read(ctx.bizhawk_ctx, addresses)
        # # Check if in level select or in time hub, then read global monkeys
        #
        # temp_counter = currentApes
        # if gameState == RAM.gameState["LevelSelect"] or currentLevel == RAM.levels["Time"] or (level == 0x18 and gameState == RAM.gameState["InLevel"]) or self.forcecollect and transitionPhase != 0x06:
        #     for i in range(len(globalMonkeys)):
        #         MonkeyID = keyList[i]
        #         MonkeyAddress = valList[i]
        #         iscaught = int.from_bytes(GlobalIDToValueTable[MonkeyID], byteorder='little') == RAM.caughtStatus["PrevCaught"]
        #         if iscaught:
        #             if (MonkeyID + self.offset) not in self.locations_list:
        #                 monkeysToSend.add(MonkeyID + self.offset)
        #         else:
        #             if allowcollect == 0x01:
        #                 if (MonkeyID + self.offset) in self.locations_list:
        #                     levels_containing_monkey = [level for level, monkeys in RAM.monkeysperlevel.items() if MonkeyID in monkeys]
        #                     room_containing_monkey = [room for room, monkeys in RAM.monkeyListTempLocal.items() if MonkeyID in monkeys]
        #                     if currentLevel in RAM.MM_roomspersublevel.keys():
        #                         Sub_Levels_Rooms = list(RAM.MM_roomspersublevel[currentLevel])
        #                     else:
        #                         Sub_Levels_Rooms = []
        #                     if levels_containing_monkey[0] == 0x18 and (level == 0x18 and (room_containing_monkey not in Sub_Levels_Rooms)) and currentRoom not in room_containing_monkey:
        #                         #print(f"+1 for Monkey#{MonkeyID}")
        #                         temp_counter += 1
        #                     locationWrites += [(MonkeyAddress,0x02.to_bytes(1, "little"), "MainRAM")]
        #                     GlobalIDToValueTable[MonkeyID] = 0x02.to_bytes(1, "little")
        #                     if not set(levels_containing_monkey).issubset(set(levelsToSync)):
        #                         levelsToSync += levels_containing_monkey
        # # if being in a level
        # # check if NOT in a boss room since there is no monkeys to send there
        # if gameState == RAM.gameState["InLevel"] and (localcondition) and not (currentRoom in bossRooms):
        #     monkeyaddrs = RAM.monkeyListLocal[currentRoom]
        #     key_list = list(monkeyaddrs.keys())
        #     val_list = list(monkeyaddrs.values())
        #
        #     addresses = []
        #     for val in val_list:
        #         tuple1 = (val, 1, "MainRAM")
        #         addresses.append(tuple1)
        #     localmonkeys = await bizhawk.read(ctx.bizhawk_ctx, addresses)
        #
        #     if level == 0x18:
        #         levelRooms = list(RAM.MM_roomspersublevel[currentLevel])
        #     else:
        #         levelRooms = list(RAM.roomsperlevel[currentLevel])
        #
        #     for i in range(len(levelRooms)):
        #         roomID = levelRooms[i]
        #         inRoom = currentRoom == roomID
        #         MonkeysInRoom_keys = list(RAM.monkeyListLocal.get(roomID).keys())
        #         MonkeysInRoom_address = list(RAM.monkeyListLocal.get(roomID).values())
        #
        #         for x in range(len(MonkeysInRoom_keys)):
        #             MonkeyID = MonkeysInRoom_keys[x]
        #             GlobalMonkeyAddress = RAM.monkeyListGlobal.get(MonkeyID)
        #             iscaughtglobal = int.from_bytes(GlobalIDToValueTable[MonkeyID], byteorder='little') in (RAM.caughtStatus["Caught"],RAM.caughtStatus["PrevCaught"])
        #             if inRoom:
        #                 if transitionPhase != 0x06:
        #                     iscaughtlocal = int.from_bytes(localmonkeys[x], byteorder='little') in (RAM.caughtStatus["Caught"], RAM.caughtStatus["PrevCaught"])
        #                 else:
        #                     iscaughtlocal = False
        #                 if iscaughtlocal:
        #                     # If the Monkey is not already in the sent locations list, add it to an array to send location
        #                     if (MonkeyID + self.offset) not in self.locations_list and currentRoom == self.roomglobal:
        #                         monkeysToSend.add(MonkeyID + self.offset)
        #                         locationWrites += [(GlobalMonkeyAddress, 0x02.to_bytes(1, "little"), "MainRAM")]
        #                         GlobalIDToValueTable[MonkeyID] = 0x02.to_bytes(1, "little")
        #                         iscaughtglobal = True
        #                 else:
        #                     if allowcollect:
        #                         # If the location ID is in the list and they are not caught, sync them
        #                         if (MonkeyID + self.offset) in self.locations_list and transitionPhase != 0x06:
        #                             #MonkeyID = key_list[x]
        #                             MonkeyAddress = val_list[x]
        #                             levels_containing_monkey = [level for level, monkeys in RAM.monkeysperlevel.items() if MonkeyID in monkeys]
        #                             MonkeyHitboxUpdateAddress = RAM.localMonkeyHitbox.get(MonkeyAddress)
        #                             locationWrites += [(MonkeyHitboxUpdateAddress, 0xFF.to_bytes(1, "little"), "MainRAM")]
        #                             locationWrites += [(MonkeyAddress, 0x02.to_bytes(1, "little"), "MainRAM")]
        #                             locationWrites += [(GlobalMonkeyAddress, 0x02.to_bytes(1, "little"), "MainRAM")]
        #                             #print(f"+1 for Monkey#{MonkeyID}")
        #                             #print(f"iscaughtglobal:{iscaughtglobal}")
        #                             temp_counter += 1
        #                             if not set(levels_containing_monkey).issubset(set(levelsToSync)):
        #                                 levelsToSync += levels_containing_monkey
        #                                 #print(levelsToSync)
        #             else:
        #                 if allowcollect:
        #                     # Supposed to only do a local sync of the current MM_Sub-Level
        #                     if (MonkeyID + self.offset) in self.locations_list and iscaughtglobal == False:
        #                         #print(f"Synched monkey #{MonkeyID}")
        #                         levels_containing_monkey = [level for level, monkeys in RAM.monkeysperlevel.items() if MonkeyID in monkeys]
        #                         room_containing_monkey = [room for room, monkeys in RAM.monkeyListTempLocal.items() if MonkeyID in monkeys]
        #                         MonkeyAddress = RAM.monkeyListTempLocal.get(room_containing_monkey[0]).get(MonkeyID)
        #                         locationWrites += [(GlobalMonkeyAddress, 0x02.to_bytes(1, "little"), "MainRAM")]
        #                         locationWrites += [(MonkeyAddress, 0x02.to_bytes(1, "little"), "MainRAM")]
        #                         GlobalIDToValueTable[MonkeyID] = 0x02.to_bytes(1, "little")
        #                         iscaughtglobal = True
        #                         print(f"Local +1 for Monkey#{MonkeyID}")
        #                         temp_counter += 1
        #                         if not set(levels_containing_monkey).issubset(set(levelsToSync)):
        #                             levelsToSync += levels_containing_monkey
        #                             #print(levelsToSync)
        #     if temp_counter > currentApes:
        #         locationWrites += [(RAM.currentApesAddress, temp_counter.to_bytes(1, "little"), "MainRAM")]
        #
        # # Check for Coins
        #
        # # New Coins System !
        # # Gets the entirety of the game's coin table, then evaluate if the server is missing some of them
        # # If a coin is collected and is not in the server it will then send
        #
        # # When allowcollect is on, the inverse is also true : Any coin the server have that is not in the game will be put in the game
        #
        # targetCoinTable = TempCoinTable if levelselect_coinlock_Address == 0x01 else CoinTable
        # targetTableAddress = RAM.temp_startingCoinAddress if levelselect_coinlock_Address == 0x01 else RAM.startingCoinAddress
        #
        # # List of coins already in the client
        # FormattedCoinTable = self.format_cointable(ctx,targetCoinTable,0,0,"Locations")
        # if FormattedCoinTable == "":
        #     FormattedCoinTable = []
        # FormattedCoinTable.sort(reverse=True)
        #
        # # List of coins in the client that the server does not have
        # ClientCoinTable = [item for item in FormattedCoinTable if (item + self.offset + 300) not in self.locations_list]
        # ClientCoinTable.sort(reverse=True)
        #
        # # List of coins in the server that the client does not have
        # ServerCoinTable = [(item - self.offset - 300) for item in self.locations_list if (300 < (item - self.offset) <= 385) and (item - self.offset - 300) not in FormattedCoinTable]
        # ServerCoinTable.sort(reverse=True)
        #
        # # Assemble the 2 coin table (Client and MissingFromServer)
        # CoinsTableString = "".join([f"01{item:02x}" for item in FormattedCoinTable])
        # FinalCoinsTableString = "".join([f"01{item:02x}" for item in ServerCoinTable])
        # finalCoinTable = f"{CoinsTableString}{FinalCoinsTableString}"
        #
        # # Adjust to the coin table format
        # while len(finalCoinTable) < 200:
        #     finalCoinTable = f"00FF{finalCoinTable}"
        # CoinsTableint = int(f"0x{finalCoinTable}", 16)
        # if allowcollect == 0x01:
        #     if ServerCoinTable != set() and ServerCoinTable != []:
        #         locationWrites += [(targetTableAddress, CoinsTableint.to_bytes(100, "little"), "MainRAM")]
        # if ClientCoinTable != set() and ClientCoinTable != []:
        #     [coinsToSend.add((item + self.offset + 300)) for item in ClientCoinTable]
        #
        # if currentRoom in FormattedCoinTable:
        #     CoinValues = RAM.coinsListLocal.get(currentRoom)
        #     CoinVisualSprite = CoinValues[0]
        #     CoinHitBoxPosition = CoinValues[1]
        #     locationWrites2 = []
        #     locationGuards2 = []
        #     locationWrites2 += [(CoinVisualSprite, 0x00.to_bytes(1, "little"), "MainRAM")]
        #     locationWrites2 += [(CoinHitBoxPosition, RAM.CoinHitBoxPositionOff.to_bytes(2, "little"), "MainRAM")]
        #     locationGuards2 += [(CoinVisualSprite,0x04.to_bytes(1, "little"), "MainRAM")]
        #     locationGuards2 += [(RAM.currentRoomIdAddress,currentRoom.to_bytes(1, "little"), "MainRAM")]
        #     await bizhawk.guarded_write(ctx.bizhawk_ctx, locationWrites2,locationGuards2)
        #
        # if locationWrites:
        #     await bizhawk.write(ctx.bizhawk_ctx, locationWrites)
        #
        # if levelsToSync:
        #     # Sync all needed levels and return the number synched
        #     SyncCount = await self.syncAllMonkeycount(ctx,levelsToSync)
        # # Check for level bosses
        # if gameState == RAM.gameState["InLevel"] and (localcondition) and (currentRoom in bossRooms):
        #     bossaddrs = RAM.bossListLocal[currentRoom]
        #     key_list = list(bossaddrs.keys())
        #     val_list = list(bossaddrs.values())
        #     addresses = []
        #
        #     for val in val_list:
        #         tuple1 = (val, 1, "MainRAM")
        #         addresses.append(tuple1)
        #
        #     bossesList = await bizhawk.read(ctx.bizhawk_ctx, addresses)
        #     #bossesToSend = set()
        #
        #     for i in range(len(bossesList)):
        #         # For TVT boss, check TVT_BossPhase, if it's 3 the fight is ongoing
        #         if (currentRoom == 68):
        #             if (TVT_BossPhase == 3 and int.from_bytes(bossesList[i], byteorder='little') == 0x00):
        #                 if (key_list[i] + self.offset) not in self.locations_list:
        #                     bossesToSend.add(key_list[i] + self.offset)
        #         elif (currentRoom == 70):
        #             if (gameRunning == 1 and int.from_bytes(bossesList[i], byteorder='little') == 0x00):
        #                 if (key_list[i] + self.offset) not in self.locations_list:
        #                     bossesToSend.add(key_list[i] + self.offset)
        #                     self.MM_Jake_Defeated = 1
        #         elif (currentRoom == 71):
        #             if int.from_bytes(bossesList[i], byteorder='little') == 0x00:
        #                 if (key_list[i] + self.offset) not in self.locations_list:
        #                     bossesToSend.add(key_list[i] + self.offset)
        #                     self.MM_Professor_Rescued = 1
        #         else:
        #             if int.from_bytes(bossesList[i], byteorder='little') == 0x00:
        #                 if (key_list[i] + self.offset) not in self.locations_list:
        #                     bossesToSend.add(key_list[i] + self.offset)
        #
        # # Check for Mailboxes
        # if (localcondition) and (currentRoom in mailboxesRooms) and (gameState == RAM.gameState["InLevel"] or gameState == RAM.gameState["TimeStation"]):
        #     mailboxesaddrs = RAM.mailboxListLocal[currentRoom]
        #
        #     boolGotMail = (gotMail == 0x02)
        #     key_list = list(mailboxesaddrs.keys())
        #     val_list = list(mailboxesaddrs.values())
        #
        #     #mail_to_send = set()
        #     # Rearrange the array if there is 2 indexes for the same mailbox
        #     for i in range(len(val_list)):
        #         strVal = str(val_list[i])
        #         if strVal.__contains__("{"):
        #             strVal = strVal.replace("{", "").replace("}", "")
        #             strVal = strVal.split(",")
        #             for j in range(len(strVal)):
        #                 key_list.append(key_list[i])
        #                 val_list.append(int(strVal[j]))
        #             val_list.pop(i)
        #             key_list.pop(i)
        #     for i in range(len(val_list)):
        #         if val_list[i] == mailboxID and boolGotMail:
        #             if (key_list[i] + self.offset) not in self.locations_list:
        #                 mailToSend.add(key_list[i] + self.offset)
        #
        #     # Only triggers if there is a red mailbox in the room and you are NOT viewing mail
        #     if (currentRoom in redmailboxesRooms) and (gotMail == 0x00):
        #         redMailboxaddrs = RAM.redMailboxes[currentRoom]
        #
        #         redkey_list = list(redMailboxaddrs.keys())
        #         redval_list = list(redMailboxaddrs.values())
        #
        #         addresses = []
        #
        #         for val in redval_list:
        #             tuple1 = (val, 1, "MainRAM")
        #             addresses.append(tuple1)
        #
        #         redMailboxesList = await bizhawk.read(ctx.bizhawk_ctx, addresses)
        #         for i in range(len(redkey_list)):
        #             if int.from_bytes(redMailboxesList[i], byteorder='little') == 0x01:
        #                 if (redkey_list[i] + self.offset) not in self.locations_list:
        #                     mailToSend.add(redkey_list[i] + self.offset)
        #
        # # Check for Jake Victory
        # if currentRoom == 19 and gameState == RAM.gameState["JakeCleared"] and jakeVictory == 0x2:
        #     #racesToSend = set()
        #     racesToSend.add(295 + self.offset)
        #     racesToSend.add(296 + self.offset)
        #     racesToSend.add(297 + self.offset)
        #     racesToSend.add(298 + self.offset)
        #     racesToSend.add(299 + self.offset)
        #
        # elif currentRoom == 36 and gameState == RAM.gameState["JakeCleared"] and jakeVictory == 0x2:
        #     #coins = set()
        #     racesToSend.add(290 + self.offset)
        #     racesToSend.add(291 + self.offset)
        #     racesToSend.add(292 + self.offset)
        #     racesToSend.add(293 + self.offset)
        #     racesToSend.add(294 + self.offset)
        #
        #
        # # Check for victory conditions
        # specter1Condition = (currentRoom == 86 and S1_P2_State == 1 and S1_P2_Life == 0)
        # specter2Condition = (currentRoom == 87 and S2_isCaptured == 1)
        # currentgoal = ctx.slot_data["goal"]
        # if RAM.gameState["InLevel"] == gameState and specter1Condition:
        #     bossesToSend.add(self.offset + 205)
        #     if currentgoal in (GoalOption.option_mm, GoalOption.option_mmtoken) and not ctx.finished_game:
        #             await ctx.send_msgs([{
        #                 "cmd": "StatusUpdate",
        #                 "status": ClientStatus.CLIENT_GOAL
        #             }])
        #             await self.send_bizhawk_message(ctx, "You have completed your goal o[8(|)", "Passthrough", "")
        #     self.MM_Completed = True
        #     ctx.finished_game = True
        # if RAM.gameState["InLevel"] == gameState and specter2Condition:
        #     bossesToSend.add(self.offset + 206)
        #
        #     if currentgoal in (GoalOption.option_ppm, GoalOption.option_ppmtoken) and not ctx.finished_game:
        #             await ctx.send_msgs([{
        #                 "cmd": "StatusUpdate",
        #                 "status": ClientStatus.CLIENT_GOAL
        #             }])
        #             await self.send_bizhawk_message(ctx, "You have completed your goal o[8(|)", "Passthrough", "")
        #     self.PPM_Completed = True
        #     ctx.finished_game = True
        #
        # locationsToSend = monkeysToSend | coinsToSend | mailToSend | bossesToSend | racesToSend
        # if locationsToSend != "" and locationsToSend != set():
        #     await ctx.check_locations(locationsToSend)
        #
        # if self.forcecollect == True:
        #     msg = f"=================================\n"
        #     msg += f"Synced progress into the game:\n"
        #     if ctx.slot_data["coin"] == 0x01:
        #         if len(ServerCoinTable) == 0:
        #             msg += f"    No Coins updated\n"
        #         else:
        #             msg += f"    {len(ServerCoinTable)} Coins updated\n"
        #     if SyncCount == 0:
        #         msg += f"    No Monkeys updated\n"
        #     else:
        #         msg += f"    {SyncCount} Monkeys updated\n"
        #     msg += f"=================================\n"
        #     logger.info(msg)
        #     self.forcecollect = False

    async def specialitems_handling(self, ctx: "BizHawkClientContext", SpecialItems_Reads) -> None:
        pass
        # gameState = SpecialItems_Reads[0]
        # gotMail = SpecialItems_Reads[1]
        # spikeState = SpecialItems_Reads[2]
        # spikeState2 = SpecialItems_Reads[3]
        # menuState = SpecialItems_Reads[4]
        # menuState2 = SpecialItems_Reads[5]
        # currentGadgets = SpecialItems_Reads[6]
        # currentRoom = SpecialItems_Reads[7]
        # gameRunning = SpecialItems_Reads[8]
        # DS_spikeColor = SpecialItems_Reads[9]
        # heldGadget = SpecialItems_Reads[10]
        # CatchingState = SpecialItems_Reads[11]
        # cookies = SpecialItems_Reads[12]
        #
        # SpecialItems_Writes = []
        # SpecialItems_Guards = []
        #
        # # Gamestate
        # valid_gameStates = (RAM.gameState['InLevel'], RAM.gameState['InLevelTT'], RAM.gameState['TimeStation'], RAM.gameState['Jake'])
        # grounded = [0x00, 0x01, 0x02, 0x05, 0x07]
        # is_grounded = (spikeState2 in grounded)
        # is_catching = (CatchingState == 0x08)
        # is_dead = (cookies == 0)
        # in_menu = (menuState == 0 and menuState2 == 1)
        # reading_mail = (gotMail == 0x01) or (gotMail == 0x02)
        # is_sliding = (spikeState2 in (0x2F,0x30))
        # is_idle = (spikeState == 0x12) and (spikeState2 in {0x80, 0x81, 0x82, 0x83, 0x84})
        # in_race = (currentRoom == 19 or currentRoom == 36)
        # cannot_control = (gameRunning == 0)
        # stunned = (spikeState2 == 0x58)
        # StunTrap_incompatible_list = [RAM.items["IcyHotPantsTrap"],RAM.items["StunTrap"],RAM.items["BananaPeelTrap"],RAM.items["MonkeyMashTrap"]]
        #
        # if (gameState not in valid_gameStates or in_menu or reading_mail or is_sliding or is_idle or cannot_control or is_catching):
        #     self.ape_handler.pause = True
        #     self.rainbow_cookie.pause = True
        #     self.camera_rotate_trap.pause = True
        # else:
        #     self.ape_handler.pause = False
        #     self.rainbow_cookie.pause = False
        #     self.camera_rotate_trap.pause = False
        #
        # if not self.specialitem_queue and not self.priority_trap_queue:
        #     #Exit if no traps
        #     return None
        #
        # else:
        #     if self.priority_trap_queue:
        #         item_id = self.priority_trap_queue[0][0]
        #         item_info = self.priority_trap_queue[0][1]
        #         IsPriority = True
        #     else:
        #         item_id = self.specialitem_queue[0][0]
        #         item_info = self.specialitem_queue[0][1]
        #         IsPriority = False
        #
        #     StunTrap_incompatible = self.stun_trap.is_active and (item_id in StunTrap_incompatible_list)
        #     # Does not send the traps in these states
        #     if gameState not in valid_gameStates or in_menu or reading_mail or is_sliding or in_race or is_idle or cannot_control or stunned or StunTrap_incompatible:
        #         if is_idle:
        #             # Trigger a Wake Up for spike. Banana Peel is deadly while Idle
        #             SpecialItems_Writes += [(RAM.spikeIdleTimer, 0x0000.to_bytes(2, "little"), "MainRAM")]
        #             await bizhawk.write(ctx.bizhawk_ctx, SpecialItems_Writes)
        #         if not IsPriority:
        #             #Not priority
        #             if item_info >= 10:
        #                 # Trap Removed for incompatibility(10 passes)
        #                 self.specialitem_queue.pop(0)
        #             elif StunTrap_incompatible:
        #                 # Trap moved to the end
        #                 self.specialitem_queue.insert(len(self.specialitem_queue)-1,[item_id,item_info +1])
        #                 self.specialitem_queue.pop(0)
        #         else:
        #             #Is priority
        #             #Give the trap 5 seconds to trigger, else discard
        #             if (time.time()) >= item_info + 5:
        #                 self.priority_trap_queue.pop(0)
        #         return None
        #         # Exit without sending trap, keeping it active for the next pass
        #     #print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        #     #print(item_info)
        #     #print(IsPriority)
        #     # Banana Peel Trap handling
        #     if item_id == RAM.items['BananaPeelTrap']:
        #         if IsPriority:
        #             self.priority_trap_queue.pop(0)
        #         else:
        #             self.specialitem_queue.pop(0)
        #         SpecialItems_Writes += [(RAM.spikeState2Address, 0x2F.to_bytes(1, "little"), "MainRAM")]
        #
        #     # Gadget Shuffle Trap handling
        #     elif item_id == RAM.items['GadgetShuffleTrap']:
        #         if IsPriority:
        #             self.priority_trap_queue.pop(0)
        #         else:
        #             self.specialitem_queue.pop(0)
        #         # print(self.specialitem_queue)
        #         chosen_gadgets = []
        #         chosen_values = [0, 0, 0, 0]
        #         faces = [0, 1, 2, 3]
        #         facesNames = ["P1 X","P1 Square","P1 Circle","P1 Triangle"]
        #         faceValues = [0xBF,0x7F,0xDF,0xEF]
        #         Trap_writes = []
        #         Trap_writes2 = []
        #         Trap_guards = []
        #
        #         # Exit if no gadgets has been unlocked yet
        #         if currentGadgets == []:
        #             return None
        #
        #         # 1 pass for each face
        #         for x in range(4):
        #             randomFace = int(round(random.random() * (len(faces) - 1), None))
        #             face = faces[randomFace]
        #             # If there is no more gadgets, it means we put an "Empty" spot
        #             if currentGadgets == []:
        #                 # print("Face #" + str(randomFace + 1) + ": None | 255")
        #                 chosen_values[face] = 0xFF
        #                 faces.pop(randomFace)
        #             else:
        #                 randomGadget = int(round(random.random() * (len(currentGadgets) - 1), None))
        #                 gadget_value = gadgetsValues[currentGadgets[randomGadget]]
        #                 chosen_values[face] = gadget_value
        #                 # print("Face #" + str(faces[randomFace]) + ": " + str(currentGadgets[randomGadget]) + " | " + str(gadgetsValues[currentGadgets[randomGadget]]))
        #                 chosen_gadgets.append(str(currentGadgets[randomGadget]))
        #                 currentGadgets.pop(randomGadget)
        #                 faces.pop(randomFace)
        #         # print(chosen_gadgets)
        #
        #         Trap_writes += [(RAM.crossGadgetAddress, chosen_values[0].to_bytes(1, "little"), "MainRAM")]
        #         Trap_writes += [(RAM.squareGadgetAddress, chosen_values[1].to_bytes(1, "little"), "MainRAM")]
        #         Trap_writes += [(RAM.circleGadgetAddress, chosen_values[2].to_bytes(1, "little"), "MainRAM")]
        #         Trap_writes += [(RAM.triangleGadgetAddress, chosen_values[3].to_bytes(1, "little"), "MainRAM")]
        #
        #         await bizhawk.write(ctx.bizhawk_ctx, Trap_writes)
        #
        #         # Select a gadget slot
        #         randomSelect = int(round(random.random() * (len(chosen_values) - 1), None))
        #
        #         Trap_writes2 += [(RAM.Controls_TriggersShapes, faceValues[randomSelect].to_bytes(1, "little"), "MainRAM")]
        #
        #         Trap_guards += [(RAM.crossGadgetAddress, chosen_values[0].to_bytes(1, "little"), "MainRAM")]
        #         Trap_guards += [(RAM.squareGadgetAddress, chosen_values[1].to_bytes(1, "little"), "MainRAM")]
        #         Trap_guards += [(RAM.circleGadgetAddress, chosen_values[2].to_bytes(1, "little"), "MainRAM")]
        #         Trap_guards += [(RAM.triangleGadgetAddress, chosen_values[3].to_bytes(1, "little"), "MainRAM")]
        #
        #         #Analog_values = {}
        #         #await self.ape_handler.input_controller.set_inputs(Analog_values)
        #
        #         #if spikeState2 in (128, 129, 131, 132):
        #         #Trap_writes += [(RAM.spikeState2Address, 0x00.to_bytes(1, "little"), "MainRAM")]
        #         #Trap_writes += [(RAM.heldGadgetAddress, chosen_values[randomSelect].to_bytes(1, "little"), "MainRAM")]
        #         #Trap_writes += [(RAM.Controls_TriggersShapes, faceValues[randomSelect].to_bytes(1, "little"), "MainRAM")]
        #         if heldGadget != chosen_values[randomSelect]:
        #             timeout_count = 0
        #             while timeout_count < 10:
        #                 timeout_count += 1
        #                 #print(timeout_count)
        #                 await bizhawk.guarded_write(ctx.bizhawk_ctx, Trap_writes2, Trap_guards)
        #
        #     # Monkey Mash Trap handling
        #     elif item_id == RAM.items['MonkeyMashTrap']:
        #         if IsPriority:
        #             self.priority_trap_queue.pop(0)
        #         else:
        #             self.specialitem_queue.pop(0)
        #         mash_duration = 10  # Example: 10 seconds per powerup item
        #         if self.ape_handler.is_active:
        #             message = f"Monkey Mash trap extended by {mash_duration} seconds! (Current: {round(self.ape_handler.duration, 0)} seconds)"
        #         else:
        #             message = f"Monkey Mash trap activated for {mash_duration} seconds!"
        #         await self.send_bizhawk_message(ctx, message, "Passthrough", "")
        #         self.ape_handler.activate_monkey(mash_duration)
        #         #print(message)
        #
        #     # Icy Hot Trap handling
        #     elif item_id == RAM.items['IcyHotPantsTrap']:
        #         # Does not fire the trap if not grounded in some way
        #         if is_grounded:
        #             if IsPriority:
        #                 self.priority_trap_queue.pop(0)
        #             else:
        #                 self.specialitem_queue.pop(0)
        #             SpecialItems_Writes += [(RAM.spikeState2Address, 0x4D.to_bytes(1, "little"), "MainRAM")]
        #             SpecialItems_Writes += [(RAM.spike_LavaOrIceTimer, 0x0100.to_bytes(2, "little"), "MainRAM")]
        #             # If the chosen spikecolor is "Vanilla", choose an effect at random between Burn/Frost
        #             if DS_spikeColor == "vanilla":
        #                 randomEffect = int(round(random.random() * (2-1), None))
        #                 if randomEffect == 0:
        #                     # Burn Effect
        #                     SpecialItems_Writes += [(RAM.spikeColor, 0x000000.to_bytes(3, "big"), "MainRAM")]
        #                 else:
        #                     # Frost Effect:
        #                     SpecialItems_Writes += [(RAM.spikeColor, 0x0000FF.to_bytes(3, "big"), "MainRAM")]
        #         else:
        #             if IsPriority:
        #                 if item_info >= (time.time() + 5):
        #                     #print("TrapLinked Trap expired")
        #                     self.priority_trap_queue.pop(0)
        #     # Rainbow Cookie handling
        #     elif item_id == RAM.items['RainbowCookie']:
        #         self.specialitem_queue.pop(0)
        #         item_duration = 20  # Example: 20 seconds per powerup item
        #         if self.rainbow_cookie.is_active:
        #             message = f"Rainbow Cookie extended by {item_duration} seconds! (Current: {round(self.rainbow_cookie.duration, 0)} seconds)"
        #         else:
        #             message = f"Rainbow Cookie activated for {item_duration} seconds!"
        #         await self.send_bizhawk_message(ctx, message, "Passthrough", "")
        #         await self.rainbow_cookie.activate_rainbow_cookie(item_duration)
        #
        #     #Stun Trap handling
        #     elif item_id == RAM.items['StunTrap']:
        #         if IsPriority:
        #             self.priority_trap_queue.pop(0)
        #         else:
        #             self.specialitem_queue.pop(0)
        #         item_duration = 2  # Example: 2 seconds per powerup item
        #         #if self.stun_trap.is_active:
        #         #    message = f"Stun Trap extended by {item_duration} seconds! (Current: {round(self.stun_trap.duration, 0)} seconds)"
        #         #else:
        #         #    message = f"Stun Trap activated for {item_duration} seconds!"
        #         message = f"Stun Trap activated for {item_duration} seconds!"
        #         await self.send_bizhawk_message(ctx, message, "Passthrough", "")
        #         await self.stun_trap.activate_StunTrap(item_duration,spikeState2,currentRoom)
        #     #Camera Rotate Trap handling
        #     elif item_id == RAM.items['CameraRotateTrap']:
        #         if IsPriority:
        #             self.priority_trap_queue.pop(0)
        #         else:
        #             self.specialitem_queue.pop(0)
        #         item_duration = 20  # Example: 2 seconds per powerup item
        #         #if self.stun_trap.is_active:
        #         #    message = f"Stun Trap extended by {item_duration} seconds! (Current: {round(self.stun_trap.duration, 0)} seconds)"
        #         #else:
        #         #    message = f"Stun Trap activated for {item_duration} seconds!"
        #         message = f"Camera Rotate Trap activated for {item_duration} seconds!"
        #         await self.send_bizhawk_message(ctx, message, "Passthrough", "")
        #         await self.camera_rotate_trap.activate_camera_rotate(item_duration, currentRoom)
        #
        #     if SpecialItems_Writes:
        #         await bizhawk.write(ctx.bizhawk_ctx, SpecialItems_Writes)

    async def water_net_handling(self, ctx: "BizHawkClientContext", WN_Reads) -> None:
        # Water Net client handling
        # If Progressive WaterNet is 0 no Swim and no Dive, if it's 1 No Dive (Swim only)
        # 8-9 Jumping/falling, 35-36 D-Jump, 83-84 Flyer => don't reset the counter

        inAir = [0x08, 0x09, 0x35, 0x36, 0x83, 0x84]
        swimming = [0x46, 0x47]
        grounded = [0x00, 0x01, 0x02, 0x05, 0x07]  # 0x80, 0x81 Removed them since you can fling you net and give you extra air

        limited_OxygenLevel = 0x64

        gameState = WN_Reads[0]
        waternetState = WN_Reads[1]
        gameRunning = WN_Reads[2]
        spikeState2 = WN_Reads[3]
        swim_oxygenLevel = WN_Reads[4]
        cookies = WN_Reads[5]
        isUnderwater = WN_Reads[6]
        watercatchState = WN_Reads[7]

        WN_writes = []

        is_grounded = spikeState2 in grounded
        # Base variables
        if waternetState == 0x00:
            WN_writes += [(RAM.swim_surfaceDetectionAddress, 0x00000000.to_bytes(4, "little"), "MainRAM")]
            WN_writes += [(RAM.canDiveAddress, 0x00000000.to_bytes(4, "little"), "MainRAM")]
            WN_writes += [(RAM.swim_oxygenReplenishSoundAddress, 0x00000000.to_bytes(4, "little"), "MainRAM")]
            WN_writes += [(RAM.swim_ReplenishOxygenUWAddress, 0x00000000.to_bytes(4, "little"), "MainRAM")]
            WN_writes += [(RAM.swim_replenishOxygenOnEntryAddress, 0x00000000.to_bytes(4, "little"), "MainRAM")]
        elif waternetState == 0x01:
            WN_writes += [(RAM.swim_surfaceDetectionAddress, 0x0801853A.to_bytes(4, "little"), "MainRAM")]
            WN_writes += [(RAM.canDiveAddress, 0x00000000.to_bytes(4, "little"), "MainRAM")]
            WN_writes += [(RAM.swim_oxygenReplenishSoundAddress, 0x00000000.to_bytes(4, "little"), "MainRAM")]
            WN_writes += [(RAM.swim_ReplenishOxygenUWAddress, 0x00000000.to_bytes(4, "little"), "MainRAM")]
            WN_writes += [(RAM.swim_replenishOxygenOnEntryAddress, 0x00000000.to_bytes(4, "little"), "MainRAM")]
        else:
            # (waternetstate > 0x01)
            WN_writes += [(RAM.swim_surfaceDetectionAddress, 0x0801853A.to_bytes(4, "little"), "MainRAM")]
            WN_writes += [(RAM.canDiveAddress, 0x08018664.to_bytes(4, "little"), "MainRAM")]
            WN_writes += [(RAM.swim_oxygenReplenishSoundAddress, 0x0C021DFE.to_bytes(4, "little"), "MainRAM")]
            WN_writes += [(RAM.swim_ReplenishOxygenUWAddress, 0xA4500018.to_bytes(4, "little"), "MainRAM")]
            WN_writes += [(RAM.swim_replenishOxygenOnEntryAddress, 0xA4434DC8.to_bytes(4, "little"), "MainRAM")]

        # Oxygen Handling
        if waternetState == 0x00:
            if gameState == RAM.gameState["InLevel"] or gameState == RAM.gameState["InLevelTT"]:
                if gameRunning == 0x01:
                    # Set the air to the "Limited" value if 2 conditions:
                    # Oxygen is higher that "Limited" value AND spike is Swimming or Grounded
                    if spikeState2 in swimming:
                        if (swim_oxygenLevel > limited_OxygenLevel):
                            WN_writes += [(RAM.swim_oxygenLevelAddress, limited_OxygenLevel.to_bytes(2, "little"), "MainRAM")]
                    else:
                        # if self.waterHeight != 0:
                        # self.waterHeight = 0
                        if is_grounded:
                            WN_writes += [(RAM.swim_oxygenLevelAddress, limited_OxygenLevel.to_bytes(2, "little"), "MainRAM")]

                #else:
                # Game Not running
                #if swim_oxygenLevel == 0 and cookies == 0 and gameRunning == 0:
                if swim_oxygenLevel == 0 and cookies == 0:
                    # You died while swimming, reset Oxygen to "Limited" value prevent death loops
                    WN_writes += [(RAM.swim_oxygenLevelAddress, limited_OxygenLevel.to_bytes(2, "little"), "MainRAM")]
                    WN_writes += [(RAM.isUnderwater, 0x00.to_bytes(1, "little"), "MainRAM")]

        if waternetState == 0x01:

            if isUnderwater == 0x00 and swim_oxygenLevel != limited_OxygenLevel:
                WN_writes += [(RAM.swim_oxygenLevelAddress, limited_OxygenLevel.to_bytes(2, "little"), "MainRAM")]
            if swim_oxygenLevel == 0 and cookies == 0 and gameRunning == 0:
                # You died while swimming, reset Oxygen to "Limited" value prevent death loops
                WN_writes += [(RAM.swim_oxygenLevelAddress, limited_OxygenLevel.to_bytes(2, "little"), "MainRAM")]
                WN_writes += [(RAM.isUnderwater, 0x00.to_bytes(1, "little"), "MainRAM")]

        # WaterCatch unlocking stuff bellow
        if watercatchState == 0x00:
            WN_writes += [(RAM.canWaterCatchAddress, 0x00.to_bytes(1, "little"), "MainRAM")]
        else:
            WN_writes += [(RAM.canWaterCatchAddress, 0x04.to_bytes(1, "little"), "MainRAM")]

        # Low Oxygen Sounds
        if spikeState2 in swimming:

            # Off
            if ctx.slot_data["lowoxygensounds"] == 0x00:
                WN_writes += [(RAM.swim_oxygenLowLevelSoundAddress, 0x3C028004.to_bytes(4, "little"), "MainRAM")]
                WN_writes += [(RAM.swim_oxygenMidLevelSoundAddress, 0x3C028004.to_bytes(4, "little"), "MainRAM")]
            # Half Beeps
            elif ctx.slot_data["lowoxygensounds"] == 0x01:

                self.lowOxygenCounter += 1
                # Should start at 1
                # print(self.lowOxygenCounter)
                if self.lowOxygenCounter <= 2:
                    WN_writes += [(RAM.swim_oxygenLowLevelSoundAddress, 0x3C02800F.to_bytes(4, "little"), "MainRAM")]
                    WN_writes += [(RAM.swim_oxygenMidLevelSoundAddress, 0x3C02800F.to_bytes(4, "little"), "MainRAM")]
                elif self.lowOxygenCounter <= 3:
                    WN_writes += [(RAM.swim_oxygenLowLevelSoundAddress, 0x3C028004.to_bytes(4, "little"), "MainRAM")]
                    WN_writes += [(RAM.swim_oxygenMidLevelSoundAddress, 0x3C028004.to_bytes(4, "little"), "MainRAM")]
                elif self.lowOxygenCounter > 3:
                    self.lowOxygenCounter = 0

            # On (Vanilla)
            else:
                # print("Vanilla")
                WN_writes += [(RAM.swim_oxygenLowLevelSoundAddress, 0x3C02800F.to_bytes(4, "little"), "MainRAM")]
                WN_writes += [(RAM.swim_oxygenMidLevelSoundAddress, 0x3C02800F.to_bytes(4, "little"), "MainRAM")]
        else:
            if self.lowOxygenCounter != 1:
                self.lowOxygenCounter = 1

        await bizhawk.write(ctx.bizhawk_ctx,WN_writes)

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

    def unlockLevels(self, ctx: "BizHawkClientContext", monkeylevelCounts, gameState, hundoMonkeysCount, reqkeys, newpositions, SAcomplete, GAcomplete, PPMcomplete):
        pass
        # TODO: Change this
        # key = self.worldkeycount
        # token = self.tokencount
        # curApesWrite = ""
        # reqApesWrite = ""
        # hundoWrite = ""
        # levellocked = RAM.levelStatus["Locked"].to_bytes(1, byteorder = "little")
        # levelopen = RAM.levelStatus["Open"].to_bytes(1, byteorder = "little")
        # levelhundo = RAM.levelStatus["Hundo"].to_bytes(1, byteorder = "little")
        # allCompleted = True
        #
        # debug = False
        #
        # levels_keys = hundoMonkeysCount.keys()
        # levels_list = list(levels_keys)
        # if gameState == RAM.gameState["LevelSelect"] or debug:
        #     for x in range(len(levels_list)):
        #         if monkeylevelCounts[x] < hundoMonkeysCount[levels_list[x]]:
        #             # print("Level " + str(x) + " not completed" + str(int.from_bytes(monkeylevelCounts[x])) + "/" + str(hundoMonkeysCount[levels_list[x]]))
        #             allCompleted = False
        #             break
        #             # Does not need to check the rest of the levels, at least 1 is not completed
        #
        # if ctx.slot_data["goal"] == GoalOption.option_ppmtoken:
        #     PPMUnlock = (key >= reqkeys[21] and token >= min(ctx.slot_data["requiredtokens"], ctx.slot_data["totaltokens"]))
        # elif ctx.slot_data["goal"] == GoalOption.option_mmtoken or ctx.slot_data["goal"] == GoalOption.option_tokenhunt:
        #     PPMUnlock = (key >= reqkeys[21])
        # else:
        #     PPMUnlock = (key >= reqkeys[21] and allCompleted)
        #
        # # Set unlocked/locked state of levels
        # # This does not handle assignment of Specter Coin icons.
        # # Most of this handling is about entrance order - the Hundo check would need to be pulled out of the big if chain because it's about level order right now.
        # # Make sure that Hundo doesn't get set on a level that needs to be Locked and that Open doesn't get set on a level that needs to be Hundo.
        # levelstates = []
        # for index in range(0, 22):
        #     # Do we have enough keys for this level? If no, lock. If yes, continue.
        #     if key >= reqkeys[index]:
        #         # Are we checking the final entrance? If yes, open. If no, continue.
        #         if index != 21:
        #             # Do we have enough keys for the next level? If no, lock. If yes, open.
        #             if key >= reqkeys[index + 1]:
        #                 levelstates.append((RAM.levelAddresses[list(RAM.levelAddresses.keys())[index]], levelopen, "MainRAM"))
        #             else:
        #                 levelstates.append((RAM.levelAddresses[list(RAM.levelAddresses.keys())[index]], levellocked, "MainRAM"))
        #         else:
        #             levelstates.append((RAM.levelAddresses[list(RAM.levelAddresses.keys())[index]], levelopen, "MainRAM"))
        #     else:
        #         levelstates.append((RAM.levelAddresses[list(RAM.levelAddresses.keys())[index]], levellocked, "MainRAM"))
        #
        # # Set hundo status on entrances that are open and have all monkeys in them caught.
        # # Starts by checking Fossil Field (the level)
        # for index in range(0, 22):
        #     # Is this level a race level?
        #     if index == 6:
        #         # Is Stadium Attack completed?
        #         if SAcomplete == 25:
        #             levelstates[newpositions[index]] = (RAM.levelAddresses[list(RAM.levelAddresses.keys())[newpositions[index]]], levelhundo, "MainRAM")
        #     elif index == 13:
        #         # Is Gladiator Attack completed?
        #         if GAcomplete == 25:
        #             levelstates[newpositions[index]] = (RAM.levelAddresses[list(RAM.levelAddresses.keys())[newpositions[index]]], levelhundo, "MainRAM")
        #     elif index == 21:
        #         # Is Peak Point Matrix completed?
        #         if PPMcomplete == 1:
        #             levelstates[newpositions[index]] = (RAM.levelAddresses[list(RAM.levelAddresses.keys())[newpositions[index]]], levelhundo, "MainRAM")
        #     else:
        #         # Standard level
        #         # Check if the entrance of the indexed level is open.
        #         # If yes, continue. If no, do nothing, the state is correct.
        #         # (Index 0) If Fossil Field is at Dark Ruins, this checks the Dark Ruins entrance (index 4).
        #         if levelstates[newpositions[index]] == (RAM.levelAddresses[list(RAM.levelAddresses.keys())[newpositions[index]]], levelopen, "MainRAM"):
        #             # Check if all monkeys of the indexed level are caught.
        #             # If yes, set the state to hundo. If no, do nothing, the state is correct.
        #             # (Index 0) If Fossil Field is at Dark Ruins, set the Dark Ruins entrance (index 4) to hundo.
        #             if monkeylevelCounts[index] >= hundoMonkeysCount[levels_list[index]]:
        #                 levelstates[newpositions[index]] = (RAM.levelAddresses[list(RAM.levelAddresses.keys())[newpositions[index]]], levelhundo, "MainRAM")
        #
        # # Monkey Madness entrance must be set to locked if Peak Point Matrix should be locked
        # if PPMUnlock == False:
        #     levelstates[20] = ((RAM.levelAddresses[list(RAM.levelAddresses.keys())[20]], levellocked, "MainRAM"))
        #
        # # If there is a change in required monkeys count, include it in the writes
        # returns = list(levelstates)
        # if curApesWrite != "":
        #     returns.append(curApesWrite)
        # if reqApesWrite != "":
        #     returns.append(reqApesWrite)
        # if hundoWrite != "":
        #     returns.append(hundoWrite)
        # return returns


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