import { useRef, useState } from "react";
import type { AppView } from "./commands";

type Transport = "pending" | "connected" | "unavailable" | "preview";
const panes = [
  { key: "status", title: "Runtime status" },
  { key: "layout", title: "Layout controls" },
  { key: "keyboard", title: "Keyboard guide" },
] as const;

export function Workbench({ transport, onNavigate }: {
  transport: Transport;
  onNavigate: (view: AppView) => void;
}) {
  const [active, setActive] = useState<(typeof panes)[number]["key"]>("status");
  const [split, setSplit] = useState(40);
  const tabs = useRef<(HTMLButtonElement | null)[]>([]);
  const activate = (index: number) => {
    const next = panes[index];
    setActive(next.key);
    tabs.current[index]?.focus();
  };
  const tabKeys = (event: React.KeyboardEvent<HTMLButtonElement>, index: number) => {
    const key = event.key;
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(key)) return;
    event.preventDefault();
    if (key === "Home") activate(0);
    else if (key === "End") activate(panes.length - 1);
    else activate((index + (key === "ArrowRight" ? 1 : -1) + panes.length) % panes.length);
  };

  return <section className="studio-page" aria-labelledby="workbench-title">
    <div className="section-heading">
      <div><p className="eyebrow">M02 / SHARED WORKBENCH</p>
        <h1 id="workbench-title">A calm space for <em>focused work.</em></h1>
        <p className="lead">A real, keyboard-accessible interface foundation. Project creation and editing stay unavailable until their native services are verified.</p>
      </div>
      <div className="heading-actions">
        <button className="subtle-action" onClick={() => onNavigate("help")} type="button">Open help <span aria-hidden="true">↗</span></button>
        <button className="gold-action" type="button" disabled title="No workspace creation service yet">New workspace +</button>
      </div>
    </div>
    <div className="workbench-tabs" role="tablist" aria-label="Workbench panels">
      {panes.map((pane, index) =>
        <button ref={node => { tabs.current[index] = node; }} key={pane.key}
          type="button" role="tab" id={"workbench-tab-" + pane.key}
          aria-controls={"workbench-panel-" + pane.key}
          aria-selected={active === pane.key} tabIndex={active === pane.key ? 0 : -1}
          className={active === pane.key ? "active" : ""}
          onKeyDown={event => tabKeys(event, index)} onClick={() => setActive(pane.key)}>
          {pane.title}
        </button>
      )}
    </div>
    <div role="tabpanel" tabIndex={0} id="workbench-panel-status"
      aria-labelledby="workbench-tab-status" className="workbench-tabpanel" hidden={active !== "status"}>
      <div className="workbench-grid">
        <article className="studio-card studio-card-feature">
          <span className="small-caps">LOCAL RUNTIME</span>
          <h2>{transport === "connected" ? "Native bridge available" :
            transport === "preview" ? "Preview without native bridge" :
            transport === "unavailable" ? "Native bridge unavailable" : "Checking native bridge"}</h2>
          <p>{transport === "connected"
            ? "Read-only status handshake verified. A workspace has not yet been configured."
            : "This status is not proof of a usable project. Open the native desktop application to verify its service connection."}</p>
          <span className="soft-chip">No cloud dependency</span>
        </article>
        <article className="studio-card">
          <span className="small-caps">NEXT CAPABILITY</span>
          <h2>Workspace canvas</h2>
          <p>Project editing belongs to a later verified module. This shared workbench does not fabricate documents or files.</p>
          <button type="button" disabled className="subtle-action">Open canvas</button>
        </article>
      </div>
    </div>
    <div role="tabpanel" tabIndex={0} id="workbench-panel-layout"
      aria-labelledby="workbench-tab-layout" className="workbench-tabpanel" hidden={active !== "layout"}>
      <div className="studio-card">
        <div className="flex-between">
          <div><span className="small-caps">M02-OPT-06</span>
            <h2>Adjust the pane split</h2>
            <p>Preview a responsive split workbench. The layout applies only to this session.</p>
          </div>
          <output htmlFor="split-control" className="value-bubble">{split}%</output>
        </div>
        <input id="split-control" aria-label="Left pane width" type="range" min={25} max={65} step={5}
          value={split} aria-valuetext={`${split}% left pane`} onChange={event => setSplit(Number(event.target.value))} />
        <div className="split-preview" style={{ gridTemplateColumns: `minmax(0, ${split}fr) minmax(0, ${100 - split}fr)` }}>
          <div><b>Navigation pane</b><small>Adjust with arrow keys</small></div>
          <div><b>Content pane</b><small>Responds to available width</small></div>
        </div>
      </div>
    </div>
    <div role="tabpanel" tabIndex={0} id="workbench-panel-keyboard"
      aria-labelledby="workbench-tab-keyboard" className="workbench-tabpanel" hidden={active !== "keyboard"}>
      <div className="studio-card">
        <span className="small-caps">ACCESSIBLE BY DEFAULT</span>
        <h2>Keyboard workflow</h2>
        <div className="shortcut-grid">
          {[
            ["Ctrl + Shift + P", "Open command palette"],
            ["Ctrl + 1…6", "Navigate common views"],
            ["F1", "Open the Help Center"],
            ["← / →", "Switch workbench tabs"],
            ["Esc", "Dismiss command palette"],
          ].map(([keys, label]) =>
            <div className="shortcut-line" key={keys}><kbd>{keys}</kbd><span>{label}</span></div>
          )}
        </div>
      </div>
    </div>
  </section>;
}

