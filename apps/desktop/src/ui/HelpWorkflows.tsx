import { useState } from "react";
import {
  getWizardIssue, getWizardStep, helpFaq, helpGlossary, helpRoute,
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
};

export function HelpWorkflows({ mode, onOpenArticle }: WorkflowsProps) {
  const [issueId, setIssueId] = useState(wizardIssues[0].id);
  const [index, setIndex] = useState(0);
  const [resolved, setResolved] = useState(false);
  const [exhausted, setExhausted] = useState(false);
  const [routeText, setRouteText] = useState("help://article/quick-start");
  const [checkResults, setCheckResults] = useState<readonly string[] | null>(null);

  const issue = getWizardIssue(issueId);
  const step = getWizardStep(issueId, index);
  const resolvedRoute = resolveHelpRoute(routeText.trim());

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
