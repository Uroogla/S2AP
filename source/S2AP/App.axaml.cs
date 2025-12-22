using Archipelago.Core;
using Archipelago.Core.AvaloniaGUI.Models;
using Archipelago.Core.AvaloniaGUI.ViewModels;
using Archipelago.Core.AvaloniaGUI.Views;
using Archipelago.Core.GameClients;
using Archipelago.Core.Models;
using Archipelago.Core.Util;
using Archipelago.MultiClient.Net.MessageLog.Messages;
using Archipelago.MultiClient.Net.Packets;
using Avalonia;
using Avalonia.Controls.ApplicationLifetimes;
using Avalonia.Controls.Platform;
using Avalonia.Markup.Xaml;
using Avalonia.Media;
using Avalonia.OpenGL;
using Newtonsoft.Json;
using ReactiveUI;
using S2AP.Models;
using Serilog;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reactive.Concurrency;
using System.Reflection;
using System.Security.Principal;
using System.Threading.Tasks;
using System.Timers;
using static S2AP.Models.Enums;

namespace S2AP;

public partial class App : Application
{
    public static MainWindowViewModel Context;
    public static ArchipelagoClient Client { get; set; }
    public static List<ILocation> GameLocations { get; set; }
    private static readonly object _lockObject = new object();
    private static Queue<string> _cosmeticEffects { get; set; }
    private static byte _sparxUpgrades { get; set; }
    private static bool _hasSubmittedGoal { get; set; }
    private static bool _useQuietHints { get; set; }
    private static Timer _sparxTimer { get; set; }
    private static Timer _loadGameTimer { get; set; }
    private static Timer _abilitiesTimer { get; set; }
    private static Timer _cosmeticsTimer { get; set; }
    private static MoneybagsOptions _moneybagsOption { get; set; }
    private static PortalTextColor _portalTextColor { get; set; }
    private static bool _destructiveMode { get; set; }
    public override void Initialize()
    {
        AvaloniaXamlLoader.Load(this);
    }
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
    public void Start()
    {
        Context = new MainWindowViewModel("0.6.2");
        Context.ClientVersion = Assembly.GetEntryAssembly().GetName().Version.ToString();
        Context.ConnectClicked += Context_ConnectClicked;
        Context.CommandReceived += (e, a) =>
        {
            if (string.IsNullOrWhiteSpace(a.Command)) return;
            Client?.SendMessage(a.Command);
            HandleCommand(a.Command);
        };
        Context.ConnectButtonEnabled = true;
        _sparxUpgrades = 0;
        _hasSubmittedGoal = false;
        _useQuietHints = true;
        Log.Logger.Information("This Archipelago Client is compatible only with the NTSC-U release of Spyro 2 (North America version).");
        Log.Logger.Information("Trying to play with a different version will not work and may release all of your locations at the start.");
        if (!IsRunningAsAdministrator())
        {
            Log.Logger.Warning("You do not appear to be running this client as an administrator.");
            Log.Logger.Warning("This may result in errors or crashes when trying to connect to Duckstation.");
        }
    }
    private void HandleCommand(string command)
    {
        if (Client == null || Client.GameState == null || Client.CurrentSession == null) return;
        switch (command)
        {
            case "clearSpyroGameState":
                Log.Logger.Information("Clearing the game state.  Please reconnect to the server while in game to refresh received items.");
                Client.ForceReloadAllItems();
                break;
            case "showTalismanCount":
                Dictionary<string, int> talismans = CalculateCurrentTalismans();
                Log.Logger.Information($"Summer Forest: {talismans.GetValueOrDefault("Summer Forest", 0)}; Autumn Plains: {talismans.GetValueOrDefault("Autumn Plains", 0)}");
                break;
            case "useQuietHints":
                Log.Logger.Information("Hints for found locations will not be displayed.  Type 'useVerboseHints' to show them.");
                _useQuietHints = true;
                break;
            case "useVerboseHints":
                Log.Logger.Information("Hints for found locations will be displayed.  Type 'useQuietHints' to show them.");
                _useQuietHints = false;
                break;
            case "showUnlockedLevels":
                showUnlockedLevels();
                break;
            case "showGoal":
                CompletionGoal goal = (CompletionGoal)(int.Parse(Client.Options?.GetValueOrDefault("goal", 0).ToString()));
                string goalText = "";
                switch (goal)
                {
                    case CompletionGoal.Ripto:
                        goalText = "Defeat Ripto";
                        break;
                    case CompletionGoal.FourteenTali:
                        goalText = "Defeat Ripto and collect 14 talismans (if open world is off)";
                        break;
                    case CompletionGoal.FortyOrb:
                        goalText = "Defeat Ripto and collect 40 orbs";
                        break;
                    case CompletionGoal.SixtyFourOrb:
                        goalText = "Defeat Ripto and collect 64 orbs";
                        break;
                    case CompletionGoal.HundredPercent:
                        goalText = "Defeat Ripto and collect 14 talismans (if open world is off), 64 orbs, and 10000 gems";
                        break;
                    case CompletionGoal.TenTokens:
                        goalText = "Collect all 10 tokens in Dragon Shores";
                        break;
                    case CompletionGoal.AllSkillpoints:
                        goalText = "Collect all 16 skill points";
                        break;
                    case CompletionGoal.Epilogue:
                        goalText = "Defeat Ripto and collect all 16 skill points";
                        break;
                    default:
                        goalText = "Defeat Ripto and collect 40 orbs";
                        break;
                }
                Log.Logger.Information($"Your goal is: {goalText}");
                break;
        }
    }
    private async void Context_ConnectClicked(object? sender, ConnectClickedEventArgs e)
    {
        if (Client != null)
        {
            Client.CancelMonitors();
            Client.Connected -= OnConnected;
            Client.Disconnected -= OnDisconnected;
            Client.ItemReceived -= ItemReceived;
            Client.MessageReceived -= Client_MessageReceived;
            Client.LocationCompleted -= Client_LocationCompleted;
            Client.CurrentSession.Locations.CheckedLocationsUpdated -= Locations_CheckedLocationsUpdated;
        }
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
        Client.ShouldSaveStateOnItemReceived = false;

        Memory.GlobalOffset = Memory.GetDuckstationOffset();

        Client.Connected += OnConnected;
        Client.Disconnected += OnDisconnected;

        await Client.Connect(e.Host, "Spyro 2");
        if (!Client.IsConnected)
        {
            Log.Logger.Error("Your host seems to be invalid.  Please confirm that you have entered it correctly.");
            return;
        }
        _cosmeticEffects = new Queue<string>();
        Client.LocationCompleted += Client_LocationCompleted;
        Client.CurrentSession.Locations.CheckedLocationsUpdated += Locations_CheckedLocationsUpdated;
        Client.MessageReceived += Client_MessageReceived;
        Client.ItemReceived += ItemReceived;
        Client.EnableLocationsCondition = () => Helpers.IsInGame();
        await Client.Login(e.Slot, !string.IsNullOrWhiteSpace(e.Password) ? e.Password : null);
        if (Client.Options?.Count > 0)
        {
            GemsanityOptions gemsanityOption = (GemsanityOptions)int.Parse(Client.Options?.GetValueOrDefault("enable_gemsanity", "0").ToString());
            int slot = Client.CurrentSession.ConnectionInfo.Slot;
            Dictionary<string, object> obj = await Client.CurrentSession.DataStorage.GetSlotDataAsync(slot);
            List<int> gemsanityIDs = new List<int>();
            if (obj.TryGetValue("gemsanity_ids", out var value))
            {
                if (value != null)
                {
                    gemsanityIDs = System.Text.Json.JsonSerializer.Deserialize<List<int>>(value.ToString());
                }
            }

            GameLocations = Helpers.BuildLocationList(includeGemsanity: gemsanityOption != GemsanityOptions.Off, gemsanityIDs: gemsanityIDs);
            GameLocations = GameLocations.Where(x => x != null && !Client.CurrentSession.Locations.AllLocationsChecked.Contains(x.Id)).ToList();
            Client.MonitorLocations(GameLocations);
            Log.Logger.Information("Warnings and errors above are okay if this is your first time connecting to this multiworld server.");
        }
        else
        {
            Log.Logger.Error("Failed to login.  Please check your host, name, and password.");
        }
    }

