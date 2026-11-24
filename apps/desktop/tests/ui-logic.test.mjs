import test from "node:test";
import assert from "node:assert/strict";
import { effectiveTheme, isTheme, isDensity, themeOptions, densityOptions, uiOptionIds } from "../.ui-tests/theme.js";
import { componentPreviewStates, isComponentPreviewState, previewStateDetails } from "../.ui-tests/component-states.js";
import { appCommands, findCommands, shortcutView } from "../.ui-tests/commands.js";
import { searchWorkspace } from "../.ui-tests/unified-search.js";
import { defaultShortcuts, isShortcutKey, remapShortcut, shortcutForView, shortcutKeys, viewForShortcut } from "../.ui-tests/shortcut-map.js";
import { findHelpArticle, helpArticles, resolveVisibleHelpArticle, searchHelp, helpOptionIds } from "../.ui-tests/help-catalog.js";
import { helpOptionReferences, findHelpOption, optionHelpRoute, resolveOptionHelpRoute, searchHelpOptions, validateHelpOptionReferences } from "../.ui-tests/help-options.js";
import { offlineHelpContract, requestOfflineHelp, wizardIssues, getWizardIssue, getWizardStep, nextWizardStep, guidedTourSteps, getGuidedTourStep, helpFaq, helpGlossary, wikiSourceMappings, helpRoute, resolveHelpRoute, validateOfflineHelpCatalog, localBrokenArticleReport } from "../.ui-tests/help-workflows.js";

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
  assert.equal(appCommands.length, 8);
  assert.equal(new Set(appCommands.map(x => x.id)).size, appCommands.length);
  assert.equal(findCommands("").length, 8);
  assert.equal(findCommands("help")[0].view, "help");
  assert.equal(findCommands("Preferences")[0].view, "settings");
  assert.equal(findCommands("NO-SUCH-COMMAND").length, 0);
  assert.equal(shortcutView("2"), "settings");
  assert.equal(shortcutView("6"), "gallery");
  for (const [key, view] of Object.entries({
    "1": "startup", "2": "settings", "3": "recovery",
    "4": "diagnostics", "5": "workbench", "6": "gallery",
  })) {
    assert.equal(shortcutView(key), view, key);
  }
  for (const key of ["__proto__", "constructor", "toString", "hasOwnProperty",
    "valueOf", "7", "01", "2x", "", "0", "999"]) {
    assert.equal(shortcutView(key), null, key);
  }
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
test("visible help reader stays synchronized with category, query and empty states", () => {
  const privacy = searchHelp("", "Privacy");
  assert.ok(privacy.length > 0);
  assert.equal(resolveVisibleHelpArticle(privacy, "quick-start"), privacy[0]);
  assert.equal(resolveVisibleHelpArticle(privacy, privacy[1].id), privacy[1]);
  const search = searchHelp("theme");
  assert.equal(resolveVisibleHelpArticle(search, "quick-start"), search[0]);
  assert.equal(resolveVisibleHelpArticle([], "quick-start"), undefined);
  assert.equal(resolveVisibleHelpArticle(search, "__proto__"), search[0]);
});

test("bounded search inputs cannot invent results or throw", () => {
  const overlong = "a".repeat(10000);
  assert.doesNotThrow(() => findCommands(overlong));
  assert.doesNotThrow(() => searchHelp(overlong));
  assert.equal(findCommands(overlong).length, 0);
  assert.equal(searchHelp(overlong).length, 0);
});


test("M02 shortcut mapping swaps collisions, preserves navigation and reserves F1", () => {
  assert.deepEqual(shortcutKeys, ["1", "2", "3", "4", "5", "6"]);
  assert.equal(shortcutForView("help", defaultShortcuts), null);
  for (const [key, destination] of Object.entries(defaultShortcuts)) {
    assert.equal(viewForShortcut(key, defaultShortcuts), destination);
    assert.equal(shortcutForView(destination, defaultShortcuts), key);
  }
  let customized = remapShortcut(defaultShortcuts, "workbench", "2");
  assert.equal(customized["2"], "workbench");
  assert.equal(customized["5"], "settings");
  assert.deepEqual(new Set(Object.values(customized)).size, 6);
  assert.equal(viewForShortcut("2", customized), "workbench");
  assert.equal(shortcutForView("settings", customized), "5");
  assert.equal(findCommands("Ctrl+2", customized)[0].view, "workbench");
  assert.equal(findCommands("Ctrl+5", customized)[0].view, "settings");
  assert.equal(remapShortcut(customized, "workbench", "2"), customized);
  assert.equal(remapShortcut(customized, "workbench", "F1"), customized);
  assert.equal(remapShortcut(customized, "workbench", "__proto__"), customized);
  for (const key of ["0", "F1", "7", "", "01", "__proto__", null]) {
    assert.equal(isShortcutKey(key), false);
    assert.equal(viewForShortcut(String(key), customized), null);
  }
  customized = remapShortcut(customized, "workbench", "5");
  assert.deepEqual(customized, defaultShortcuts);
  assert.deepEqual(remapShortcut(customized, "gallery", "1"), {
    ...defaultShortcuts, "1": "gallery", "6": "startup",
  });
});


