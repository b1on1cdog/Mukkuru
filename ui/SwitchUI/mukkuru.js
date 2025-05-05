
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
    'run': './assets/audio/Popup + Run Title.wav',
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

function vanish(element)
{
    var oppArray = ["0.9", "0.8", "0.7", "0.6", "0.5", "0.4", "0.3", "0.2", "0.1", "0"];
    var x = 0;
    (function next() {
        element.style.opacity = oppArray[x];
        if(++x < oppArray.length) {
            setTimeout(next, 25); //depending on how fast you want to fade
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
  fetch(backendURL+ "/log/"+btoa(message)).then(function(response) {
    return response.text();
});
}
function unblockElements(){
  const elements = document.querySelectorAll('.pending');

  elements.forEach(el => {
      el.classList.remove('pending');
  });
  //document.getElementsByClassName("homeMenu")[0].style.setProperty("display", "flex");
}

var docStyle = window.getComputedStyle(document.documentElement);
var lightColor = docStyle.getPropertyValue('--bg-color');  //#EBEBEB
var darkColor = docStyle.getPropertyValue('--main-color'); //#2E2E2E

function applyDarkMode(){
  document.documentElement.style.setProperty("--bg-color", darkColor);
  document.documentElement.style.setProperty("--main-color", lightColor);
  console.log("[debug] dark mode enabled");
}

let configReady;

const isConfigReady = new Promise((resolve) => {
  configReady = resolve; // assign resolver to outer variable
});

function clockUpdate(meridiem){
    backend_log("[time]");

    const now = new Date();
    const h = document.querySelector('.timeHour');

    let hours = now.getHours();
    let suffix = "";
    if (meridiem && hours > 12) {
      hours = hours - 12;
      suffix = " PM";
    } else if (meridiem) {
      suffix = " AM";
    }

    h.innerText = hours;
    const m = document.querySelector('.timeMinute');

    if (now.getMinutes() < 10) {
        m.innerText = "0" + now.getMinutes();
    } else {
        m.innerText = now.getMinutes() + suffix;
    }
  }