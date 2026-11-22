/** Разбор кодов стран из поля формы. */

const ISO2 = /^[A-Z]{2}$/;

/**
 * Разбирает строку кодов в уникальные коды верхнего регистра.
 * @param {string} raw например `"au, MX;ro"`
 * @returns {{codes: string[], invalid: string[]}} все коды и среди них неверные
 */
export function parseGeo(raw) {
  const codes = [...new Set(raw.split(/[\s,;]+/).map((s) => s.trim().toUpperCase()).filter(Boolean))];
  return { codes, invalid: codes.filter((code) => !ISO2.test(code)) };
}
