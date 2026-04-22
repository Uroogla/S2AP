import typing
from dataclasses import dataclass
from Options import (Toggle, DefaultOnToggle, Option, Range, Choice, ItemDict, DeathLink, PerGameCommonOptions,
                     OptionGroup, OptionSet)
from .LogicTricks import normalized_name_tricks

class GoalOptions:
    RIPTO = 0
    SIXTY_FOUR_ORB = 3
    HUNDRED_PERCENT = 4
    TEN_TOKENS = 5
    ALL_SKILLPOINTS = 6
    EPILOGUE = 7
    ORB_HUNT = 8

class LevelLockOptions:
    VANILLA = 0
    KEYS = 1
    ORBS = 2

class MoneybagsOptions:
    VANILLA = 0
    PRICE_SHUFFLE = 1
    MONEYBAGSSANITY = 2

class GemsanityOptions:
    OFF = 0
    PARTIAL = 1
    FULL = 2

class GemsanityLocationOptions:
    LOCAL = 0
    GLOBAL = 1

class SparxUpgradeOptions:
    OFF = 0
    BLUE = 1
    GREEN = 2
    SPARXLESS = 3
    TRUE_SPARXLESS = 4

class WTWarpOptions:
    VANILLA = 0
    DOOR = 1
    WALL_ORB = 2

class AbilityOptions:
    VANILLA = 0
    IN_POOL = 1
    OFF = 2
    START_WITH = 3

class BomboOptions:
    VANILLA = 0
    THIRD_ONLY = 1
    FIRST_ONLY = 2
    FIRST_ONLY_NO_ATTACK = 3

class TrickDifficultyOptions:
    OFF = 0
    EASY = 1
    MEDIUM = 2
    HARD = 3
    CUSTOM = 4

class PortalTextColorOptions:
    DEFAULT = 0
    RED = 1
    GREEN = 2
    BLUE = 3
    PINK = 4
    WHITE = 5

class RandomizeGemColorOptions:
    DEFAULT = 0
    SHUFFLE = 1
    RANDOM = 2
    TRUE_RANDOM = 3


class GoalOption(Choice):
    """Choose the completion goal.
    Ripto - Collect enough orbs to open the arena and beat Ripto.
    64 Orb - Collect 64 orbs and beat Ripto.
    100 Percent - Collect all talismans, orbs, and gems and beat Ripto.
        In Open World mode, no talismans are required.
    10 Tokens - Collect 8000 gems and 55 orbs to unlock the theme park
        and collect all 10 tokens in Dragon Shores.
    All Skillpoints - Collect all 16 skill points in the game.
    Epilogue - Unlock the full epilogue by collecting all 16 skill points
        and defeating Ripto."""
    display_name = "Completion Goal"
    default = GoalOptions.RIPTO
    option_ripto = GoalOptions.RIPTO
    option_64_orb = GoalOptions.SIXTY_FOUR_ORB
    option_100_percent = GoalOptions.HUNDRED_PERCENT
    option_10_tokens = GoalOptions.TEN_TOKENS
    option_all_skillpoints = GoalOptions.ALL_SKILLPOINTS
    option_epilogue = GoalOptions.EPILOGUE
    # TODO: Allow this once edge cases are handled.
    # option_orb_hunt = GoalOptions.ORB_HUNT

class OrbHuntRequirement(Range):
    """How many orbs are needed to complete the Orb Hunt goal.
    Has no effect if any other goal is chosen."""
    display_name = "Orbs Required for Orb Hunt"
    range_start = 2
    range_end = 64
    default = 40

class RiptoDoorOrbs(Range):
    """How many orbs are required to unlock the door to Ripto."""
    display_name = "Orbs to Unlock Ripto"
    range_start = 0
    range_end = 64
    default = 40

class TotalAvailableOrbs(Range):
    """The number of orbs available.
    NOTE: Will add orbs if required to complete your goal.
    Other orb requirements will be adjusted according to the number available."""
    display_name = "Orbs Available"
    range_start = 2
    range_end = 64
    default = 64

class GuaranteedItemsOption(ItemDict):
    """Guarantees that the specified items will be in the item pool"""
    display_name = "Guaranteed Items"

class EnableOpenWorld(Toggle):
    """If on, Crush and Gulp do not require talismans.
    Removes talisman items from the pool.
    Effectively allows early access to each homeworld,
    though swim and climb may logicially lock progression."""
    display_name = "Enable Open World"

