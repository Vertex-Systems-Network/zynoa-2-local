import csv, json, pathlib
root=pathlib.Path(__file__).resolve().parents[1]
phases=[
 ('P00','governance','Governance, options bank, autonomous dev loop'),
 ('P01','foundation','Rust/Tauri core, SQLite, hardware probe'),
 ('P02','professional-gui','Professional shell, component system, UX baselines'),
 ('P03','chat','Real local chat, persistence, model streaming'),
 ('P04','coding','Coding Studio, tools, Git, tests and rollback'),
 ('P05','model-intelligence','Hardware ranking, catalog, fast downloads'),
 ('P06','research-browser','Web search, browser, citation-backed research'),
 ('P07','knowledge-memory','File knowledge, retrieval and advanced memory'),
 ('P08','design-studio','Editable Figma-style Design Studio'),
 ('P09','media','Optional media workflows / ComfyUI'),
 ('P10','agents','Advanced agents and workflows for end users'),
 ('P11','release','Reliability, security and production release'),
 ('P12','extension-platform','Post-v1 extensions and platforms'),
]
manifest={"schema_version":1,"phase_order":[],"merge_policy":{"one_active_delivery_phase":True,"one_primary_pr":True,"next_branch_only_after_verified_merge":True,"auto_merge_requires_checks":True,"outside_workspace_actions":"deny"}}
for k,slug,title in phases:
    manifest['phase_order'].append({"id":k,"slug":slug,"title":title,"branch":f"phase/{k[1:]}-{slug}","status":"PLANNED","completion":"merged SHA on protected main plus tests and evidence"})
(root/'docs/state/PHASES.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
patterns=[
('Navigation','Workspace left rail','Cursor/VS Code','Fast tool switch and spatial memory'),
('Navigation','Expandable project sidebar','VS Code','Project context without permanent width tax'),
('Navigation','Command palette','VS Code','Keyboard-first discoverability'),
('Navigation','Tab persistence','VS Code','Recover multi-task context'),
('Navigation','Breadcrumb hierarchy','Figma/VS Code','Understand nested project/location'),
('Layout','Resizable split panes','Cursor','Customizable working density'),
('Layout','Right property inspector','Figma','Inspect selection without page change'),
('Layout','Bottom console and problems','VS Code','See logs while staying in workspace'),
('Layout','Dockable panels','Modern IDEs','Customize information visibility'),
('Layout','Compact status bar','VS Code','Continuous state without interrupting flow'),
('Chat','Focused conversation composer','Claude','Lower composition friction'),
('Chat','Model picker and mode badges','AI chat workbenches','Clear model/mode selection'),
('Chat','Message edit and regenerate','ChatGPT','Iteration with context'),
('Chat','Streaming token state','Claude','Prompt feedback and perception of speed'),
('Chat','Artifacts or output split-view','AI workbenches','Compare answer with output'),
('Chat','Tool trace timeline','Agent interfaces','Explain actual actions'),
('Chat','Context usage inspector','Developer AI tools','Prevent silent context loss'),
('Chat','Conversation branch navigation','AI chat clients','Explore alternatives reversibly'),
('Coding','Code file tree with filters','VS Code','Find working files quickly'),
('Coding','Inline diff decorations','Cursor','Review edits in place'),
('Coding','Terminal with command provenance','IDEs','Make agent commands auditable'),
('Coding','Problems list + test results','VS Code','Fix detected failures'),
('Coding','Git branch and PR status','GitHub/IDEs','Stay aligned with phase workflow'),
('Coding','Checkpoints and rollback','Coding agents','Safe autonomous editing'),
('Coding','Code references panel','IDEs','Navigate symbols and definitions'),
('Research','Source result split view','Research apps','Review claims against evidence'),
('Research','Citation click-through','Research apps','Trace output to actual page'),
('Research','Evidence quality flags','Research apps','Distinguish strong/weak sourcing'),
('Research','Research notebook','Notebook tools','Persist and organize findings'),
('Research','Query/history exploration','Search UIs','Reproduce research'),
('Models','Compatibility reason tags','Model managers','Explain hardware feasibility'),
('Models','Model memory/VRAM estimator','Model runners','Avoid unsafe downloads/loads'),
('Models','Download state and verification','Download managers','Recover from interruption'),
('Models','Quality and speed eval history','Benchmark tools','Measure not guess'),
('Models','Per-task model profile','Local AI clients','Match model to intent'),
('Design','Canvas with layers and frames','Figma/Penpot','True editable layout'),
('Design','Properties inspector and variants','Figma/Penpot','Editable components and states'),
('Design','Auto-layout controls','Figma/Penpot','Responsive structured designs'),
('Design','Component library and tokens','Penpot','Consistent design and reuse'),
('Design','Zoom/pan/minimap','Figma','Navigate large documents'),
('Design','History + undo/redo','Figma','Non-destructive iteration'),
('Design','Asset selection/library','Design tools','Find reusable resources'),
('System','Hardware diagnostics view','System monitors','Transparent performance limits'),
('System','Background queue with checkpoints','Workflow apps','Unattended execution clarity'),
('System','Scoped security/audit log','Security dashboards','Trust and inspection'),
('System','Offline/degraded modes','Native apps','Reliable handling of connectivity'),
('System','Multi-window restore state','Desktop apps','Consistent workspace continuity'),
]
with (root/'docs/research/UI_PATTERN_BANK.csv').open('w',encoding='utf8',newline='') as f:
    writer=csv.writer(f)
    writer.writerow(['category','pattern','reference_to_research','intended_benefit','source_url','research_date','validated','own_implementation_note'])
    for item in patterns: writer.writerow([*item,'','','NO','Research pattern and implement independently'])
model_policy={"version":1,"ranking_principle":"Hard feasibility & policy filters first. Then task-specific weighted, measured scores with confidence.","weights":{"task_quality":0.30,"memory_and_stability":0.25,"measured_speed":0.15,"agent_tool_reliability":0.15,"context":0.05,"trust_and_license":0.05,"local_availability":0.05},"profiles":[{"id":"fast","intended_role":"classification, summaries, lightweight chat"},{"id":"balanced","intended_role":"general user chat, everyday coding"},{"id":"deep_reasoning","intended_role":"complex plans, architecture, review"},{"id":"code","intended_role":"repo editing and tests"},{"id":"vision","intended_role":"image comprehension"},{"id":"embeddings","intended_role":"knowledge retrieval"},{"id":"image_generation","intended_role":"creative raster generation"}],"mandatory_filters":["license_compliant","runtime_backend_available","modality_supported","free_memory_and_disk_fit","required_tools_verified","security_trust_status_acceptable"],"missing_benchmarks":"UNVERIFIED; benchmark before claiming performance"}
(root/'docs/architecture/MODEL_ROUTING.json').write_text(json.dumps(model_policy,indent=2)+'\n',encoding='utf8')
print(f'{len(phases)} phases, {len(patterns)} UI research patterns, routing policy created')
