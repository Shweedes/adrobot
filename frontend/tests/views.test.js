import assert from "node:assert/strict";
import test from "node:test";

import { numberFormat } from "../js/dom.js";
import { createdHtml, routeHtml } from "../js/create/view.js";
import { campaignHtml, campaignListHtml, flowHtml, messageHtml } from "../js/editor/view.js";

const stats = { clicks: 0, unique: 0, bots: 0 };

const geoStream = {
  id: 1334269,
  name: "Geo AU",
  position: 1,
  enabled: true,
  kind: "redirect",
  target: "https://google.com",
  filters: [{ name: "country", mode: "accept", values: ["AU"] }],
  offers: [],
  stats,
};

const offerStream = {
  id: 1334270,
  name: "Offer 18813",
  position: 2,
  enabled: true,
  kind: "offers",
  target: null,
  filters: [],
  offers: [
    { offer_id: 18813, name: "18813 Flexacil [JOINT-PE] [vsl es -] ReactJs v4", share: 100, state: "active" },
  ],
  stats: { clicks: 1234, unique: 20, bots: 2 },
};

const details = {
  campaign: {
    id: 217261,
    name: "test_olekhnovich_campaign1235453643819",
    state: "active",
    alias: "EmQ9zA",
    tracking_url: "https://kylovoa.com/EmQ9zA",
  },
  streams: [geoStream, offerStream],
  totals: { clicks: 1234, unique: 20, bots: 2 },
  range: "today",
};

test("campaignHtml показывает фильтр, редирект, оффер и ссылку кампании", () => {
  const html = campaignHtml(details);
  assert.match(html, /Страны: принимать AU/);
  assert.match(html, /Перенаправляет на <a href="https:\/\/google.com"/);
  assert.match(html, /data-copy="https:\/\/kylovoa.com\/EmQ9zA"/);
  assert.match(html, /Активна/);
});

test("ID оффера показывается один раз", () => {
  const html = flowHtml(offerStream, 1);
  assert.match(html, />18813<\/span>Flexacil/);
  assert.doesNotMatch(html, /18813 Flexacil/);
  assert.match(html, /100%/);
});

test("числа форматируются в русской локали", () => {
  assert.ok(flowHtml(offerStream, 1).includes(numberFormat.format(1234)));
});

test("единственный оффер помечается data-last, при нескольких метки нет", () => {
  assert.match(flowHtml(offerStream, 1), /data-last/);
  const two = {
    ...offerStream,
    offers: [
      { offer_id: 1, name: "a", share: 50, state: "active" },
      { offer_id: 2, name: "b", share: 50, state: "active" },
    ],
  };
  assert.doesNotMatch(flowHtml(two, 1), /data-last/);
});

test("пустой поток предлагает добавить оффер", () => {
  const html = flowHtml({ ...offerStream, offers: [] }, 1);
  assert.match(html, /В потоке нет офферов/);
  assert.match(html, /id="add-1334270"/);
});

test("отключённый поток помечается", () => {
  assert.match(flowHtml({ ...geoStream, enabled: false }, 0), /Отключён/);
});

test("HTML из данных экранируется", () => {
  const html = campaignHtml({
    ...details,
    campaign: { ...details.campaign, name: "<script>alert(1)</script>" },
  });
  assert.doesNotMatch(html, /<script>/);
  assert.match(html, /&lt;script&gt;/);
});

test("campaignListHtml содержит кнопки открытия кампаний", () => {
  const html = campaignListHtml([{ id: 5, name: "test_x", state: "active" }]);
  assert.match(html, /data-open="5"/);
});

test("messageHtml экранирует текст и добавляет кнопку", () => {
  const html = messageHtml({
    title: "Ошибка",
    text: "<b>x</b>",
    action: { label: "Повторить", attrs: 'data-retry="5"' },
  });
  assert.match(html, /&lt;b&gt;x&lt;\/b&gt;/);
  assert.match(html, /data-retry="5"/);
});

const meta = { prefix: "test_", domain: "kylovoa.com", group: "G", source: "S", redirect_url: "https://google.com" };

test("routeHtml без данных подсказывает, что заполнить", () => {
  const html = routeHtml({ geo: [], offer: null, meta });
  assert.match(html, /Страны пока не указаны/);
  assert.match(html, /Оффер пока не выбран/);
  assert.match(html, /Перенаправляем на google.com/);
});

test("routeHtml показывает страны и оффер без дубля ID", () => {
  const html = routeHtml({
    geo: ["AU", "MX"],
    offer: { id: 18813, name: "18813 Flexacil", state: "active" },
    meta,
  });
  assert.match(html, /chip geo">AU/);
  assert.match(html, /chip geo">MX/);
  assert.match(html, /Оффер 18813: Flexacil/);
});

test("createdHtml содержит ссылку, копирование и открытие в редакторе", () => {
  const html = createdHtml({ id: 9, name: "test_a", geo: ["AU"], tracking_url: "https://h/x" });
  assert.match(html, /data-copy="https:\/\/h\/x"/);
  assert.match(html, /data-open="9"/);
  assert.match(html, /data-reset/);
});
