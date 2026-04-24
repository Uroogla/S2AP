class GameStatus:
    InGame = 0
    Talking = 1
    Spawning = 3
    Paused = 4
    Loading = 5
    Cutscene = 6
    LoadingWorld = 7
    GameLoadMaybe = 9
    TitleScreen = 11

class SpyroColor:
    SpyroColorDefault = 0
    SpyroColorRed = 1
    SpyroColorBlue = 2
    SpyroColorPink = 3
    SpyroColorGreen = 4
    SpyroColorYellow = 5
    SpyroColorBlack = 6

class ImportantLocationIDs:
    RiptoDefeated = 1258000

# NOTE: This corresponds specifically to 0x00066f54.
# Other addresses use a different set of non-incremental values, starting at 0x0a.
class LevelInGameIDs:
    SummerForest = 0
    Glimmer = 1
    IdolSprings = 2
    Colossus = 3
    Hurricos = 4
    AquariaTowers = 5
    SunnyBeach = 6
    OceanSpeedway = 7
    CrushsDungeon = 8
    AutumnPlains = 9
    SkelosBadlands = 10
    CrystalGlacier = 11
    BreezeHarbor = 12
    Zephyr = 13
    MetroSpeedway = 14
    Scorch = 15
    ShadyOasis = 16
    MagmaCone = 17
    FractureHills = 18
    IcySpeedway = 19
    GulpsOverlook = 20
    WinterTundra = 21
    MysticMarsh = 22
    CloudTemples = 23
    CanyonSpeedway = 24
    RoboticaFarms = 25
    Metropolis = 26
    DragonShores = 27
    RiptosArena = 28

class SpyroStates:
    Flop = 6
    Bonk = 13
    DeathDrowning = 30
    DeathPirouette = 31
    DeathSquash = 32
    DeathBurn = 58
