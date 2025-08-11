// Copyright (c) 2025 b1on1cdog
// Licensed under the MIT License
const audioContext = new (window.AudioContext || window.webkitAudioContext)();
const audioBuffers = {};
const maxPoolSize = 4;
const audioPlayedAt = {};
let userConfiguration = {};
let lockControls = false;
let isVideoPlayer = false;
let currentContext = 0;
let isContextMenu = false;
let currentMedia = 0;
let mediaItems;

const bufferPools = {};

async function loadSound(name, url) {
  try {
    const response = await fetch(url);
    const arrayBuffer = await response.arrayBuffer();
    audioBuffers[name] = await audioContext.decodeAudioData(arrayBuffer);
    audioPlayedAt[name] = 0;
    // Initialize pool for this sound
    bufferPools[name] = [];
  } catch (error) {
    console.error(`Error loading sound ${name}:`, error);
  }
}

async function initSounds() {
  const soundFiles = {
    'tick': './assets/audio/tick',
    'select': './assets/audio/select',
    'home': './assets/audio/home',
    'border': './assets/audio/border',
    'enter-back': './assets/audio/back',
    'run': './assets/audio/run',
    'settings': './assets/audio/settings',
    'shot' : './assets/audio/shot',
  };
  
  await Promise.all(Object.keys(soundFiles).map(name => 
    loadSound(name, soundFiles[name])
  ));
}

initSounds();

function playSound(name) {
  const now = Date.now();
    if (!audioBuffers[name]) {
      console.warn(`Sound "${name}" not loaded`);
      return;
    }
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffers[name];
    source.connect(audioContext.destination);
  
    if (name == "border") {
      if (now - audioPlayedAt[name] > 150) {
          source.start(0);
      }
    } else {
      source.start(0);
    }
  
    audioPlayedAt[name] = Date.now();
  }
  

function sleep (time) {
  return new Promise((resolve) => setTimeout(resolve, time));
}

function blink(element){
  vanish(element);
  setTimeout(unvanish, 300, element, 35);
}

function vanish(element)
{
    var oppArray = ["0.9", "0.8", "0.7", "0.6", "0.5", "0.4", "0.3", "0.2", "0.1", "0"];
    var x = 0;
    (function next() {
        element.style.opacity = oppArray[x];
        if(++x < oppArray.length) {
            setTimeout(next, 20);
        }
    })();
}

function unvanish(element, ms)
{
    var oppArray = ["0.1", "0.2", "0.3","0.4","0.5","0.6","0.7","0.8","0.9","1"];
    var x = 0;
    (function next() {
        element.style.opacity = oppArray[x];
        if(++x < oppArray.length) {
            setTimeout(next, ms);
        }
    })();
}

function returnMainScreen(){
  playSound("enter-back");
  setTimeout(function () {
    currentRow = 1;
    document.getElementsByClassName("mediaList")[0].style.display = "none";
    document.getElementsByClassName("gameList")[0].style.display = "";
    document.getElementsByClassName("homeHeader")[0].style.display = "";
    document.getElementsByClassName("footerNavigation")[0].style.display = "";
    document.getElementsByClassName("appList")[0].style.display = "none";
    currentIndex = 0;
    }, 300);
    blink(document.getElementsByClassName("homeMenu")[0]);
}

function goHome(){
    vanish(document.getElementsByClassName("homeMenu")[0]);
    playSound("home");
        sleep(500).then(() => {
            window.location.replace("/frontend/")
        }); 
}

function booleanTgl(statement){
 return statement?"ON":"OFF";
}

function backend_log(message){
  console.log(message);
  fetch("/log/"+btoa(message)).then(function(response) {
    return response.text();
});
}
function unblockElements(){
  const elements = document.querySelectorAll('.pending');

  elements.forEach(el => {
      el.classList.remove('pending');
  });
}

var docStyle = window.getComputedStyle(document.documentElement);
var lightColor = docStyle.getPropertyValue('--bg-color');  //#EBEBEB
var darkColor = docStyle.getPropertyValue('--main-color'); //#2E2E2E

function applyDarkMode(){
  document.documentElement.style.setProperty("--bg-color", darkColor);
  document.documentElement.style.setProperty("--main-color", lightColor);
  document.documentElement.style.setProperty("--bland-bg","#5E5E5E" );
  console.log("[debug] dark mode enabled");
}

let configReady;

const isConfigReady = new Promise((resolve) => {
  configReady = resolve;
});

