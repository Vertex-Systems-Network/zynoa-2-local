import { useEffect, useRef, useState } from "react";
import { findHelpOption, helpOptionReferences, optionHelpRoute, resolveOptionHelpRoute, searchHelpOptions } from "./help-options";
import {
  getWizardIssue, getWizardStep, getGuidedTourStep, guidedTourSteps, helpFaq, helpGlossary, helpRoute,
  localBrokenArticleReport, nextWizardStep, offlineHelpContract,
  resolveHelpRoute, validateOfflineHelpCatalog, wikiSourceMappings,
  wizardIssues, type HelpWorkflowMode, type IssueReason,
} from "./help-workflows";

export function LocalArticleReport({ articleId }: { articleId: string }) {
  const [visible, setVisible] = useState(false);
  const [reason, setReason] = useState<IssueReason>("outdated-instructions");
  const [copyState, setCopyState] = useState("");
  const content = localBrokenArticleReport(articleId, reason);
  const copy = async () => {
    if (!content || !navigator.clipboard?.writeText) {
      setCopyState("Copy unavailable. Select the report text and copy it manually.");
      return;
    }
    try {
      await navigator.clipboard.writeText(content);
      setCopyState("Copied locally. Nothing was sent to a server.");
    } catch {
      setCopyState("Clipboard denied. Select and copy the report text manually.");
    }
  };
  return <section className="help-local-report" aria-labelledby="help-report-title">
    <h3 id="help-report-title">Report an article locally</h3>
    <p>Prepare a privacy-safe report to copy yourself. This app does not upload tickets or read your files.</p>
    <button type="button" className="subtle-action" aria-expanded={visible}
      aria-controls="m19-report-body" onClick={() => { setVisible(value => !value); setCopyState(""); }}>
      {visible ? "Hide local report" : "Prepare local report"}
    </button>
    {visible && <div id="m19-report-body" className="help-report-body">
      <label htmlFor="m19-report-reason">Reason</label>
      <select id="m19-report-reason" value={reason}
        onChange={event => { setReason(event.target.value as IssueReason); setCopyState(""); }}>
        <option value="outdated-instructions">Outdated instructions</option>
        <option value="broken-reference">Broken reference</option>
        <option value="unreadable-article">Unreadable article</option>
      </select>
      <label htmlFor="m19-report-payload">Local report (no personal content)</label>
      <textarea id="m19-report-payload" readOnly rows={8} value={content ?? "Invalid article reference"} />
      <button type="button" className="subtle-action" disabled={!content} onClick={() => void copy()}>
        Copy report locally
      </button>
      <p role="status">{copyState || "Not sent. Copy only if you choose."}</p>
    </div>}
  </section>;
}

type WorkflowsProps = {
  mode: Exclude<HelpWorkflowMode, "articles">;
  onOpenArticle: (articleId: string) => void;
  initialOptionId?: string;
};