export function ComponentGallery() {
  const [sampleInput, setSampleInput] = useState("");
  const [selectedAction, setSelectedAction] = useState<"primary" | "secondary" | null>(null);
  return <section className="studio-page" aria-labelledby="gallery-title">
    <p className="eyebrow">M02 / DESIGN FOUNDATION</p>
    <h1 id="gallery-title">One system.<br /><em>Every detail considered.</em></h1>
    <p className="lead">A living component reference for the desktop shell. Preview states are labeled; they are not evidence of completed backend services.</p>
    <div className="gallery-metrics">
      <div><b>01</b><span>Semantic tokens</span><small>Context-aware colors</small></div>
      <div><b>02</b><span>Accessible states</span><small>Keyboard first</small></div>
      <div><b>03</b><span>No extra runtime</span><small>Local-first foundations</small></div>
    </div>
    <div className="gallery-grid">
      <section className="studio-card">
        <span className="small-caps">FOUNDATIONS / COLORS</span><h2>Semantic palette</h2>
        <div className="swatches">
          {["surface", "surface-raised", "accent", "text-primary", "status-success", "status-warning"].map(token =>
            <div className="swatch-row" key={token}><span className={"swatch swatch-" + token} aria-hidden="true" /><code>{token}</code></div>
          )}
        </div>
      </section>
      <section className="studio-card">
        <span className="small-caps">COMPONENTS / BUTTONS</span><h2>Actions & feedback</h2>
        <div className="component-row" role="group" aria-label="Select a gallery action preview">
          <button className="gold-action" type="button" aria-pressed={selectedAction === "primary"} onClick={() => setSelectedAction("primary")}>Primary action</button>
          <button className="subtle-action" type="button" aria-pressed={selectedAction === "secondary"} onClick={() => setSelectedAction("secondary")}>Secondary</button>
          <button className="gold-action" type="button" disabled title="Unavailable in this foundation preview">Unavailable</button>
        </div>
        <label className="input-label" htmlFor="gallery-text">Example text field</label>
        <input id="gallery-text" value={sampleInput} maxLength={80}
          onChange={event => setSampleInput(event.target.value)}
          placeholder="Type a sample value..." />
        <p className="component-helper" role="status">
          {selectedAction ? `${selectedAction === "primary" ? "Primary" : "Secondary"} action selected (visual preview only). Input text was not changed.`
            : "Select an action to preview its selected state. Nothing is saved."}
        </p>
        <p className="component-helper">Sample input stays independent of action selection and resets when you leave this screen.</p>
      </section>
      <section className="studio-card">
        <span className="small-caps">COMPONENTS / STATUS</span><h2>Clear system states</h2>
        <div className="component-state-list" role="group" aria-label="Illustrative status states, not live service health">
          <div><span className="soft-chip">Ready</span><small>Local preview available</small></div>
          <div><span className="soft-chip pending-chip">Pending</span><small>Awaiting verification</small></div>
          <div><span className="soft-chip warning-chip">Offline</span><small>Remote action not requested</small></div>
          <div><span className="soft-chip error-chip">Error example</span><small>Recovery instruction required</small></div>
        </div>
      </section>
      <section className="studio-card">
        <span className="small-caps">COMPONENTS / TYPE</span><h2>Editorial hierarchy</h2>
        <div className="type-specimen"><b>Heading / 32</b><p>Readable interfaces, without the noise.</p><small>Body / 13 · restrained contrast and generous line-height</small></div>
      </section>
    </div>
  </section>;
}
