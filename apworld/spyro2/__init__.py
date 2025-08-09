# world/spyro2/__init__.py
from typing import Dict, Set, List

from BaseClasses import MultiWorld, Region, Item, Entrance, Tutorial, ItemClassification

from worlds.AutoWorld import World, WebWorld
from worlds.generic.Rules import set_rule, add_rule, add_item_rule, forbid_item

from .Items import Spyro2Item, Spyro2ItemCategory, item_dictionary, key_item_names, item_descriptions, BuildItemPool
from .Locations import Spyro2Location, Spyro2LocationCategory, location_tables, location_dictionary
from .Options import Spyro2Option, GoalOptions, MoneybagsOptions, SparxUpgradeOptions, AbilityOptions, LogicTrickOptions, spyro_options_groups


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
    enabled_hint_locations = []
    required_client_version = (0, 5, 0)
    item_name_to_id = Spyro2Item.get_name_to_id()
    location_name_to_id = Spyro2Location.get_name_to_id()
    item_name_groups = {}
    item_descriptions = item_descriptions

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

    def generate_early(self):
        self.enabled_location_categories.add(Spyro2LocationCategory.TALISMAN)
        self.enabled_location_categories.add(Spyro2LocationCategory.ORB)
        self.enabled_location_categories.add(Spyro2LocationCategory.EVENT)
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
        if self.options.goal.value == GoalOptions.TEN_TOKENS:
            self.enabled_location_categories.add(Spyro2LocationCategory.SHORES_TOKEN)
        # Use the Moneybags unlocks for logic if they are in place.  The checks themselves will not be randomized.
        if self.options.moneybags_settings.value != MoneybagsOptions.MONEYBAGSSANITY:
            self.enabled_location_categories.add(Spyro2LocationCategory.MONEYBAGS)

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
                    location.category not in [Spyro2LocationCategory.EVENT, Spyro2LocationCategory.TOTAL_GEM]:
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

        foo = BuildItemPool(self.multiworld, itempoolSize, self.options)
        for item in foo:
            itempool.append(self.create_item(item.name))

        # Add regular items to itempool
        self.multiworld.itempool += itempool

    def create_item(self, name: str) -> Item:
        data = self.item_name_to_id[name]
        useful_categories = {}

        if name in key_item_names or \
                item_dictionary[name].category in [Spyro2ItemCategory.TALISMAN, Spyro2ItemCategory.ORB, Spyro2ItemCategory.EVENT, Spyro2ItemCategory.MONEYBAGS, Spyro2ItemCategory.SKILLPOINT_GOAL, Spyro2ItemCategory.TOKEN] or \
                self.options.enable_progressive_sparx_logic.value and name == 'Progressive Sparx Health Upgrade':
            item_classification = ItemClassification.progression
        elif item_dictionary[name].category in useful_categories or \
                not self.options.enable_progressive_sparx_logic.value and name == 'Progressive Sparx Health Upgrade' or \
                name in ["Double Jump Ability", "Permanent Fireball Ability"]:
            item_classification = ItemClassification.useful
        elif item_dictionary[name].category == Spyro2ItemCategory.TRAP:
            item_classification = ItemClassification.trap
        else:
            item_classification = ItemClassification.filler

        return Spyro2Item(name, item_classification, data, self.player)

    def get_filler_item_name(self) -> str:
        return "Orb"
    
    def set_rules(self) -> None:
        def is_boss_defeated(self, boss, state):
            return state.has(boss + " Defeated", self.player)

        def get_gems_accessible_in_level(self, level, state):
            # Older versions of Python do not support switch statements, so use if/elif.
            if level == 'Glimmer':
                gems = 353
                if state.has("Moneybags Unlock - Climb", self.player):
                    # Upper level in cave; technically accessible with double jump
                    gems += 47
                return gems
            elif level == 'Summer Forest':
                gems = 155
                if state.has("Moneybags Unlock - Swim", self.player):
                    # TODO: Count underwater gems for DJ logic.
                    gems += 221
                    if state.has("Moneybags Unlock - Door to Aquaria Towers", self.player):
                        gems += 14
                    if state.has("Moneybags Unlock - Climb", self.player):
                        gems += 10
                return gems
            elif level == 'Idol Springs':
                # Probably 315, but gem RNG from the strong chest could impact this - remove those gems from logic.
                gems = 298
                if state.has("Moneybags Unlock - Swim", self.player):
                    gems += 102
                return gems
            elif level == 'Colossus':
                return 400
            elif level == 'Hurricos':
                if not state.has("Moneybags Unlock - Swim", self.player):
                    return 0
                return 400
            elif level == 'Aquaria Towers':
                if not state.has("Moneybags Unlock - Swim", self.player) or \
                        not state.has("Moneybags Unlock - Door to Aquaria Towers", self.player) or \
                        (self.options.enable_progressive_sparx_logic.value and not has_sparx_health(self, 1, state)):
                    return 0
                # TODO: Allow for getting in without swim as a trick.
                gems = 127
                if state.has("Moneybags Unlock - Aquaria Towers Submarine", self.player):
                    gems += 273
                return gems
            elif level == "Sunny Beach":
                if not state.has("Moneybags Unlock - Swim", self.player):
                    return 0
                # TODO: Allow for getting in without swim.
                gems = 380
                if state.has("Moneybags Unlock - Climb", self.player):
                    gems += 20
                return gems
            elif level == "Ocean Speedway":
                if not state.has("Moneybags Unlock - Swim", self.player) or not state.has("Orb", self.player, 3):
                    return 0
                return 400
            elif level == "Autumn Plains":
                if not is_boss_defeated(self, "Crush", state):
                    return 0
                gems = 118
                if state.has("Orb", self.player, 6):
                    gems += 22
                if state.has("Moneybags Unlock - Climb", self.player):
                    gems += 51
                    if state.has("Orb", self.player, 8):
                        gems += 202
                        if state.has("Moneybags Unlock - Shady Oasis Portal", self.player):
                            gems += 7
                return gems
            elif level == "Skelos Badlands":
                if not is_boss_defeated(self, "Crush", state) or \
                        (self.options.enable_progressive_sparx_logic.value and not has_sparx_health(self, 2, state)):
                    return 0
                return 400
            elif level == "Crystal Glacier":
                if not is_boss_defeated(self, "Crush", state):
                    return 0
                gems = 245
                if state.has("Moneybags Unlock - Crystal Glacier Bridge", self.player):
                    gems += 155
                return gems
            elif level == "Breeze Harbor":
                if not is_boss_defeated(self, "Crush", state):
                    return 0
                return 400
            elif level == "Zephyr":
                if not is_boss_defeated(self, "Crush", state) or \
                        not state.has("Moneybags Unlock - Zephyr Portal", self.player):
                    return 0
                gems = 284
                if state.has("Moneybags Unlock - Climb", self.player):
                    gems += 116
                return gems
            elif level == "Metro Speedway":
                if not is_boss_defeated(self, "Crush", state) or not state.has("Orb", self.player, 6):
                    return 0
                return 400
            elif level == "Scorch":
                if not is_boss_defeated(self, "Crush", state) or not state.has("Moneybags Unlock - Climb", self.player):
                    return 0
                return 400
            elif level == "Shady Oasis":
                if not is_boss_defeated(self, "Crush", state) or \
                        not state.has("Moneybags Unlock - Climb", self.player) or \
                        not state.has("Orb", self.player, 8) or \
                        not state.has("Moneybags Unlock - Shady Oasis Portal", self.player):
                    return 0
                gems = 380
                if state.has("Moneybags Unlock - Headbash", self.player):
                    gems += 20
                return gems
            elif level == "Magma Cone":
                if not is_boss_defeated(self, "Crush", state) or \
                        not state.has("Moneybags Unlock - Climb", self.player) or \
                        not state.has("Orb", self.player, 8):
                    return 0
                gems = 295
                if state.has("Moneybags Unlock - Magma Cone Elevator", self.player):
                    gems += 105
                return 400
            elif level == "Fracture Hills":
                if not is_boss_defeated(self, "Crush", state) or not state.has("Moneybags Unlock - Climb", self.player):
                    return 0
                return 400
            elif level == "Icy Speedway":
                if not is_boss_defeated(self, "Crush", state) or \
                        not state.has("Moneybags Unlock - Climb", self.player) or \
                        not state.has("Orb", self.player, 8) or \
                        not state.has("Moneybags Unlock - Icy Speedway Portal", self.player):
                    return 0
                return 400
            elif level == "Winter Tundra":
                if not is_boss_defeated(self, "Gulp", state):
                    return 0
                gems = 139
                if state.has("Moneybags Unlock - Headbash", self.player):
                    gems += 261
                return 400
            elif level == "Mystic Marsh":
                if not is_boss_defeated(self, "Gulp", state):
                    return 0
                return 400
            elif level == "Cloud Temples":
                if not is_boss_defeated(self, "Gulp", state):
                    return 0
                gems = 375
                if state.has("Moneybags Unlock - Headbash", self.player):
                    gems += 25
                return gems
            elif level == "Canyon Speedway":
                if not is_boss_defeated(self, "Gulp", state) or \
                        not state.has("Moneybags Unlock - Canyon Speedway Portal", self.player):
                    return 0
                return 400
            elif level == "Robotica Farms":
                if not is_boss_defeated(self, "Gulp", state) or \
                        not state.has("Moneybags Unlock - Headbash", self.player):
                    return 0
                return 400
            elif level == "Metropolis":
                if not is_boss_defeated(self, "Gulp", state) or \
                        not state.has("Moneybags Unlock - Headbash", self.player):
                    return 0
                return 400
            return 0

        def has_total_accessible_gems(self, state, max_gems):
            accessible_gems = 0

            for level in self.all_levels:
                accessible_gems += get_gems_accessible_in_level(self, level, state)

            if not is_boss_defeated(self, "Ripto", state):
                # Remove gems for possible Moneybags payments.  To avoid a player locking themselves out of progression,
                # we have to assume every possible payment is made, including where the player can skip into the level
                # out of logic and then pay Moneybags.
                # TODO: Add Dragon Shores theater logic.
                if self.options.moneybags_settings == MoneybagsOptions.VANILLA:
                    # Total gem checks probably don't make sense under these settings.
                    accessible_gems -= 4100
                elif self.options.moneybags_settings == MoneybagsOptions.MONEYBAGSSANITY:
                    # Glimmer bridge is vanilla to avoid a 1 check sphere 0.
                    accessible_gems -= 100
            return accessible_gems >= max_gems

        def has_sparx_health(self, health, state):
            if self.options.enable_progressive_sparx_health.value in [SparxUpgradeOptions.OFF, SparxUpgradeOptions.TRUE_SPARXLESS]:
                return True
            max_health = 0
            if self.options.enable_progressive_sparx_health.value == SparxUpgradeOptions.BLUE:
                max_health = 2
            elif self.options.enable_progressive_sparx_health.value == SparxUpgradeOptions.GREEN:
                max_health = 1
            max_health += state.count("Progressive Sparx Health Upgrade", self.player)
            return max_health >= health
            
        def set_indirect_rule(self, regionName, rule):
            region = self.multiworld.get_region(regionName, self.player)
            entrance = self.multiworld.get_entrance(regionName, self.player)
            set_rule(entrance, rule)
            self.multiworld.register_indirect_condition(region, entrance)
         
        for region in self.multiworld.get_regions(self.player):
            for location in region.locations:
                    set_rule(location, lambda state: True)

        if self.options.goal.value == GoalOptions.RIPTO:
            self.multiworld.completion_condition[self.player] = lambda state: is_boss_defeated(self, "Ripto", state)
        elif self.options.goal.value == GoalOptions.FOURTEEN_TALISMAN:
            self.multiworld.completion_condition[self.player] = lambda state: is_boss_defeated(self, "Ripto", state) and state.has("Summer Forest Talisman", self.player, 6) and state.has("Autumn Plains Talisman", self.player, 8)
        elif self.options.goal.value == GoalOptions.FORTY_ORB:
            self.multiworld.completion_condition[self.player] = lambda state: is_boss_defeated(self, "Ripto", state) and state.has("Orb", self.player, 40)
        elif self.options.goal.value == GoalOptions.SIXTY_FOUR_ORB:
            self.multiworld.completion_condition[self.player] = lambda state: is_boss_defeated(self, "Ripto", state) and state.has("Orb", self.player, 64)
        elif self.options.goal.value == GoalOptions.HUNDRED_PERCENT:
            self.multiworld.completion_condition[self.player] = lambda state: is_boss_defeated(self, "Ripto", state) and state.has("Summer Forest Talisman", self.player, 6) and state.has("Autumn Plains Talisman", self.player, 8) and state.has("Orb", self.player, 64) and has_total_accessible_gems(self, state, 10000)
        elif self.options.goal.value == GoalOptions.TEN_TOKENS:
            self.multiworld.completion_condition[self.player] = lambda state: state.has("Dragon Shores Token", self.player, 10)
        elif self.options.goal.value == GoalOptions.ALL_SKILLPOINTS:
            self.multiworld.completion_condition[self.player] = lambda state: state.has("Skill Point", self.player, 16)
        elif self.options.goal.value == GoalOptions.EPILOGUE:
            self.multiworld.completion_condition[self.player] = lambda state: is_boss_defeated(self, "Ripto", state) and state.has("Skill Point", self.player, 16)

        # Summer Forest Rules
        # TODO: Change logic based on tricks.
        set_rule(
            self.multiworld.get_location("Summer Forest: On a secret ledge", self.player),
            lambda state: state.has("Moneybags Unlock - Swim", self.player)
        )
        set_rule(
            self.multiworld.get_location("Summer Forest: Atop a ladder", self.player),
            lambda state: state.has("Moneybags Unlock - Climb", self.player)
        )
        set_rule(
            self.multiworld.get_location("Summer Forest: Behind the door", self.player),
            lambda state: state.has("Moneybags Unlock - Swim", self.player)
        )
        if Spyro2LocationCategory.GEM_50 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Summer Forest: 50% Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Summer Forest", state) >= 200
            )
        if Spyro2LocationCategory.GEM_75 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Summer Forest: 75% Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Summer Forest", state) >= 300
            )
        if Spyro2LocationCategory.GEM_100 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Summer Forest: All Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Summer Forest", state) >= 400
            )
        if Spyro2LocationCategory.MONEYBAGS in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Summer Forest: Moneybags Unlock: Door to Aquaria Towers", self.player),
                lambda state: state.has("Moneybags Unlock - Swim", self.player)
            )

        # Glimmer Rules
        set_rule(
            self.multiworld.get_location("Glimmer: Gem Lamp Flight in cave", self.player),
            lambda state: state.has("Moneybags Unlock - Climb", self.player)
        )
        if Spyro2LocationCategory.GEM_100 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Glimmer: All Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Glimmer", state) >= 400
            )

        # Idol Springs Rules
        set_rule(
            self.multiworld.get_location("Idol Springs: Foreman Bud's puzzles", self.player),
            lambda state: state.has("Moneybags Unlock - Swim", self.player)
        )
        if Spyro2LocationCategory.GEM_75 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Idol Springs: 75% Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Idol Springs", state) >= 300
            )
        if Spyro2LocationCategory.GEM_100 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Idol Springs: All Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Idol Springs", state) >= 400
            )

        # Colossus Rules

        # Hurricos Rules
        set_indirect_rule(self, "Hurricos", lambda state: state.has("Moneybags Unlock - Swim", self.player))

        # Aquaria Towers Rules
        if self.options.enable_progressive_sparx_logic.value:
            set_indirect_rule(
                self,
                "Aquaria Towers",
                lambda state: state.has("Moneybags Unlock - Swim", self.player) and state.has("Moneybags Unlock - Door to Aquaria Towers", self.player) and has_sparx_health(self, 1, state)
            )
        else:
            set_indirect_rule(
                self,
                "Aquaria Towers",
                lambda state: state.has("Moneybags Unlock - Swim", self.player) and state.has("Moneybags Unlock - Door to Aquaria Towers", self.player)
            )

        # Sunny Beach rules
        set_indirect_rule(self, "Sunny Beach", lambda state: state.has("Moneybags Unlock - Swim", self.player))
        set_rule(
            self.multiworld.get_location("Sunny Beach: Turtle soup I", self.player),
            lambda state: state.has("Moneybags Unlock - Climb", self.player)
        )
        set_rule(
            self.multiworld.get_location("Sunny Beach: Turtle soup II", self.player),
            lambda state: state.has("Moneybags Unlock - Climb", self.player)
        )
        if Spyro2LocationCategory.GEM_100 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Sunny Beach: All Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Sunny Beach", state) >= 400
            )

        # Ocean Speedway rules
        set_indirect_rule(
            self,
            "Ocean Speedway",
            lambda state: state.has("Moneybags Unlock - Swim", self.player) and state.has("Orb", self.player, 3)
        )

        # Crush's Dungeon rules
        # TODO: It is likely that the client implementation will make swim not required because Elora will warp
        #  the player. But this complicates the logic significantly.
        if self.options.logic_crush_early.value == LogicTrickOptions.ALWAYS_ON or self.options.logic_crush_early.value == LogicTrickOptions.ON_WITH_DOUBLE_JUMP and self.options.double_jump_ability.value == AbilityOptions.VANILLA:
            if self.options.enable_progressive_sparx_logic.value:
                set_indirect_rule(
                    self,
                    "Crush's Dungeon",
                    lambda state: state.has("Moneybags Unlock - Swim", self.player) and has_sparx_health(self, 1, state)
                )
            else:
                set_indirect_rule(
                    self,
                    "Crush's Dungeon",
                    lambda state: state.has("Moneybags Unlock - Swim", self.player)
                )
        elif self.options.logic_crush_early.value == LogicTrickOptions.ON_WITH_DOUBLE_JUMP:
            if self.options.enable_progressive_sparx_logic.value:
                set_indirect_rule(
                    self,
                    "Crush's Dungeon",
                    lambda state: state.has("Moneybags Unlock - Swim", self.player) and has_sparx_health(self, 1, state) and (state.has("Double Jump Ability", self.player) or state.has("Summer Forest Talisman", self.player, 6))
                )
            else:
                set_indirect_rule(
                    self,
                    "Crush's Dungeon",
                    lambda state: state.has("Moneybags Unlock - Swim", self.player) and (state.has("Double Jump Ability", self.player) or state.has("Summer Forest Talisman", self.player, 6))
                )
        else:
            if self.options.enable_progressive_sparx_logic.value:
                set_indirect_rule(
                    self,
                    "Crush's Dungeon",
                    lambda state: state.has("Moneybags Unlock - Swim", self.player) and state.has("Summer Forest Talisman", self.player, 6) and has_sparx_health(self, 1, state)
                )
            else:
                set_indirect_rule(
                    self,
                    "Crush's Dungeon",
                    lambda state: state.has("Moneybags Unlock - Swim", self.player) and state.has("Summer Forest Talisman", self.player, 6)
                )

        # Autumn Plains Rules
        set_indirect_rule(self, "Autumn Plains", lambda state: is_boss_defeated(self, "Crush", state))
        set_rule(
            self.multiworld.get_location("Autumn Plains: The end of the wall", self.player),
            lambda state: state.has("Orb", self.player, 6)
        )
        set_rule(
            self.multiworld.get_location("Autumn Plains: Long glide!", self.player),
            lambda state: state.has("Moneybags Unlock - Climb", self.player) and state.has("Orb", self.player, 8)
        )
        if Spyro2LocationCategory.GEM_50 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Autumn Plains: 50% Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Autumn Plains", state) >= 200
            )
        if Spyro2LocationCategory.GEM_75 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Autumn Plains: 75% Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Autumn Plains", state) >= 300
            )
        if Spyro2LocationCategory.GEM_100 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Autumn Plains: All Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Autumn Plains", state) >= 400
            )
        if Spyro2LocationCategory.MONEYBAGS in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Autumn Plains: Moneybags Unlock: Shady Oasis Portal", self.player),
                lambda state: state.has("Moneybags Unlock - Climb", self.player) and state.has("Orb", self.player, 8)
            )
        if Spyro2LocationCategory.MONEYBAGS in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Autumn Plains: Moneybags Unlock: Icy Speedway Portal", self.player),
                lambda state: state.has("Moneybags Unlock - Climb", self.player) and state.has("Orb", self.player, 8)
            )

        # Skelos Badlands rules
        if self.options.enable_progressive_sparx_logic.value:
            set_indirect_rule(
                self,
                "Skelos Badlands",
                lambda state: has_sparx_health(self, 2, state)
            )

        # Crystal Glacier rules
        set_rule(
            self.multiworld.get_location("Crystal Glacier: Talisman", self.player),
            lambda state: state.has("Moneybags Unlock - Crystal Glacier Bridge", self.player)
        )
        set_rule(
            self.multiworld.get_location("Crystal Glacier: Draclet cave", self.player),
            lambda state: state.has("Moneybags Unlock - Crystal Glacier Bridge", self.player)
        )
        set_rule(
            self.multiworld.get_location("Crystal Glacier: George the snow leopard", self.player),
            lambda state: state.has("Moneybags Unlock - Crystal Glacier Bridge", self.player)
        )
        if Spyro2LocationCategory.GEM_75 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Crystal Glacier: 75% Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Crystal Glacier", state) >= 300
            )
        if Spyro2LocationCategory.GEM_100 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Crystal Glacier: All Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Crystal Glacier", state) >= 400
            )

        # Breeze Harbor rules

        # Zephyr rules
        set_indirect_rule(
            self,
            "Zephyr",
            lambda state: state.has("Moneybags Unlock - Zephyr Portal", self.player)
        )
        set_rule(
            self.multiworld.get_location("Zephyr: Cowlek corral II", self.player),
            lambda state: state.has("Moneybags Unlock - Climb", self.player)
        )
        if Spyro2LocationCategory.GEM_75 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Zephyr: 75% Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Zephyr", state) >= 300
            )
        if Spyro2LocationCategory.GEM_100 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Zephyr: All Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Zephyr", state) >= 400
            )

        # Metro Speedway rules
        set_indirect_rule(
            self,
            "Metro Speedway",
            lambda state: state.has("Orb", self.player, 6)
        )

        # Scorch rules
        set_indirect_rule(
            self,
            "Scorch",
            lambda state: state.has("Moneybags Unlock - Climb", self.player)
        )

        # Shady Oasis rules
        set_indirect_rule(
            self,
            "Scorch",
            lambda state: state.has("Moneybags Unlock - Climb", self.player) and state.has("Orb", self.player, 8) and state.has("Moneybags Unlock - Shady Oasis Portal", self.player)
        )
        set_rule(
            self.multiworld.get_location("Shady Oasis: Free Hippos", self.player),
            lambda state: state.has("Moneybags Unlock - Headbash", self.player)
        )
        if Spyro2LocationCategory.GEM_100 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Shady Oasis: All Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Shady Oasis", state) >= 400
            )

        # Magma Cone rules
        set_indirect_rule(
            self,
            "Scorch",
            lambda state: state.has("Moneybags Unlock - Climb", self.player) and state.has("Orb", self.player, 8)
        )
        set_rule(
            self.multiworld.get_location("Magma Cone: Talisman", self.player),
            lambda state: state.has("Moneybags Unlock - Magma Cone Elevator", self.player)
        )
        set_rule(
            self.multiworld.get_location("Magma Cone: Party crashers", self.player),
            lambda state: state.has("Moneybags Unlock - Magma Cone Elevator", self.player)
        )
        if Spyro2LocationCategory.GEM_75 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Magma Cone: 75% Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Magma Cone", state) >= 300
            )
        if Spyro2LocationCategory.GEM_100 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Magma Cone: All Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Magma Cone", state) >= 400
            )

        # Fracture Hills rules
        set_indirect_rule(
            self,
            "Fracture Hills",
            lambda state: state.has("Moneybags Unlock - Climb", self.player)
        )
        set_rule(
            self.multiworld.get_location("Fracture Hills: Earthshaper bash", self.player),
            lambda state: state.has("Moneybags Unlock - Headbash", self.player)
        )

        # Icy Speedway rules
        set_indirect_rule(
            self,
            "Icy Speedway",
            lambda state: state.has("Moneybags Unlock - Climb", self.player) and state.has("Orb", self.player, 8) and state.has("Moneybags Unlock - Icy Speedway Portal", self.player)
        )

        # Gulp's Overlook rules
        # TODO: The orb and climb requirements are likely not true because of Elora warping the player (or Gulp Skip).
        #  But this complicates logic substantially so ignore it for now.
        if self.options.logic_gulp_early.value == LogicTrickOptions.ALWAYS_ON or self.options.logic_gulp_early.value == LogicTrickOptions.ON_WITH_DOUBLE_JUMP and self.options.double_jump_ability.value == AbilityOptions.VANILLA:
            if self.options.enable_progressive_sparx_logic.value:
                set_indirect_rule(
                    self,
                    "Gulp's Overlook",
                    lambda state: state.has("Moneybags Unlock - Climb", self.player) and state.has("Orb", self.player, 8) and has_sparx_health(self, 2, state)
                )
            else:
                set_indirect_rule(
                    self,
                    "Gulp's Overlook",
                    lambda state: state.has("Moneybags Unlock - Climb", self.player) and state.has("Orb", self.player, 8)
                )
        elif self.options.logic_gulp_early.value == LogicTrickOptions.ON_WITH_DOUBLE_JUMP:
            if self.options.enable_progressive_sparx_logic.value:
                set_indirect_rule(
                    self,
                    "Gulp's Overlook",
                    lambda state: state.has("Moneybags Unlock - Climb", self.player) and state.has("Orb", self.player, 8) and (state.has("Double Jump Ability", self.player) or state.has("Summer Forest Talisman", self.player, 6) and state.has("Autumn Plains Talisman", self.player, 8)) and has_sparx_health(self, 2, state)
                )
            else:
                set_indirect_rule(
                    self,
                    "Gulp's Overlook",
                    lambda state: state.has("Moneybags Unlock - Climb", self.player) and state.has("Orb", self.player, 8) and (state.has("Double Jump Ability", self.player) or state.has("Summer Forest Talisman", self.player, 6) and state.has("Autumn Plains Talisman", self.player, 8))
                )
        else:
            if self.options.enable_progressive_sparx_logic.value:
                set_indirect_rule(
                    self,
                    "Gulp's Overlook",
                    lambda state: state.has("Moneybags Unlock - Climb", self.player) and state.has("Orb", self.player, 8) and state.has("Summer Forest Talisman", self.player, 6) and state.has("Autumn Plains Talisman", self.player, 8) and has_sparx_health(self, 2, state)
                )
            else:
                set_indirect_rule(
                    self,
                    "Gulp's Overlook",
                    lambda state: state.has("Moneybags Unlock - Climb", self.player) and state.has("Orb", self.player, 8) and state.has("Summer Forest Talisman", self.player, 6) and state.has("Autumn Plains Talisman", self.player, 8)
                )

        # Winter Tundra Rules
        set_indirect_rule(self, "Winter Tundra", lambda state: is_boss_defeated(self, "Gulp", state))
        set_rule(
            self.multiworld.get_location("Winter Tundra: On the tall wall", self.player),
            lambda state: state.has("Moneybags Unlock - Headbash", self.player)
        )
        set_rule(
            self.multiworld.get_location("Winter Tundra: Top of the waterfall", self.player),
            lambda state: state.has("Moneybags Unlock - Headbash", self.player)
        )
        set_rule(
            self.multiworld.get_location("Winter Tundra: Smash the rock", self.player),
            lambda state: state.has("Moneybags Unlock - Headbash", self.player)
        )
        if Spyro2LocationCategory.GEM_50 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Winter Tundra: 50% Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Winter Tundra", state) >= 200
            )
        if Spyro2LocationCategory.GEM_75 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Winter Tundra: 75% Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Winter Tundra", state) >= 300
            )
        if Spyro2LocationCategory.GEM_100 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Winter Tundra: All Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Winter Tundra", state) >= 400
            )

        # Mystic Marsh rules

        # Cloud Temples rules
        set_indirect_rule(
            self,
            "Cloud Temples",
            lambda state: state.has("Orb", self.player, 15)
        )
        if Spyro2LocationCategory.GEM_100 in self.enabled_location_categories:
            set_rule(
                self.multiworld.get_location("Cloud Temples: All Gems", self.player),
                lambda state: get_gems_accessible_in_level(self, "Cloud Temples", state) >= 400
            )

        # Canyon Speedway rules
        set_indirect_rule(
            self,
            "Canyon Speedway",
            lambda state: state.has("Moneybags Unlock - Canyon Speedway Portal", self.player)
        )

        # Robotica Farms rules
        set_indirect_rule(
            self,
            "Robotica Farms",
            lambda state: state.has("Moneybags Unlock - Headbash", self.player)
        )

        # Metropolis rules
        set_indirect_rule(
            self,
            "Metropolis",
            lambda state: state.has("Moneybags Unlock - Headbash", self.player) and state.has("Orb", self.player, 25)
        )

        # Ripto's Arena rules
        if self.options.logic_ripto_early.value == LogicTrickOptions.ALWAYS_ON  or self.options.logic_ripto_early.value == LogicTrickOptions.ON_WITH_DOUBLE_JUMP and self.options.double_jump_ability.value == AbilityOptions.VANILLA:
            if self.options.enable_progressive_sparx_logic.value:
                set_indirect_rule(
                    self,
                    "Ripto's Arena",
                    lambda state: state.has("Moneybags Unlock - Headbash", self.player) and has_sparx_health(self, 3, state)
                )
            else:
                set_indirect_rule(
                    self,
                    "Ripto's Arena",
                    lambda state: state.has("Moneybags Unlock - Headbash", self.player)
                )
        elif self.options.logic_ripto_early.value == LogicTrickOptions.ON_WITH_DOUBLE_JUMP:
            if self.options.enable_progressive_sparx_logic.value:
                set_indirect_rule(
                    self,
                    "Ripto's Arena",
                    lambda state: state.has("Moneybags Unlock - Headbash", self.player) and (state.has("Double Jump Ability", self.player) or state.has("Orb", self.player, 40)) and has_sparx_health(self, 3, state)
                )
            else:
                set_indirect_rule(
                    self,
                    "Ripto's Arena",
                    lambda state: state.has("Moneybags Unlock - Headbash", self.player) and (state.has("Double Jump Ability", self.player) or state.has("Orb", self.player, 40))
                )
        else:
            if self.options.enable_progressive_sparx_logic.value:
                set_indirect_rule(
                    self,
                    "Ripto's Arena",
                    lambda state: state.has("Moneybags Unlock - Headbash", self.player) and state.has("Orb", self.player, 40) and has_sparx_health(self, 3, state)
                )
            else:
                set_indirect_rule(
                    self,
                    "Ripto's Arena",
                    lambda state: state.has("Moneybags Unlock - Headbash", self.player) and state.has("Orb", self.player, 40)
                )

        # Dragon Shores rules
        set_indirect_rule(self, "Dragon Shores", lambda state: is_boss_defeated(self, "Ripto", state))
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
        

        slot_data = {
            "options": {
                "goal": self.options.goal.value,
                "guaranteed_items": self.options.guaranteed_items.value,
                "enable_25_pct_gem_checks": self.options.enable_25_pct_gem_checks.value,
                "enable_50_pct_gem_checks": self.options.enable_50_pct_gem_checks.value,
                "enable_75_pct_gem_checks": self.options.enable_75_pct_gem_checks.value,
                "enable_gem_checks": self.options.enable_gem_checks.value,
                "enable_total_gem_checks": self.options.enable_total_gem_checks.value,
                "max_total_gem_checks": self.options.max_total_gem_checks.value,
                "enable_skillpoint_checks": self.options.enable_skillpoint_checks.value,
                "moneybags_settings": self.options.moneybags_settings.value,
                "enable_filler_extra_lives": self.options.enable_filler_extra_lives.value,
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
                "logic_crush_early": self.options.logic_crush_early.value,
                "logic_gulp_early": self.options.logic_gulp_early.value,
                "logic_ripto_early": self.options.logic_ripto_early.value,
            },
            # "moneybags_prices": moneybags_prices,
            "seed": self.multiworld.seed_name,  # to verify the server's multiworld
            "slot": self.multiworld.player_name[self.player],  # to connect to server
            "base_id": self.base_id,  # to merge location and items lists
            "locationsId": locations_id,
            "locationsAddress": locations_address,
            "locationsTarget": locations_target,
            "itemsId": items_id,
            "itemsAddress": items_address
        }

        return slot_data
