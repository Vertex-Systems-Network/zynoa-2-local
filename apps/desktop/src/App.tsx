import { useEffect, useState } from "react";
import { probeWorkspaceStatus } from "./ipc";

type View = "startup" | "settings" | "recovery" | "diagnostics";
type StartupState = "starting" | "desktop" | "browser";
type TransportState = "pending" | "connected" | "unavailable" | "preview";
const views: { key: View; title: string; shortcut: string; icon: string }[] = [
  { key: "startup", title: "Overview", shortcut: "1", icon: "⌂" },
  { key: "settings", title: "Settings", shortcut: "2", icon: "⚙" },
  { key: "recovery", title: "Recovery", shortcut: "3", icon: "↺" },
  { key: "diagnostics", title: "Diagnostics", shortcut: "4", icon: "◎" },
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

function Settings() {
  return (
    <section className="detail" aria-labelledby="settings-title">
      <p className="eyebrow">PREFERENCES / RESTRICTED</p><h1 id="settings-title">Settings<span className="period">.</span></h1>
      <p className="lead">Preferences are view-only until the native configuration service has been implemented and tested.</p>
      <div className="setting-row"><div><strong>Interface appearance</strong><p>Theme changes are not available yet.</p></div><select disabled aria-label="Interface appearance" value="dark" onChange={() => undefined}><option value="dark">Dark foundation</option></select></div>
      <div className="setting-row"><div><strong>Application storage</strong><p>Native app-owned locations are registered; user-chosen folders and relocation are not available yet.</p></div><button type="button" disabled>Choose folder</button></div>
      <div className="notice" role="status">These controls do not save preferences or create workspace documents. Startup initializes app-owned local metadata.</div>
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
      if (!event.ctrlKey || event.altKey || event.metaKey || event.shiftKey) return;
      if (!/^[1-4]$/.test(event.key)) return;
      const target = Number(event.key) - 1;
      if (target >= views.length) return;
      event.preventDefault();
      setView(views[target].key);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  // Each view starts at the top; focus the native scroll surface for keyboard PageDown.
  useEffect(() => {
    const surface = document.getElementById("main-content");
    if (surface) {
      surface.scrollTop = 0;
      surface.focus({ preventScroll: true });
    }
  }, [view]);

  return (
    <div className="shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="brand"><span className="brand-symbol" aria-hidden="true">Z</span><span className="brand-word">ZYNOA<small>DESKTOP ENVIRONMENT</small></span></div>
        <p className="nav-label">WORKSPACE</p>
        <nav aria-label="Application sections">
          {views.map((page) => (
            <button key={page.key} className={"nav-link " + (view === page.key ? "selected" : "")} aria-current={view === page.key ? "page" : undefined} type="button" onClick={() => setView(page.key)}>
              <span className="nav-icon" aria-hidden="true">{page.icon}</span><span>{page.title}</span><kbd>⌃{page.shortcut}</kbd>
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom"><span className="version">FOUNDATION BUILD · 0.1.0</span><div className="offline"><span className="dot healthy" /> Local-first shell</div></div>
      </aside>
      <main id="main-content" tabIndex={-1}>
        <header className="topbar"><div className="crumb">Zynoa <span>/</span> <strong>{views.find((page) => page.key === view)?.title}</strong></div><div className="top-actions"><span>PHASE 01</span><span className="avatar" aria-label="Profile not yet configured">Z</span></div></header>
        <div className="content">{view === "startup" ? <Startup state={startup} transport={transport} /> : view === "settings" ? <Settings /> : view === "recovery" ? <Recovery /> : <Diagnostics transport={transport} />}</div>
        <footer className="footer"><span>Local desktop foundation</span><span>Native services require verification · <strong>No workspace data stored</strong></span></footer>
      </main>
    </div>
  );
}
