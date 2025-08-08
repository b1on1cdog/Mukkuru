# Mukkuru
-----------------
Cross-Platform customizable game launcher written in Python, optimized for GamePads.<br/>
> [!IMPORTANT]
> Mukkuru is still at early stages; some features might have bugs and/or security flaws, use at your own discretion.<br/>
# License
Mukkuru is [licensed under MIT](LICENSE)<br/>
See [third-party.md](docs/third-party.md) for third-party files license terms.<br/>

# Current features
- Linux, Windows and MacOS Support<br/>
- 3 Built-in themes similar to popular consoles<br/>
- Under 30mb executable<br/>
- Import custom user themes<br/>
- Import custom ui sound effects<br/>
- Dark mode and light mode<br/>
- Support fetching game library from:<br>
    - Steam launcher<br/>
    - (Linux) Heroic launcher<br/>
    - (Windows) Epic Games Launcher <br/>
    - (MacOS) Steam launcher under Crossover<br/>
    - (MacOS) Epic Games Launcher under CrossOver<br/>
- Skip duplicated games<br/>
- Update to latest version from app settings<br/>
- WebUI to transfer files from another device<br/>
- Video playback and take video screenshots with a single button<br/>
- Automatically download boxarts from SteamGridDB<br/>
- Multi-language (currently only English and Spanish) <br/>
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
- Add button to transfer mukkuru media to user folders<br/>
- Add button to delete all video thumbnails<br/>
- Add support for non-flatpak Heroic and MacOS Heroic<br/>
- More webui features:<br/>
    - Videoplayback control<br/>
    - Play Mukkuru videos from webui<br/>
    - Wallpaper change<br/>
    - Menu to organize games, mark as favorite, blacklist, etc<br/>
    - Upload game boxart<br/>
    - Option to setup SteamGridDB api<br/>
    - Must also support plugins<br/>
    - (Optional) chunk checksum validation to prevent file corruption in upload<br/>
- Game provider install helper (Steam, Heroic, etc)<br/>
- Add joystick buttons customization<br/>
- Add ability to download games</br>
- Implement SQLite instead of JSON<br/>
- Support for linux box86 in arm64<br/>
- Add support for freebsd<br/>

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
