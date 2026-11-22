import assert from "node:assert/strict";
import test from "node:test";

test("контроллеры экспортируют то, что импортирует main.js", async () => {
  const editor = await import("../js/editor/controller.js");
  const create = await import("../js/create/controller.js");
  for (const name of ["currentCampaignId", "initEditor", "openCampaign", "showCampaignList"]) {
    assert.equal(typeof editor[name], "function", `editor/controller.js: нет ${name}`);
  }
  assert.equal(typeof create.initCreate, "function");
});