let aliveFails = 0;
let protonList = [];

async function fetch_proton_list(){
      const response = await fetch("/library/proton");
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      protonList = await response.json();
}

async function hardwareStatusUpdate(){
      if (aliveFails > 1) {
        return;
      }
      const response = await fetch("/hardware/battery");
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      battery = await response.json();
      if (battery == null) {
          document.getElementsByClassName("batteryState")[0].style.display = "none";
      } else {
          const batteryLevel =  document.getElementsByClassName("batteryLevel")[0];
          const batteryState = document.getElementsByClassName("batteryState")[0];
          const batteryPercent = document.getElementById("batteryPercent");
          const batteryCharging = document.getElementsByClassName("batteryCharging")[0];
          batteryLevel.style.width = "" + (100-battery.percent) + "%";
          batteryPercent.innerHTML = Math.trunc(battery.percent) + '<span class="chargePercent">%</span>';
          if ("power_plugged" in battery && battery.power_plugged) {
            if (!batteryCharging.classList.contains("active")) {
              batteryCharging.classList.add("active");
              batteryState.style.backgroundColor = "rgba(33, 255, 59, 0.82)";
            }
          } else if (batteryCharging.classList.contains("active")) {
              batteryCharging.classList.remove("active");
              batteryState.style.removeProperty("background-color");
          }
      }
      

      const network_resp = await fetch("/hardware/network");
      if (!network_resp.ok) {
        throw new Error(`HTTP ${network_resp.status}`);
      }
      network = await network_resp.json();
      const wifiState = document.getElementsByClassName("wifiState-icon")[0];
      const wifiPath = wifiState.querySelectorAll("path")[0];
      if (!network.internet) {
        backend_log("no network");
        wifiState.style.opacity = "0.4";
      } else if (!network.wifi) {
        wifiState.style.opacity = "1";
        wifiPath.setAttribute("d", "M159.13 136.02l-35.26-29.32L0 256.01 123.86 405.3l35.26-29.29-99.6-119.99 99.61-120zm-17.62 142.89h45.8v-45.8h-45.8v45.8zm228.98-45.8h-45.8v45.8h45.8v-45.8zm-137.39 45.8h45.8v-45.8h-45.8v45.8zM388.11 106.7l-35.26 29.32 99.62 119.99L352.85 376l35.26 29.29L512 256.01 388.11 106.7z")
        wifiState.setAttribute("viewBox", "0 0 500 500");
        wifiState.style.width = "32px";
        wifiState.style.height = "32px";
      } else if (network.wifi) {
        wifiState.style.opacity = "1";
        if (network.signal > 70) {
          wifiPath.setAttribute("d", "M1 9l2 2a12.73 12.73 0 0 1 18 0l2-2A15.57 15.57 0 0 0 1 9zm8 8l3 3 3-3c-1.65-1.66-4.34-1.66-6 0zm-4-4l2 2c2.76-2.76 7.24-2.76 10 0l2-2C15.14 9.14 8.87 9.14 5 13z");
        } else if (network.signal > 40) {
          wifiPath.setAttribute("d", "M 9 17 L 12 20 L 15 17 C 13.35 15.34 10.66 15.34 9 17 Z M 5 13 L 7 15 C 9.76 12.24 14.24 12.24 17 15 L 19 13 C 15.14 9.14 8.87 9.14 5 13 Z");
        } else {
          wifiPath.setAttribute("d", "M 9 17 L 12 20 L 15 17 C 13.35 15.34 10.66 15.34 9 17 Z");
        }

      }

}

function clockUpdate(meridiem){
    const now = new Date();
    const h = document.querySelector('.timeHour');

    let hours = now.getHours();
    let suffix = "";

    if (meridiem && hours > 12) {
      hours = hours - 12;
      suffix = " PM";
    } else if (meridiem) {
      suffix = " AM";
      if (hours == 0) {
        hours = 12;
      }
    }

    h.innerText = hours;
    const m = document.querySelector('.timeMinute');

    if (now.getMinutes() < 10) {
        m.innerText = "0" + now.getMinutes() + suffix;
    } else {
        m.innerText = now.getMinutes() + suffix;
    }
    try {
      hardwareStatusUpdate();
    } catch {

    }
    
  }

function hideUI(state){
  if (state) {
    document.getElementsByClassName("homeBody")[0].classList.add("pending");
    document.getElementsByClassName("homeFooter")[0].classList.add("pending");
  } else {
    document.getElementsByClassName("homeBody")[0].classList.remove("pending");
    document.getElementsByClassName("homeFooter")[0].classList.remove("pending");
  }
}

