# Mukkuru
-----------------
Cross-Platform customizable game launcher written in Python, optimized for GamePads.<br/>
This is still in early stages and is not yet suitable for final use.<br/>

# License
Mukkuru is [licensed under MIT](license.md)<br/>
See [third-party.md](third-party.md) for third-party files license terms.<br/>

# Current features
- SW, SW2, PS5 like themes<br/>
- Dark mode<br/>
- Scan games from Steam Library<br/>
- Scan games from Epic Games Library<br/>
- Automatically download boxarts from SteamGridDB<br/>
- Linux, Windows and MacOS Support<br/>
- Strict static analysis compliance<br/>

# Release scope
Release static builds with priority support:<br/>
- Windows x86_64<br/>
- Linux x86_64<br/>
- MacOS ARM64<br/>
Architectures not listed might need to run the source code directly and might require modifications.</br>

Release static builds with low priority:<br/>
- MacOS x86_64<br/>
- Linux ARM64<br/>
- Windows ARM64<br/>
These ones will not receive static builds often and might not have full compatibility<br/>

# Changelog
[Read changelog.md](changelog.md)

# To-do list
- Switch-Like contextual menus (when pressing options and some footer items) <br/>
- Add ability to download games</br>
- Add joystick buttons customization<br/>
- Better settings toggle positioning<br/>
- Log to file <br/>
- Allow user to use their own SteamGrid api key to bypass my middle api<br/>
- Add scanning animation <br/>
- Order recent played items in main screen<br/>
- Allow to add games as favorite <br/>
- CSS Loader<br/>
- Chosing custom themes from settings<br/>
- Additional webui to manipulate Mukkuru config from another device <br/>
    - Drag and drop wallpaper change <br/>
    - Drag and drop video playback <br/>
    - Menu to organize games, mark as favorite, blacklist, etc <br/>
    - Must also support plugins <br/>
    - Must use chunk splitting to prevent browser upload filesize limit <br/>
    - (Optional) chunk checksum validation to prevent file corruption in upload <br/>
- Plugin support, with a plugin storefront<br/>
    - The first plugin might be one to patch VNs<br/>
- Heroic Support<br/>
- Game provider install helper (Steam, Heroic, etc)<br/>
- User friendly installer<br/>

# Known issues
- A too small window might cause view issues<br/>
- A too big window might cause keyguide to display incorrectly in app launcher<br/>

# Contribution guidelines
- **Linting** Use pylint and remove as many warnings as reasonably possible before submitting your code. <br/>
- **Nuitka Compatibility** Ensure your changes do **not break Nuitka compilation** as some users rely in static builds. <br/>
- **Dependencies** Avoid introducing new dependencies unless absolutely necessary. <br/>
- **Licensing** Do **not include GPL, LGPL**, or any other restrictive licensed code. <br/>
- **Cross-Platform Code** Avoid using platform-specific code outside its target (ex: running MacOS code without a Darwin platform check). <br/>

# Donations
---------------
Donations could help me spending more time in these projects<br/>
USDT TRC20: TNkFKTZocgB7DssLa3c8SfqqAEGB2hpj8j<br/>
BTC: 19eWbB2YCUxfX2mLAkwWrPnMGLU42Jwabo<br/>