class LevelLockOption(Choice):
    """Rules for unlocking each level.
    Glimmer, homeworlds, and bosses always have their vanilla requirements.
    If Moneybagssanity is off, sets prices to 0 to ensure beatable seeds.
    Vanilla: Levels are available if you meet the vanilla requirements.
    Keys: Levels are unlocked by finding "Unlock" items.
        Note: you may need to increase the number of locations (for example,
        by adding gem checks) to provide spots for the keys.
    """
    display_name = "Level Locks"
    default = LevelLockOptions.VANILLA
    option_vanilla = LevelLockOptions.VANILLA
    option_keys = LevelLockOptions.KEYS
    # TODO: Implement.
    # option_orbs = LevelLockOptions.ORBS

class StartingLevelCount(Range):
    """How many level unlocks the player starts with.
    The player always has access to Glimmer, homeworlds, and bosses.
    Only has an effect when level locks are on."""
    display_name = "Starting Level Unlocks"
    range_start = 0
    range_end = 22
    default = 8

class StartWithAbilities(Toggle):
    """The player will start with swim, climb, headbash."""
    display_name = "Start With Abilities"

class StartWithWarps(Toggle):
    """The player will start with warps to all 3 worlds.
    Only has an effect in open world mode."""
    display_name = "Open World Start With Warps"

class WTWarpOption(Choice):
    """When warping to Winter Tundra from outside Crush or Gulp,
    reroutes the warp to inside the castle. No logic is changed.
    Represents planned vanilla functionality that was cut.
    Vanilla: Warps always go to outside the castle.
    Door: Warps inside the castle if you have unlocked the
        door with headbash.
    Wall Orb: Warps inside the castle if you have the WT wall orb.
    """
    display_name = "Winter Tundra Inner Warp"
    default = WTWarpOptions.VANILLA
    option_vanilla = WTWarpOptions.VANILLA
    option_door = WTWarpOptions.DOOR
    option_wall_orb = WTWarpOptions.WALL_ORB

class Enable25PctGemChecksOption(Toggle):
    """Adds checks for getting 25% of the gems in a level"""
    display_name = "Enable 25% Gem Checks"

class Enable50PctGemChecksOption(Toggle):
    """Adds checks for getting 50% of the gems in a level"""
    display_name = "Enable 50% Gem Checks"

class Enable75PctGemChecksOption(Toggle):
    """Adds checks for getting 75% of the gems in a level"""
    display_name = "Enable 75% Gem Checks"

class EnableGemChecksOption(Toggle):
    """Adds checks for getting all gems in a level"""
    display_name = "Enable 100% Gem Checks"

class EnableTotalGemChecksOption(Toggle):
    """Adds checks for every 500 gems you collect total.
    Gems currently paid to Moneybags do not count
    towards your total. Logic assumes you pay Moneybags everywhere
    you can so you cannot be locked out of checks."""
    display_name = "Enable Total Gem Count Checks"

class MaxTotalGemCheckOption(Range):
    """The highest number of total gems that can be required
    for Total Gem Count checks. Has no effect if
    Enable Total Gem Count Checks is disabled."""
    display_name = "Max for Total Gem Count Checks"
    range_start = 500
    range_end = 10000
    default = 4000

class EnableSkillpointChecksOption(Toggle):
    """Adds checks for getting skill points"""
    display_name = "Enable Skillpoint Checks"

class EnableLifeBottleChecksOption(Toggle):
    """Adds checks for getting life bottles"""
    display_name = "Enable Life Bottle Checks"

class EnableSpiritParticleChecksOption(Toggle):
    """Adds checks for getting all spirit particles in a level.
    Some minigame enemies are counted as spirit particles,
    like Draclets in Crystal Glacier. Some enemies only release
    spirit particles while the camera is on them."""
    display_name = "Enable Spirit Particle Checks"

class EnableGemsanityOption(Choice):
    """Adds checks for each individual gem.
    If Moneybagssanity is off, all Moneybags prices will be set to 0 in game.
    Full requires the host to edit allow_full_gemsanity
        in their yaml file, as it is very disruptive.
    Off: Individual gems are not checks.
    Partial: 200 randomly chosen gems become checks. For every level
        with loose gems (not speedways), 8 items giving 50 gems for
        that level will be added to the pool.
    Full: All gems are checks."""
    display_name = "Enable Gemsanity"
    default = GemsanityOptions.OFF
    option_off = GemsanityOptions.OFF
    option_partial = GemsanityOptions.PARTIAL
    option_full = GemsanityOptions.FULL

