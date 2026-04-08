from .Logic import Logic

class GemRuleRestriction:
    bits = []
    restriction_text = ""
    gems_restricted = 0

    def __init__(self, bits: list, restriction_text: str, restriction_lambda, gems_restricted: int):
        self.bits = bits
        self.restriction_text = restriction_text
        self.restriction_lambda = restriction_lambda
        self.gems_restricted = gems_restricted

class GemRules:
    empty_bits = []
    restrictions: list[GemRuleRestriction] = []

    def __init__(self, empty_bits: list, restrictions: list[GemRuleRestriction]):
        self.empty_bits = empty_bits
        self.restrictions = restrictions

class LevelAccessRule:
    pass

class LevelRules:
    level_name = ""
    orbs = {}
    moneybags_locations = {}
    life_bottles = {}
    skill_points = {}
    gem_rules: GemRules

    def __init__(
        self,
        level_name: str,
        homeworld_access_rule,
        access_rule,
        talisman_rule,
        orbs: dict,
        moneybags_locations: dict,
        life_bottles: dict,
        skill_points: dict,
        spirit_particles_rule,
        gem_rules: GemRules
    ):
        self.level_name = level_name
        self.homeworld_access_rule = homeworld_access_rule
        self.access_rule = access_rule
        self.talisman_rule = talisman_rule
        self.orbs = orbs
        self.moneybags_locations = moneybags_locations
        self.life_bottles = life_bottles
        self.skill_points = skill_points
        self.spirit_particles_rule = spirit_particles_rule
        self.gem_rules = gem_rules

