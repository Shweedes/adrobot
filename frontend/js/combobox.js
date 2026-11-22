/** Поле с автокомплитом: поиск с задержкой, клавиатура, ARIA. */

import { $, debounce, esc } from "./dom.js";

const SEARCH_DELAY_MS = 180;

/**
 * Подключает автокомплит к полю ввода и списку подсказок.
 *
 * Подсказка выбирается по `mousedown` с `preventDefault`: поле не теряет фокус,
 * и `blur` не закрывает список раньше клика.
 * @template T
 * @param {object} options
 * @param {HTMLInputElement} options.input
 * @param {HTMLElement} options.panel список подсказок
 * @param {(query: string) => Promise<T[]>} options.search
 * @param {(item: T) => string} options.renderItem HTML содержимого подсказки
 * @param {(item: T) => void} options.onPick
 */
export function createCombobox({ input, panel, search, renderItem, onPick }) {
  let items = [];
  let active = -1;
  let requestId = 0;

  const open = () => {
    panel.hidden = false;
    input.setAttribute("aria-expanded", "true");
  };

  const close = () => {
    panel.hidden = true;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  };

  const paint = () => {
    panel.innerHTML = items.length
      ? items
          .map(
            (item, i) =>
              `<li role="option" id="${panel.id}-${i}" data-i="${i}" aria-selected="${i === active}">` +
              `${renderItem(item)}</li>`
          )
          .join("")
      : '<li class="combo-empty">Ничего не найдено</li>';
    if (active >= 0) {
      input.setAttribute("aria-activedescendant", `${panel.id}-${active}`);
      $(`#${panel.id}-${active}`)?.scrollIntoView({ block: "nearest" });
    }
  };

  const run = async () => {
    const mine = ++requestId;
    try {
      const result = await search(input.value.trim());
      if (mine !== requestId) return;
      items = result;
      active = items.length ? 0 : -1;
      paint();
    } catch (error) {
      if (mine !== requestId) return;
      items = [];
      panel.innerHTML = `<li class="combo-empty">${esc(error.message)}</li>`;
    }
    open();
  };

  const pick = (index) => {
    const item = items[index];
    if (!item) return;
    close();
    onPick(item);
  };

  input.addEventListener("input", debounce(run, SEARCH_DELAY_MS));
  input.addEventListener("focus", () => {
    input.select();
    run();
  });
  input.addEventListener("blur", close);
  input.addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (panel.hidden) return run();
      if (!items.length) return;
      active = (active + (event.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
      paint();
    } else if (event.key === "Enter" && !panel.hidden && active >= 0) {
      event.preventDefault();
      pick(active);
    } else if (event.key === "Escape") {
      close();
    }
  });
  panel.addEventListener("mousedown", (event) => {
    const option = event.target.closest("[data-i]");
    if (!option) return;
    event.preventDefault();
    pick(Number(option.dataset.i));
  });
}
