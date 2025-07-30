
// Copyright (c) 2025 b1on1cdog
// Licensed under the MIT License

function showPreviousSeparator(state){
    if (tabOptions[selectedTab][selectedOption].previousElementSibling != null && tabOptions[selectedTab][selectedOption].previousElementSibling.className == "option-separator") {
        tabOptions[selectedTab][selectedOption].previousElementSibling.style.display = state?"":"none";
    }
}

function showNextSeparator(state){
    if (tabOptions[selectedTab][selectedOption].nextElementSibling != null && tabOptions[selectedTab][selectedOption].nextElementSibling.className == "option-separator") {
        tabOptions[selectedTab][selectedOption].nextElementSibling.style.display = state?"":"none";
    }
}

function refreshOptions() {
    document.querySelectorAll(".options").forEach((item, index) => {
        options = item.querySelectorAll(".menu-option");
        tabOptions[index] = options;
});
}

let previousPages = [];
let isScrollable = false;
let scrollableItem = null;

function openNextPage(newScreen){
    absoluteTab = document.getElementById("options-"+selectedTab);
    previousPages.push(absoluteTab.cloneNode(true));
    absoluteTab.replaceChildren(newScreen);
    //scrollIntoView({ behavior: "instant", block: "center", inline: "nearest" });
    refreshOptions();
}

function removeElementWithSibling(element){
  element.nextElementSibling.remove();
  element.remove();
}
/* this is used by home */
async function applyStoreFilter(isSettings = false) {
  stores_response = await fetch("/storefront/get");
  stores = await stores_response.json();
  steam = false;
  crossover_steam = false;
  egs = false;
  heroic = false;

  backend_log(JSON.stringify(stores));

  for (let i = 0; i < stores.length; i++) {
   switch (stores[i]) {
    case "steam":
      steam = true;
      break;
    case "crossover_steam":
      crossover_steam = true;
      break;
    case "egs":
      egs = true;
      break;
    case "heroic":
      heroic = true;
      break;
    default:
      break;
   }
  }

  if (isSettings) {
    if (!steam && !crossover_steam) {
      removeElementWithSibling(document.getElementById("sources-0"));
      removeElementWithSibling(document.getElementById("sources-1"));
    }
    if (!egs) {
      removeElementWithSibling(document.getElementById("sources-2"));
    }
    if (!heroic) {
      removeElementWithSibling(document.getElementById("sources-3"));
    }
    refreshOptions();
    return;
  }
  steamContext = document.getElementById("steamContext");
  //debug
  //crossover_steam = true;
  if (crossover_steam) {
    const clone = steamContext.cloneNode(true);
    clone.removeAttribute("onclick");
    clone.innerHTML = clone.innerHTML + " (Crossover)";
    clone.onclick = () => { 
      openThirdPartyStore("crossover_steam");
     };
     if (steam) {
        clone.classList.remove("selected");
     }
     steamContext.parentNode.insertBefore(clone, steamContext.nextSibling);
  }

  if (!steam) {
      steamContext.remove();
  }

  egsContext = document.getElementById("egsContext");
  if (!egs) {
    egsContext.remove();
  }
  
}

function openPreviousPage(){
    absoluteTab = document.getElementById("options-"+selectedTab);
    const previousPage = previousPages.pop();
    absoluteTab.replaceChildren(...previousPage.childNodes);
    refreshOptions();
    isScrollable = false;
    selectedOption = 0;
    document.querySelectorAll(".menu-option.selected").forEach((element) => element.classList.remove("selected"));
    document.querySelectorAll(".option-separator").forEach((element) => element.style.display = "");
    if (!isTab){
        showPreviousSeparator(false);
        tabOptions[selectedTab][selectedOption].classList.add("selected");
        showNextSeparator(false);
    }
}
