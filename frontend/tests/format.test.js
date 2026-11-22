import assert from "node:assert/strict";
import test from "node:test";

import { hostOf, offerLabel, searchTerm } from "../js/format.js";
import { parseGeo } from "../js/geo.js";

test("offerLabel убирает ID из начала названия", () => {
  assert.equal(
    offerLabel(18813, "18813 Flexacil [JOINT-PE] [vsl es -] ReactJs v4"),
    "Flexacil [JOINT-PE] [vsl es -] ReactJs v4"
  );
});

test("offerLabel не трогает название, где ID не в начале", () => {
  assert.equal(offerLabel(5, "5th avenue offer"), "5th avenue offer");
  assert.equal(offerLabel(7, "Offer 7"), "Offer 7");
});

test("searchTerm превращает выбранное значение в пустой запрос", () => {
  assert.equal(searchTerm("18813 · Flexacil"), "");
  assert.equal(searchTerm("flex"), "flex");
});

test("hostOf возвращает хост или исходную строку", () => {
  assert.equal(hostOf("https://google.com/path"), "google.com");
  assert.equal(hostOf("не url"), "не url");
});

test("parseGeo нормализует коды и находит неверные", () => {
  assert.deepEqual(parseGeo(" au, MX;ro  au "), { codes: ["AU", "MX", "RO"], invalid: [] });
  assert.deepEqual(parseGeo("AUS, 1"), { codes: ["AUS", "1"], invalid: ["AUS", "1"] });
  assert.deepEqual(parseGeo(""), { codes: [], invalid: [] });
});