class GemsanityItemLocations(Choice):
    """Should gem items be shuffled only
    in your world, or spread across the entire multiworld.
    Global is more disruptive to other players."""
    display_name = "Gemsanity Item Locations"
    default = GemsanityLocationOptions.LOCAL
    option_local = GemsanityLocationOptions.LOCAL
    option_global = GemsanityLocationOptions.GLOBAL

class FullGemsanityUseIndividualGems(Toggle):
    """Should gem items be bundles of 50 gems each,
     or individual gems. Applies only to full gemsanity.
     Turning this on slows down generation significantly."""
    display_name = "Full Gemsanity Use Individual Gem Items"

class MoneybagsSettings(Choice):
    """Settings for Moneybags unlocks.
    Vanilla - Pay Moneybags to progress as usual
    Moneybagssanity - You cannot pay Moneybags at all and must\
        find unlock items to progress. Glimmer Bridge
        is excluded to avoid issues with early game randomization."""
    display_name = "Moneybags Settings"
    default = MoneybagsOptions.VANILLA
    option_vanilla = MoneybagsOptions.VANILLA
    option_moneybagssanity = MoneybagsOptions.MONEYBAGSSANITY

class EnableDeathLink(DeathLink):
    """Spyro will die when a DeathLink is
    received and will send them on his death.
    Not every death will trigger a DeathLink,
    and not every received DeathLink will kill Spyro."""
    display_name = "DeathLink"

class EnableFillerExtraLives(DefaultOnToggle):
    """Adds extra lives to the item pool."""
    display_name = "Enable Extra Lives Filler"

class EnableFillerDestructiveSpyro(Toggle):
    """Adds to the item pool an item temporarily powering up
    Spyro so anything destructible he touches is destroyed.
    Affects enemies, strong chests, breakable walls, etc.
    Warning: Behavior is not consistent while charging."""
    display_name = "Enable Temporary Destructive Spyro Filler"

# Likely possible but check for side effects.
#class EnableFillerInvincibility(Toggle):
#    """Allows filler items to include temporary invincibility"""
#    display_name = "Enable Temporary Invincibility Filler"

class EnableFillerColorChange(Toggle):
    """Adds changing Spyro's color to the item pool."""
    display_name = "Enable Changing Spyro's Color Filler"

class EnableFillerBigHeadMode(Toggle):
    """Adds turning on Big Head Mode and flat Spyro Mode
    to the item pool."""
    display_name = "Enable Big Head and Flat Spyro Filler"

class EnableFillerHealSparx(Toggle):
    """Adds healing Sparx to the item pool.
    Sparx must be alive to be healed."""
    display_name = "Enable Healing Sparx Filler"

class TrapFillerPercent(Range):
    """The percentage of filler items that will be traps."""
    display_name = "Trap Percentage of Filler"
    range_start = 0
    range_end = 100
    default = 0

class EnableTrapDamageSparx(Toggle):
    """Adds damaging Sparx to the item pool.
    Cannot directly kill Spyro."""
    display_name = "Enable Hurting Sparx Trap"

class EnableTrapSparxless(Toggle):
    """Adds an item removing Sparx to the item pool."""
    display_name = "Enable Sparxless Trap"

class EnableTrapInvisible(Toggle):
    """Adds turning Spyro invisible briefly to the item pool.
    Duckstation must be run in Interpreter mode for this to have any effect."""
    display_name = "Enable Invisibility Trap"

class EnableTrapRemappedController(Toggle):
    """Allows filler items to "remap" your controller briefly.
    Duckstation must be run in Interpreter mode for this to have any effect."""
    display_name = "Enable Remapped Controller"

class EnableProgressiveSparxHealth(Choice):
    """Start the game with lower max health
    and add items to the pool to increase your max health.
    Off - The game behaves normally.
    Blue - Your max health starts at blue Sparx.
    Green - Your max health starts at green Sparx.
    Sparxless - Your max health starts at no Sparx.
    True Sparxless - Your max health is permanently Sparxless."""
    display_name = "Enable Progressive Sparx Health Upgrades"
    default = SparxUpgradeOptions.OFF
    option_off = SparxUpgradeOptions.OFF
    option_blue = SparxUpgradeOptions.BLUE
    option_green = SparxUpgradeOptions.GREEN
    option_sparxless = SparxUpgradeOptions.SPARXLESS
    option_true_sparxless = SparxUpgradeOptions.TRUE_SPARXLESS

