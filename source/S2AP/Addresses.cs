using System.Collections.Generic;

namespace S2AP
{
    public static class Addresses
    {
        public const uint TotalTalismanAddress = 0x00067108;
        public const uint TotalOrbAddress = 0x0006702c;
        public const uint TalismanStartAddress = 0x0006b264; // Starts with Summer Forest!
        public const uint OrbStartAddress = 0x00069fd0; // Includes bytes for levels with no orbs!
        public const uint CurrentLevelAddress = 0x00066f54;
        public const uint IsInDemoMode = 0x00067024; // 0x00067044 seems to behave similarly but is 0 on the Demo mode guidebook screen.
        public const uint GameStatus = 0x000681c8;
        // The values at this and the following 3 bytes seem to be 0 only on reset.
        public const uint ResetCheckAddress = 0x00066f14;
        public const uint PlayerLives = 0x0006712c;
        public const uint PlayerHealth = 0x0006a248;

        public const uint TotalGemAddress = 0x000670cc; // 0x00067660 is the HUD display; may need to be edited if this value is modified.
        public const uint LevelGemsAddress = 0x0006ac04; // One entire word per level, including boss levels.

        public const uint SkelosCactiSkillPoint = 0x0006470c;
        public const uint HurricosWindmillSkillPoint = 0x0006470d;
        public const uint ColossusHockeySkillPoint = 0x0006470e;
        public const uint FractureSuperchargeSkillPoint = 0x0006470f;
        public const uint CrushPerfectSkillPoint = 0x00064711;
        public const uint GulpPerfectSkillPoint = 0x00064712;
        public const uint RiptoPerfectSkillPoint = 0x00064713;
        public const uint ScorchTreesSkillPoint = 0x00064714;
        public const uint OceanTimeAttackSkillPoint = 0x00064715;
        public const uint MetroTimeAttackSkillPoint = 0x00064716;
        public const uint IcyTimeAttackSkillPoint = 0x00064717;
        public const uint CanyonTimeAttackSkillPoint = 0x00064718;
        public const uint IdolTikiSkillPoint = 0x00064719;
        public const uint AquariaSeaweedSkillPoint = 0x0006471a;
        public const uint GulpRiptoSkillPoint = 0x0006471b;
        public const uint SkelosCatbatSkillPoint = 0x0006471c;

        public const uint TokenAddress = 0x000646be; // Each token gets 1 word, but a value of 1 on this byte determines if it's collected.

        public const uint SpyroStateAddress = 0x0006a040; // One byte, set to 31 in decimal to kill Spyro for Death Link.

        public const uint BigHeadMode = 0x0698be;
        public const uint FlatSpyroMode = 0x0698bf;
        public const uint SpyroWidth = 0x0698c1;
        public const uint SpyroHeight = 0x0698c5;
        public const uint SpyroLength = 0x0698c9;
        public const uint SpyroColorAddress = 0x0698cc;

        public const uint PermanentFireballAddress = 0x000698bb;
        public const uint DoubleJumpAddress1 = 0x00035ba8;
        public const uint DoubleJumpAddress2 = 0x00035bb8;
        public const uint InvisibleAddress1 = 0x0004c584;
        public const uint InvisibleAddress2 = 0x0004c586;
        public const uint DestructiveSpyroAddress = 0x0006a12a;

        public const uint CrystalBridgeUnlock = 0x00064670;
        public const uint AquariaSubUnlock = 0x00064674;
        public const uint MagmaElevatorUnlock = 0x00064678;
        public const uint GlimmerBridgeUnlock = 0x0006467c;
        public const uint SwimUnlock = 0x00064680;
        public const uint ClimbUnlock = 0x00064684;
        public const uint HeadbashUnlock = 0x00064688;
        public const uint WallToAquariaUnlock = 0x0006468c;
        public const uint ZephyrPortalUnlock = 0x00064698;
        public const uint ShadyPortalUnlock = 0x0006469c;
        public const uint IcyPortalUnlock = 0x000646a0;
        public const uint CanyonPortalUnlock = 0x000646b8;

