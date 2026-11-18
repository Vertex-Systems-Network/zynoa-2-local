# Professional Desktop UI Design System — P02 Freeze Criteria

## Goal
A purpose-built, high-density yet approachable desktop AI workbench; not a literal clone of Claude/Cursor/Figma proprietary artwork. Design must optimize actual workflows and stay coherent across future modules.

## Navigation architecture
1. Persistent left rail: Home, Chat, Code, Research, Design, Models, Projects, Tools.
2. Expandable project/context sidebar; main tabbed workspace; optional right inspector for properties/evidence/model details.
3. Bottom context-sensitive console (logs, terminal, search results, downloads) and global top task/status strip.
4. Command palette, keyboard shortcuts, searchable settings and in-app onboarding.
5. Responsive resizing for desktop, Windows scaling, reduced motion and high contrast.

## Required screen blueprints, P02
- Onboarding (welcome, device check, runtime discovery, permissions policy, result summary)
- Home (recent projects, recent tasks, model state, intelligent recommendations)
- Workspace shell (multi-tabs, sidebar navigation, bottom console, inspector)
- Chat states (empty, streaming, attached files, tool status, error, offline)
- Coding states (file tree, Monaco editor, diff, terminal, Git, tests, errors)
- Model gallery/detail/download states
- Research source/citation states
- Design canvas shell with layer tree and properties (P08 engine implemented later)
- Tasks/queue, agent trace, runtime monitor, security center, settings and diagnostics

## Tokens and visual language
- Semantic token roles: surface/base, surface/raised, panel, border/subtle, text/primary, text/secondary, accent, success, warning, destructive, focus, selection; dark and light themes.
- 4px rhythm; spacing 4/8/12/16/24/32; 4/8/12 radii only when justified; type scale 11/12/13/14/16/20/24 for dense desktop UI; minimum 44px touch only where touch context requires it.
- Neutral surfaces with restrained accent; no excess gradients, dashboard gimmicks or decorative cards in working views.
- Icons from single consistent library; avoid mixing metaphor styles. High-density details can use compact text but remain legible.
- Reusable components: Button, Input, Select, Tree, Splitter, Tabs, Panel, Dialog, CommandMenu, Toast, VirtualList, FileRow, ModelCard, StatusIndicator, DiffViewer, AgentStep, EvidenceCard, CanvasToolbar.
- Standard states: idle, loading, progress, partial, success, offline, error, empty, disabled, denied; no false 'ready' badges.

## P02 definition of 'final GUI'
Freeze the layout primitives, tokens, navigation, component API, documented per-module UX contracts, keyboard/focus behavior, and screenshot acceptance baseline. Do **not** freeze future feature-specific screens forever or call a mock interactive module operational. The feature modules in P03+ fill real functionality into the locked shell.

## Research and comparisons
Study Claude (conversation simplicity), Cursor/VS Code (workbench productivity), Figma/Penpot (canvas/layer/component patterns), and modern native desktop apps. Record exact pattern, user benefit, weakness, implementation/licensing constraints and proposed original variation in `docs/research/OPTIONS_BANK.md`. No copy-pasting proprietary UI source/assets.

## Dedicated P08 Figma-like editor
Must use a document scene graph with stable IDs; node types FRAME, GROUP, VECTOR, TEXT, IMAGE, COMPONENT, INSTANCE; component definitions; variant props; auto-layout/constraints; align/distribute; snapping; zoom/pan; layers and properties; undo/redo; autosave; asset library; token bindings; export formats. An editable canvas cannot be replaced by generated image previews. Candidate engine: Konva/react-konva (MIT, validate performance); compare Fabric.js and custom renderers. Penpot for architectural reference; check license before any code reuse. tldraw SDK is not assumed free for production.
