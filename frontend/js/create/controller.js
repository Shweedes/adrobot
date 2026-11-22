/** Экран создания кампании: форма, проверка полей, отправка. */

import { api } from "../api.js";
import { createCombobox } from "../combobox.js";
import { $, copyText, toast } from "../dom.js";
import { offerLabel } from "../format.js";
import { parseGeo } from "../geo.js";
import { offerOptionHtml, searchOffers } from "../offers.js";
import { autoSettingsHtml, createdHtml, routeHtml } from "./view.js";

const HINTS = {
  name: "Префикс добавится автоматически",
  geo: "Двухбуквенные коды стран через запятую",
  offer: "Поиск по офферам Keitaro",
};

const state = { meta: null, offer: null };

/**
 * Показывает подсказку или ошибку под полем.
 * @param {"name"|"geo"|"offer"} field
 * @param {string|null} message `null` оставляет текст без изменений
 * @param {"error"|"ok"|null} kind
 */
function setField(field, message, kind) {
  const box = $(`#field-${field}`);
  box.classList.toggle("is-error", kind === "error");
  box.classList.toggle("is-ok", kind === "ok");
  if (message != null) $(`#h-${field}`).textContent = message;
}

/** Текст ошибки для неверных кодов стран. */
const invalidGeoMessage = (invalid) =>
  `«${invalid.join(", ")}» — нужны двухбуквенные коды, например AU`;

/** Перерисовывает превью маршрута по текущему состоянию формы. */
function renderRoute() {
  const { codes, invalid } = parseGeo($("#f-geo").value);
  const geo = codes.filter((code) => !invalid.includes(code));
  $("#route").innerHTML = routeHtml({ geo, offer: state.offer, meta: state.meta });
}

/** Проверяет поля формы и подсвечивает ошибки. */
function validate() {
  let ok = true;
  const { codes, invalid } = parseGeo($("#f-geo").value);
  if (!$("#f-name").value.trim()) {
    setField("name", "Введите название кампании", "error");
    ok = false;
  }
  if (!codes.length) {
    setField("geo", "Укажите хотя бы одну страну", "error");
    ok = false;
  } else if (invalid.length) {
    setField("geo", invalidGeoMessage(invalid), "error");
    ok = false;
  }
  if (!state.offer) {
    setField("offer", "Выберите оффер из списка", "error");
    ok = false;
  }
  return ok;
}

/** Возвращает форму в исходное состояние. */
function reset() {
  $("#create-form").reset();
  state.offer = null;
  for (const field of Object.keys(HINTS)) setField(field, HINTS[field], null);
  $("#created").hidden = true;
  renderRoute();
  $("#f-name").focus();
}

/** Показывает результат создания. */
function showCreated(campaign) {
  const box = $("#created");
  box.hidden = false;
  box.innerHTML = createdHtml(campaign);
  box.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

/** Отправляет форму и показывает результат или ошибку. */
async function onSubmit(event) {
  event.preventDefault();
  if (!validate()) return;
  const button = $("#create-btn");
  button.disabled = true;
  button.textContent = "Создаём…";
  try {
    const campaign = await api("/campaigns", {
      method: "POST",
      body: { name: $("#f-name").value.trim(), geo: $("#f-geo").value, offer_id: state.offer.id },
    });
    showCreated(campaign);
    toast("Кампания создана", "ok");
  } catch (error) {
    toast(error.message, "error");
  } finally {
    button.disabled = false;
    button.textContent = "Создать кампанию";
  }
}

/** Реагирует на ввод кодов стран. */
function onGeoInput(event) {
  const { codes, invalid } = parseGeo(event.target.value);
  if (invalid.length) setField("geo", invalidGeoMessage(invalid), "error");
  else if (codes.length) setField("geo", `Стран: ${codes.length}`, "ok");
  else setField("geo", HINTS.geo, null);
  renderRoute();
}

/** Реагирует на кнопки панели результата. */
function onCreatedClick(event) {
  const button = event.target.closest("button");
  if (!button) return;
  if (button.dataset.copy) copyText(button.dataset.copy);
  if (button.dataset.open) location.hash = `#edit/${button.dataset.open}`;
  if ("reset" in button.dataset) reset();
}

/** Подключает выбор оффера из подсказок. */
function bindOfferPicker() {
  const input = $("#f-offer");
  createCombobox({
    input,
    panel: $("#offer-list"),
    search: searchOffers,
    renderItem: offerOptionHtml,
    onPick: (offer) => {
      state.offer = offer;
      input.value = `${offer.id} · ${offerLabel(offer.id, offer.name)}`;
      setField("offer", "Оффер выбран", "ok");
      renderRoute();
    },
  });
  input.addEventListener("input", () => {
    if (!state.offer) return;
    state.offer = null;
    setField("offer", "Выберите оффер из списка", null);
    renderRoute();
  });
}

/**
 * Подключает экран создания кампании.
 * @param {import("../types.js").Meta} meta
 */
export function initCreate(meta) {
  state.meta = meta;
  $("#prefix").textContent = meta.prefix;
  $("#auto").innerHTML = autoSettingsHtml(meta);
  renderRoute();

  $("#f-geo").addEventListener("input", onGeoInput);
  $("#f-name").addEventListener("input", () => setField("name", HINTS.name, null));
  bindOfferPicker();
  $("#create-form").addEventListener("submit", onSubmit);
  $("#created").addEventListener("click", onCreatedClick);
}
