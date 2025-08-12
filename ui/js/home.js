// Copyright (c) 2025 b1on1cdog
// Licensed under the MIT License

let currentIndex = 0;
let currentRow = 1;
let isUserGestureRequired = false;
let lastFocused = null;

function userGestureNoLongerRequired() {
  if (isUserGestureRequired) {
    isUserGestureRequired = false;
    localStorage.setItem("userGestureRequired", "false");
    if (!lockControls){
      document.getElementById('overlay').style.display = 'none';
    }
    overlayMessage = document.getElementById('overlay-message');
    overlayMessage.innerText = overlayMessage.dataset.original;
  }
}

function setGameProperty(property, value, value2 = undefined){
    switch (property) {
      case "favorite":
        if (userConfiguration.favorite.includes(value)){
          const index = userConfiguration.favorite.indexOf(value);
          userConfiguration.favorite.splice(index, 1);
        } else {
          userConfiguration.favorite.push(value);
        }
        break;
      case "proton":
        protonConfig = userConfiguration["protonConfig"];
        protonConfig[value] = value2;
        userConfiguration["protonConfig"] = protonConfig;
        break;
      case "blacklist":
        if (userConfiguration.blacklist.includes(value)){
          const index = userConfiguration.blacklist.indexOf(value);
          userConfiguration.blacklist.splice(index, 1);
        } else {
          userConfiguration.blacklist.push(value);
        }
        break;
      case "archived":
        archiveGame(value);
        return;
      case "lossless_scaling":
          if (userConfiguration.losslessScaling.includes(value)){
            const index = userConfiguration.losslessScaling.indexOf(value);
            userConfiguration.losslessScaling.splice(index, 1);
            toggleLosslessScaling(value, false);
          } else {
            userConfiguration.losslessScaling.push(value);
            toggleLosslessScaling(value, true);
          }
        break;
      default:
        return;
    }

    fetch("/config/set", {
      method: "POST",
      body: JSON.stringify(userConfiguration),
      headers: {
        "Content-type": "application/json; charset=UTF-8"
      }
      }).then((response) => {
        
      });
}

function handleElementPress(e) {
  const element = e.currentTarget;
  if (element.classList.contains("gameLauncher")) {
    currentRow = 1;
  } else if (element.classList.contains("appLauncher")) {
    currentRow = 3;
  }
  if (element.dataset.index != undefined){
    currentIndex = parseInt(element.dataset.index);
  }
  return element;
}

