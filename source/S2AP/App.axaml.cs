using Archipelago.Core;
using Archipelago.Core.AvaloniaGUI.Models;
using Archipelago.Core.AvaloniaGUI.ViewModels;
using Archipelago.Core.AvaloniaGUI.Views;
using Archipelago.Core.GameClients;
using Archipelago.Core.Models;
using Archipelago.Core.Util;
using Archipelago.MultiClient.Net.BounceFeatures.DeathLink;
using Archipelago.MultiClient.Net.MessageLog.Messages;
using Archipelago.MultiClient.Net.Models;
using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using Newtonsoft.Json;
using ReactiveUI;
using S2AP.Models;
using S2AP.Patching;
using Serilog;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Reactive.Concurrency;
using System.Reflection;
using System.Security.Principal;
using System.Threading.Tasks;
using System.Timers;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.IO;
using static S2AP.Models.Enums;

namespace S2AP;

/**
 * Represents the client, interactions with the AP server, any runtime game modifications.
 */
public partial class App : Application
{
    // TODO: Remember to set this in S2AP.Desktop as well.
    public static string Version = "2.0.0";
    public static List<string> SupportedVersions = ["1.2.0-rc", "1.2.0", "2.0.0-rc", "2.0.0"];

    public static MainWindowViewModel Context;
    public static ArchipelagoClient Client { get; set; }
    private static string _playerName { get; set; }
    public static List<ILocation> GameLocations { get; set; }
    private static readonly object _lockObject = new object();
    private static ConcurrentQueue<string> _cosmeticEffects { get; set; }
    private static byte _sparxUpgrades { get; set; }
    private static bool _hasSubmittedGoal { get; set; }
    private static bool _useQuietHints { get; set; }
    private static int _unlockedLevels { get; set; }
    private static Timer _sparxTimer { get; set; }
    private static Timer _loadGameTimer { get; set; }
    private static Timer _abilitiesTimer { get; set; }
    private static Timer _cosmeticsTimer { get; set; }
    private static MoneybagsOptions _moneybagsOption { get; set; }
    private static PortalTextColor _portalTextColor { get; set; }
    private static LevelInGameIDs _previousLevel { get; set; }
    private static bool _destructiveMode { get; set; }
    private static byte _previousLifeCount { get; set; }
    private static bool _justDied { get; set; }
    private static bool _justReceivedDeathLink { get; set; }
    private static DeathLinkService _deathLinkService { get; set; }
    // Avoid marking the playthrough complete or opening the Ripto door before this value is populated.
    private static int _requiredOrbs = 65;
    private static bool _handleGemsanity = false;
    public override void Initialize()
    {
        AvaloniaXamlLoader.Load(this);
    }

    /**
     * The client relies on having admin permissions to modify Duckstation's memory.
     * This function would raise an exception on Unix.
     * @return true if the user is an admin, or false otherwise.
     */
    private static bool IsRunningAsAdministrator()
    {
        var identity = WindowsIdentity.GetCurrent();
        var principal = new WindowsPrincipal(identity);
        return principal.IsInRole(WindowsBuiltInRole.Administrator);
    }

    public override void OnFrameworkInitializationCompleted()
    {
        Start();
        if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
        {
            desktop.MainWindow = new MainWindow
            {
                DataContext = Context
            };
        }
        else if (ApplicationLifetime is ISingleViewApplicationLifetime singleViewPlatform)
        {
            singleViewPlatform.MainView = new MainWindow
            {
                DataContext = Context
            };
        }
        base.OnFrameworkInitializationCompleted();
    }

    /**
     * Returns a Dictionary of details from the most recent connection.
     * 
     * File path is ./connection.json.
     * 
     * @return A Dictionary with the most recent connection, with keys of host and slot.
     */
    public static Dictionary<String, String> GetLastConnectionDetails()
    {
        string connectionDetails = File.ReadAllText(@"./connection.json");
        return System.Text.Json.JsonSerializer.Deserialize<Dictionary<String, String>>(connectionDetails);
    }

    /**
     * Saves a details from the most recent connection to ./connection.json.
     * 
     * @param A Dictionary with the most recent connection, with keys of host and slot.
     */
    public static void SaveLastConnectionDetails(Dictionary<String, String> lastConnectionDetails)
    {
        string json = System.Text.Json.JsonSerializer.Serialize(lastConnectionDetails);
        File.WriteAllText(@"./connection.json", json);
    }

    /**
     * Runs on starting the application.
     * Sets up handlers and gives initial information to the user.
     */
    public void Start()
    {
        Context = new MainWindowViewModel("0.6.1 or later");  // Minimum AP Version
        Context.ClientVersion = Assembly.GetEntryAssembly().GetName().Version.ToString();
        Context.ConnectClicked += Context_ConnectClicked;
        Context.CommandReceived += (e, a) =>
        {
            if (string.IsNullOrWhiteSpace(a.Command)) return;
            HandleCommand(a);
        };
        Context.ConnectButtonEnabled = true;
        Context.AutoscrollEnabled = true;
        Dictionary<String, String> lastConnectionDetails = new Dictionary<string, string>();
        lastConnectionDetails["slot"] = "";
        lastConnectionDetails["host"] = "";
        // Don't save password.
        try
        {
            lastConnectionDetails = GetLastConnectionDetails();
            if (!lastConnectionDetails.ContainsKey("slot"))
            {
                lastConnectionDetails["slot"] = "";
            }
            if (!lastConnectionDetails.ContainsKey("host"))
            {
                lastConnectionDetails["host"] = "";
            }
        }
        catch (Exception ex)
        {
            Log.Logger.Verbose($"Could not load connection details file.\r\n{ex.ToString()}");
        }
        Context.Host = lastConnectionDetails["host"];
        Context.Slot = lastConnectionDetails["slot"];
        _sparxUpgrades = 0;
        _hasSubmittedGoal = false;
        _useQuietHints = true;
        // No level ID set
        _previousLevel = (LevelInGameIDs)255;
        Log.Logger.Information("This Archipelago Client is compatible only with the NTSC-U\r\n" +
            "release of Spyro 2 (North America version).\r\n\r\n" +
            "This game has an optional Archipelago patch, which fixes a few small bugs.\r\n" +
            "If you put your vanilla game .bin and .cue files, named spyro2.bin and spyro2.cue,\r\n" +
            "in the same folder as this S2AP.Desktop client executable,\r\n" +
            "you can generate it using the !patch command.\r\n");
        if (!IsRunningAsAdministrator())
        {
            Log.Logger.Warning("You do not appear to be running this client as an administrator.\r\n" +
                "This may result in errors or crashes when trying to connect to Duckstation.");
        }
    }

    /**
     * Potentially kills the player when a DeathLink is received.
     * The game can softlock in some levels, so exclude those.
     * 
     * @param deathLink Information about the deathlink, including cause and source.
     */
    private static void HandleDeathLink(DeathLink deathLink)
    {
        if (deathLink.Source == Client.CurrentSession.Players.ActivePlayer.Name)
        {
            return;
        }
        LevelInGameIDs currentLevel = (LevelInGameIDs)Memory.ReadByte(Addresses.CurrentLevelAddress);
        LevelInGameIDs[] deathLinkLevels = [
            LevelInGameIDs.SummerForest,
            LevelInGameIDs.Glimmer,
            LevelInGameIDs.Colossus,
            LevelInGameIDs.IdolSprings,
            LevelInGameIDs.Hurricos,
            LevelInGameIDs.SunnyBeach,
            LevelInGameIDs.AquariaTowers,
            LevelInGameIDs.CrushsDungeon,
            LevelInGameIDs.AutumnPlains,
            LevelInGameIDs.BreezeHarbor,
            LevelInGameIDs.SkelosBadlands,
            LevelInGameIDs.CrystalGlacier,
            LevelInGameIDs.Zephyr,
            LevelInGameIDs.Scorch,
            LevelInGameIDs.FractureHills,
            LevelInGameIDs.MagmaCone,
            LevelInGameIDs.ShadyOasis,
            LevelInGameIDs.GulpsOverlook,
            LevelInGameIDs.WinterTundra,
            LevelInGameIDs.MysticMarsh,
            LevelInGameIDs.CloudTemples,
            LevelInGameIDs.RoboticaFarms,
            LevelInGameIDs.Metropolis,
            LevelInGameIDs.RiptosArena
        ];
        if (!deathLinkLevels.Contains(currentLevel))
        {
            string ignoreMessage = "Received DeathLink from " + deathLink.Source;
            if (deathLink.Cause != null)
            {
                ignoreMessage = ignoreMessage + " - " + deathLink.Cause;
            }
            Log.Logger.Information($"{ignoreMessage}\r\nIgnored the DeathLink to avoid softlock in current level.");
            return;
        }

        _justReceivedDeathLink = true;
        Memory.WriteByte(Addresses.SpyroStateAddress, (byte)SpyroStates.DeathPirouette);
        string message = "Received DeathLink from " + deathLink.Source;
        if (deathLink.Cause != null)
        {
            message = message + " - " + deathLink.Cause;
        }
        Log.Logger.Information(message);
    }
    
