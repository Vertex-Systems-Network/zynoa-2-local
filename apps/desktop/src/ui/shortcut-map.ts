/** M02-OPT-04: reversible, collision-free, session-only Ctrl+1..6 navigation keys. */
import type { AppView } from "./commands";

export const shortcutKeys = ["1", "2", "3", "4", "5", "6"] as const;
export type ShortcutKey = (typeof shortcutKeys)[number];
export type ShortcutTarget = Exclude<AppView, "help" | "changelog" | "backup" | "locations" | "updates">;
export type ShortcutAssignments = Readonly<Record<ShortcutKey, ShortcutTarget>>;

export const defaultShortcuts: ShortcutAssignments = {
  "1": "startup",
  "2": "settings",
  "3": "recovery",
  "4": "diagnostics",
  "5": "workbench",
  "6": "gallery",
};

export const shortcutTargets: ReadonlyArray<{ view: ShortcutTarget; title: string }> = [
  { view: "startup", title: "Overview" },
  { view: "workbench", title: "Workbench" },
  { view: "gallery", title: "Components" },
  { view: "settings", title: "Preferences" },
  { view: "recovery", title: "Recovery" },
  { view: "diagnostics", title: "Diagnostics" },
];

export function isShortcutKey(value: unknown): value is ShortcutKey {
  return typeof value === "string" && shortcutKeys.some(key => key === value);
}

export function shortcutForView(view: AppView, current: ShortcutAssignments): ShortcutKey | null {
  if (view === "help") return null; // F1 is fixed, never remappable.
  return shortcutKeys.find(key => current[key] === view) ?? null;
}

export function viewForShortcut(key: string, current: ShortcutAssignments): ShortcutTarget | null {
  return isShortcutKey(key) ? current[key] : null;
}

/** Collision handling swaps the two navigation destinations instead of dropping one. */
export function remapShortcut(
  current: ShortcutAssignments, view: ShortcutTarget, requestedKey: string,
): ShortcutAssignments {
  if (!isShortcutKey(requestedKey)) return current;
  const previousKey = shortcutForView(view, current);
  if (!previousKey || previousKey === requestedKey) return current;
  return { ...current, [requestedKey]: view, [previousKey]: current[requestedKey] };
}
