/** Экран редактора: загрузка кампании, период, добавление и удаление офферов. */

import { api } from "../api.js";
import { createCombobox } from "../combobox.js";
import { $, copyText, toast } from "../dom.js";
import { searchTerm } from "../format.js";
import { offerOptionHtml, searchOffers } from "../offers.js";
import { campaignHtml, campaignListHtml, campaignOptionHtml, messageHtml } from "./view.js";

const CONFIRM_TIMEOUT_MS = 3000;

const state = { campaignId: null, range: "today" };
let root;

/** ID открытой кампании или `null`. */
export const currentCampaignId = () => state.campaignId;

/** Включает или выключает кнопку «Обновить». */
const setRefreshEnabled = (enabled) => {
  $("#refresh").disabled = !enabled;
};

/**
 * Отрисовывает кампанию и подключает добавление офферов в её потоки.
 * @param {import("../types.js").CampaignDetails} details
 */
function render(details) {
  const { campaign, streams } = details;
  state.campaignId = campaign.id;
  $("#f-campaign").value = `${campaign.id} · ${campaign.name}`;
  setRefreshEnabled(true);
  root.innerHTML = campaignHtml(details);
  streams.filter((s) => s.kind === "offers").forEach(bindAddOffer);
}

/**
 * Выполняет изменение, показывает обновлённую кампанию и уведомление.
 * @param {() => Promise<import("../types.js").CampaignDetails>} request
 * @param {string} successMessage
 */
async function mutate(request, successMessage) {
  root.classList.add("is-busy");
  try {
    render(await request());
    toast(successMessage, "ok");
  } catch (error) {
    toast(error.message, "error");
  } finally {
    root.classList.remove("is-busy");
  }
}

/** Путь к офферам потока открытой кампании с текущим периодом. */
const offersPath = (streamId, offerId = "") =>
  `/campaigns/${state.campaignId}/streams/${streamId}/offers${offerId && `/${offerId}`}` +
  `?range=${state.range}`;

/**
 * Подключает поле добавления оффера в поток; офферы потока в подсказках не показываются.
 * @param {import("../types.js").Stream} stream
 */
function bindAddOffer(stream) {
  const input = $(`#add-${stream.id}`);
  const present = new Set(stream.offers.map((o) => o.offer_id));
  createCombobox({
    input,
    panel: $(`#add-list-${stream.id}`),
    search: async (query) => (await searchOffers(query)).filter((o) => !present.has(o.id)),
    renderItem: offerOptionHtml,
    onPick: (offer) => {
      input.value = "";
      mutate(
        () => api(offersPath(stream.id), { method: "POST", body: { offer_id: offer.id } }),
        `Оффер ${offer.id} добавлен`
      );
    },
  });
}

/**
 * Первый клик по корзине просит подтверждения, второй удаляет.
 * @param {HTMLButtonElement} button
 */
function armRemove(button) {
  const original = button.innerHTML;
  button.classList.add("armed");
  button.textContent = "last" in button.dataset ? "Удалить последний?" : "Удалить?";
  setTimeout(() => {
    button.classList.remove("armed");
    button.innerHTML = original;
  }, CONFIRM_TIMEOUT_MS);
}

/** Удаляет оффер, на кнопке которого подтвердили действие. */
function removeOffer(button) {
  const { stream, offer } = button.dataset;
  const message =
    "last" in button.dataset
      ? `Оффер ${offer} удалён. В потоке не осталось офферов, добавьте новый`
      : `Оффер ${offer} удалён`;
  mutate(() => api(offersPath(stream, offer), { method: "DELETE" }), message);
}

/** Реагирует на кнопки внутри редактора. */
function onRootClick(event) {
  const button = event.target.closest("button");
  if (!button) return;
  const { dataset } = button;
  if (dataset.copy) return copyText(dataset.copy);
  if (dataset.open) {
    location.hash = `#edit/${dataset.open}`;
    return;
  }
  if ("reloadList" in dataset) return showCampaignList();
  if (dataset.retry) return openCampaign(Number(dataset.retry));
  if ("remove" in dataset) {
    if (button.classList.contains("armed")) removeOffer(button);
    else armRemove(button);
  }
}

/** Переключает период статистики. */
function onRangeClick(event) {
  const button = event.target.closest("[data-range]");
  if (!button) return;
  state.range = button.dataset.range;
  for (const item of $("#range").children) item.setAttribute("aria-pressed", String(item === button));
  if (state.campaignId) openCampaign(state.campaignId);
}

/**
 * Загружает и показывает кампанию.
 * @param {number} id
 */
export async function openCampaign(id) {
  state.campaignId = id;
  setRefreshEnabled(false);
  root.innerHTML = '<div class="skeleton"></div><div class="skeleton"></div>';
  try {
    render(await api(`/campaigns/${id}?range=${state.range}`));
  } catch (error) {
    state.campaignId = null;
    root.innerHTML = messageHtml({
      title: `Не удалось открыть кампанию ${id}`,
      text: error.message,
      action: { label: "Повторить", attrs: `data-retry="${id}"` },
    });
  }
}

/** Показывает список последних кампаний, если ни одна не открыта. */
export async function showCampaignList() {
  state.campaignId = null;
  setRefreshEnabled(false);
  root.innerHTML = '<div class="skeleton"></div>';
  let html;
  try {
    const campaigns = await api("/campaigns?q=");
    html = campaigns.length
      ? campaignListHtml(campaigns)
      : messageHtml({
          title: "Кампаний пока нет",
          text: "Создайте первую на вкладке «Создать кампанию».",
        });
  } catch (error) {
    html = messageHtml({
      title: "Не удалось загрузить список кампаний",
      text: error.message,
      action: { label: "Повторить", attrs: "data-reload-list" },
    });
  }
  if (state.campaignId === null) root.innerHTML = html;
}

/** Подключает экран редактора: события, период и поиск кампании. */
export function initEditor() {
  root = $("#editor");
  root.addEventListener("click", onRootClick);
  $("#range").addEventListener("click", onRangeClick);
  $("#refresh").addEventListener("click", () => state.campaignId && openCampaign(state.campaignId));
  createCombobox({
    input: $("#f-campaign"),
    panel: $("#campaign-list"),
    search: (query) => api(`/campaigns?q=${encodeURIComponent(searchTerm(query))}`),
    renderItem: campaignOptionHtml,
    onPick: (campaign) => {
      location.hash = `#edit/${campaign.id}`;
    },
  });
}
