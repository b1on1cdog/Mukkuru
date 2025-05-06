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

function allowRendering(reload = false) {
  backend_log("applying localization...")
  fetch(backendURL+"/localization").then(function(response) {
    return response.json();
  }).then(function(data) {
    homeMenu = document.getElementsByClassName("homeMenu")[0];
    translation = data;
    if (translation["available"] == false) {
      backend_log("localization unavailable");
      if (reload) {
        backend_log("reloading....");
        location.reload();
      }
    } else {
    swapText("aboutTab", translation["About"]);
    swapText("navigationTab", translation["Navigation"]);
    swapText("languageTab", translation["Language"]);
    swapText("libraryTab", translation["Library"]);
    swapText("themesTab", translation["Themes"]);
    swapText("options-keyGuide", translation["Options"]);
    swapText("start-keyGuide", translation["Start"]);
    swapText("ok-keyGuide", translation["OK"]);
    swapText("back-keyGuide", translation["Back"]);
    swapTGL("librarySource", translation["LibrarySources"]);
    swapText("librarySource-desc", translation["LibrarySources-desc"]);
    swapText("settings-header", translation["SystemSettings"]);

    swapTGL("skipNoArt", translation["skipNoArt"]);
    swapTGL("fullScreen", translation["fullScreen"]);
    swapTGL("12H", translation["12H"]);
    swapTGL("loop", translation["loop"]);
    swapText("loop-desc", translation["loop-desc"]);
    swapTGL("startupGameScan", translation["startupGameScan"]);
    swapText("startupGameScan-desc", translation["startupGameScan-desc"]);
    swapTGL("maxGamesInHomeScreen", translation["maxGamesInHomeScreen"]);
    swapText("maxGamesInHomeScreen-desc", translation["maxGamesInHomeScreen-desc"]);

    swapTGL("hardwareInfo", translation["hardwareInfo"]);

    patchHTML("lightMode", "Basic White", translation["lightMode"]);
    patchHTML("darkMode", "Basic Black", translation["darkMode"]);

    swapAriaLabel("settingsFB", translation["settingsFB"]);
    swapAriaLabel("storeFB", translation["storeFB"]);
    swapAriaLabel("scanFB", translation["scanFB"]);
    swapAriaLabel("powerFB", translation["powerFB"]);
    swapAriaLabel("controllerFB", translation["controllerFB"]);

    const elements = document.querySelectorAll('[data-loc]');
    elements.forEach(el => {
      switch(el.dataset.trm) {
        case "ariaLabel":
          swapAriaLabel(el.id, translation[el.dataset.loc]);
          break;
        case "patchHTML":
         // patchHTML(el.id, ..., translation[el.dataset.loc]);
          break;
        case "swapText":
          swapText(el.id, translation[el.dataset.loc]);
          break;
        case "swapTGL":
          swapTGL(el.id, translation[el.dataset.loc]);
          break;
        default:
          backend_log("unknown translation rule");
          break;
      }
      backend_log(el.id + " > " + el.innerText.length)
    });


    }

    if (!reload){
      unblockElements();
      unvanish(homeMenu, 40);
    }
  });

}

/*
Possible way to make this logic simpler (at expense of HTML complexity):
data-loc: localization key
data-trm: translation method

const elements = document.querySelectorAll('[data-loc]');
  elements.forEach(el => {
    switch(el.dataset.trm) {
      case "ariaLabel":
        swapAriaLabel(el.id, translation[el.dataset.loc]);
        break;
      case "patchHTML":
        patchHTML(el.id, ..., translation[el.dataset.loc]);
        break;
      case "swapText":
        swapText(el.id, translation[el.dataset.loc]);
        break;
      case "swapTGL":
        swapTGL(el.id, translation[el.dataset.loc]);
        break;
    }
  });

*/