test("M19 offline catalog has a pinned schema, version and valid internal references", () => {
  assert.equal(offlineHelpContract.schema_version, 1);
  assert.match(offlineHelpContract.catalog_version, /^2026\.\d+-p02$/);
  assert.equal(offlineHelpContract.offline_only, true);
  assert.equal(offlineHelpContract.publication, "source-preview-not-published");
  assert.equal(offlineHelpContract.article_count, helpArticles.length);
  assert.ok(helpArticles.length >= 12);
  assert.equal(offlineHelpContract.m19_option_count, 8);
  assert.deepEqual(validateOfflineHelpCatalog(), []);
});

test("M19 typed internal Help routes never allow traversal, prototypes or external links", () => {
  for (const item of helpArticles) {
    const route = helpRoute(item.id);
    assert.equal(route, "help://article/" + item.id);
    assert.equal(resolveHelpRoute(route), item.id);
  }
  for (const input of [
    "https://github.com", "file:///etc/passwd", "help://article/../../secrets",
    "help://wiki/M02", "help://article/__proto__", "help://article/constructor",
    "help://article/%2e%2e%2f", "help://article/", "help://article/quick-start?x=1",
    "help://article/quick-start#top", "help://article/QUICK-START",
  ]) assert.equal(resolveHelpRoute(input), null, input);
  assert.equal(helpRoute("constructor"), null);
});

test("M19 recovery wizard has functional bounded step transitions and article targets", () => {
  assert.equal(wizardIssues.length, 4);
  const ids = new Set(wizardIssues.map(item => item.id));
  assert.equal(ids.size, wizardIssues.length);
  for (const issue of wizardIssues) {
    assert.equal(getWizardIssue(issue.id), issue);
    assert.ok(issue.steps.length >= 3);
    for (let i = 0; i < issue.steps.length; i++) {
      const step = getWizardStep(issue.id, i);
      assert.equal(step, issue.steps[i]);
      assert.ok(findHelpArticle(step.articleId));
      assert.equal(nextWizardStep(issue.id, i), i + 1 < issue.steps.length ? i + 1 : null);
    }
    assert.equal(getWizardStep(issue.id, -1), null);
    assert.equal(getWizardStep(issue.id, 1000), null);
    assert.equal(nextWizardStep(issue.id, -1), null);
    assert.equal(nextWizardStep(issue.id, 1.5), null);
  }
  assert.equal(getWizardIssue("__proto__"), undefined);
  assert.equal(getWizardStep("not-real", 0), null);
  assert.equal(nextWizardStep("not-real", 0), null);
});

test("M19 FAQ, glossary and source-only Wiki mappings are genuinely linked", () => {
  assert.ok(helpFaq.length >= 5);
  assert.ok(helpGlossary.length >= 6);
  assert.equal(new Set(helpFaq.map(x => x.id)).size, helpFaq.length);
  assert.equal(new Set(helpGlossary.map(x => x.term)).size, helpGlossary.length);
  for (const item of helpFaq) assert.ok(findHelpArticle(item.articleId), item.id);
  assert.deepEqual(wikiSourceMappings.map(x => x.id), ["M02", "M19", "M26"]);
  for (const map of wikiSourceMappings) {
    assert.match(map.source, /^docs\/wiki\/pages\/[A-Za-z0-9-]+\.md$/);
    assert.ok(findHelpArticle(map.articleId));
    assert.equal(map.published, false);
  }
});

test("M19 local report includes only allowlisted metadata, never user content or transmission", () => {
  const report = localBrokenArticleReport("native-troubleshooting", "broken-reference");
  assert.ok(report);
  assert.deepEqual(JSON.parse(report), {
    schema_version: 1, module: "M19", catalog_version: offlineHelpContract.catalog_version,
    article_id: "native-troubleshooting", reason: "broken-reference", transmitted: false,
  });
  assert.equal(localBrokenArticleReport("__proto__", "broken-reference"), null);
  assert.equal(localBrokenArticleReport("quick-start", "invalid"), null);
  assert.ok(!report.includes("http://") && !report.includes("https://"));
});