class ProgressiveSparxHealthLogic(Toggle):
    """Certain Sparx health amounts are expected before
    you are required to enter different levels.
    Aquaria Towers, Crush, and Autumn Plains expects green Sparx.
    Entering Skelos Badlands, Gulp, and Winter Tundra expects blue Sparx.
    Entering Ripto expects gold Sparx.
    This does nothing unless Enable Progressive Sparx Health Upgrades
    is set to blue, green, or Sparxless,"""
    display_name = "Enable Progressive Sparx Health Logic"

class DoubleJumpAbility(Choice):
    """Settings for the unintended double jump ability, where jumping
    then pressing square without letting go of jump gains extra height.
    May impact logic on harder trick settings.
    Duckstation must be run in Interpreter mode for this to have any effect.
    Vanilla - Double Jump behaves normally.
    In Pool - Adds Double Jump to the item pool.
        The ability is disabled until you acquire the item.
    Off - Double Jump is disabled."""
    display_name = "Double Jump Ability"
    default = AbilityOptions.VANILLA
    option_vanilla = AbilityOptions.VANILLA
    option_in_pool = AbilityOptions.IN_POOL
    option_off = AbilityOptions.OFF

class FireballAbility(Choice):
    """Settings for the Dragon Shores permanent fireball ability.
    May impact logic, even on the easiest trick settings.
    Vanilla - The fireball powerup in Dragon Shores behaves normally.
    In Pool - Adds Permanent Fireball to the item pool.
        The Dragon Shores powerup does not work.
    Off - Permanent Fireball is disabled.
        The Dragon Shores powerup does not work.
    Start With - You begin the game with fireball, as in New Game Plus."""
    display_name = "Permanent Fireball Ability"
    default = AbilityOptions.VANILLA
    option_vanilla = AbilityOptions.VANILLA
    option_in_pool = AbilityOptions.IN_POOL
    option_off = AbilityOptions.OFF
    option_start_with = AbilityOptions.START_WITH

class TrickDifficulty(Choice):
    """Determines which tricks, if any, are in logic.
    See https://github.com/Uroogla/S2AP/wiki/Tricks-and-Presets
    Off: Only dev-intended strategies are expected.
    Easy Tricks: Straightforward double jumps and fireball usage may be required.
    Medium Tricks: Standard speedrunning tricks, including more difficult
        double jumps, may be required.
    Custom: Choose exactly which tricks are in logic."""
    display_name = "Trick Difficulty"
    default = TrickDifficultyOptions.OFF
    option_off = TrickDifficultyOptions.OFF
    option_easy_tricks = TrickDifficultyOptions.EASY
    option_medium_tricks = TrickDifficultyOptions.MEDIUM
    option_custom = TrickDifficultyOptions.CUSTOM

class CustomTricks(OptionSet):
    """Set various tricks for logic.
    Only used if Trick Difficulty is Custom.
    Format as a comma-separated list of "nice" names:
    ["Sunny Beach Turtle Soup without Climb", "Crystal Glacier Bridge without Moneybags"].
    A full list of supported tricks can be found at:
    https://github.com/Uroogla/S2AP/blob/main/apworld/spyro2/LogicTricks.py
    """
    display_name = "Custom Tricks"
    valid_keys = tuple(normalized_name_tricks.keys())
    valid_keys_casefold = True

class ColossusStartingGoals(Range):
    """How many goals you start with in both Colossus orb challenges."""
    display_name = "Colossus Starting Goals"
    range_start = 0
    range_end = 4
    default = 0

class IdolEasyFish(Toggle):
    """Red fish behave the same as other types of fish in Idol Springs."""
    display_name = "Idol Easy Fish"

class HurricosEasyLightningOrbs(Toggle):
    """Lightning thieves do not steal the orbs in Hurricos."""
    display_name = "Hurricos Easy Lightning Orbs"

class BreezeRequiredGears(Range):
    """How many gears you must collect to complete the trolley orb."""
    display_name = "Breeze Required Gears"
    range_start = 1
    range_end = 50
    default = 50

