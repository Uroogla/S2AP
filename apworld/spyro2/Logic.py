from abc import ABC, abstractmethod
from Options import OptionError
from worlds.AutoWorld import World
from .Options import AbilityOptions, SparxUpgradeOptions, LevelLockOptions
from .LogicTricks import normalized_name_tricks

class Logic(ABC):
    world: World = None

    # General Logic/Abilities
    def is_boss_defeated(self, boss, state):
        if self.world.options.enable_open_world and self.world.options.open_world_warp_unlocks and boss in ["Crush", "Gulp"]:
            return True
        return state.has(boss + " Defeated", self.world.player)

    def can_bypass_moneybags(self, state):
        # TODO: Add theater logic.
        return self.is_boss_defeated("Ripto", state)

    def can_swim(self, state):
        return state.has("Moneybags Unlock - Swim", self.world.player) or self.can_bypass_moneybags(state)

    def can_climb(self, state):
        return state.has("Moneybags Unlock - Climb", self.world.player) or self.can_bypass_moneybags(state)

    def can_headbash(self, state):
        return state.has("Moneybags Unlock - Headbash", self.world.player) or self.can_bypass_moneybags(state)

    def can_double_jump(self, state):
        return self.world.options.double_jump_ability.value == AbilityOptions.VANILLA or state.has("Double Jump Ability", self.world.player)

    def can_fireball(self, state):
        # TODO: Need to handle logic for fireball from shores out of bounds,
        # but this is computationally complex and almost never affects vanilla logic.
        return self.world.options.permanent_fireball_ability.value == AbilityOptions.START_WITH or \
            self.world.options.permanent_fireball_ability.value == AbilityOptions.IN_POOL and state.has("Permanent Fireball Ability", self.world.player)

    def can_break_headbash_crate(self, state):
        return self.can_headbash(state) or self.can_fireball(state)

    def get_gemsanity_gems(self, level, state):
        count = 0
        count += state.count(f"{level} Red Gem", self.world.player)
        count += state.count(f"{level} Green Gem", self.world.player) * 2
        count += state.count(f"{level} Blue Gem", self.world.player) * 5
        count += state.count(f"{level} Gold Gem", self.world.player) * 10
        count += state.count(f"{level} Pink Gem", self.world.player) * 25
        count += state.count(f"{level} Gem Bundle", self.world.player) * self.world.options.gemsanity_gem_bundle_size
        return count

    def has_sparx_health(self, health, state):
        if self.world.options.enable_progressive_sparx_health.value in [SparxUpgradeOptions.OFF, SparxUpgradeOptions.TRUE_SPARXLESS]:
            return True
        max_health = 0
        if self.world.options.enable_progressive_sparx_health.value == SparxUpgradeOptions.BLUE:
            max_health = 2
        elif self.world.options.enable_progressive_sparx_health.value == SparxUpgradeOptions.GREEN:
            max_health = 1
        max_health += state.count("Progressive Sparx Health Upgrade", self.world.player)
        return max_health >= health

    def can_satisfy_level_lock(self, level_name, state):
        if self.world.options.level_lock_options.value == LevelLockOptions.VANILLA:
            return True
        if level_name in ["Summer Forest", "Glimmer", "Crush's Dungeon", "Autumn Plains", "Gulp's Overlook", "Winter Tundra", "Ripto's Arena"]:
            return True
        if self.world.options.level_lock_options.value == LevelLockOptions.KEYS:
            return state.has(f"{level_name} Unlock", self.world.player)
        return True

    # Level Access logic
    def can_enter_idol(self, state):
        return self.can_satisfy_level_lock("Idol Springs", state)

    def can_enter_colossus(self, state):
        return self.can_satisfy_level_lock("Colossus", state)

    def can_enter_hurricos(self, state):
        return self.can_access_summer_second_half(state) and self.can_satisfy_level_lock("Hurricos", state)

    def can_enter_aquaria(self, state):
        if self.world.options.enable_progressive_sparx_logic.value:
            return self.can_access_sf_past_aquaria_wall(state) and self.can_satisfy_level_lock("Aquaria Towers", state) and self.has_sparx_health(1, state)
        else:
            return self.can_access_sf_past_aquaria_wall(state) and self.can_satisfy_level_lock("Aquaria Towers", state)

    def can_enter_sunny(self, state):
        return self.can_access_summer_second_half(state) and self.can_satisfy_level_lock("Sunny Beach", state)

    def can_enter_ocean(self, state):
        return self.can_access_summer_second_half(state) and \
            self.can_satisfy_level_lock("Ocean Speedway", state) and \
            (
                    state.has("Orb", self.world.player, 3) or
                    hasattr(self, "logic_sf_swim_in_air") and self.logic_sf_swim_in_air and self.can_swim(state)
            )

    def can_enter_crush(self, state):
        has_sufficient_sparx = not self.world.options.enable_progressive_sparx_logic.value or self.has_sparx_health(1, state)
        is_open_world = self.world.options.enable_open_world.value
        # While there are several ways to skip into Crush early,
        # the player has chosen not to be in open world, so there's no reason
        # to add tricks for these skips.
        return self.can_access_summer_second_half(state) and \
            has_sufficient_sparx and \
            (
                is_open_world or
                state.has("Summer Forest Talisman", self.world.player, 6)
            )


    def can_enter_autumn(self, state):
        return self.world.options.enable_open_world and self.world.options.open_world_warp_unlocks or \
            self.is_boss_defeated("Crush", state)

    def can_enter_skelos(self, state):
        if self.world.options.enable_progressive_sparx_logic.value:
            return self.can_satisfy_level_lock("Skelos Badlands", state) and self.has_sparx_health(2, state)
        else:
            return self.can_satisfy_level_lock("Skelos Badlands", state)

    def can_enter_crystal(self, state):
        if self.world.options.enable_progressive_sparx_logic.value:
            return self.can_satisfy_level_lock("Crystal Glacier", state) and self.has_sparx_health(1, state)
        else:
            return self.can_satisfy_level_lock("Crystal Glacier", state)

    def can_enter_breeze(self, state):
        if self.world.options.enable_progressive_sparx_logic.value:
            return self.can_satisfy_level_lock("Breeze Harbor", state) and self.has_sparx_health(1, state)
        else:
            return self.can_satisfy_level_lock("Breeze Harbor", state)

    def can_enter_zephyr(self, state):
        if not state.has("Moneybags Unlock - Zephyr Portal", self.world.player) and not self.can_bypass_moneybags(state):
            return False
        if self.world.options.enable_progressive_sparx_logic.value:
            return self.can_satisfy_level_lock("Zephyr", state) and self.has_sparx_health(1, state)
        else:
            return self.can_satisfy_level_lock("Zephyr", state)

    def can_enter_metro(self, state):
        return state.has("Orb", self.world.player, 6) and self.can_satisfy_level_lock("Metro Speedway", state)

    def can_enter_scorch(self, state):
        if not self.can_access_autumn_second_half(state):
            return False
        if self.world.options.enable_progressive_sparx_logic.value:
            return self.can_satisfy_level_lock("Scorch", state) and self.has_sparx_health(1, state)
        else:
            return self.can_satisfy_level_lock("Scorch", state)

    def can_enter_shady(self, state):
        if not self.can_access_autumn_shady_section(state):
            return False
        if self.world.options.enable_progressive_sparx_logic.value:
            return self.can_satisfy_level_lock("Shady Oasis", state) and self.has_sparx_health(1, state)
        else:
            return self.can_satisfy_level_lock("Shady Oasis", state)

    def can_enter_magma(self, state):
        if not self.can_pass_autumn_door(state):
            return False
        if self.world.options.enable_progressive_sparx_logic.value:
            return self.can_satisfy_level_lock("Magma Cone", state) and self.has_sparx_health(1, state)
        else:
            return self.can_satisfy_level_lock("Magma Cone", state)

    def can_enter_fracture(self, state):
        if not self.can_access_autumn_second_half(state):
            return False
        if self.world.options.enable_progressive_sparx_logic.value:
            return self.can_satisfy_level_lock("Fracture Hills", state) and self.has_sparx_health(1, state)
        else:
            return self.can_satisfy_level_lock("Fracture Hills", state)

    def can_enter_icy(self, state):
        return self.can_pass_autumn_door(state) and self.can_satisfy_level_lock("Icy Speedway", state) and \
            (self.can_bypass_moneybags(state) or state.has("Moneybags Unlock - Icy Speedway Portal", self.world.player))

    def can_enter_gulp(self, state):
        has_sufficient_sparx = not self.world.options.enable_progressive_sparx_logic.value or self.has_sparx_health(2, state)
        is_open_world = self.world.options.enable_open_world.value
        return self.can_pass_autumn_door(state) and has_sufficient_sparx and \
            (is_open_world or (state.has("Summer Forest Talisman", self.world.player, 6) and state.has("Autumn Plains Talisman", self.world.player, 8)))

    def can_enter_winter(self, state):
        return self.world.options.enable_open_world and self.world.options.open_world_warp_unlocks or \
            self.is_boss_defeated("Gulp", state)

    def can_enter_mystic(self, state):
        if self.world.options.enable_progressive_sparx_logic.value:
            return self.can_satisfy_level_lock("Mystic Marsh", state) and self.has_sparx_health(2, state)
        else:
            return self.can_satisfy_level_lock("Mystic Marsh", state)

    def can_enter_cloud(self, state):
        if not self.can_satisfy_level_lock("Cloud Temples", state):
            return False
        if self.world.options.enable_progressive_sparx_logic.value:
            if not self.has_sparx_health(2, state):
                return False
        return state.has("Orb", self.world.player, 15) or \
            self.can_access_winter_second_half(state) and \
            (
                hasattr(self, "logic_wt_oob_double_jump") and self.logic_wt_oob_double_jump and self.can_double_jump(state) or
                hasattr(self, "logic_wt_oob_nothing") and self.logic_wt_oob_nothing
            ) and \
            (
                hasattr(self, "logic_wt_swim_from_oob") and self.logic_wt_swim_from_oob and self.can_swim(state) or
                hasattr(self, "logic_wt_glide_from_oob") and self.logic_wt_glide_from_oob
            )

    def can_enter_canyon(self, state):
        return self.can_satisfy_level_lock("Canyon Speedway", state) and \
            (
                self.can_bypass_moneybags(state) or
                state.has("Moneybags Unlock - Canyon Speedway Portal", self.world.player) or
                self.can_access_winter_second_half(state) and
                (
                    hasattr(self, "logic_wt_oob_double_jump") and self.logic_wt_oob_double_jump and self.can_double_jump(state) or
                    hasattr(self, "logic_wt_oob_nothing") and self.logic_wt_oob_nothing
                ) and
                (
                    hasattr(self, "logic_wt_swim_from_oob") and self.logic_wt_swim_from_oob and self.can_swim(state) or
                    hasattr(self, "logic_wt_glide_from_oob") and self.logic_wt_glide_from_oob
                )
            )

    def can_enter_robotica(self, state):
        if not self.can_access_winter_second_half(state):
            return False
        if self.world.options.enable_progressive_sparx_logic.value:
            return self.can_satisfy_level_lock("Robotica Farms", state) and self.has_sparx_health(2, state)
        else:
            return self.can_satisfy_level_lock("Robotica Farms", state)

    def can_enter_metropolis(self, state):
        if not self.can_satisfy_level_lock("Metropolis", state):
            return False
        if self.world.options.enable_progressive_sparx_logic.value:
            if not self.has_sparx_health(2, state):
                return False
        return self.can_access_winter_second_half(state) and \
            (
                state.has("Orb", self.world.player, 25) or
                (
                    hasattr(self, "logic_wt_oob_double_jump") and self.logic_wt_oob_double_jump and self.can_double_jump(state) or
                    hasattr(self, "logic_wt_oob_nothing") and self.logic_wt_oob_nothing
                ) and
                (
                    hasattr(self, "logic_wt_swim_from_oob") and self.logic_wt_swim_from_oob and self.can_swim(state) or
                    hasattr(self, "logic_wt_glide_from_oob") and self.logic_wt_glide_from_oob
                )
            )

    def can_fight_ripto(self, state):
        return self.can_access_ripto(state) and \
            (not self.world.options.enable_progressive_sparx_logic.value or self.has_sparx_health(3, state))

    def can_enter_shores(self, state):
        if self.is_boss_defeated("Ripto", state):
            return True

        if not self.can_satisfy_level_lock("Dragon Shores", state):
            return False
        return self.can_access_winter_second_half(state) and \
            (
                (
                    hasattr(self, "logic_wt_oob_double_jump") and self.logic_wt_oob_double_jump and self.can_double_jump(state) or
                    hasattr(self, "logic_wt_oob_nothing") and self.logic_wt_oob_nothing
                ) and
                (
                    hasattr(self, "logic_wt_swim_from_oob") and self.logic_wt_swim_from_oob and self.can_swim(state) or
                    hasattr(self, "logic_wt_glide_from_oob") and self.logic_wt_glide_from_oob
                )
            )

    # Level-specific logic
    def can_access_sf_secret_ledge(self, state):
        return self.can_swim(state) or \
            hasattr(self, "logic_sf_ledge_double_jump") and self.logic_sf_ledge_double_jump and self.can_double_jump(state)

    def can_access_summer_second_half(self, state):
        return self.can_swim(state) or \
            hasattr(self, "logic_sf_second_half_double_jump") and self.logic_sf_second_half_double_jump and self.can_double_jump(state) or \
            hasattr(self, "logic_sf_second_half_nothing") and self.logic_sf_second_half_nothing

    def can_access_sf_ladder(self, state):
        return self.can_access_summer_second_half(state) and \
            (
                self.can_climb(state) or
                hasattr(self, "logic_sf_swim_in_air") and self.logic_sf_swim_in_air and self.can_swim(state) or
                hasattr(self, "logic_sf_frog_proxy") and self.logic_sf_frog_proxy
            )

    def can_access_sf_past_aquaria_wall(self, state):
        return self.can_access_summer_second_half(state) and \
            (
                hasattr(self, "logic_sf_swim_in_air") and self.logic_sf_swim_in_air and self.can_swim(state) or
                hasattr(self, "logic_sf_aquaria_wall_double_jump") and self.logic_sf_aquaria_wall_double_jump and self.can_double_jump(state) or
                hasattr(self, "logic_sf_aquaria_wall_nothing") and self.logic_sf_aquaria_wall_nothing or
                self.can_bypass_moneybags(state) or
                state.has("Moneybags Unlock - Wall by Aquaria Towers", self.world.player)
            )

    def can_do_glimmer_outdoor_lamps(self, state):
        return True

    def can_do_glimmer_indoor_lamps(self, state):
        return self.can_climb(state) or \
            hasattr(self, "logic_indoor_lamps_double_jump") and self.logic_indoor_lamps_double_jump and self.can_double_jump(state) or \
            hasattr(self, "logic_indoor_lamps_fireball") and self.logic_indoor_lamps_fireball and self.can_fireball(state) or \
            hasattr(self, "logic_indoor_lamps_superfly") and self.logic_indoor_lamps_superfly

    def can_access_idol_lake(self, state):
        return self.can_swim(state)

    def can_access_aquaria_first_tunnel(self, state):
        return self.can_swim(state) or \
            hasattr(self, "logic_at_first_tunnel_double_jump") and self.logic_at_first_tunnel_double_jump and self.can_double_jump(state) or \
            hasattr(self, "logic_at_sheep_proxy") and self.logic_at_sheep_proxy

    def can_access_aquaria_room_two_bottom(self, state):
        return self.can_swim(state) or \
            hasattr(self, "logic_at_sheep_proxy") and self.logic_at_sheep_proxy

    def can_access_aquaria_room_two_crab_pit(self, state):
        return self.can_swim(state) or \
            hasattr(self, "logic_at_sheep_proxy") and self.logic_at_sheep_proxy and \
            hasattr(self, "logic_at_gems_oob") and self.logic_at_gems_oob

    def can_access_aquaria_room_two_shark_pit(self, state):
        return self.can_swim(state) and \
            (
                self.can_bypass_moneybags(state) or
                state.has("Moneybags Unlock - Aquaria Towers Submarine", self.world.player) or
                self.can_fireball(state)
            ) or \
            (
                hasattr(self, "logic_at_sheep_proxy") and self.logic_at_sheep_proxy and
                hasattr(self, "logic_at_gems_oob") and self.logic_at_gems_oob and
                self.can_fireball(state)
            )

    def can_access_aquaria_room_two_middle(self, state):
        return self.can_swim(state) or \
            (
                hasattr(self, "logic_at_sheep_proxy") and self.logic_at_sheep_proxy and
                hasattr(self, "logic_at_gems_oob") and self.logic_at_gems_oob
            )

    def can_access_aquaria_room_two_top(self, state):
        return self.can_swim(state) and \
            (
                self.can_bypass_moneybags(state) or
                state.has("Moneybags Unlock - Aquaria Towers Submarine", self.world.player) or
                (
                    hasattr(self, "logic_at_button_three_fireball") and self.logic_at_button_three_fireball and
                    self.can_fireball(state)
                )
            ) or \
            (
                hasattr(self, "logic_at_sheep_proxy") and self.logic_at_sheep_proxy and
                hasattr(self, "logic_at_gems_oob") and self.logic_at_gems_oob
            )

    def can_access_aquaria_pre_moneybags_tunnel(self, state):
        return self.can_swim(state) or \
            (
                hasattr(self, "logic_at_sheep_proxy") and self.logic_at_sheep_proxy and
                hasattr(self, "logic_at_gems_oob") and self.logic_at_gems_oob
            )

    def can_access_aquaria_shark_tunnel(self, state):
        return self.can_swim(state) and \
            (
                self.can_bypass_moneybags(state) or
                state.has("Moneybags Unlock - Aquaria Towers Submarine", self.world.player) or
                (
                    hasattr(self, "logic_at_button_three_fireball") and self.logic_at_button_three_fireball and
                    self.can_fireball(state)
                )
            ) or \
            (
                hasattr(self, "logic_at_sheep_proxy") and self.logic_at_sheep_proxy and
                hasattr(self, "logic_at_gems_oob") and self.logic_at_gems_oob and
                self.can_fireball(state)
            )

    def can_access_aquaria_room_three(self, state):
        return self.can_swim(state) and \
            (
                self.can_bypass_moneybags(state) or
                state.has("Moneybags Unlock - Aquaria Towers Submarine", self.world.player) or
                (
                    hasattr(self, "logic_at_button_three_fireball") and self.logic_at_button_three_fireball and
                    self.can_fireball(state)
                )
            ) or \
            hasattr(self, "logic_at_sheep_proxy") and self.logic_at_sheep_proxy

    def can_access_aquaria_talisman_area_gems(self, state):
        return self.can_access_aquaria_room_three(state) or \
            hasattr(self, "logic_at_talisman_area_double_jump") and self.logic_at_talisman_area_double_jump and self.can_double_jump(state)

    def can_complete_aquaria_children_orb(self, state):
        return (
                self.can_access_aquaria_room_three(state) and
                hasattr(self, "logic_at_royal_children_oob") and self.logic_at_royal_children_oob
            ) or \
            self.can_swim(state) and \
            (
                self.can_bypass_moneybags(state) or
                state.has("Moneybags Unlock - Aquaria Towers Submarine", self.world.player)
            )

    def can_get_aquaria_spirit_particles(self, state):
        return self.can_swim(state) and \
            (
                self.can_bypass_moneybags(state) or
                state.has("Moneybags Unlock - Aquaria Towers Submarine", self.world.player)
            )

    def can_access_sunny_middle_room(self, state):
        return self.can_swim(state) or \
            hasattr(self, "logic_sb_first_turtle") and self.logic_sb_first_turtle

    def can_access_sunny_middle_ladders(self, state):
        return self.can_access_sunny_middle_room(state) and \
            (
                self.can_climb(state) or
                hasattr(self, "logic_sb_double_jump_ladder_skip") and self.logic_sb_double_jump_ladder_skip and self.can_double_jump(state) or
                hasattr(self, "logic_sb_nothing_ladder_skip") and self.logic_sb_nothing_ladder_skip
            )

    def can_access_sunny_final_area(self, state):
        return self.can_swim(state) or \
            hasattr(self, "logic_sb_first_turtle") and self.logic_sb_first_turtle

    def can_access_sunny_turtle_soup(self, state):
        return hasattr(self, "logic_sb_first_turtle") and self.logic_sb_first_turtle or \
            self.can_swim(state) and \
            (
                hasattr(self, "logic_sb_final_turtle") and self.logic_sb_final_turtle or
                self.can_climb(state)
            )

    def can_access_metro_platform(self, state):
        # Or a proxy, at a later date.
        return state.has("Orb", self.world.player, 6) or \
            self.can_pass_autumn_door(state) or \
            hasattr(self, "logic_ap_zephyr_double_jump") and self.logic_ap_zephyr_double_jump and self.can_double_jump(state)

    def can_access_autumn_wall(self, state):
        # Or a proxy, at a later date.
        return state.has("Orb", self.world.player, 6) or \
            self.can_pass_autumn_door(state) or \
            hasattr(self, "logic_ap_zephyr_double_jump") and self.logic_ap_zephyr_double_jump and self.can_double_jump(state)

    def can_access_autumn_second_half(self, state):
        # Or double frog proxy.
        return self.can_climb(state) or \
            hasattr(self, "logic_ap_climb_skip") and self.logic_ap_climb_skip and self.can_double_jump(state)

    def can_pass_autumn_door(self, state):
        # Or double frog proxy.
        return self.can_access_autumn_second_half(state) and \
            (
                state.has("Orb", self.world.player, 8) or
                hasattr(self, "logic_ap_door_skip") and self.logic_ap_door_skip and self.can_double_jump(state) or
                hasattr(self, "logic_ap_climb_skip") and self.logic_ap_climb_skip and self.can_double_jump(state)
            )

    def can_access_autumn_shady_section(self, state):
        return self.can_pass_autumn_door(state) and \
            (self.can_bypass_moneybags(state) or state.has("Moneybags Unlock - Shady Oasis Portal", self.world.player))

    def can_access_crystal_bridge(self, state):
        return self.can_bypass_moneybags(state) or \
            state.has("Moneybags Unlock - Crystal Glacier Bridge", self.world.player) or \
            hasattr(self, "logic_crystal_bridge_double_jump") and self.logic_crystal_bridge_double_jump and self.can_double_jump(state) or \
            hasattr(self, "logic_crystal_bridge_snowball_proxy") and self.logic_crystal_bridge_snowball_proxy

    def can_access_zephyr_ladder(self, state):
        return self.can_climb(state) or \
            hasattr(self, "logic_zephyr_ladder_double_jump") and self.logic_zephyr_ladder_double_jump and self.can_double_jump(state)

    def can_access_shady_hippos(self, state):
        return self.can_headbash(state) or (not self.world.options.shady_require_headbash.value and self.can_fireball(state))

    def can_pass_magma_start(self, state):
        return self.can_climb(state) or \
            hasattr(self, "logic_mc_start_double_jump") and self.logic_mc_start_double_jump and self.can_double_jump(state) or \
            hasattr(self, "logic_mc_start_nothing") and self.logic_mc_start_nothing

    def can_reach_magma_second_level(self, state):
        return self.can_pass_magma_start(state) and \
            (
                self.can_climb(state) or
                hasattr(self, "logic_mc_second_level_double_jump") and self.logic_mc_second_level_double_jump and self.can_double_jump(state)
            )

    def can_access_magma_popcorn(self, state):
        return self.can_pass_magma_start(state) and \
            (
                self.can_climb(state) or
                hasattr(self, "logic_mc_popcorn_double_jump") and self.logic_mc_popcorn_double_jump and self.can_double_jump(state)
            )

    def can_access_magma_moneybags(self, state):
        return self.can_reach_magma_second_level(state) and \
        (
            self.can_climb(state) or
            hasattr(self, "logic_mc_moneybags_double_jump") and self.logic_mc_moneybags_double_jump and self.can_double_jump(state)
        )

    def can_pass_magma_elevator(self, state):
        return self.can_access_magma_moneybags(state) and \
            (
                state.has("Moneybags Unlock - Magma Cone Elevator", self.world.player) or
                self.can_bypass_moneybags(state) or
                hasattr(self, "logic_mc_elevator_double_jump") and self.logic_mc_elevator_double_jump and self.can_double_jump(state)
            )

    def can_access_magma_talisman(self, state):
        return self.can_pass_magma_elevator(state) and self.can_climb(state) or \
            self.can_access_magma_moneybags(state) and hasattr(self, "logic_mc_elevator_double_jump") and self.logic_mc_elevator_double_jump and self.can_double_jump(state)

    def can_access_magma_party_crashers(self, state):
        return self.can_access_magma_talisman(state)

    def can_access_magma_fireball_balloons(self, state):
        return self.can_access_magma_party_crashers(state) or self.can_pass_magma_elevator(state) and self.can_fireball(state)

    def can_access_fracture_supercharge(self, state):
        return True

    def can_access_fracture_faun(self, state):
        return True

    def can_access_fracture_hunter(self, state):
        return self.can_headbash(state) or (not self.world.options.fracture_require_headbash.value and self.can_fireball(state))

    def can_access_fracture_enemies(self, state):
        return self.world.options.fracture_easy_earthshapers.value or self.can_fireball(state) or self.can_access_fracture_hunter(state)

    def can_access_winter_second_half(self, state):
        return self.can_headbash(state) or \
            hasattr(self, "logic_wt_castle_double_jump") and self.logic_wt_castle_double_jump and self.can_double_jump(state) or \
            hasattr(self, "logic_wt_castle_penguin_proxy") and self.logic_wt_castle_penguin_proxy

    def can_access_winter_waterfall(self, state):
        return self.can_access_winter_second_half(state) and \
            (
                self.can_swim(state) or
                hasattr(self, "logic_wt_oob_double_jump") and self.logic_wt_oob_double_jump and self.can_double_jump(state) or
                hasattr(self, "logic_wt_oob_nothing") and self.logic_wt_oob_nothing
            )

    def can_pass_metropolis_elevators(self, state):
        return self.can_headbash(state) or self.can_fireball(state)

    def can_access_metropolis_ox(self, state):
        return self.can_pass_metropolis_elevators(state) and \
            (
                self.can_climb(state) or
                hasattr(self, "logic_metropolis_ox_superfly") and self.logic_metropolis_ox_superfly
            )

    def can_access_ripto(self, state):
        return self.can_access_winter_second_half(state) and \
            (
                state.has("Orb", self.world.player, self.world.options.ripto_door_orbs.value) or
                (
                        hasattr(self, "logic_wt_oob_double_jump") and self.logic_wt_oob_double_jump and self.can_double_jump(state) or
                        hasattr(self, "logic_wt_oob_nothing") and self.logic_wt_oob_nothing
                ) and
                hasattr(self, "logic_wt_swim_from_oob") and self.logic_wt_swim_from_oob and self.can_swim(state)
            )