test("M19 search resolves all new functional guides completely offline", () => {
  for (const [query, id] of [
    ["rail sidebar", "navigation"], ["wizard recover", "wizard-guide"],
    ["glossary definition", "faq-glossary"], ["wiki broken", "wiki-mapping"],
    ["report issue", "report-guide"],
  ]) assert.ok(searchHelp(query).some(x => x.id === id), query);
  assert.equal(searchHelp("M19-OPT-07")[0].id, "report-guide");
  assert.equal(searchHelp("M19-OPT-06")[0].id, "wiki-mapping");
});


test("M19 versioned local search rejects stale, malformed and oversized requests", () => {
  const request = {
    schema_version: 1, catalog_version: offlineHelpContract.catalog_version,
    query: "  WiKi  ", category: "All", limit: 3,
  };
  const response = requestOfflineHelp(request);
  assert.equal(response.ok, true);
  assert.equal(response.schema_version, 1);
  assert.equal(response.catalog_version, offlineHelpContract.catalog_version);
  assert.ok(response.matches.length <= 3);
  assert.ok(response.total >= response.matches.length);
  assert.ok(response.matches.some(item => item.id === "wiki-mapping"));
  for (const [invalid, code] of [
    [null, "M19-SCHEMA-001"],
    [[], "M19-SCHEMA-001"],
    [{ ...request, schema_version: 2 }, "M19-SCHEMA-001"],
    [{ ...request, catalog_version: "stale" }, "M19-CATALOG-409"],
    [{ ...request, query: "x".repeat(121) }, "M19-QUERY-400"],
    [{ ...request, category: "Untrusted" }, "M19-QUERY-400"],
    [{ ...request, limit: 0 }, "M19-QUERY-400"],
    [{ ...request, limit: 100 }, "M19-QUERY-400"],
    [{ ...request, limit: NaN }, "M19-QUERY-400"],
    [{ ...request, query: {} }, "M19-QUERY-400"],
  ]) {
    const failure = requestOfflineHelp(invalid);
    assert.equal(failure.ok, false);
    assert.equal(failure.code, code);
  }
  assert.deepEqual(requestOfflineHelp({ ...request, category: "Troubleshooting", limit: 50 }).matches
    .every(article => article.category === "Troubleshooting"), true);
});

test("M02 interactive state explorer is deterministic, complete and local-only", () => {
  assert.deepEqual(componentPreviewStates.map(x => x.id), ["ready", "loading", "empty", "error", "offline"]);
  assert.equal(new Set(componentPreviewStates.map(x => x.id)).size, 5);
  for (const item of componentPreviewStates) {
    assert.equal(isComponentPreviewState(item.id), true);
    assert.deepEqual(previewStateDetails(item.id), item);
    assert.ok(item.title && item.detail && item.remedy);
  }
  for (const invalid of [null, {}, "", "retrying", "__proto__", "READY", 1]) {
    assert.equal(isComponentPreviewState(invalid), false);
  }
  assert.equal(previewStateDetails("unknown").id, "ready");
});

test("M19 guided onboarding stays bounded and links only real offline articles", () => {
  assert.equal(guidedTourSteps.length, 5);
  assert.equal(new Set(guidedTourSteps.map(x => x.title)).size, 5);
  for (let i = 0; i < guidedTourSteps.length; i++) {
    const step = getGuidedTourStep(i);
    assert.equal(step, guidedTourSteps[i]);
    assert.ok(step.title && step.instruction && findHelpArticle(step.articleId));
  }
  for (const invalid of [-1, 1.5, 5, 100, NaN]) assert.equal(getGuidedTourStep(invalid), null);
  assert.deepEqual(validateOfflineHelpCatalog(), []);
});

test("M02/M19 all sixteen option guides resolve locally and fail closed", () => {
  assert.deepEqual(validateHelpOptionReferences(), []);
  assert.equal(helpOptionReferences.length, 16);
  assert.equal(new Set(helpOptionReferences.map(item => item.id)).size, 16);
  for (const item of helpOptionReferences) {
    assert.equal(findHelpOption(item.id), item);
    assert.deepEqual(resolveOptionHelpRoute(optionHelpRoute(item.id)), item);
    assert.ok(findHelpArticle(item.articleId));
    assert.ok(item.defaultState && item.interaction && item.limits && item.recovery);
  }
  for (const invalid of [
    "https://evil.test", "help://option/M02-OPT-00",
    "help://option/M19-OPT-09", "help://option/../../config",
    "help://option/M02-OPT-01?x=1", "help://option/M02-OPT-01/",
    "HELP://option/M19-OPT-01", "__proto__", "",
  ]) assert.equal(resolveOptionHelpRoute(invalid), null);
  assert.equal(searchHelpOptions("", "M02").length, 8);
  assert.equal(searchHelpOptions("", "M19").length, 8);
  assert.ok(searchHelpOptions("theme").some(x => x.id === "M02-OPT-02"));
  assert.ok(searchHelpOptions("theme","M02").some(x => x.id === "M02-OPT-02"));
  assert.ok(searchHelpOptions("glossary","M19").some(x => x.id === "M19-OPT-04"));
  assert.equal(searchHelpOptions("theme","M19").every(x => x.module === "M19"), true);
  assert.deepEqual(searchHelpOptions("unmatched-token-zzzzz"), []);
});

