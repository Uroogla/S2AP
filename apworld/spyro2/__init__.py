# world/spyro2/__init__.py
from typing import Dict, Set, List, Union, ClassVar

from BaseClasses import MultiWorld, Region, Item, Entrance, Tutorial, ItemClassification
from Options import OptionError
import Utils
from settings import Group, Bool, UserFilePath

from worlds.AutoWorld import World, WebWorld
from worlds.generic.Rules import set_rule, add_rule, add_item_rule, forbid_item

from .Items import (Spyro2Item, Spyro2ItemCategory, item_dictionary, key_item_names,
    item_descriptions, BuildItemPool, item_name_groups)
from .Locations import (Spyro2Location, Spyro2LocationCategory, location_tables,
    location_dictionary, location_name_groups)
from .Options import Spyro2Option, GoalOptions, GemsanityOptions, GemsanityLocationOptions, MoneybagsOptions, \
    RandomizeGemColorOptions, LevelLockOptions, TrickDifficultyOptions, spyro_options_groups, AbilityOptions, GemsanityRewardOptions
from .Logic import Logic, BaseLogic, EasyLogic, MediumLogic, CustomLogic
from .Rules import get_level_rules
from .Client import Spyro2Client

class Spyro2Settings(Group):

    class AllowFullGemsanity(Bool):
        """Permits full gemsanity options for multiplayer games.
        Full gemsanity adds 2546 locations and up to that many progression items.
        These items may be local-only or spread across the multiworld."""

    allow_full_gemsanity: Union[AllowFullGemsanity, bool] = False


class Spyro2Web(WebWorld):
    bug_report_page = ""
    theme = "stone"
    option_groups = spyro_options_groups
    setup_en = Tutorial(
        "Multiworld Setup Guide",
        "A guide to setting up the Archipelago Spyro 2 randomizer on your computer.",
        "English",
        "setup_en.md",
        "setup/en",
        ["ArsonAssassin", "Uroogla"]
    )
    game_info_languages = ["en"]
    tutorials = [setup_en]