    private void Client_LocationCompleted(object? sender, LocationCompletedEventArgs e)
    {
        if (Client.GameState == null || Client.CurrentSession == null) return;
        CalculateCurrentTalismans();
        CalculateCurrentOrbs();
        GemsanityOptions gemsanityOption = (GemsanityOptions)int.Parse(Client.Options?.GetValueOrDefault("enable_gemsanity", "0").ToString());
        if (gemsanityOption != GemsanityOptions.Off)
        {
            CalculateCurrentGems();
        }
        CheckGoalCondition();
    }

    private async void ItemReceived(object? o, ItemReceivedEventArgs args)
    {
        if (Client.GameState == null || Client.CurrentSession == null) return;
        Log.Logger.Debug($"Item Received: {JsonConvert.SerializeObject(args.Item)}");
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
                });
                break;
            case "Moneybags Unlock - Crystal Glacier Bridge":
                if (_moneybagsOption == MoneybagsOptions.Moneybagssanity)
                {
                    UnlockMoneybags(Addresses.CrystalBridgeUnlock);
                }
                break;
            case "Moneybags Unlock - Aquaria Towers Submarine":
                if (_moneybagsOption == MoneybagsOptions.Moneybagssanity)
                {
                    UnlockMoneybags(Addresses.AquariaSubUnlock);
                }
                break;
            case "Moneybags Unlock - Magma Cone Elevator":
                if (_moneybagsOption == MoneybagsOptions.Moneybagssanity)
                {
                    UnlockMoneybags(Addresses.MagmaElevatorUnlock);
                }
                break;
            case "Moneybags Unlock - Swim":
                if (
                    _moneybagsOption == MoneybagsOptions.Moneybagssanity ||
                    int.Parse(Client.Options?.GetValueOrDefault("enable_open_world", "0").ToString()) == 1 &&
                    int.Parse(Client.Options?.GetValueOrDefault("open_world_ability_and_warp_unlocks", "0").ToString()) == 1
                )
                {
                    UnlockMoneybags(Addresses.SwimUnlock);
                }
                break;
            case "Moneybags Unlock - Climb":
                if (
                    _moneybagsOption == MoneybagsOptions.Moneybagssanity ||
                    int.Parse(Client.Options?.GetValueOrDefault("enable_open_world", "0").ToString()) == 1 &&
                    int.Parse(Client.Options?.GetValueOrDefault("open_world_ability_and_warp_unlocks", "0").ToString()) == 1
                )
                {
                    UnlockMoneybags(Addresses.ClimbUnlock);
                }
                break;
            case "Moneybags Unlock - Headbash":
                if (
                    _moneybagsOption == MoneybagsOptions.Moneybagssanity ||
                    int.Parse(Client.Options?.GetValueOrDefault("enable_open_world", "0").ToString()) == 1 &&
                    int.Parse(Client.Options?.GetValueOrDefault("open_world_ability_and_warp_unlocks", "0").ToString()) == 1
                )
                {
                    UnlockMoneybags(Addresses.HeadbashUnlock);
                }
                break;
            case "Moneybags Unlock - Door to Aquaria Towers":
                if (_moneybagsOption == MoneybagsOptions.Moneybagssanity)
                {
                    UnlockMoneybags(Addresses.WallToAquariaUnlock);
                }
                break;
            case "Moneybags Unlock - Zephyr Portal":
                if (_moneybagsOption == MoneybagsOptions.Moneybagssanity)
                {
                    UnlockMoneybags(Addresses.ZephyrPortalUnlock);
                }
                break;
            case "Moneybags Unlock - Shady Oasis Portal":
                if (_moneybagsOption == MoneybagsOptions.Moneybagssanity)
                {
                    UnlockMoneybags(Addresses.ShadyPortalUnlock);
                }
                break;
            case "Moneybags Unlock - Icy Speedway Portal":
                if (_moneybagsOption == MoneybagsOptions.Moneybagssanity)
                {
                    UnlockMoneybags(Addresses.IcyPortalUnlock);
                }
                break;
            case "Moneybags Unlock - Canyon Speedway Portal":
                if (_moneybagsOption == MoneybagsOptions.Moneybagssanity)
                {
                    UnlockMoneybags(Addresses.CanyonPortalUnlock);
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
    private void showUnlockedLevels()
    {
        List<Item> unlockedLevels = (Client.GameState?.ReceivedItems.Where(x => x.Name.EndsWith(" Unlock")).ToList() ?? new List<Item>());
        if (unlockedLevels.Count >= int.Parse(Client.Options?.GetValueOrDefault("open_world_level_unlocks", "0").ToString()))
        {
            Log.Logger.Information("You have unlocked: ");
            string unlockedLevelsString = "";
            int levelCount = 0;
            foreach (Item unlockedLevel in unlockedLevels)
            {
                if (unlockedLevel.Name == "Dragon Shores Unlock")
                {
                    unlockedLevelsString += ("Shores" + "; ");
                }
                else
                {
                    string newLevel = unlockedLevel.Name.Split(" Unlock")[0].Split(" ")[0];
                    unlockedLevelsString += (newLevel + "; ");
                }
                levelCount++;
                // Print 6 per line so it is easier to read.
                if (levelCount % 6 == 0)
                {
                    Log.Logger.Information(unlockedLevelsString.Substring(0, unlockedLevelsString.Length - 2));
                    unlockedLevelsString = "";
                }
            }
            if (unlockedLevelsString.Length > 0)
            {
                unlockedLevelsString = unlockedLevelsString.Substring(0, unlockedLevelsString.Length - 2);
                Log.Logger.Information(unlockedLevelsString);
            }
        }
    }
    private static async void HandleAbilities(object source, ElapsedEventArgs e)
    {
        if (!Helpers.IsInGame() || Client.GameState == null || Client.CurrentSession == null)
        {
            return;
        }
        CalculateCurrentTalismans();
        CalculateCurrentOrbs();
        AbilityOptions doubleJumpOption = (AbilityOptions)int.Parse(Client.Options?.GetValueOrDefault("double_jump_ability", "0").ToString());
        int hasDoubleJumpItem = (byte)(Client.GameState?.ReceivedItems.Where(x => x.Name == "Double Jump Ability").Count() ?? 0);
        AbilityOptions fireballOption = (AbilityOptions)int.Parse(Client.Options?.GetValueOrDefault("permanent_fireball_ability", "0").ToString());
        int hasFireballItem = (byte)(Client.GameState?.ReceivedItems.Where(x => x.Name == "Permanent Fireball Ability").Count() ?? 0);

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
            Memory.Write(Addresses.DestructiveSpyroAddress, (short)0xFF);
        } // Turns off automatically on its own.

        GemsanityOptions gemsanityOption = (GemsanityOptions)int.Parse(Client.Options?.GetValueOrDefault("enable_gemsanity", "0").ToString());
        if (gemsanityOption != GemsanityOptions.Off)
        {
            // Disable updating local and global gem counts on collecting a gem, loading into a level, and respawning.
            Memory.Write(Addresses.localGemIncrementAddress, 0);
            Memory.Write(Addresses.globalGemIncrementAddress, 0);
            Memory.Write(Addresses.globalGemRespawnFixAddress, 0);
            Memory.Write(Addresses.localGemRespawnFixAddress, 0);
            //Memory.Write(Addresses.localGemLoadFixAddress, 0);
            //Memory.Write(Addresses.globalGemLoadFixAddress, 0);
        }
        int openWorldOption = int.Parse(Client.Options?.GetValueOrDefault("enable_open_world", "0").ToString());
        if (openWorldOption != 0)
        {
            LevelInGameIDs currentLevel = (LevelInGameIDs)Memory.ReadByte(Addresses.CurrentLevelAddress);

            if (currentLevel == LevelInGameIDs.SummerForest)
            {
                bool isIdolUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Idol Springs Unlock")).Count() ?? 0) > 0;
                bool isColossusUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Colossus Unlock")).Count() ?? 0) > 0;
                bool isHurricosUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Hurricos Unlock")).Count() ?? 0) > 0;
                bool isAquariaUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Aquaria Towers Unlock")).Count() ?? 0) > 0;
                bool isSunnyUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Sunny Beach Unlock")).Count() ?? 0) > 0;
                bool isOceanUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Ocean Speedway Unlock")).Count() ?? 0) > 0;
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
                    } else
                    {
                        Memory.Write(portalAddress, 0);
                    }
                    portalAddress += 8;
                }
                /*Memory.Write(Addresses.IdolPortalAddress + 0x48, isIdolUnlocked ? 0x01100100 : 0x00100001);
                Memory.Write(Addresses.ColossusPortalAddress + 0x48, isColossusUnlocked ? 0x01100100 : 0x00100001);
                Memory.Write(Addresses.HurricosPortalAddress + 0x48, isHurricosUnlocked ? 0x01100100 : 0x00100001);
                Memory.Write(Addresses.AquariaPortalAddress + 0x48, isAquariaUnlocked ? 0x01100100 : 0x00100001);
                Memory.Write(Addresses.SunnyPortalAddress + 0x48, isSunnyUnlocked ? 0x01100100 : 0x00100001);
                Memory.Write(Addresses.OceanPortalAddress + 0x48, isOceanUnlocked ? 0x01100100 : 0x00100001);*/
            }
            else if (currentLevel == LevelInGameIDs.AutumnPlains)
            {
                bool isSkelosUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Skelos Badlands Unlock")).Count() ?? 0) > 0;
                bool isCrystalUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Crystal Glacier Unlock")).Count() ?? 0) > 0;
                bool isBreezeUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Breeze Harbor Unlock")).Count() ?? 0) > 0;
                bool isZephyrUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Zephyr Unlock")).Count() ?? 0) > 0;
                bool isMetroUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Metro Speedway Unlock")).Count() ?? 0) > 0;
                bool isScorchUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Scorch Unlock")).Count() ?? 0) > 0;
                bool isShadyUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Shady Oasis Unlock")).Count() ?? 0) > 0;
                bool isMagmaUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Magma Cone Unlock")).Count() ?? 0) > 0;
                bool isFractureUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Fracture Hills Unlock")).Count() ?? 0) > 0;
                bool isIcyUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Icy Speedway Unlock")).Count() ?? 0) > 0;
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
                bool isMysticUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Mystic Marsh Unlock")).Count() ?? 0) > 0;
                bool isCloudUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Cloud Temples Unlock")).Count() ?? 0) > 0;
                bool isCanyonUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Canyon Speedway Unlock")).Count() ?? 0) > 0;
                bool isRoboticaUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Robotica Farms Unlock")).Count() ?? 0) > 0;
                bool isMetropolisUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Metropolis Unlock")).Count() ?? 0) > 0;
                bool isDragonShoresUnlocked = (Client.GameState?.ReceivedItems.Where(x => x.Name == ("Dragon Shores Unlock")).Count() ?? 0) > 0;
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
    private static async void HandleMaxSparxHealth(object source, ElapsedEventArgs e)
    {
        if (!Helpers.IsInGame() || Client.GameState == null || Client.CurrentSession == null)
        {
            return;
        }
        byte currentHealth = Memory.ReadByte(Addresses.PlayerHealth);
        if (currentHealth > _sparxUpgrades)
        {
            Memory.WriteByte(Addresses.PlayerHealth, _sparxUpgrades);
        }
        if (_sparxUpgrades == 3)
        {
            _sparxTimer.Enabled = false;
        }
    }
    private static async void HandleCosmeticQueue(object source, ElapsedEventArgs e)
    {
        if (Client.GameState == null || Client.CurrentSession == null) return;
        // Avoid overwhelming the game when many cosmetic effects are received at once by processing only 1
        // every 5 seconds.  This also lets the user see effects when logging in asynchronously.
        // TODO: Handle this on game reset as well.
        int openWorldOption = int.Parse(Client.Options?.GetValueOrDefault("enable_open_world", "0").ToString());
        if (openWorldOption != 0)
        {
            Memory.WriteByte(Addresses.CrushGuidebookUnlock, 1);
            Memory.WriteByte(Addresses.GulpGuidebookUnlock, 1);
            if (int.Parse(Client.Options?.GetValueOrDefault("open_world_ability_and_warp_unlocks", "0").ToString()) != 0)
            {
                Memory.WriteByte(Addresses.AutumnGuidebookUnlock, 1);
                Memory.WriteByte(Addresses.WinterGuidebookUnlock, 1);
            }
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
                if ((Client.GameState?.ReceivedItems.Where(x => x.Name == $"{levelName} Unlock").Count() ?? 0) == 0)
                {
                    WriteStringToMemory(nameAddresses[0], nameAddresses[1], "LOCKED", padWithSpaces: false);
                }
                else
                {
                    WriteStringToMemory(nameAddresses[0], nameAddresses[1], levelName, padWithSpaces: false);
                }
            }
        }
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
            Client.GameState != null &&
            Client.CurrentSession != null
        )
        {
            string effect = _cosmeticEffects.Dequeue();
            switch (effect)
            {
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
    private static void StartSpyroGame(object source, ElapsedEventArgs e)
    {
        if (!Helpers.IsInGame() || Client.GameState == null || Client.CurrentSession == null)
        {
            Log.Logger.Information("Player is not yet in game.");
            return;
        }
        // Make Glimmer bridge free.  In normal settings, this cannot be an item or the start is too restrictive.
        // It's not worth making this payment an item for Gemsanity alone.
        Memory.Write(Addresses.GlimmerBridgeUnlock, 0);
        MoneybagsOptions moneybagsOption = (MoneybagsOptions)int.Parse(Client.Options?.GetValueOrDefault("moneybags_settings", "0").ToString());
        GemsanityOptions gemsanityOption = (GemsanityOptions)int.Parse(Client.Options?.GetValueOrDefault("enable_gemsanity", "0").ToString());
        Dictionary<string, uint> moneybagsAddresses = new Dictionary<string, uint>()
        {
            { "Crystal Glacier Bridge", Addresses.CrystalBridgeUnlock },
            { "Aquaria Towers Submarine", Addresses.AquariaSubUnlock },
            { "Magma Cone Elevator", Addresses.MagmaElevatorUnlock },
            { "Swim", Addresses.SwimUnlock },
            { "Climb", Addresses.ClimbUnlock },
            { "Headbash", Addresses.HeadbashUnlock },
            { "Door to Aquaria Towers", Addresses.WallToAquariaUnlock },
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
                if ((Client.GameState?.ReceivedItems.Where(x => x.Name == $"Moneybags Unlock - {unlock}").Count() ?? 0) == 0)
                {
                    Memory.Write(unlockAddress, 20001);
                }
                else
                {
                    Memory.Write(unlockAddress, 65536);
                }
            }
        }
        else if (moneybagsOption == MoneybagsOptions.Vanilla && gemsanityOption != GemsanityOptions.Off)
        {
            foreach (string unlock in moneybagsAddresses.Keys)
            {
                uint unlockAddress = moneybagsAddresses[unlock];
                if ((Client.GameState?.ReceivedItems.Where(x => x.Name == $"Moneybags Unlock - {unlock}").Count() ?? 0) == 0)
                {
                    Memory.Write(unlockAddress, 0);
                }
                else
                {
                    Memory.Write(unlockAddress, 65536);
                }
            }
        }
        _loadGameTimer.Enabled = false;
    }
    private static void CheckGoalCondition()
    {
        if (
            Client == null ||
            Client.CurrentSession == null ||
            Client.CurrentSession.Locations == null ||
            Client.CurrentSession.Locations.AllLocationsChecked == null ||
            Client.GameState == null ||
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
        if ((CompletionGoal)goal == CompletionGoal.Ripto || (CompletionGoal)goal == CompletionGoal.FourteenTali && isOpenWorld != 0)
        {
            if ((Client.GameState?.ReceivedItems.Where(x => x != null && x.Name == "Ripto Defeated").Count() ?? 0) > 0)
            {
                Client.SendGoalCompletion();
                _hasSubmittedGoal = true;
            }
        }
        else if ((CompletionGoal)goal == CompletionGoal.FourteenTali)
        {
            if (currentTalismans >= 14 && (Client.GameState?.ReceivedItems.Where(x => x != null && x.Name == "Ripto Defeated").Count() ?? 0) > 0)
            {
                Client.SendGoalCompletion();
                _hasSubmittedGoal = true;
            }
        }
        else if ((CompletionGoal)goal == CompletionGoal.FortyOrb)
        {
            if (currentOrbs >= 40 && (Client.GameState?.ReceivedItems.Where(x => x != null && x.Name == "Ripto Defeated").Count() ?? 0) > 0)
            {
                Client.SendGoalCompletion();
                _hasSubmittedGoal = true;
            }
        }
        else if ((CompletionGoal)goal == CompletionGoal.SixtyFourOrb)
        {
            if (currentOrbs >= 64 && (Client.GameState?.ReceivedItems.Where(x => x != null && x.Name == "Ripto Defeated").Count() ?? 0) > 0)
            {
                Client.SendGoalCompletion();
                _hasSubmittedGoal = true;
            }
        }
        else if ((CompletionGoal)goal == CompletionGoal.HundredPercent)
        {
            if (currentOrbs >= 64 && (isOpenWorld != 0 || currentTalismans >= 14) && currentGems == 10000 && (Client.GameState?.ReceivedItems.Where(x => x != null && x.Name == "Ripto Defeated").Count() ?? 0) > 0)
            {
                Client.SendGoalCompletion();
                _hasSubmittedGoal = true;
            }
        }
        else if ((CompletionGoal)goal == CompletionGoal.TenTokens)
        {
            if (currentTokens >= 10)
            {
                Client.SendGoalCompletion();
                _hasSubmittedGoal = true;
            }
        }
        else if ((CompletionGoal)goal == CompletionGoal.AllSkillpoints)
        {
            if (currentSkillPoints >= 16)
            {
                Client.SendGoalCompletion();
                _hasSubmittedGoal = true;
            }
        }
        else if ((CompletionGoal)goal == CompletionGoal.Epilogue)
        {
            if (currentSkillPoints >= 16 && (Client.GameState?.ReceivedItems.Where(x => x != null && x.Name == "Ripto Defeated").Count() ?? 0) > 0)
            {
                Client.SendGoalCompletion();
                _hasSubmittedGoal = true;
            }
        }
    }
    private static async void ActivateBigHeadMode()
    {
        Memory.WriteByte(Addresses.SpyroHeight, (byte)(32));
        Memory.WriteByte(Addresses.SpyroLength, (byte)(32));
        Memory.WriteByte(Addresses.SpyroWidth, (byte)(32));
        Memory.Write(Addresses.BigHeadMode, (short)(1));
    }
    private static async void ActivateFlatSpyroMode()
    {
        Memory.WriteByte(Addresses.SpyroHeight, (byte)(16));
        Memory.WriteByte(Addresses.SpyroLength, (byte)(16));
        Memory.WriteByte(Addresses.SpyroWidth, (byte)(2));
        Memory.Write(Addresses.BigHeadMode, (short)0x100);
    }
    private static async void TurnSpyroColor(SpyroColor colorEnum)
    {
        Memory.Write(Addresses.SpyroColorAddress, (short)colorEnum);
    }
    private static async void UnlockMoneybags(uint address)
    {
        // Flag the check as paid for, and set the price to 0.  Otherwise, we'll get back too many gems when beating Ripto.
        Memory.Write(address, 65536);
        Log.Logger.Information("If you are in the same zone as Moneybags, you can talk to him to complete the unlock for free.");
    }
    private static void LogItem(Item item)
    {
        // Not supported at this time.
        /*var messageToLog = new LogListItem(new List<TextSpan>()
            {
                new TextSpan(){Text = $"[{item.Id.ToString()}] -", TextColor = new SolidColorBrush(Color.FromRgb(255, 255, 255))},
                new TextSpan(){Text = $"{item.Name}", TextColor = new SolidColorBrush(Color.FromRgb(200, 255, 200))}
            });
        lock (_lockObject)
        {
            RxApp.MainThreadScheduler.Schedule(() =>
            {
                Context.ItemList.Add(messageToLog);
            });
        }*/
    }

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
                spans.Add(new TextSpan() { Text = part.Text, TextColor = new SolidColorBrush(Color.FromRgb(part.Color.R, part.Color.G, part.Color.B)) });
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
    private static void Locations_CheckedLocationsUpdated(System.Collections.ObjectModel.ReadOnlyCollection<long> newCheckedLocations)
    {
        if (Client.GameState == null || Client.CurrentSession == null) return;
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
    private static Dictionary<string, int> CalculateCurrentTalismans()
    {
        var summerCount = Client.GameState?.ReceivedItems.Where(x => x != null && x.Name == "Summer Forest Talisman").Count() ?? 0;
        summerCount = Math.Min(summerCount, 6);
        var autumnCount = Client.GameState?.ReceivedItems.Where(x => x != null && x.Name == "Autumn Plains Talisman").Count() ?? 0;
        autumnCount = Math.Min(autumnCount, 8);
        var currentLevel = Memory.ReadByte(Addresses.CurrentLevelAddress);
        // Handle Elora in Summer Forest and the door to Crush by special casing talisman count in this level only.
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
    private static int CalculateCurrentOrbs()
    {
        var count = Client.GameState?.ReceivedItems.Where(x => x != null && x.Name == "Orb").Count() ?? 0;
        count = Math.Min(count, 64);
        Memory.WriteByte(Addresses.TotalOrbAddress, (byte)(count));
        return count;
    }
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
                int levelGemCount = Client.GameState?.ReceivedItems?.Where(x => x != null && x.Name == $"{levelName} Red Gem").Count() ?? 0;
                levelGemCount += 2 * (Client.GameState?.ReceivedItems?.Where(x => x != null && x.Name == $"{levelName} Green Gem").Count() ?? 0);
                levelGemCount += 5 * (Client.GameState?.ReceivedItems?.Where(x => x != null && x.Name == $"{levelName} Blue Gem").Count() ?? 0);
                levelGemCount += 10 * (Client.GameState?.ReceivedItems?.Where(x => x != null && x.Name == $"{levelName} Gold Gem").Count() ?? 0);
                levelGemCount += 25 * (Client.GameState?.ReceivedItems?.Where(x => x != null && x.Name == $"{levelName} Pink Gem").Count() ?? 0);
                levelGemCount += 50 * (Client.GameState?.ReceivedItems?.Where(x => x != null && x.Name == $"{levelName} 50 Gems").Count() ?? 0);
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
    private static int CalculateCurrentSkillPoints()
    {
        return Client.GameState?.ReceivedItems.Where(x => x != null && x.Name == "Skill Point").Count() ?? 0;
    }
    private static int CalculateCurrentTokens()
    {
        return Client.GameState?.ReceivedItems.Where(x => x != null && x.Name == "Dragon Shores Token").Count() ?? 0;
    }
    private static void OnConnected(object sender, EventArgs args)
    {
        Log.Logger.Information("Connected to Archipelago");
        Log.Logger.Information($"Playing {Client.CurrentSession.ConnectionInfo.Game} as {Client.CurrentSession.Players.GetPlayerName(Client.CurrentSession.ConnectionInfo.Slot)}");

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
            _sparxUpgrades = (byte)(Client.GameState?.ReceivedItems.Where(x => x.Name == "Progressive Sparx Health Upgrade").Count() ?? 0);
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
    }

    private static void OnDisconnected(object sender, EventArgs args)
    {
        Log.Logger.Information("Disconnected from Archipelago");
        // Avoid ongoing timers affecting a new game.
        _sparxUpgrades = 0;
        _hasSubmittedGoal = false;
        _useQuietHints = true;
        Log.Logger.Information("This Archipelago Client is compatible only with the NTSC-U release of Spyro 2 (North America version).");
        Log.Logger.Information("Trying to play with a different version will not work and may release all of your locations at the start.");

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
        _cosmeticEffects = new Queue<string>();
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
