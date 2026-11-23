/** M02/M19 option-by-option offline reference. No HTML, network or persisted state. */
import { findHelpArticle, helpOptionIds } from "./help-catalog.js";
import { uiOptionIds } from "./theme.js";

export type HelpOptionAvailability = "session" | "preview-only" | "built-in" | "partial";
export type HelpOptionReference = Readonly<{
  id: string; module: "M02" | "M19"; title: string; articleId: string;
  defaultState: string; interaction: string; limits: string; recovery: string;
  availability: HelpOptionAvailability;
}>;
export const helpOptionReferences: readonly HelpOptionReference[] = [
  {
    "id": "M02-OPT-01",
    "module": "M02",
    "title": "Navigation density",
    "articleId": "appearance",
    "defaultState": "Comfortable",
    "interaction": "Switch to Compact in Preferences, or restore defaults",
    "limits": "Changes spacing in the current window only",
    "recovery": "Use Restore interface defaults; no saved preference",
    "availability": "session"
  },
  {
    "id": "M02-OPT-02",
    "module": "M02",
    "title": "Light / Dark / System appearance",
    "articleId": "appearance",
    "defaultState": "Follow system",
    "interaction": "Select Follow system, Dark or Light in Preferences",
    "limits": "System tracks Windows; manual override resets on restart",
    "recovery": "Choose Follow system to undo; no OS settings are written",
    "availability": "session"
  },
  {
    "id": "M02-OPT-03",
    "module": "M02",
    "title": "Compact properties preview",
    "articleId": "navigation",
    "defaultState": "Comfortable preview rows",
    "interaction": "Open Workbench → Layout controls, toggle Compact on/off",
    "limits": "Illustrative property rows, not a real project inspector",
    "recovery": "Toggle again; no user project was edited",
    "availability": "preview-only"
  },
  {
    "id": "M02-OPT-04",
    "module": "M02",
    "title": "Ctrl+1–6 navigation mapping",
    "articleId": "commands",
    "defaultState": "Fixed 1–6 assignments",
    "interaction": "Open Workbench → Keyboard guide; assign or reset navigation keys",
    "limits": "Collision-safe swaps, session only; F1 and Ctrl+Shift+P reserved",
    "recovery": "Restore default shortcuts in Workbench",
    "availability": "session"
  },
  {
    "id": "M02-OPT-05",
    "module": "M02",
    "title": "Command palette search",
    "articleId": "commands",
    "defaultState": "Closed, empty query",
    "interaction": "Press Ctrl+Shift+P, type a view, select with arrows and Enter",
    "limits": "Local allowlisted navigation only; maximum 100 characters",
    "recovery": "Press Escape or close; no arbitrary scripts execute",
    "availability": "session"
  },
  {
    "id": "M02-OPT-06",
    "module": "M02",
    "title": "Split pane sizing",
    "articleId": "navigation",
    "defaultState": "40% navigation / 60% content",
    "interaction": "Open Workbench → Layout controls, move the split slider",
    "limits": "Only two illustrative panes; allowed 25–65% in 5-point steps",
    "recovery": "Reset pane split to 40/60; no workspace geometry saved",
    "availability": "preview-only"
  },
  {
    "id": "M02-OPT-07",
    "module": "M02",
    "title": "Keyboard focus visibility",
    "articleId": "commands",
    "defaultState": "Always active for keyboard focus",
    "interaction": "Use Tab or Shift+Tab on controls and Workbench tabpanels",
    "limits": "2px semantic outline; pointer click might not trigger focus-visible",
    "recovery": "Continue with Tab; report missing focus as an accessibility defect",
    "availability": "built-in"
  },
  {
    "id": "M02-OPT-08",
    "module": "M02",
    "title": "Reduced-motion behavior",
    "articleId": "appearance",
    "defaultState": "Follows Windows setting",
    "interaction": "Enable reduced motion in Windows Accessibility; inspect app",
    "limits": "Automatic CSS and live OS indicator; no in-app override switch",
    "recovery": "Restore Windows setting externally; no app preference saved",
    "availability": "built-in"
  },
  {
    "id": "M19-OPT-01",
    "module": "M19",
    "title": "Search bundled articles",
    "articleId": "quick-start",
    "defaultState": "Empty query, All topics",
    "interaction": "Use Help → Articles & search; filter local results",
    "limits": "Up to 120 characters, typed catalog version and max 50 results",
    "recovery": "Clear filters; malformed versions fail closed",
    "availability": "session"
  },
  {
    "id": "M19-OPT-02",
    "module": "M19",
    "title": "Contextual F1 Help",
    "articleId": "commands",
    "defaultState": "Current active view",
    "interaction": "Press F1 from a view or use its Help toolbar button",
    "limits": "Known local article IDs only; no automatic external navigation",
    "recovery": "Return via sidebar to the original desktop view",
    "availability": "built-in"
  },
  {
    "id": "M19-OPT-03",
    "module": "M19",
    "title": "Recovery steps and guided lessons",
    "articleId": "wizard-guide",
    "defaultState": "First step for chosen issue",
    "interaction": "Use Guided tour or Troubleshooting wizard; Previous, Next and Restart",
    "limits": "Textual steps only; annotated screenshots and hotspot overlays not implemented",
    "recovery": "Start over or prepare a safe local article report",
    "availability": "partial"
  },
  {
    "id": "M19-OPT-04",
    "module": "M19",
    "title": "Local glossary",
    "articleId": "faq-glossary",
    "defaultState": "All bundled terms",
    "interaction": "Open Help → FAQ & glossary and browse six definitions",
    "limits": "Fixed offline content; no external definition lookup",
    "recovery": "Choose a related offline guide for additional context",
    "availability": "built-in"
  },
  {
    "id": "M19-OPT-05",
    "module": "M19",
    "title": "Browse FAQ",
    "articleId": "faq-glossary",
    "defaultState": "All questions collapsed",
    "interaction": "Open Help → FAQ & glossary, expand a summary using Enter/Space",
    "limits": "Five local answers; no remote feedback processing",
    "recovery": "Close the disclosure or read its linked local guide",
    "availability": "built-in"
  },
  {
    "id": "M19-OPT-06",
    "module": "M19",
    "title": "Wiki mapping and link checker",
    "articleId": "wiki-mapping",
    "defaultState": "Source preview, unpublished",
    "interaction": "Open Wiki & link checker and validate help://article/... links",
    "limits": "Hosted GitHub Wiki is not published/synced; source maps are local",
    "recovery": "Fix invalid local route; never infer remote Wiki availability",
    "availability": "partial"
  },
  {
    "id": "M19-OPT-07",
    "module": "M19",
    "title": "Local broken-article report",
    "articleId": "report-guide",
    "defaultState": "Hidden, Outdated instructions reason",
    "interaction": "Open any article, Prepare local report, choose reason and copy JSON",
    "limits": "No upload, no project contents or automatic GitHub ticket",
    "recovery": "Select and copy manually if clipboard permission is denied",
    "availability": "session"
  },
  {
    "id": "M19-OPT-08",
    "module": "M19",
    "title": "Offline help behavior",
    "articleId": "offline",
    "defaultState": "Offline catalog bundled, no toggle",
    "interaction": "Open Help without internet and use all local modes",
    "limits": "No cloud search, no stored search history, no remote Wiki dependency",
    "recovery": "If an article is missing, clear filters or read bundled troubleshooting",
    "availability": "built-in"
  }
];

