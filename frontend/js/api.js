/** Клиент HTTP API приложения. */

/**
 * Выполняет запрос к API и возвращает JSON.
 * @param {string} path путь без префикса `/api`
 * @param {{method?: string, body?: object}} [options]
 * @throws {Error} с текстом ошибки сервера
 */
export async function api(path, { method = "GET", body } = {}) {
  let res;
  try {
    res = await fetch(`/api${path}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Нет связи с сервером. Проверьте, что приложение запущено.");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new Error(data?.error?.message || `Ошибка ${res.status}`);
  }
  return res.json();
}
