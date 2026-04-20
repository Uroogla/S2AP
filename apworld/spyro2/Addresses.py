class RAM:
    TotalTalismanAddress = 0x00067108
    TotalOrbAddress = 0x0006702c
    TalismanStartAddress = 0x0006b264 # Starts with Summer Forest!
    OrbStartAddress = 0x00069fd0 # Includes bytes for levels with no orbs!
    CurrentLevelAddress = 0x00066f54
    IsInDemoMode = 0x00067024 # 0x00067044 seems to behave similarly but is 0 on the Demo mode guidebook screen.
    GameStatus = 0x000681c8
    # The values at this and the following 3 bytes seem to be 0 only on reset.
    ResetCheckAddress = 0x00066f14
    PlayerLives = 0x0006712c
    PlayerHealth = 0x0006a248
    SpiritParticlesAddress = 0x00066fb0

    PlayerZPos = 0x69FF8
    PlayerAnimationLength = 0x6A04C
    PlayerVelocityStatus = 0x6A044

    RiptoDoorOrbRequirementAddress = 0x0007695c
    RiptoDoorOrbDisplayAddress = 0x000769e0

    TotalGemAddress = 0x000670cc # 0x00067660 is the HUD display; may need to be edited if this value is modified.
    LevelGemsAddress = 0x0006ac04 # One entire word per level, including boss levels.

    SkillPointAddresses = 0x0006470c
    SkelosCactiSkillPoint = 0x0
    HurricosWindmillSkillPoint = 0x1
    ColossusHockeySkillPoint = 0x2
    FractureSuperchargeSkillPoint = 0x3
    CrushPerfectSkillPoint = 0x5
    GulpPerfectSkillPoint = 0x6
    RiptoPerfectSkillPoint = 0x7
    ScorchTreesSkillPoint = 0x8
    OceanTimeAttackSkillPoint = 0x9
    MetroTimeAttackSkillPoint = 0xa
    IcyTimeAttackSkillPoint = 0xb
    CanyonTimeAttackSkillPoint = 0xc
    IdolTikiSkillPoint = 0xd
    AquariaSeaweedSkillPoint = 0xe
    GulpRiptoSkillPoint = 0xf
    SkelosCatbatSkillPoint = 0x10

    TokenAddress = 0x000646be # Each token gets 1 word, but a value of 1 on this byte determines if it's collected.
    SpyroStateAddress = 0x0006a040 # One byte

    # Cosmetics
    BigHeadMode = 0x0698be
    FlatSpyroMode = 0x0698bf
    SpyroWidth = 0x0698c1
    SpyroHeight = 0x0698c5
    SpyroLength = 0x0698c9
    SpyroColorAddress = 0x0698cc
    PortalTextRed = 0x00064468
    PortalTextGreen = 0x00064469
    PortalTextBlue = 0x0006446a

    RedGemShadow = 0x00064450
    RedGemColor = 0x00064454
    GreenGemShadow = 0x00064460
    GreenGemColor = 0x00064464
    BlueGemShadow = 0x00064470
    BlueGemColor = 0x00064474
    GoldGemShadow = 0x00064480
    GoldGemColor = 0x00064484
    PinkGemShadow = 0x00064490
    PinkGemColor = 0x00064494

    # Abilities
    PermanentFireballAddress = 0x000698bb
    DoubleJumpAddress1 = 0x00035ba8
    DoubleJumpAddress2 = 0x00035bb8
    InvisibleAddress1 = 0x0004c584
    InvisibleAddress2 = 0x0004c586
    DestructiveSpyroAddress = 0x0006a12a

    # Moneybags
    MoneybagsUnlocks = 0x00064670
    CrystalBridgeUnlock = 0x0
    AquariaSubUnlock = 0x4
    MagmaElevatorUnlock = 0x8
    GlimmerBridgeUnlock = 0xc
    SwimUnlock = 0x10
    ClimbUnlock = 0x14
    HeadbashUnlock = 0x18
    WallToAquariaUnlock = 0x1c
    ZephyrPortalUnlock = 0x28
    ShadyPortalUnlock = 0x2c
    IcyPortalUnlock = 0x30
    CanyonPortalUnlock = 0x48
    
    # Elora text addresses, for giving talisman counts.
    SummerEloraStartText = 0x001818cb
    SummerEloraEndText = 0x00181973
    SummerEloraWarpStartText = 0x00181a70
    SummerEloraWarpEndText = 0x00181abb
    AutumnEloraStartText = 0x00191813
    AutumnEloraEndText = 0x001918b8
    AutumnEloraWarpStartText = 0x00191a84
    AutumnEloraWarpEndText = 0x00191acf

    # Life Bottle Addresses
    SummerLifeBottle1Address = [0x0006ac8f - 0x0006ac84, 7]
    SummerLifeBottle2Address = [0x0006ac90 - 0x0006ac84, 0]
    SummerLifeBottle3Address = [0x0006ac8b - 0x0006ac84, 6]
    IdolLifeBottleAddress = [0x0006acd3 - 0x0006ac84, 1]
    ColossusLifeBottleAddress = [0x0006acfc - 0x0006ac84, 6]
    HurricosLifeBottleAddress = [0x0006ad0f - 0x0006ac84, 5]
    AquariaLifeBottleAddress = [0x0006ad2f - 0x0006ac84, 5]
    AutumnLifeBottleAddress = [0x0006adb3 - 0x0006ac84, 6]
    SkelosLifeBottleAddress = [0x0006ade0 - 0x0006ac84, 3]
    CrystalLifeBottleAddress = [0x0006adff - 0x0006ac84, 7]
    BreezeLifeBottle1Address = [0x0006ae21 - 0x0006ac84, 7]
    BreezeLifeBottle2Address = [0x0006ae22 - 0x0006ac84, 4]
    ZephyrLifeBottleAddress = [0x0006ae3c - 0x0006ac84, 5]
    ScorchLifeBottleAddress = [0x0006ae78 - 0x0006ac84, 2]
    ShadyLifeBottleAddress = [0x0006ae93 - 0x0006ac84, 5]
    MagmaLifeBottle1Address = [0x0006aeb9 - 0x0006ac84, 0]
    MagmaLifeBottle2Address = [0x0006aeba - 0x0006ac84, 0]
    MagmaLifeBottle3Address = [0x0006aeba - 0x0006ac84, 1]
    MagmaLifeBottle4Address = [0x0006aeba - 0x0006ac84, 2]
    FractureLifeBottleAddress = [0x0006aee1 - 0x0006ac84, 0]
    MysticLifeBottle1Address = [0x0006af61 - 0x0006ac84, 4]
    MysticLifeBottle2Address = [0x0006af61 - 0x0006ac84, 5]
    CloudLifeBottleAddress = [0x0006af72 - 0x0006ac84, 1]

    # Bit masks for gems (and other flags) in each level.
    GemMaskAddress = 0x0006ac84
    SummerGemMask = 0x0
    GlimmerGemMask = 0x0006acaa - 0x0006ac84
    IdolGemMask = 0x0006acc4 - 0x0006ac84
    ColossusGemMask = 0x0006ace7 - 0x0006ac84
    HurricosGemMask = 0x0006ad04 - 0x0006ac84
    AquariaGemMask = 0x0006ad24 - 0x0006ac84
    SunnyGemMask = 0x0006ad4d - 0x0006ac84
    AutumnGemMask = 0x0006ada7 - 0x0006ac84
    SkelosGemMask = 0x0006adcc - 0x0006ac84
    CrystalGemMask = 0x0006adf1 - 0x0006ac84
    BreezeGemMask = 0x0006ae14 - 0x0006ac84
    ZephyrGemMask = 0x0006ae2b - 0x0006ac84
    ScorchGemMask = 0x0006ae6c - 0x0006ac84
    ShadyGemMask = 0x0006ae88 - 0x0006ac84
    MagmaGemMask = 0x0006aeaa - 0x0006ac84
    FractureGemMask = 0x0006aecf - 0x0006ac84
    WinterGemMask = 0x0006af25 - 0x0006ac84
    MysticGemMask = 0x0006af4d - 0x0006ac84
    CloudGemMask = 0x0006af6e - 0x0006ac84
    RoboticaGemMask = 0x0006afac - 0x0006ac84
    MetropolisGemMask = 0x0006afca - 0x0006ac84

    # Gemsanity code change addresses.
    localGemIncrementAddress = 0x000396C0
    globalGemIncrementAddress = 0x000396d4
    globalGemRespawnFixAddress = 0x0001d36c
    localGemRespawnFixAddress = 0x0001d380
    localGemLoadFixAddress = 0x00076B98
    globalGemLoadFixAddress = 0x00076BA0
    playBeepAddress = 0x5429c

    # Address of portal surface flags.
    SummerPortalBlock = 0x000e2d34
    AutumnPortalBlock = 0x000f5330
    WinterPortalBlock = 0x000cf28c

    # Guidebook "Has Entered Level" Flags
    CrushGuidebookUnlock = 0x0006B08C
    AutumnGuidebookUnlock = 0x0006B08D
    GulpGuidebookUnlock = 0x0006B098
    WinterGuidebookUnlock = 0x0006B099

    # Level Name Strings
    IdolNameAddress = 0x000106d0
    ColossusNameAddress = 0x000106c4
    HurricosNameAddress = 0x000106b8
    AquariaNameAddress = 0x000106a8
    SunnyNameAddress = 0x0001069c
    OceanNameAddress = 0x0001068c
    SkelosNameAddress = 0x0001065c
    CrystalNameAddress = 0x0001064c
    BreezeNameAddress = 0x0001063c
    ZephyrNameAddress = 0x00066e98
    MetroNameAddress = 0x0001062c
    ScorchNameAddress = 0x00066e90
    ShadyNameAddress = 0x00010620
    MagmaNameAddress = 0x00010614
    FractureNameAddress = 0x00010604
    IcyNameAddress = 0x000105f4
    MysticNameAddress = 0x000105c4
    CloudNameAddress = 0x000105b4
    CanyonNameAddress = 0x000105a4
    RoboticaNameAddress = 0x00010594
    MetropolisNameAddress = 0x00010588
    ShoresNameAddress = 0x00010578

    # Easy Challenge Addresses
    ColossusSpyroHockeyScore = 0x00198ec5
    ColossusOpponentHockeyScore = 0x00198cc9
    IdolFishThrowUp = 0x00082010
    IdolFishIncludeReds = 0x00082048
    IdolFishIncludeRedsHUD = 0x0007efe0
    HurricosLightningThiefStatuses = [
        0x18C8DC,
        0x18CB44,
        0x18CBF4,
        0x18CCA4,
        0x18CCFC,
        0x18CD54,
        0x18CDAC,
        0x18CE04,
        0x18CF0C,
        0x18CFBC
    ]
    HurricosLightningThiefZCoordinates = [
        0x18C8A8,
        0x18CB10,
        0x18CBC0,
        0x18CC70,
        0x18CCC8,
        0x18CD20,
        0x18CD78,
        0x18CDD0,
        0x18CED8,
        0x18CF88
    ]
    spyroHUDScore = 0x00066FEC
    opponentHUDScore = 0x67084
    firstBomboStatus = 0x189f3d
    secondBomboStatus = 0x189b75
    thirdBomboStatus = 0x189805
    bomboAttackAddress = 0x79b34
    fractureHeadbashCheck = 0x78a88
    maxFractureSpiritParticles = 0x64826
    FractureEarthshaperStatuses = [
        0x188DEC,
        0x188E44,
        0x188E9C,
        0x188EF4,
        0x188F4C,
        0x188FA4,
        0x188FFC
    ]
    FractureEarthshaperZCoordinates = [
        0x188DB8,
        0x188E10,
        0x188E68,
        0x188EC0,
        0x188F18,
        0x188F70,
        0x188FC8
    ]
    ShadyHeadbashCheck = 0x7d6c0
    GulpDoubleDamage = 0x120c5e

    # Used to verify game is correct
    GuidebookText = 0x00010308

    # Winter Tundra warp reroute addresses
    WTWallOrbAddress = 0x69fe5
    WTWallOrbBit = 0
    WTDoorGemAddress = 0x6af25
    WTDoorGemBit = 7
    WTWarpAddress = 0x6470a

    lastReceivedArchipelagoID = 0x1c0
    tempLastReceivedArchipelagoID = 0x1c4

class ROM:
    RomDialogueOrbCount = 0x3ec0c
    OrbCountCode = [0x2c, 0x70, 0x22, 0xac]
    RomSFEloraWarp = 0x1057960
    EloraWarpCode = [0x49, 0x7d, 0x00, 0x0c]
    RomAPEloraWarp = 0x24f6a20
    RomLoadOrbCount = 0x152540
    RomSFOrbCount = 0x1050700
    RomAPOrbCount = 0x24f0040
    RomWTOrbCount = 0x405e1a4
    RomPlayBeep = 0x5c9e4
    PlayBeepCode = [0xc8, 0x41, 0x01, 0x0c]
