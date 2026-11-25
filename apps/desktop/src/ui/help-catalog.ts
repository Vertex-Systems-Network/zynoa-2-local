import { systemCenters } from "./system-centers.js";
/** Bundled M19 help index. No fetch, HTML injection, telemetry or cloud requirement. */
export type HelpCategory = "Get started" | "Interface" | "Privacy" | "Troubleshooting";
export type HelpArticle = {
  readonly id: string;
  readonly title: string;
  readonly category: HelpCategory;
  readonly summary: string;
  readonly keywords: readonly string[];
  readonly sections: readonly { readonly heading: string; readonly paragraphs: readonly string[] }[];
  readonly related: readonly string[];
};

export const helpArticles: readonly HelpArticle[] = [
  {
    id: "quick-start", title: "Get started with Zynoa", category: "Get started",
    summary: "Understand the desktop shell and which features are available today.",
    keywords: ["home", "overview", "windows", "native"],
    sections: [
      { heading: "Start with Overview", paragraphs: [
        "Open Overview to check the native startup state. The browser preview cannot prove that Windows native services are running.",
        "The read-only native handshake reports the current workspace as not configured. Workspace creation is not yet enabled.",
      ] },
      { heading: "Navigate without a mouse", paragraphs: [
        "Use the left navigation rail or Ctrl+1 through Ctrl+6 to switch available pages. Open the command palette with Ctrl+Shift+P; press F1 for this Help Center.",
        "A disabled control means its backing service is not implemented; it does not create files or report imaginary progress.",
      ] },
    ], related: ["commands", "offline"],
  },
  {
    id: "appearance", title: "Themes and interface density", category: "Interface",
    summary: "Switch between system, dark and light appearance; compact or comfortable spacing.",
    keywords: ["theme", "dark", "light", "system", "density", "compact", "M02-OPT-01", "M02-OPT-02"],
    sections: [
      { heading: "Choose an appearance", paragraphs: [
        "Open Preferences. Choose Follow system, Dark or Light. Follow system reacts to the operating system color preference while the app is open.",
        "Choose Comfortable or Compact navigation density. Changes apply immediately to this window.",
      ] },
      { heading: "Persistence boundary", paragraphs: [
        "These appearance preferences are session-only in this build. They are not written to your user vault, a browser storage API or a remote service.",
        "Returning to system appearance after restarting is expected until a verified native settings service exists.",
      ] },
    ], related: ["commands", "privacy"],
  },
  {
    id: "commands", title: "Command palette and keyboard shortcuts", category: "Interface",
    summary: "Quick navigation, search and focus handling with keyboard support.",
    keywords: ["ctrl", "shift", "palette", "shortcut", "focus", "F1", "M02-OPT-05"],
    sections: [
      { heading: "Quickly find a screen", paragraphs: [
        "Press Ctrl+Shift+P or activate the Command button in the top toolbar. Search a screen, local Help article or documented option; use Arrow Up or Arrow Down to select a result.",
        "Press Enter to open the selected view, bundled Help article or option reference. Escape closes, while Tab moves between controls. Focus returns to the element that opened the palette on dismissal.",
      ] },
      { heading: "Global shortcuts", paragraphs: [
        "By default Ctrl+1 opens Overview; Ctrl+2 Preferences; Ctrl+3 Recovery; Ctrl+4 Diagnostics; Ctrl+5 Workbench; Ctrl+6 Components. The Workbench Keyboard guide lets you swap the six assignments during the current session. F1 opens Help and cannot be reassigned.",
        "Shortcuts do not intercept typing inside editable form controls, except the explicit command-palette shortcut.",
      ] },
    ], related: ["appearance", "quick-start"],
  },
  {
    id: "offline", title: "Offline and local-first behavior", category: "Privacy",
    summary: "What the interface can do without an internet connection.",
    keywords: ["internet", "offline", "privacy", "cloud", "M19-OPT-08"],
    sections: [
      { heading: "Bundled help", paragraphs: [
        "This Help Center and its search index are bundled into the desktop application. Opening articles does not contact a server.",
        "Any external Wiki page is optional and requires an explicit user action and a working internet connection. A web page is not part of the offline bundle.",
      ] },
      { heading: "Native services", paragraphs: [
        "The desktop native workspace handshake is read-only. This build cannot create a project or send diagnostic events to GitHub on the user's behalf.",
      ] },
    ], related: ["privacy", "quick-start"],
  },
  {
    id: "privacy", title: "Data and diagnostics boundaries", category: "Privacy",
    summary: "Understand what Zynoa stores and what is not sent.",
    keywords: ["storage", "vault", "permissions", "logs", "diagnostics"],
    sections: [
      { heading: "What stays on device", paragraphs: [
        "The native shell initializes app-owned local metadata and storage under the application data folder, outside the executable. This UI does not expose backup or restore operations yet.",
        "The Help Center records no search terms in remote services or local browser storage. Diagnostic reporting remains disabled by default.",
      ] },
      { heading: "Avoid accidental data loss", paragraphs: [
        "Do not treat the Recovery screen as proof of a usable backup. The interface labels unavailable backup features as disabled until recovery is independently tested.",
      ] },
    ], related: ["offline", "native-troubleshooting"],
  },
  {
    id: "native-troubleshooting", title: "Native connection troubleshooting", category: "Troubleshooting",
    summary: "What to check if the native handshake is unavailable.",
    keywords: ["error", "handshake", "unavailable", "browser", "Windows", "reopen"],
    sections: [
      { heading: "Browser preview or disconnected transport", paragraphs: [
        "Open the actual Windows desktop application to test native integration. A browser preview cannot access the Tauri native bridge.",
        "If the native handshake fails inside the installed application, close and reopen the app. The Diagnostics page shows a capability summary, not live raw logs.",
      ] },
      { heading: "Unavailable workspaces", paragraphs: [
        "Workspace creation, backups and restore remain disabled in this foundation build. Do not enter real project data into placeholder controls.",
      ] },
    ], related: ["quick-start", "privacy"],
  },
  {
    id: "faq", title: "Frequently asked questions", category: "Get started",
    summary: "Answers about themes, workspace creation, cloud access and screenshots.",
    keywords: ["FAQ", "questions", "why", "backup", "import"],
    sections: [
      { heading: "Is my workspace already saved?", paragraphs: [
        "No. A read-only native handshake does not create a project. The app's internal vault being initialized is not the same as a saved user workspace.",
      ] },
      { heading: "Can I work fully offline?", paragraphs: [
        "The shell, component gallery, appearance options and bundled help are local. Some future features will need optional providers, but they are not advertised as active now.",
      ] },
      { heading: "Is the UI finished?", paragraphs: [
        "P02 implements shared UI foundations incrementally. A feature is considered complete only with real native screenshots and integration tests for all its documented states.",
      ] },
    ], related: ["appearance", "offline", "quick-start"],
  },
  {
    id: "navigation", title: "Adaptive navigation and Workbench panes", category: "Interface",
    summary: "Expand or collapse the rail, find named panes and use the split preview safely.",
    keywords: ["rail", "sidebar", "Alt+N", "breadcrumb", "split", "pane", "workbench", "M02"],
    sections: [
      { heading: "Move around the desktop", paragraphs: [
        "At narrow Windows widths, the left rail collapses into accessible icons. Press Alt+N or use Expand navigation to see full names. The active page stays selected.",
        "Workbench has Runtime status, Layout controls and Keyboard guide tabs. Switch focused tabs with Left/Right/Home/End and open a panel with Tab.",
      ] },
      { heading: "Understand the preview", paragraphs: [
        "The Layout controls slider changes two illustrative pane widths. It does not move or persist real project files or create a workspace.",
        "The compact properties toggle changes sample row spacing only. The app does not yet have an editable native project inspector.",
      ] },
    ], related: ["commands", "appearance", "quick-start"],
  },
  {
    id: "wizard-guide", title: "Run offline troubleshooting", category: "Troubleshooting",
    summary: "Follow an interactive, reversible recovery path for common desktop problems.",
    keywords: ["wizard", "recover", "fix", "steps", "M19-OPT-03", "M19-OPT-08"],
    sections: [
      { heading: "Choose a problem", paragraphs: [
        "Open Help Center → Troubleshooting wizard. Choose native bridge, missing article, keyboard or unavailable workspace. The first guided step appears immediately.",
        "Select This fixed it to end, or Still stuck to proceed. Previous step and Start over remain available. No automatic repair command is executed.",
      ] },
      { heading: "When all steps are exhausted", paragraphs: [
        "Read the linked offline article or prepare a sanitized local report. Nothing is sent to GitHub automatically.",
        "Only article IDs and allowlisted reason codes appear in the report. Do not attach private files or credentials to public tickets.",
      ] },
    ], related: ["native-troubleshooting", "privacy", "offline"],
  },
  {
    id: "faq-glossary", title: "Using FAQ and glossary", category: "Get started",
    summary: "Explore verified answers and technical terms with direct links to offline guides.",
    keywords: ["faq", "glossary", "definition", "M19-OPT-04", "M19-OPT-05"],
    sections: [
      { heading: "Browse answers", paragraphs: [
        "Select FAQ & glossary inside Help Center. Expand a question using Enter, Space or pointer. Each answer links to a deeper offline article.",
        "The glossary describes native handshake, offline catalog, contextual Help and session-only settings. No external account is required.",
      ] },
    ], related: ["faq", "quick-start", "offline"],
  },
  {
    id: "wiki-mapping", title: "Validate local Help and Wiki references", category: "Troubleshooting",
    summary: "Inspect source-controlled Wiki mappings and resolve local Help routes without internet.",
    keywords: ["wiki", "link", "broken", "route", "version", "M19-OPT-06"],
    sections: [
      { heading: "Local versus published", paragraphs: [
        "The Wiki & link checker lists trusted Markdown source mappings. These are not a published GitHub Wiki and do not establish live remote availability.",
        "Paste a help://article/<id> route to validate an existing bundled article. A broken or unknown ID cannot be opened; path traversal is rejected.",
      ] },
      { heading: "Audit the catalog", paragraphs: [
        "Check bundled article and Wiki mappings checks unique IDs, related links, FAQ references and guided wizard recovery articles locally.",
        "Successful source validation proves only the offline app bundle. Hosted Wiki publication and final screenshots are independent acceptance gates.",
      ] },
    ], related: ["offline", "wizard-guide", "privacy"],
  },
  {
    id: "report-guide", title: "Report a broken article without uploading data", category: "Troubleshooting",
    summary: "Create a sanitized, local-only issue summary with no automatic transmission.",
    keywords: ["report", "broken reference", "privacy", "issue", "M19-OPT-07"],
    sections: [
      { heading: "Prepare a safe report", paragraphs: [
        "Open any article and choose Prepare local report. Select Outdated instructions, Broken reference or Unreadable article.",
        "A read-only JSON summary includes the catalog version, known article ID and reason. It excludes typed text, project content, account information and timestamps.",
      ] },
      { heading: "Copy, never upload automatically", paragraphs: [
        "Copy report locally requires clipboard permission; if denied, select and copy the visible report manually.",
        "Remote issue automation is not implemented in the desktop Help Center. You decide if and where to share the sanitized summary.",
      ] },
    ], related: ["privacy", "wiki-mapping", "offline"],
  },
  {
    id: "change-history", title: "Changelog and release history", category: "Interface",
    summary: "Read the bundled capability limitations and distinguish verified releases from unfinished work.",
    keywords: ["changelog", "release history", "known issues", "module changes", "M26"],
    sections: [
      { heading: "Open the Changelog", paragraphs: [
        "Choose Changelog in the System navigation or search Changelog in the command palette. Use Tab to enter the selected tab, then Left/Right, Home or End to navigate What's New, Known Issues, Version History, Module Changes, Audit Timeline, Notifications and Migration Notes.",
        "Known Issues shows bundled capability limitations, not a live issue tracker. Filter by module and search. Reset filters to see all bundled notices.",
      ] },
      { heading: "Release verification boundary", paragraphs: [
        "No signed release feed or verified history cache is available in this preview. Release and version panels intentionally show an unavailable or empty state, rather than inventing a release.",
        "Local native connection status is not release verification. No background network request, issue publication or update action is performed. Press F1 for this article.",
        "Audit Timeline, Notifications and Migration Notes explain their missing service prerequisites. Disabled actions cannot query private events, export, change preferences or perform recovery. Contextual guidance returns to this local article.",
      ] },
      { heading: "M26-OPT-01 — Filter by release version or channel", paragraphs: ["Disabled: no signed feed or verified channel/version choices. Read the reason; no setting or network request occurs."] },
      { heading: "M26-OPT-02 — Filter by module", paragraphs: ["Session-only combo: default All modules; choose M23–M26 with native arrows/Enter. M23 shows its bundled notice. Reset filters restores All and clears search/selection."] },
      { heading: "M26-OPT-03 — Filter by change category", paragraphs: ["Disabled: no verified release entries. Do not infer categories from local capability notices."] },
      { heading: "M26-OPT-04 — Toggle end-user or technical details", paragraphs: ["Disabled: authorized audience and verified event query required. No private event or saved toggle is exposed."] },
      { heading: "M26-OPT-05 — Search changelog", paragraphs: ["Type backup or a module ID. Search is local, case-insensitive, all-word and bounded to 120 characters. zzznomatch shows zero notices; activate the no-match reset action or Reset filters to clear both filters and return focus to search. No GitHub query."] },
      { heading: "M26-OPT-06 — Open linked issue", paragraphs: ["Disabled: select a bundled notice and read its detail; no verified public issue link is attached and no browser opens."] },
      { heading: "M26-OPT-07 — Open linked pull request", paragraphs: ["Disabled: a verified merge receipt is required. A PR or issue closure is not release evidence."] },
      { heading: "M26-OPT-08 — View documentation changes", paragraphs: ["F1 opens this bundled article from any Change Center tab. Local guidance works offline; no verified per-release revision or external navigation is enabled."] },
      { heading: "M26-OPT-09 — Display release badges and dates", paragraphs: ["Read-only unavailable state: no release date, version or shipped badge is inferred from issue status or a native connection."] },
      { heading: "M26-OPT-10 — View known problems", paragraphs: ["Known Issues lists four M23–M26 limitations, not live open issues. Tab through notice buttons; Enter moves focus to local detail. Back to notice list returns to the originating notice; Tab also reaches unavailable explanations. Reset restores all four."] },
      { heading: "M26-OPT-11 — View fixed problems", paragraphs: ["Disabled: only verified published fixes may appear. Implemented, merged or closed issues are not released."] },
      { heading: "M26-OPT-12 — Module history navigation", paragraphs: ["Use Left/Right or Home/End on the tablist to reach Module Changes; local filter/search work on support notices, not historical releases. Reset restores all."] },
      { heading: "M26-OPT-13 — Subscribe to what-is-new indicator", paragraphs: ["Disabled: signed notification service not connected. No subscription, permission prompt or saved preference."] },
      { heading: "M26-OPT-14 — Show migration and breaking-change notes", paragraphs: ["Disabled: release-specific backup, compatibility and migration instructions require a verified release. No migration or storage changes occur."] },
      { heading: "M26-OPT-15 — Open technical audit timeline", paragraphs: ["Audit Timeline is a read-only authorization boundary. Native persistence does not grant private query access; no audit entries or technical data are exposed."] },
      { heading: "M26-OPT-16 — Export change history", paragraphs: ["Disabled: verified sanitized export required. No path picker, file, JSON, Markdown or private data leaves the app."] },
      { heading: "M26-OPT-17 — Compare two released versions", paragraphs: ["Disabled: two verified released versions required. No version/date selection or comparison is fabricated."] },
      { heading: "M26-OPT-18 — Open rollback/recovery guidance", paragraphs: ["Disabled: a verified supported recovery path is required; no rollback or backup operation runs."] },
      { heading: "M26-OPT-19 — Configure update/changelog unread marker", paragraphs: ["Disabled: verified per-device read-state storage required. No state is saved or unpublished work marked new."] },
      { heading: "M26-OPT-20 — Report problem from a change", paragraphs: ["Disabled: no authorized change-reporting service. No issue, private content or network request is sent."] },
    ], related: ["offline", "privacy", "commands"],
  },
  ...systemCenters.map(center=>({id:center.article,title:center.title+" — local planning guide",category:"Privacy" as const,summary:center.description,keywords:[center.module,center.title],sections:[
    ...center.screens.map(screen=>({heading:screen.id+" — "+screen.title,paragraphs:[screen.description,screen.status+". Open the named screen from "+center.title+". No privileged service is invoked."]})),
    ...center.options.map(option=>({heading:option.id+" — "+option.title,paragraphs:[option.reason,option.kind==="blocked"?"The action is disabled. Tab to its explanation; use F1 for bundled guidance.":"Change a session-only draft using the labeled control. Reset session drafts or leave the center to clear it."]}))
  ],related:["privacy","native-troubleshooting","change-history"]})),
];

