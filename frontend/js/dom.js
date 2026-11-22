/** Общие DOM-хелперы: выборка, экранирование, уведомления, буфер обмена. */

const HTML_ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
const TOAST_MS = { info: 3500, ok: 3500, error: 7000 };

/** Находит первый элемент по селектору. */
export const $ = (selector, root = document) => root.querySelector(selector);

/** Экранирует значение для вставки в HTML. */
export const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => HTML_ESCAPES[c]);

/** Форматирует числа в русской локали. */
export const numberFormat = new Intl.NumberFormat("ru-RU");

/**
 * Откладывает вызов `fn` до паузы в `ms` мс.
 * @param {Function} fn
 * @param {number} ms
 */
export function debounce(fn, ms) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}

/**
 * Показывает уведомление.
 * @param {string} message
 * @param {"info"|"ok"|"error"} [kind]
 */
export function toast(message, kind = "info") {
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  el.textContent = message;
  $("#toasts").append(el);
  setTimeout(() => el.remove(), TOAST_MS[kind]);
}

/** Копирует текст в буфер обмена и сообщает результат. */
export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    toast("Ссылка скопирована", "ok");
  } catch {
    toast("Не удалось скопировать: выделите ссылку вручную", "error");
  }
}