export function HelpWorkflows({ mode, onOpenArticle, initialOptionId }: WorkflowsProps) {
  const selectedOptionHeadingRef = useRef<HTMLHeadingElement>(null);
  const [issueId, setIssueId] = useState(wizardIssues[0].id);
  const [optionQuery, setOptionQuery] = useState("");
  const [optionModule, setOptionModule] = useState<"All" | "M02" | "M19">("All");
  const [selectedOptionId, setSelectedOptionId] = useState(initialOptionId && findHelpOption(initialOptionId) ? initialOptionId : "M02-OPT-01");
  const [optionRouteText, setOptionRouteText] = useState("help://option/M02-OPT-01");
  const [tourIndex, setTourIndex] = useState(0);
  const [index, setIndex] = useState(0);
  const [resolved, setResolved] = useState(false);
  const [exhausted, setExhausted] = useState(false);
  const [routeText, setRouteText] = useState("help://article/quick-start");
  const [checkResults, setCheckResults] = useState<readonly string[] | null>(null);

  // Select incoming global-search options even if the Help view is already open.
  useEffect(() => {
    if (initialOptionId && findHelpOption(initialOptionId)) {
      setOptionQuery("");
      setOptionModule("All");
      setSelectedOptionId(initialOptionId);
      setOptionRouteText("help://option/" + initialOptionId);
    }
  }, [initialOptionId]);
  // Deep-linked option Help is a keyboard destination, not just a visual
  // filter change. Move focus to the actual selected heading after both the
  // app view-focus effect and palette-unmount recovery have completed.
  // This keeps the destination discoverable by Windows UI Automation and
  // by assistive technology rather than leaving focus on stale search results.
  useEffect(() => {
    if (mode !== "options" || !initialOptionId ||
        selectedOptionId !== initialOptionId || !findHelpOption(initialOptionId)) return;
    let secondFrame = 0;
    const firstFrame = window.requestAnimationFrame(() => {
      secondFrame = window.requestAnimationFrame(() => {
        selectedOptionHeadingRef.current?.focus({ preventScroll: false });
      });
    });
    return () => {
      window.cancelAnimationFrame(firstFrame);
      if (secondFrame) window.cancelAnimationFrame(secondFrame);
    };
  }, [mode, initialOptionId, selectedOptionId]);

  const issue = getWizardIssue(issueId);
  const step = getWizardStep(issueId, index);
  const resolvedRoute = resolveHelpRoute(routeText.trim());
  const tourStep = getGuidedTourStep(tourIndex);
  const optionResults = searchHelpOptions(optionQuery, optionModule);
  const selectedOption = optionResults.find(option => option.id === selectedOptionId) ?? optionResults[0];
  const validOptionRoute = resolveOptionHelpRoute(optionRouteText.trim());

  if (mode === "options") return <section className="help-tool-panel" aria-labelledby="help-options-title">
    <p className="eyebrow">M02 + M19 / OFFLINE OPTION REFERENCE</p>
    <h2 id="help-options-title">Every shared setting, explained.</h2>
    <p>16 local entries with defaults, keyboard/workflow instructions, limitations and recovery. No external service is contacted.</p>
    <div className="help-option-filters">
      <label className="help-tool-field" htmlFor="help-options-search">
        <span>Filter options</span>
        <input id="help-options-search" type="search" maxLength={100}
          value={optionQuery} onChange={event => setOptionQuery(event.target.value)}
          placeholder="Try focus, theme, offline or M19-OPT-06" />
      </label>
      <label className="help-tool-field" htmlFor="help-options-module">
        <span>Module</span>
        <select id="help-options-module" value={optionModule}
          onChange={event => setOptionModule(event.target.value as "All" | "M02" | "M19")}>
          <option value="All">All modules</option><option value="M02">M02 interface</option><option value="M19">M19 Help</option>
        </select>
      </label>
    </div>
    <div className="help-option-layout">
      <div className="help-option-list" role="group" aria-label="Bundled option descriptions">
        <p role="status">{optionResults.length} of {helpOptionReferences.length} local options</p>
        {optionResults.map(option =>
          <button type="button" key={option.id} aria-pressed={selectedOption?.id === option.id}
            onClick={() => setSelectedOptionId(option.id)}>
            <code>{option.id}</code><span>{option.title}</span>
          </button>)}
        {!optionResults.length && <p role="status">No matching options. Clear the text and choose All modules.</p>}
      </div>
      {selectedOption ? <article className="help-option-detail" role="region" aria-labelledby="help-selected-option-title">
        <span className="small-caps">{selectedOption.id} / {selectedOption.availability.toUpperCase()}</span>
        <h3 id="help-selected-option-title" tabIndex={-1} ref={selectedOptionHeadingRef}>{selectedOption.title}</h3>
        <dl>
          <dt>Default</dt><dd>{selectedOption.defaultState}</dd>
          <dt>How to use</dt><dd>{selectedOption.interaction}</dd>
          <dt>Limits & privacy</dt><dd>{selectedOption.limits}</dd>
          <dt>Recovery / undo</dt><dd>{selectedOption.recovery}</dd>
        </dl>
        <p className="help-tool-muted">Internal route: <code>{optionHelpRoute(selectedOption.id)}</code></p>
        <button type="button" className="subtle-action"
          onClick={() => onOpenArticle(selectedOption.articleId)}>Read full bundled guide</button>
      </article> : <div className="help-option-detail" role="status">No option selected for this filter.</div>}
    </div>
    <div className="help-option-route-checker">
      <label className="help-tool-field" htmlFor="help-option-route">
        <span>Validate a local option route (help://option/...)</span>
        <input id="help-option-route" maxLength={80} value={optionRouteText}
          onChange={event => setOptionRouteText(event.target.value)} />
      </label>
      <p role="status">{validOptionRoute ? "Known bundled option ID; no network opened." :
        "Unknown or invalid option route. Nothing opened."}</p>
      <button type="button" className="subtle-action" disabled={!validOptionRoute}
        onClick={() => { if (validOptionRoute) {
          setOptionModule("All"); setOptionQuery(""); setSelectedOptionId(validOptionRoute.id);
        } }}>Open verified local option</button>
    </div>
  </section>;

  if (mode === "tour") return <section className="help-tool-panel" aria-labelledby="help-tour-title">
    <p className="eyebrow">M19 / GUIDED LOCAL ONBOARDING</p>
    <h2 id="help-tour-title">Learn the real interface, step by step.</h2>
    <p>Five local lessons. No file, account, remote service or window is changed.</p>
    {tourStep ? <div className="help-tour-card" role="region" aria-label="Current guided tour step">
      <p className="small-caps">STEP {tourIndex + 1} OF {guidedTourSteps.length}</p>
      <h3>{tourStep.title}</h3><p>{tourStep.instruction}</p>
      <button type="button" className="subtle-action" onClick={() => onOpenArticle(tourStep.articleId)}>Read related offline guide</button>
      <div className="help-wizard-actions">
        <button type="button" className="text-action" disabled={tourIndex === 0}
          onClick={() => setTourIndex(current => Math.max(0, current - 1))}>Previous lesson</button>
        <button type="button" className="gold-action" onClick={() => setTourIndex(current => Math.min(guidedTourSteps.length, current + 1))}>
          {tourIndex === guidedTourSteps.length - 1 ? "Finish guided tour" : "Next lesson"}</button>
        <button type="button" className="subtle-action" disabled={tourIndex === 0}
          onClick={() => setTourIndex(0)}>Restart tour</button>
      </div>
    </div> : <div className="help-tour-card" role="status" aria-live="polite">
      <h3>All five lessons viewed</h3>
      <p>No workspace, preferences or native services were changed.</p>
      <button type="button" className="gold-action" onClick={() => setTourIndex(0)}>Restart tour</button>
    </div>}
  </section>;

  if (mode === "troubleshoot") return <section className="help-tool-panel" aria-labelledby="help-troubleshoot-title">
    <p className="eyebrow">M19 / OFFLINE RECOVERY WIZARD</p>
    <h2 id="help-troubleshoot-title">Find a safe recovery path.</h2>
    <p>Choose a problem. The next step is based on your response and never invokes a native repair command.</p>
    <label className="help-tool-field" htmlFor="help-issue-picker">
      <span>What are you trying to fix?</span>
      <select id="help-issue-picker" value={issueId} onChange={event => {
        setIssueId(event.target.value); setIndex(0); setResolved(false); setExhausted(false);
      }}>
        {wizardIssues.map(item => <option key={item.id} value={item.id}>{item.title}</option>)}
      </select>
    </label>
    <p className="help-tool-muted">{issue?.summary}</p>
    {resolved ? <div className="help-tool-result" role="status">
      <h3>Resolved for this session</h3>
      <p>The wizard has not changed your files, preferences or native services.</p>
      <button className="subtle-action" type="button"
        onClick={() => { setIndex(0); setResolved(false); setExhausted(false); }}>Run again</button>
    </div> : exhausted ? <div className="help-tool-result" role="status">
      <h3>More help is needed</h3>
      <p>All local suggestions have been shown. No remote ticket was sent.</p>
      {step && <button type="button" className="subtle-action" onClick={() => onOpenArticle(step.articleId)}>Read relevant article</button>}
      {step && <LocalArticleReport articleId={step.articleId} />}
      <button type="button" className="subtle-action" onClick={() => { setIndex(0); setExhausted(false); }}>Start over</button>
    </div> : step && <div className="help-wizard-step">
      <p className="small-caps">STEP {index + 1} OF {issue?.steps.length}</p>
      <h3>{step.title}</h3>
      <p>{step.instruction}</p>
      <button type="button" className="subtle-action" onClick={() => onOpenArticle(step.articleId)}>Read this offline article</button>
      <div className="help-wizard-actions">
        <button type="button" className="gold-action" onClick={() => setResolved(true)}>This fixed it</button>
        <button type="button" className="subtle-action" onClick={() => {
          const next = nextWizardStep(issueId, index);
          if (next === null) setExhausted(true);
          else setIndex(next);
        }}>{nextWizardStep(issueId, index) === null ? "Still stuck — see options" : "Still stuck — next step"}</button>
        {index > 0 && <button type="button" className="text-action" onClick={() => setIndex(value => Math.max(0, value - 1))}>Previous step</button>}
      </div>
    </div>}
  </section>;

  if (mode === "faq") return <section className="help-tool-panel" aria-labelledby="help-faq-title">
    <p className="eyebrow">M19 / FAQ & GLOSSARY</p>
    <h2 id="help-faq-title">Practical answers, no network.</h2>
    <div className="help-faq-grid">
      <div><h3>Frequently asked questions</h3>
        {helpFaq.map(item => <details key={item.id} className="help-faq-entry">
          <summary>{item.question}</summary><p>{item.answer}</p>
          <button className="subtle-action" type="button" onClick={() => onOpenArticle(item.articleId)}>Read related guide</button>
        </details>)}
      </div>
      <div><h3>Glossary</h3>
        <dl className="help-glossary-entries">
          {helpGlossary.map(item => <div key={item.term}><dt>{item.term}</dt><dd>{item.definition}</dd></div>)}
        </dl>
      </div>
    </div>
  </section>;

  return <section className="help-tool-panel" aria-labelledby="help-wiki-title">
    <p className="eyebrow">M19 / LOCAL DOCUMENT MAP</p>
    <h2 id="help-wiki-title">Offline links and Wiki sources.</h2>
    <p>These Wiki Markdown files are source-controlled references. A hosted Wiki has not been published or synced.</p>
    <div className="help-wiki-mappings">
      {wikiSourceMappings.map(mapping => <article className="help-wiki-row" key={mapping.id}>
        <div><strong>{mapping.title}</strong><code>{mapping.source}</code>
          <small>Source preview · remote publication not verified</small></div>
        <button className="subtle-action" type="button" onClick={() => onOpenArticle(mapping.articleId)}>Open related offline guide</button>
      </article>)}
    </div>
    <div className="help-route-checker">
      <h3>Validate a local Help link</h3>
      <label className="help-tool-field" htmlFor="help-local-route">
        <span>Local route (help://article/...)</span>
        <input id="help-local-route" type="text" maxLength={120} value={routeText}
          onChange={event => setRouteText(event.target.value)} />
      </label>
      <p role="status">{resolvedRoute
        ? "Valid local article reference; no network required."
        : "Unrecognized or broken local article reference. Nothing was opened."}</p>
      <button type="button" disabled={!resolvedRoute} className="subtle-action"
        onClick={() => { if (resolvedRoute) onOpenArticle(resolvedRoute); }}>Open verified offline reference</button>
      <button type="button" className="subtle-action"
        onClick={() => setCheckResults(validateOfflineHelpCatalog())}>Check bundled article and Wiki mappings</button>
      {checkResults !== null && <p role="status">{checkResults.length === 0
        ? "All built-in article, FAQ, wizard and Wiki-source references are valid."
        : "Found " + checkResults.length + " source mapping issue(s): " + checkResults.join("; ")}</p>}
      <p className="help-tool-muted">Catalog {offlineHelpContract.catalog_version} · {offlineHelpContract.article_count} articles · offline only.
        A checked local route does not establish that the hosted GitHub Wiki is online.</p>
    </div>
    <p className="help-tool-muted">Example: {helpRoute("quick-start")}.</p>
  </section>;
}
