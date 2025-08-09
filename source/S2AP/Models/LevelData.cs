namespace S2AP.Models
{
    public class LevelData
    {
        public string Name { get; set; }
        public int OrbCount { get; set; }
        public int LevelId { get; set; }
        public bool HasTalisman { get; set; }
        public bool IsBoss { get; set; }
        public uint[] MoneybagsAddresses { get; set; }
        public uint[] SkillPointAddresses { get; set; }
        public LevelData(string name, int levelId, int orbCount, bool hasTalisman, bool isBoss, uint[] moneybagsAddresses, uint[] skillPointAddresses)
        {
            Name = name;
            OrbCount = orbCount;
            LevelId = levelId;
            HasTalisman = hasTalisman;
            IsBoss = isBoss;
            MoneybagsAddresses = moneybagsAddresses;
            SkillPointAddresses = skillPointAddresses;
        }
    }
}
