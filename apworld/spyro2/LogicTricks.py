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
                    Logic expects using swim in air in
                    Summer Forest to bypass climbing the
                    ladder, to access gems inside the
                    Aquaria Towers wall, and to enter
                    Ocean Speedway and Aquaria Towers.
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
    'Autumn Plains Double Jumps from Zephyr': {
        'name'    : 'logic_ap_zephyr_double_jump',
        'tags'    : ("Double Jump", "Autumn Plains",),
        'tooltip' : '''\
                    Logic expects using the double jump ability
                    from the Zephyr portal to reach the outer
                    wall and the gems by Metro Speedway. Metro
                    Speedway level access always requires talking
                    to Elora.
                    '''
    },
    'Autumn Plains Climb Skip': {
        'name'    : 'logic_ap_climb_skip',
        'tags'    : ("Double Jump", "Autumn Plains",),
        'tooltip' : '''\
                    Logic expects using the double jump ability
                    on terrain in Autumn Plains to skip climb.
                    This grants access to both sides of the
                    Professor's door in the castle.
                    '''
    },
    'Autumn Plains Skip Professor\'s Door': {
        'name'    : 'logic_ap_door_skip',
        'tags'    : ("Double Jump", "Autumn Plains",),
        'tooltip' : '''\
                    Logic expects using the double jump ability
                    to pass the Professor's door in the castle.
                    This normally requires 8 orbs.
                    If Climb Skip is enabled, this option is ignored.
                    '''
    },
    'Crystal Glacier Skip Bridge with Double Jump': {
        'name'    : 'logic_crystal_bridge_double_jump',
        'tags'    : ("Double Jump", "Crystal Glacier",),
        'tooltip' : '''\
                    Logic expects using a double jump
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
    'Winter Tundra Inside Castle with Double Jump': {
        'name'    : 'logic_wt_castle_double_jump',
        'tags'    : ("Double Jump", "Winter Tundra",),
        'tooltip' : '''\
                    Logic expects using a double jump
                    to skip the headbash lock in Winter
                    Tundra.
                    '''
    },
    'Winter Tundra Inside Castle with Penguin Proxy': {
        'name'    : 'logic_wt_castle_penguin_proxy',
        'tags'    : ("Proxy", "Winter Tundra",),
        'tooltip' : '''\
                    Logic expects using a proxy on the
                    penguin fodder to skip the headbash
                    lock in Winter Tundra.
                    '''
    },
    'Winter Tundra Out of Bounds with Double Jump': {
        'name'    : 'logic_wt_oob_double_jump',
        'tags'    : ("Double Jump", "Winter Tundra",),
        'tooltip' : '''\
                    Logic expects using double jump
                    from the top of the stairs to get
                    out of bounds.
                    Grants access to the waterfall orb without
                    swim, and to other levels with additional
                    tricks.
                    '''
    },
    'Winter Tundra Out of Bounds with Nothing': {
        'name'    : 'logic_wt_oob_nothing',
        'tags'    : ("Winter Tundra",),
        'tooltip' : '''\
                    Logic expects using a careful glide
                    from the top of the stairs to get
                    out of bounds.
                    Grants access to the waterfall orb without
                    swim, and to other levels with additional
                    tricks.
                    '''
    },
    'Winter Tundra Swim from Out of Bounds': {
        'name'    : 'logic_wt_swim_from_oob',
        'tags'    : ("Winter Tundra",),
        'tooltip' : '''\
                    Logic expects using an out of bounds swim
                    to enter all available Winter Tundra
                    levels, if they are not locked by a key.
                    Requires one of the tricks to get out of
                    bounds.
                    '''
    },
    'Winter Tundra Glide into Levels from Out of Bounds': {
        'name'    : 'logic_wt_glide_from_oob',
        'tags'    : ("Winter Tundra",),
        'tooltip' : '''\
                    Logic expects using an out of bounds glide
                    to enter Dragon Shores, Metropolis, Canyon
                    Speedway, and Cloud Temples, if the level
                    is not locked by a key.
                    Requires one of the tricks to get out of
                    bounds.
                    '''
    },
    'Metropolis Ox Orb without Climb': {
        'name'    : 'logic_metropolis_ox_superfly',
        'tags'    : ("Metropolis",),
        'tooltip' : '''\
                    Logic expects using superfly and breaking
                    the height cap to reach the ox area without
                    climb. This uses double jump inputs but is
                    possible without double jump unlocked.
                    '''
    },

}

normalized_name_tricks = {trick.casefold(): info for (trick, info) in known_logic_tricks.items()}