class ScorchBomboSettings(Choice):
    """Settings for the Bombo orb in Scorch.
    Vanilla - Bombo behaves as normal.
    First Only - Complete the first (shortest) path to complete the orb.
    Attackless First Only - Complete the first (shortest) path to
        complete the orb. Bombo will not attack."""
    display_name = "Scorch Bombo Settings"
    default = BomboOptions.VANILLA
    option_vanilla = BomboOptions.VANILLA
    option_first_only = BomboOptions.FIRST_ONLY
    option_attackless_first_only = BomboOptions.FIRST_ONLY_NO_ATTACK

class FractureRequireHeadbash(DefaultOnToggle):
    """Whether Hunter requires headbash to start Earthshaper Bash.
    Without headbash, this orb can be completed with fireball
    or the Fracture Easy Earthshapers setting.
    This changes the orb's logic."""
    display_name = "Fracture Require Headbash"

class FractureEasyEarthshapers(Toggle):
    """Removes the 7 earthshapers from the Alchemist area and
    reduces the maximum number of spirit particles in the level.
    Removes the headbash requirement from the Fracture Hills
    all spirit particles check. The second orb still requires
    headbash, unless Fracture Require Headbash is disabled."""
    display_name = "Fracture Easy Earthshapers"

class MagmaSpyroStartingPopcorn(Range):
    """How many popcorn crystals you start with in each Hunter orb challenge."""
    display_name = "Magma Spyro Starting Popcorn"
    range_start = 0
    range_end = 9
    default = 0

class MagmaHunterStartingPopcorn(Range):
    """How many popcorn crystals Hunter starts with in each Hunter orb challenge."""
    display_name = "Magma Hunter Starting Popcorn"
    range_start = 0
    range_end = 9
    default = 0

class ShadyRequireHeadbash(DefaultOnToggle):
    """Whether Free Hippos in Shady Oasis requires headbash to start.
    Without headbash, this orb can be completed with fireball.
    This changes the orb's logic."""
    display_name = "Shady Require Headbash"

class EasyGulp(Toggle):
    """Spyro does double damage to Gulp."""
    display_name = "Easy Gulp"

class PortalAndGemCollectionColor(Choice):
    """Changes the color of the number that appears when gems are collected,
    as well as the text on portals."""
    display_name = "Portal and Gem Collection Text Color"
    default = PortalTextColorOptions.DEFAULT
    option_default = PortalTextColorOptions.DEFAULT
    option_red = PortalTextColorOptions.RED
    option_green = PortalTextColorOptions.GREEN
    option_blue = PortalTextColorOptions.BLUE
    option_pink = PortalTextColorOptions.PINK
    option_white = PortalTextColorOptions.WHITE

class GemColor(Choice):
    """Changes the color of gem types (and some other items in game).
    Default: No changes.
    Shuffle: Mixes up the colors of gem types.
    Random Choice: Gem colors are randomly selected from a curated set of options.
    True Random: Gem colors are completely random.  This probably won't look great.
    """
    display_name = "Gem Color"
    default = RandomizeGemColorOptions.DEFAULT
    option_default = RandomizeGemColorOptions.DEFAULT
    option_shuffle = RandomizeGemColorOptions.SHUFFLE
    option_random_choice = RandomizeGemColorOptions.RANDOM
    option_true_random = RandomizeGemColorOptions.TRUE_RANDOM