function closeCTX(){
  isContextMenu = false;
  ctxMenu = document.getElementsByClassName("contextualMenu active")[0];                    
  currentContext = 0;
  selectedContext = ctxMenu.getElementsByClassName("contextItem selected")[0];
  selectedContext.classList.remove("selected");
  firstContext = ctxMenu.getElementsByClassName("contextItem")[0];
  firstContext.classList.add("selected");
  elements = document.getElementsByClassName("contextualMenu active");
  Array.prototype.forEach.call(elements, function(element) {
   element.classList.remove("active");
   });
}

// start video_parser.js
//Mukkuru::Load:media.js
// end video_parser.js

async function reloadGameThumbnails(){
  loadingSpinner = document.getElementById("loadingSpinner");
  backend_log("reloading game thumbnails...");
  if (!loadingSpinner.classList.contains("active")){
    loadingSpinner.classList.add("active");
  }

  const library_response = await fetch("/library/get");
  if (!library_response.ok) {
    throw new Error(`HTTP ${network_resp.status}`);
  }
  game_library = await library_response.json();
  all_games = document.querySelectorAll('.gameLauncher, .appLauncher');
  all_games.forEach((element) => {
  AppID = element.dataset.gameid;
  if (game_library[AppID]["Thumbnail"]){
      thumbnail = element.querySelectorAll('.gameLauncher-thumbnail, .appLauncher-thumbnail')[0];
      thumbnail.src = './thumbnails/'+AppID+'.jpg';
    }
  });
  backend_log("reload done");
}

