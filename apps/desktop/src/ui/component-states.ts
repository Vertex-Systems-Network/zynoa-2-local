/** M02 fixed local illustrative state model. No native actions, network or timers. */
export const componentPreviewStates = [
  { id: "ready", label: "Ready", title: "Example is ready", detail: "A local UI preview can accept input.", remedy: "Use Tab to visit enabled controls. Nothing is saved." },
  { id: "loading", label: "Loading", title: "Example is loading", detail: "Illustrative progress, not an active task.", remedy: "No worker, download or timer runs in this example." },
  { id: "empty", label: "Empty", title: "No items in this example", detail: "This sample collection contains no results.", remedy: "Choose Ready to restore the sample view." },
  { id: "error", label: "Error", title: "An example operation failed", detail: "Error feedback without calling any service.", remedy: "Read the message and choose Ready to demonstrate recovery." },
  { id: "offline", label: "Offline", title: "An example connection is unavailable", detail: "A local sample, not a network probe.", remedy: "Offline Help is bundled. Choose Ready to reset this sample." },
] as const;
export type ComponentPreviewState = (typeof componentPreviewStates)[number]["id"];
export function isComponentPreviewState(value: unknown): value is ComponentPreviewState {
  return typeof value === "string" && componentPreviewStates.some(item => item.id === value);
}
export function previewStateDetails(state: ComponentPreviewState): (typeof componentPreviewStates)[number] {
  return componentPreviewStates.find(item => item.id === state) ?? componentPreviewStates[0];
}
