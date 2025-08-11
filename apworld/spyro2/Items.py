from enum import IntEnum
from typing import NamedTuple
from BaseClasses import Item
from .Options import MoneybagsOptions, SparxUpgradeOptions, AbilityOptions
from Options import OptionError


class Spyro2ItemCategory(IntEnum):
    TALISMAN = 0,
    ORB = 1,
    EVENT = 2,
    MISC = 3,
    TRAP = 4,
    SKILLPOINT_GOAL = 5,
    MONEYBAGS = 6,
    TOKEN = 7,
    ABILITY = 8


class Spyro2ItemData(NamedTuple):
    name: str
    s2_code: int
    category: Spyro2ItemCategory


class Spyro2Item(Item):
    game: str = "Spyro 2"

    @staticmethod
    def get_name_to_id() -> dict:
        base_id = 1230000
        return {item_data.name: (base_id + item_data.s2_code if item_data.s2_code is not None else None) for item_data in _all_items}


key_item_names = {
    "Summer Forest Talisman",
    "Autumn Plains Talisman",
    "Orb"
}


_all_items = [Spyro2ItemData(row[0], row[1], row[2]) for row in [
    ("Crush Defeated", 2000, Spyro2ItemCategory.EVENT),
    ("Gulp Defeated", 2001, Spyro2ItemCategory.EVENT),
    ("Ripto Defeated", 2002, Spyro2ItemCategory.EVENT),
    
    ("Summer Forest Talisman", 1000, Spyro2ItemCategory.TALISMAN),
    ("Autumn Plains Talisman", 1001, Spyro2ItemCategory.TALISMAN),
    ("Orb", 1002, Spyro2ItemCategory.ORB),
    ("Extra Life", 1003, Spyro2ItemCategory.MISC),
    ("Filler", 1004, Spyro2ItemCategory.MISC),
    ("Damage Sparx Trap", 1005, Spyro2ItemCategory.TRAP),
    ("Sparxless Trap", 1006, Spyro2ItemCategory.TRAP),
    ("Invisibility Trap", 1007, Spyro2ItemCategory.TRAP),
    ("Turn Spyro Red", 1008, Spyro2ItemCategory.MISC),
    ("Turn Spyro Blue", 1009, Spyro2ItemCategory.MISC),
    ("Turn Spyro Pink", 1010, Spyro2ItemCategory.MISC),
    ("Turn Spyro Yellow", 1011, Spyro2ItemCategory.MISC),
    ("Turn Spyro Green", 1012, Spyro2ItemCategory.MISC),
    ("Turn Spyro Black", 1013, Spyro2ItemCategory.MISC),
    ("Big Head Mode", 1014, Spyro2ItemCategory.MISC),
    ("Flat Spyro Mode", 1015, Spyro2ItemCategory.MISC),
    ("Heal Sparx", 1016, Spyro2ItemCategory.MISC),
    ("Progressive Sparx Health Upgrade", 1017, Spyro2ItemCategory.MISC),
    ("Skill Point", 1018, Spyro2ItemCategory.SKILLPOINT_GOAL),
    ("Dragon Shores Token", 1019, Spyro2ItemCategory.TOKEN),
    ("Double Jump Ability", 1020, Spyro2ItemCategory.ABILITY),
    ("Permanent Fireball Ability", 1021, Spyro2ItemCategory.ABILITY),
    ("Destructive Spyro", 1022, Spyro2ItemCategory.MISC),

    ("Moneybags Unlock - Crystal Glacier Bridge", 3000, Spyro2ItemCategory.MONEYBAGS),
    ("Moneybags Unlock - Aquaria Towers Submarine", 3001, Spyro2ItemCategory.MONEYBAGS),
    ("Moneybags Unlock - Magma Cone Elevator", 3002, Spyro2ItemCategory.MONEYBAGS),
    # The following leads to too restrictive a start or is unnecessary with double jump.
    #("Moneybags Unlock - Glimmer Bridge", 3003, Spyro2ItemCategory.MONEYBAGS),
    ("Moneybags Unlock - Swim", 3004, Spyro2ItemCategory.MONEYBAGS),
    ("Moneybags Unlock - Climb", 3005, Spyro2ItemCategory.MONEYBAGS),
    ("Moneybags Unlock - Headbash", 3006, Spyro2ItemCategory.MONEYBAGS),
    ("Moneybags Unlock - Door to Aquaria Towers", 3007, Spyro2ItemCategory.MONEYBAGS),
    ("Moneybags Unlock - Zephyr Portal", 3008, Spyro2ItemCategory.MONEYBAGS),
    ("Moneybags Unlock - Shady Oasis Portal", 3009, Spyro2ItemCategory.MONEYBAGS),
    ("Moneybags Unlock - Icy Speedway Portal", 3010, Spyro2ItemCategory.MONEYBAGS),
    ("Moneybags Unlock - Canyon Speedway Portal", 3011, Spyro2ItemCategory.MONEYBAGS),
]]

item_descriptions = {}

item_dictionary = {item_data.name: item_data for item_data in _all_items}