test("unified command palette discovers bundled articles and exact M02/M19 option references", () => {
  const initial = searchWorkspace("");
  assert.equal(initial.length, 8);
  assert.ok(initial.every(item => item.kind === "view" && item.destination.kind === "view"));
  const theme = searchWorkspace("theme");
  assert.ok(theme.some(item => item.kind === "article" && item.destination.articleId === "appearance"));
  assert.ok(theme.some(item => item.kind === "option" && item.destination.optionId === "M02-OPT-02"));
  assert.equal(searchWorkspace("M19-OPT-06")[0].destination.optionId, "M19-OPT-06");
  assert.equal(searchWorkspace("Data and diagnostics boundaries")[0].destination.articleId, "privacy");
  assert.ok(searchWorkspace("offline").some(item => item.kind === "article"));
  assert.equal(searchWorkspace("NOT_A_REAL_ROUTE_13283").length, 0);
  assert.ok(searchWorkspace("theme").length <= 20);
  assert.equal(new Set(theme.map(item => item.id)).size, theme.length);
});
test("unified search preserves remaps, ignores malformed keys and never invents destinations", () => {
  const custom = remapShortcut(defaultShortcuts, "workbench", "2");
  assert.equal(searchWorkspace("Ctrl+2", custom)[0].destination.view, "workbench");
  assert.equal(searchWorkspace("Ctrl+5", custom)[0].destination.view, "settings");
  assert.ok(searchWorkspace("a".repeat(10000)).length <= 20);
  for (const entry of searchWorkspace("help")) {
    if (entry.destination.kind === "view") {
      assert.ok(appCommands.some(command => command.view === entry.destination.view));
    } else if (entry.destination.kind === "article") {
      assert.ok(findHelpArticle(entry.destination.articleId));
    } else {
      assert.ok(findHelpOption(entry.destination.optionId));
      assert.ok(resolveOptionHelpRoute(optionHelpRoute(entry.destination.optionId)));
    }
  }
  assert.equal(searchWorkspace("__proto__").length, 0);
});

import { changeNotices, filterChangeNotices, changeAvailability, changeServicePanels, isChangeServiceSection } from "../.ui-tests/change-center.js";
test("M26 bundled limitations are not released changes and filters remain local", () => {
  assert.equal(findCommands("Changelog")[0].view, "changelog");
  assert.equal(searchWorkspace("Changelog")[0].keys, "VIEW");
  assert.equal(shortcutForView("changelog", defaultShortcuts), null);
  assert.equal(findHelpArticle("change-history").id, "change-history");
  assert.ok(wikiSourceMappings.some(item => item.id === "M26" && item.published === false));
  assert.equal(filterChangeNotices("", "All").length, changeNotices.length);
  assert.ok(changeNotices.every(item => item.kind === "capability-limitation"));
  assert.ok(filterChangeNotices("backup", "M23").length > 0);
  assert.equal(filterChangeNotices("backup", "M25").length, 0);
  assert.equal(filterChangeNotices("no-such-notice", "All").length, 0);
  for (const transport of ["pending","connected","unavailable","preview"]) {
    const state = changeAvailability(transport);
    assert.equal(state.verifiedReleaseCount, 0);
    assert.equal(state.liveIssuesAvailable, false);
    assert.equal(state.releaseFeedAvailable, false);
  }
  assert.equal(changeAvailability("pending").status, "Checking local runtime");
  assert.equal(changeAvailability("unavailable").status, "Local runtime unavailable");
});

test("M26 service boundaries are explicit and never imply authorization", () => {
  assert.deepEqual(Object.keys(changeServicePanels), ["audit","preferences","migration"]);
  for (const [key,panel] of Object.entries(changeServicePanels)) {
    assert.equal(isChangeServiceSection(key),true);
    assert.ok(panel.heading.length > 0);
    assert.equal(panel.actions.length,2);
    assert.ok(panel.actions.every(action=>action.label && action.reason));
  }
  for (const key of ["releases","issues","versions","modules","__proto__","constructor",""]) {
    assert.equal(isChangeServiceSection(key),false);
  }
  for (const transport of ["pending","connected","unavailable","preview"]) {
    assert.equal(changeAvailability(transport).releaseFeedAvailable,false);
    assert.equal(changeAvailability(transport).liveIssuesAvailable,false);
  }
});