export const helpOptionIds = [
  "M19-OPT-01", "M19-OPT-02", "M19-OPT-03", "M19-OPT-04",
  "M19-OPT-05", "M19-OPT-06", "M19-OPT-07", "M19-OPT-08",
] as const;

function plainText(article: HelpArticle): string {
  return [article.title, article.category, article.summary, ...article.keywords,
    ...article.sections.flatMap(section => [section.heading, ...section.paragraphs])]
    .join(" ").toLocaleLowerCase();
}

export function findHelpArticle(id: string): HelpArticle | undefined {
  return helpArticles.find(article => article.id === id);
}

/** Reader must never render a document absent from the visible filtered results. */
export function resolveVisibleHelpArticle(results: readonly HelpArticle[], preferredId: string): HelpArticle | undefined {
  return results.find(article => article.id === preferredId) ?? results[0];
}

export function searchHelp(query: string, category: HelpCategory | "All" = "All"): HelpArticle[] {
  const words = query.trim().toLocaleLowerCase().slice(0, 120).split(/\s+/).filter(Boolean);
  return helpArticles
    .filter(article => category === "All" || article.category === category)
    .map(article => {
      const text = plainText(article);
      if (!words.every(word => text.includes(word))) return null;
      const title = article.title.toLocaleLowerCase();
      const score = words.reduce((total, word) => total
        + (title.startsWith(word) ? 20 : 0)
        + (title.includes(word) ? 10 : 0)
        + (article.keywords.some(keyword => keyword.toLocaleLowerCase().includes(word)) ? 6 : 0), 0);
      return { article, score };
    })
    .filter((match): match is { article: HelpArticle; score: number } => match !== null)
    .sort((a, b) => b.score - a.score || a.article.title.localeCompare(b.article.title))
    .map(result => result.article);
}
