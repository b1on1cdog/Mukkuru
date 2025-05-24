# Mukkuru
-----------------
Cross-Platform customizable game launcher written in Python, optimized for GamePads.<br/>
This is still in early stages and is not yet suitable for final use.<br/>

# Current features
- Switch-like theme<br/>
- Dark mode<br/>
- Scan games from Steam Library<br/>
- Automatically download boxarts from SteamGridDB (when available)<br/>
- Linux and Windows Support<br/>
- Strict static analysis compliance<br/>

# Planed features (To-do list)
- Add joystick buttons<br/>
- Allow user to use his own SteamGrid api key <br/>
- Add scanning animation <br/>
- Order recent played items in main screen<br/>
- Switch-Like contextual menus (when pressing options and some footer items) <br/>
- Allow to add games as favorite <br/>
- Cache screens for faster loading times<br/>
- CSS Loader<br/>
- Chosing custom themes from settings<br/>
- Plugin support, with a plugin storefront<br/>
- MacOS support<br/>
- User friendly installer<br/>

# Changelog
-----------------
# 0.2.8

# 0.2.7
- Renamed 'backend.py' to 'mukkuru.py', webview is now launched from backend and not viceversa <br/>
- Optional experimental pywebview file, as an alternative to pyside6<br/>
- Solved last W0603 violation <br/>
- Fullscreen now works without rebooting app <br/>
- Noticeable webview code refactoring <br/>
# 0.2.6
- More robust Windows Steam Path detection<br/>
- Store button now opens Steam storefront in bigpicture mode <br/>
- Added ethernet icon if device does not use wireless <br/>
- Battery icon now reacts to device battery percentage <br/>
- Battery icon is now not visible if device has no battery <br/>
# 0.2.5
- Using a private api instead of SteamGridDB one, to prevent API key misuse<br/>
- Added vanish effect when entering all-software menu <br/>
- Added sound effect when pressing all-software button <br/>
# 0.2.4
- Expanded exclusions <br/>
- Fixed crash when searching a game title <br/>
# 0.2.3
- Disabled resource logs <br/>
- Fixed bug that made non-steam games artwork fetching fail<br/>
- Last played game will now be first one in homescreen <br/>
- Corrected Crash when a game title didn't match <br/>
- Changed storage calculation dir from / to /home in Linux <br/>
- Steam Deck GPU is now abbreviated <br/>
# 0.2.2
- Fixed crash when some directories didn't exists<br/>
- Improved game artwork fetching accuracy<br/>
- If an artwork is duplicated, the one that does not exactly match game title will be removed<br/>
# 0.2.1
- Fixed items in applist overlapping keyGuide<br/>
- Fixed extraneous gap between apps in smaller resolutions<br/>
- Fixed applist names being cut<br/>
# 0.2.0
- All-software menu apps now have visible title<br/>
- All-software menu apps are now launchable<br/>
- All-software button now has visible title<br/>
- Fixed variable mismatch that made apps not to launch<br/>
# 0.1.9
- Added all-software menu<br/>
- Footer is now fixed to screen<br/>
- Fluent scrolling effect (all-software menu)<br/>
# 0.1.8
- Language can now be switched from Settings<br/>
- Localization now does not require app restart<br/>
- Improved localization logic<br/>
- Fixed issue where 12-Hour suffix was not added if minutes were under 10<br/>
# 0.1.7
- Added localization<br/>
- Rendering is now temporarily locked until everything is ready to display<br/>
- Fix time bug at 12:00AM in 12-Hour time<br/>
# 0.1.6
- Added 12-Hour time<br/>
- App version now only needs to be changed in a single place<br/>
- Added Fullscreen toggle<br/>
# 0.1.5
- Added option to scan for games at Mukkuru startup<br/>
- Game library can now be accesed during a scan<br/>
- Huge Backend code re-structuration (Addresing W0603, E0602, C0301, C0303)<br/>
- Added Backwards config.json compatibility<br/>
- Added a timeout of 20 seconds to network requests (W3101)<br/>
# 0.1.4
- Removed context menu<br/>
- Added fluent transitions <br/>
- Settings code re-structuration<br/>
- Fixed game library race condition<br/>
# 0.1.3
- Dark mode can now be toggled from settings<br/>
- Dark mode now applies to settings<br/>
- Added "about" tab, it will show system information<br/>
- Solved FOUC during page transitions <br/>
# 0.1.2
- Implemented dark mode<br/>
- Fixed bug that broke game launching in Windows<br/>
- Fixed sounds were not playing at app launch<br/>
- Fixed small lines in launcher borders<br/>
# 0.1.1
- Changed mukkuru config folder<br/>
- Added SteamGridDB API, boxarts are now downloaded automatically (when available)<br/>
- Solved multiple bugs<br/>
- Added exclusion array to hide Proton, Steamworks and Linux runtime from showing as games<br/>

# Donations
---------------
I do not actively ask for donations, however, donations could help me spending more time in these projects<br/>
USDT TRC20: TNkFKTZocgB7DssLa3c8SfqqAEGB2hpj8j<br/>
BTC: 19eWbB2YCUxfX2mLAkwWrPnMGLU42Jwabo<br/>