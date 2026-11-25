/** HTML-шаблоны редактора кампании. */

import { esc, numberFormat } from "../dom.js";
import { offerLabel } from "../format.js";

const FILTER_NAMES = {
  country: "Страны",
  city: "Города",
  device_type: "Тип устройства",
  os: "ОС",
  browser: "Браузер",
  language: "Язык",
};
const FILTER_MODES = { accept: "принимать", reject: "отклонять" };
const TRASH_ICON =
  '<svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">' +
  '<path d="M3.5 5h11M7 5V3.5h4V5m-6 0 .6 9h6.8l.6-9M7.5 8v4m3-4v4" stroke="currentColor" ' +
  'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';

/**
 * Клики, уники и боты; без статистики вместо цифр прочерки, а не нули.
 * @param {import("../types.js").Stats} stats
 * @param {boolean} [unavailable] Keitaro не отдал отчёт
 */
export function statsHtml(stats, unavailable = false) {
  const value = (n) => (unavailable ? "—" : numberFormat.format(n));
  return `
  <dl class="stats" ${unavailable ? 'title="Статистика недоступна"' : ""}>
    <div><dt>Клики</dt><dd>${value(stats.clicks)}</dd></div>
    <div><dt>Уники</dt><dd>${value(stats.unique)}</dd></div>
    <div><dt>Боты</dt><dd>${value(stats.bots)}</dd></div>
  </dl>`;
}

/**
 * Сообщение с заголовком и необязательной кнопкой.
 * @param {{title: string, text: string, action?: {label: string, attrs: string}}} params
 *   `action.attrs` — готовые атрибуты кнопки, например `data-retry="5"`
 */
export function messageHtml({ title, text, action }) {
  const button = action
    ? `<div><button class="btn" type="button" ${action.attrs}>${esc(action.label)}</button></div>`
    : "";
  return `<div class="empty"><strong>${esc(title)}</strong>${esc(text)}${button}</div>`;
}

/**
 * Строка кампании в выпадающем списке поиска.
 * @param {import("../types.js").Campaign} campaign
 */
export function campaignOptionHtml(campaign) {
  const state =
    campaign.state && campaign.state !== "active"
      ? `<span class="badge off opt-state">${esc(campaign.state)}</span>`
      : "";
  return (
    `<span class="opt-id">${campaign.id}</span>` +
    `<span class="opt-name">${esc(campaign.name)}</span>${state}`
  );
}

/**
 * Список последних кампаний для быстрого выбора.
 * @param {import("../types.js").Campaign[]} campaigns
 */
export function campaignListHtml(campaigns) {
  const rows = campaigns
    .map((c) => {
      const state = c.state && c.state !== "active" ? `<span class="badge off">${esc(c.state)}</span>` : "";
      return `
      <li>
        <button type="button" class="campaign-row" data-open="${c.id}">
          <span class="opt-id">${c.id}</span>
          <span class="opt-name">${esc(c.name)}</span>
          ${state}
        </button>
      </li>`;
    })
    .join("");
  return `
    <div class="panel">
      <h2>Последние кампании</h2>
      <p class="muted list-note">Выберите кампанию из списка или найдите другую в поле выше.</p>
      <ul class="campaign-list">${rows}</ul>
    </div>`;
}

/** Чипы фильтров потока. */
function filtersHtml(stream) {
  if (!stream.filters.length) return '<span class="chip">Все посетители</span>';
  return stream.filters
    .map((f) => {
      const label = FILTER_NAMES[f.name] || f.name;
      const mode = FILTER_MODES[f.mode] || f.mode;
      const geo = f.name === "country" ? "geo" : "";
      return `<span class="chip ${geo}">${esc(label)}: ${esc(mode)} ${esc(f.values.join(", "))}</span>`;
    })
    .join("");
}

