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
    }
}
