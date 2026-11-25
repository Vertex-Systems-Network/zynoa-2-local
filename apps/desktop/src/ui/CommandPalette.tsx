import { useEffect, useMemo, useRef, useState } from "react";
import type { AppView } from "./commands";
import type { ShortcutAssignments } from "./shortcut-map";
import { searchWorkspace, type HelpDestination, type PaletteResult } from "./unified-search";

type Props = {
  open: boolean;
  onClose: () => void;
  onNavigate: (view: AppView) => void;
  onOpenHelp: (target: HelpDestination) => void;
  returnFocusTarget?: HTMLElement | null;
  shortcuts: ShortcutAssignments;
};

export function CommandPalette({ open, onClose, onNavigate, onOpenHelp, returnFocusTarget, shortcuts }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);
  const navigationRef = useRef(false);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);
  // Keep the real edit field as the accessibility focus until the user
  // explicitly navigates results. A default Enter target is not a focus move.
  const [resultNavigation, setResultNavigation] = useState(false);
  const matches = useMemo(() => searchWorkspace(query, shortcuts), [query, shortcuts]);

  useEffect(() => {
    if (!open) return;
    navigationRef.current = false;
    returnFocusRef.current = returnFocusTarget?.isConnected ? returnFocusTarget :
      document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const frame = window.requestAnimationFrame(() => inputRef.current?.focus());
    return () => {
      window.cancelAnimationFrame(frame);
      if (navigationRef.current) {
        // Even same-view navigation must focus the destination rather than a stale opener.
        window.requestAnimationFrame(() =>
          document.getElementById("main-content")?.focus({ preventScroll: true }));
      } else if (returnFocusRef.current?.isConnected) {
        returnFocusRef.current?.focus({ preventScroll: true });
      } else {
        document.getElementById("main-content")?.focus({ preventScroll: true });
      }
    };
  }, [open]);

  useEffect(() => {
    if (!open) {
      setQuery("");
      setSelected(0);
      setResultNavigation(false);
    }
  }, [open]);

  if (!open) return null;
  const execute = (entry: PaletteResult) => {
    navigationRef.current = true;
    if (entry.destination.kind === "view") onNavigate(entry.destination.view);
    else onOpenHelp(entry.destination);
    onClose();
  };

  const onDialogKey = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape") {
      event.preventDefault();
      event.stopPropagation();
      onClose();
      return;
    }
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const direction = event.key === "ArrowDown" ? 1 : -1;
      setResultNavigation(matches.length > 0);
      setSelected(current =>
        matches.length ? (current + direction + matches.length) % matches.length : 0
      );
      inputRef.current?.focus();
      return;
    }
    if (event.key === "Enter" && matches.length && event.target === inputRef.current) {
      event.preventDefault();
      execute(matches[Math.min(selected, matches.length - 1)]);
      return;
    }
    if (event.key === "Tab" && dialogRef.current) {
      const focusable = Array.from(dialogRef.current.querySelectorAll<HTMLElement>(
        "button:not([disabled]),input:not([disabled])"
      ));
      if (!focusable.length) return;
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  };

  return (
    <div className="palette-backdrop" onMouseDown={event => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <div className="command-dialog" ref={dialogRef} role="dialog" aria-modal="true"
        aria-labelledby="command-title" onKeyDown={onDialogKey}>
        <div className="command-dialog-header">
          <div><p className="eyebrow">QUICK ACTIONS</p><h2 id="command-title">Command palette</h2></div>
          <button className="icon-button close-command" type="button" onClick={onClose}
            aria-label="Close command palette">×</button>
        </div>
        <label className="search-control" htmlFor="command-query">
          <span aria-hidden="true">⌕</span>
          <input id="command-query" ref={inputRef} autoFocus value={query} maxLength={100}
            onChange={event => { setQuery(event.target.value); setSelected(0); setResultNavigation(false); }}
            autoComplete="off" spellCheck={false}
            role="combobox" aria-autocomplete="list" aria-expanded={true}
            aria-label="Search available commands and offline Help"
            aria-controls="command-results"
            aria-activedescendant={resultNavigation && matches.length ? "command-" + matches[Math.min(selected, matches.length - 1)].id : undefined}
            placeholder="Search views, help, settings…" />
          <kbd>ESC</kbd>
        </label>
        <div className="command-results" id="command-results" role="listbox"
          aria-label="Available commands and bundled Help results">
          {matches.length ? matches.map((command, index) =>
            <button key={command.id} type="button"
              id={"command-" + command.id}
              role="option" aria-selected={selected === index}
              className={"command-result " + (selected === index ? "active" : "")} data-kind={command.kind}
              onMouseEnter={() => { setSelected(index); setResultNavigation(false); }}
              onClick={() => execute(command)}>
              <span className="command-glyph" aria-hidden="true">{command.symbol}</span>
              <span><strong>{command.title}</strong><small>{command.description}</small></span>
              <kbd>{command.keys}</kbd>
            </button>
          ) : <div className="empty-state" role="status">
            <strong>No matching commands</strong><p>Try “help”, “workbench” or “preferences”.</p>
          </div>}
        </div>
        <footer className="command-dialog-foot">
          <span>↑ ↓ navigate</span><span>↵ open</span><span>Esc close</span>
          <span className="command-count" role="status">{matches.length} local results</span>
        </footer>
      </div>
    </div>
  );
}