/** Цель редиректа потока. */
function targetHtml(stream) {
  const target = stream.target;
  if (!target) return '<p class="target">Редирект без адреса</p>';
  const link = /^https?:\/\//i.test(target)
    ? `<a href="${esc(target)}" target="_blank" rel="noopener noreferrer">${esc(target)}</a>`
    : esc(target);
  return `<p class="target">Перенаправляет на ${link}</p>`;
}

/** Строка оффера с долей трафика и кнопкой удаления. */
function offerRowHtml(stream, offer) {
  const last = stream.offers.length === 1 ? "data-last" : "";
  return `
      <li class="offer">
        <div class="offer-name"><span class="offer-id">${offer.offer_id}</span>${esc(offerLabel(offer.offer_id, offer.name))}</div>
        <div class="share" role="img" aria-label="Доля ${offer.share}%"><i style="width:${Math.min(100, offer.share)}%"></i></div>
        <span class="pct">${offer.share}%</span>
        <button class="icon-btn" type="button" data-remove ${last} data-stream="${stream.id}" data-offer="${offer.offer_id}" aria-label="Удалить оффер ${esc(offerLabel(offer.offer_id, offer.name))}">${TRASH_ICON}</button>
      </li>`;
}

/** Офферы потока и поле для добавления нового. */
function offersHtml(stream) {
  const rows =
    stream.offers.map((o) => offerRowHtml(stream, o)).join("") ||
    '<li class="offer"><span class="muted">В потоке нет офферов, посетителям некуда уходить. Добавьте оффер ниже.</span></li>';
  return `
    <ul class="offers">${rows}</ul>
    <div class="add-offer">
      <div class="field">
        <label class="sr-only" for="add-${stream.id}">Добавить оффер в поток ${esc(stream.name)}</label>
        <div class="combo">
          <input id="add-${stream.id}" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="add-list-${stream.id}" autocomplete="off" placeholder="Добавить оффер: ID или название">
          <ul id="add-list-${stream.id}" class="combo-panel" role="listbox" hidden></ul>
        </div>
      </div>
    </div>`;
}

/**
 * Карточка потока с номером по порядку.
 * @param {import("../types.js").Stream} stream
 * @param {number} index
 * @param {boolean} [noStats] статистика недоступна
 */
export function flowHtml(stream, index, noStats = false) {
  const disabled = stream.enabled ? "" : '<span class="badge off">Отключён</span>';
  return `
    <li class="flow ${stream.enabled ? "" : "is-off"}">
      <span class="node" aria-hidden="true">${index + 1}</span>
      <div class="panel">
        <div class="flow-head">
          <div>
            <div class="flow-title"><h3>${esc(stream.name)}</h3>${disabled}</div>
            <div class="chips">${filtersHtml(stream)}</div>
          </div>
          ${statsHtml(stream.stats, noStats)}
        </div>
        ${stream.kind === "offers" ? offersHtml(stream) : targetHtml(stream)}
      </div>
    </li>`;
}

/**
 * Заголовок кампании с итогами и список потоков.
 * @param {import("../types.js").CampaignDetails} details
 */
export function campaignHtml(details) {
  const { campaign, streams, totals } = details;
  const noStats = Boolean(details.stats_error);
  const statsNote = noStats
    ? `<p class="stats-note">${esc(details.stats_error)}: цифры за период не показаны.</p>`
    : "";
  const active = campaign.state === "active";
  const link = campaign.tracking_url
    ? `<div class="link-row"><code>${esc(campaign.tracking_url)}</code>` +
      `<button class="btn small" type="button" data-copy="${esc(campaign.tracking_url)}">Копировать</button></div>`
    : "";
  return `
    <div class="panel campaign-head">
      <div>
        <h2>${esc(campaign.name)}</h2>
        <div class="meta"><span class="badge ${active ? "" : "off"}">${active ? "Активна" : esc(campaign.state || "—")}</span><span>ID ${campaign.id}</span></div>
        ${link}
      </div>
      ${statsHtml(totals, noStats)}
    </div>
    ${statsNote}
    <ol class="flows">${streams.map((s, i) => flowHtml(s, i, noStats)).join("")}</ol>`;
}