export function findHelpOption(id: string): HelpOptionReference | undefined {
  return helpOptionReferences.find(option => option.id === id);
}
export function optionHelpRoute(id: string): string | null {
  return findHelpOption(id) ? "help://option/" + id : null;
}
export function resolveOptionHelpRoute(route: string): HelpOptionReference | null {
  const match = /^help:\/\/option\/((?:M02|M19)-OPT-0[1-8])$/.exec(route);
  return match ? findHelpOption(match[1]) ?? null : null;
}
export function searchHelpOptions(query: string, module: "All" | "M02" | "M19" = "All"): HelpOptionReference[] {
  const normalized = query.trim().slice(0,100).toLocaleLowerCase();
  return helpOptionReferences.filter(option =>
    (module === "All" || option.module === module) &&
    [option.id, option.title, option.defaultState, option.interaction, option.limits, option.recovery]
      .some(value => value.toLocaleLowerCase().includes(normalized)));
}
export function validateHelpOptionReferences(): readonly string[] {
  const expected = [...uiOptionIds, ...helpOptionIds];
  const ids = helpOptionReferences.map(option => option.id);
  const failures: string[] = [];
  if (expected.length !== 16 || ids.length !== 16 || new Set(ids).size !== 16)
    failures.push("Missing or duplicate option reference");
  for (const id of expected)
    if (!ids.includes(id)) failures.push("Missing option: " + id);
  for (const option of helpOptionReferences) {
    if (!expected.includes(option.id as typeof expected[number]) ||
      !option.id.startsWith(option.module + "-OPT-") ||
      !findHelpArticle(option.articleId) ||
      !option.title.trim() || !option.defaultState.trim() ||
      !option.interaction.trim() || !option.limits.trim() || !option.recovery.trim() ||
      resolveOptionHelpRoute(optionHelpRoute(option.id) ?? "")?.id !== option.id)
      failures.push("Invalid option details: " + option.id);
  }
  return failures;
}
