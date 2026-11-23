/** M19 offline workflows. This module has no network, filesystem or analytics access. */
import { findHelpArticle, helpArticles, helpOptionIds, searchHelp, type HelpArticle, type HelpCategory } from "./help-catalog.js";

export const offlineHelpContract = Object.freeze({
  schema_version: 1,
  catalog_version: "2026.11-p02",
  offline_only: true,
  publication: "source-preview-not-published",
  article_count: helpArticles.length,
  m19_option_count: helpOptionIds.length,
});

/** Typed, bounded and version-pinned local search contract; no network fallback. */
export type OfflineHelpSearchRequest = Readonly<{
  schema_version: number;
  catalog_version: string;
  query: string;
  category: HelpCategory | "All";
  limit: number;
}>;
export type OfflineHelpSearchResult =
  | Readonly<{ ok: true; schema_version: 1; catalog_version: string;
      total: number; matches: readonly HelpArticle[] }>
  | Readonly<{ ok: false; code: "M19-SCHEMA-001" | "M19-CATALOG-409" | "M19-QUERY-400";
      message: string }>;

export function requestOfflineHelp(request: unknown): OfflineHelpSearchResult {
  if (!request || typeof request !== "object" || Array.isArray(request))
    return { ok: false, code: "M19-SCHEMA-001", message: "Invalid local search request." };
  const value = request as Partial<OfflineHelpSearchRequest>;
  if (value.schema_version !== offlineHelpContract.schema_version)
    return { ok: false, code: "M19-SCHEMA-001", message: "Unsupported Help search schema." };
  if (value.catalog_version !== offlineHelpContract.catalog_version)
    return { ok: false, code: "M19-CATALOG-409", message: "The Help catalog version has changed." };
  const categories = ["All", "Get started", "Interface", "Privacy", "Troubleshooting"] as const;
  if (typeof value.query !== "string" || value.query.length > 120 ||
      !categories.some(category => category === value.category) ||
      !Number.isInteger(value.limit) || (value.limit ?? 0) < 1 || (value.limit ?? 0) > 50)
    return { ok: false, code: "M19-QUERY-400", message: "Invalid query, category or result limit." };
  const matches = searchHelp(value.query, value.category as HelpCategory | "All");
  return {
    ok: true, schema_version: 1, catalog_version: offlineHelpContract.catalog_version,
    total: matches.length, matches: matches.slice(0, value.limit),
  };
}

export type HelpWorkflowMode = "articles" | "options" | "tour" | "troubleshoot" | "faq" | "wiki";
export type IssueReason = "broken-reference" | "outdated-instructions" | "unreadable-article";

export type WizardStep = {
  readonly title: string;
  readonly instruction: string;
  readonly articleId: string;
};
export type WizardIssue = {
  readonly id: string;
  readonly title: string;
  readonly summary: string;
  readonly steps: readonly WizardStep[];
};

