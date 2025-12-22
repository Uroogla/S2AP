from abc import ABC, abstractmethod
from .Options import SparxUpgradeOptions


class Spyro2LogicRules(ABC):
    def __init__(self, player, options):
        self.player = player
        self.options = options

    def is_boss_defeated(self, boss, state):
        return state.has(boss + " Defeated", self.player)

    @abstractmethod
    def has_moneybags_unlock(self, unlock, state):
        pass

    def can_swim(self, state):
        return state.has("Moneybags Unlock - Swim", self.player)

    def can_climb(self, state):
        return state.has("Moneybags Unlock - Climb", self.player)

    def can_headbash(self, state):
        return state.has("Moneybags Unlock - Headbash", self.player)

    def can_double_jump(self, state):
        return state.has("Double Jump Ability", self.player)

    def can_fireball(self, state):
        # TODO: Handle vanilla unlock.
        return state.has("Permanent Fireball Ability", self.player)

    def get_gemsanity_gems(self, level, state):
        count = 0
        count += state.count(f"{level} Red Gem", self.player)
        count += state.count(f"{level} Green Gem", self.player) * 2
        count += state.count(f"{level} Blue Gem", self.player) * 5
        count += state.count(f"{level} Gold Gem", self.player) * 10
        count += state.count(f"{level} Pink Gem", self.player) * 25
        count += state.count(f"{level} 50 Gems", self.player) * 50
        return count

    def has_sparx_health(self, health, state):
        if self.options.enable_progressive_sparx_health.value in [
            SparxUpgradeOptions.OFF,
            SparxUpgradeOptions.TRUE_SPARXLESS
        ]:
            return True
        max_health = 0
        if self.options.enable_progressive_sparx_health.value == SparxUpgradeOptions.BLUE:
            max_health = 2
        elif self.options.enable_progressive_sparx_health.value == SparxUpgradeOptions.GREEN:
            max_health = 1
        max_health += state.count("Progressive Sparx Health Upgrade", self.player)
        return max_health >= health

    def has_all_talismans(self, state):
        return state.count("Summer Forest Talisman", self.player) >= 6 and \
            state.count("Autumn Plains Talisman", self.player) >= 8

    @abstractmethod
    def has_glimmer_indoor_lamps_access(self, state):
        pass


class Spyro2VanillaLogicRules(Spyro2LogicRules):
    def has_moneybags_unlock(self, unlock, state):
        return state.has(f"Moneybags Unlock - {unlock}", self.player) or self.is_boss_defeated("Ripto", state)

    def has_glimmer_indoor_lamps_access(self, state):
        return self.can_climb(state)


class Spyro2EasyLogicRules(Spyro2LogicRules):
    def has_moneybags_unlock(self, unlock, state):
        return state.has(f"Moneybags Unlock - {unlock}", self.player) or self.is_boss_defeated("Ripto", state)

    def has_glimmer_indoor_lamps_access(self, state):
        return self.can_climb(state) or self.can_double_jump(state) or self.can_fireball(state)


class Spyro2MediumLogicRules(Spyro2LogicRules):
    def has_moneybags_unlock(self, unlock, state):
        return state.has(f"Moneybags Unlock - {unlock}", self.player) or \
            self.is_boss_defeated("Ripto", state) or \
            self.has_theater_access(state)

    def has_glimmer_indoor_lamps_access(self, state):
        return True


class Spyro2HardLogicRules(Spyro2LogicRules):
    def has_moneybags_unlock(self, unlock, state):
        return state.has(f"Moneybags Unlock - {unlock}", self.player) or \
            self.is_boss_defeated("Ripto", state) or \
            self.has_theater_access(state)

    def has_glimmer_indoor_lamps_access(self, state):
        return True
