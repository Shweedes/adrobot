/** HTML-шаблоны экрана создания кампании. */

import { esc } from "../dom.js";
import { hostOf, offerLabel } from "../format.js";

/**
 * Превью маршрута трафика.
 * @param {{geo: string[], offer: import("../types.js").Offer|null,
 *   meta: import("../types.js").Meta}} params `geo` — только корректные коды
 */
export function routeHtml({ geo, offer, meta }) {
  const countries = geo.length
    ? `<span class="chips">${geo.map((c) => `<span class="chip geo">${esc(c)}</span>`).join("")}</span>`
    : '<span class="muted">Страны пока не указаны</span>';
  const offerText = offer
    ? `Оффер ${esc(offer.id)}: ${esc(offerLabel(offer.id, offer.name))}`
    : '<span class="muted">Оффер пока не выбран</span>';
  return `
    <li class="hop is-done">
      <h3>Переход по ссылке кампании</h3>
      <p>${esc(meta.domain)}/…</p>
    </li>
    <li class="hop is-geo">
      <h3>Поток 1: выбранные страны</h3>
      <p>${countries}</p>
      <p>Перенаправляем на ${esc(hostOf(meta.redirect_url))}</p>
    </li>
    <li class="hop">
      <h3>Поток 2: все остальные</h3>
      <p>${offerText}</p>
    </li>`;
}

/**
 * Настройки, которые подставляются в кампанию автоматически.
 * @param {import("../types.js").Meta} meta
 */
export function autoSettingsHtml(meta) {
  return `
    <dt>Домен</dt><dd>${esc(meta.domain)}</dd>
    <dt>Группа</dt><dd>${esc(meta.group)}</dd>
    <dt>Источник</dt><dd>${esc(meta.source)}</dd>
    <dt>Ротация</dt><dd>По позиции</dd>`;
}

/**
 * Панель «Кампания создана».
 * @param {import("../types.js").Campaign & {geo: string[]}} campaign
 */
export function createdHtml(campaign) {
  const link = campaign.tracking_url
    ? `<div class="link-row"><code>${esc(campaign.tracking_url)}</code>` +
      `<button class="btn small" type="button" data-copy="${esc(campaign.tracking_url)}">Копировать ссылку</button></div>`
    : "";
  return `
    <div class="panel success">
      <h2>Кампания создана</h2>
      <p>${esc(campaign.name)}, ID ${campaign.id}. Потоков: 2. Гео: ${esc(campaign.geo.join(", "))}.</p>
      ${link}
      <div class="actions">
        <button class="btn primary" type="button" data-open="${campaign.id}">Открыть в редакторе</button>
        <button class="btn" type="button" data-reset>Создать ещё</button>
      </div>
    </div>`;
}