class BaseLogic(Logic):
    def __init__(self, world: World):
        self.world = world

    def can_pass_magma_elevator(self, state):
        return self.can_access_magma_moneybags(state) and \
            (self.can_bypass_moneybags(state) or state.has("Moneybags Unlock - Magma Cone Elevator", self.world.player))

    def can_access_magma_talisman(self, state):
        return self.can_pass_magma_elevator(state) and self.can_climb(state)


class EasyLogic(Logic):
    def __init__(self, world: World):
        self.world = world
        setattr(self, "logic_sf_second_half_double_jump", True)
        setattr(self, "logic_sf_swim_in_air", True)
        setattr(self, "logic_indoor_lamps_double_jump", True)
        setattr(self, "logic_indoor_lamps_fireball", True)
        setattr(self, "logic_sb_double_jump_ladder_skip", True)
        setattr(self, "logic_at_first_tunnel_double_jump", True)
        setattr(self, "logic_ap_zephyr_double_jump", True)
        setattr(self, "logic_ap_door_skip", True)
        setattr(self, "logic_mc_start_double_jump", True)
        setattr(self, "logic_mc_second_level_double_jump", True)


class MediumLogic(Logic):
    def __init__(self, world: World):
        self.world = world
        setattr(self, "logic_sf_ledge_double_jump", True)
        setattr(self, "logic_sf_second_half_double_jump", True)
        setattr(self, "logic_sf_second_half_nothing", True)
        setattr(self, "logic_sf_swim_in_air", True)
        setattr(self, "logic_sf_aquaria_wall_double_jump", True)
        setattr(self, "logic_indoor_lamps_double_jump", True)
        setattr(self, "logic_indoor_lamps_fireball", True)
        setattr(self, "logic_indoor_lamps_superfly", True)
        setattr(self, "logic_sb_double_jump_ladder_skip", True)
        setattr(self, "logic_sb_nothing_ladder_skip", True)
        setattr(self, "logic_at_first_tunnel_double_jump", True)
        setattr(self, "logic_at_talisman_area_double_jump", True)
        setattr(self, "logic_at_button_three_fireball", True)
        setattr(self, "logic_at_royal_children_oob", True)
        setattr(self, "logic_ap_zephyr_double_jump", True)
        setattr(self, "logic_ap_climb_skip", True)
        setattr(self, "logic_ap_door_skip", True)
        setattr(self, "logic_crystal_bridge_double_jump", True)
        setattr(self, "logic_zephyr_ladder_double_jump", True)
        setattr(self, "logic_mc_start_double_jump", True)
        setattr(self, "logic_mc_start_nothing", True)
        setattr(self, "logic_mc_second_level_double_jump", True)
        setattr(self, "logic_mc_popcorn_double_jump", True)
        setattr(self, "logic_mc_moneybags_double_jump", True)
        setattr(self, "logic_mc_elevator_double_jump", True)
        setattr(self, "logic_wt_castle_double_jump", True)
        setattr(self, "logic_wt_oob_double_jump", True)
        setattr(self, "logic_wt_swim_from_oob", True)
        setattr(self, "logic_metropolis_ox_superfly", True)


class CustomLogic(Logic):
    def __init__(self, world: World):
        self.world = world
        # Determine tricks in logic
        for trick in self.world.options.custom_tricks:
            normalized_name = trick.casefold()
            if normalized_name in normalized_name_tricks:
                setattr(self, normalized_name_tricks[normalized_name]['name'], True)
            else:
                raise OptionError(f'Unknown Spyro 2 logic trick for player {self.player}: {trick}')