@dataclass
class Spyro2Option(PerGameCommonOptions):
    goal: GoalOption
    guaranteed_items: GuaranteedItemsOption
    # TODO: Enable.
    # orb_hunt_requirement: OrbHuntRequirement
    ripto_door_orbs: RiptoDoorOrbs
    # TODO: Handle edge cases and enable.
    # available_orbs: TotalAvailableOrbs
    enable_open_world: EnableOpenWorld
    open_world_warp_unlocks: StartWithWarps
    start_with_abilities: StartWithAbilities
    wt_warp_options: WTWarpOption
    level_lock_options: LevelLockOption
    level_unlocks: StartingLevelCount
    enable_25_pct_gem_checks: Enable25PctGemChecksOption
    enable_50_pct_gem_checks: Enable50PctGemChecksOption
    enable_75_pct_gem_checks: Enable75PctGemChecksOption
    enable_gem_checks: EnableGemChecksOption
    enable_total_gem_checks: EnableTotalGemChecksOption
    max_total_gem_checks: MaxTotalGemCheckOption
    enable_skillpoint_checks: EnableSkillpointChecksOption
    enable_life_bottle_checks: EnableLifeBottleChecksOption
    enable_spirit_particle_checks: EnableSpiritParticleChecksOption
    enable_gemsanity: EnableGemsanityOption
    gemsanity_item_locations: GemsanityItemLocations
    full_gemsanity_individual_gems: FullGemsanityUseIndividualGems
    moneybags_settings: MoneybagsSettings
    death_link: EnableDeathLink
    enable_filler_extra_lives: EnableFillerExtraLives
    enable_destructive_spyro_filler: EnableFillerDestructiveSpyro
    enable_filler_color_change: EnableFillerColorChange
    enable_filler_big_head_mode: EnableFillerBigHeadMode
    enable_filler_heal_sparx: EnableFillerHealSparx
    trap_filler_percent: TrapFillerPercent
    enable_trap_damage_sparx: EnableTrapDamageSparx
    enable_trap_sparxless: EnableTrapSparxless
    enable_trap_invisibility: EnableTrapInvisible
    enable_progressive_sparx_health: EnableProgressiveSparxHealth
    enable_progressive_sparx_logic: ProgressiveSparxHealthLogic
    double_jump_ability: DoubleJumpAbility
    permanent_fireball_ability: FireballAbility
    trick_difficulty: TrickDifficulty
    custom_tricks: CustomTricks
    colossus_starting_goals: ColossusStartingGoals
    idol_easy_fish: IdolEasyFish
    hurricos_easy_lightning_orbs: HurricosEasyLightningOrbs
    breeze_required_gears: BreezeRequiredGears
    scorch_bombo_settings: ScorchBomboSettings
    fracture_require_headbash: FractureRequireHeadbash
    fracture_easy_earthshapers: FractureEasyEarthshapers
    magma_spyro_starting_popcorn: MagmaSpyroStartingPopcorn
    magma_hunter_starting_popcorn: MagmaHunterStartingPopcorn
    shady_require_headbash: ShadyRequireHeadbash
    easy_gulp: EasyGulp
    portal_gem_collection_color: PortalAndGemCollectionColor
    gem_color: GemColor


# Group logic/trick options together, especially for the local WebHost.
spyro_options_groups = [
    OptionGroup(
        "Enabled Locations",
        [
            Enable25PctGemChecksOption,
            Enable50PctGemChecksOption,
            Enable75PctGemChecksOption,
            EnableGemChecksOption,
            EnableTotalGemChecksOption,
            MaxTotalGemCheckOption,
            EnableGemsanityOption,
            GemsanityItemLocations,
            FullGemsanityUseIndividualGems,
            EnableSkillpointChecksOption,
            EnableLifeBottleChecksOption,
            EnableSpiritParticleChecksOption
        ],
        False
    ),
    OptionGroup(
        "Game Progression",
        [
            EnableOpenWorld,
            StartWithAbilities,
            StartWithWarps,
            LevelLockOption,
            StartingLevelCount,
            RiptoDoorOrbs,
            MoneybagsSettings,
            WTWarpOption,
            # PowerupLockSettings,
        ],
        False
    ),
    OptionGroup(
        "Item Pool",
        [
            DoubleJumpAbility,
            FireballAbility,
            EnableFillerExtraLives,
            EnableFillerDestructiveSpyro,
            EnableFillerColorChange,
            EnableFillerBigHeadMode,
            EnableFillerHealSparx,
            TrapFillerPercent,
            EnableTrapDamageSparx,
            EnableTrapSparxless,
            EnableTrapInvisible
        ],
        True
    ),
    OptionGroup(
        "Sparx Settings",
        [
            EnableProgressiveSparxHealth,
            ProgressiveSparxHealthLogic
        ],
        True
    ),
    OptionGroup(
        "Game Difficulty",
        [
            TrickDifficulty,
            CustomTricks,
            ColossusStartingGoals,
            IdolEasyFish,
            HurricosEasyLightningOrbs,
            BreezeRequiredGears,
            ScorchBomboSettings,
            FractureRequireHeadbash,
            FractureEasyEarthshapers,
            MagmaSpyroStartingPopcorn,
            MagmaHunterStartingPopcorn,
            ShadyRequireHeadbash,
            EasyGulp
        ],
        True
    ),
    OptionGroup(
        "Cosmetics",
        [
            PortalAndGemCollectionColor,
            GemColor
        ],
        True
    ),
]
