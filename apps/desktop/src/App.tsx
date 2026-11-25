import type { HelpDestination } from "./ui/unified-search";
import { useEffect, useRef, useState } from "react";
import { probeWorkspaceStatus } from "./ipc";
import { CommandPalette } from "./ui/CommandPalette";
import { Workbench, ComponentGallery } from "./ui/Workbench";
import { HelpCenter } from "./ui/HelpCenter";
import { ChangeCenter } from "./ui/ChangeCenter";
import { SystemCenter } from "./ui/SystemCenter";
import { effectiveTheme, densityOptions, isDensity, isTheme, themeOptions, type ThemePreference, type DensityPreference } from "./ui/theme";
import type { AppView } from "./ui/commands";
import { defaultShortcuts, remapShortcut, shortcutForView, viewForShortcut, type ShortcutAssignments } from "./ui/shortcut-map";

type View = AppView;
type StartupState = "starting" | "desktop" | "browser";
type TransportState = "pending" | "connected" | "unavailable" | "preview";
const views: { key: View; title: string; shortcut: string; icon: string; section: string }[] = [
  { key: "startup", title: "Overview", shortcut: "1", icon: "⌂", section: "WORKSPACE" },
  { key: "workbench", title: "Workbench", shortcut: "5", icon: "▣", section: "WORKSPACE" },
  { key: "gallery", title: "Components", shortcut: "6", icon: "◫", section: "EXPLORE" },
  { key: "help", title: "Help Center", shortcut: "F1", icon: "?", section: "EXPLORE" },
  { key: "settings", title: "Preferences", shortcut: "2", icon: "⚙", section: "SYSTEM" },
  { key: "recovery", title: "Recovery", shortcut: "3", icon: "↺", section: "SYSTEM" },
  { key: "diagnostics", title: "Diagnostics", shortcut: "4", icon: "◎", section: "SYSTEM" },
  { key: "changelog", title: "Changelog", shortcut: "", icon: "≡", section: "SYSTEM" },
  { key: "backup", title: "Backup Center", shortcut: "", icon: "▤", section: "SYSTEM" },
  { key: "locations", title: "Data Locations", shortcut: "", icon: "▱", section: "SYSTEM" },
  { key: "updates", title: "Update Center", shortcut: "", icon: "⇧", section: "SYSTEM" },
];

function Startup({ state, transport }: { state: StartupState; transport: TransportState }) {
  return (
    <>
      <p className="eyebrow">DESKTOP FOUNDATION / P01</p>
      <h1>One workspace.<br /><em>Built to last.</em></h1>
      <p className="lead">A local-first environment for projects and files. This foundation shell includes a read-only native handshake and app-owned startup storage. Workspace creation and user-facing services are not available yet.</p>
      <div className="hero-grid">
        <section className="panel emphasis" aria-label="Startup status">
          <div className="panel-head">Startup status <span className={state === "starting" ? "dot pending" : "dot healthy"} /></div>
          <h2>{state === "starting" ? "Preparing interface" : state === "desktop" ? "Native window displayed" : "Browser preview"}</h2>
          <p>{state === "desktop" ? "The native shell started with app-local storage initialized. The workspace is not configured, and optional background services are unavailable." : state === "browser" ? "The browser preview cannot establish native runtime readiness. Use the Windows executable to check desktop startup." : "Initializing locally without a cloud connection."}</p>
          <div className="status-strip"><span className="status-pill">Offline interface</span><span className="status-muted" role="status">{transport === "connected" ? "Typed native handshake connected · workspace not configured" : transport === "unavailable" ? "Native handshake unavailable · reopen the application" : transport === "preview" ? "Browser-only preview" : "Checking the read-only native transport"}</span></div>
        </section>
        <section className="panel" aria-label="Workspace status">
          <div className="panel-head">Your workspace <span className="muted-symbol">↗</span></div>
          <h2>Nothing opened yet</h2>
          <p>Project creation and persistent workspace storage are not enabled in the foundation shell.</p>
          <button type="button" disabled title="Workspace service is not implemented">Create workspace <span>↗</span></button>
        </section>
      </div>
      <div className="section-top"><h3>Foundation progress</h3><span>Verification stages</span></div>
      <div className="checklist">
        <div className="check-item"><b>01</b><div><strong>Local desktop shell</strong><small>Bundled React view and Tauri window</small></div><span className="check-info">Native CI tested</span></div>
        <div className="check-item"><b>02</b><div><strong>Native service transport</strong><small>Typed commands and workspace boundaries</small></div><span className="check-info">Read-only handshake</span></div>
        <div className="check-item"><b>03</b><div><strong>Durable storage and recovery</strong><small>Native vault and event records; backup/restore not available</small></div><span className="check-pending">Foundation only</span></div>
      </div>
    </>
  );
}