    /**
     * Takes text the user has entered into the client and processes it as a command or sends it to the server.
     * 
     * @param command What the user has typed, in a wrapper class.
     */
    private async void HandleCommand(ArchipelagoCommandEventArgs command)
    {
        string commandText = command.Command;
        if (commandText.ToLower() == "!patch")
        {
            Log.Logger.Information("!patch");
            string patchedCue = "spyro2_ap_patch.cue";
            string patchedRom = "spyro2_ap_patch.bin";
            if (
                Patcher.WriteCue("spyro2.cue", patchedCue, patchedRom) &&
                Patcher.WriteRom("spyro2.bin", patchedRom)
            )
            {
                Log.Logger.Information($"Patch successful - the patched .bin can be found\r\n" +
                    $"at {patchedRom}");
            }
            return;
        }
        if (Client == null || Client.ItemState == null || Client.CurrentSession == null) return;
        int openWorldOption = int.Parse(Client.Options?.GetValueOrDefault("enable_open_world", "0").ToString());
        CompletionGoal goal = (CompletionGoal)(int.Parse(Client.Options?.GetValueOrDefault("goal", 0).ToString()));
        Dictionary<string, int> talismans = CalculateCurrentTalismans();
        switch (commandText.ToLower())
        {
            case "!help":
                // This is also a server command, so send the message after.
                string commandsText = "";
                // !help is covered by the server response.
                // commandsText += "!help\r\n\tShow available commands.\r\n";
                commandsText += "!goal\r\n\tShows your current goal and progress towards it.\r\n";
                commandsText += "!options\r\n\tShows important options for your slot.\r\n";
                commandsText += "!unlockedLevels\r\n\tWhen level locks are keys, shows the levels you have unlocked.\r\n";
                commandsText += "!talismans\r\n\tWhen open world is off, shows how many talismans you have received.\r\n";
                commandsText += "!patch\r\n\tCreates a patched version of your vanilla ROM for Archipelago.\r\n\tThis is not seed-specific and is optional.\r\n";
                commandsText += "!reloadItems\r\n\tIn case of a desync, sends all received AP Items again.\r\n\tRequires reconnecting.\r\n";
                commandsText += "!quietHints\r\n\tMakes hints easier to read by hiding items you have already found.\r\n";
                commandsText += "!verboseHints\r\n\tChanges hints to the default archipelago behavior,\r\n\tshowing items you have already found.\r\n";
                commandsText += "!debugInfo\r\n\tPrints information about your game to the screen.\r\n\tYou may be asked to screenshot this if there is an error.\r\n";
                Client?.SendMessage(command.Command);
                await Task.Delay(200);
                Log.Logger.Information(commandsText);
                break;
            case "!options":
                GemsanityOptions gemsanityOption = (GemsanityOptions)int.Parse(Client.Options?.GetValueOrDefault("enable_gemsanity", "0").ToString());
                LevelLockOptions levelLockOption = (LevelLockOptions)int.Parse(Client.Options?.GetValueOrDefault("level_lock_options", "0").ToString());
                TrickDifficultyOptions trickDifficultyOption = (TrickDifficultyOptions)int.Parse(Client.Options?.GetValueOrDefault("trick_difficulty", "0").ToString());
                string worldSettings = openWorldOption != 0 ? "Open World" : "Vanilla Progression";
                string goalString = $"{goal}";
                if (goal == CompletionGoal.Ripto)
                {
                    goalString += $" ({_requiredOrbs} orbs)";
                }
                string optionsString = $"\tGoal: {goalString} - Use !goal for more info\r\n" +
                    $"\tWorld Settings: {worldSettings}\r\n" +
                    $"\tLevel Locks: {levelLockOption}\r\n" +
                    $"\tMoneybagssanity: {_moneybagsOption}\r\n" +
                    $"\tGemsanity: {gemsanityOption}\r\n" +
                    // TODO: Uncomment and support.
                    // $"\tPowerup Locks: {_powerupLockOption}\r\n" +
                    $"\tTrick Difficulty: {trickDifficultyOption}\r\n" +
                    $"\tRipto's Arena Requirement: {_requiredOrbs} orb(s)\r\n";
                Log.Logger.Information($"\r\n{command.Command}\r\n{optionsString}");
                break;
            case "!debuginfo":
                int slot = Client.CurrentSession.ConnectionInfo.Slot;
                Dictionary<string, object> slotData = await Client.CurrentSession.DataStorage.GetSlotDataAsync(slot);
                slotData.TryGetValue("apworldVersion", out var hostVersionValue);
                LevelInGameIDs currentLevel = (LevelInGameIDs)Memory.ReadByte(Addresses.CurrentLevelAddress);
                string debugString = $"\tGame Version: {Helpers.gameVersion}\r\n" +
                    $"\tHost APWorld Version: {hostVersionValue}\r\n" +
                    $"\tClient Version: {Version}\r\n" +
                    $"\tCurrent Level: {currentLevel}\r\n";
                // TODO: Add more information.
                Log.Logger.Information($"\r\n{command.Command}\r\n{debugString}Screenshot this if requested to help debug issues.\r\n");
                break;
            case "clearspyrogamestate":
            case "!reloaditems":
                Log.Logger.Information($"\r\n{command.Command}\r\n" +
                    "\tClearing the game state.  Please reconnect to the server while in game to refresh received items.\r\n");
                Client.ForceReloadAllItems();
                break;
            case "showtalismancount":
            case "!talismans":
                Log.Logger.Information($"\r\n{command.Command}");
                if (openWorldOption != 0)
                {
                    Log.Logger.Information("Talismans are removed in Open World mode.\r\n");
                    break;
                }
                Log.Logger.Information($"Summer Forest: {talismans.GetValueOrDefault("Summer Forest", 0)}; Autumn Plains: {talismans.GetValueOrDefault("Autumn Plains", 0)}\r\n");
                break;
            case "usequiethints":
            case "!quiethints":
                Log.Logger.Information($"\r\n{command.Command}\r\n" +
                    "\tHints for found locations will not be displayed.  Type 'useVerboseHints' to show them.\r\n");
                _useQuietHints = true;
                break;
            case "useverbosehints":
            case "!verbosehints":
                Log.Logger.Information($"\r\n{command.Command}\r\n" +
                    "\tHints for found locations will be displayed.  Type 'useQuietHints' to show them.\r\n");
                _useQuietHints = false;
                break;
            case "showunlockedlevels":
            case "!unlockedlevels":
                Log.Logger.Information($"\r\n{command.Command}");
                showUnlockedLevels(true);
                break;
            case "showgoal":
            case "!goal":
                Log.Logger.Information($"\r\n{command.Command}");
                string goalText = "";
                string progressText = "";
                int orbs = CalculateCurrentOrbs();
                string orbsNeededText = _requiredOrbs == 1 ? $"{_requiredOrbs} orb" : $"{_requiredOrbs} orbs";
                string orbsText = orbs == 1 ? $"{orbs} orb" : $"{orbs} orbs";
                int gems = CalculateCurrentGems();
                string gemsText = gems == 1 ? $"{gems} gem" : $"{gems} gems";
                int talismanCount = talismans.GetValueOrDefault("Total", 0);
                string talismansText = talismanCount == 1 ? $"{talismanCount} talisman" : $"{talismanCount} talismans";
                int tokens = CalculateCurrentTokens();
                string tokensText = tokens == 1 ? $"{tokens} token" : $"{tokens} tokens";
                int skillPoints = CalculateCurrentSkillPoints();
                string skillPointsText = skillPoints == 1 ? $"{skillPoints} Skill Point" : $"{skillPoints} Skill Points";
                bool beatenRipto = Client.CurrentSession?.Items.AllItemsReceived.Any(x => x != null && x.ItemName == "Ripto Defeated") ?? false;
                string defeatedRiptoText = beatenRipto ? "have defeated Ripto" : "have not defeated Ripto";
                switch (goal)
                {
                    case CompletionGoal.Ripto:
                        goalText = $"Defeat Ripto and collect {orbsNeededText}, the requirement to open his arena";
                        progressText = $"You have {orbsText} and {defeatedRiptoText}.";
                        break;
                    case CompletionGoal.SixtyFourOrb:
                        goalText = "Defeat Ripto and collect all 64 orbs";
                        progressText = $"You have {orbsText} and {defeatedRiptoText}.";
                        break;
                    case CompletionGoal.HundredPercent:
                        if (openWorldOption == 0)
                        {
                            goalText = "Defeat Ripto and collect all 14 talismans, 64 orbs, and 10000 gems";
                            progressText = $"You have {talismansText}, {orbsText}, {gemsText},\r\nand {defeatedRiptoText}";
                        }
                        else
                        {
                            goalText = "Defeat Ripto and collect all 64 orbs and 10000 gems";
                            progressText = $"You have {orbsText}, {gemsText}, and {defeatedRiptoText}";
                        }
                        break;
                    case CompletionGoal.TenTokens:
                        goalText = "Collect 55 orbs and 8000 gems to unlock the theme park\r\n" +
                            "and collect all 10 tokens in Dragon Shores";
                        progressText = $"You have {orbsText}, {gemsText}, and {tokensText}";
                        break;
                    case CompletionGoal.AllSkillpoints:
                        goalText = "Collect all 16 skill points";
                        progressText = $"You have {skillPointsText}";
                        break;
                    case CompletionGoal.Epilogue:
                        goalText = "Defeat Ripto and collect all 16 skill points";
                        progressText = $"You have {skillPointsText} and {defeatedRiptoText}";
                        break;
                    default:
                        Log.Logger.Error("Error finding your goal\r\n");
                        return;
                }
                Log.Logger.Information($"\tYour goal is: {goalText}\r\n\t{progressText}\r\n");
                break;
            default:
                Client?.SendMessage(commandText);
                break;
        }
    }
    
    /**
     * Fires when the user clicks the client's connect button.
     * Tries to connect to Duckstation and Archipelago, then set up the session.
     */
    private async void Context_ConnectClicked(object? sender, ConnectClickedEventArgs e)
    {
        // Don't double bind.
        if (Client != null)
        {
            Client.CancelMonitors();
            Client.Connected -= OnConnected;
            Client.Disconnected -= OnDisconnected;
            Client.ItemReceived -= ItemReceived;
            Client.MessageReceived -= Client_MessageReceived;
            Client.LocationCompleted -= Client_LocationCompleted;
            if (Client.CurrentSession != null)
            {
                Client.CurrentSession.Locations.CheckedLocationsUpdated -= Locations_CheckedLocationsUpdated;
            }
            _unlockedLevels = 0;
        }

        // Connect to Duckstation.
        DuckstationClient? client = null;
        try
        {
            client = new DuckstationClient();
        }
        catch (ArgumentException ex)
        {
            Log.Logger.Warning("Duckstation not running, open Duckstation and launch the game before connecting!");
            return;
        }
        var DuckstationConnected = client.Connect();
        if (!DuckstationConnected)
        {
            Log.Logger.Warning("Duckstation not running, open Duckstation and launch the game before connecting!");
            return;
        }
        Client = new ArchipelagoClient(client);

        Memory.GlobalOffset = Memory.GetDuckstationOffset();

        Client.Connected += OnConnected;
        Client.Disconnected += OnDisconnected;

        // Try to connect to the AP server.
        await Client.Connect(e.Host.Trim(), "Spyro 2", "save1");
        if (!Client.IsConnected)
        {
            Log.Logger.Error("Your host seems to be invalid.  Please confirm that you have entered it correctly.");
            return;
        }
        // Set up handlers and variables for the session.
        _cosmeticEffects = new ConcurrentQueue<string>();
        Client.LocationCompleted += Client_LocationCompleted;
        Client.CurrentSession.Locations.CheckedLocationsUpdated += Locations_CheckedLocationsUpdated;
        Client.MessageReceived += Client_MessageReceived;
        Client.ItemReceived += ItemReceived;
        Client.EnableLocationsCondition = () => Helpers.IsInGame();
        // Don't trim password, since leading and trailing whitespace is allowed.
        _playerName = e.Slot.Trim();
        await Client.Login(e.Slot.Trim(), !string.IsNullOrWhiteSpace(e.Password) ? e.Password : null);
        if (Client.Options?.Count > 0)
        {
            GemsanityOptions gemsanityOption = (GemsanityOptions)int.Parse(Client.Options?.GetValueOrDefault("enable_gemsanity", "0").ToString());
            int slot = Client.CurrentSession.ConnectionInfo.Slot;
            Dictionary<string, object> slotData = await Client.CurrentSession.DataStorage.GetSlotDataAsync(slot);
            List<int> gemsanityIDs = new List<int>();
            if (slotData.TryGetValue("gemsanity_ids", out var value))
            {
                if (value != null)
                {
                    gemsanityIDs = System.Text.Json.JsonSerializer.Deserialize<List<int>>(value.ToString());
                }
            }
            // Verify compatibility between the host's version and this client.
            if (slotData.TryGetValue("apworldVersion", out var versionValue))
            {
                if (versionValue != null && SupportedVersions.Contains(versionValue.ToString().ToLower()))
                {
                    Log.Logger.Information($"The host's AP world version is {versionValue.ToString()} and the client version is {Version}.\r\n" +
                        "These versions are known to be compatible.");
                }
                else if (versionValue != null && versionValue.ToString().ToLower() != Version.ToLower())
                {
                    Log.Logger.Warning($"The host's AP world version is {versionValue.ToString()} but the client version is {Version}.\r\n" +
                        "Please ensure these are compatible before proceeding.");
                }
                else if (versionValue == null)
                {
                    Log.Logger.Error($"The host's AP world version predates 1.0.0, but the client version is {Version}.\r\n" +
                        "This will almost certainly result in errors.");
                }
            }
            else
            {
                Log.Logger.Error($"The host's AP world version predates 1.0.0, but the client version is {Version}.\r\n" +
                    "This will almost certainly result in errors.");
            }
            _requiredOrbs = int.Parse(Client.Options?.GetValueOrDefault("ripto_door_orbs", 0).ToString());
            bool easyFracture = int.Parse(Client.Options?.GetValueOrDefault("fracture_easy_earthshapers", 0).ToString()) > 0;

            // Set up the list of locations based on player settings.
            GameLocations = Helpers.BuildLocationList(easyFracture: easyFracture, includeGemsanity: gemsanityOption != GemsanityOptions.Off, gemsanityIDs: gemsanityIDs);
            GameLocations = GameLocations.Where(x => x != null && !Client.CurrentSession.Locations.AllLocationsChecked.Contains(x.Id)).ToList();
            Client.MonitorLocations(GameLocations);
        }
        else
        {
            Log.Logger.Error("Failed to login.  Please check your host, name, and password.");
        }
    }

