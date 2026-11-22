/** Чистые функции форматирования значений для интерфейса. */

/** Убирает ID из начала названия оффера: Keitaro уже кладёт его в название. */
export const offerLabel = (id, name) => String(name).replace(new RegExp(`^${id}\\s+`), "");

/** Превращает выбранное значение вида «ID · название» в пустой запрос поиска. */
export const searchTerm = (value) => (value.includes(" · ") ? "" : value);

/** Возвращает хост URL или исходную строку, если это не URL. */
export function hostOf(url) {
  try {
    return new URL(url).host;
  } catch {
    return url;
  }
}
