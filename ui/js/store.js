// Copyright (c) 2025 b1on1cdog
// Licensed under the MIT License

const patchesURL = "/repos/patches"
const packagesURL = "/repos/packages"

async function getInstalledGameIds(){
    response = await fetch("/library/get");
    games = await response.json();
    return Object.keys(games);
}

async function installPatch(appId, patchIndex){
    console.log("User asked to install patch")
    await fetch(`${patchesURL}/${appId}/${patchIndex}`, {
        method : "POST"
    });
    startProgressBar().then( () => {
        fetchPatches();
    });
}

async function fetchPackages(){
    packages_response = await fetch(packagesURL);
    packages = await packages_response.json();
    packages = packages[0]
    const packagesMenu = document.getElementById("options-0");
    while (packagesMenu.firstChild) {
        packagesMenu.firstChild.remove();
    }
    let packagesCount = 0;
    
    const firstSeparator = document.createElement("div");
    firstSeparator.classList.add("option-separator");
    packagesMenu.appendChild(firstSeparator);
    
    const reinstallingStr = translate_str("reinstalling...", "reinstalling...")
    const installingStr = translate_str("installing...", "installing...")
    const installStr = translate_str("install", "install");
    const installedStr = translate_str("installed", "installed");
    const noItemToListStr = translate_str("NoItemsToList", "No items to list");

    if (packagesCount == 0) {
        const emptyElement = document.createElement("div");
        emptyElement.classList.add("menu-option");
        emptyElement.classList.add("store-item");
        emptyElement.innerText = noItemToListStr;
        packagesMenu.appendChild(emptyElement);
        const finalSeparator = document.createElement("div");
        finalSeparator.classList.add("option-separator");
        packagesMenu.appendChild(finalSeparator);
    }

    const spacer = document.createElement('div');
    spacer.style.minHeight = "150px";
    patchesMenu.appendChild(spacer);
    refreshOptions();
}

async function fetchPatches(){
    patches_rp = await fetch(patchesURL);
    patches = await patches_rp.json();
    game_ids = await getInstalledGameIds();
    patches = patches[0]
    patchesMenu = document.getElementById("options-1");
    while (patchesMenu.firstChild) {
        patchesMenu.firstChild.remove();
    }
    let patchCount = 0;

    const firstSeparator = document.createElement("div");
    firstSeparator.classList.add("option-separator");
    patchesMenu.appendChild(firstSeparator);
    const reinstallingStr = translate_str("reinstalling...", "reinstalling...")
    const installingStr = translate_str("installing...", "installing...")
    const installStr = translate_str("install", "install");
    const installedStr = translate_str("installed", "installed");
    const noItemToListStr = translate_str("NoItemsToList", "No items to list");

    for (const [key, value] of Object.entries(patches)) {
        const AppID = key
        if (!game_ids.includes(AppID)) {
            continue;
        }
        value.forEach((patch, index) => {
            const PatchIndex = index;
            box_img = './thumbnails/'+AppID+'.jpg';
            const thumbnail = document.createElement('img')
            thumbnail.src = box_img;
            thumbnail.alt = patch["name"];

            mb_filesize = Math.round(patch["filesize"] /(1024*1024) , 2);

            const patchInstalled = patch["installed"];

            const patchElement = document.createElement("div");
            patchElement.classList.add("menu-option");
            patchElement.classList.add("store-item");
            patchElement.innerText = patch["name"];
            patchElement.id = patch["id"];
            patchElement.dataset.appid = AppID;
            patchElement.dataset.index = PatchIndex;
            patchElement.addEventListener("click", function(){

                const installText = patchInstalled?reinstallingStr:installingStr;
                patchElement.getElementsByClassName("left-label")[0].innerText = installText;
                installPatch(AppID, PatchIndex);
            });
            patchElement.appendChild(thumbnail);

            const leftLabel = document.createElement("span");
            leftLabel.classList.add("left-label");
            leftLabel.innerText = installStr;
            if (patchInstalled) {
                leftLabel.innerText = installedStr;
                leftLabel.style.color = "orange";
            }
            patchElement.appendChild(leftLabel);

            const rightLabel = document.createElement("span");
            rightLabel.classList.add("right-label");
            rightLabel.innerText = mb_filesize + " mb";
            patchElement.appendChild(rightLabel);

            const separator = document.createElement("div");
            separator.classList.add("option-separator");
            
            patchesMenu.appendChild(patchElement);
            patchesMenu.appendChild(separator);
            patchCount++;
        });
    }
    if (patchCount == 0) {
        const emptyElement = document.createElement("div");
        emptyElement.classList.add("menu-option");
        emptyElement.classList.add("store-item");
        emptyElement.innerText = noItemToListStr;
        patchesMenu.appendChild(emptyElement);
        const finalSeparator = document.createElement("div");
        finalSeparator.classList.add("option-separator");
        patchesMenu.appendChild(finalSeparator);
    }
    const spacer = document.createElement('div');
    spacer.style.minHeight = "150px";
    patchesMenu.appendChild(spacer);
    refreshOptions();
}

