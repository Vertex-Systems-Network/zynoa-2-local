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
        "Press Ctrl+Shift+P or activate the Command button in the top toolbar. Type a screen name and use Arrow Up or Arrow Down to select a result.",
        "Press Enter to navigate, Escape to close, or Tab to move between controls. Focus returns to the element that opened the palette.",
      ] },
      { heading: "Global shortcuts", paragraphs: [
        "Ctrl+1 opens Overview; Ctrl+2 Preferences; Ctrl+3 Recovery; Ctrl+4 Diagnostics; Ctrl+5 Workbench; Ctrl+6 Components. F1 opens Help.",
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