/** Five bounded informational lessons. Never drives other windows or native commands. */
export const guidedTourSteps = [
  { title: "Start with Overview", instruction: "Use Ctrl+1 or the rail for the read-only native status. No workspace is created.", articleId: "quick-start" },
  { title: "Explore Workbench", instruction: "Use Ctrl+5. Arrow keys navigate Runtime, Layout and Keyboard tabs; layout previews are session only.", articleId: "navigation" },
  { title: "Select an appearance", instruction: "Use Ctrl+2 for system, dark or light and comfortable or compact density. Reset when finished.", articleId: "appearance" },
  { title: "Use offline Help", instruction: "F1 opens contextual Help. Search, glossary, FAQ and local Wiki mapping are bundled.", articleId: "offline" },
  { title: "Understand unavailable services", instruction: "Workspace creation, backup restore and remote ticket sending are not enabled; do not treat previews as saved files.", articleId: "privacy" },
] as const;
export function getGuidedTourStep(index: number): (typeof guidedTourSteps)[number] | null {
  return Number.isInteger(index) && index >= 0 ? guidedTourSteps[index] ?? null : null;
}
export const wizardIssues: readonly WizardIssue[] = [
  { id: "native-connection", title: "Native bridge is unavailable",
    summary: "Determine whether you are in browser preview or the real Windows desktop application.",
    steps: [
      { title: "Check your runtime", instruction: "Open Overview and read the Native bridge status. Browser preview cannot provide the desktop connection.", articleId: "native-troubleshooting" },
      { title: "Restart the native window", instruction: "If you are using the actual installed Windows app, close and reopen it. Do not delete local app-data directories.", articleId: "native-troubleshooting" },
      { title: "Review Diagnostics", instruction: "Open Diagnostics from the sidebar; note the local capability status. No raw logs or private files are uploaded.", articleId: "privacy" },
    ] },
  { id: "missing-article", title: "Help search finds nothing",
    summary: "Recover from a query, category filter or an unsupported topic without going online.",
    steps: [
      { title: "Clear the search filter", instruction: "Select All topics, clear the query and try one descriptive keyword.", articleId: "quick-start" },
      { title: "Try a known offline category", instruction: "Search for theme, keyboard, offline or native. The local catalog supports mixed-case queries.", articleId: "offline" },
      { title: "Check the catalog version", instruction: "Read the bundled catalog version shown in Help. Unsupported future module docs are not promised as shipped.", articleId: "faq" },
    ] },
  { id: "keyboard-navigation", title: "Keyboard navigation is confusing",
    summary: "Recover a changed shortcut, hidden rail or command palette without deleting settings.",
    steps: [
      { title: "Locate navigation", instruction: "Press Alt+N to expand the icon rail, or use its accessible expand button.", articleId: "commands" },
      { title: "Reset shortcut assignments", instruction: "Open Workbench → Keyboard guide → Restore default shortcuts. Changes are session-only.", articleId: "commands" },
      { title: "Restore app focus", instruction: "Press Escape to close the command palette or F1 to open Help. Reopen Workbench using the sidebar.", articleId: "commands" },
    ] },
  { id: "workspace-unavailable", title: "New workspace or backup is disabled",
    summary: "Understand real feature boundaries; no test-only UI should be mistaken for saved work.",
    steps: [
      { title: "Check the availability label", instruction: "A disabled New workspace button means there is no verified creation service in this phase.", articleId: "quick-start" },
      { title: "Avoid placeholder input", instruction: "Do not enter real project data into preview controls or assume a native handshake is a created project.", articleId: "privacy" },
      { title: "Review offline capabilities", instruction: "Help, command navigation and interface preferences work locally; workspace saving and backup do not.", articleId: "offline" },
    ] },
];

export const helpFaq = [
  { id: "saved-project", question: "Does a native connection mean my work is saved?",
    answer: "No. The read-only bridge handshake is not a saved workspace or a backup.", articleId: "quick-start" },
  { id: "offline-search", question: "Can I search Help without internet?",
    answer: "Yes. All displayed articles and the search index are in the desktop bundle. No request is sent.", articleId: "offline" },
  { id: "shortcut-recovery", question: "What if I change Ctrl+1–6 by mistake?",
    answer: "Open Workbench → Keyboard guide → Restore default shortcuts. F1 and Ctrl+Shift+P stay reserved.", articleId: "commands" },
  { id: "privacy-report", question: "Will a broken article report contact GitHub?",
    answer: "No. A local, sanitized report can be copied manually. Nothing is uploaded or opened automatically.", articleId: "privacy" },
  { id: "wiki-online", question: "Is the GitHub Wiki already live and synchronized?",
    answer: "No. The mapping shown here is source-controlled documentation only; remote Wiki publication is not verified.", articleId: "offline" },
] as const;

export const helpGlossary = [
  { term: "Native handshake", definition: "A read-only availability check between the desktop window and its local service." },
  { term: "Offline catalog", definition: "Versioned articles shipped in the application bundle, with no cloud search." },
  { term: "Contextual Help", definition: "The F1 route from the active desktop view to a relevant bundled article." },
  { term: "Command palette", definition: "A local allowlisted search of application navigation commands." },
  { term: "Session-only setting", definition: "A change that resets when the application restarts; it is not stored as an account or disk preference." },
  { term: "Wiki source map", definition: "An auditable association between a local Help article and source-controlled Wiki Markdown, not a live hosted page." },
] as const;

