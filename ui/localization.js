function swapText(elementID, newText) {
  const element = document.getElementById(elementID);
  if (element != undefined && element != null) {
      element.innerText = newText;
  }
}

function swapAriaLabel(elementID, newText) {
  const element = document.getElementById(elementID);
  if (element != undefined && element != null) {
      element.ariaLabel = newText;
  }
}

function swapTGL(elementID, newText){
  const element = document.getElementById(elementID);
  if (element != undefined && element != null) {
      replaceText = element.innerHTML.split("<span")[0];
      resize = (21 / newText.length ) * 100;
      if (resize > 130) {
        resize = 120;
      }
      element.innerHTML = element.innerHTML.replace(replaceText, newText);
      element.style.fontSize = resize + "%";
  }
}


function patchHTML(elementID, oldText, newText){
  const element = document.getElementById(elementID);
  if (element != undefined && element != null) {
      element.innerHTML = element.innerHTML.replace(oldText, newText);
  }
}

let localization = {};
let localizationReady;

const isLocalizationReady = new Promise((resolve) => {
  localizationReady = resolve;
});

function translate_str(key, str){
  if (localization["available"] == false ) {
    backend_log("localization not available");
    return str;
  } else if (localization[key] == undefined) {
    backend_log("undefined key, l "+Object.keys(localization).length);
    return str;
  }
  return localization[key];
}

function translateAll(translation = localization) {
  const elements = document.querySelectorAll('[data-loc]');
   elements.forEach(el => {
      try {
      let loc_key = el.dataset.loc;
      if (loc_key == "id") {
        loc_key = el.id;
      }
      switch(el.dataset.trm) {
        case "ariaLabel":
          swapAriaLabel(el.id, translation[loc_key]);
          break;
        case "patchHTML":
          patchHTML(el.id, el.dataset.patch, translation[loc_key]);
          break;
        case "swapText":
          swapText(el.id, translation[loc_key]);
          break;
        case "swapTGL":
          swapTGL(el.id, translation[loc_key]);
          break;
        default:
          backend_log("unknown translation rule");
          break;
      }
    } catch (err) {
      backend_log("exception: "+err.message);
    }
    });
    localizationReady();
}

function get_localization(){
  fetch("/localization").then(function(response) {
    return response.json();
  }).then(function(data) {
    localization = data;
    if (localization["available"] == false) {
      localizationReady();
      return;
    }
    translateAll(data);
  });
}



function allowRendering(reload = false) {
  backend_log("applying localization...")
  fetch("/localization").then(function(response) {
    return response.json();
  }).then(function(data) {
    homeMenu = document.getElementsByClassName("homeMenu")[0];
    translation = data;
    localization = data;
    if (translation["available"] == false) {
      backend_log("localization unavailable");
      if (reload) {
        backend_log("reloading....");
        location.reload();
      }
      localizationReady();
    } else {
    
    swapText("options-keyText", translation["Options"]);
    swapText("start-keyGuide", translation["Start"]);
    swapText("ok-keyGuide", translation["OK"]);
    swapText("back-keyText", translation["Back"]);
    swapTGL("librarySource", translation["LibrarySources"]);
    swapText("librarySource-desc", translation["LibrarySources-desc"]);
    swapText("settings-header", translation["SystemSettings"]);
    swapText("store-header", translation["Store"]);

    apOption = document.getElementById("autoPlayOption");
    if (apOption != undefined){
      apOption.dataset.off = translate_str("AutoPlayDisabled", "AutoPlay enabled");
      apOption.dataset.on = translate_str("AutoPlayEnabled", "AutoPlay disabled");
    }
    translateAll(translation);

    }

    if (!reload){
      unblockElements();
      unvanish(homeMenu, 40);
    }
  });

}