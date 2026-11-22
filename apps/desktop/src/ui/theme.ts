/** M02 local-only, session-scoped design controls (no native preference persistence). */
export type ThemePreference = "system" | "dark" | "light";
export type DensityPreference = "comfortable" | "compact";

export const themeOptions = [
  { value: "system", label: "Follow system", description: "Uses the operating system appearance." },
  { value: "dark", label: "Dark", description: "Warm charcoal and gold contrast." },
  { value: "light", label: "Light", description: "Warm paper and ink contrast." },
] as const satisfies ReadonlyArray<{
  value: ThemePreference;
  label: string;
  description: string;
}>;

export const densityOptions = [
  { value: "comfortable", label: "Comfortable" },
  { value: "compact", label: "Compact" },
] as const satisfies ReadonlyArray<{ value: DensityPreference; label: string }>;

export function effectiveTheme(preference: ThemePreference, systemDark: boolean): "light" | "dark" {
  return preference === "system" ? (systemDark ? "dark" : "light") : preference;
}

export function isTheme(value: unknown): value is ThemePreference {
  return value === "system" || value === "dark" || value === "light";
}

export function isDensity(value: unknown): value is DensityPreference {
  return value === "comfortable" || value === "compact";
}

export const uiOptionIds = [
  "M02-OPT-01", "M02-OPT-02", "M02-OPT-03", "M02-OPT-04",
  "M02-OPT-05", "M02-OPT-06", "M02-OPT-07", "M02-OPT-08",
] as const;
