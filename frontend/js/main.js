/** Точка входа: загрузка настроек, вкладки и маршрутизация по hash. */

import { api } from "./api.js";
import { $, toast } from "./dom.js";
import { initCreate } from "./create/controller.js";
import { currentCampaignId, initEditor, openCampaign, showCampaignList } from "./editor/controller.js";

/** Показывает выбранный экран и подсвечивает вкладку. */
function showView(name) {
  for (const tab of document.querySelectorAll(".tabs [role=tab]")) {
    tab.setAttribute("aria-selected", String(tab.dataset.view === name));
  }
  $("#view-create").hidden = name !== "create";
  $("#view-edit").hidden = name !== "edit";
}

/** Приводит экран в соответствие с `location.hash`: `#create`, `#edit`, `#edit/<id>`. */
function applyHash() {
  const [view, idPart] = location.hash.replace("#", "").split("/");
  if (view !== "edit") return showView("create");

  showView("edit");
  const id = Number(idPart);
  if (id) {
    if (id !== currentCampaignId()) openCampaign(id);
  } else if (currentCampaignId() === null) {
    showCampaignList();
  }
}

/** Переключает экран по клику на вкладку, запоминая открытую кампанию. */
function onTabClick(event) {
  const tab = event.target.closest("[data-view]");
  if (!tab) return;
  const campaignId = currentCampaignId();
  location.hash = tab.dataset.view === "edit" ? `#edit${campaignId ? `/${campaignId}` : ""}` : "#create";
}

/** Загружает настройки и запускает экраны. */
async function start() {
  let meta;
  try {
    meta = await api("/meta");
  } catch (error) {
    toast(error.message, "error");
    return;
  }
  initCreate(meta);
  initEditor();
  $(".tabs").addEventListener("click", onTabClick);
  window.addEventListener("hashchange", applyHash);
  applyHash();
}

start();