async function isAlive(){
    if (aliveFails > 1) {
      return;
    }
    try {
      const response = await fetch("/alive");
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
      message = await response.json();

      aliveFails = 0;
      if ( message["command"] != undefined) {
        const command = message["command"];
        const value = message["value"] ?? "";
        switch (command) {
          case "playVideo":
            fetch_videos(value);
            break;
          case "reloadVideos":
            fetch_videos();
            break;
          case "playAudio":
            break;
          case "reloadGameThumbnails":
            reloadGameThumbnails();
            break;
          case "ScanFinished":
            reloadGameThumbnails();
            setTimeout(() => {
              backend_log("scan done, removing loading spinner");
              document.getElementById("loadingSpinner").classList.remove("active");
            }, "2500");
            break;
          default:
            break;
        }
      }
    } catch (exception) {
      aliveFails++;
      document.getElementById('overlay').style.display = 'flex';
      lockControls = true;
      console.log("AliveError: " + exception.message);
  }
}

  function showKeyGuide(state) {
    document.getElementsByClassName("homeFooter")[0].style.display = state?"flex":"none";
  }
  function showBottomBar(state) {
    document.getElementsByClassName("footerNavigation")[0].style.display = state?"flex":"none";
  }

  async function toggleLosslessScaling(app_id, state = true){
    await fetch("/library/lossless_scaling/"+app_id, { method: state?"POST":"DELETE" });
  }

  async function archiveGame(app_id){
    startProgressBar(true);
    await fetch("/library/archive/"+app_id, { method: "POST"});
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

const isFirefox = typeof navigator !== 'undefined' && /firefox/i.test(navigator.userAgent);
const isKioskMode = typeof navigator !== 'undefined' && /kioskMode/i.test(navigator.userAgent);

const keyBindings = {
  "Enter": "confirm",
  " ": "confirm",
  "Escape": "back",
  "Backspace" : "back",
  "Shift" : "options",
  "ArrowLeft" : "left",
  "ArrowRight" : "right",
  "ArrowUp" : "up",
  "ArrowDown" : "down",
  "w" : "up",
  "s" : "down",
  "a" : "left",
  "d" : "right"
};

async function updateConfiguration() {
  response = await fetch("/config/set", {
    method: "POST",
    body: JSON.stringify(userConfiguration),
    headers: {
    "Content-type": "application/json; charset=UTF-8"
      }
    });
}

function restartMukkuru(){
  fetch("/app/restart").then(function(response) {
    return 0;
  });
  homeMenu = document.getElementsByClassName("homeMenu")[0];
  vanish(homeMenu);
}

async function shutdownDevice(reboot = false) {
    url = "/app/shutdown"
    if (reboot) {
      url = "/app/reboot"
    }
    await fetch(url, {
      method: "POST"
    });
}

async function refreshServer(){
    res = await fetch("/server/info");
    sOption = document.getElementById("sOption");
    sOption.innerText = await res.text();
    if (res.status == "200") {
        document.getElementById("dashboardQR").style.display = "";
        return true;
    } else {
        document.getElementById("dashboardQR").style.display = "none";
    }
    return false;
}

async function serverHandle(action){
   if (action == "auto") {
    state = await refreshServer();
    if (state) {
      return serverHandle("close");
    } else {
      return serverHandle("start");
    }
   }
   response = await fetch("/server/"+action, {method: "POST"});
   return await refreshServer();
}

function exitMukkuru(){
  localStorage.clear();
  fetch("/app/exit").then(function(response) {
    return 0;
  });
  homeMenu = document.getElementsByClassName("homeMenu")[0];
  vanish(homeMenu);
}


function handleAutoPlay(action = "update"){
  apOption = document.getElementById("autoPlayOption");
  apState = userConfiguration["autoPlayMedia"];
  switch (action) {
    case "auto":
      handleAutoPlay(apState?"false":"true");
      break;
    case "true":
      userConfiguration["autoPlayMedia"] = true;
      updateConfiguration();
      handleAutoPlay("update");
      break;
    case "false":
      userConfiguration["autoPlayMedia"] = false;
      updateConfiguration();
      handleAutoPlay("update");
      break;
    default://update or anything else
      apOption.innerText = apState?apOption.dataset.on:apOption.dataset.off;
      break
  }
}

function mediaControl(action) {
  prevMedia = currentMedia;
  switch (action) {
    case "up":
      currentMedia = Math.max(currentMedia-4, 0);
      break;
    case "down":
      currentMedia = Math.min(currentMedia+4, mediaItems.length-1);
      break;
    case "left":
      currentMedia = Math.max(currentMedia-1, 0);
      break;
    case "right":
      currentMedia = Math.min(currentMedia+1, mediaItems.length-1);
      break;
    case "back":
      //goHome();
      returnMainScreen();
      break;
    case "options":
      document.getElementById("videoContextMenu").classList.add("active");
      isContextMenu = true;
      return;
    case "confirm":
      switch (mediaItems[currentMedia].className){
        case "videoLauncher":
          const resume = ("resume" in mediaItems[currentMedia].dataset);
          if (resume) {
            document.getElementById("resumeContextMenu").classList.add("active");
            isContextMenu = true;
            return;
          }
          playVideo(mediaItems[currentMedia].id);
          break;
        default:
          playSound("border");
          return;
      }
      playSound("run");
      return;
  }
   if (currentMedia == prevMedia) {
      playSound("border");
   } else {
      playSound("select");
   }
   mediaItems[currentMedia].focus();       
}

function wrapIndex(index, arrayLength) {
  return (index + arrayLength) % arrayLength;
}

function isPrintableKey(ev) {
  if (ev.ctrlKey || ev.altKey || ev.metaKey) return false;
  if (ev.key.length === 1) return true;
  return ev.key === "Enter" || ev.key === " ";
}

let isUserGestureRequired = false;

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

async function openThirdPartyStore(store) {
  backend_log("opening store "+ store);
  response = await fetch("/store/"+store);
  responseJson = await response.json();
}

function close_context_menu(play_sound = true){
  isContextMenu = false;
  currentContext = 0;
  //restart selected position
  selectedContext = ctxMenu.getElementsByClassName("contextItem selected")[0];
  selectedContext.classList.remove("selected");
  firstContext = ctxMenu.getElementsByClassName("contextItem")[0];
  firstContext.classList.add("selected");
  elements = document.getElementsByClassName("contextualMenu active");
  Array.prototype.forEach.call(elements, function(element) {
     element.classList.remove("active");
  });
  if (play_sound){
    playSound("enter-back");
  }
}

function open_context_menu(contextMenuName){
  isContextMenu = true;
  document.getElementById(contextMenuName).classList.add("active");
  //refreshCtxMenu();
  playSound("select");
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

MEGABYTE = 1000 * 1000;

async function createProgressBar(){
  const progressOverlay = document.createElement('div');
  progressOverlay.classList.add("overlay");
  progressOverlay.id = "overlay-pb";
  
  const progressBar = document.createElement("progress");
  progressBar.id = "progress-bar";
  progressBar.value = "0";
  progressBar.max = "100";

  const progressTitle = document.createElement("div");
  progressTitle.id = "progress-title";
  progressTitle.classList.add("message");
  progressTitle.style.bottom = "60%";
  progressTitle.style.position = "fixed";
  
  const progressText = document.createElement("div");
  progressText.classList.add("progress-text");
  progressText.id = "progress-text";
  progressText.innerText = "0mb / 0mb";

  progressOverlay.appendChild(progressBar);
  progressOverlay.appendChild(progressTitle);
  progressOverlay.appendChild(progressText);
  document.body.appendChild(progressOverlay); 
}

async function startProgressBar(usePercent = false) {
  await sleep(600);
  document.getElementById("overlay-pb").classList.add("active");
  progressActive = true;
  lockControls = true;
  while (progressActive) {
    response = await fetch("/app/progress");
    global_progress = await response.json();
    progressActive = global_progress["active"];

    const downloaded = (global_progress["downloaded"] / MEGABYTE).toFixed(2);
    const total = (global_progress["total"] / MEGABYTE).toFixed(2);
    if (progressActive){
        document.getElementById("progress-bar").value = global_progress["progress"];
        document.getElementById("progress-title").innerText = global_progress["context"];
        progressMessage = `${Math.round(global_progress["progress"])}%`;
        if (usePercent == false) {
          progressMessage = `${downloaded} / ${total}mb`;
        }
        document.getElementById("progress-text").innerText = progressMessage;
    }
    await sleep(200);
  }
  closeProgressBar();
}

async function closeProgressBar(){
  lockControls = false;
  document.getElementById("overlay-pb").classList.remove("active");
}

async function updateMukkuru() {
  close_context_menu(false);
  startProgressBar();
  response = await fetch("/app/update");
  response_text = await response.text();
  if (response_text == "up-to-date") {
    document.getElementById("messageBox").innerText = "Mukkuru is already up-to-date";
    open_context_menu("messageContext");
  } else if (response_text == "unsupported") {
    document.getElementById("messageBox").innerText = "This Mukkuru app does not support updates";
    open_context_menu("messageContext");
  }
}

async function move_files(transfer_type) {
  response = await fetch("/app/move/"+ transfer_type, {method:"POST"});
  response_text = await response.text();
  document.getElementById("messageBox").innerText = response_text;
  open_context_menu("messageContext");
}

function openStore(){
  playSound("select");
  setTimeout( () =>{
    window.location.replace("/frontend/store");
  }, 100);
}
async function fetch_archives(){
    const archives_r = await fetch("/library/archives");
    const archives = await archives_r.json();
    return archives;
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
    gameArray.forEach((item) => {
        const AppID = item[0];
        box_src = './thumbnails/'+AppID+'.jpg';

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

        const button = document.createElement('button');
        button.className = 'gameLauncher';
        button.id = AppID;
        button.dataset.gameid = AppID;
        button.dataset.source = item[1]["Source"];
        button.dataset.knowndir = "InstallDir" in item[1];
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
        touchEndHandler = () => {
          clearTimeout(timer);
          if (fired){
            fired = false;
            //handle short press
            return;
          }
          //handle long press
          return;
        }
        touchCancelHandler = () => {
          fired = false;
          clearTimeout(timer);
        }
        app.addEventListener('touchstart', touchStartHandler);
        app.addEventListener('touchend', touchEndHandler);
        app.addEventListener('touchcancel', touchCancelHandler);
        button.addEventListener('touchstart', touchStartHandler);
        button.addEventListener('touchend', touchEndHandler);
        button.addEventListener('touchcancel', touchCancelHandler);

    });

    if (gamesAdded >= gameLimit) {
        backend_log("Game limit exceeded, creating all-software button");
        const moreButton = document.createElement('button');
        moreButton.className = 'gameLauncher-more';
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
    
    gameLaunchers = document.querySelectorAll('.gameLauncher, .gameLauncher-more');
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
            item.scrollIntoView({ behavior: "instant", block: "center", inline: "center" });
            if (displayHero) {//start displayHero
                if (!item.classList.contains("gameLauncher-more")) {
                    bg.style.backgroundImage = "url('hero/" + item.id+ ".png')";
                } else{
                    bg.style.backgroundImage = "none";
                }
            }//end displayHero
        });
    });
    measure_time("library loading time", library_start)
}

function attachContextItem(condition, context_menu, context_item){
    if (condition && !context_item.isConnected){
      context_menu.appendChild(context_item);
    } else if (!condition && context_item.isConnected) {
      context_menu.removeChild(context_item);
    }
}