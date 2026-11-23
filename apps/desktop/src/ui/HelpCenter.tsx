import { useEffect, useMemo, useState } from "react";
import { findHelpArticle, helpArticles, resolveVisibleHelpArticle, type HelpCategory } from "./help-catalog";
import { LocalArticleReport, HelpWorkflows } from "./HelpWorkflows";
import { offlineHelpContract, requestOfflineHelp, type HelpWorkflowMode } from "./help-workflows";

type Props = { contextArticle?: string };

const categories: readonly (HelpCategory | "All")[] = [
  "All", "Get started", "Interface", "Privacy", "Troubleshooting",
];

export function HelpCenter({ contextArticle }: Props) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<HelpCategory | "All">("All");
  const [articleId, setArticleId] = useState(contextArticle || "quick-start");
  const [showGlossary, setShowGlossary] = useState(false);
  const [mode, setMode] = useState<HelpWorkflowMode>("articles");
  const searchResponse = useMemo(() => requestOfflineHelp({
    schema_version: 1, catalog_version: offlineHelpContract.catalog_version,
    query, category, limit: 50,
  }), [query, category]);
  const results = searchResponse.ok ? searchResponse.matches : [];
  const selected = resolveVisibleHelpArticle(results, articleId);
  const openArticle = (id: string) => {
    setQuery("");
    setCategory("All");
    setArticleId(id);
    setMode("articles");
  };

  useEffect(() => {
    if (contextArticle && findHelpArticle(contextArticle)) openArticle(contextArticle);
  }, [contextArticle]);

  return <section className="help-page" aria-labelledby="help-title">
    <div className="help-hero">
      <div>
        <p className="eyebrow">M19 / LOCAL KNOWLEDGE</p>
        <h1 id="help-title">Answers, right<br /><em>where you work.</em></h1>
        <p className="lead">Browse real, bundled guidance without a network connection.
          Articles describe only verified UI capabilities and clearly mark future services.</p>
      </div>
      <div className="help-offline-indicator" role="status"><span aria-hidden="true">●</span> Offline catalog ready
        <small>{helpArticles.length} built-in articles · catalog {offlineHelpContract.catalog_version} · no cloud search</small>
      </div>
    </div>
    <div className="help-workflow-switch" role="group" aria-label="Offline Help workflows">
      {([
        ["articles", "Articles & search"],
        ["troubleshoot", "Troubleshooting wizard"],
        ["faq", "FAQ & glossary"],
        ["wiki", "Wiki & link checker"],
      ] as const).map(([key, title]) =>
        <button type="button" key={key} className={mode === key ? "selected" : ""}
          aria-pressed={mode === key} onClick={() => setMode(key)}>{title}</button>
      )}
    </div>
    {mode === "articles" ? <>
    <div className="help-search-row">
      <label className="search-control help-search" htmlFor="help-query">
        <span aria-hidden="true">⌕</span>
        <input id="help-query" type="search" maxLength={120}
          value={query} onChange={event => setQuery(event.target.value)}
          placeholder="Search articles, topics, or error recovery…" aria-label="Search offline help" />
        <kbd>LOCAL</kbd>
      </label>
      <label className="visually-hidden" htmlFor="help-filter">Filter help category</label>
      <select id="help-filter" className="help-category" value={category}
        onChange={event => setCategory(event.target.value as HelpCategory | "All")}
        aria-label="Filter help by category">
        {categories.map(item => <option key={item} value={item}>{item === "All" ? "All topics" : item}</option>)}
      </select>
    </div>
    {!searchResponse.ok && <p role="alert" className="help-search-error">
      {searchResponse.code}: {searchResponse.message}
    </p>}
    <div className="help-body">
      <aside className="help-list" aria-label="Help article results">
        <div className="help-list-heading"><b>Explore the library</b><span role="status">{results.length} results</span></div>
        {results.length ? results.map(article =>
          <button key={article.id} type="button"
            className={"help-result " + (article.id === selected?.id ? "active" : "")}
            aria-current={article.id === selected?.id ? "true" : undefined}
            onClick={() => openArticle(article.id)}>
            <span className="help-result-category">{article.category}</span>
            <strong>{article.title}</strong><small>{article.summary}</small>
            <span aria-hidden="true" className="help-result-arrow">↗</span>
          </button>
        ) : <div className="empty-state" role="status">
          <strong>No articles found</strong><p>Try “theme”, “offline”, “native” or clear the category filter.</p>
          <button className="subtle-action" type="button" onClick={() => { setQuery(""); setCategory("All"); }}>Clear filters</button>
        </div>}
        <div className="help-list-footer">
          <b>Need a deeper answer?</b>
          <p>Remote reporting and the hosted Wiki are not configured in this foundation build. Bundled articles remain available offline.</p>
        </div>
      </aside>
      {selected ? <article className="help-article" aria-labelledby="help-article-title">
        <div className="help-breadcrumb"><span>Help Center</span><span aria-hidden="true">/</span><span>{selected.category}</span></div>
        <span className="soft-chip">BUNDLED GUIDE</span>
        <h2 id="help-article-title">{selected.title}</h2>
        <p className="help-article-lead">{selected.summary}</p>
        <div className="help-article-body">
          {selected.sections.map(section =>
            <section key={section.heading}>
              <h3>{section.heading}</h3>
              {section.paragraphs.map(paragraph => <p key={paragraph}>{paragraph}</p>)}
            </section>
          )}
        </div>
        <div className="help-related">
          <b>Continue learning</b>
          <div>
            {selected.related.map(id => {
              const item = findHelpArticle(id);
              return item ? <button key={id} type="button" onClick={() => openArticle(id)}>
                {item.title}<span aria-hidden="true">↗</span>
              </button> : null;
            })}
          </div>
        </div>
        <div className="help-glossary">
          <button type="button" className="glossary-toggle" aria-expanded={showGlossary}
            onClick={() => setShowGlossary(value => !value)}>
            <span><b>Quick glossary</b><small>Common terms in Zynoa</small></span>
            <span aria-hidden="true">{showGlossary ? "−" : "+"}</span>
          </button>
          {showGlossary && <dl>
            <dt>Native handshake</dt><dd>Read-only communication between the window and its local Tauri service.</dd>
            <dt>Theme</dt><dd>Session appearance tokens, not a saved workspace preference.</dd>
            <dt>Offline article</dt><dd>A guide included in the app bundle without a remote request.</dd>
          </dl>}
        </div>
        <div className="help-feedback">
          <div><strong>Found something inaccurate?</strong><p>Remote issue reporting is disabled; use this sanitized, copy-only local report.</p></div>
          <LocalArticleReport articleId={selected.id} />
        </div>
      </article> : <article className="help-article" role="status" aria-labelledby="help-article-title">
        <h2 id="help-article-title">No matching help article</h2>
        <p>Try a different search term or clear the category filter to browse bundled offline guidance.</p>
      </article>}
    </div>
    </> : <HelpWorkflows mode={mode} onOpenArticle={openArticle} />}
  </section>;
}
