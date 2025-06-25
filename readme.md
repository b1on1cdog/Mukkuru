# Mukkuru
-----------------
Cross-Platform customizable game launcher written in Python, optimized for GamePads.<br/>
This is still in early stages and is not yet suitable for final use.<br/>

# License
Mukkuru is [licensed under MIT](LICENSE)<br/>
See [third-party.md](docs/third-party.md) for third-party files license terms.<br/>

# Current features
- SW, SW2, PS5 like themes<br/>
- Import custom user themes<br/>
- Dark mode<br/>
- Scan games from Steam Library<br/>
- Scan games from Epic Games Library and Heroic<br/>
- Automatically download boxarts from SteamGridDB<br/>
- Linux, Windows and MacOS Support<br/>
- Strict static analysis compliance<br/>
- Plug and play compile environment<br/>

# Release scope
Release static builds with priority support:<br/>
- Windows x86_64<br/>
- Linux x86_64<br/>
- MacOS ARM64<br/>
Architectures not listed might need to run the source code directly and might require modifications.</br>
Some others are going to receive occasional uploads</br>

# Changelog
[Read changelog.md](docs/changelog.md)

# To-do list
- Switch-Like contextual menus (when pressing options and some footer items)<br/>
- Add ability to download games</br>
- Add joystick buttons customization<br/>
- Add scanning animation <br/>
- Order recent played items in main screen<br/>
- Allow to add games as favorite <br/>
- Additional webui to manipulate Mukkuru config from another device <br/>
    - Drag and drop wallpaper change <br/>
    - Drag and drop video playback <br/>
    - Menu to organize games, mark as favorite, blacklist, etc <br/>
    - Option to setup SteamGridDB api <br/>
    - Must also support plugins <br/>
    - Must use chunk splitting to prevent browser upload filesize limit <br/>
    - (Optional) chunk checksum validation to prevent file corruption in upload <br/>
- Plugin support, with a plugin storefront<br/>
    - The first plugin might be one to patch VNs<br/>
- Game provider install helper (Steam, Heroic, etc)<br/>
- Support for linux box86 in arm64<br/>
- User friendly installer<br/>

# Known issues
- A too big window might cause keyguide to display incorrectly in app launcher<br/>

# Contribution guidelines
- **Linting** Use pylint and remove as many warnings as reasonably possible before submitting your code. <br/>
- **Nuitka Compatibility** Ensure your changes do **not break Nuitka compilation** as some users rely in static builds. <br/>
- **Dependencies** Avoid introducing new dependencies unless absolutely necessary. <br/>
- **Licensing** Do **not include GPL, LGPL** or any other restrictive licensed code. <br/>
- **Cross-Platform Code** Avoid using platform-specific code outside its target (ex: running MacOS code without a Darwin platform check). <br/>

# Donations
---------------
Donations could help me spending more time in these projects<br/>
USDT TRC20: TNkFKTZocgB7DssLa3c8SfqqAEGB2hpj8j<br/>
BTC: 19eWbB2YCUxfX2mLAkwWrPnMGLU42Jwabo<br/>