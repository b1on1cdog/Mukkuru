# Changelog
-----------------
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
- SW2 style now applies to applist<br/>
- Improved SW2 selector animation<br/>
- PS5 style now applies to applist<br/>
- PS5 style visibility is improved in light mode<br/>
- [fix] PS5 placeholders are now invisible <br/>
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
- SW2 list style <br/>
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
- Added PS5-like list style <br/>
- Added PS5 Sound effects <br/>
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
