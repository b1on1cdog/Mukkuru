# Changelog
-----------------
# 0.4.0
- Lossless scaling option is now hidden in games from uncompatible sources<br/>
- Some backend functions are now documented using Sphinx markup<br/>
- Added game archiving to compress games to save space<br/>
- Added "Manage all games" option to tamper LaunchOptions in the go<br/>
- This will also allow detecting, stopping, pausing and resuming launched games<br/>
- Improved lossless scaling toggle so it won't break non-steam games<br/>
- Simplified frontend game fetching code<br/>
- Disabling cursor is now decided by user<br/>
- Fixed cursor blinking during during reload<br/>
- Fixed FOUC when using iframe in Dark Mode<br/>
- Fixed pressing options with context menu replayed sound effect<br/>
- Removed "gameLauncher-more"<br/>
- Added support for webp and png thumbnails and hero<br/>
- Added partial support for touchscreen and mouse in homescreen<br/>
- Added a small delay when passing the border with selector loop enabled<br/>
- Tracebacks are now saved in logs<br/>
- Solved crash trying to print message<br/>
- Modified compile.py so it could be re-used in other projects easier<br/>
- Contextual menus are now animated<br/>
- About hwinfo can now be overrided using environment variables<br/>
- Migrated from JSON files to SQLite<br/>
- Video thumbnails are now stored in Mukkuru config folder so video folders are not poluted<br/>
# 0.3.14
- Removed unused assets and compressed some images<br/>
- Replaced Mukkuru icon<br/>
- Solved language not applying until app reboot<br/>
- Parameters are now type hinted<br/>
- Added shutdown and reboot options<br/>
- Added option to skip games with same title<br/>
- Changing Settings tab will now revert scroll position<br/>
- AddToStartup and RemoveFromStartup are now a single setting<br/>
- Added a description to "Add to startup"<br/>
- Added "Add To Startup" support for MacOS and Windows<br/>
- (Windows/Linux) Added "Enable Lossless scaling" option when Lossless Scaling is installed<br/>
- Returning from all-software and media list menu will not reload home anymore<br/>
- Solved accidental configuration update when calling settings functions<br/>
- Improved backend_log, it will now log with more information<br/>
# 0.3.13
- Fixed server port busy prevented terminating old instance in Linux<br/>
- Fixed controls not locked during global progress bar display<br/>
- Fixed unable to return in dashboard file download<br/>
- Localized Mukkuru Store, global progress bar and update messages<br/>
- Fixed global progress bar not appearing after starting patch install<br/>
- Removed kill_process_on_port since is not used anymore<br/>
- (SteamOS only) added option to launch Mukkuru at startup<br/>
- (Linux) Solved Firefox crash message<br/>
# 0.3.12
- JV2 is now default theme<br/>
- "original" is now default ui effect<br/>
- removed "download_steam_avatar" as it was unnecesary and unreliable<br/>
- Mukkuru can now download and install game patches<br/>
- Games can now be refreshed without refreshing whole home screen<br/>
- Update button will now display a prompt with the changelog before updating<br/>
- Updates and downloads will now show a progress bar<br/>
- Mukkuru will now exclude itself from library scan <br/>
- Fixed bad reference to batteryCharging<br/>
- Opening a new instance will terminate previous by HTTP instead of killing by signal<br/>
- Fixed 2 Proton builds not properly excluded from library scan due to missing comma<br/>
- Moved screenshot destination and use all video sources settings from "Advanced" to "Library"<br/>
- JS files moved to a folder<br/>
- Added basic js preprocessor<br/>
# 0.3.11
- Using SGDB api directly when set in user_config<br/>
- Heroic is now its own game source instead of being an epic games failover<br/>
- Unavailable game sources will now be delisted from settings<br/>
- Added return hints for most functions<br/>
- Implemented environment sanitization to prevent bundled libs from breaking subprocess calls<br/>
- Improved settings SOC detection<br/>
- (Linux) Removed flaskwebui dependency and added a check to prevent exception when a browser do not exists<br/>
- (Windows) Solved potential crash when trying to open Mukkuru without Steam installed<br/>
- (MacOS) "darwin" is now also valid for update names<br/>
- (MacOS) Fixed broken updater due to missing .dmg extension<br/>
- (MacOS) Settings/about will now display MacOS version instead of "Darwin"<br/>
- (MacOS) Added Epic Games support under Crossover<br/>
- (MacOS) Added option to open Crossover Steam Store when available<br/>
# 0.3.10
- Disabled Mukkuru Store contextItem since it was not supposed to be in release versions<br/>
- Improved webui dashboard appearance<br>
- Removed .html from urls<br/>
- Added option to download files from webui<br/>
- Added app list to dashboard, you can now request launching your games from another device<br/>
- Replaced upload icon asset<br/>
- 3 last played games will now be listed first<br/>
- Solved crash when a config parent directory did not exists<br/>
- Solved get_proton_list exception when Steam was not installed<br/>
- Remove mukkuru.png from gitignore since is needed for compile<br/>
- If GPU and CPU have same name, CPU/GPU name will be displayed as "SOC"<br/>
- Avatar image will now be fetched from avatar cache before trying from internet<br/>
- Mukkuru will now delete 0 bytes avatar images<br/>
- (MacOS) Fixed DMG creation, also added alias so users can drag app to Applications<br/>
- (MacOS) Compiler will use create-dmg if installed, otherwise hdiutil<br/>
- (MacOS) Added support for system-wide crossover installs<br/>
- (MacOS) the app name inside DMG will be just "Mukkuru" instead of "mukkuru-darwin-arm64"<br/>
- (MacOS) Added app metadata<br/>
- (Linux) Solved failed artwork scan due to interpreter exit<br/>
# 0.3.9
- Display battery percent option is now hidden in devices without battery<br/>
- Removed "interface" config key, as it was never needed in first place<br/>
- Added a context Menu when pressing Store button<br/>
- "AMD64" is now renamed to "x86_64"<br/>
- Settings/About will display arch in app version<br/>
- Added sound when closing context menu<br/>
- Added function to update app from settings/about<br/>
- Trying to open a new instance of Mukkuru will now terminate the old one<br/>
- Improved app starting speed<br/>
- Added button to move files from misc to user downloads <br/>
- Added option to select user pictures as screenshots destination<br/>
- Added option to load videos from user video directory <br/>
# 0.3.8
- Some theme logic was moved to CSS so it can be controlled from user themes<br/>
- Fixed game scrolling title not stopping in JV2 Theme<br/>
- Removed tooltip in top of username<br/>
- It is now possible to load user audio effects<br/>
- MP3 and OGG are now supported audio effects formats<br/>
- Added an extra built-in ui audio effect called "original"<br/>
- Distributed some mukkuru.py functions in other files to prevent too many lines in single file<br/>
- Added screenshots when pressing "options" during video playback<br/>
- Users can now resume video playback after closing video<br/>
- Simplified compile.py, removing unused functions and migrating some logic to src files<br/>
- "BUILD_VERSION" is removed, as it wasn't really relevant to users anyways<br/>
# 0.3.7
- Added option to display battery percent <br/>
- Added small spinning animation when library scan is in progress<br/>
- Thumbnails will now be updated without requiring menu reload<br/>
- Fixed non-flatpak firefox not closing<br/>
- Fixed art blacklist code<br/>
- Solved dashboard undefined text in english<br/>
- Solved overlay not being displayed when using english<br/>
- Fixed third-party.md links<br/>
# 0.3.6
- non-steam games that are not from heroic/lutris can now run<br/>
- added executable metadata for windows build<br/>
- 'onedir' in compile.py will be '--standalone' when using nuitka<br/>
- JV2 Theme item selector now applies to videos, avatar and context Menus<br/>
- Added min size to app icons in AppList<br/>
- Added Steam Crossover support in MacOS<br/>
# 0.3.5
- Implemented own videocontrols<br/>
- Flaskwebgui as default view for Linux<br/>
- Cursor is now hidden<br/>
- Buttons can now unlock view in iframe<br/>
- An overlay message will be shown when user button press is required<br/>
- Battery will show charging icon when device is charging<br/>
- Solved wrong separators being hidden<br/>
- Added option to display software licenses<br/>
# 0.3.4.1
- Added option to delete videos<br/>
- Solved exception when trying to update deleted videos<br/>
- Fixed back keyguide appearing at homescreen start when it should not<br/>
# 0.3.4
- Game context menu is now accesible from applist <br/>
- Added option to select proton version in games that require proton<br/>
- Server dashboard can now be translated<br/>
- Back keyguide button will now appear in appList/videoList<br/>
- removed fixed "backendURL" variable as it was not needed in first place<br/>
- Deleted video files will now reflect in media screen<br/>
- Media menu won't open and will instead show a text message when there's no media to play<br/>
- Fixed typo<br/>
# 0.3.3
- Applied keybindings to settings<br/>
- Power button will now display a context menu, restart app option added<br/>
- Exiting Mukkuru will now show a vanishing effect first<br/>
- UI will be locked with a overlay message when backend is no longer running <br/>
- Moved footer localization to DOM<br/>
- Added server option to transfer media and files<br/>
- Added WIP video player<br/>
# 0.3.2
- Added %command% in launch_app for compatibility<br/>
- Added game image size limit in applist<br/>
- Fixed missing keyGuide<br/>
- Added contextual menus (add games to favorite, show/hide games)<br/>
- Favorite games will now display a small heart in top right<br/>
- WASD and Spacebar can now be used to move in menu<br/>
- Snap bugfix (still untested)<br/>
# 0.3.1
- Small hack to make app work in Steam Deck gaming mode (requires firefox flatpak)<br/>
- Moved hardware info os position, Gamescope will now add (Gaming mode) string to os name<br/>
- More items to exclusions <br/>
# 0.3.0
- Heroic library support in Linux<br/>
- Settings ui overflow fix<br/>
- Added advanced tab in settings<br/>
- compile.py now also supports pyinstaller<br/>
- in hardware info GPU will now be hidden when not detected<br/>
- Failover avatar image<br/>
- fixed battery level indicator <br/>
- game assets download are now multithreaded<br/>
- Games without thumbnail are positioned later (unless favorite)<br/>
# 0.2.18
-Settings items now scroll<br/>
-Settings toggles are now aligned<br/>
-Settings items now handle better scaling<br/>
# 0.2.17
-Added ability to load user themes<br/>
-Frontend changes to allow setting some changes from css<br/>
-Temporal seg_fault linux fix <br/>
-Steam is now optional<br/>
-Linux shorcut path fix</br>
# 0.2.16
- [source] files are now organized in folders<br/>
- [source] get_battery() was moved to hardware_if<br/>
- Added tkinter for basic ui when main ui is not available <br/>
- Replaced PySide6 wef_bundle (to reduce app size, and make ui easily swappable)<br/>
- Updated third-party.md<br/>
- Fixed shortcut parsing bug in Linux<br/>
- First public update<br/>
# 0.2.15
- Added function to list themes<br/>
- [source] Separated hardware/network info functions to a [different file](/utils/hardware_if.py)<br/>
- Some functions results are now cached<br/>
- Core number to use in waitress can now be set from config.json<br/>
- backend_log will now append to a log file<br/>
- Changes to compiler.py, added args --docker, --clean, --wipe and --run<br/>
- Added FlaskUI as an optional view<br/>
- Minor UI Changes<br/>
# 0.2.14
- JV2 style now applies to applist<br/>
- Improved JV2 selector animation<br/>
- BlanceUI style now applies to applist<br/>
- BlanceUI style visibility is improved in light mode<br/>
- [fix] BlanceUI placeholders are now invisible <br/>
- [fix] spacer is now added after placeholders<br/>
- [fix] improved network interface detection <br/>
- [fix] solved MacOS annoying "boop" when navigating in settings <br/>
- [source] enhanced compile.py, now it handles venv and dependencies automatically<br/>
- App now uses a static build version when compiled<br/>
- Now using executable directory instead of working directory <br/>
# 0.2.13
- CSS preprocessor functions are now commented to prevent css code warnings<br/>
- Added MacOS steam support <br/>
- Removed scorer based filename detection (fuzzywuzzy no longer needed) <br/>
- [fix] Required folders are now verified one by one in startup (before only parent dir was checked) <br/>
- Avatar image is now accepted as both .png and .jpg <br/>
- Avatar image will now be copied from Steam cache when API is not available <br/>
- [source] Changelog is now in a separate file [changelog.md](changelog.md) <br/>
- [source] Steam functions are now in a [different module](/utils/steam.py) <br/>
- [source] Added [third-party.md](third-party.md) <br/>
# 0.2.12
- JV2 list style <br/>
- [fix] opening store used to open settings instead <br/>
- [fix] sound effects label off bounds <br/>
- Added WIP CSS Preprocessor <br/>
# 0.2.11
- Renamed default ui <br/>
- Updated SGDB Token <br/>
- Added code to download hero and logo from SteamGridDB<br/>
- Games with missing asset in steamGridDB will now avoid retry in future scans<br/>
- Fixed Settings not hightlighting White when dark mode was disabled<br/>
- Improved navigation logic<br/>
# 0.2.10
- Added BlancheUI theme <br/>
- Added *** Sound effects <br/>
- Solved crash when a translation was not available <br/>
- Added waitress as dependency <br/>
- Improved loading speed <br/>
- Fixed some images failling to load<br/>
- Thumbnails are now loaded from mukkuru config folder <br/>
# 0.2.9
- Avatar image is now downloaded from Steam API<br/>
- Selected theme/library source is now highlighted in a different font color<br/>
- Added Epic games as library source (Windows only)<br/>
- Library sources can now be set from Settings <br/>
- Solved left arrow exception in settings<br/>
- Simplified some code<br/>
# 0.2.8
- Removed some unused debugging logs<br/>
- Minor bugfixes<br/>
- Improved network detection accuracy<br/>
- Numeric options can now be altered from Settings UI<br/>
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