    /**
     * Fires when a location is checked.
     * This does *not* fire if the location is not in the AP server's list of remaining checks.
     * Therefore, do not rely on it as the only way to fire code, since collect and release can cause it not to trigger.
     */
    private void Client_LocationCompleted(object? sender, LocationCompletedEventArgs e)
    {
        try
        {
            if (Client.ItemState == null || Client.CurrentSession == null) return;
            CalculateCurrentTalismans();
            CalculateCurrentOrbs();
            GemsanityOptions gemsanityOption = (GemsanityOptions)int.Parse(Client.Options?.GetValueOrDefault("enable_gemsanity", "0").ToString());
            if (gemsanityOption != GemsanityOptions.Off)
            {
                CalculateCurrentGems();
            }
            CheckGoalCondition();
        }
        catch (Exception ex)
        {
            Log.Logger.Warning("Encountered an error while completing a location.");
            Log.Logger.Warning(ex.ToString());
            Log.Logger.Warning("This is not necessarily a problem if it happens during release or collect.");
        }
    }

    /**
     * Fires when an item is received.
     * Handle items as they come in, though we largely rely on Client.CurrentSession.Items instead.
     */
    private async void ItemReceived(object? o, ItemReceivedEventArgs args)
    {
        try
        {
            if (Client.ItemState == null || Client.CurrentSession == null) return;
            Log.Logger.Debug($"Item Received: {JsonConvert.SerializeObject(args.Item)}");
            UpdateItemLog();
            // Give items a moment to update before printing values.
            await Task.Delay(200);
            int currentHealth;
            Dictionary<string, int> talismans;
            switch (args.Item.Name)
            {
                case "Summer Forest Talisman":
                    talismans = CalculateCurrentTalismans();
                    Log.Logger.Information($"Current Talisman count - Summer Forest: {talismans.GetValueOrDefault("Summer Forest", 0)}; Autumn Plains: {talismans.GetValueOrDefault("Autumn Plains", 0)}");
                    CheckGoalCondition();
                    break;
                case "Autumn Plains Talisman":
                    talismans = CalculateCurrentTalismans();
                    Log.Logger.Information($"Current Talisman count - Summer Forest: {talismans.GetValueOrDefault("Summer Forest", 0)}; Autumn Plains: {talismans.GetValueOrDefault("Autumn Plains", 0)}");
                    CheckGoalCondition();
                    break;
                case "Orb":
                    CalculateCurrentOrbs();
                    CheckGoalCondition();
                    break;
                case "Skill Point":
                case "Dragon Shores Token":
                case "Ripto Defeated":
                    CheckGoalCondition();
                    break;
                case "Extra Life":
                    var currentLives = Memory.ReadShort(Addresses.PlayerLives);
                    Memory.Write(Addresses.PlayerLives, (short)(Math.Min(99, currentLives + 1)));
                    break;
                case "Heal Sparx":
                    // Collecting a skill point provides a full heal, so wait for that to complete first.
                    await Task.Run(async () =>
                    {
                        await Task.Delay(3000);
                        currentHealth = Memory.ReadByte(Addresses.PlayerHealth);
                        Memory.WriteByte(Addresses.PlayerHealth, (byte)(Math.Min(3, currentHealth + 1)));
                    });
                    break;
                case "Damage Sparx Trap":
                    // Collecting a skill point provides a full heal, so wait for that to complete first.
                    await Task.Run(async () =>
                    {
                        await Task.Delay(3000);
                        currentHealth = Memory.ReadByte(Addresses.PlayerHealth);
                        Memory.WriteByte(Addresses.PlayerHealth, (byte)(Math.Max(currentHealth - 1, 0)));
                    });
                    break;
                case "Sparxless Trap":
                    // Collecting a skill point provides a full heal, so wait for that to complete first.
                    await Task.Run(async () =>
                    {
                        await Task.Delay(3000);
                        Memory.WriteByte(Addresses.PlayerHealth, (byte)(0));
                    });
                    break;
                case "Big Head Mode":
                case "Flat Spyro Mode":
                case "Turn Spyro Red":
                case "Turn Spyro Blue":
                case "Turn Spyro Yellow":
                case "Turn Spyro Pink":
                case "Turn Spyro Green":
                case "Turn Spyro Black":
                case "Normal Spyro":
                    _cosmeticEffects.Enqueue(args.Item.Name);
                    break;
                case "Invisibility Trap":
                    await Task.Run(async () =>
                    {
                        Memory.Write(Addresses.InvisibleAddress1, (short)1);
                        Memory.Write(Addresses.InvisibleAddress2, (short)0x3402);
                        await Task.Delay(15000);
                        Memory.Write(Addresses.InvisibleAddress1, (short)0);
                        Memory.Write(Addresses.InvisibleAddress2, (short)0);
                    });
                    break;
                case "Destructive Spyro":
                    await Task.Run(async () =>
                    {
                        // If effects overlap, this doesn't quite work, but the effect is short enough not to matter.
                        _destructiveMode = true;
                        await Task.Delay(15000);
                        _destructiveMode = false;
                        Log.Logger.Information("Destructive mode has ended.");
                    });
                    break;
                case "Remapped Controller Trap":
                    // This can crash the game, presumably due to changing lines that are being executed.
                    /*await Task.Run(async () =>
                    {
                        Memory.Write(Addresses.AnalogReadAddressOne, 0x3c027f7f); // Set both analog sticks to 0x7f7f, which is off.
                        Memory.Write(Addresses.AnalogReadAddressTwo, 0x34427f7f);
                        Memory.Write(Addresses.ControllerReadLeftHalf, 0x9042a95f); // Swap the left and right half of the controller.
                        Memory.Write(Addresses.ControllerReadRightHalf, 0x9063a95e);
                        await Task.Delay(15000);
                        Memory.Write(Addresses.AnalogReadAddressOne, 0x3c028007); // Correctly load analog stick data.
                        Memory.Write(Addresses.AnalogReadAddressTwo, 0x9063a95e);
                        Memory.Write(Addresses.ControllerReadLeftHalf, 0x9042a95e); // Load the controller halves in the right order.
                        Memory.Write(Addresses.ControllerReadRightHalf, 0x9063a95f);
                    });*/
                    break;
                case "Moneybags Unlock - Crystal Glacier Bridge":
                    if (_moneybagsOption == MoneybagsOptions.Moneybagssanity)
                    {
                        Log.Logger.Information("If you are in the same zone as Moneybags,\r\nyou can talk to him to complete the unlock for free.");
                    }
                    break;
                case "Moneybags Unlock - Aquaria Towers Submarine":
                    if (_moneybagsOption == MoneybagsOptions.Moneybagssanity)
                    {
                        Log.Logger.Information("If you are in the same zone as Moneybags,\r\nyou can talk to him to complete the unlock for free.");
                    }
                    break;
                case "Moneybags Unlock - Magma Cone Elevator":
                    if (_moneybagsOption == MoneybagsOptions.Moneybagssanity)
                    {
                        Log.Logger.Information("If you are in the same zone as Moneybags,\r\nyou can talk to him to complete the unlock for free.");
                    }
                    break;
                case "Moneybags Unlock - Swim":
                    if (
                        _moneybagsOption == MoneybagsOptions.Moneybagssanity ||
                        int.Parse(Client.Options?.GetValueOrDefault("start_with_abilities", "0").ToString()) == 1
                    )
                    {
                        Log.Logger.Information("If you are in the same zone as Moneybags,\r\nyou can talk to him to complete the unlock for free.");
                    }
                    break;
                case "Moneybags Unlock - Climb":
                    if (
                        _moneybagsOption == MoneybagsOptions.Moneybagssanity ||
                        int.Parse(Client.Options?.GetValueOrDefault("start_with_abilities", "0").ToString()) == 1
                    )
                    {
                        Log.Logger.Information("If you are in the same zone as Moneybags,\r\nyou can talk to him to complete the unlock for free.");
                    }
                    break;
                case "Moneybags Unlock - Headbash":
                    if (
                        _moneybagsOption == MoneybagsOptions.Moneybagssanity ||
                        int.Parse(Client.Options?.GetValueOrDefault("start_with_abilities", "0").ToString()) == 1
                    )
                    {
                        Log.Logger.Information("If you are in the same zone as Moneybags,\r\nyou can talk to him to complete the unlock for free.");
                    }
                    break;
                case "Moneybags Unlock - Door to Aquaria Towers":
                case "Moneybags Unlock - Wall by Aquaria Towers":
                    if (_moneybagsOption == MoneybagsOptions.Moneybagssanity)
                    {
                        Log.Logger.Information("If you are in the same zone as Moneybags,\r\nyou can talk to him to complete the unlock for free.");
                    }
                    break;
                case "Moneybags Unlock - Zephyr Portal":
                    if (_moneybagsOption == MoneybagsOptions.Moneybagssanity)
                    {
                        Log.Logger.Information("If you are in the same zone as Moneybags,\r\nyou can talk to him to complete the unlock for free.");
                    }
                    break;
                case "Moneybags Unlock - Shady Oasis Portal":
                    if (_moneybagsOption == MoneybagsOptions.Moneybagssanity)
                    {
                        Log.Logger.Information("If you are in the same zone as Moneybags,\r\nyou can talk to him to complete the unlock for free.");
                    }
                    break;
                case "Moneybags Unlock - Icy Speedway Portal":
                    if (_moneybagsOption == MoneybagsOptions.Moneybagssanity)
                    {
                        Log.Logger.Information("If you are in the same zone as Moneybags,\r\nyou can talk to him to complete the unlock for free.");
                    }
                    break;
                case "Moneybags Unlock - Canyon Speedway Portal":
                    if (_moneybagsOption == MoneybagsOptions.Moneybagssanity)
                    {
                        Log.Logger.Information("If you are in the same zone as Moneybags,\r\nyou can talk to him to complete the unlock for free.");
                    }
                    break;
                case "Progressive Sparx Health Upgrade":
                    _sparxUpgrades++;
                    break;
                case "Double Jump Ability":
                case "Permanent Fireball Ability":
                    // Managed by HandleAbilities()
                    break;
                default:
                    if (args.Item.Name.EndsWith(" Gem") || args.Item.Name.EndsWith(" Gems"))
                    {
                        CalculateCurrentGems();
                        CheckGoalCondition();
                    }
                    else if (args.Item.Name.EndsWith(" Unlock"))
                    {
                        switch (args.Item.Name)
                        {
                            case "Idol Springs Unlock":
                                WriteStringToMemory(Addresses.IdolNameAddress, Addresses.IdolNameAddress + 16, "Idol Springs", padWithSpaces: false);
                                break;
                            case "Colossus Unlock":
                                WriteStringToMemory(Addresses.ColossusNameAddress, Addresses.ColossusNameAddress + 12, "Colossus", padWithSpaces: false);
                                break;
                            case "Hurricos Unlock":
                                WriteStringToMemory(Addresses.HurricosNameAddress, Addresses.HurricosNameAddress + 12, "Hurricos", padWithSpaces: false);
                                break;
                            case "Aquaria Towers Unlock":
                                WriteStringToMemory(Addresses.AquariaNameAddress, Addresses.AquariaNameAddress + 16, "Aquaria Towers", padWithSpaces: false);
                                break;
                            case "Sunny Beach Unlock":
                                WriteStringToMemory(Addresses.SunnyNameAddress, Addresses.SunnyNameAddress + 12, "Sunny Beach", padWithSpaces: false);
                                break;
                            case "Ocean Speedway Unlock":
                                WriteStringToMemory(Addresses.OceanNameAddress, Addresses.OceanNameAddress + 16, "Ocean Speedway", padWithSpaces: false);
                                break;
                            case "Skelos Badlands Unlock":
                                WriteStringToMemory(Addresses.SkelosNameAddress, Addresses.SkelosNameAddress + 16, "Skelos Badlands", padWithSpaces: false);
                                break;
                            case "Crystal Glacier Unlock":
                                WriteStringToMemory(Addresses.CrystalNameAddress, Addresses.CrystalNameAddress + 16, "Crystal Glacier", padWithSpaces: false);
                                break;
                            case "Breeze Harbor Unlock":
                                WriteStringToMemory(Addresses.BreezeNameAddress, Addresses.BreezeNameAddress + 16, "Breeze Harbor", padWithSpaces: false);
                                break;
                            case "Zephyr Unlock":
                                WriteStringToMemory(Addresses.ZephyrNameAddress, Addresses.ZephyrNameAddress + 8, "Zephyr", padWithSpaces: false);
                                break;
                            case "Metro Speedway Unlock":
                                WriteStringToMemory(Addresses.MetroNameAddress, Addresses.MetroNameAddress + 16, "Metro Speedway", padWithSpaces: false);
                                break;
                            case "Scorch Unlock":
                                WriteStringToMemory(Addresses.ScorchNameAddress, Addresses.ScorchNameAddress + 8, "Scorch", padWithSpaces: false);
                                break;
                            case "Shady Oasis Unlock":
                                WriteStringToMemory(Addresses.ShadyNameAddress, Addresses.ShadyNameAddress + 12, "Shady Oasis", padWithSpaces: false);
                                break;
                            case "Magma Cone Unlock":
                                WriteStringToMemory(Addresses.MagmaNameAddress, Addresses.MagmaNameAddress + 12, "Magma Cone", padWithSpaces: false);
                                break;
                            case "Fracture Hills Unlock":
                                WriteStringToMemory(Addresses.FractureNameAddress, Addresses.FractureNameAddress + 16, "Fracture Hills", padWithSpaces: false);
                                break;
                            case "Icy Speedway Unlock":
                                WriteStringToMemory(Addresses.IcyNameAddress, Addresses.IcyNameAddress + 16, "Icy Speedway", padWithSpaces: false);
                                break;
                            case "Mystic Marsh Unlock":
                                WriteStringToMemory(Addresses.MysticNameAddress, Addresses.MysticNameAddress + 16, "Mystic Marsh", padWithSpaces: false);
                                break;
                            case "Cloud Temples Unlock":
                                WriteStringToMemory(Addresses.CloudNameAddress, Addresses.CloudNameAddress + 16, "Cloud Temples", padWithSpaces: false);
                                break;
                            case "Canyon Speedway Unlock":
                                WriteStringToMemory(Addresses.CanyonNameAddress, Addresses.CanyonNameAddress + 16, "Canyon Speedway", padWithSpaces: false);
                                break;
                            case "Robotica Farms Unlock":
                                WriteStringToMemory(Addresses.RoboticaNameAddress, Addresses.RoboticaNameAddress + 16, "Robotica Farms", padWithSpaces: false);
                                break;
                            case "Metropolis Unlock":
                                WriteStringToMemory(Addresses.MetropolisNameAddress, Addresses.MetropolisNameAddress + 12, "Metropolis", padWithSpaces: false);
                                break;
                            case "Dragon Shores Unlock":
                                WriteStringToMemory(Addresses.ShoresNameAddress, Addresses.ShoresNameAddress + 16, "Dragon Shores", padWithSpaces: false);
                                break;
                        }
                        // Other unlock effects managed by HandleAbilities().
                        showUnlockedLevels();
                    }
                    break;
            }
        }
        catch (Exception ex)
        {
            Log.Logger.Warning("Encountered an error while receiving an item.\r\n" +
                ex.ToString() + "\r\n");
        }
    }
    