def get_level_rules(logic: Logic):
    return [
        LevelRules(
            "Summer Forest",
            None,
            None,
            None,
            {
                "Summer Forest: Hunter's Challenge": None,
                "Summer Forest: On a secret ledge": lambda state: logic.can_access_sf_secret_ledge(state),
                "Summer Forest: Atop a ladder": lambda state: logic.can_access_sf_ladder(state),
                "Summer Forest: Behind the door": lambda state: logic.can_access_summer_second_half(state)
            },
            {
                "Summer Forest: Moneybags Unlock: Swim": None,
                "Summer Forest: Moneybags Unlock: Wall by Aquaria Towers": lambda state: logic.can_access_summer_second_half(state)
            },
            {
                "Summer Forest: First Life Bottle Near Glimmer": None,
                "Summer Forest: Second Life Bottle Near Glimmer": None,
                "Summer Forest: Life Bottle Near Sunny Beach": lambda state: logic.can_access_summer_second_half(state)
            },
            {},
            None,
            GemRules(
                [27, 41, 42, 43, 44, 45, 46, 47, 61, 62, 63, 72, 73, 81, 82, 95, 96, 97, 98, 99, 100, 108, 126, 127, 128],
                [
                    GemRuleRestriction(
                        [146, 147, 148, 149, 152],
                        "access to the ledge overlooking Colossus",
                        lambda state: logic.can_access_sf_secret_ledge(state),
                        9
                    ),
                    GemRuleRestriction(
                        [49, 50, 51, 116, 117, 118, 119, 120, 121, 138, 144, 150, 151, 153, 154, 155, 156, 157, 158],
                        "swim",
                        lambda state: logic.can_swim(state),
                        42
                    ),
                    GemRuleRestriction(
                        [1, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 22, 23, 24, 25, 26, 52, 53, 54, 68, 69, 74, 77, 78, 79, 80, 87, 88, 89, 90, 91, 92, 93],
                        "access to the second half of Summer Forest",
                        lambda state: logic.can_access_summer_second_half(state),
                        170
                    ),
                    GemRuleRestriction(
                        [83, 84, 85, 86, 94, 102, 103, 104, 105, 106],
                        "access to the Summer Forest ladder",
                        lambda state: logic.can_access_sf_ladder(state),
                        10
                    ),
                    GemRuleRestriction(
                        [2, 3, 4, 5, 13, 21, 101, 107],
                        "access beyond the wall to Aquaria Towers",
                        lambda state: logic.can_access_sf_past_aquaria_wall(state),
                        14
                    ),
                ]
            )
        ),
        LevelRules(
            "Glimmer",
            None,
            None,
            None,
            {
                "Glimmer: Lizard hunt": None,
                "Glimmer: Gem Lamp Flight outdoors": lambda state: logic.can_do_glimmer_outdoor_lamps(state),
                "Glimmer: Gem Lamp Flight in cave": lambda state: logic.can_do_glimmer_indoor_lamps(state)
            },
            # Moneybags removed as check because of restrictive starts.
            {},
            {},
            {},
            None,
            GemRules(
                [1, 2, 3, 4, 5, 6, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 152],
                [
                    GemRuleRestriction(
                        [110, 111, 112, 113, 114, 115, 117, 118, 119, 151],
                        "indoor lamp access",
                        lambda state: logic.can_do_glimmer_indoor_lamps(state),
                        47
                    )
                ]
            )
        ),
        LevelRules(
            "Idol Springs",
            None,
            lambda state: logic.can_enter_idol(state),
            None,
            {
                "Idol Springs: Foreman Bud's puzzles": lambda state: logic.can_access_idol_lake(state),
                "Idol Springs: Hula Girl rescue": None
            },
            {},
            {"Idol Springs: Life Bottle": None},
            {"Idol Springs: Land on Idol": None},
            None,
            GemRules(
                [63, 88, 90, 122, 127, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145],
                [
                    GemRuleRestriction(
                        [16, 17, 18, 19, 20, 21, 61, 64, 65, 66, 67, 76, 85, 86, 93, 94, 95, 96, 99, 100, 101, 102, 103, 104, 105, 106],
                        "access to the lake",
                        lambda state: logic.can_access_idol_lake(state),
                        102
                    )
                ]
            )
        ),
        LevelRules(
            "Colossus",
            None,
            lambda state: logic.can_enter_colossus(state),
            None,
            {
                "Colossus: Hockey vs. Goalie": None,
                "Colossus: Hockey one on one": None,
                # TODO: Add powerup logic.
                "Colossus: Evil spirit search": None,
            },
            {},
            {"Colossus: Life Bottle": None},
            {"Colossus: Perfect in Hockey": None},
            None,
            GemRules(
                [1, 2, 3, 4, 5, 6, 7, 25, 32, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 71, 117, 118, 119, 127, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178],
                []
            )
        ),
        LevelRules(
            "Hurricos",
            None,
            lambda state: logic.can_enter_hurricos(state),
            None,
            {
                # TODO: Add powerup logic.
                "Hurricos: Factory Glide 2": None,
                "Hurricos: Stone thief chase": None,
                "Hurricos: Factory Glide 1": None,
            },
            {},
            {"Hurricos: Life Bottle": None},
            {"Hurricos: All Windmills": None},
            None,
            GemRules(
                [42, 43, 44, 45, 46, 83, 85, 86, 87, 94, 116, 123, 126, 127, 128, 129, 130, 131],
                # TODO: Add powerup logic.
                []
            )
        ),
        LevelRules(
            "Aquaria Towers",
            None,
            lambda state: logic.can_enter_aquaria(state),
            lambda state: logic.can_access_aquaria_room_three(state),
            {
                "Aquaria Towers: Seahorse Rescue": lambda state: logic.can_complete_aquaria_children_orb(state),
                "Aquaria Towers: Manta ride I": lambda state: logic.can_access_aquaria_room_three(state),
                "Aquaria Towers: Manta ride II": lambda state: logic.can_access_aquaria_room_three(state),
            },
            {"Aquaria Towers: Moneybags Unlock: Aquaria Towers Submarine": lambda state: logic.can_access_aquaria_pre_moneybags_tunnel(state)},
            {"Aquaria Towers: Life Bottle": lambda state: logic.can_access_aquaria_room_two_bottom(state)},
            {"Aquaria Towers: All Seaweed": lambda state: logic.can_get_aquaria_spirit_particles(state)},
            lambda state: logic.can_get_aquaria_spirit_particles(state),
            GemRules(
                [85, 86, 87, 88, 89, 90, 91, 92, 94, 95, 96, 97, 98, 99, 100, 109, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 167],
                [
                    GemRuleRestriction(
                        [168, 169, 176, 177, 178, 179, 180, 182, 183],
                        "access to the first tunnel",
                        lambda state: logic.can_access_aquaria_first_tunnel(state),
                        19
                    ),
                    GemRuleRestriction(
                        [1, 2, 8, 14, 15, 42, 52, 53, 54, 135, 165, 181],
                        "access to the second button room's dry area",
                        lambda state: logic.can_access_aquaria_room_two_bottom(state),
                        21
                    ),
                    GemRuleRestriction(
                        [9, 10, 33, 51, 55, 56, 57, 58, 63],
                        "access to the second button room's crab pit",
                        lambda state: logic.can_access_aquaria_room_two_crab_pit(state),
                        27
                    ),
                    GemRuleRestriction(
                        [112, 113, 114, 115, 116, 117],
                        "access to the second button room's shark pit",
                        lambda state: logic.can_access_aquaria_room_two_shark_pit(state),
                        25
                    ),
                    GemRuleRestriction(
                        [41, 43, 44, 45, 46, 47, 48, 49],
                        "access to the second button room's upper area",
                        lambda state: logic.can_access_aquaria_room_two_middle(state),
                        13
                    ),
                    GemRuleRestriction(
                        [3, 4],
                        "access to the second button room's highest area",
                        lambda state: logic.can_access_aquaria_room_two_top(state),
                        10
                    ),
                    GemRuleRestriction(
                        [34, 35, 36, 37, 38, 39, 40, 50, 59, 60, 61, 62, 64, 65, 66],
                        "access to the tunnel before Moneybags",
                        lambda state: logic.can_access_aquaria_pre_moneybags_tunnel(state),
                        22
                    ),
                    GemRuleRestriction(
                        [5, 6, 7, 16, 17, 18, 19, 20, 24, 25, 26, 29, 30, 31, 127, 128],
                        "access to the third button room",
                        lambda state: logic.can_access_aquaria_room_three(state),
                        56
                    ),
                    GemRuleRestriction(
                        [21, 22, 23, 67, 110, 111],
                        "access to the talisman area",
                        lambda state: logic.can_access_aquaria_talisman_area_gems(state),
                        17
                    ),
                    GemRuleRestriction(
                        [102, 103, 104, 105, 106, 107, 108, 118, 129, 130],
                        "access to the shark tunnel",
                        lambda state: logic.can_access_aquaria_shark_tunnel(state),
                        40
                    ),
                    GemRuleRestriction(
                        [68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 93, 101, 119, 120, 121, 122, 123, 124, 125, 126, 131, 132, 133, 134],
                        "access to the upper level",
                        lambda state: logic.can_access_aquaria_room_three(state),
                        125
                    )
                ]
            )
        ),
        LevelRules(
            "Sunny Beach",
            None,
            lambda state: logic.can_enter_sunny(state),
            lambda state: logic.can_access_sunny_final_area(state),
            {
                # TODO: Add powerup logic.
                "Sunny Beach: Blasting boxes": lambda state: logic.can_access_sunny_underwater(state),
                "Sunny Beach: Turtle soup I": lambda state: logic.can_access_sunny_turtle_soup(state),
                "Sunny Beach: Turtle soup II": lambda state: logic.can_access_sunny_turtle_soup(state),
            },
            {},
            {},
            {},
            lambda state: logic.can_access_sunny_underwater(state),
            GemRules(
                [1, 2, 3, 4, 5, 6, 53, 91, 105, 106, 107, 109],
                [
                    # TODO: Better handle logic.
                    GemRuleRestriction(
                        [56, 57, 58, 83, 84, 85, 86, 87, 108],
                        "climb",
                        lambda state: logic.can_climb(state),
                        20
                    )
                ]
            )
        ),
        LevelRules(
            "Ocean Speedway",
            None,
            lambda state: logic.can_enter_ocean(state),
            None,
            {
                "Ocean Speedway: Follow Hunter": None
            },
            {},
            {},
            {
                "Ocean Speedway: Under 1:10": None
            },
            None,
            GemRules(
                [],
                []
            )
        ),
        LevelRules(
            "Crush's Dungeon",
            None,
            lambda state: logic.can_enter_crush(state),
            None,
            {},
            {},
            {},
            {
                "Crush's Dungeon: Perfect": None,
            },
            None,
            GemRules(
                [],
                []
            )
        ),
        LevelRules(
            "Autumn Plains",
            None,
            lambda state: logic.can_enter_autumn(state),
            None,
            {
                "Autumn Plains: The end of the wall": lambda state: logic.can_access_autumn_wall(state),
                "Autumn Plains: Long glide!": lambda state: logic.can_pass_autumn_door(state)
            },
            {
                "Autumn Plains: Moneybags Unlock: Zephyr Portal": None,
                "Autumn Plains: Moneybags Unlock: Climb": None,
                "Autumn Plains: Moneybags Unlock: Shady Oasis Portal": lambda state: logic.can_pass_autumn_door(state),
                "Autumn Plains: Moneybags Unlock: Icy Speedway Portal": lambda state: logic.can_pass_autumn_door(state)
            },
            {"Autumn Plains: Life Bottle": lambda state: logic.can_access_autumn_second_half(state)},
            {},
            None,
            GemRules(
                [1, 2, 3, 4, 5, 6, 102, 103, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133],
                [
                    GemRuleRestriction(
                        [31, 32],
                        "access to the Metro Speedway portal",
                        lambda state: logic.can_access_metro_platform(state),
                        2
                    ),
                    GemRuleRestriction(
                        [89, 90],
                        "access to the orb wall",
                        lambda state: logic.can_access_autumn_wall(state),
                        20
                    ),
                    GemRuleRestriction(
                        [17, 18, 19, 20, 21, 35, 36, 37, 46, 47, 93, 94],
                        "access beyond the ladder",
                        lambda state: logic.can_access_autumn_second_half(state),
                        51
                    ),
                    GemRuleRestriction(
                        [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 99, 100, 101, 122],
                        "access to beyond the Professor's door",
                        lambda state: logic.can_pass_autumn_door(state),
                        202
                    ),
                    GemRuleRestriction(
                        [75, 76, 77],
                        "access to the Shady Oasis section",
                        lambda state: logic.can_access_autumn_shady_section(state),
                        7
                    )
                ]
            )
        ),
        LevelRules(
            "Skelos Badlands",
            lambda state: logic.can_enter_autumn(state),
            lambda state: logic.can_enter_skelos(state),
            None,
            {
                "Skelos Badlands: Lava lizards I": None,
                "Skelos Badlands: Lava lizards II": None,
                # TODO: Add powerup logic.
                "Skelos Badlands: Dem bones": None,
            },
            {},
            {"Skelos Badlands: Life Bottle": None},
            {
                "Skelos Badlands: All Cacti": None,
                "Skelos Badlands: Catbat Quartet": None
            },
            None,
            GemRules(
                [1, 2, 3, 48, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 138, 139, 140, 141, 142, 143, 144, 155, 156, 157, 158, 159, 160, 161],
                []
            )
        ),
        LevelRules(
            "Crystal Glacier",
            lambda state: logic.can_enter_autumn(state),
            lambda state: logic.can_enter_crystal(state),
            lambda state: logic.can_access_crystal_bridge(state),
            {
                # TODO: Add powerup logic.
                "Crystal Glacier: Draclet cave": lambda state: logic.can_access_crystal_bridge(state),
                "Crystal Glacier: George the snow leopard": lambda state: logic.can_access_crystal_bridge(state)
            },
            {"Crystal Glacier: Moneybags Unlock: Crystal Glacier Bridge": None},
            {"Crystal Glacier: Life Bottle": lambda state: logic.can_access_crystal_bridge(state)},
            {},
            lambda state: logic.can_access_crystal_bridge(state),
            GemRules(
                [1, 2, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71],
                [
                    GemRuleRestriction(
                        [23, 24, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96],
                        "access past the paid bridge",
                        lambda state: logic.can_access_crystal_bridge(state),
                        155
                    )
                ]
            )
        ),
        LevelRules(
            "Breeze Harbor",
            lambda state: logic.can_enter_autumn(state),
            lambda state: logic.can_enter_breeze(state),
            None,
            {
                # TODO: Add powerup logic.
                "Breeze Harbor: Gear grab": None,
                "Breeze Harbor: Mine blast": None
            },
            {},
            {
                "Breeze Harbor: Life Bottle by Final Bonfire": None,
                "Breeze Harbor: Life Bottle by Final Cannon": None,
            },
            {},
            None,
            GemRules(
                [1, 2, 3, 4, 5, 6, 7, 15, 16, 17, 18, 19, 85, 90, 100, 111, 112],
                # TODO: Add powerup logic.
                [
                    GemRuleRestriction(
                        [29, 30, 31],
                        "swim",
                        lambda state: logic.can_swim(state),
                        9
                    )
                ]
            )
        ),
        LevelRules(
            "Zephyr",
            lambda state: logic.can_enter_autumn(state),
            lambda state: logic.can_enter_zephyr(state),
            None,
            {
                # TODO: Add powerup logic.
                "Zephyr: Cowlek corral I": None,
                "Zephyr: Cowlek corral II": lambda state: logic.can_access_zephyr_ladder(state),
                "Zephyr: Sowing seeds II": None,
                "Zephyr: Sowing seeds I": None
            },
            {},
            {
                "Zephyr: Life Bottle": None
            },
            {},
            lambda state: logic.can_access_zephyr_ladder(state),
            GemRules(
                [1, 2, 8, 9, 10, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 105, 107, 117, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 149, 150, 151, 153, 167, 168],
                # TODO: Add powerup logic.
                [
                    GemRuleRestriction(
                        [90, 91, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180],
                        "access past the ladder",
                        lambda state: logic.can_access_zephyr_ladder(state),
                        116
                    )
                ]
            )
        ),
        LevelRules(
            "Metro Speedway",
            lambda state: logic.can_enter_autumn(state),
            lambda state: logic.can_enter_metro(state),
            None,
            {
                "Metro Speedway: Grab the Loot": None
            },
            {},
            {},
            {
                "Metro Speedway: Under 1:15": None
            },
            None,
            GemRules(
                [],
                []
            )
        ),
        LevelRules(
            "Scorch",
            lambda state: logic.can_enter_autumn(state),
            lambda state: logic.can_enter_scorch(state),
            None,
            {
                # TODO: Add powerup logic.
                "Scorch: Barrel of Monkeys": None,
                "Scorch: Capture the flags": None
            },
            {},
            {
                "Scorch: Life Bottle": None
            },
            {
                "Scorch: All Trees": None
            },
            None,
            GemRules(
                [1, 2, 3, 4, 5, 93, 94, 95, 96, 97, 98, 99, 100, 101, 106, 115, 134, 135, 136, 137, 142, 143, 144, 148],
                # TODO: Add powerup logic.
                []
            )
        ),
        LevelRules(
            "Shady Oasis",
            lambda state: logic.can_enter_autumn(state),
            lambda state: logic.can_enter_shady(state),
            None,
            {
                # TODO: Add powerup logic.
                "Shady Oasis: Catch 3 thieves": None,
                "Shady Oasis: Free Hippos": lambda state: logic.can_access_shady_hippos(state)
            },
            {},
            {
                "Shady Oasis: Life Bottle": None
            },
            {},
            None,
            GemRules(
                [1, 2, 3, 4, 5, 6, 7, 28, 29, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 138, 140, 141, 142, 143, 148, 155, 168, 169],
                # TODO: Add powerup logic.
                [
                    GemRuleRestriction(
                        [144, 145, 146, 147],
                        "breaking a headbash crate",
                        lambda state: logic.can_break_headbash_crate(state),
                        20
                    )
                ]
            )
        ),
        LevelRules(
            "Magma Cone",
            lambda state: logic.can_enter_autumn(state),
            lambda state: logic.can_enter_magma(state),
            lambda state: logic.can_access_magma_talisman(state),
            {
                # TODO: Add powerup logic.
                "Magma Cone: Crystal geysers I": lambda state: logic.can_access_magma_popcorn(state),
                "Magma Cone: Crystal geysers II": lambda state: logic.can_access_magma_popcorn(state),
                "Magma Cone: Party crashers": lambda state: logic.can_access_magma_party_crashers(state),
            },
            {"Magma Cone: Moneybags Unlock: Magma Cone Elevator": lambda state: logic.can_access_magma_moneybags(state)},
            {
                "Magma Cone: Life Bottle by Moneybags": lambda state: logic.can_access_magma_moneybags(state),
                "Magma Cone: Life Bottle on Ledge 1": lambda state: logic.can_access_magma_moneybags(state),
                "Magma Cone: Life Bottle on Ledge 2": lambda state: logic.can_access_magma_moneybags(state),
                "Magma Cone: Life Bottle on Ledge 3": lambda state: logic.can_access_magma_moneybags(state)
            },
            {},
            lambda state: logic.can_access_magma_party_crashers(state),
            GemRules(
                [1, 2, 48, 78, 121, 122, 123],
                # TODO: Handle climb and powerup logic.
                [
                    GemRuleRestriction(
                        [27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 92, 93, 94, 95, 96, 97, 98, 99, 100, 114, 115, 116, 117, 118, 119, 120, 124, 125, 126],
                        "access to the magma cone elevator",
                        lambda state: logic.can_access_magma_talisman(state),
                        105
                    )
                ]
            )
        ),
        LevelRules(
            "Fracture Hills",
            lambda state: logic.can_enter_autumn(state),
            lambda state: logic.can_enter_fracture(state),
            None,
            {
                # TODO: Add powerup logic.
                "Fracture Hills: Earthshaper bash": lambda state: logic.can_access_fracture_hunter(state),
                "Fracture Hills: Free the faun": lambda state: logic.can_access_fracture_faun(state),
                "Fracture Hills: Alchemist escort": None,
            },
            {},
            {
                "Fracture Hills: Life Bottle": None
            },
            {
                "Fracture Hills: 3 Laps of Supercharge": lambda state: logic.can_access_fracture_supercharge(state)
            },
            lambda state: logic.can_access_fracture_enemies(state),
            GemRules(
                [1, 2, 3, 20, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91],
                # TODO: Handle powerup logic.
                []
            )
        ),
        LevelRules(
            "Icy Speedway",
            lambda state: logic.can_enter_autumn(state),
            lambda state: logic.can_enter_icy(state),
            None,
            {
                "Icy Speedway: Parasail through Rings": None
            },
            {},
            {},
            {
                "Icy Speedway: Under 1:15": None
            },
            None,
            GemRules(
                [],
                []
            )
        ),
        LevelRules(
            "Gulp's Overlook",
            lambda state: logic.can_enter_autumn(state),
            lambda state: logic.can_enter_gulp(state),
            None,
            {},
            {},
            {},
            {
                "Gulp's Overlook: Perfect": None,
                "Gulp's Overlook: Hit Ripto": None
            },
            None,
            GemRules(
                [],
                []
            )
        ),
        LevelRules(
            "Winter Tundra",
            None,
            lambda state: logic.can_enter_winter(state),
            None,
            {
                "Winter Tundra: On the tall wall": lambda state: logic.can_access_winter_second_half(state),
                "Winter Tundra: Top of the waterfall": lambda state: logic.can_access_winter_waterfall(state),
                "Winter Tundra: Smash the rock": lambda state: logic.can_headbash(state)
            },
            {
                "Winter Tundra: Moneybags Unlock: Canyon Speedway Portal": None,
                "Winter Tundra: Moneybags Unlock: Headbash": None
            },
            {},
            {},
            None,
            GemRules(
                [1, 2, 3, 4, 5, 6, 7, 13, 14, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143],
                [
                    GemRuleRestriction(
                        [96, 97, 98, 99, 100, 101, 102],
                        "breaking a headbash crate",
                        lambda state: logic.can_break_headbash_crate(state),
                        35
                    ),
                    GemRuleRestriction(
                        [8, 9, 10, 11, 12],
                        "headbash",
                        lambda state: logic.can_headbash(state),
                        11
                    ),
                    GemRuleRestriction(
                        [30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 68, 69, 70, 71, 72, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 92, 93, 94, 95, 103, 104, 105, 106],
                        "headbash",
                        lambda state: logic.can_access_winter_second_half(state),
                        208
                    ),
                    GemRuleRestriction(
                        [73, 74, 75, 76, 77],
                        "access past the Ripto door",
                        lambda state: logic.can_access_ripto(state),
                        7
                    )
                ]
            )
        ),
        LevelRules(
            "Mystic Marsh",
            lambda state: logic.can_enter_winter(state),
            lambda state: logic.can_enter_mystic(state),
            None,
            {
                "Mystic Marsh: Fix the fountain": None,
                "Mystic Marsh: Very versatile thieves!": lambda state: logic.can_swim(state),
                "Mystic Marsh: Retrieve professor's pencil": None
            },
            {},
            {
                "Mystic Marsh: Life Bottle by Basil": None,
                "Mystic Marsh: Life Bottle by Cooking Pot": None,
            },
            {},
            lambda state: logic.can_swim(state),
            GemRules(
                [1, 112, 113, 114, 115, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157],
                [
                    GemRuleRestriction(
                        [43, 69, 70, 71, 72, 73, 74, 75, 76, 95, 96, 97, 98, 99, 100, 116, 117, 118, 119, 120, 121, 127, 128, 129, 130, 134, 135, 136, 141],
                        "swim",
                        lambda state: logic.can_swim(state),
                        88
                    )
                ]
            )
        ),
        LevelRules(
            "Cloud Temples",
            lambda state: logic.can_enter_winter(state),
            lambda state: logic.can_enter_cloud(state),
            None,
            {
                # TODO: Work out powerup logic.
                "Cloud Temples: Agent Zero's secret hideout": None,
                "Cloud Temples: Ring tower bells": None,
                "Cloud Temples: Break down doors": None
            },
            {},
            {
                "Cloud Temples: Life Bottle": None,
            },
            {},
            None,
            GemRules(
                [1, 34, 54, 55, 101, 102, 103],
                [
                    GemRuleRestriction(
                        [104, 105, 106, 107, 108],
                        "breaking a headbash crate",
                        lambda state: logic.can_break_headbash_crate(state),
                        25
                    )
                ]
            )
        ),
        LevelRules(
            "Canyon Speedway",
            lambda state: logic.can_enter_winter(state),
            lambda state: logic.can_enter_canyon(state),
            None,
            {
                "Canyon Speedway: Shoot down balloons": None
            },
            {},
            {},
            {
                "Canyon Speedway: Under 1:10": None
            },
            None,
            GemRules(
                [],
                []
            )
        ),
        LevelRules(
            "Robotica Farms",
            lambda state: logic.can_enter_winter(state),
            lambda state: logic.can_enter_robotica(state),
            None,
            {
                # TODO: Work out powerup logic.
                "Robotica Farms: Switch on bug light": None,
                "Robotica Farms: Clear tractor path": None,
                "Robotica Farms: Exterminate crow bugs": None
            },
            {},
            {},
            {},
            lambda state: logic.can_fireball(state) or logic.can_headbash(state),
            GemRules(
                [1, 2, 3, 4, 5, 6, 7, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 130, 138, 139, 147, 148, 149, 150, 151, 152, 179, 180, 181, 182, 183],
                # TODO: Powerup logic
                []
            )
        ),
        LevelRules(
            "Metropolis",
            lambda state: logic.can_enter_winter(state),
            lambda state: logic.can_enter_metropolis(state),
            None,
            {
                # TODO: Work out powerup logic.
                "Metropolis: Conquer invading cows": lambda state: logic.can_pass_metropolis_elevators(state),
                "Metropolis: Shoot down sheep saucers I": lambda state: logic.can_pass_metropolis_elevators(state),
                "Metropolis: Shoot down sheep saucers II": lambda state: logic.can_pass_metropolis_elevators(state),
                "Metropolis: Ox bombing": lambda state: logic.can_access_metropolis_ox(state),
            },
            {},
            {},
            {},
            lambda state: logic.can_pass_metropolis_elevators(state),
            GemRules(
                [38, 45, 65, 91, 97, 105, 129, 130, 131, 132],
                [
                    GemRuleRestriction(
                        [17, 18, 19],
                        "access to the ox area",
                        lambda state: logic.can_access_metropolis_ox(state),
                        15
                    ),
                    GemRuleRestriction(
                        [9, 10, 11, 12, 13, 14, 15, 16, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 39, 40, 41, 42, 43, 44, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 92, 93, 94, 95, 96, 98, 99, 100, 101, 102, 103, 104, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 133, 134, 135, 136],
                        "access past the elevators",
                        lambda state: logic.can_pass_metropolis_elevators(state),
                        361
                    )
                ]
            )
        ),

        LevelRules(
            "Ripto's Arena",
            lambda state: logic.can_enter_winter(state),
            lambda state: logic.can_fight_ripto(state),
            None,
            {},
            {},
            {},
            {
                "Ripto's Arena: Perfect": None
            },
            None,
            GemRules(
                [],
                []
            )
        ),
    ]
