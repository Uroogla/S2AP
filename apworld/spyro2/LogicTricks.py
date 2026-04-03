known_logic_tricks = {

    'Summer Forest Ledge Orb with Double Jump': {
        'name'    : 'logic_sf_ledge_double_jump',
        'tags'    : ("Double Jump", "Summer Forest",),
        'tooltip' : '''\
                    Logic expects using double jump from the
                    end of Hunter's challenge to reach the
                    orb overlooking Colossus without swim.
                    '''
    },
    'Summer Forest Second Half with Double Jump': {
        'name'    : 'logic_sf_second_half_double_jump',
        'tags'    : ("Double Jump", "Summer Forest",),
        'tooltip' : '''\
                    Logic expects using double jump to reach the
                    second half of Summer Forest without swim.
                    '''
    },
    'Summer Forest Second Half with Nothing': {
        'name'    : 'logic_sf_second_half_nothing',
        'tags'    : ("Summer Forest",),
        'tooltip' : '''\
                    Logic expects no AP items to reach the
                    second half of Summer Forest.
                    '''
    },
    'Summer Forest Swim in Air': {
        'name'    : 'logic_sf_swim_in_air',
        'tags'    : ("Swim in Air", "Summer Forest",),
        'tooltip' : '''\
                    Logic expects using swim in air in Summer Forest
                    to climb the ladder, access gems inside the
                    Aquaria Towers wall, and enter Ocean Speedway,
                    Crush's Dungeon, and Aquaria Towers.
                    '''
    },
    'Enter Crush with Double Jump': {
        'name'    : 'logic_enter_crush_with_double_jump',
        'tags'    : ("Double Jump", "Summer Forest", "Crush's Dungeon",),
        'tooltip' : '''\
                    Logic expects using double jump in Summer Forest
                    enter Crush's Dungeon.
                    '''
    },
    'Summer Forest Frog Proxy': {
        'name'    : 'logic_sf_frog_proxy',
        'tags'    : ("Proxy", "Summer Forest",),
        'tooltip' : '''\
                    Logic expects using a frog proxy in Summer Forest
                    to bypass the ladder.
                    '''
    },
    'Summer Forest Aquaria Wall with Double Jump': {
        'name'    : 'logic_sf_aquaria_wall_double_jump',
        'tags'    : ("Double Jump", "Summer Forest",),
        'tooltip' : '''\
                    Logic expects using double jump in Summer Forest
                    to bypass the wall to Aquaria Towers.
                    '''
    },
    'Summer Forest Aquaria Wall with Nothing': {
        'name'    : 'logic_sf_aquaria_wall_nothing',
        'tags'    : ("Double Jump", "Summer Forest",),
        'tooltip' : '''\
                    Logic expects bypassing the wall to Aquaria Towers
                    with no AP items.
                    '''
    },
    'Glimmer Indoor Lamps with Double Jump': {
        'name'    : 'logic_indoor_lamps_double_jump',
        'tags'    : ("Double Jump", "Glimmer",),
        'tooltip' : '''\
                    Logic expects using double jump to complete
                    indoor lamps without climb.
                    Grants logical access to all climb-locked
                    areas.
                    '''
    },
    'Glimmer Indoor Lamps with Fireball': {
        'name'    : 'logic_indoor_lamps_fireball',
        'tags'    : ("Fireball", "Glimmer",),
        'tooltip' : '''\
                    Logic expects using fireball to complete
                    indoor lamps without climb.
                    Grants logical access to all climb-locked
                    areas.
                    '''
    },
    'Glimmer Indoor Lamps with Superfly': {
        'name'    : 'logic_indoor_lamps_superfly',
        'tags'    : ("Powerup", "Glimmer",),
        'tooltip' : '''\
                    Logic expects using the superfly powerup
                    to complete indoor lamps without climb.
                    Grants logical access to all climb-locked
                    areas.
                    '''
    },
    'Aquaria Towers First Tunnel with Double Jump': {
        'name'    : 'logic_at_first_tunnel_double_jump',
        'tags'    : ("Double Jump", "Aquaria Towers",),
        'tooltip' : '''\
                    Logic expects using double jump to get gems
                    in the first tunnel without swim.
                    '''
    },
    'Aquaria Towers Talisman Area with Double Jump': {
        'name'    : 'logic_at_talisman_area_double_jump',
        'tags'    : ("Double Jump", "Aquaria Towers",),
        'tooltip' : '''\
                    Logic expects using double jump to get gems
                    near the talisman. You cannot get the talisman
                    this way.
                    '''
    },
    'Aquaria Towers Sheep Proxy': {
        'name'    : 'logic_at_sheep_proxy',
        'tags'    : ("Proxy", "Aquaria Towers",),
        'tooltip' : '''\
                    Logic expects using sheep proxy to reach the
                    final button, granting access to the talisman
                    and many areas without swim.
                    '''
    },
    'Aquaria Towers Third Button with Fireball': {
        'name'    : 'logic_at_button_three_fireball',
        'tags'    : ("Aquaria Towers",),
        'tooltip' : '''\
                    Logic expects using swim and fireball
                    to hit the final button through the wall.
                    Skips needing the submarine.
                    '''
    },
    'Aquaria Towers Royal Children Out of Bounds': {
        'name'    : 'logic_at_royal_children_oob',
        'tags'    : ("Aquaria Towers",),
        'tooltip' : '''\
                    Logic expects going out of bounds
                    to rescue the final seahorse without
                    access to the full level.
                    Only matters with sheep proxy on.
                    '''
    },
    'Aquaria Towers Gems Out of Bounds': {
        'name'    : 'logic_at_gems_oob',
        'tags'    : ("Aquaria Towers",),
        'tooltip' : '''\
                    Logic expects going out of bounds
                    from the upper area to collect gems.
                    May require the player softlock
                    and re-enter the level.
                    '''
    },
    'Crystal Glacier Skip Bridge with Double Jump': {
        'name'    : 'logic_crystal_bridge_double_jump',
        'tags'    : ("Double Jump", "Crystal Glacier",),
        'tooltip' : '''\
                    Logic expects using a double jump or sproder
                    to skip the Moneybags bridge.
                    '''
    },
    'Crystal Glacier Skip Bridge with Snowball Proxy': {
        'name'    : 'logic_crystal_bridge_snowball_proxy',
        'tags'    : ("Proxy", "Crystal Glacier",),
        'tooltip' : '''\
                    Logic expects using a snowball proxy
                    to skip the Moneybags bridge.
                    '''
    },
    'Zephyr Skip Ladder with Double Jump': {
        'name'    : 'logic_zephyr_ladder_double_jump',
        'tags'    : ("Double Jump", "Zephyr",),
        'tooltip' : '''\
                    Logic expects using a double jump
                    to skip the ladder by the cowlek pen.
                    '''
    },
}

normalized_name_tricks = {trick.casefold(): info for (trick, info) in known_logic_tricks.items()}
