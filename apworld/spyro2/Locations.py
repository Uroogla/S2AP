from enum import IntEnum
from typing import Optional, NamedTuple, Dict

from BaseClasses import Location, Region
from .Items import Spyro2Item

class Spyro2LocationCategory(IntEnum):
    TALISMAN = 0,
    ORB = 1,
    EVENT = 2,
    GEM_25 = 3,
    GEM_50 = 4,
    GEM_75 = 5,
    GEM_100 = 6,
    SKILLPOINT = 7,
    SKILLPOINT_GOAL = 8,
    TOTAL_GEM = 9,
    SHORES_TOKEN = 10,
    MONEYBAGS = 11


class Spyro2LocationData(NamedTuple):
    name: str
    default_item: str
    category: Spyro2LocationCategory


class Spyro2Location(Location):
    game: str = "Spyro 2"
    category: Spyro2LocationCategory
    default_item_name: str

    def __init__(
        self,
        player: int,
        name: str,
        category: Spyro2LocationCategory,
        default_item_name: str,
        address: Optional[int] = None,
        parent: Optional[Region] = None
    ):
        super().__init__(player, name, address, parent)
        self.default_item_name = default_item_name
        self.category = category
        self.name = name

    @staticmethod
    def get_name_to_id() -> dict:
        base_id = 1230000
        table_offset = 1000

        # Order follows the in-memory order of talismans and orbs.
        table_order = [
            "Summer Forest","Glimmer","Idol Springs","Colossus","Hurricos","Aquaria Towers","Sunny Beach","Ocean Speedway","Crush's Dungeon",
            "Autumn Plains","Skelos Badlands","Crystal Glacier","Breeze Harbor","Zephyr","Metro Speedway","Scorch","Shady Oasis","Magma Cone","Fracture Hills","Icy Speedway","Gulp's Overlook",
            "Winter Tundra","Mystic Marsh","Cloud Temples","Canyon Speedway","Robotica Farms","Metropolis","Dragon Shores","Ripto's Arena",
            "Inventory"
        ]

        output = {}
        for i, region_name in enumerate(table_order):
            if len(location_tables[region_name]) > table_offset:
                raise Exception("A location table has {} entries, that is more than {} entries (table #{})".format(len(location_tables[region_name]), table_offset, i))

            output.update({location_data.name: id for id, location_data in enumerate(location_tables[region_name], base_id + (table_offset * i))})

        return output

    def place_locked_item(self, item: Spyro2Item):
        self.item = item
        self.locked = True
        item.location = self