async function fetch_games(isConfigReady = undefined) {
    const root = document.documentElement; // This is the <html> element
    const styles = getComputedStyle(root);
    const displayHero = styles.getPropertyValue('--display-hero').trim() == "1";
    const gameList = document.querySelector('.gameList');
    const appList = document.querySelector('.appList');
    const useGlass = styles.getPropertyValue('--use-glass').trim() == "1";
    const allSoftwareThumbnailURL = styles.getPropertyValue('--all-software-thumbnail').trim().slice(1, -1);
    const archives = await fetch_archives();
    response = await fetch("/library/get");
    data = await response.json();

    library_start = performance.now();
    gameArr = Object.entries(data);

    while (gameList.firstChild) {
      gameList.removeChild(gameList.firstChild);
    }
    while (appList.firstChild) {
      appList.removeChild(appList.firstChild);
    }

    const favoriteGames = new Set(userConfiguration.favorite);
    const recentPlayed = new Set(userConfiguration.recentPlayed);

    gameArray = [
        ...gameArr.filter(([key]) => recentPlayed.has(key)),
        ...gameArr.filter(([key]) => favoriteGames.has(key) && !recentPlayed.has(key)),
        ...gameArr.filter(([key, val]) => !recentPlayed.has(key) && !favoriteGames.has(key) && val.Thumbnail === true),
        ...gameArr.filter(([key, val]) => !recentPlayed.has(key) && !favoriteGames.has(key) && val.Thumbnail !== true)
    ];
    
    gamesSkipped = 0;
    gamesAdded = 0;
    if (isConfigReady != undefined) {
      await isConfigReady;
    }

    gameLimit = userConfiguration["maxGamesInHomeScreen"];
    const archivedTag = document.createElement('div');
    archivedTag.className = "archiveTag";
    let gameIndex = -1;
    gameArray.forEach((item) => {
        const AppID = item[0];
        box_src = './thumbnails/'+AppID;

        if (item[1]["Thumbnail"]) {

        } else if (userConfiguration["skipNoArt"] == true){
            gamesSkipped++;
            return;
        } else {
            box_src = "./assets/vector/missing.svg";
        }

        if (userConfiguration["blacklist"].includes(AppID)){
            gamesSkipped++;
            return;
        }
        gameIndex++;
        const itemIndex = gameIndex;

        const button = document.createElement('button');
        button.className = 'gameLauncher';
        button.id = AppID;
        button.dataset.gameid = AppID;
        button.dataset.source = item[1]["Source"];
        button.dataset.knowndir = "InstallDir" in item[1];
        button.dataset.index = itemIndex;
        let proton = false;
        if ("Proton" in item[1] && item[1]["Proton"] == true ) {
            proton = true;
        }
        button.dataset.proton = proton;

        const title = document.createElement('div');
        title.className = 'gameLauncher-title';
        title.textContent = item[1]["AppName"];
        title.dataset.text = title.textContent;

        const thumbnail = document.createElement('img');
        thumbnail.className = 'gameLauncher-thumbnail';
        thumbnail.src = box_src;
        thumbnail.alt = item[1]["AppName"];

        button.appendChild(title);
        button.appendChild(thumbnail);
        if (useGlass) {
            const glass = document.createElement('div');
            glass.className = 'glass-effect';
            button.appendChild(glass);
        }
        if (gameLimit > gamesAdded){
            gameList.appendChild(button);
            gamesAdded++;
        }

        if (favoriteGames.has(AppID)){
            button.classList.add("favorite");
        }
        if (archives[AppID] != undefined) {
          button.classList.add("archived");
          button.appendChild(archivedTag.cloneNode(true));
        }

        const app = button.cloneNode(true);
        app.className = app.className.replace('gameLauncher','appLauncher');
        app.id = "app_" + AppID;
        Array.from(app.children).forEach((item) => {
          item.className = item.className.replace("gameLauncher", "appLauncher");
        });
        appList.appendChild(app);

        let timer = null;
        let fired = false;
        const holdDuration = 800;
        touchStartHandler = () => {
          timer = setTimeout(() => {
            fired = true;
            console.log("Hold press registered");
          }, holdDuration);
        };
        touchEndHandler = e => {
          clearTimeout(timer);
          if (fired){
            fired = false;
            //handle long press
            handleElementPress(e);
            document.dispatchEvent(new KeyboardEvent("keydown", {key:"Shift", code:"ShiftLeft", bubbles:true}));
            return;
          }
          //handle short press
          element.click();
          return;
        }
        touchCancelHandler = () => {
          fired = false;
          clearTimeout(timer);
        }
        const contextHandler = e => {
          handleElementPress(e);
          document.dispatchEvent(new KeyboardEvent("keydown", {key:"Shift", code:"ShiftLeft", bubbles:true}));
        }
        const clickHandler = e => {
          console.log("Click event received");
          handleElementPress(e);
          document.dispatchEvent(new KeyboardEvent("keydown", {key:"Enter", code:"Enter", bubbles:true}));
        }
        app.addEventListener('touchstart', touchStartHandler);
        app.addEventListener('touchend', touchEndHandler);
        app.addEventListener('touchcancel', touchCancelHandler);
        app.addEventListener('click', clickHandler);
        app.addEventListener('contextmenu', contextHandler);
        button.addEventListener('touchstart', touchStartHandler);
        button.addEventListener('touchend', touchEndHandler);
        button.addEventListener('touchcancel', touchCancelHandler);
        button.addEventListener('click', clickHandler)
        button.addEventListener('contextmenu', contextHandler);
    });

    if (gamesAdded >= gameLimit) {
        backend_log("Game limit exceeded, creating all-software button");
        const moreButton = document.createElement('button');
        moreButton.className = 'gameLauncher';
        moreButton.id = "allSoftware";

        const thumbnail = document.createElement('img');
        thumbnail.className = 'gameLauncher-thumbnail';

        if (allSoftwareThumbnailURL != "") {
            thumbnail.src = allSoftwareThumbnailURL;
        } else {
            thumbnail.src = "assets/img/all-software.png";
        }

        const title = document.createElement('div');
        title.className = 'gameLauncher-title';
        title.id = "allSoftware-title";
        title.textContent = "All Software";
        title.dataset.trm = "swapText";
        title.dataset.loc = "AllSoftware";
        title.dataset.text = title.textContent;
        moreButton.appendChild(title);
        moreButton.appendChild(thumbnail);
        gameList.appendChild(moreButton);
    }
    
    gameLaunchers = document.querySelectorAll('.gameLauncher');
    appLaunchers = document.querySelectorAll('.appLauncher');

    document.querySelectorAll('.gameLauncher-placeholder').forEach(e => e.remove());
    
    if (gameLaunchers.length < userConfiguration["maxGamesInHomeScreen"]){
        blocksToAdd = userConfiguration["maxGamesInHomeScreen"] - gameLaunchers.length;
        while (blocksToAdd > 0) {
            blocksToAdd--;
            const block = document.createElement('button');
            block.className = 'gameLauncher-placeholder';
            block.disabled = true;
            gameList.appendChild(block);
        }
    }
    
    const spacer = document.createElement('div');
    spacer.style.minWidth = "300px";
    gameList.appendChild(spacer);

    appLaunchers.forEach(item => {
        item.addEventListener('focus', () => {
            lastFocused = item;
            handleElementPress({ currentTarget: item });
            item.scrollIntoView({ behavior: "instant", block: "center" });
        });
    });

    if (displayHero) {
        bg = document.getElementById("bg");
        bg.style.backgroundRepeat = "no-repeat";
        bg.style.backgroundSize = "cover";
        bg.style.backgroundPosition = "center";
        homeMenu.style.backgroundColor = "none";
    }

    gameLaunchers.forEach(item => {
        item.addEventListener('focus', () => {
            lastFocused = item;
            handleElementPress({ currentTarget: item });
            item.scrollIntoView({ behavior: "instant", block: "center", inline: "center" });
            if (displayHero) {//start displayHero
              if (item.id == "allSoftware") {
                bg.style.backgroundImage = "none";
              } else {
                bg.style.backgroundImage = "url('hero/" + item.id+ "')";
              }
            }//end displayHero
        });
    });
    measure_time("library loading time", library_start)
}

function contextDismissal(e){
  if (isContextMenu) {
    ctxMenu = document.getElementsByClassName("contextualMenu active")[0];
    if (!ctxMenu.contains(e.target)) {
      console.log("Dismissing context menu...");
      close_context_menu();
    }
    if (lastFocused != null) {
      lastFocused.focus();
    }
  }
}