class Spyro2World(World):
    """
    Spyro 2 is a game about a purple dragon who wants to go on vacation.
    """

    game: str = "Spyro 2"
    options_dataclass = Spyro2Option
    options: Spyro2Option
    topology_present: bool = False  # Turn on when entrance randomizer is available.
    web = Spyro2Web()
    data_version = 0
    base_id = 1230000
    enabled_location_categories: Set[Spyro2LocationCategory]
    required_client_version = (0, 5, 0)
    # TODO: Remember to update this!
    ap_world_version = "2.0.0"
    item_name_to_id = Spyro2Item.get_name_to_id()
    location_name_to_id = Spyro2Location.get_name_to_id()
    item_name_groups = item_name_groups
    item_descriptions = item_descriptions
    location_name_groups = location_name_groups
    key_locked_levels = []
    glitches_item_name: str = "Glitched Item"  # UT Glitched Logic Support, Not implemented yet.
    options_copy = []  # Copy of options used to support UT.
    settings: ClassVar[Spyro2Settings]

    # TODO: Remember to keep this False.
    PRINT_GEM_REQS = False  # Prints out the logic for each gem on generating a seed. Not for production use.

    all_levels = [
        "Summer Forest","Glimmer","Idol Springs","Colossus","Hurricos","Aquaria Towers","Sunny Beach","Ocean Speedway","Crush's Dungeon",
        "Autumn Plains","Skelos Badlands","Crystal Glacier","Breeze Harbor","Zephyr","Metro Speedway","Scorch","Shady Oasis","Magma Cone","Fracture Hills","Icy Speedway","Gulp's Overlook",
        "Winter Tundra","Mystic Marsh","Cloud Temples","Canyon Speedway","Robotica Farms","Metropolis","Dragon Shores","Ripto's Arena",
    ]

    def __init__(self, multiworld: MultiWorld, player: int):
        super().__init__(multiworld, player)
        self.locked_items = []
        self.locked_locations = []
        self.main_path_locations = []
        self.enabled_location_categories = set()
        self.enabled_hint_locations = []
        self.chosen_gem_locations = []
        # TODO: Implement.
        self.level_orb_requirements = {
            "Idol Springs": 0,
            "Colossus": 0,
            "Hurricos": 0,
            "Sunny Beach": 0,
            "Aquaria Towers": 0,
            "Crystal Glacier": 0,
            "Skelos Badlands": 0,
            "Breeze Harbor": 0,
            "Zephyr": 0,
            "Scorch": 0,
            "Fracture Hills": 0,
            "Magma Cone": 0,
            "Shady Oasis": 0,
            "Icy Speedway": 0,
            "Mystic Marsh": 0,
            "Canyon Speedway": 0,
            "Robotica Farms": 0,
        }

    def generate_early(self):
        is_ut = getattr(self.multiworld, "generation_is_fake", False)

        self.enabled_location_categories.add(Spyro2LocationCategory.TALISMAN)
        self.enabled_location_categories.add(Spyro2LocationCategory.ORB)
        self.enabled_location_categories.add(Spyro2LocationCategory.EVENT)
        self.enabled_location_categories.add(Spyro2LocationCategory.SHORES_TOKEN)
        if self.options.enable_25_pct_gem_checks.value:
            self.enabled_location_categories.add(Spyro2LocationCategory.GEM_25)
        if self.options.enable_50_pct_gem_checks.value:
            self.enabled_location_categories.add(Spyro2LocationCategory.GEM_50)
        if self.options.enable_75_pct_gem_checks.value:
            self.enabled_location_categories.add(Spyro2LocationCategory.GEM_75)
        if self.options.enable_gem_checks.value:
            self.enabled_location_categories.add(Spyro2LocationCategory.GEM_100)
        if self.options.enable_skillpoint_checks.value:
            self.enabled_location_categories.add(Spyro2LocationCategory.SKILLPOINT)
        if self.options.goal.value in [GoalOptions.ALL_SKILLPOINTS, GoalOptions.EPILOGUE]:
            self.enabled_location_categories.add(Spyro2LocationCategory.SKILLPOINT_GOAL)
        if self.options.enable_total_gem_checks.value:
            self.enabled_location_categories.add(Spyro2LocationCategory.TOTAL_GEM)
        # Use the Moneybags unlocks for logic if they are in place.  The checks themselves will not be randomized.
        if self.options.moneybags_settings.value != MoneybagsOptions.MONEYBAGSSANITY:
            self.enabled_location_categories.add(Spyro2LocationCategory.MONEYBAGS)
        if self.options.enable_life_bottle_checks.value:
            self.enabled_location_categories.add(Spyro2LocationCategory.LIFE_BOTTLE)
        if self.options.enable_gemsanity.value != GemsanityOptions.OFF:
            self.enabled_location_categories.add(Spyro2LocationCategory.GEM)
        bundle_count = int(21 * 400 / self.options.gemsanity_gem_bundle_size)
        if not self.settings.allow_full_gemsanity and self.multiworld.players > 1:
            if self.options.enable_gemsanity.value == GemsanityOptions.FULL:
                 raise OptionError(f"Spyro 2: Player {self.player_name} has gemsanity set to full, which adds 2546 locations "
                                  f"and up to that many progression items to the pool and may result in long generation times. "
                                  f"They must either switch to partial gemsanity, or the "
                                  f"host needs to enable allow_full_gemsanity in their host.yaml settings.")
            if bundle_count > 400 and self.options.gemsanity_reward_type.value == GemsanityRewardOptions.BUNDLES and self.options.enable_gemsanity.value != GemsanityOptions.OFF:
                 raise OptionError(f"Spyro 2: Player {self.player_name} has their gemsanity gem bundle size set to [{self.options.gemsanity_gem_bundle_size.value}] "
                                  f"which is attempting to add [{bundle_count}] progression items (and locations) to the pool and may "
                                  f"result in long generation times. They must switch to a larger bundle size (less items to place). "
                                  f"Alternatively, the host can enable allow_full_gemsanity in their host.yaml settings to authorize "
                                  f"up to 2600 progression items (per spyro gemsanity player) to be added to the item pool.")
        if  self.options.enable_gemsanity.value == GemsanityOptions.PARTIAL:
            all_gem_locations = []
            for location in location_dictionary:
                if location_dictionary[location].category == Spyro2LocationCategory.GEM:
                    all_gem_locations.append(location)
            # Universal Tracker does not know which gems were picked.  Have it assume all gems were picked when it
            # creates its seed.  The location list on the AP server will then remove all non-selected gems.
            if is_ut:
                self.chosen_gem_locations = []
            else:
                self.chosen_gem_locations = self.multiworld.random.sample(all_gem_locations, k=bundle_count)
            
        if self.options.gemsanity_item_locations.value == GemsanityLocationOptions.LOCAL:
            for itemname, item in item_dictionary.items():
                if item.category in [Spyro2ItemCategory.GEM, Spyro2ItemCategory.GEMSANITY_PARTIAL]:
                    self.options.local_items.value.add(itemname)
        if self.options.enable_spirit_particle_checks.value:
            self.enabled_location_categories.add(Spyro2LocationCategory.SPIRIT_PARTICLE)

        if hasattr(self.multiworld, "re_gen_passthrough"):
            self.key_locked_levels = self.multiworld.re_gen_passthrough["Spyro 2"]["key_locked_levels"]
        else:
            possible_locked_levels = [
                "Colossus", "Idol Springs", "Hurricos", "Aquaria Towers", "Sunny Beach", "Ocean Speedway",
                "Skelos Badlands", "Crystal Glacier", "Breeze Harbor", "Zephyr", "Metro Speedway", "Scorch", "Shady Oasis",
                "Magma Cone", "Fracture Hills", "Icy Speedway", "Mystic Marsh", "Cloud Temples", "Canyon Speedway",
                "Robotica Farms", "Metropolis", "Dragon Shores"
            ]
            self.key_locked_levels = self.multiworld.random.sample(possible_locked_levels, k=22 - self.options.level_unlocks.value)

        # Generation struggles to place the requirement to get to the second half of Autumn Plains.
        # This restricts too much of the seed.
        early_double_jump = False
        if self.options.double_jump_ability.value != AbilityOptions.IN_POOL:
            early_double_jump = False
        elif self.options.trick_difficulty == TrickDifficultyOptions.EASY:
            early_double_jump = True
        elif self.options.trick_difficulty == TrickDifficultyOptions.CUSTOM:
            for trick in self.options.custom_tricks.value:
                normalized_name = trick.casefold()
                if normalized_name == "summer forest second half with double jump":
                    early_double_jump = True
                    break

        early_swim = False
        if not early_double_jump:
            if self.options.trick_difficulty in [TrickDifficultyOptions.OFF, TrickDifficultyOptions.EASY]:
                early_swim = True
            elif self.options.trick_difficulty == TrickDifficultyOptions.CUSTOM:
                early_swim = True
                for trick in self.options.custom_tricks.value:
                    normalized_name = trick.casefold()
                    if normalized_name == "summer forest second half with nothing":
                        early_swim = False
                        break

        if self.options.moneybags_settings.value == MoneybagsOptions.MONEYBAGSSANITY and \
            not (
                self.options.start_with_abilities.value or
                self.options.enable_open_world.value and self.options.open_world_warp_unlocks
            ) and \
            early_swim:
            self.multiworld.early_items[self.player]["Moneybags Unlock - Swim"] = 1

        if self.options.moneybags_settings.value == MoneybagsOptions.MONEYBAGSSANITY and \
            not (
                self.options.start_with_abilities.value or
                self.options.enable_open_world.value and self.options.open_world_warp_unlocks
            ) and \
            early_double_jump:
            self.multiworld.early_items[self.player]["Double Jump Ability"] = 1

    def create_regions(self):
        # Create Regions
        regions: Dict[str, Region] = {}
        regions["Menu"] = self.create_region("Menu", [])
        regions.update({region_name: self.create_region(region_name, location_tables[region_name]) for region_name in (self.all_levels + ["Inventory"])})
        
        # Connect Regions
        def create_connection(from_region: str, to_region: str):
            connection = Entrance(self.player, f"{to_region}", regions[from_region])
            regions[from_region].exits.append(connection)
            connection.connect(regions[to_region])
            
        create_connection("Menu", "Glimmer")
        create_connection("Menu", "Inventory")
                
        create_connection("Glimmer", "Summer Forest")
        create_connection("Summer Forest", "Idol Springs")
        create_connection("Summer Forest", "Colossus")
        create_connection("Summer Forest", "Hurricos")
        create_connection("Summer Forest", "Aquaria Towers")
        create_connection("Summer Forest", "Sunny Beach")
        create_connection("Summer Forest", "Ocean Speedway")
             
        create_connection("Summer Forest", "Crush's Dungeon")
        create_connection("Summer Forest", "Autumn Plains")

        create_connection("Autumn Plains", "Skelos Badlands")
        create_connection("Autumn Plains", "Crystal Glacier")
        create_connection("Autumn Plains", "Breeze Harbor")
        create_connection("Autumn Plains", "Zephyr")
        create_connection("Autumn Plains", "Metro Speedway")
        create_connection("Autumn Plains", "Scorch")
        create_connection("Autumn Plains", "Shady Oasis")
        create_connection("Autumn Plains", "Magma Cone")
        create_connection("Autumn Plains", "Fracture Hills")
        create_connection("Autumn Plains", "Icy Speedway")

        create_connection("Autumn Plains", "Gulp's Overlook")
        create_connection("Autumn Plains", "Winter Tundra")

        create_connection("Winter Tundra", "Mystic Marsh")
        create_connection("Winter Tundra", "Cloud Temples")
        create_connection("Winter Tundra", "Canyon Speedway")
        create_connection("Winter Tundra", "Robotica Farms")
        create_connection("Winter Tundra", "Metropolis")

        create_connection("Winter Tundra", "Ripto's Arena")
        create_connection("Winter Tundra", "Dragon Shores")
        
    # For each region, add the associated locations retrieved from the corresponding location_table
    def create_region(self, region_name, location_table) -> Region:
        new_region = Region(region_name, self.player, self.multiworld)
        for location in location_table:
            if location.category in self.enabled_location_categories and \
                    location.category not in [Spyro2LocationCategory.EVENT, Spyro2LocationCategory.TOTAL_GEM, Spyro2LocationCategory.GEM]:
                new_location = Spyro2Location(
                    self.player,
                    location.name,
                    location.category,
                    location.default_item,
                    self.location_name_to_id[location.name],
                    new_region
                )
                new_region.locations.append(new_location)
            elif location.category in self.enabled_location_categories and \
                    location.category == Spyro2LocationCategory.GEM and \
                    (len(self.chosen_gem_locations) == 0 or location.name in self.chosen_gem_locations):
                new_location = Spyro2Location(
                    self.player,
                    location.name,
                    location.category,
                    location.default_item,
                    self.location_name_to_id[location.name],
                    new_region
                )
                new_region.locations.append(new_location)
            elif location.category in self.enabled_location_categories and \
                    location.category == Spyro2LocationCategory.TOTAL_GEM:
                gems_needed = int(location.name.split("Total Gems: ")[1])
                if gems_needed <= self.options.max_total_gem_checks.value:
                    new_location = Spyro2Location(
                        self.player,
                        location.name,
                        location.category,
                        location.default_item,
                        self.location_name_to_id[location.name],
                        new_region
                    )
                    new_region.locations.append(new_location)
            elif location.category == Spyro2LocationCategory.EVENT:
                event_item = self.create_item(location.default_item)
                new_location = Spyro2Location(
                    self.player,
                    location.name,
                    location.category,
                    location.default_item,
                    self.location_name_to_id[location.name],
                    new_region
                )
                event_item.code = None
                new_location.place_locked_item(event_item)
                new_region.locations.append(new_location)
        self.multiworld.regions.append(new_region)
        return new_region

    def create_items(self):
        itempool: List[Spyro2Item] = []
        itempoolSize = 0

        for location in self.multiworld.get_locations(self.player):
            if location.category in [Spyro2LocationCategory.EVENT, Spyro2LocationCategory.MONEYBAGS, Spyro2LocationCategory.SKILLPOINT_GOAL, Spyro2LocationCategory.SHORES_TOKEN]:
                item = self.create_item(location.default_item_name)
                self.multiworld.get_location(location.name, self.player).place_locked_item(item)
            elif location.category in self.enabled_location_categories:
                itempoolSize += 1

        foo = BuildItemPool(self, itempoolSize, self.options, self.key_locked_levels)
        for item in foo:
            itempool.append(self.create_item(item.name))

        # Add regular items to itempool
        self.multiworld.itempool += itempool

    def create_item(self, name: str) -> Item:
        data = self.item_name_to_id[name]
        useful_categories = {}

        if name in key_item_names or \
                name == "Glitched Item" or \
                name == "Permanent Fireball Ability" or \
                item_dictionary[name].category in [Spyro2ItemCategory.LEVEL_UNLOCK, Spyro2ItemCategory.TALISMAN, Spyro2ItemCategory.ORB, Spyro2ItemCategory.EVENT, Spyro2ItemCategory.MONEYBAGS, Spyro2ItemCategory.SKILLPOINT_GOAL, Spyro2ItemCategory.GEM, Spyro2ItemCategory.GEMSANITY_PARTIAL] or \
                self.options.enable_progressive_sparx_logic.value and name == 'Progressive Sparx Health Upgrade' or \
                name in ["Double Jump Ability"] and self.options.trick_difficulty.value != TrickDifficultyOptions.OFF or \
                name == "Dragon Shores Token" and self.options.goal.value == GoalOptions.TEN_TOKENS:
            item_classification = ItemClassification.progression
        elif item_dictionary[name].category in useful_categories or \
                not self.options.enable_progressive_sparx_logic.value and name == 'Progressive Sparx Health Upgrade' or \
                name in ["Double Jump Ability"] and self.options.trick_difficulty.value == TrickDifficultyOptions.OFF:
            item_classification = ItemClassification.useful
        elif item_dictionary[name].category == Spyro2ItemCategory.TRAP:
            item_classification = ItemClassification.trap
        else:
            item_classification = ItemClassification.filler

        return Spyro2Item(name, item_classification, data, self.player)

    def get_filler_item_name(self) -> str:
        return "Extra Life"
    
    def set_rules(self) -> None:
        logic: Logic
        if self.options.trick_difficulty.value == TrickDifficultyOptions.OFF:
            logic = BaseLogic(self)
        elif self.options.trick_difficulty.value == TrickDifficultyOptions.EASY:
            logic = EasyLogic(self)
        elif self.options.trick_difficulty.value == TrickDifficultyOptions.MEDIUM:
            logic = MediumLogic(self)
        elif self.options.trick_difficulty.value == TrickDifficultyOptions.CUSTOM:
            logic = CustomLogic(self)
        else:
            logic = BaseLogic(self)

        all_level_rules = get_level_rules(logic)

        def get_gems_accessible_in_level(self, level, state):
            if level in ["Crush's Dungeon", "Gulp's Overlook", "Ripto's Arena", "Dragon Shores"]:
                return 0
            if self.options.enable_gemsanity.value != GemsanityOptions.OFF and "Speedway" not in level:
                return logic.get_gemsanity_gems(level, state)

            for level_rule in all_level_rules:
                if level_rule.level_name == level:
                    if level_rule.homeworld_access_rule is not None and not level_rule.homeworld_access_rule(state):
                        return 0
                    if level_rule.access_rule is not None and not level_rule.access_rule(state):
                        return 0
                    gems = 400
                    for gem_restriction in level_rule.gem_rules.restrictions:
                        if gem_restriction.restriction_lambda is not None and not gem_restriction.restriction_lambda(state):
                            gems -= gem_restriction.gems_restricted
                    return gems
            return 0

        def has_total_accessible_gems(self, state, max_gems):
            accessible_gems = 0

            for level in self.all_levels:
                accessible_gems += get_gems_accessible_in_level(self, level, state)

            if not logic.is_boss_defeated("Ripto", state):
                # Remove gems for possible Moneybags payments.  To avoid a player locking themselves out of progression,
                # we have to assume every possible payment is made, including where the player can skip into the level
                # out of logic and then pay Moneybags.
                # Moneybags for Glimmer is free, as well as when gemsanity or level locks is on and moneybagssanity is not.
                # TODO: Add Dragon Shores theater logic.
                if self.options.moneybags_settings == MoneybagsOptions.VANILLA and \
                    self.options.enable_gemsanity.value == GemsanityOptions.OFF and \
                    self.options.level_lock_options.value == LevelLockOptions.VANILLA:
                    # Total gem checks probably don't make sense under these settings.
                    accessible_gems -= 4000
            return accessible_gems >= max_gems

        def set_indirect_rule(self, regionName, rule):
            region = self.multiworld.get_region(regionName, self.player)
            entrance = self.multiworld.get_entrance(regionName, self.player)
            set_rule(entrance, rule)
            self.multiworld.register_indirect_condition(region, entrance)
         
        for region in self.multiworld.get_regions(self.player):
            for location in region.locations:
                    set_rule(location, lambda state: True)

        if self.options.goal.value == GoalOptions.RIPTO:
            self.multiworld.completion_condition[self.player] = lambda state: logic.is_boss_defeated("Ripto", state) and state.has("Orb", self.player, self.options.ripto_door_orbs.value)
        elif self.options.goal.value == GoalOptions.SIXTY_FOUR_ORB:
            self.multiworld.completion_condition[self.player] = lambda state: logic.is_boss_defeated("Ripto", state) and state.has("Orb", self.player, 64)
        elif self.options.goal.value == GoalOptions.HUNDRED_PERCENT and not self.options.enable_open_world.value:
            self.multiworld.completion_condition[self.player] = lambda state: logic.is_boss_defeated("Ripto", state) and state.has("Summer Forest Talisman", self.player, 6) and state.has("Autumn Plains Talisman", self.player, 8) and state.has("Orb", self.player, 64) and has_total_accessible_gems(self, state, 10000)
        elif self.options.goal.value == GoalOptions.HUNDRED_PERCENT and self.options.enable_open_world.value:
            self.multiworld.completion_condition[self.player] = lambda state: logic.is_boss_defeated("Ripto", state) and state.has("Orb", self.player, 64) and has_total_accessible_gems(self, state, 10000)
        elif self.options.goal.value == GoalOptions.TEN_TOKENS:
            self.multiworld.completion_condition[self.player] = lambda state: state.has("Dragon Shores Token", self.player, 10) and state.has("Orb", self.player, 55) and has_total_accessible_gems(self, state, 8000)
        elif self.options.goal.value == GoalOptions.ALL_SKILLPOINTS:
            self.multiworld.completion_condition[self.player] = lambda state: state.has("Skill Point", self.player, 16)
        elif self.options.goal.value == GoalOptions.EPILOGUE:
            self.multiworld.completion_condition[self.player] = lambda state: logic.is_boss_defeated("Ripto", state) and state.has("Skill Point", self.player, 16)

        for level_rules in all_level_rules:
            level = level_rules.level_name
            if level_rules.access_rule is not None:
                set_indirect_rule(self, level, level_rules.access_rule)
            if level_rules.talisman_rule is not None:
                set_rule(
                    self.multiworld.get_location(f"{level}: Talisman", self.player),
                    level_rules.talisman_rule
                )
            for orb_name in level_rules.orbs:
                if level_rules.orbs[orb_name] is not None:
                    set_rule(
                        self.multiworld.get_location(orb_name, self.player),
                        level_rules.orbs[orb_name]
                    )
            for moneybags_name in level_rules.moneybags_locations:
                if Spyro2LocationCategory.MONEYBAGS in self.enabled_location_categories and \
                        level_rules.moneybags_locations[moneybags_name] is not None:
                    set_rule(
                        self.multiworld.get_location(moneybags_name, self.player),
                        level_rules.moneybags_locations[moneybags_name]
                    )
            for life_bottle_name in level_rules.life_bottles:
                if Spyro2LocationCategory.LIFE_BOTTLE in self.enabled_location_categories and \
                        level_rules.life_bottles[life_bottle_name] is not None:
                    set_rule(
                        self.multiworld.get_location(life_bottle_name, self.player),
                        level_rules.life_bottles[life_bottle_name]
                    )
            if Spyro2LocationCategory.SKILLPOINT in self.enabled_location_categories:
                for skillpoint_name in level_rules.skill_points:
                    if level_rules.skill_points[skillpoint_name] is not None:
                        set_rule(
                            self.multiworld.get_location(f"{skillpoint_name} (Skill Point)", self.player),
                            level_rules.skill_points[skillpoint_name]
                        )
            if Spyro2LocationCategory.SKILLPOINT_GOAL in self.enabled_location_categories:
                for skillpoint_name in level_rules.skill_points:
                    if level_rules.skill_points[skillpoint_name] is not None:
                        set_rule(
                            self.multiworld.get_location(f"{skillpoint_name} (Goal)", self.player),
                            level_rules.skill_points[skillpoint_name]
                        )
            if Spyro2LocationCategory.SPIRIT_PARTICLE in self.enabled_location_categories:
                if level_rules.spirit_particles_rule is not None:
                    set_rule(
                        self.multiworld.get_location(f"{level}: All Spirit Particles", self.player),
                        level_rules.spirit_particles_rule
                    )
            if Spyro2LocationCategory.GEM in self.enabled_location_categories:
                # Bits of the gems, not accounting for empty bits
                empty_bits = level_rules.gem_rules.empty_bits
                for gem_restriction in level_rules.gem_rules.restrictions:
                    restriction_bits = gem_restriction.bits
                    for gem in restriction_bits:
                        skipped_bits = 0
                        for bit in empty_bits:
                            if bit < gem:
                                skipped_bits += 1
                            else:
                                break
                        if self.PRINT_GEM_REQS:
                            print(f"{level}: Gem {gem - skipped_bits} requires {gem_restriction.restriction_text}.")
                        if gem_restriction.restriction_lambda is not None and \
                            (
                                len(self.chosen_gem_locations) == 0 or
                                f"{level}: Gem {gem - skipped_bits}" in self.chosen_gem_locations
                            ):
                            set_rule(
                                self.multiworld.get_location(f"{level}: Gem {gem - skipped_bits}", self.player),
                                gem_restriction.restriction_lambda
                            )

        # Dragon Shores rules
        set_indirect_rule(self, "Dragon Shores", lambda state: logic.can_enter_shores(state))
        if Spyro2LocationCategory.SHORES_TOKEN in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Dragon Shores: Tunnel o' Love", self.player),
                lambda state: has_total_accessible_gems(self, state, 8000) and state.has("Orb", self.player, 55)
            )
        if Spyro2LocationCategory.SHORES_TOKEN in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Dragon Shores: Shooting Gallery I", self.player),
                lambda state: has_total_accessible_gems(self, state, 8000) and state.has("Orb", self.player, 55)
            )
        if Spyro2LocationCategory.SHORES_TOKEN in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Dragon Shores: Shooting Gallery II", self.player),
                lambda state: has_total_accessible_gems(self, state, 8000) and state.has("Orb", self.player, 55)
            )
        if Spyro2LocationCategory.SHORES_TOKEN in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Dragon Shores: Shooting Gallery III", self.player),
                lambda state: has_total_accessible_gems(self, state, 8000) and state.has("Orb", self.player, 55)
            )
        if Spyro2LocationCategory.SHORES_TOKEN in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Dragon Shores: Rollercoaster I", self.player),
                lambda state: has_total_accessible_gems(self, state, 8000) and state.has("Orb", self.player, 55)
            )
        if Spyro2LocationCategory.SHORES_TOKEN in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Dragon Shores: Rollercoaster II", self.player),
                lambda state: has_total_accessible_gems(self, state, 8000) and state.has("Orb", self.player, 55)
            )
        if Spyro2LocationCategory.SHORES_TOKEN in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Dragon Shores: Rollercoaster III", self.player),
                lambda state: has_total_accessible_gems(self, state, 8000) and state.has("Orb", self.player, 55)
            )
        if Spyro2LocationCategory.SHORES_TOKEN in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Dragon Shores: Dunk Tank I", self.player),
                lambda state: has_total_accessible_gems(self, state, 8000) and state.has("Orb", self.player, 55)
            )
        if Spyro2LocationCategory.SHORES_TOKEN in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Dragon Shores: Dunk Tank II", self.player),
                lambda state: has_total_accessible_gems(self, state, 8000) and state.has("Orb", self.player, 55)
            )
        if Spyro2LocationCategory.SHORES_TOKEN in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Dragon Shores: Dunk Tank III", self.player),
                lambda state: has_total_accessible_gems(self, state, 8000) and state.has("Orb", self.player, 55)
            )

        # Level Gem Count rules
        for level in self.all_levels:
            if level in ["Crush's Dungeon", "Gulp's Overlook", "Dragon Shores", "Ripto's Arena"]:
                continue
            if Spyro2LocationCategory.GEM_25 in self.enabled_location_categories:
                set_rule(
                    self.multiworld.get_location(f"{level}: 25% Gems", self.player),
                    lambda state, level=level: get_gems_accessible_in_level(self, level, state) >= 100
                )
            if Spyro2LocationCategory.GEM_50 in self.enabled_location_categories:
                set_rule(
                    self.multiworld.get_location(f"{level}: 50% Gems", self.player),
                    lambda state, level=level: get_gems_accessible_in_level(self, level, state) >= 200
                )
            if Spyro2LocationCategory.GEM_75 in self.enabled_location_categories:
                set_rule(
                    self.multiworld.get_location(f"{level}: 75% Gems", self.player),
                    lambda state, level=level: get_gems_accessible_in_level(self, level, state) >= 300
                )
            if Spyro2LocationCategory.GEM_100 in self.enabled_location_categories:
                set_rule(
                    self.multiworld.get_location(f"{level}: All Gems", self.player),
                    lambda state, level=level: get_gems_accessible_in_level(self, level, state) >= 400
                )

        # Inventory rules
        if Spyro2LocationCategory.TOTAL_GEM in self.enabled_location_categories:
            for i in range(20):
                gems = 500 * (i + 1)
                if gems <= self.options.max_total_gem_checks.value:
                    set_rule(
                        self.multiworld.get_location(f"Total Gems: {gems}", self.player),
                        lambda state, gems=gems: has_total_accessible_gems(self, state, gems)
                    )
                else:
                    break

    # Universal Tracker Support
    def interpret_slot_data(self, slot_data):
        return slot_data

    def fill_slot_data(self) -> Dict[str, object]:
        slot_data: Dict[str, object] = {}


        name_to_s2_code = {item.name: item.s2_code for item in item_dictionary.values()}
        # Create the mandatory lists to generate the player's output file
        items_id = []
        items_address = []
        locations_id = []
        locations_address = []
        locations_target = []
        
        for location in self.multiworld.get_filled_locations():


            if location.item.player == self.player:
                #we are the receiver of the item
                items_id.append(location.item.code)
                items_address.append(name_to_s2_code[location.item.name])


            if location.player == self.player:
                #we are the sender of the location check
                locations_address.append(item_dictionary[location_dictionary[location.name].default_item].s2_code)
                locations_id.append(location.address)
                if location.item.player == self.player:
                    locations_target.append(name_to_s2_code[location.item.name])
                else:
                    locations_target.append(0)

        gemsanity_locations = []
        for loc in self.chosen_gem_locations:
            loc_id = self.location_name_to_id[loc]
            gemsanity_locations.append(loc_id)

        colors = [
            [0x00000040, 0x002000ff],  # Red
            [0x00104808, 0x0020ff00],  # Green
            [0x00480020, 0x00ff0080],  # Blue/Purple
            [0x00005066, 0x0000c0ff],  # Gold
            [0x00240034, 0x008000c0],  # Magenta
        ]
        if self.options.gem_color.value == RandomizeGemColorOptions.SHUFFLE:
            self.random.shuffle(colors)
        elif self.options.gem_color.value == RandomizeGemColorOptions.RANDOM:
            colors = colors + [
                [0x00003848, 0x002060ff],  # Orange
                [0x00482400, 0x00ff9000],  # Cyan
                [0x00160826, 0x00642288],  # Violet
                [0x00801490, 0x004314ff],  # Hot Pink
                [0x00202626, 0x00c0c0c0],  # Silver
                [0x000a2026, 0x0000d7ff],  # Gold
                [0x0000a050, 0x0000fc7c],  # Neon Green
                [0x00808000, 0x00808000],  # Teal
            ]
            self.random.shuffle(colors)
        elif self.options.gem_color.value == RandomizeGemColorOptions.TRUE_RANDOM:
            colors = [
                [self.random.randint(0, 16777216), self.random.randint(0, 16777216)],
                [self.random.randint(0, 16777216), self.random.randint(0, 16777216)],
                [self.random.randint(0, 16777216), self.random.randint(0, 16777216)],
                [self.random.randint(0, 16777216), self.random.randint(0, 16777216)],
                [self.random.randint(0, 16777216), self.random.randint(0, 16777216)],
            ]

        slot_data = {
            "options": {
                "goal": self.options.goal.value,
                "guaranteed_items": self.options.guaranteed_items.value,
                "ripto_door_orbs": self.options.ripto_door_orbs.value,
                "enable_open_world": self.options.enable_open_world.value,
                "open_world_warp_unlocks": self.options.open_world_warp_unlocks.value,
                "start_with_abilities": self.options.start_with_abilities.value,
                "wt_warp_options": self.options.wt_warp_options.value,
                "level_lock_options": self.options.level_lock_options.value,
                "level_unlocks": self.options.level_unlocks.value,
                "enable_25_pct_gem_checks": self.options.enable_25_pct_gem_checks.value,
                "enable_50_pct_gem_checks": self.options.enable_50_pct_gem_checks.value,
                "enable_75_pct_gem_checks": self.options.enable_75_pct_gem_checks.value,
                "enable_gem_checks": self.options.enable_gem_checks.value,
                "enable_total_gem_checks": self.options.enable_total_gem_checks.value,
                "max_total_gem_checks": self.options.max_total_gem_checks.value,
                "enable_skillpoint_checks": self.options.enable_skillpoint_checks.value,
                "enable_life_bottle_checks": self.options.enable_life_bottle_checks.value,
                "enable_spirit_particle_checks": self.options.enable_spirit_particle_checks.value,
                "enable_gemsanity": self.options.enable_gemsanity.value,
                "gemsanity_item_locations": self.options.gemsanity_item_locations.value,
                "gemsanity_reward_type": self.options.gemsanity_reward_type.value,
                "gemsanity_gem_bundle_size": self.options.gemsanity_gem_bundle_size.value,
                "moneybags_settings": self.options.moneybags_settings.value,
                "death_link": self.options.death_link.value,
                "enable_filler_extra_lives": self.options.enable_filler_extra_lives.value,
                "enable_destructive_spyro_filler": self.options.enable_destructive_spyro_filler.value,
                "enable_filler_color_change": self.options.enable_filler_color_change.value,
                "enable_filler_big_head_mode": self.options.enable_filler_big_head_mode.value,
                "enable_filler_heal_sparx": self.options.enable_filler_heal_sparx.value,
                "trap_filler_percent": self.options.trap_filler_percent.value,
                "enable_trap_damage_sparx": self.options.enable_trap_damage_sparx.value,
                "enable_trap_sparxless": self.options.enable_trap_sparxless.value,
                "enable_trap_invisibility": self.options.enable_trap_invisibility.value,
                "enable_progressive_sparx_health": self.options.enable_progressive_sparx_health.value,
                "enable_progressive_sparx_logic": self.options.enable_progressive_sparx_logic.value,
                "double_jump_ability": self.options.double_jump_ability.value,
                "permanent_fireball_ability": self.options.permanent_fireball_ability.value,
                "trick_difficulty": self.options.trick_difficulty.value,
                "custom_tricks": self.options.custom_tricks.value,
                "colossus_starting_goals": self.options.colossus_starting_goals.value,
                "idol_easy_fish": self.options.idol_easy_fish.value,
                "hurricos_easy_lightning_orbs": self.options.hurricos_easy_lightning_orbs.value,
                "breeze_required_gears": self.options.breeze_required_gears.value,
                "scorch_bombo_settings": self.options.scorch_bombo_settings.value,
                "fracture_require_headbash": self.options.fracture_require_headbash.value,
                "fracture_easy_earthshapers": self.options.fracture_easy_earthshapers.value,
                "magma_spyro_starting_popcorn": self.options.magma_spyro_starting_popcorn.value,
                "magma_hunter_starting_popcorn": self.options.magma_hunter_starting_popcorn.value,
                "shady_require_headbash": self.options.shady_require_headbash.value,
                "easy_gulp": self.options.easy_gulp.value,
                "portal_gem_collection_color": self.options.portal_gem_collection_color.value,
                "gem_color": self.options.gem_color.value,
                "red_gem_shadow_color": colors[0][0],
                "red_gem_color": colors[0][1],
                "green_gem_shadow_color": colors[1][0],
                "green_gem_color": colors[1][1],
                "blue_gem_shadow_color": colors[2][0],
                "blue_gem_color": colors[2][1],
                "gold_gem_shadow_color": colors[3][0],
                "gold_gem_color": colors[3][1],
                "pink_gem_shadow_color": colors[4][0],
                "pink_gem_color": colors[4][1],
            },
            "gemsanity_ids": gemsanity_locations,
            "level_orb_requirements": self.level_orb_requirements,
            "key_locked_levels": self.key_locked_levels,
            "seed": self.multiworld.seed_name,  # to verify the server's multiworld
            "slot": self.multiworld.player_name[self.player],  # to connect to server
            "base_id": self.base_id,  # to merge location and items lists
            "locationsId": locations_id,
            "locationsAddress": locations_address,
            "locationsTarget": locations_target,
            "itemsId": items_id,
            "itemsAddress": items_address,
            "apworldVersion": self.ap_world_version,
        }

        return slot_data