# To ensure backwards compatibility, do not reorder locations or insert new ones in the middle of a list.
location_tables = {
    # Homeworld 1
    "Summer Forest": [
        Spyro2LocationData("Summer Forest: Hunter's Challenge", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Summer Forest: On a secret ledge", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Summer Forest: Atop a ladder", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Summer Forest: Behind the door", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Summer Forest: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Summer Forest: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Summer Forest: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Summer Forest: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        Spyro2LocationData("Summer Forest: Moneybags Unlock: Swim", "Moneybags Unlock - Swim", Spyro2LocationCategory.MONEYBAGS),
        Spyro2LocationData("Summer Forest: Moneybags Unlock: Door to Aquaria Towers", "Moneybags Unlock - Door to Aquaria Towers", Spyro2LocationCategory.MONEYBAGS),
    ],
    "Glimmer": [
        Spyro2LocationData("Glimmer: Talisman", "Summer Forest Talisman", Spyro2LocationCategory.TALISMAN),
        Spyro2LocationData("Glimmer: Lizard hunt", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Glimmer: Gem Lamp Flight outdoors", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Glimmer: Gem Lamp Flight in cave", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Glimmer: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Glimmer: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Glimmer: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Glimmer: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        # The following leads to too restrictive a start.
        #Spyro2LocationData("Glimmer: Moneybags Unlock: Glimmer Bridge", "Moneybags Unlock - Glimmer Bridge", Spyro2LocationCategory.MONEYBAGS),
    ],
    "Idol Springs": [
        Spyro2LocationData("Idol Springs: Talisman", "Summer Forest Talisman", Spyro2LocationCategory.TALISMAN),
        Spyro2LocationData("Idol Springs: Foreman Bud's puzzles", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Idol Springs: Hula Girl rescue", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Idol Springs: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Idol Springs: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Idol Springs: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Idol Springs: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        Spyro2LocationData("Idol Springs: Land on Idol (Skill Point)", "Filler", Spyro2LocationCategory.SKILLPOINT),
        Spyro2LocationData("Idol Springs: Land on Idol (Goal)", "Skill Point", Spyro2LocationCategory.SKILLPOINT_GOAL),
    ],
    "Colossus": [
        Spyro2LocationData("Colossus: Talisman", "Summer Forest Talisman", Spyro2LocationCategory.TALISMAN),
        Spyro2LocationData("Colossus: Hockey vs. Goalie", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Colossus: Hockey one on one", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Colossus: Evil spirit search", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Colossus: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Colossus: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Colossus: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Colossus: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        Spyro2LocationData("Colossus: Perfect in Hockey (Skill Point)", "Filler", Spyro2LocationCategory.SKILLPOINT),
        Spyro2LocationData("Colossus: Perfect in Hockey (Goal)", "Skill Point", Spyro2LocationCategory.SKILLPOINT_GOAL),
    ],
    "Hurricos": [
        Spyro2LocationData("Hurricos: Talisman", "Summer Forest Talisman", Spyro2LocationCategory.TALISMAN),
        # This is the in-memory order.
        Spyro2LocationData("Hurricos: Factory Glide 2", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Hurricos: Stone thief chase", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Hurricos: Factory Glide 1", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Hurricos: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Hurricos: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Hurricos: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Hurricos: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        Spyro2LocationData("Hurricos: All Windmills (Skill Point)", "Filler", Spyro2LocationCategory.SKILLPOINT),
        Spyro2LocationData("Hurricos: All Windmills (Goal)", "Skill Point", Spyro2LocationCategory.SKILLPOINT_GOAL),
    ],
    "Aquaria Towers": [
        Spyro2LocationData("Aquaria Towers: Talisman", "Summer Forest Talisman", Spyro2LocationCategory.TALISMAN),
        Spyro2LocationData("Aquaria Towers: Seahorse Rescue", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Aquaria Towers: Manta ride I", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Aquaria Towers: Manta ride II", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Aquaria Towers: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Aquaria Towers: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Aquaria Towers: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Aquaria Towers: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        Spyro2LocationData("Aquaria Towers: Moneybags Unlock: Aquaria Towers Submarine", "Moneybags Unlock - Aquaria Towers Submarine", Spyro2LocationCategory.MONEYBAGS),
        Spyro2LocationData("Aquaria Towers: All Seaweed (Skill Point)", "Filler", Spyro2LocationCategory.SKILLPOINT),
        Spyro2LocationData("Aquaria Towers: All Seaweed (Goal)", "Skill Point", Spyro2LocationCategory.SKILLPOINT_GOAL),
    ],
    "Sunny Beach": [
        Spyro2LocationData("Sunny Beach: Talisman", "Summer Forest Talisman", Spyro2LocationCategory.TALISMAN),
        Spyro2LocationData("Sunny Beach: Blasting boxes", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Sunny Beach: Turtle soup I", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Sunny Beach: Turtle soup II", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Sunny Beach: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Sunny Beach: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Sunny Beach: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Sunny Beach: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
    ],
    "Ocean Speedway": [
        Spyro2LocationData("Ocean Speedway: Follow Hunter", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Ocean Speedway: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Ocean Speedway: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Ocean Speedway: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Ocean Speedway: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        Spyro2LocationData("Ocean Speedway: Under 1:10 (Skill Point)", "Filler", Spyro2LocationCategory.SKILLPOINT),
        Spyro2LocationData("Ocean Speedway: Under 1:10 (Goal)", "Skill Point", Spyro2LocationCategory.SKILLPOINT_GOAL),
    ],
    "Crush's Dungeon": [
        Spyro2LocationData("Crush's Dungeon: Crush Defeated", "Crush Defeated", Spyro2LocationCategory.EVENT),
        Spyro2LocationData("Crush's Dungeon: Perfect (Skill Point)", "Filler", Spyro2LocationCategory.SKILLPOINT),
        Spyro2LocationData("Crush's Dungeon: Perfect (Goal)", "Skill Point", Spyro2LocationCategory.SKILLPOINT_GOAL),
    ],
    # Homeworld 2
    "Autumn Plains": [
        Spyro2LocationData("Autumn Plains: The end of the wall", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Autumn Plains: Long glide!", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Autumn Plains: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Autumn Plains: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Autumn Plains: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Autumn Plains: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        Spyro2LocationData("Autumn Plains: Moneybags Unlock: Zephyr Portal", "Moneybags Unlock - Zephyr Portal", Spyro2LocationCategory.MONEYBAGS),
        Spyro2LocationData("Autumn Plains: Moneybags Unlock: Climb", "Moneybags Unlock - Climb", Spyro2LocationCategory.MONEYBAGS),
        Spyro2LocationData("Autumn Plains: Moneybags Unlock: Shady Oasis Portal", "Moneybags Unlock - Shady Oasis Portal", Spyro2LocationCategory.MONEYBAGS),
        Spyro2LocationData("Autumn Plains: Moneybags Unlock: Icy Speedway Portal", "Moneybags Unlock - Icy Speedway Portal", Spyro2LocationCategory.MONEYBAGS),
    ],
    "Skelos Badlands": [
        Spyro2LocationData("Skelos Badlands: Talisman", "Autumn Plains Talisman", Spyro2LocationCategory.TALISMAN),
        Spyro2LocationData("Skelos Badlands: Lava lizards I", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Skelos Badlands: Lava lizards II", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Skelos Badlands: Dem bones", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Skelos Badlands: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Skelos Badlands: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Skelos Badlands: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Skelos Badlands: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        Spyro2LocationData("Skelos Badlands: All Cacti (Skill Point)", "Filler", Spyro2LocationCategory.SKILLPOINT),
        Spyro2LocationData("Skelos Badlands: All Cacti (Goal)", "Skill Point", Spyro2LocationCategory.SKILLPOINT_GOAL),
        Spyro2LocationData("Skelos Badlands: Catbat Quartet (Skill Point)", "Filler", Spyro2LocationCategory.SKILLPOINT),
        Spyro2LocationData("Skelos Badlands: Catbat Quartet (Goal)", "Skill Point", Spyro2LocationCategory.SKILLPOINT_GOAL),
    ],
    "Crystal Glacier": [
        Spyro2LocationData("Crystal Glacier: Talisman", "Autumn Plains Talisman", Spyro2LocationCategory.TALISMAN),
        Spyro2LocationData("Crystal Glacier: Draclet cave", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Crystal Glacier: George the snow leopard", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Crystal Glacier: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Crystal Glacier: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Crystal Glacier: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Crystal Glacier: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        Spyro2LocationData("Crystal Glacier: Moneybags Unlock: Crystal Glacier Bridge", "Moneybags Unlock - Crystal Glacier Bridge", Spyro2LocationCategory.MONEYBAGS),
    ],
    "Breeze Harbor": [
        Spyro2LocationData("Breeze Harbor: Talisman", "Autumn Plains Talisman", Spyro2LocationCategory.TALISMAN),
        Spyro2LocationData("Breeze Harbor: Gear grab", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Breeze Harbor: Mine blast", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Breeze Harbor: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Breeze Harbor: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Breeze Harbor: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Breeze Harbor: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
    ],
    "Zephyr": [
        Spyro2LocationData("Zephyr: Talisman", "Autumn Plains Talisman", Spyro2LocationCategory.TALISMAN),
        Spyro2LocationData("Zephyr: Cowlek corral I", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Zephyr: Cowlek corral II", "Orb", Spyro2LocationCategory.ORB),
        # This is the in-memory order.
        Spyro2LocationData("Zephyr: Sowing seeds II", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Zephyr: Sowing seeds I", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Zephyr: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Zephyr: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Zephyr: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Zephyr: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
    ],
    "Metro Speedway": [
        Spyro2LocationData("Metro Speedway: Grab the Loot", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Metro Speedway: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Metro Speedway: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Metro Speedway: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Metro Speedway: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        Spyro2LocationData("Metro Speedway: Under 1:15 (Skill Point)", "Filler", Spyro2LocationCategory.SKILLPOINT),
        Spyro2LocationData("Metro Speedway: Under 1:15 (Goal)", "Skill Point", Spyro2LocationCategory.SKILLPOINT_GOAL),
    ],
    "Scorch": [
        Spyro2LocationData("Scorch: Talisman", "Autumn Plains Talisman", Spyro2LocationCategory.TALISMAN),
        Spyro2LocationData("Scorch: Barrel of Monkeys", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Scorch: Capture the flags", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Scorch: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Scorch: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Scorch: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Scorch: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        Spyro2LocationData("Scorch: All Trees (Skill Point)", "Filler", Spyro2LocationCategory.SKILLPOINT),
        Spyro2LocationData("Scorch: All Trees (Goal)", "Skill Point", Spyro2LocationCategory.SKILLPOINT_GOAL),
    ],
    "Shady Oasis": [
        Spyro2LocationData("Shady Oasis: Talisman", "Autumn Plains Talisman", Spyro2LocationCategory.TALISMAN),
        Spyro2LocationData("Shady Oasis: Catch 3 thieves", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Shady Oasis: Free Hippos", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Shady Oasis: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Shady Oasis: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Shady Oasis: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Shady Oasis: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
    ],
    "Magma Cone": [
        Spyro2LocationData("Magma Cone: Talisman", "Autumn Plains Talisman", Spyro2LocationCategory.TALISMAN),
        Spyro2LocationData("Magma Cone: Crystal geysers I", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Magma Cone: Crystal geysers II", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Magma Cone: Party crashers", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Magma Cone: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Magma Cone: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Magma Cone: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Magma Cone: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        Spyro2LocationData("Magma Cone: Moneybags Unlock: Magma Cone Elevator", "Moneybags Unlock - Magma Cone Elevator", Spyro2LocationCategory.MONEYBAGS),
    ],
    "Fracture Hills": [
        Spyro2LocationData("Fracture Hills: Talisman", "Autumn Plains Talisman", Spyro2LocationCategory.TALISMAN),
        # This is the in-memory order.
        Spyro2LocationData("Fracture Hills: Earthshaper bash", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Fracture Hills: Free the faun", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Fracture Hills: Alchemist escort", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Fracture Hills: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Fracture Hills: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Fracture Hills: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Fracture Hills: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        Spyro2LocationData("Fracture Hills: 3 Laps of Supercharge (Skill Point)", "Filler", Spyro2LocationCategory.SKILLPOINT),
        Spyro2LocationData("Fracture Hills: 3 Laps of Supercharge (Goal)", "Skill Point", Spyro2LocationCategory.SKILLPOINT_GOAL),
    ],
    "Icy Speedway": [
        Spyro2LocationData("Icy Speedway: Parasail through Rings", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Icy Speedway: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Icy Speedway: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Icy Speedway: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Icy Speedway: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        Spyro2LocationData("Icy Speedway: Under 1:15 (Skill Point)", "Filler", Spyro2LocationCategory.SKILLPOINT),
        Spyro2LocationData("Icy Speedway: Under 1:15 (Goal)", "Skill Point", Spyro2LocationCategory.SKILLPOINT_GOAL),
    ],
    "Gulp's Overlook": [
        Spyro2LocationData("Gulp's Overlook: Gulp Defeated", "Gulp Defeated", Spyro2LocationCategory.EVENT),
        Spyro2LocationData("Gulp's Overlook: Perfect (Skill Point)", "Filler", Spyro2LocationCategory.SKILLPOINT),
        Spyro2LocationData("Gulp's Overlook: Perfect (Goal)", "Skill Point", Spyro2LocationCategory.SKILLPOINT_GOAL),
        Spyro2LocationData("Gulp's Overlook: Hit Ripto (Skill Point)", "Filler", Spyro2LocationCategory.SKILLPOINT),
        Spyro2LocationData("Gulp's Overlook: Hit Ripto (Goal)", "Skill Point", Spyro2LocationCategory.SKILLPOINT_GOAL),
    ],
    # Homeworld 3
    "Winter Tundra": [
        Spyro2LocationData("Winter Tundra: On the tall wall", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Winter Tundra: Top of the waterfall", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Winter Tundra: Smash the rock", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Winter Tundra: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Winter Tundra: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Winter Tundra: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Winter Tundra: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        Spyro2LocationData("Winter Tundra: Moneybags Unlock: Canyon Speedway Portal", "Moneybags Unlock - Canyon Speedway Portal", Spyro2LocationCategory.MONEYBAGS),
        Spyro2LocationData("Winter Tundra: Moneybags Unlock: Headbash", "Moneybags Unlock - Headbash", Spyro2LocationCategory.MONEYBAGS),
    ],
    "Mystic Marsh": [
        Spyro2LocationData("Mystic Marsh: Fix the fountain", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Mystic Marsh: Very versatile thieves!", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Mystic Marsh: Retrieve professor's pencil", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Mystic Marsh: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Mystic Marsh: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Mystic Marsh: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Mystic Marsh: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
    ],
    "Cloud Temples": [
        Spyro2LocationData("Cloud Temples: Agent Zero's secret hideout", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Cloud Temples: Ring tower bells", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Cloud Temples: Break down doors", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Cloud Temples: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Cloud Temples: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Cloud Temples: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Cloud Temples: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
    ],
    "Canyon Speedway": [
        Spyro2LocationData("Canyon Speedway: Shoot down balloons", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Canyon Speedway: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Canyon Speedway: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Canyon Speedway: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Canyon Speedway: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        Spyro2LocationData("Canyon Speedway: Under 1:10 (Skill Point)", "Filler", Spyro2LocationCategory.SKILLPOINT),
        Spyro2LocationData("Canyon Speedway: Under 1:10 (Goal)", "Skill Point", Spyro2LocationCategory.SKILLPOINT_GOAL),
    ],
    "Robotica Farms": [
        Spyro2LocationData("Robotica Farms: Switch on bug light", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Robotica Farms: Clear tractor path", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Robotica Farms: Exterminate crow bugs", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Robotica Farms: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Robotica Farms: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Robotica Farms: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Robotica Farms: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
        # There is a memory address for a skill point here, but it is not implemented.
    ],
    "Metropolis": [
        Spyro2LocationData("Metropolis: Conquer invading cows", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Metropolis: Shoot down sheep saucers I", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Metropolis: Shoot down sheep saucers II", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Metropolis: Ox bombing", "Orb", Spyro2LocationCategory.ORB),
        Spyro2LocationData("Metropolis: 25% Gems", "Filler", Spyro2LocationCategory.GEM_25),
        Spyro2LocationData("Metropolis: 50% Gems", "Filler", Spyro2LocationCategory.GEM_50),
        Spyro2LocationData("Metropolis: 75% Gems", "Filler", Spyro2LocationCategory.GEM_75),
        Spyro2LocationData("Metropolis: All Gems", "Filler", Spyro2LocationCategory.GEM_100),
    ],
    "Dragon Shores": [
        Spyro2LocationData("Dragon Shores: Tunnel o' Love", "Dragon Shores Token", Spyro2LocationCategory.SHORES_TOKEN),
        Spyro2LocationData("Dragon Shores: Shooting Gallery I", "Dragon Shores Token", Spyro2LocationCategory.SHORES_TOKEN),
        Spyro2LocationData("Dragon Shores: Shooting Gallery II", "Dragon Shores Token", Spyro2LocationCategory.SHORES_TOKEN),
        Spyro2LocationData("Dragon Shores: Shooting Gallery III", "Dragon Shores Token", Spyro2LocationCategory.SHORES_TOKEN),
        Spyro2LocationData("Dragon Shores: Rollercoaster I", "Dragon Shores Token", Spyro2LocationCategory.SHORES_TOKEN),
        Spyro2LocationData("Dragon Shores: Rollercoaster II", "Dragon Shores Token", Spyro2LocationCategory.SHORES_TOKEN),
        Spyro2LocationData("Dragon Shores: Rollercoaster III", "Dragon Shores Token", Spyro2LocationCategory.SHORES_TOKEN),
        Spyro2LocationData("Dragon Shores: Dunk Tank I", "Dragon Shores Token", Spyro2LocationCategory.SHORES_TOKEN),
        Spyro2LocationData("Dragon Shores: Dunk Tank II", "Dragon Shores Token", Spyro2LocationCategory.SHORES_TOKEN),
        Spyro2LocationData("Dragon Shores: Dunk Tank III", "Dragon Shores Token", Spyro2LocationCategory.SHORES_TOKEN),
    ],
    "Ripto's Arena": [
        Spyro2LocationData("Ripto's Arena: Ripto Defeated", "Ripto Defeated", Spyro2LocationCategory.EVENT),
        Spyro2LocationData("Ripto's Arena: Perfect (Skill Point)", "Filler", Spyro2LocationCategory.SKILLPOINT),
        Spyro2LocationData("Ripto's Arena: Perfect (Goal)", "Skill Point", Spyro2LocationCategory.SKILLPOINT_GOAL),
    ],
    "Inventory": [
        Spyro2LocationData("Total Gems: 500", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 1000", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 1500", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 2000", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 2500", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 3000", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 3500", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 4000", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 4500", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 5000", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 5500", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 6000", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 6500", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 7000", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 7500", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 8000", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 8500", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 9000", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 9500", "Filler", Spyro2LocationCategory.TOTAL_GEM),
        Spyro2LocationData("Total Gems: 10000", "Filler", Spyro2LocationCategory.TOTAL_GEM),
    ]
}

location_dictionary: Dict[str, Spyro2LocationData] = {}
for location_table in location_tables.values():
    location_dictionary.update({location_data.name: location_data for location_data in location_table})