    /**
     * Displays to the user the list of levels they have keys for, if applicable.
     * 
     * @param alwaysShow If true, will always print the list. Otherwise, only does so when a new level has been unlocked.
     */
    private void showUnlockedLevels(bool alwaysShow = false)
    {
        LevelLockOptions levelLockOption = (LevelLockOptions)int.Parse(Client.Options?.GetValueOrDefault("level_lock_options", "0").ToString());
        if (levelLockOption == LevelLockOptions.Vanilla)
        {
            Log.Logger.Information("Levels have their vanilla unlock requirements.");
        }
        else if (levelLockOption != LevelLockOptions.Keys)
        {
            // TODO: Revisit this message when orb locks are added.
            Log.Logger.Information("Levels are not locked by keys.");
        }
        List<ItemInfo> unlockedLevels = (Client.CurrentSession?.Items.AllItemsReceived.Where(x => x.ItemName.EndsWith(" Unlock")).ToList() ?? new List<ItemInfo>());
        if (alwaysShow || unlockedLevels.Count > _unlockedLevels)
        {
            _unlockedLevels = unlockedLevels.Count;
        }
        else
        {
            return;
        }
        if (unlockedLevels.Count >= int.Parse(Client.Options?.GetValueOrDefault("level_unlocks", "0").ToString()))
        {
            string unlockedLevelsString = "You have unlocked:";
            int levelCount = 0;
            foreach (ItemInfo unlockedLevel in unlockedLevels)
            {
                string newLevel;
                if (unlockedLevel.ItemName == "Dragon Shores Unlock")
                {
                    newLevel = "Shores";
                }
                else
                {
                    newLevel = unlockedLevel.ItemName.Split(" Unlock")[0].Split(" ")[0];
                }
                levelCount++;
                // Print 6 per line so it is easier to read.
                if (levelCount % 6 == 1)
                {
                    unlockedLevelsString += "\r\n";
                }
                unlockedLevelsString += (newLevel + "; ");
            }
            if (unlockedLevelsString != "You have unlocked:")
            {
                unlockedLevelsString = unlockedLevelsString.Substring(0, unlockedLevelsString.Length - 2);
            }
            else
            {
                unlockedLevelsString += "\r\nNo levels yet";
            }
            Log.Logger.Information($"{unlockedLevelsString}\r\n");
        }
    }
    
    /**
     * Function repeatedly called by a timer that affects gameplay and goaling.
     * Despite the name, affects more than just abilities.
     */
    private static async void HandleAbilities(object source, ElapsedEventArgs e)
    {
        // TODO: Clean this up, like S3.
        try
        {
            if (!Helpers.IsInGame() || Client.ItemState == null || Client.CurrentSession == null)
            {
                return;
            }
            CalculateCurrentTalismans();
            CalculateCurrentOrbs();
            GemsanityOptions gemsanityOption = (GemsanityOptions)int.Parse(Client.Options?.GetValueOrDefault("enable_gemsanity", "0").ToString());
            if (gemsanityOption != GemsanityOptions.Off)
            {
                CalculateCurrentGems();
            }
            HandleMoneybagsUnlocks();
            HandleInnerWTWarpAccess();
            CheckGoalCondition();
            byte lifeCount = Memory.ReadByte(Addresses.PlayerLives);
            AbilityOptions doubleJumpOption = (AbilityOptions)int.Parse(Client.Options?.GetValueOrDefault("double_jump_ability", "0").ToString());
            int hasDoubleJumpItem = (byte)(Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == "Double Jump Ability").Count() ?? 0);
            AbilityOptions fireballOption = (AbilityOptions)int.Parse(Client.Options?.GetValueOrDefault("permanent_fireball_ability", "0").ToString());
            int hasFireballItem = (byte)(Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == "Permanent Fireball Ability").Count() ?? 0);

            if (doubleJumpOption == AbilityOptions.AlwaysOff || doubleJumpOption == AbilityOptions.InPool && hasDoubleJumpItem == 0)
            {
                Memory.Write(Addresses.DoubleJumpAddress1, 0x2402FE00);
                Memory.Write(Addresses.DoubleJumpAddress2, 0xAC22A08C);
            }
            else
            {
                Memory.Write(Addresses.DoubleJumpAddress1, 0x24020800);
                Memory.Write(Addresses.DoubleJumpAddress2, 0xAC22A0A8);
            }

            if (fireballOption == AbilityOptions.AlwaysOff || fireballOption == AbilityOptions.InPool && hasFireballItem == 0)
            {
                Memory.WriteByte(Addresses.PermanentFireballAddress, (byte)0);
            }
            else if (fireballOption == AbilityOptions.StartWith || fireballOption == AbilityOptions.InPool && hasFireballItem == 1)
            {
                Memory.WriteByte(Addresses.PermanentFireballAddress, (byte)1);
            } // else vanilla behavior, controlled by game.

            if (_destructiveMode)
            {
                // TODO: This is buggy.
                // Probably need to temporarily overwrite changes to this halfword elsewhere too.
                Memory.Write(Addresses.DestructiveSpyroAddress, (short)0xFF);
            } // Turns off automatically on its own.

            LevelInGameIDs currentLevel = (LevelInGameIDs)Memory.ReadByte(Addresses.CurrentLevelAddress);
            if (currentLevel != _previousLevel && _handleGemsanity)
            {
                Helpers.UpdateLocationList(currentLevel, Client);
            }
            GameStatus gameStatus = (GameStatus)Memory.ReadByte(Addresses.GameStatus);
            if (_deathLinkService != null && !_hasSubmittedGoal)
            {
                byte health = Memory.ReadByte(Addresses.PlayerHealth);
                int zPos = Memory.ReadInt(Addresses.PlayerZPos);
                int animationLength = Memory.ReadInt(Addresses.PlayerAnimationLength);
                byte spyroState = Memory.ReadByte(Addresses.SpyroStateAddress);
                byte spyroVelocityFlag = Memory.ReadByte(Addresses.PlayerVelocityStatus);
                LevelInGameIDs[] deathLinkLevels = [
                    LevelInGameIDs.SummerForest,
                LevelInGameIDs.Glimmer,
                LevelInGameIDs.Colossus,
                LevelInGameIDs.IdolSprings,
                LevelInGameIDs.Hurricos,
                LevelInGameIDs.SunnyBeach,
                LevelInGameIDs.AquariaTowers,
                LevelInGameIDs.CrushsDungeon,
                LevelInGameIDs.AutumnPlains,
                LevelInGameIDs.BreezeHarbor,
                LevelInGameIDs.SkelosBadlands,
                LevelInGameIDs.CrystalGlacier,
                LevelInGameIDs.Zephyr,
                LevelInGameIDs.Scorch,
                LevelInGameIDs.FractureHills,
                LevelInGameIDs.MagmaCone,
                LevelInGameIDs.ShadyOasis,
                LevelInGameIDs.GulpsOverlook,
                LevelInGameIDs.WinterTundra,
                LevelInGameIDs.MysticMarsh,
                LevelInGameIDs.CloudTemples,
                LevelInGameIDs.RoboticaFarms,
                LevelInGameIDs.Metropolis,
                LevelInGameIDs.RiptosArena
                ];

                if (
                    !_justDied &&
                    Helpers.IsInGame() &&
                    Client.ItemState != null &&
                    Client.CurrentSession != null &&
                    deathLinkLevels.Contains(currentLevel) &&
                    gameStatus != GameStatus.Cutscene &&
                    gameStatus != GameStatus.Loading &&
                    gameStatus != GameStatus.TitleScreen &&
                    (
                        health > 128 ||
                        (zPos > 0 && zPos < 0x400) ||  // zPos is 0 on initial load into a save
                        (spyroState == (byte)SpyroStates.Flop && spyroVelocityFlag == 1 && 0x3b < animationLength) ||
                        spyroState == (byte)SpyroStates.DeathBurn ||
                        spyroState == (byte)SpyroStates.DeathDrowning && animationLength >= 116 ||
                        spyroState == (byte)SpyroStates.DeathSquash
                    )
                )
                {
                    _justDied = true;
                    string deathlinkCause = "Unknown";
                    if (health > 128)
                    {
                        deathlinkCause = "Damage";
                    }
                    else if (zPos > 0 && zPos < 0x400)
                    {
                        deathlinkCause = "Fell below death plane";
                    }
                    else if (spyroState == (byte)SpyroStates.Flop && spyroVelocityFlag == 1 && 0x3b < animationLength)
                    {
                        deathlinkCause = "Fell to death";
                    }
                    else if (spyroState == (byte)SpyroStates.DeathBurn)
                    {
                        deathlinkCause = "Burned";
                    }
                    else if (spyroState == (byte)SpyroStates.DeathDrowning && animationLength >= 116)
                    {
                        deathlinkCause = "Drowned";
                    }
                    else if (spyroState == (byte)SpyroStates.DeathSquash)
                    {
                        deathlinkCause = "Squashed";
                    }
                    Log.Logger.Information($"Sending DeathLink. Cause: {deathlinkCause}");
                    if (deathlinkCause == "Unknown")
                    {
                        deathlinkCause = Client.CurrentSession.Players.ActivePlayer.Name + " died in Spyro 2.";
                    }
                    else
                    {
                        deathlinkCause = Client.CurrentSession.Players.ActivePlayer.Name + $" died in Spyro 2: {deathlinkCause}";
                    }
                    _deathLinkService.SendDeathLink(new DeathLink(Client.CurrentSession.Players.ActivePlayer.Name, cause: deathlinkCause));
                }
                else if (_justDied &&
                    !(
                        health > 128 ||
                        zPos < 0x400 ||
                        (spyroState == (byte)SpyroStates.Flop && spyroVelocityFlag == 1 && 0x3b < animationLength) ||
                        spyroState == (byte)SpyroStates.DeathBurn ||
                        spyroState == (byte)SpyroStates.DeathDrowning && animationLength >= 116 ||
                        spyroState == (byte)SpyroStates.DeathSquash
                    )
                )
                {
                    _justDied = false;
                    _justReceivedDeathLink = false;
                }
            }

