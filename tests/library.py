'''Run mukkuru tests'''

from library.steam import get_non_steam_games, get_steam_games, get_steam_env

def test_scan(options):
    '''
    Scan library for games
    1 - Steam
    2 - Non-Steam
    4 - EGS
    '''
    option_steam = 1 << 0  # 0001 = 1
    option_nonsteam = 1 << 1  # 0010 = 2
    option_egs = 1 << 2  # 0100 = 4

    steam = get_steam_env()

    games = {}
    if options & option_steam:
        steam_games = get_steam_games(steam)
        games.update(steam_games)
    # Scan Non-Steam games
    if options & option_nonsteam:
        non_steam_games = get_non_steam_games(steam)
        games.update(non_steam_games)
    if options & option_egs:
        #egs_games = get_egs_games()
        egs_games = {}
        games.update(egs_games)
    print(games)