def BuildItemPool(multiworld, count, options):
    item_pool = []
    included_itemcount = 0

    if options.guaranteed_items.value:
        for item_name in options.guaranteed_items.value:
            item = item_dictionary[item_name]
            item_pool.append(item)
            included_itemcount = included_itemcount + 1
    remaining_count = count - included_itemcount
    for i in range(6):
        item_pool.append(item_dictionary["Summer Forest Talisman"])
    for i in range(8):
        item_pool.append(item_dictionary["Autumn Plains Talisman"])
    for i in range(64):
        item_pool.append(item_dictionary["Orb"])
    remaining_count = remaining_count - 78

    if options.moneybags_settings.value == MoneybagsOptions.MONEYBAGSSANITY:
        item_pool.append(item_dictionary["Moneybags Unlock - Crystal Glacier Bridge"])
        item_pool.append(item_dictionary["Moneybags Unlock - Aquaria Towers Submarine"])
        item_pool.append(item_dictionary["Moneybags Unlock - Magma Cone Elevator"])
        # item_pool.append(item_dictionary["Moneybags Unlock - Glimmer Bridge"])
        item_pool.append(item_dictionary["Moneybags Unlock - Swim"])
        item_pool.append(item_dictionary["Moneybags Unlock - Climb"])
        item_pool.append(item_dictionary["Moneybags Unlock - Headbash"])
        item_pool.append(item_dictionary["Moneybags Unlock - Door to Aquaria Towers"])
        item_pool.append(item_dictionary["Moneybags Unlock - Zephyr Portal"])
        item_pool.append(item_dictionary["Moneybags Unlock - Shady Oasis Portal"])
        item_pool.append(item_dictionary["Moneybags Unlock - Icy Speedway Portal"])
        item_pool.append(item_dictionary["Moneybags Unlock - Canyon Speedway Portal"])
        remaining_count = remaining_count - 11

    if options.double_jump_ability.value == AbilityOptions.IN_POOL:
        item_pool.append(item_dictionary["Double Jump Ability"])
        remaining_count = remaining_count - 1
    if options.permanent_fireball_ability.value == AbilityOptions.IN_POOL:
        item_pool.append(item_dictionary["Permanent Fireball Ability"])
        remaining_count = remaining_count - 1
    
    if options.enable_progressive_sparx_health in [SparxUpgradeOptions.BLUE, SparxUpgradeOptions.GREEN, SparxUpgradeOptions.SPARXLESS]:
        item_pool.append(item_dictionary["Progressive Sparx Health Upgrade"])
        remaining_count = remaining_count - 1
    if options.enable_progressive_sparx_health in [SparxUpgradeOptions.GREEN, SparxUpgradeOptions.SPARXLESS]:
        item_pool.append(item_dictionary["Progressive Sparx Health Upgrade"])
        remaining_count = remaining_count - 1
    if options.enable_progressive_sparx_health in [SparxUpgradeOptions.SPARXLESS]:
        item_pool.append(item_dictionary["Progressive Sparx Health Upgrade"])
        remaining_count = remaining_count - 1

    if remaining_count < 0:
        raise OptionError(f"The options you have selected require at least {remaining_count * -1} more checks to be enabled.")

    # Build a weighted list of allowed filler items.
    # Make changing Spyro's color in general the same weight as other items.
    allowed_misc_items = []
    allowed_trap_items = []

    for item in _all_items:
        if item.name == 'Extra Life' and options.enable_filler_extra_lives:
            for i in range(0, 6):
                allowed_misc_items.append(item)
        elif item.name == 'Destructive Spyro' and options.enable_destructive_spyro_filler:
            for i in range(0, 6):
                allowed_misc_items.append(item)
        elif item.name.startswith('Turn Spyro ') and options.enable_filler_color_change:
            allowed_misc_items.append(item)
        elif (item.name == 'Big Head Mode' or item.name == 'Flat Spyro Mode') and options.enable_filler_big_head_mode:
            for i in range(0, 3):
                allowed_misc_items.append(item)
        elif item.name == 'Heal Sparx' and options.enable_filler_heal_sparx:
            for i in range(0, 6):
                allowed_misc_items.append(item)
        elif item.name == 'Damage Sparx Trap' and options.enable_trap_damage_sparx:
            allowed_trap_items.append(item)
        elif item.name == 'Sparxless Trap' and options.enable_trap_sparxless:
            allowed_trap_items.append(item)
        elif item.name == 'Invisibility Trap' and options.enable_trap_invisibility:
            allowed_trap_items.append(item)

    if remaining_count > 0 and options.trap_filler_percent.value > 0 and len(allowed_trap_items) == 0:
        raise OptionError(f"Trap percentage is set to {options.trap_filler_percent.value}, but none have been turned on.")
    if remaining_count > 0 and options.trap_filler_percent.value < 100 and len(allowed_misc_items) == 0:
        raise OptionError(f"{100 - options.trap_filler_percent.value} percent of filler items are meant to be non-traps, but no non-trap items have been turned on.")

    # Get the correct blend of traps and filler items.
    for i in range(remaining_count):
        if multiworld.random.random() * 100 < options.trap_filler_percent.value:
            itemList = [item for item in allowed_trap_items]
        else:
            itemList = [item for item in allowed_misc_items]
        item = multiworld.random.choice(itemList)
        item_pool.append(item)
    
    multiworld.random.shuffle(item_pool)
    return item_pool