            if (gameStatus != GameStatus.Paused && gameStatus != GameStatus.LoadingWorld)
            {
                if (gemsanityOption != GemsanityOptions.Off)
                {
                    // Disable updating local and global gem counts on collecting a gem, loading into a level, and respawning.
                    Memory.Write(Addresses.localGemIncrementAddress, 0);
                    Memory.Write(Addresses.globalGemIncrementAddress, 0);
                    Memory.Write(Addresses.globalGemRespawnFixAddress, 0);
                    Memory.Write(Addresses.localGemRespawnFixAddress, 0);
                    Memory.Write(Addresses.playBeepAddress, 0);
                    // Only apply these during the correct overlays.
                    // Probably easier to just patch.
                    //Memory.Write(Addresses.localGemLoadFixAddress, 0);
                    //Memory.Write(Addresses.globalGemLoadFixAddress, 0);
                }
                if (currentLevel == LevelInGameIDs.Colossus)
                {
                    int startingGoals = int.Parse(Client.Options?.GetValueOrDefault("colossus_starting_goals", "0").ToString());
                    int currentGoals = (int)Memory.ReadByte(Addresses.ColossusSpyroHockeyScore);
                    if (currentGoals < startingGoals)
                    {
                        Memory.WriteByte(Addresses.ColossusSpyroHockeyScore, (byte)startingGoals);
                        Memory.WriteByte(Addresses.spyroHUDScore, (byte)startingGoals);
                    }
                }
                else if (currentLevel == LevelInGameIDs.IdolSprings)
                {
                    bool easyFish = int.Parse(Client.Options?.GetValueOrDefault("idol_easy_fish", "0").ToString()) > 0;
                    if (easyFish)
                    {
                        Memory.Write(Addresses.IdolFishThrowUp, 0x0802080c);
                        Memory.Write(Addresses.IdolFishIncludeReds, 0x28820006);
                        Memory.Write(Addresses.IdolFishIncludeRedsHUD, 0x28a20006);
                    }
                }
                else if (currentLevel == LevelInGameIDs.Hurricos)
                {
                    bool easyLightningOrbs = int.Parse(Client.Options?.GetValueOrDefault("hurricos_easy_lightning_orbs", "0").ToString()) > 0;
                    if (easyLightningOrbs)
                    {
                        foreach (uint thiefStatus in Addresses.HurricosLightningThiefStatuses)
                        {
                            Memory.WriteByte(thiefStatus, 253);
                        }
                        foreach (uint thiefZCoordinate in Addresses.HurricosLightningThiefZCoordinates)
                        {
                            Memory.Write(thiefZCoordinate, 0);
                        }
                    }
                }
                else if (currentLevel == LevelInGameIDs.BreezeHarbor)
                {
                    int requiredGears = int.Parse(Client.Options?.GetValueOrDefault("breeze_required_gears", "0").ToString());
                    int currentGears = (int)Memory.ReadByte(Addresses.spyroHUDScore);
                    if (currentGears > 50)
                    {
                        Memory.WriteByte(Addresses.spyroHUDScore, 50);
                    }
                    else if (currentGears < 50 - requiredGears)
                    {
                        Memory.WriteByte(Addresses.spyroHUDScore, (byte)(50 - requiredGears));
                    }
                }
                else if (currentLevel == LevelInGameIDs.Scorch)
                {
                    // Nothing ever goes wrong in Scorch : )
                    BomboOptions bomboSettings = (BomboOptions)int.Parse(Client.Options?.GetValueOrDefault("scorch_bombo_settings", "0").ToString());
                    if (bomboSettings == BomboOptions.FirstOnly)
                    {
                        // Mark the other two bombos as complete, and move their models out of rendering range.
                        // Otherwise, their models appear on the flagpoles.
                        // -0x35 is the offset from status to z coordinate
                        Memory.WriteByte(Addresses.secondBomboStatus, 11);
                        Memory.Write(Addresses.secondBomboStatus - 0x35, 100000);
                        Memory.WriteByte(Addresses.thirdBomboStatus, 11);
                        Memory.Write(Addresses.thirdBomboStatus - 0x35, 100000);
                    }
                    else if (bomboSettings == BomboOptions.FirstOnlyNoAttack)
                    {
                        Memory.WriteByte(Addresses.secondBomboStatus, 11);
                        Memory.Write(Addresses.secondBomboStatus - 0x35, 100000);
                        Memory.WriteByte(Addresses.thirdBomboStatus, 11);
                        Memory.Write(Addresses.thirdBomboStatus - 0x35, 100000);
                        Memory.Write(Addresses.bomboAttackAddress, 0x0801E71E);
                    }
                }
                else if (currentLevel == LevelInGameIDs.FractureHills)
                {
                    bool requireHeadbash = int.Parse(Client.Options?.GetValueOrDefault("fracture_require_headbash", "0").ToString()) > 0;
                    bool easyEarthshapers = int.Parse(Client.Options?.GetValueOrDefault("fracture_easy_earthshapers", "0").ToString()) > 0;
                    if (!requireHeadbash)
                    {
                        Memory.Write(Addresses.fractureHeadbashCheck, 0x0801E2A5);
                    }
                    if (easyEarthshapers)
                    {
                        foreach (uint earthshaperStatus in Addresses.FractureEarthshaperStatuses)
                        {
                            Memory.WriteByte(earthshaperStatus, 253);
                        }
                        foreach (uint earthshaperZCoordinate in Addresses.FractureEarthshaperZCoordinates)
                        {
                            Memory.Write(earthshaperZCoordinate, 0);
                        }
                        Memory.WriteByte(Addresses.maxFractureSpiritParticles, 22);
                    }
                }
                else if (currentLevel == LevelInGameIDs.MagmaCone)
                {
                    int spyroStartingScore = int.Parse(Client.Options?.GetValueOrDefault("magma_spyro_starting_popcorn", "0").ToString());
                    int hunterStartingScore = int.Parse(Client.Options?.GetValueOrDefault("magma_hunter_starting_popcorn", "0").ToString());
                    int spyroScore = Memory.ReadByte(Addresses.spyroHUDScore);
                    int hunterScore = Memory.ReadByte(Addresses.opponentHUDScore);
                    if (spyroScore < spyroStartingScore)
                    {
                        Memory.WriteByte(Addresses.spyroHUDScore, (byte)spyroStartingScore);
                    }
                    if (hunterScore < hunterStartingScore)
                    {
                        Memory.WriteByte(Addresses.opponentHUDScore, (byte)hunterStartingScore);
                    }
                }
                else if (currentLevel == LevelInGameIDs.ShadyOasis)
                {
                    bool requireHeadbash = int.Parse(Client.Options?.GetValueOrDefault("shady_require_headbash", "0").ToString()) > 0;
                    if (!requireHeadbash)
                    {
                        Memory.Write(Addresses.ShadyHeadbashCheck, 0x00000000);
                    }
                }
                else if (currentLevel == LevelInGameIDs.GulpsOverlook)
                {
                    bool easyGulp = int.Parse(Client.Options?.GetValueOrDefault("easy_gulp", "0").ToString()) > 0;
                    if (easyGulp)
                    {
                        Memory.WriteByte(Addresses.GulpDoubleDamage, 1);
                    }
                }
                // Exiting from WT and loading a save could crash the game with bad timing without the gameStatus check.
                else if (currentLevel == LevelInGameIDs.WinterTundra && gameStatus != GameStatus.GameLoadMaybe)
                {
                    Memory.WriteByte(Addresses.RiptoDoorOrbRequirementAddress, (byte)_requiredOrbs);
                    Memory.WriteByte(Addresses.RiptoDoorOrbDisplayAddress, (byte)_requiredOrbs);
                }
                LevelLockOptions levelLockOption = (LevelLockOptions)int.Parse(Client.Options?.GetValueOrDefault("level_lock_options", "0").ToString());
                if (levelLockOption == LevelLockOptions.Keys)
                {
                    if (currentLevel == LevelInGameIDs.SummerForest)
                    {
                        bool isIdolUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Idol Springs Unlock")).Count() ?? 0) > 0;
                        bool isColossusUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Colossus Unlock")).Count() ?? 0) > 0;
                        bool isHurricosUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Hurricos Unlock")).Count() ?? 0) > 0;
                        bool isAquariaUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Aquaria Towers Unlock")).Count() ?? 0) > 0;
                        bool isSunnyUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Sunny Beach Unlock")).Count() ?? 0) > 0;
                        bool isOceanUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Ocean Speedway Unlock")).Count() ?? 0) > 0;
                        bool[] summerUnlocks = [
                            isIdolUnlocked,
                        isColossusUnlocked,
                        isHurricosUnlocked,
                        isAquariaUnlocked,
                        isSunnyUnlocked,
                        isOceanUnlocked
                        ];
                        // Glimmer is always unlocked.
                        uint portalAddress = Addresses.SummerPortalBlock + 8;
                        foreach (bool isUnlocked in summerUnlocks)
                        {
                            if (isUnlocked)
                            {
                                Memory.Write(portalAddress, 6);
                            }
                            else
                            {
                                Memory.Write(portalAddress, 0);
                            }
                            portalAddress += 8;
                        }
                    }
                    else if (currentLevel == LevelInGameIDs.AutumnPlains)
                    {
                        bool isSkelosUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Skelos Badlands Unlock")).Count() ?? 0) > 0;
                        bool isCrystalUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Crystal Glacier Unlock")).Count() ?? 0) > 0;
                        bool isBreezeUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Breeze Harbor Unlock")).Count() ?? 0) > 0;
                        bool isZephyrUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Zephyr Unlock")).Count() ?? 0) > 0;
                        bool isMetroUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Metro Speedway Unlock")).Count() ?? 0) > 0;
                        bool isScorchUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Scorch Unlock")).Count() ?? 0) > 0;
                        bool isShadyUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Shady Oasis Unlock")).Count() ?? 0) > 0;
                        bool isMagmaUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Magma Cone Unlock")).Count() ?? 0) > 0;
                        bool isFractureUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Fracture Hills Unlock")).Count() ?? 0) > 0;
                        bool isIcyUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Icy Speedway Unlock")).Count() ?? 0) > 0;
                        bool[] autumnUnlocks = [
                            isSkelosUnlocked,
                        isCrystalUnlocked,
                        isBreezeUnlocked,
                        isZephyrUnlocked,
                        isMetroUnlocked,
                        isScorchUnlocked,
                        isShadyUnlocked,
                        isMagmaUnlocked,
                        isFractureUnlocked,
                        isIcyUnlocked
                        ];
                        uint portalAddress = Addresses.AutumnPortalBlock;
                        foreach (bool isUnlocked in autumnUnlocks)
                        {
                            if (isUnlocked)
                            {
                                Memory.Write(portalAddress, 6);
                            }
                            else
                            {
                                Memory.Write(portalAddress, 0);
                            }
                            portalAddress += 8;
                        }
                    }
                    else if (currentLevel == LevelInGameIDs.WinterTundra)
                    {
                        bool isMysticUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Mystic Marsh Unlock")).Count() ?? 0) > 0;
                        bool isCloudUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Cloud Temples Unlock")).Count() ?? 0) > 0;
                        bool isCanyonUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Canyon Speedway Unlock")).Count() ?? 0) > 0;
                        bool isRoboticaUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Robotica Farms Unlock")).Count() ?? 0) > 0;
                        bool isMetropolisUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Metropolis Unlock")).Count() ?? 0) > 0;
                        bool isDragonShoresUnlocked = (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == ("Dragon Shores Unlock")).Count() ?? 0) > 0;
                        // This order does not match the index order, for whatever reason.
                        bool[] winterUnlocks = [
                            isMysticUnlocked,
                        isCloudUnlocked,
                        isRoboticaUnlocked,
                        isMetropolisUnlocked,
                        isCanyonUnlocked,
                        isDragonShoresUnlocked
                        ];
                        uint portalAddress = Addresses.WinterPortalBlock;
                        foreach (bool isUnlocked in winterUnlocks)
                        {
                            if (isUnlocked)
                            {
                                Memory.Write(portalAddress, 6);
                            }
                            else
                            {
                                Memory.Write(portalAddress, 0);
                            }
                            portalAddress += 8;
                        }
                    }
                }
            }

            _previousLifeCount = lifeCount;
            _previousLevel = currentLevel;
        }
        catch (Exception ex)
        {
            Log.Logger.Warning("Encountered an error while managing the game loop.\r\n" +
                $"{ex.ToString()}");
        }
    }
    
    /**
     * Handles the Sparx health upgrades within the game loop.
     */
    private static async void HandleMaxSparxHealth(object source, ElapsedEventArgs e)
    {
        if (!Helpers.IsInGame() || Client.ItemState == null || Client.CurrentSession == null)
        {
            return;
        }
        byte currentHealth = Memory.ReadByte(Addresses.PlayerHealth);
        // Don't adjust negative health, which breaks deathlink.
        if (currentHealth <= 128 && currentHealth > _sparxUpgrades)
        {
            Memory.WriteByte(Addresses.PlayerHealth, _sparxUpgrades);
        }
        if (_sparxUpgrades == 3)
        {
            _sparxTimer.Enabled = false;
        }
    }
    
    /**
     * Changes Spyro's color and big head mode, if there are any queued effects.
     * 
     * Also handles gem cosmetics and level lock options, which would be better moved elsewhere.
     */
    private static async void HandleCosmeticQueue(object source, ElapsedEventArgs e)
    {
        // TODO: Reorganize this function.
        if (Client.ItemState == null || Client.CurrentSession == null) return;
        CheckGoalCondition();
        // Avoid overwhelming the game when many cosmetic effects are received at once by processing only 1
        // every 5 seconds.  This also lets the user see effects when logging in asynchronously.
        // TODO: Handle this on game reset as well.
        int openWorldOption = int.Parse(Client.Options?.GetValueOrDefault("enable_open_world", "0").ToString());
        if (openWorldOption != 0)
        {
            Memory.WriteByte(Addresses.CrushGuidebookUnlock, 1);
            Memory.WriteByte(Addresses.GulpGuidebookUnlock, 1);
            if (int.Parse(Client.Options?.GetValueOrDefault("open_world_warp_unlocks", "0").ToString()) != 0)
            {
                Memory.WriteByte(Addresses.AutumnGuidebookUnlock, 1);
                Memory.WriteByte(Addresses.WinterGuidebookUnlock, 1);
            }
        }
        LevelLockOptions levelLockOptions = (LevelLockOptions)int.Parse(Client.Options?.GetValueOrDefault("level_lock_options", "0").ToString());
        if (levelLockOptions == LevelLockOptions.Keys)
        {
            Dictionary<string, uint[]> levelNames = new Dictionary<string, uint[]>()
            {
                { "Idol Springs", [Addresses.IdolNameAddress, Addresses.IdolNameAddress + 16] },
                { "Colossus", [Addresses.ColossusNameAddress, Addresses.ColossusNameAddress + 12] },
                { "Hurricos", [Addresses.HurricosNameAddress, Addresses.HurricosNameAddress + 12] },
                { "Aquaria Towers", [Addresses.AquariaNameAddress, Addresses.AquariaNameAddress + 16] },
                { "Sunny Beach", [Addresses.SunnyNameAddress, Addresses.SunnyNameAddress + 12] },
                { "Ocean Speedway", [Addresses.OceanNameAddress, Addresses.OceanNameAddress + 16] },
                { "Skelos Badlands", [Addresses.SkelosNameAddress, Addresses.SkelosNameAddress + 16] },
                { "Crystal Glacier", [Addresses.CrystalNameAddress, Addresses.CrystalNameAddress + 16] },
                { "Breeze Harbor", [Addresses.BreezeNameAddress, Addresses.BreezeNameAddress + 16] },
                { "Zephyr", [Addresses.ZephyrNameAddress, Addresses.ZephyrNameAddress + 8] },
                { "Metro Speedway", [Addresses.MetroNameAddress, Addresses.MetroNameAddress + 16] },
                { "Scorch", [Addresses.ScorchNameAddress, Addresses.ScorchNameAddress + 8] },
                { "Shady Oasis", [Addresses.ShadyNameAddress, Addresses.ShadyNameAddress + 12] },
                { "Magma Cone", [Addresses.MagmaNameAddress, Addresses.MagmaNameAddress + 12] },
                { "Fracture Hills", [Addresses.FractureNameAddress, Addresses.FractureNameAddress + 16] },
                { "Icy Speedway", [Addresses.IcyNameAddress, Addresses.IcyNameAddress + 16] },
                { "Mystic Marsh", [Addresses.MysticNameAddress, Addresses.MysticNameAddress + 16] },
                { "Cloud Temples", [Addresses.CloudNameAddress, Addresses.CloudNameAddress + 16] },
                { "Canyon Speedway", [Addresses.CanyonNameAddress, Addresses.CanyonNameAddress + 16] },
                { "Robotica Farms", [Addresses.RoboticaNameAddress, Addresses.RoboticaNameAddress + 16] },
                { "Metropolis", [Addresses.MetropolisNameAddress, Addresses.MetropolisNameAddress + 12] },
                { "Dragon Shores", [Addresses.ShoresNameAddress, Addresses.ShoresNameAddress + 16] }
            };
            foreach (string levelName in levelNames.Keys)
            {
                uint[] nameAddresses = levelNames[levelName];
                if ((Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == $"{levelName} Unlock").Count() ?? 0) == 0)
                {
                    WriteStringToMemory(nameAddresses[0], nameAddresses[1], "LOCKED", padWithSpaces: false);
                }
                else
                {
                    WriteStringToMemory(nameAddresses[0], nameAddresses[1], levelName, padWithSpaces: false);
                }
            }
        }
        Memory.Write(Addresses.RedGemShadow, int.Parse(Client.Options?.GetValueOrDefault("red_gem_shadow_color", "0").ToString()));
        Memory.Write(Addresses.RedGemColor, int.Parse(Client.Options?.GetValueOrDefault("red_gem_color", "0").ToString()));
        Memory.Write(Addresses.GreenGemShadow, int.Parse(Client.Options?.GetValueOrDefault("green_gem_shadow_color", "0").ToString()));
        Memory.Write(Addresses.GreenGemColor, int.Parse(Client.Options?.GetValueOrDefault("green_gem_color", "0").ToString()));
        Memory.Write(Addresses.BlueGemShadow, int.Parse(Client.Options?.GetValueOrDefault("blue_gem_shadow_color", "0").ToString()));
        Memory.Write(Addresses.BlueGemColor, int.Parse(Client.Options?.GetValueOrDefault("blue_gem_color", "0").ToString()));
        Memory.Write(Addresses.GoldGemShadow, int.Parse(Client.Options?.GetValueOrDefault("gold_gem_shadow_color", "0").ToString()));
        Memory.Write(Addresses.GoldGemColor, int.Parse(Client.Options?.GetValueOrDefault("gold_gem_color", "0").ToString()));
        Memory.Write(Addresses.PinkGemShadow, int.Parse(Client.Options?.GetValueOrDefault("pink_gem_shadow_color", "0").ToString()));
        Memory.Write(Addresses.PinkGemColor, int.Parse(Client.Options?.GetValueOrDefault("pink_gem_color", "0").ToString()));
        switch (_portalTextColor)
        {
            case PortalTextColor.Red:
                Memory.WriteByte(Addresses.PortalTextRed, 128);
                Memory.WriteByte(Addresses.PortalTextGreen, 0);
                Memory.WriteByte(Addresses.PortalTextBlue, 0);
                break;
            case PortalTextColor.Green:
                Memory.WriteByte(Addresses.PortalTextRed, 0);
                Memory.WriteByte(Addresses.PortalTextGreen, 128);
                Memory.WriteByte(Addresses.PortalTextBlue, 0);
                break;
            case PortalTextColor.Blue:
                Memory.WriteByte(Addresses.PortalTextRed, 0);
                Memory.WriteByte(Addresses.PortalTextGreen, 0);
                Memory.WriteByte(Addresses.PortalTextBlue, 128);
                break;
            case PortalTextColor.Pink:
                Memory.WriteByte(Addresses.PortalTextRed, 64);
                Memory.WriteByte(Addresses.PortalTextGreen, 0);
                Memory.WriteByte(Addresses.PortalTextBlue, 64);
                break;
            case PortalTextColor.White:
                Memory.WriteByte(Addresses.PortalTextRed, 128);
                Memory.WriteByte(Addresses.PortalTextGreen, 128);
                Memory.WriteByte(Addresses.PortalTextBlue, 128);
                break;
            default:
                Memory.WriteByte(Addresses.PortalTextRed, 64);
                Memory.WriteByte(Addresses.PortalTextGreen, 64);
                Memory.WriteByte(Addresses.PortalTextBlue, 0);
                break;
        }
        if (
            _cosmeticEffects.Count > 0 &&
            Memory.ReadShort(Addresses.GameStatus) == (short)GameStatus.InGame &&
            Client.ItemState != null &&
            Client.CurrentSession != null &&
            _cosmeticEffects.TryDequeue(out string effect)
        )
        {
            switch (effect)
            {
                case "Normal Spyro":
                    TurnSpyroColor(SpyroColor.SpyroColorDefault);
                    DeactivateBigHeadMode();
                    break;
                case "Big Head Mode":
                    ActivateBigHeadMode();
                    break;
                case "Flat Spyro Mode":
                    ActivateFlatSpyroMode();
                    break;
                case "Turn Spyro Red":
                    TurnSpyroColor(SpyroColor.SpyroColorRed);
                    break;
                case "Turn Spyro Blue":
                    TurnSpyroColor(SpyroColor.SpyroColorBlue);
                    break;
                case "Turn Spyro Yellow":
                    TurnSpyroColor(SpyroColor.SpyroColorYellow);
                    break;
                case "Turn Spyro Pink":
                    TurnSpyroColor(SpyroColor.SpyroColorPink);
                    break;
                case "Turn Spyro Green":
                    TurnSpyroColor(SpyroColor.SpyroColorGreen);
                    break;
                case "Turn Spyro Black":
                    TurnSpyroColor(SpyroColor.SpyroColorBlack);
                    break;
            }
        }
    }
    
    /**
     * Perform necessary setup for once the player is in a save file.
     */
    private static async void StartSpyroGame(object source, ElapsedEventArgs e)
    {
        if (!Helpers.IsInGame() || Client.ItemState == null || Client.CurrentSession == null)
        {
            Log.Logger.Information("Player is not yet in control of Spyro.");
            return;
        }
        Log.Logger.Information("Player is in control of Spyro. Starting game!");
        bool deathLink = int.Parse(Client.Options?.GetValueOrDefault("death_link", "0").ToString()) > 0;
        if (deathLink)
        {
            _deathLinkService = Client.EnableDeathLink();
            _deathLinkService.OnDeathLinkReceived += new DeathLinkService.DeathLinkReceivedHandler(HandleDeathLink);
        }
        CheckGoalCondition();
        LevelInGameIDs currentLevel = (LevelInGameIDs)Memory.ReadByte(Addresses.CurrentLevelAddress);
        Helpers.UpdateLocationList(currentLevel, Client);
        _handleGemsanity = true;
        if (_loadGameTimer != null)
        {
            _loadGameTimer.Enabled = false;
        }
    }

    /**
     * Handles Moneybags unlocks as part of the game loop.
     * Ensures there's no desync due to items coming in on another save.
     */
    private static void HandleMoneybagsUnlocks()
    {
        // Make Glimmer bridge free.  In normal settings, this cannot be an item or the start is too restrictive.
        // It's not worth making this payment an item for Gemsanity alone.
        Memory.Write(Addresses.GlimmerBridgeUnlock, 0);
        MoneybagsOptions moneybagsOption = (MoneybagsOptions)int.Parse(Client.Options?.GetValueOrDefault("moneybags_settings", "0").ToString());
        GemsanityOptions gemsanityOption = (GemsanityOptions)int.Parse(Client.Options?.GetValueOrDefault("enable_gemsanity", "0").ToString());
        LevelLockOptions levelLockOption = (LevelLockOptions)int.Parse(Client.Options?.GetValueOrDefault("level_lock_options", "0").ToString());
        int startWithAbilities = int.Parse(Client.Options?.GetValueOrDefault("start_with_abilities", "0").ToString());
        Dictionary<string, uint> moneybagsAddresses = new Dictionary<string, uint>()
        {
            { "Crystal Glacier Bridge", Addresses.CrystalBridgeUnlock },
            { "Aquaria Towers Submarine", Addresses.AquariaSubUnlock },
            { "Magma Cone Elevator", Addresses.MagmaElevatorUnlock },
            { "Swim", Addresses.SwimUnlock },
            { "Climb", Addresses.ClimbUnlock },
            { "Headbash", Addresses.HeadbashUnlock },
            { "Wall by Aquaria Towers", Addresses.WallToAquariaUnlock },  // Name changed in 2.0.0.
            { "Zephyr Portal", Addresses.ZephyrPortalUnlock },
            { "Shady Oasis Portal", Addresses.ShadyPortalUnlock },
            { "Icy Speedway Portal", Addresses.IcyPortalUnlock },
            { "Canyon Speedway Portal", Addresses.CanyonPortalUnlock },
        };
        if (moneybagsOption == MoneybagsOptions.Moneybagssanity)
        {
            foreach (string unlock in moneybagsAddresses.Keys)
            {
                uint unlockAddress = moneybagsAddresses[unlock];
                if (
                    (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == $"Moneybags Unlock - {unlock}").Count() ?? 0) == 0 &&
                    (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == "Ripto Defeated").Count() ?? 0) == 0
                )
                {
                    Memory.Write(unlockAddress, 20001);
                }
                else
                {
                    Memory.Write(unlockAddress, 65536);
                }
            }
        }
        else if (
            moneybagsOption == MoneybagsOptions.Vanilla &&
            (
                gemsanityOption != GemsanityOptions.Off ||
                levelLockOption != LevelLockOptions.Vanilla
            )
        )
        {
            foreach (string unlock in moneybagsAddresses.Keys)
            {
                uint unlockAddress = moneybagsAddresses[unlock];
                if ((Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == $"Moneybags Unlock - {unlock}").Count() ?? 0) == 0)
                {
                    Memory.Write(unlockAddress, 0);
                }
                else
                {
                    Memory.Write(unlockAddress, 65536);
                }
            }
        }
        else if (
            moneybagsOption == MoneybagsOptions.Vanilla &&
            startWithAbilities == 1
        )
        {
            foreach (string unlock in moneybagsAddresses.Keys)
            {
                if (unlock != "Swim" && unlock != "Climb" && unlock != "Headbash")
                {
                    continue;
                }
                uint unlockAddress = moneybagsAddresses[unlock];
                Memory.Write(unlockAddress, 65536);
            }
        }
    }

    /**
     * Based on player settings, restore unused game functionality that lets the player warp to the inner castle area from other worlds.
     */
    private static void HandleInnerWTWarpAccess()
    {
        WTWarpOptions warpOption = (WTWarpOptions)int.Parse(Client.Options?.GetValueOrDefault("wt_warp_options", "0").ToString());
        bool rerouteWarp = false;
        if (warpOption == WTWarpOptions.Door)
        {
            if (Memory.ReadBit(Addresses.WTDoorGemAddress, Addresses.WTDoorGemBit))
            {
                rerouteWarp = true;
            }
        }
        if (warpOption == WTWarpOptions.WallOrb)
        {
            if (Memory.ReadBit(Addresses.WTWallOrbAddress, Addresses.WTWallOrbBit))
            {
                rerouteWarp = true;
            }
        }
        Memory.Write(Addresses.WTWarpAddress, (short)(rerouteWarp ? 1 : 0));
    }
    
    /**
     * Checks if the player has completed their goal and informs the server if so.
     */
    private static void CheckGoalCondition()
    {
        if (
            Client == null ||
            Client.CurrentSession == null ||
            Client.CurrentSession.Locations == null ||
            Client.CurrentSession.Locations.AllLocationsChecked == null ||
            Client.ItemState == null ||
            GameLocations == null
        )
        {
            return;
        }
        if (_hasSubmittedGoal)
        {
            return;
        }
        var currentTalismans = CalculateCurrentTalismans().GetValueOrDefault("Total", 0);
        var currentOrbs = CalculateCurrentOrbs();
        var currentSkillPoints = CalculateCurrentSkillPoints();
        var currentTokens = CalculateCurrentTokens();
        var currentGems = Memory.ReadShort(Addresses.TotalGemAddress);
        int goal = int.Parse(Client.Options?.GetValueOrDefault("goal", 0).ToString());
        int isOpenWorld = int.Parse(Client.Options?.GetValueOrDefault("enable_open_world", 0).ToString());
        if ((CompletionGoal)goal == CompletionGoal.Ripto)
        {
            if (currentOrbs >= _requiredOrbs && (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x != null && x.ItemName == "Ripto Defeated").Count() ?? 0) > 0)
            {
                _hasSubmittedGoal = true;
                Task.Run(async () =>
                {
                    Client.SendGoalCompletion();
                });
            }
        }
        else if ((CompletionGoal)goal == CompletionGoal.SixtyFourOrb)
        {
            if (currentOrbs >= 64 && (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x != null && x.ItemName == "Ripto Defeated").Count() ?? 0) > 0)
            {
                _hasSubmittedGoal = true;
                Task.Run(async () =>
                {
                    Client.SendGoalCompletion();
                });
            }
        }
        else if ((CompletionGoal)goal == CompletionGoal.HundredPercent)
        {
            if (currentOrbs >= 64 && (isOpenWorld != 0 || currentTalismans >= 14) && currentGems == 10000 && (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x != null && x.ItemName == "Ripto Defeated").Count() ?? 0) > 0)
            {
                _hasSubmittedGoal = true;
                Task.Run(async () =>
                {
                    Client.SendGoalCompletion();
                });
            }
        }
        else if ((CompletionGoal)goal == CompletionGoal.TenTokens)
        {
            if (currentTokens >= 10 && currentOrbs >= 55 && currentGems >= 8000)
            {
                _hasSubmittedGoal = true;
                Task.Run(async () =>
                {
                    Client.SendGoalCompletion();
                });
            }
        }
        else if ((CompletionGoal)goal == CompletionGoal.AllSkillpoints)
        {
            if (currentSkillPoints >= 16)
            {
                _hasSubmittedGoal = true;
                Task.Run(async () =>
                {
                    Client.SendGoalCompletion();
                });
            }
        }
        else if ((CompletionGoal)goal == CompletionGoal.Epilogue)
        {
            if (currentSkillPoints >= 16 && (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x != null && x.ItemName == "Ripto Defeated").Count() ?? 0) > 0)
            {
                _hasSubmittedGoal = true;
                Task.Run(async () =>
                {
                    Client.SendGoalCompletion();
                });
            }
        }
    }
    
    /**
     * Turns off big head mode and also flat Spyro mode.
     */
    private static async void DeactivateBigHeadMode()
    {
        // Disables both big head mode and flat spyro.
        Memory.Write(Addresses.BigHeadMode, (short)0);
    }
    
    /**
     * Turns on big head mode. The size of the head is customizable and needs to be explicitly set.
     */
    private static async void ActivateBigHeadMode()
    {
        Memory.WriteByte(Addresses.SpyroHeight, (byte)(32));
        Memory.WriteByte(Addresses.SpyroLength, (byte)(32));
        Memory.WriteByte(Addresses.SpyroWidth, (byte)(32));
        Memory.Write(Addresses.BigHeadMode, (short)(1));
    }
    
    /**
     * Turns on flat Spyro mode. The dimensions are customizable and need to be explicitly set.
     */
    private static async void ActivateFlatSpyroMode()
    {
        Memory.WriteByte(Addresses.SpyroHeight, (byte)(16));
        Memory.WriteByte(Addresses.SpyroLength, (byte)(16));
        Memory.WriteByte(Addresses.SpyroWidth, (byte)(2));
        Memory.Write(Addresses.BigHeadMode, (short)0x100);
    }
    
    /**
     * Sets Spyro's color to a standard color. This should be extendable to custom colors.
     * 
     * @param colorEnum The color to use.
     */
    private static async void TurnSpyroColor(SpyroColor colorEnum)
    {
        // TODO: Support arbitrary hex values.
        Memory.Write(Addresses.SpyroColorAddress, (short)colorEnum);
    }
    
    /**
     * Updates the Received Items tab.  Unlike the Hints tab, rewrites the list each time.
     */
    private static void UpdateItemLog()
    {
        Dictionary<string, int> itemCount = new Dictionary<string, int>();
        List<LogListItem> messagesToLog = new List<LogListItem>();
        if (Client != null && Client.CurrentSession != null && Client.CurrentSession.Items != null)
        {
            foreach (ItemInfo item in Client.CurrentSession.Items.AllItemsReceived)
            {
                string itemName = item.ItemName;
                if (itemCount.ContainsKey(itemName))
                {
                    itemCount[itemName] = itemCount[itemName] + 1;
                }
                else
                {
                    itemCount[itemName] = 1;
                }
            }
            RxApp.MainThreadScheduler.Schedule(() =>
            {
                List<string> sortedItems = itemCount.Keys.ToList();
                sortedItems.Sort();
                foreach (string item in sortedItems)
                {
                    messagesToLog.Add(new LogListItem(
                        new List<TextSpan>() {
                            new TextSpan() { Text = $"{item}: ", TextColor = new SolidColorBrush(Avalonia.Media.Color.FromRgb(200, 255, 200)) },
                            new TextSpan() { Text = $"{itemCount[item]}", TextColor = new SolidColorBrush(Avalonia.Media.Color.FromRgb(200, 255, 200)) }
                        }
                    ));
                }
            });
        }
        lock (_lockObject)
        {
            RxApp.MainThreadScheduler.Schedule(() =>
            {
                Context.ItemList.Clear();
                foreach (LogListItem messageToLog in messagesToLog)
                {
                    Context.ItemList.Add(messageToLog);
                }
            });
        }
    }

    /**
     * Fires when a message is received from the client.
     * 
     * Used to handle the hint tab and to avoid showing found items in the hint list.
     */
    private void Client_MessageReceived(object? sender, MessageReceivedEventArgs e)
    {
        // If the player requests it, don't show "found" hints in the main client.
        if (e.Message.Parts.Any(x => x.Text == "[Hint]: ") && (!_useQuietHints || !e.Message.Parts.Any(x => x.Text.Trim() == "(found)")))
        {
            LogHint(e.Message);
        }
        if (!e.Message.Parts.Any(x => x.Text == "[Hint]: ") || !_useQuietHints || !e.Message.Parts.Any(x => x.Text.Trim() == "(found)"))
        {
            Log.Logger.Information(JsonConvert.SerializeObject(e.Message));
        }
    }
    
    /**
     * Adds a hint message to the Hints tab.
     * 
     * @param message The message with the hint.
     */
    private static void LogHint(LogMessage message)
    {
        var newMessage = message.Parts.Select(x => x.Text);

        foreach (var hint in Context.HintList)
        {
            IEnumerable<string> hintText = hint.TextSpans.Select(y => y.Text);
            if (newMessage.Count() != hintText.Count())
            {
                continue;
            }
            bool isMatch = true;
            for (int i = 0; i < hintText.Count(); i++)
            {
                if (newMessage.ElementAt(i) != hintText.ElementAt(i))
                {
                    isMatch = false;
                    break;
                }
            }
            if (isMatch)
            {
                return; //Hint already in list
            }
        }
        List<TextSpan> spans = new List<TextSpan>();
        foreach (var part in message.Parts)
        {
            RxApp.MainThreadScheduler.Schedule(() =>
            {
                spans.Add(new TextSpan() { Text = part.Text, TextColor = new SolidColorBrush(Avalonia.Media.Color.FromRgb(part.Color.R, part.Color.G, part.Color.B)) });
            });
        }
        lock (_lockObject)
        {
            RxApp.MainThreadScheduler.Schedule(() =>
            {
                Context.HintList.Add(new LogListItem(spans));
            });
        }
    }
    
    /**
     * Fires when new locations are checked.
     * 
     * @param newCheckedLocations A collection of newly checked locations to process.
     */
    private static void Locations_CheckedLocationsUpdated(System.Collections.ObjectModel.ReadOnlyCollection<long> newCheckedLocations)
    {
        foreach (long location in newCheckedLocations)
        {
            foreach (LevelInGameIDs levelID in Helpers.remainingGemsanityChecks.Keys)
            {
                if (Helpers.remainingGemsanityChecks[levelID].Keys.Contains((int)location))
                {
                    Helpers.remainingGemsanityChecks[levelID].Remove((int)location);
                }
            }
        }
        if (Client.ItemState == null || Client.CurrentSession == null) return;
        if (!Helpers.IsInGame())
        {
            Log.Logger.Error("Check sent while not in game. Please report this in the Discord thread!");
        }
        CalculateCurrentTalismans();
        CalculateCurrentOrbs();
        CheckGoalCondition();
    }
    
    /**
     * Writes a block of text to memory. endAddress will generally be the null terminator and will not be written to.
     */
    private static void WriteStringToMemory(uint startAddress, uint endAddress, string stringToWrite, bool padWithSpaces=true)
    {
        uint address = startAddress;
        int stringIndex = 0;
        while (address < endAddress)
        {
            char charToWrite = ' ';
            if (!padWithSpaces)
            {
                charToWrite = '\0';
            }
            if (stringIndex < stringToWrite.Length)
            {
                charToWrite = stringToWrite[stringIndex];
            }
            Memory.WriteByte(address, (byte)charToWrite);
            stringIndex++;
            address++;
        }
    }
    
    /**
     * Returns a mapping of talisman type to count.
     * 
     * @return A Dictionary with keys of Summer Forest, Autumn Plains, and Total, and values representing item counts.
     */
    private static Dictionary<string, int> CalculateCurrentTalismans()
    {
        var summerCount = Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x != null && x.ItemName == "Summer Forest Talisman").Count() ?? 0;
        summerCount = Math.Min(summerCount, 6);
        var autumnCount = Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x != null && x.ItemName == "Autumn Plains Talisman").Count() ?? 0;
        autumnCount = Math.Min(autumnCount, 8);
        var currentLevel = Memory.ReadByte(Addresses.CurrentLevelAddress);
        // Handle Elora in Summer Forest and the door to Crush by special casing talisman count in this level only.
        // Note that Elora won't open the door if your count is more than 6.
        if (currentLevel == (byte)LevelInGameIDs.SummerForest)
        {
            Memory.WriteByte(Addresses.TotalTalismanAddress, (byte)summerCount);
            WriteStringToMemory(Addresses.SummerEloraStartText, Addresses.SummerEloraEndText, $"Hi, Spyro! You have @4{summerCount}@0 Summer Forest Talismans.");
            WriteStringToMemory(Addresses.SummerEloraWarpStartText, Addresses.SummerEloraWarpEndText, $"Hi, Spyro! You have @4{summerCount}@0 Summer Forest Talismans.");
        }
        else if (currentLevel == (byte)LevelInGameIDs.AutumnPlains)
        {
            Memory.WriteByte(Addresses.TotalTalismanAddress, (byte)(summerCount + autumnCount));
            WriteStringToMemory(Addresses.AutumnEloraStartText, Addresses.AutumnEloraEndText, $"Hi, Spyro! You have @4{summerCount + autumnCount }@0 Talismans.");
            WriteStringToMemory(Addresses.AutumnEloraWarpStartText, Addresses.AutumnEloraWarpEndText, $"Hi, Spyro! You have @4{summerCount + autumnCount}@0 Talismans.");
        }
        return new Dictionary<string, int>() {
            { "Summer Forest", summerCount },
            { "Autumn Plains", autumnCount },
            { "Total", summerCount + autumnCount }
         };
    }
    
    /**
     * Returns the number of orbs the player has.
     * 
     * @return The number of AP orbs received.
     */
    private static int CalculateCurrentOrbs()
    {
        var count = Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x != null && x.ItemName == "Orb").Count() ?? 0;
        count = Math.Min(count, 64);
        Memory.WriteByte(Addresses.TotalOrbAddress, (byte)(count));
        return count;
    }
    
    /**
     * Returns the number of gems the player has. In gemsanity, also sets the value correctly.
     *
     * @return The total number of gems the player has.
     */
    private static int CalculateCurrentGems()
    {
        GemsanityOptions gemsanityOption = (GemsanityOptions)int.Parse(Client.Options?.GetValueOrDefault("enable_gemsanity", "0").ToString());
        if (gemsanityOption == GemsanityOptions.Off)
        {
            return Memory.ReadShort(Addresses.TotalGemAddress);
        }
        uint levelGemCountAddress = Addresses.LevelGemsAddress;
        int totalGems = 0;
        int i = 0;
        foreach (LevelData level in Helpers.GetLevelData())
        {
            if (!level.Name.Contains("Speedway"))
            {
                string levelName = level.Name;
                int levelGemCount = Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x != null && x.ItemName == $"{levelName} Red Gem").Count() ?? 0;
                levelGemCount += 2 * (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x != null && x.ItemName == $"{levelName} Green Gem").Count() ?? 0);
                levelGemCount += 5 * (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x != null && x.ItemName == $"{levelName} Blue Gem").Count() ?? 0);
                levelGemCount += 10 * (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x != null && x.ItemName == $"{levelName} Gold Gem").Count() ?? 0);
                levelGemCount += 25 * (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x != null && x.ItemName == $"{levelName} Pink Gem").Count() ?? 0);
                levelGemCount += 50 * (Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x != null && x.ItemName == $"{levelName} 50 Gems").Count() ?? 0);
                Memory.Write(levelGemCountAddress, levelGemCount);
                totalGems += levelGemCount;
            } else
            {
                totalGems += Memory.ReadInt(levelGemCountAddress);
            }
            i++;
            levelGemCountAddress += 4;
        }
        Memory.Write(Addresses.TotalGemAddress, totalGems);
        return totalGems;
    }
    
    /**
     * Returns the number of completed skill points.
     * 
     * @return The total number of skill points the player has.
     */
    private static int CalculateCurrentSkillPoints()
    {
        return Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x != null && x.ItemName == "Skill Point").Count() ?? 0;
    }
    
    /**
     * Returns the number of Dragon Shores tokens the player has.
     * 
     * @return The total number of Dragon Shores tokens the player has.
     */
    private static int CalculateCurrentTokens()
    {
        return Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x != null && x.ItemName == "Dragon Shores Token").Count() ?? 0;
    }
    
    /**
     * Performs setup actions when the client connects to the server.
     */
    private static void OnConnected(object sender, EventArgs args)
    {
        // TODO: These should probably be moved later, to match Spyro 3.

        // There is a tradeoff here when creating new threads.  Separate timers allow for better control over when
        // memory reads and writes will happen, but they take away threads for other client tasks.
        // This solution is fine with the current item pool size but won't scale with gemsanity.
        // TODO: Test which of these can be combined without impacting the end result.
        _loadGameTimer = new Timer();
        _loadGameTimer.Elapsed += new ElapsedEventHandler(StartSpyroGame);
        _loadGameTimer.Interval = 5000;
        _loadGameTimer.Enabled = true;

        _abilitiesTimer = new Timer();
        _abilitiesTimer.Elapsed += new ElapsedEventHandler(HandleAbilities);
        _abilitiesTimer.Interval = 500;
        _abilitiesTimer.Enabled = true;

        _cosmeticsTimer = new Timer();
        _cosmeticsTimer.Elapsed += new ElapsedEventHandler(HandleCosmeticQueue);
        _cosmeticsTimer.Interval = 5000;
        _cosmeticsTimer.Enabled = true;

        ProgressiveSparxHealthOptions sparxOption = (ProgressiveSparxHealthOptions)int.Parse(Client.Options?.GetValueOrDefault("enable_progressive_sparx_health", "0").ToString());
        if (sparxOption != ProgressiveSparxHealthOptions.Off)
        {
            _sparxUpgrades = (byte)(Client.CurrentSession?.Items?.AllItemsReceived?.Where(x => x.ItemName == "Progressive Sparx Health Upgrade").Count() ?? 0);
            if (sparxOption == ProgressiveSparxHealthOptions.Blue)
            {
                _sparxUpgrades += 2;
            }
            else if (sparxOption == ProgressiveSparxHealthOptions.Green)
            {
                _sparxUpgrades += 1;
            }
            _sparxTimer = new Timer();
            _sparxTimer.Elapsed += new ElapsedEventHandler(HandleMaxSparxHealth);
            _sparxTimer.Interval = 500;
            _sparxTimer.Enabled = true;
        }

        _moneybagsOption = (MoneybagsOptions)int.Parse(Client.Options?.GetValueOrDefault("moneybags_settings", "0").ToString());
        _portalTextColor = (PortalTextColor)int.Parse(Client.Options?.GetValueOrDefault("portal_gem_collection_color", "0").ToString());

        // Repopulate hint list.  There is likely a better way to do this using the Get network protocol
        // with keys=[$"hints_{team}_{slot}"].
        Client?.SendMessage("!hint");
        UpdateItemLog();

        Dictionary<String, String> lastConnectionDetails = new Dictionary<string, string>();
        lastConnectionDetails["slot"] = Context.Slot;
        lastConnectionDetails["host"] = Context.Host;
        try
        {
            SaveLastConnectionDetails(lastConnectionDetails);
        }
        catch (Exception ex)
        {
            Log.Logger.Verbose($"Failed to write connection details\r\n{ex.ToString()}");
        }
    }

    /**
     * Performs cleanup actions when the client disconnects from the server.
     */
    private static void OnDisconnected(object sender, EventArgs args)
    {
        // Avoid ongoing timers affecting a new game.
        _sparxUpgrades = 0;
        _hasSubmittedGoal = false;
        _useQuietHints = true;
        _handleGemsanity = false;
        _unlockedLevels = 0;
        _requiredOrbs = 65;

        if (_deathLinkService != null)
        {
            _deathLinkService = null;
        }
        if (_loadGameTimer != null)
        {
            _loadGameTimer.Enabled = false;
            _loadGameTimer = null;
        }
        if (_abilitiesTimer != null)
        {
            _abilitiesTimer.Enabled = false;
            _abilitiesTimer = null;
        }
        _cosmeticEffects = new ConcurrentQueue<string>();
        if (_cosmeticsTimer != null)
        {
            _cosmeticsTimer.Enabled = false;
            _cosmeticsTimer = null;
        }
        if (_sparxTimer != null)
        {
            _sparxTimer.Enabled = false;
            _sparxTimer = null;
        }
    }
}
