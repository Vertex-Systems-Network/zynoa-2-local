/** M02 fixed allowlisted command navigation; no arbitrary code execution. */
export type AppView =
  | "startup" | "workbench" | "gallery" | "help" | "settings" | "recovery" | "diagnostics";

export type AppCommand = {
  readonly id: string;
  readonly title: string;
  readonly description: string;
  readonly section: "Workspace" | "Explore" | "System";
  readonly view: AppView;
  readonly keys: string;
  readonly symbol: string;
};

export const appCommands: readonly AppCommand[] = [
  { id: "go.overview", title: "Overview", description: "Home and native startup status", section: "Workspace", view: "startup", keys: "Ctrl+1", symbol: "⌂" },
  { id: "go.workbench", title: "Workbench", description: "Status panes and available workspace views", section: "Workspace", view: "workbench", keys: "Ctrl+5", symbol: "▣" },
  { id: "go.components", title: "Components", description: "Reusable design tokens and UI states", section: "Explore", view: "gallery", keys: "Ctrl+6", symbol: "◫" },
  { id: "go.help", title: "Help Center", description: "Search the bundled offline help catalog", section: "Explore", view: "help", keys: "F1", symbol: "?" },
  { id: "go.settings", title: "Preferences", description: "Session theme and navigation density", section: "System", view: "settings", keys: "Ctrl+2", symbol: "⚙" },
  { id: "go.recovery", title: "Recovery", description: "Native recovery availability and limitations", section: "System", view: "recovery", keys: "Ctrl+3", symbol: "↺" },
  { id: "go.diagnostics", title: "Diagnostics", description: "Read-only local system status", section: "System", view: "diagnostics", keys: "Ctrl+4", symbol: "◎" },
] as const;

export function findCommands(query: string): AppCommand[] {
  const normalized = query.trim().toLocaleLowerCase().slice(0, 100);
  const words = normalized.split(/\s+/).filter(Boolean);
  if (!words.length) return [...appCommands];
  return appCommands
    .map(command => {
      const title = command.title.toLocaleLowerCase();
      const haystack = [command.title, command.description, command.section, command.keys]
        .join(" ").toLocaleLowerCase();
      if (!words.every(word => haystack.includes(word))) return null;
      const score = (title === normalized ? 100 : title.startsWith(normalized) ? 50 : 0)
        + words.filter(word => title.includes(word)).length * 10;
      return { command, score };
    })
    .filter((item): item is { command: AppCommand; score: number } => item !== null)
    .sort((a, b) => b.score - a.score || a.command.title.localeCompare(b.command.title))
    .map(item => item.command);
}

export function shortcutView(key: string): AppView | null {
  const map: Record<string, AppView> = {
    "1": "startup", "2": "settings", "3": "recovery",
    "4": "diagnostics", "5": "workbench", "6": "gallery",
  };
  return map[key] ?? null;
}
