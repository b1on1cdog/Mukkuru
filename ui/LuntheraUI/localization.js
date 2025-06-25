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
    
    swapText("options-keyGuide", translation["Options"]);
    swapText("start-keyGuide", translation["Start"]);
    swapText("ok-keyGuide", translation["OK"]);
    swapText("back-keyGuide", translation["Back"]);
    swapTGL("librarySource", translation["LibrarySources"]);
    swapText("librarySource-desc", translation["LibrarySources-desc"]);
    swapText("settings-header", translation["SystemSettings"]);
    swapAriaLabel("settingsFB", translation["settingsFB"]);
    swapAriaLabel("storeFB", translation["storeFB"]);
    swapAriaLabel("scanFB", translation["scanFB"]);
    swapAriaLabel("powerFB", translation["powerFB"]);
    swapAriaLabel("controllerFB", translation["controllerFB"]);
    
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
      //    backend_log("translating ->"+el.id)
          swapText(el.id, translation[loc_key]);
          break;
        case "swapTGL":
          swapTGL(el.id, translation[loc_key]);
          break;
        default:
          backend_log("unknown translation rule");
          break;
      }
     // backend_log(el.id + " > " + el.innerText.length)
    } catch (err) {
      backend_log("exception: "+err.message);

    }
    });


    }

    if (!reload){
      unblockElements();
      unvanish(homeMenu, 40);
    }
  });

}