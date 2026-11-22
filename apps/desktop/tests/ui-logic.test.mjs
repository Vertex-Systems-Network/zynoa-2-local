import test from "node:test";
import assert from "node:assert/strict";
import { effectiveTheme, isTheme, isDensity, themeOptions, densityOptions, uiOptionIds } from "../.ui-tests/theme.js";
import { appCommands, findCommands, shortcutView } from "../.ui-tests/commands.js";
import { findHelpArticle, helpArticles, searchHelp, helpOptionIds } from "../.ui-tests/help-catalog.js";

test("theme defaults follow operating system and never coerce unknown values", () => {
  assert.equal(effectiveTheme("system", true), "dark");
  assert.equal(effectiveTheme("system", false), "light");
  assert.equal(effectiveTheme("dark", false), "dark");
  assert.equal(effectiveTheme("light", true), "light");
  for (const item of ["system", "dark", "light"]) assert.equal(isTheme(item), true);
  for (const item of [null, "", "automatic", {}, 1, false]) assert.equal(isTheme(item), false);
  assert.deepEqual(themeOptions.map(x => x.value), ["system", "dark", "light"]);
});
test("density is a strict allowlist and options have unique IDs", () => {
  assert.deepEqual(densityOptions.map(x => x.value), ["comfortable", "compact"]);
  assert.equal(isDensity("compact"), true);
  assert.equal(isDensity("small"), false);
  assert.equal(new Set(uiOptionIds).size, 8);
  assert.equal(new Set(helpOptionIds).size, 8);
});
test("command palette only returns fixed application navigation commands", () => {
  assert.equal(appCommands.length, 7);
  assert.equal(new Set(appCommands.map(x => x.id)).size, appCommands.length);
  assert.equal(findCommands("").length, 7);
  assert.equal(findCommands("help")[0].view, "help");
  assert.equal(findCommands("Preferences")[0].view, "settings");
  assert.equal(findCommands("NO-SUCH-COMMAND").length, 0);
  assert.equal(shortcutView("2"), "settings");
  assert.equal(shortcutView("6"), "gallery");
  assert.equal(shortcutView("__proto__"), null);
  for (const cmd of findCommands("gO")) assert.ok(appCommands.includes(cmd));
});
test("help catalog is deterministic, unique and internally linked", () => {
  assert.ok(helpArticles.length >= 6);
  const ids = new Set(helpArticles.map(x => x.id));
  assert.equal(ids.size, helpArticles.length);
  for (const article of helpArticles) {
    assert.ok(article.title.trim() && article.summary.trim());
    assert.ok(article.sections.every(x => x.heading.trim() && x.paragraphs.length));
    for (const related of article.related) assert.ok(ids.has(related), related);
    assert.equal(findHelpArticle(article.id), article);
  }
  assert.equal(findHelpArticle("no-such-topic"), undefined);
});
test("offline help search and category filter work without network", () => {
  assert.equal(searchHelp("  ").length, helpArticles.length);
  assert.ok(searchHelp("theme").some(x => x.id === "appearance"));
  assert.equal(searchHelp("totally-unmatched-phrase").length, 0);
  assert.deepEqual(searchHelp("", "Privacy").map(x => x.category), ["Privacy", "Privacy"]);
  assert.equal(searchHelp("M02-OPT-02")[0].id, "appearance");
  assert.equal(searchHelp("windows native").some(x => x.id === "native-troubleshooting"), true);
  assert.ok(searchHelp("HELP").every(x => x.id && x.title));
});
test("bounded search inputs cannot invent results or throw", () => {
  const overlong = "a".repeat(10000);
  assert.doesNotThrow(() => findCommands(overlong));
  assert.doesNotThrow(() => searchHelp(overlong));
  assert.equal(findCommands(overlong).length, 0);
  assert.equal(searchHelp(overlong).length, 0);
});