function Settings({ theme, onTheme, density, onDensity, onHelp, onReset, systemDark, reducedMotion }: {
  theme: ThemePreference; onTheme: (next: ThemePreference) => void;
  density: DensityPreference; onDensity: (next: DensityPreference) => void;
  onHelp: () => void; onReset: () => void;
  systemDark: boolean; reducedMotion: boolean;
}) {
  return (
    <section className="detail settings-page" aria-labelledby="settings-title">
      <p className="eyebrow">M02 / YOUR INTERFACE</p><h1 id="settings-title">Make it <em>your workspace.</em></h1>
      <p className="lead">Fine-tune your working environment. Appearance and density update this window immediately; they are session-only until a native preferences service is verified.</p>
      <div className="settings-intro"><div className="settings-symbol" aria-hidden="true">◐</div>
        <div><strong>Interface appearance</strong><p>Choose a comfortable environment for focus and readability.</p></div>
        <span className="soft-chip">SESSION ONLY</span>
      </div>
      <div className="setting-row"><div><strong>Appearance</strong><p>Follow Windows colors or choose a fixed palette.</p></div>
        <select aria-label="Interface appearance" value={theme} onChange={event => {
          if (isTheme(event.target.value)) onTheme(event.target.value);
        }}>
          {themeOptions.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
      </div>
      <div className="setting-row"><div><strong>Navigation density</strong><p>Comfortable spacing or compact lists for faster scanning.</p></div>
        <select aria-label="Navigation density" value={density} onChange={event => {
          if (isDensity(event.target.value)) onDensity(event.target.value);
        }}>
          {densityOptions.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
      </div>
      <div className="setting-row"><div><strong>Native storage</strong><p>Data locations are owned by the native runtime. User-selected relocation remains unavailable.</p></div>
        <button type="button" disabled>Choose folder</button>
      </div>
      <div className="settings-live-summary" role="status" aria-live="polite">
        <strong>Current window appearance: {effectiveTheme(theme, systemDark)}</strong>
        <span>Theme source: {theme === "system" ? "Operating system" : "Manual override"} · Navigation: {density} · Motion: {reducedMotion ? "Reduced by Windows" : "Windows standard"}</span>
        <small>Values reflect this running window, not saved Windows or account settings.</small>
      </div>
      <div className="settings-motion" role="group" tabIndex={0}
        aria-label="Reduced motion (M02-OPT-08)">
        <div><strong>Reduced motion</strong>
          <p>Follows Windows accessibility settings. Read-only; no in-app switch or saved preference.</p></div>
        <output aria-live="polite">{reducedMotion ? "Reduced by Windows" : "Windows standard motion"}</output>
      </div>
      <div className="settings-actions">
        <button type="button" className="subtle-action" disabled={theme === "system" && density === "comfortable"}
          onClick={onReset}>Restore interface defaults</button>
      </div>
      <div className="notice" role="status">Changes are not saved to disk or synchronized with any account. A restart returns to the system default.</div>
      <button type="button" className="text-action" onClick={onHelp}>Appearance & keyboard help ↗</button>
    </section>
  );
}

function Recovery() {
  return (
    <section className="detail" aria-labelledby="recovery-title">
      <p className="eyebrow">DATA / SAFETY</p><h1 id="recovery-title">Recovery<span className="period">.</span></h1>
      <p className="lead">The native vault is initialized outside the executable. Backup and restore controls remain disabled until a verified restore drill and user-facing recovery flow exist.</p>
      <div className="panel wide"><div className="panel-head">Recovery center <span className="status-muted">Not configured</span></div><h2>No verified backups</h2><p>A native storage foundation exists, but no workspace data or user-accessible backup inventory is configured. Backup protection is not yet available.</p><button type="button" disabled>Restore from backup</button></div>
    </section>
  );
}

function Diagnostics({ transport }: { transport: TransportState }) {
  const nativeReady = transport === "connected";
  return (
    <section className="detail" aria-labelledby="diagnostics-title">
      <p className="eyebrow">SYSTEM / VISIBILITY</p><h1 id="diagnostics-title">Diagnostics<span className="period">.</span></h1>
      <p className="lead">{nativeReady ? "Native diagnostics record only fixed local event categories. No crash messages, file paths, passwords or document contents are collected. This view does not read stored logs or send reports." : "Live diagnostics are unavailable in this browser or while the native transport is disconnected. No remote telemetry is sent."}</p>
      <div className="diagnostic-grid">
        <div className="metric"><span>Local event spool</span><strong>{nativeReady ? "Native-only" : "Not verified"}</strong><small>{nativeReady ? "Boot and denied-request classes only" : "Open the local desktop application"}</small></div>
        <div className="metric"><span>Remote reporting</span><strong>Disabled</strong><small>No automatic issue publishing or telemetry</small></div>
      </div>
      <div className="notice" role="status">This is a capability summary, not a live log viewer or complete device health scan.</div>
    </section>
  );
}

export function App() {
  const [view, setView] = useState<View>("startup");
  const [startup, setStartup] = useState<StartupState>("starting");
  const [transport, setTransport] = useState<TransportState>("pending");
  const [paletteOpen, setPaletteOpen] = useState(false);
  const paletteOpenerRef = useRef<HTMLElement | null>(null);
  const [theme, setTheme] = useState<ThemePreference>("system");
  const [density, setDensity] = useState<DensityPreference>("comfortable");
  const [systemDark, setSystemDark] = useState(true);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [helpTopic, setHelpTopic] = useState("quick-start");
  const [helpDestination, setHelpDestination] = useState<HelpDestination | null>(null);
  const [shortcuts, setShortcuts] = useState<ShortcutAssignments>(defaultShortcuts);
  const [navigationCollapsed, setNavigationCollapsed] = useState(false);

  useEffect(() => {
    const query = window.matchMedia("(prefers-color-scheme: dark)");
    setSystemDark(query.matches);
    const change = (event: MediaQueryListEvent) => setSystemDark(event.matches);
    query.addEventListener("change", change);
    return () => query.removeEventListener("change", change);
  }, []);

  // Watch OS accessibility settings without writing to disk or changing Windows.
  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = (event: MediaQueryListEvent) => setReducedMotion(event.matches);
    setReducedMotion(query.matches);
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  // Match the 900px native minimum with a compact rail; users can override
  // the rail state for the current window, never writing a preference to disk.
  useEffect(() => {
    const query = window.matchMedia("(max-width: 1000px)");
    const update = (event: MediaQueryListEvent) => setNavigationCollapsed(event.matches);
    setNavigationCollapsed(query.matches);
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  const navigateView = (next: View) => { setHelpDestination(null); setView(next); };
  const openContextHelp = () => {
    setHelpDestination(null);
    const topics: Record<View, string> = {
      startup: "quick-start", workbench: "commands", gallery: "appearance",
      help: "quick-start", settings: "appearance", recovery: "privacy",
      diagnostics: "native-troubleshooting", changelog: "change-history", backup: "backup-center", locations: "data-locations", updates: "update-center",
    };
    setHelpTopic(topics[view]);
    setView("help");
  };
  useEffect(() => {
    let disposed = false;
    const nativeHostPresent = "__TAURI_INTERNALS__" in window;
    const frame = window.requestAnimationFrame(() => {
      if (!nativeHostPresent) {
        setStartup("browser");
        setTransport("preview");
        return;
      }
      setStartup("desktop");
      void probeWorkspaceStatus().then(() => {
        if (!disposed) setTransport("connected");
      }).catch(() => {
        if (!disposed) setTransport("unavailable");
      });
    });
    return () => { disposed = true; window.cancelAnimationFrame(frame); };
  }, []);
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const command = event.ctrlKey && event.shiftKey &&
        !event.altKey && !event.metaKey && event.key.toLowerCase() === "p";
      if (command) {
        event.preventDefault();
        if (!paletteOpen) {
          paletteOpenerRef.current =
            document.activeElement instanceof HTMLElement ? document.activeElement : null;
        }
        setPaletteOpen(open => !open);
        return;
      }
      // Modal controls own focus and navigation; global background shortcuts stay blocked.
      if (paletteOpen) {
        if (event.key === "F1" ||
            (event.ctrlKey && !event.altKey && !event.metaKey && /^[1-6]$/.test(event.key))) {
          event.preventDefault();
        }
        return;
      }
      // Alt+N is a keyboard-accessible rail toggle, not an OS-wide shortcut.
      if (event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey &&
          event.key.toLowerCase() === "n" &&
          !(event.target instanceof HTMLElement &&
            event.target.matches("input,textarea,select,[contenteditable=true]"))) {
        event.preventDefault();
        setNavigationCollapsed(current => !current);
        return;
      }
      if (event.key === "F1" && !event.altKey && !event.ctrlKey && !event.metaKey) {
        event.preventDefault();
        setHelpDestination(null);
        setView(current => {
          const topics: Record<View, string> = {
            startup: "quick-start", workbench: "commands", gallery: "appearance",
            help: "quick-start", settings: "appearance", recovery: "privacy",
            diagnostics: "native-troubleshooting", changelog: "change-history", backup: "backup-center", locations: "data-locations", updates: "update-center",
          };
          setHelpTopic(topics[current]);
          return "help";
        });
        return;
      }
      const element = event.target;
      if (element instanceof HTMLElement &&
          element.matches("input,textarea,select,[contenteditable=true]")) return;
      if (!event.ctrlKey || event.altKey || event.metaKey || event.shiftKey) return;
      const target = viewForShortcut(event.key, shortcuts);
      if (!target) return;
      event.preventDefault();
      setHelpDestination(null);
      setView(target);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [paletteOpen, shortcuts]);

  // Each view starts at the top; focus the native scroll surface for keyboard PageDown.
  useEffect(() => {
    const surface = document.getElementById("main-content");
    if (surface) {
      surface.scrollTop = 0;
      // A direct Help option route owns focus via its selected heading;
      // focusing the general scroll pane would steal screen-reader context.
      if (view !== "help" || helpDestination?.kind !== "option") {
        surface.focus({ preventScroll: true });
      }
    }
  }, [view, helpDestination]);

  return (
    <div className="shell" data-theme={effectiveTheme(theme, systemDark)} data-density={density}>
      <aside className="sidebar" aria-label="Primary navigation" data-nav-collapsed={navigationCollapsed} inert={paletteOpen}>
        <div className="brand"><span className="brand-symbol" aria-hidden="true">Z</span><span className="brand-word">ZYNOA<small>DESKTOP ENVIRONMENT</small></span></div>
        <button type="button" className="nav-toggle" aria-controls="application-sections"
          aria-expanded={!navigationCollapsed}
          aria-label={navigationCollapsed ? "Expand navigation rail (Alt+N)" : "Collapse navigation rail (Alt+N)"}
          aria-keyshortcuts="Alt+N"
          onClick={() => setNavigationCollapsed(value => !value)}>
          <span aria-hidden="true">{navigationCollapsed ? "»" : "«"}</span>
          <span className="nav-toggle-label">{navigationCollapsed ? "Expand navigation" : "Collapse navigation"}</span>
        </button>
        <nav id="application-sections" aria-label="Application sections">
          {["WORKSPACE", "EXPLORE", "SYSTEM"].map(section =>
            <div className="sidebar-group" key={section} role="group" aria-label={section + " views"}>
              <p className="nav-label">{section}</p>
              {views.filter(page => page.section === section).map(page =>
                page.key === "changelog" ?
                <button key={page.key} type="button" className={"nav-link " + (view === page.key ? "selected" : "")}
                  aria-current={view === page.key ? "page" : undefined} aria-label="Changelog"
                  onClick={() => navigateView(page.key)}>
                  <span className="nav-icon" aria-hidden="true">{page.icon}</span>
                  <span className="nav-link-title">{page.title}</span>
                </button> : page.key === "backup" || page.key === "locations" || page.key === "updates" ?
                <button key={page.key} type="button" className={"nav-link " + (view === page.key ? "selected" : "")} aria-current={view === page.key ? "page" : undefined} aria-label={page.title} onClick={()=>navigateView(page.key)}><span className="nav-icon" aria-hidden="true">{page.icon}</span><span className="nav-link-title">{page.title}</span></button> :
                <button key={page.key} className={"nav-link " + (view === page.key ? "selected" : "")}
                  aria-current={view === page.key ? "page" : undefined}
                  aria-label={page.title + " (" + (page.key === "help" ? "F1" : "Ctrl+" + shortcutForView(page.key, shortcuts)) + ")"}
                  aria-keyshortcuts={page.key === "help" ? "F1" : "Control+" + shortcutForView(page.key, shortcuts)}
                  type="button"
                  onClick={() => navigateView(page.key)}>
                  <span className="nav-icon" aria-hidden="true">{page.icon}</span>
                  <span className="nav-link-title">{page.title}</span><kbd>{page.key === "help" ? "F1" : "⌃" + shortcutForView(page.key, shortcuts)}</kbd>
                </button>
              )}
            </div>
          )}
        </nav>
        <div className="sidebar-bottom"><span className="version">SHARED UI / P02 · 0.1.0</span><div className="offline" aria-label="Local-first interface"><span className="dot healthy" aria-hidden="true" /><span className="offline-copy">Local-first interface</span></div></div>
      </aside>
      <main id="main-content" tabIndex={-1} inert={paletteOpen}>
        <header className="topbar">
          <nav className="crumb" aria-label="Breadcrumb">
            <span>Zynoa</span><span aria-hidden="true">/</span>
            <strong aria-current="page">{views.find(page => page.key === view)?.title}</strong>
          </nav>
          <div className="top-actions">
            <button className="top-command" type="button" onClick={event => {
              paletteOpenerRef.current = event.currentTarget;
              setPaletteOpen(true);
            }}
              aria-haspopup="dialog" aria-keyshortcuts="Control+Shift+P">⌕ <span>Search or run a command</span> <kbd>Ctrl ⇧ P</kbd></button>
            <button className="top-help" type="button" onClick={openContextHelp} aria-label="Open contextual help (F1)">?</button>
            <span className="avatar" aria-label="Profile not yet configured">Z</span>
          </div>
        </header>
        <div className="content">
          {view === "startup" ? <Startup state={startup} transport={transport} /> :
            view === "workbench" ? <Workbench transport={transport} onNavigate={navigateView}
              shortcuts={shortcuts}
              onRemapShortcut={(target, key) => setShortcuts(current => remapShortcut(current, target, key))}
              onResetShortcuts={() => setShortcuts(defaultShortcuts)} /> :
            view === "gallery" ? <ComponentGallery /> :
            view === "help" ? <HelpCenter contextArticle={helpTopic} destination={helpDestination} /> :
            view === "settings" ? <Settings theme={theme} onTheme={setTheme} density={density} onDensity={setDensity} systemDark={systemDark} reducedMotion={reducedMotion} onReset={() => { setTheme("system"); setDensity("comfortable"); }} onHelp={openContextHelp} /> :
            view === "recovery" ? <Recovery /> :
            view === "changelog" ? <ChangeCenter transport={transport} onHelp={openContextHelp} /> :
            view === "backup" || view === "locations" || view === "updates" ? <SystemCenter key={view} view={view} transport={transport} onHelp={openContextHelp} onDiagnostics={()=>navigateView("diagnostics")} /> : <Diagnostics transport={transport} />}
        </div>
        <footer className="footer"><span>Local-first shared interface · P02</span><span>Native services require verification · <strong>No workspace data stored</strong></span></footer>
      </main>
      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)}
        onNavigate={navigateView}
        onOpenHelp={target => { setHelpDestination(target); setView("help"); }}
        shortcuts={shortcuts} returnFocusTarget={paletteOpenerRef.current} />
    </div>
  );
}
