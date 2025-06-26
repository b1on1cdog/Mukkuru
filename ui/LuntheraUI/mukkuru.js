/*
(function(document) {
    var config = {
        kitId: 'ozw8epo',
        scriptTimeout: 3000,
        async: true
    };

    var htmlElement = document.documentElement;

    var timeoutId = setTimeout(function() {
        htmlElement.className = htmlElement.className.replace(/\bwf-loading\b/g, "") + " wf-inactive";
    }, config.scriptTimeout);

    // Create Typekit script element
    var typekitScript = document.createElement("script");
    var firstScript = document.getElementsByTagName("script")[0];
    var scriptLoaded = false;

    // Add loading class to HTML element
    htmlElement.className += " wf-loading";

    // Configure Typekit script
    typekitScript.src = 'https://use.typekit.net/' + config.kitId + '.js';
    typekitScript.async = true;

    // Set up load/readystate handlers
    typekitScript.onload = typekitScript.onreadystatechange = function() {
        var readyState = this.readyState;
        
        // Skip if already loaded or in incomplete state
        if (scriptLoaded || (readyState && readyState != "complete" && readyState != "loaded")) {
            return;
        }
        
        scriptLoaded = true;
        clearTimeout(timeoutId);
        
        try {
            Typekit.load(config);
        } catch (error) {
            // Handle error if Typekit fails to load
        }
    };

    // Insert Typekit script before the first script element
    firstScript.parentNode.insertBefore(typekitScript, firstScript);
})(document);
*/
const backendURL = "http://localhost:49347";

const audioContext = new (window.AudioContext || window.webkitAudioContext)();
const audioBuffers = {}; // Store all loaded buffers
const maxPoolSize = 4; // Maximum number of instances to keep for each sound
const audioPlayedAt = {};
let userConfiguration = {};

// Object to track buffer sources pools for each sound
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
      source.start(0); // Start playing immediately
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
            setTimeout(next, 20); //depending on how fast you want to fade
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
            setTimeout(next, ms); //depending on how fast you want to fade
        }
    })();
}

function goHome(){
    vanish(document.getElementsByClassName("homeMenu")[0]);
    playSound("home");
        sleep(500).then(() => {
            window.location.replace(backendURL+"/frontend/")
        }); 
}

function booleanTgl(statement){
 return statement?"ON":"OFF";
}

function backend_log(message){
  console.log(message);
  fetch(backendURL+ "/log/"+btoa(message)).then(function(response) {
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
  configReady = resolve; // assign resolver to outer variable
});

function hardwareStatusUpdate(){
     fetch(backendURL+"/hardware/battery").then(function(response) {
        return response.json();
    }).then(function(battery) {
      if (battery == null) {
          document.getElementsByClassName("batteryState")[0].style.display = "none";
      } else {
          document.getElementsByClassName("batteryLevel")[0].style.width = "" + (100-battery.percent) + "%";
      }
      
    });

      fetch(backendURL+"/hardware/network").then(function(response) {
        return response.json();
    }).then(function(network) {
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
    });

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
    hardwareStatusUpdate();
  }

  function showKeyGuide(state) {
    document.getElementsByClassName("homeFooter")[0].style.display = state?"flex":"none";
  }
  function showBottomBar(state) {
    document.getElementsByClassName("footerNavigation")[0].style.display = state?"flex":"none";
  }
  const isFirefox = typeof navigator !== 'undefined' && /firefox/i.test(navigator.userAgent);