// Copyright (c) 2025 b1on1cdog
// Licensed under the MIT License
const audioContext = new (window.AudioContext || window.webkitAudioContext)();
const audioBuffers = {};
const maxPoolSize = 4; // Maximum number of instances to keep for each sound
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
    'tick': './assets/audio/Tick.wav',
    'select': './assets/audio/Select.wav',
    'home': './assets/audio/Home.wav',
    'border': './assets/audio/Border.wav',
    'enter-back': './assets/audio/Enter & Back.wav',
    'run': './assets/audio/Run.wav',
    'settings': './assets/audio/Settings.wav',
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
          batteryLevel.style.width = "" + (100-battery.percent) + "%";
          if ("power_plugged" in battery && battery.power_plugged) {
            batteryCharging = document.getElementsByClassName("batteryCharging")[0];
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

let videoTimeUpdateIntervalId;
let videoTimeDisplayTimeoutId;

function playVideo(videoFile){
  isVideoPlayer = true;
  video = document.getElementById("videoPlayer");
  video.classList.add("active");
  
/*
  var source = document.createElement('source');
  source.setAttribute('src', videoFile);
  source.setAttribute('type', 'video/mp4');
  video.appendChild(source);
*/
  video.src = videoFile;
  video.load();
  video.play();
  hideUI(true);
  if (isContextMenu) {
    closeCTX();
  }
  videoTime = document.getElementById("videoTime");
  videoTimeUpdateIntervalId = setInterval(() => {
    if (videoTime == undefined) {
      videoTime = document.getElementById("videoTime");
    }
    videoTime.innerText = formatDuration(video.currentTime) + "/" + formatDuration(video.duration);
  }, "1000");
  
}

function closeVideo(){
  isVideoPlayer = false;
  video = document.getElementById("videoPlayer");
  video.classList.remove("active");
  video.pause();
  video.currentTime = 0;
  hideUI(false);
  if (videoTimeUpdateIntervalId != undefined){
    clearInterval(videoTimeUpdateIntervalId);
    document.getElementById("videoTime").classList.remove("active");
  }
}

function formatDuration(totalSeconds) {
  const sec = Math.floor(totalSeconds % 60).toString().padStart(2, '0');
  const min = Math.floor((totalSeconds / 60) % 60).toString().padStart(2, '0');
  const hrs = Math.floor(totalSeconds / 3600);

  return hrs > 0 ? `${hrs}:${min}:${sec}` : `${min}:${sec}`;
}


function videoControl(action){
  video = document.getElementById("videoPlayer");
  switch (action) {
    case "left":
      video.currentTime = Math.max(video.currentTime - 15, 0);
      break;
    case "right":
      video.currentTime = Math.min(video.currentTime + 15, video.duration);
      break;
    case "up":
      video.volume = Math.min(video.volume + 0.05, 1);
      break;
    case "down":
      video.volume = Math.max(video.volume - 0.05, 0);
      break;
    case "back":
      closeVideo();
      return;
    case "confirm":
      if (video.paused) {
        video.play();
      } else {
        video.pause();
      }
      break;
    default:
      break;
  }
  videoTime = document.getElementById("videoTime");
  videoTime.innerText =  formatDuration(video.currentTime) + "/" + formatDuration(video.duration);
  videoTime.classList.add("active");
  if (videoTimeDisplayTimeoutId != undefined) {
    clearTimeout(videoTimeDisplayTimeoutId);
  }
  videoTimeDisplayTimeoutId = setTimeout(() => {
      videoTime.classList.remove("active");
    }, "3500");
}

// video_parser.js

let videos = { };

function send_videos_metadata(){
    fetch("/video/set", {
      method: "POST",
      body: JSON.stringify(videos),
      headers: {
        "Content-type": "application/json; charset=UTF-8"
      }
      }).then((response) => {
        
      });
}
function deleteVideo(videoItem){
    const videoFile = videoItem.dataset.play;
    fetch(videoFile, {
      method: "DELETE",
      headers: {
        "Content-type": "application/json; charset=UTF-8"
      }
      }).then((response) => {
        videoItem.remove();
        document.getElementById("videoContextMenu").classList.remove("active");
        isContextMenu = false;
        mediaItems = document.querySelectorAll('.videoLauncher')
        if (mediaItems.length == 0) {
          goHome();
        } else {
          currentMedia--;
          mediaItems[currentMedia].focus();
        }
      });
}

function send_video_thumbnail(thumbnail, video_id){
    fetch("/video/thumbnail/"+video_id, {
      method: "POST",
      body: JSON.stringify(thumbnail),
      headers: {
        "Content-type": "application/json; charset=UTF-8"
      }
      }).then((response) => {
        
      });
}

async function get_video_metadata(video_url, vid){
    console.log("processing metadata for " + video_url);
    vid.id = 'metadata-video';
    vid.preload = 'metadata';
    vid.src = video_url;
    vid.muted = true;
    document.body.appendChild(vid);

    await new Promise(r => vid.onloadedmetadata = r);
    const duration = vid.duration;

    vid.currentTime = Math.min(90.5, duration / 2);

    await new Promise(r => vid.onseeked = r);

    const c  = document.createElement('canvas');
    c.width  = vid.videoWidth;
    c.height = vid.videoHeight;
    c.getContext('2d').drawImage(vid, 0, 0);
    const png = c.toDataURL('image/png');
    vid.pause();
    metadata = {
        "duration" : vid.duration,
        "thumbnail" : png,
    }
    return metadata;
}

function refreshVideoMetadata(video_id, video_duration = "00:00"){
    videoElement = document.getElementById("video_"+video_id);
    if (videoElement != undefined){
        try {
            th = videoElement.getElementsByClassName("video-thumbnail")[0];
            th.src = th.src;
            duration = videoElement.getElementsByClassName("duration")[0];
            duration.textContent = formatDuration(video_duration);
        } catch {}
    }
}

async function update_videos_metadata(vids){
    const vid = document.createElement('video');
    for (const id in vids) {
        const video = vids[id];
        if ("duration" in video && video["thumbnail_exists"]){
            //console.log("skipping "+id)
            continue;
        }
        const metadata = await get_video_metadata(video.url, vid);
        thumbnail = metadata["thumbnail"];
        delete metadata.thumbnail;
        Object.assign(videos[id], metadata);
        send_video_thumbnail(thumbnail, id);

        //let's refresh thumbnail
        setTimeout(() => {
            refreshVideoMetadata(id, metadata.duration);
        }, "500");
    }
  //  console.log(JSON.stringify(videos));
    send_videos_metadata();
    vid.remove();
}

function fetch_videos(){
    document.querySelectorAll('.videoLauncher').forEach(el => el.remove());
    fetch("/media/get").then(function(response) {
        return response.json();
    }).then(function(data) {
        videos = data["videos"];
       // console.log(data);
        update_videos_metadata(videos);
        mediaList = document.getElementsByClassName("mediaList")[0];
        for (const id in videos){
            video = videos[id];
            
            const videoLauncher = document.createElement('button');
            videoLauncher.className = 'videoLauncher';
            /*
            if (favoriteGames.has(AppID)){
                app.classList.add("favorite");
            }*/
            videoLauncher.id = "video_" + id;
            videoLauncher.dataset.play = video.url;
            const videoTitle = document.createElement('div');
            videoTitle.className = "video-title";
            videoTitle.textContent = video.file
            videoTitle.dataset.text = videoTitle.textContent;
            const videoImage = document.createElement('img');
            videoImage.className = 'video-thumbnail';
            videoImage.src = video.thumbnail_url;
            videoImage.alt = video.file;
            const durationElement = document.createElement('div');
            durationElement.className = "duration";
            durationElement.textContent = formatDuration(video.duration);
            videoLauncher.appendChild(videoTitle);
            videoLauncher.appendChild(videoImage);
            videoLauncher.appendChild(durationElement);
            mediaList.appendChild(videoLauncher);
            videoLauncher.addEventListener('focus', () => {
              videoLauncher.scrollIntoView({ behavior: "instant", block: "center" });
            });
        }

    });
}

// end video_parser.js

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
            playVideo(value);
            fetch_videos();
            break;
          case "reloadVideos":
            fetch_videos();
            break;
          case "playAudio":
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
      goHome();
      break;
    case "options":
      document.getElementById("videoContextMenu").classList.add("active");
      isContextMenu = true;
      return;
    case "confirm":
      switch (mediaItems[currentMedia].className){
        case "videoLauncher":
          playVideo(mediaItems[currentMedia].dataset.play);
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