export const wikiSourceMappings = [
  { id: "M02", title: "Professional GUI & Design System", source: "docs/wiki/pages/M02.md", articleId: "appearance", published: false },
  { id: "M19", title: "Documentation Wiki & Help Center", source: "docs/wiki/pages/M19.md", articleId: "offline", published: false },
] as const;

export function helpRoute(articleId: string): string | null {
  return findHelpArticle(articleId) ? "help://article/" + articleId : null;
}
export function resolveHelpRoute(route: string): string | null {
  const matched = /^help:\/\/article\/([a-z0-9-]{1,70})$/.exec(route);
  return matched && findHelpArticle(matched[1]) ? matched[1] : null;
}

export function getWizardIssue(id: string): WizardIssue | undefined {
  return wizardIssues.find(item => item.id === id);
}

export function getWizardStep(id: string, requestedIndex: number): WizardStep | null {
  const issue = getWizardIssue(id);
  return issue && Number.isInteger(requestedIndex) && requestedIndex >= 0
    ? issue.steps[requestedIndex] ?? null : null;
}

export function nextWizardStep(issueId: string, index: number): number | null {
  const issue = getWizardIssue(issueId);
  return issue && Number.isInteger(index) && index >= 0 && index + 1 < issue.steps.length
    ? index + 1 : null;
}

/** Reports contain an allowlisted code and an article ID, never typed user content. */
export function localBrokenArticleReport(articleId: string, reason: IssueReason): string | null {
  if (!findHelpArticle(articleId) ||
      !["broken-reference", "outdated-instructions", "unreadable-article"].includes(reason)) return null;
  return JSON.stringify({
    schema_version: 1,
    module: "M19",
    catalog_version: offlineHelpContract.catalog_version,
    article_id: articleId,
    reason,
    transmitted: false,
  }, null, 2);
}

export function validateOfflineHelpCatalog(): readonly string[] {
  const errors: string[] = [];
  const ids = new Set(helpArticles.map(article => article.id));
  if (ids.size !== helpArticles.length) errors.push("Duplicate article ID");
  if (offlineHelpContract.article_count !== helpArticles.length) errors.push("Catalog article count mismatch");
  if (new Set(helpOptionIds).size !== 8) errors.push("M19 option mapping incomplete");
  for (const article of helpArticles) {
    if (!article.sections.length || !article.title.trim() || !article.summary.trim())
      errors.push("Incomplete article: " + article.id);
    for (const related of article.related)
      if (!ids.has(related)) errors.push("Missing related article: " + article.id + " -> " + related);
    if (resolveHelpRoute(helpRoute(article.id) ?? "") !== article.id)
      errors.push("Invalid local route: " + article.id);
  }
  for (const faq of helpFaq) if (!ids.has(faq.articleId)) errors.push("Invalid FAQ article: " + faq.id);
  for (const step of guidedTourSteps)
    if (!ids.has(step.articleId)) errors.push("Invalid guided tour article: " + step.title);
  for (const issue of wizardIssues) {
    if (!issue.steps.length) errors.push("Empty wizard: " + issue.id);
    for (const step of issue.steps)
      if (!ids.has(step.articleId)) errors.push("Missing recovery article: " + issue.id);
  }
  const wikiIds = new Set<string>();
  for (const wiki of wikiSourceMappings) {
    if (wikiIds.has(wiki.id) || !ids.has(wiki.articleId) ||
        !/^docs\/wiki\/pages\/[A-Za-z0-9-]+\.md$/.test(wiki.source))
      errors.push("Invalid Wiki source mapping: " + wiki.id);
    wikiIds.add(wiki.id);
    if (wiki.published) errors.push("Unverified remote Wiki publication: " + wiki.id);
  }
  return errors;
}
