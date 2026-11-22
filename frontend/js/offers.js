/** Поиск офферов и их отображение в выпадающих списках. */

import { api } from "./api.js";
import { esc } from "./dom.js";
import { offerLabel, searchTerm } from "./format.js";

/**
 * Ищет офферы по ID или названию.
 * @param {string} query
 * @returns {Promise<import("./types.js").Offer[]>}
 */
export const searchOffers = (query) => api(`/offers?q=${encodeURIComponent(searchTerm(query))}`);

/**
 * HTML строки оффера в списке подсказок.
 * @param {import("./types.js").Offer} offer
 */
export function offerOptionHtml(offer) {
  const state =
    offer.state && offer.state !== "active"
      ? `<span class="badge off opt-state">${esc(offer.state)}</span>`
      : "";
  return (
    `<span class="opt-id">${offer.id}</span>` +
    `<span class="opt-name">${esc(offerLabel(offer.id, offer.name))}</span>${state}`
  );
}
