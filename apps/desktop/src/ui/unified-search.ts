/** Unified allowlisted M02/M19 discovery. Never persists, fetches or executes commands. */
import { findCommands, type AppView } from "./commands.js";
import { searchHelp } from "./help-catalog.js";
import { searchHelpOptions } from "./help-options.js";
import { defaultShortcuts, shortcutForView, type ShortcutAssignments } from "./shortcut-map.js";
export type HelpDestination = Readonly<{ kind: "article"; articleId: string } | { kind: "option"; optionId: string }>;
export type PaletteDestination = HelpDestination | Readonly<{ kind: "view"; view: AppView }>;
export type PaletteResult = Readonly<{
  id: string; kind: PaletteDestination["kind"]; title: string;
  description: string; symbol: string; keys: string; destination: PaletteDestination;
}>;
/** Blank input displays only navigation; typed text also discovers bundled Help. */
export function searchWorkspace(query: string, shortcuts: ShortcutAssignments = defaultShortcuts): PaletteResult[] {
  const normalized = query.trim().slice(0, 100);
  const commands: PaletteResult[] = findCommands(normalized, shortcuts).map(command => ({
    id: command.id, kind: "view", title: command.title, description: command.description,
    symbol: command.symbol, keys: command.view === "help" ? "F1" : "Ctrl+" + shortcutForView(command.view, shortcuts),
    destination: { kind: "view", view: command.view },
  }));
  if (!normalized) return commands;
  const articles: PaletteResult[] = searchHelp(normalized).slice(0, 8).map(article => ({
    id: "article-" + article.id, kind: "article", title: article.title,
    description: article.summary, symbol: "?", keys: "GUIDE",
    destination: { kind: "article", articleId: article.id },
  }));
  const options: PaletteResult[] = searchHelpOptions(normalized).slice(0, 8).map(option => ({
    id: "option-" + option.id, kind: "option", title: option.title,
    description: option.id + " · " + option.limits, symbol: "◫", keys: "OPTION",
    destination: { kind: "option", optionId: option.id },
  }));
  // Keep traversal finite and show view actions before offline article/option entries.
  return [...commands, ...articles, ...options].slice(0, 20);
}