        public const uint SummerEloraStartText = 0x001818cb;
        public const uint SummerEloraEndText = 0x00181973;
        public const uint SummerEloraWarpStartText = 0x00181a70;
        public const uint SummerEloraWarpEndText = 0x00181abb;

        public const uint AutumnEloraStartText = 0x00191813;
        public const uint AutumnEloraEndText = 0x001918b8;
        public const uint AutumnEloraWarpStartText = 0x00191a84;
        public const uint AutumnEloraWarpEndText = 0x00191acf;

        public static readonly List<uint> SummerLifeBottle1Address = [0x0006ac8f, 7];
        public static readonly List<uint> SummerLifeBottle2Address = [0x0006ac90, 0];
        public static readonly List<uint> SummerLifeBottle3Address = [0x0006ac8b, 6];
        public static readonly List<uint> IdolLifeBottleAddress = [0x0006acd3, 1];
        public static readonly List<uint> ColossusLifeBottleAddress = [0x0006acfc, 6];
        public static readonly List<uint> HurricosLifeBottleAddress = [0x0006ad0f, 5];
        public static readonly List<uint> AquariaLifeBottleAddress = [0x0006ad2f, 5];
        public static readonly List<uint> AutumnLifeBottleAddress = [0x0006adb3, 6];
        public static readonly List<uint> SkelosLifeBottleAddress = [0x0006ade0, 3];
        public static readonly List<uint> CrystalLifeBottleAddress = [0x0006adff, 7];
        public static readonly List<uint> BreezeLifeBottle1Address = [0x0006ae21, 7];
        public static readonly List<uint> BreezeLifeBottle2Address = [0x0006ae22, 4];
        public static readonly List<uint> ZephyrLifeBottleAddress = [0x0006ae3c, 5];
        public static readonly List<uint> ScorchLifeBottleAddress = [0x0006ae78, 2];
        public static readonly List<uint> ShadyLifeBottleAddress = [0x0006ae93, 5];
        public static readonly List<uint> MagmaLifeBottle1Address = [0x0006aeb9, 0];
        public static readonly List<uint> MagmaLifeBottle2Address = [0x0006aeba, 0];
        public static readonly List<uint> MagmaLifeBottle3Address = [0x0006aeba, 1];
        public static readonly List<uint> MagmaLifeBottle4Address = [0x0006aeba, 2];
        public static readonly List<uint> FractureLifeBottleAddress = [0x0006aee1, 0];
        public static readonly List<uint> MysticLifeBottle1Address = [0x0006af61, 4];
        public static readonly List<uint> MysticLifeBottle2Address = [0x0006af61, 5];
        public static readonly List<uint> CloudLifeBottleAddress = [0x0006af72, 1];

        public const uint SummerGemMask = 0x0006ac84;
        public const uint GlimmerGemMask = 0x0006acaa;
        public const uint IdolGemMask = 0x0006acc4;
        public const uint ColossusGemMask = 0x0006ace7;
        public const uint HurricosGemMask = 0x0006ad04;
        public const uint AquariaGemMask = 0x0006ad24;
        public const uint SunnyGemMask = 0x0006ad4d;
        public const uint AutumnGemMask = 0x0006ada7;
        public const uint SkelosGemMask = 0x0006adcc;
        public const uint CrystalGemMask = 0x0006adf1;
        public const uint BreezeGemMask = 0x0006ae14;
        public const uint ZephyrGemMask = 0x0006ae2b;
        public const uint ScorchGemMask = 0x0006ae6c;
        public const uint ShadyGemMask = 0x0006ae88;
        public const uint MagmaGemMask = 0x0006aeaa;
        public const uint FractureGemMask = 0x0006aecf;
        public const uint WinterGemMask = 0x0006af25;
        public const uint MysticGemMask = 0x0006af4d;
        public const uint CloudGemMask = 0x0006af6e;
        public const uint RoboticaGemMask = 0x0006afac;
        public const uint MetropolisGemMask = 0x0006afca;
    }
}
