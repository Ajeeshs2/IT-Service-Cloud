# CHANGELOG — aits-org-setup-recipe.updated.md

Source: `.refs/aits-org-setup-recipe/aits-org-setup-recipe.md` (unmodified)
Run: it-service-cloud-bha853 — snapshot, Sharing, IT Service Core, Agentforce, Unified Catalog, SLA, Assignment Rules, Knowledge, Portal, Data Cloud, Embedded chat, CMDB
Change log of record: `docs/recipe-changes.md` (Atlas). Writer of this draft: Sage. Auditor: Echo.
Publish status: **Recipe version 2.0 — not published** (user approves publishing at the end of the run)

## Version 2.0 (2026-11-02)

This release = draft v15.1 + the version and bundle header. It is published as a NEW recipe, "IT Service Cloud Setup Recipe v2"; version 1 stays unchanged as its own reference.

| Version | Date | File | Notes |
|---|---|---|---|
| 2.0 | 2026-11-02 | New reference "IT Service Cloud Setup Recipe v2" (recipe + changelog); bundle on public GitHub `Ajeeshs2/IT-Service-Cloud`, folder `aits-org-setup-recipe/`, tag `v2.0` | Rebuilt, feature-driven recipe; 82 approved changes (detail below) |
| 1 | — | Separate reference "IT Service Cloud Setup Recipe" (unchanged); also GitHub tag `v1.0` | Original, unversioned recipe (sha256 1a65da5d…). Rollback = keep using version 1; no archive folder |

**Versioning rule:** each future update raises the version number and adds a section here (e.g. 2.1 for a small update, 3.0 for a restructure). Earlier versions remain available unchanged (their own reference and git tag), never deleted.

The draft labels below (v1 … v15.1) are internal working drafts of version 2.0.

## Applied to body (Status = approved in recipe-changes.md) — 82 RCs

| RC-id | Status | Sections changed | Summary |
|---|---|---|---|
| RC-id | Status | Sections changed | Summary |
| RC-1 | approved · verified | Step 0 → "Target Organization-Wide Defaults" table | Replaced 28-row table with user-approved 23-row table (row order as given by user). Asset row updated per RC-33 (v6). Verified on it-service-cloud-bha853: 18/18 present objects match, 6 absent skipped |
| RC-2 | approved | Step 0 target table; Phase 1 → "Sharing Settings Audit" query; Step 0 → "Verification query (post-save)"; Step 0 → "UI-to-API name mapping" | Removed Incident, Knowledge (`Knowledge__kav`, incl. "Usually already correct — verify" note), Broadcast Topic, Broadcast Communication, Broadcast Communication Audience |
| RC-3 | approved | Step 0 target table (Inventory Reservation row) | No change — `Controlled by Parent` / `Private` / Skip if absent |
| RC-31 | approved (2026-10-30) | Step 0 → removed "Metadata deploy does NOT work for OWD … MUST be done via the browser UI"; added "Execution model — two levels" + "Level 1 — Programmatic (default)" | Step 0 is programmatic via `sharing/apply_owd.py` + `sharing/aits-step0-sharing.xml` |
| RC-45 | approved (2026-10-30) | Step 0 → Level 1 steps (plan → review → `deploy --confirm` → verify, exit codes 0/2/1); "Level 2 — Browser fallback" heading + scope line wrapping the existing URL / page verification / interaction flow (kept verbatim) | Browser only for rows in generated `sharing/browser-fallback.md`, then `verify` |
| RC-37 | approved (2026-10-30) | Step 0 → note under target table | Inventory Reservation row unchanged; note: untested (object absent on reference org), rejected combination → Level 2 list. Wording corrected per Echo: the RC-37 text said "untested on orgs without the object", which is inverted. Atlas asked to align recipe-changes.md |
| RC-20 + RC-46 | approved (2026-10-30) | Step 0 Level 2 → step 7 replaced, new step 8; "Known pre-existing validation issues" auto-fix replaced with stop-and-ask; Level 1 → note on invalid specs / systemic failures | Save errors on unlisted rows or rejection of a listed row → STOP and ask the user; values change only with approval |
| RC-33 | approved (2026-10-30) | Step 0 table → Asset = Controlled by Parent / Controlled by Parent ("Follows Account"); Phase 1 → Asset note after audit text | Asset follows Account (replaces the earlier decoupled Public Read/Write / Read Only target) |
| RC-39 | approved (2026-10-30) | Step 0 → "Account children" note under target table | Account change cascades to Contact, Order, Asset; plan/verify report them; no extra confirm |
| RC-47 | approved scope (RC-33/39) | Step 0 → note under "Verification query (post-save)" (per Echo v6 audit) | Controlled-by-Parent rows (Asset; Inventory Reservation internal) verified from retrieved object-meta.xml; `verify` does it automatically |
| RC-35 | approved (2026-10-30) | none (packaging) | `recipe/sharing/aits-step0-sharing.xml` + `recipe/sharing/apply_owd.py` bundled with the recipe |
| RC-48 | approved · verified (2026-10-30) | New "## Phase 0: IT Service Enablement (gate)" before Phase 1 (RC-48 text verbatim; "see RC-49" → "see RC-49 (appendix, proposed)"); Recipe Summary (first row); Execution Order block (first line); Optimized execution order (item 0); Feature Selection (mandatory note); Recipe Summary intro sentence "Programmatic Phases (Phase 0 gate, then …)" (v7.1, per Echo) | IT Service Enablement must be ON before any other phase or step; check via `checks/check_it_service_enablement.py` (exit 0/3/1), page fallback |
| RC-52 | approved · verified (2026-10-30) | Phase 3 → "Deploy" replaced with "Deploy (Level 1 — programmatic, XML process)" (RC-52 text + plan/deploy/verify commands, exit codes 0/2/1); Combined-deploy callout now points to the script; Phase 5 and Phase 6 "Deploy" → covered by the Phase 3 script run | Incident + Problem + Change via `settings/apply_settings.py` + `settings/aits-itsm-settings.xml`; target = all flags true except manage=false |
| RC-53 | approved (2026-10-30) | Phase 3 → "Slack broadcasts" note | `enableSlackBroadcastType` not managed (org value preserved) |
| RC-54 | approved (2026-10-30) | Phase 3 → read-then-merge deploy steps removed; flags reference header → "reference only" | Static 35-flag list kept as reference only |
| RC-55 | approved (2026-10-30) | Phase 3 → step 2 now `deploy IncidentMgmt --confirm` (after user approves the plan, once per run); paragraph after exit codes (RC-55 text verbatim: approval scope, split isolation, cap `3 × ceil(log2 n) + 1`, clean stop, `--retry-failed`) | One approval per run; deploy cap scales with batch size |
| RC-56 | approved (2026-10-30) | Phase 3 → note after RC-55 paragraph | Each deploy logged immediately to `settings/<Setting>-deploy-log.jsonl`; interrupt finishes current poll, submits nothing new |
| RC-57 | approved (2026-10-30) | Phase 3 → note after RC-56 | `requires=` flags (e.g. Slack broadcasts) skipped as *not available* unless `--assume-available` |
| RC-58 | approved (2026-10-30) | Operational Learnings → new #23 | After any interruption/rejected action, query DeployRequest (last 15 min) before continuing |
| RC-59 | approved (2026-10-30) | Operational Learning #1 replaced; Error Handling "Merge pattern" bullet → "Settings changes" | Never hand-build IncidentMgmt XML; always plan → approval → `deploy --confirm` → verify via the settings script |
| RC-60 | approved · verified (2026-10-30) | Phase 7 → "Check", "Recommended approach (direct deploy)" XML, "Deploy" bullets and "Alternative (SOAP read)" replaced with "Deploy (Level 1 — programmatic, XML process)" (RC-60 text verbatim + plan/deploy/verify steps) | Release Mgmt via settings script; all 3 flags ON; prerequisite Change Mgmt. Includes the ReleaseMgmt part of RC-51 (enableReleaseEventCreation) |
| RC-65 | approved · verified (2026-10-30) | Feature Selection (1a–1d labels + feature-driven note); Recipe Summary (sentence + rows 1a–1d, Phase 8 row drops "batch with Phase 7"); new "## IT Service Core (Phases 1a–1d — feature-driven)" section (RC-65 text verbatim + status/plan/deploy/verify `--features` steps + numbering note); Phase 3/5/6/7 renamed 1a/1b/1c/1d "(formerly Phase N)"; combined-deploy callout and Phase 5/6 "skip if combined" callouts removed; 1a/1b/1c/1d commands → `--features`; 1d "Batch with Phase 8" callout removed; Execution Order block, optimized order and Parallelization rewritten | Only user-selected IT Service Core features run; prerequisites enforced; IncidentMgmt features combined automatically |
| RC-66 | approved (2026-10-30) | IT Service Core section → "Feature ownership of shared IncidentMgmt flags" table | Which flags each feature owns |
| RC-67 | approved (2026-10-30) | IT Service Core section → "Observed behavior on this org" | All four features selected and ON on it-service-cloud-bha853 |
| RC-65 follow-on renumbering | consequence of RC-65 | Guardrail #1 "(1a–1d, 4–9, 12)"; Guardrail #3 "Phases 1a–1d and 4–12"; Learning #1 "Phases 1a, 1b and 1c"; Learning #22 and Phase 2 header "Phases 1a–1d, 4–9, 12"; Step 15 troubleshooting "(Phase 1a)"; PSG assignment table Phase column 3/5/6/7 → 1a/1b/1c/1d | No other content changed |
| RC-68 | approved · verified offline (2026-10-30) | IT Service Core section → failure-isolation paragraph (RC-68 text verbatim); Phase 1a → RC-52 sentence ("per feature in dependency order") and RC-55 cap sentence ("plus 1 per feature in the file") | Failures isolated per feature in prerequisite order; a feature whose prerequisite is not ON is marked not applied |
| RC-69 | approved (2026-10-30) | Intro sentence (also fixes stale "Phases 1–9, 12" missed in v12); Recipe Summary sentence + row; section heading → "Pre-flight audit (read-only): permission sets/PSGs + sharing settings audit"; Execution Order block; optimized order item 1 | Avoids confusion with IT Service Core Phases 1a–1d. Guardrail #3 and the Learnings had no "Phase 1" references left to change |
| Q6 org exception | closed (user 2026-10-30) | Step 0 → "Observed behavior on this org (it-service-cloud-bha853)" note at end of Step 0 | Asset kept ReadWrite/Read on this org (no revert); `verify` reports Asset as an expected mismatch. Recipe default stays RC-33 |
| RC-44 | approved (2026-10-30) | Guardrails → new "### 5. Availability-Driven Run — Missing Objects Are Never Failures"; Phase 1 audit note; Step 0 Level 1 note; Step 0 "Objects that may be absent" table | Missing objects/features are skipped and reported as *not in org*, never as failures |
| RC-5 | approved (implemented by RC-88) | Pre-flight audit section | Org snapshot & skip map = `checks/preflight.py` |
| RC-9 | approved (2026-10-30) | Learning #19 replaced; Agentforce section "Agent names (RC-9)"; 3b wizard (Employee wizard pattern removed — Employee agent comes from Enhanced Chat); activation + Access Agents fixes and 9d Data Library steps use `<FULFILLER_AGENT>` / `<EMPLOYEE_AGENT>` placeholders | Agents are discovered (Employee = routing-flow target; Fulfiller by template), never hard-coded; other agents ignored |
| RC-68 addendum | approved | IT Service Core → "Script rules" → Exit codes | Later file's prerequisite failed → "not applied", result file written, exit 2; exit 1 only for systemic problems / bad input / prerequisites missing before start |
| RC-70 | approved · settings verified (dry run) | New "## Agentforce (Phases 3a–3e)" (RC-70 text verbatim + settings sentence + commands) with 3a–3e sub-sections; replaces Phase 12 and Steps 2/3c/6/7/8/9/13 | Feature-driven Agentforce phases; 3e optional |
| RC-71 | approved · verified (offline) | IT Service Core → "Script rules" → Prerequisites | Prerequisites enforced on what actually turned ON, within/across files, transitively |
| RC-72 | approved · verified | Agentforce → "Agent checks (RC-72)"; old Steps 3c, 6, 13 removed; verification parts of old Steps 8/9 → "re-run checks/check_agents.py"; Learning #13 points to the check | `checks/check_agents.py` read-only agent/Enhanced Chat checks |
| RC-73 | approved · verified | New "## Unified Catalog (Phases 4a–4c)" (RC-73 text verbatim + commands); old Phase 8 removed | Context Service, Apex templates, UC permissions; Release not a prerequisite |
| RC-74 | approved | IT Service Core → "Script rules"; Feature Selection note; 3e | `--features all` excludes optional phases (3e, 9c) |
| RC-75 | approved (scope RC-73) | IT Service Core → "Script rules"; Unified Catalog note | `status --json`; 4c NOTE on `--features all`; PSG status per row |
| RC-76 | approved · verified | New "## SLA Management (Phases 5a–5c)" (RC-76 text verbatim); old Step 15 kept as "Level 2 reference" with the never-click-Create rule added; Learning #18 points to 5b | 5c optional, user request only |
| RC-77 | approved · verified | IT Service Core → "Permissions (RC-77)"; 1a–1d PSG lists → permissions-script lines; "Permission Set Assignment Pattern" replaced; Guardrail #3 | Permission groups belong to their feature phase; no extra PSGs |
| RC-78 | approved (RC-76 scope) | SLA section → "Check (RC-78)" | `checks/check_sla.py` |
| RC-79 | approved · verified | New "## Assignment Rules (Phases 6a–6c)" (RC-79 text verbatim + commands); old Phase 9 removed; old Step 1 kept as 6c "Level 2 reference" (refs renumbered) | 6a = 4a, 6b BRE permissions, 6c Decision Table Access |
| RC-80 | approved (scope RC-77/79) | Assignment Rules → "Permissions script (RC-80)" | Result file per mode; permission set skipped when its licence isn't assigned |
| RC-81 | approved · verified | New "## Knowledge (Phases 7a–7b)" (RC-81 text verbatim + commands); old Phase 4 removed; Learnings #7 and #16 updated | Knowledge via settings script (suggestedArticles preserved); no Incident prerequisite; numbering 7/8/9 |
| RC-82 | approved | IT Service Core → "Script rules" → Safety | Script refuses to patch a non-unique flag |
| RC-83 | approved · verified | New "## Self-service portal (Phases 8a–8c)" (RC-83 text verbatim + check + org note); old Step 10 kept as "create a new site" reference (sub-steps renumbered 1–4; existing-site and template checks moved to 8a/8b) | Choose an existing site by template; create only if the user chooses |
| RC-84 | approved | New "## Embedded chat on the portal (Phases 10a–10c)" (RC-84 text verbatim + help article + org note); replaces old Step 14 | 10a/10b checked; 10c manual |
| RC-85 | approved · verified | New "## Phase 1e: Notification Service [mandatory]" (RC-85 text verbatim); 1d "Optional features → Notification Service" bullets removed; IT Service Core intro | Mandatory, always runs |
| RC-86 | approved · verified | New "## CMDB & Service Graph (Phases 11a–11c)" (RC-86 text verbatim + check + org note); old Steps 3/3b kept as "Level 2 reference" | CMDB checks + page confirmations; browser only with approval |
| RC-87 | approved · verified (check only) | Phase 3c (RC-87 text verbatim); old Step 2 kept as "Level 2 reference — Enhanced Chat page" (interaction flow points to 3c; Phase 12 refs → 3b) | Enhanced Chat turn-on is part of 3c |
| RC-88 | approved · verified | "## Pre-flight audit" (RC-88 text + performance + hardening, verbatim); old permission-set/PSG queries removed; sharing audit query + RC-44/RC-33 notes kept as "manual equivalent, reference" | `checks/preflight.py` runs first, every run |
| RC-89 | approved (2026-11-02) | New "## Data Cloud (Phases 9a–9d — ALWAYS LAST)" (RC-89 text verbatim + commands + org note); old Phase 2 and Phase 12 PII-masking text removed; old Steps 11/12 kept as 9d references; Guardrail #1, Learnings #9/#22 renumbered | Data Cloud last; never cancel the background install; 9c optional |
| RC-91 | approved · verified (dry run) | 3a (prompt template PSs via `apply_permissions.py --features platform`); Data Cloud 9b (GenieAdmin via `--features datacloud`; "Data Cloud User Enhanced Security" = MANUAL step after provisioning); Permission Set Assignment Pattern | Closes the two spec gaps Sage flagged in v14 |
| RC-49 | approved — UNTESTED | Phase 0 → "If OFF (RC-49, UNTESTED)" (recipe text verbatim) | Level 2 browser turn-on, then re-run the check |
| RC-90 | approved as note | Phase 1e → "Follow-on template deploy (RC-90, note)" | Templates are customer-customised: the recipe does not create or fix them; observation only |
| RC-89 (update) | approved | Data Cloud intro text re-synced verbatim (9c in a LATER run; 9d separate follow-up run, original browser steps kept); command list 9c/9d wording | — |
| 9d Steps 11/12 | user decision 2026-11-02 (RC-89) | Original Step 11 and Step 12 text restored VERBATIM from the source recipe (v14 had renamed headings and renumbered references); only RC-9 agent placeholders differ (12 lines); "run only after provisioning, separate follow-up run" note above, incl. the RC-19 provisioned check | Note: the verbatim text keeps its original cross-references (e.g. "Step 7/8", "Phase 4") by design |
| RC-21 | approved (recommended set) | Step 0 → callout under the target table (verbatim) | Warn: Product Classification (+Attr) internal access reduced |
| RC-32 | approved (recommended set) | Step 0 Level 1 → note (verbatim) | Reductions show after ~2 min; re-verify before reporting mismatches |
| RC-34 | approved (recommended set) | Step 0 Level 1 → note | Contract follows Account — deploy Account only |
| RC-38 | approved (recommended set) | Step 0 Level 1 step 2 (verbatim) | List all reductions to the user and get approval before `deploy --confirm` |
| RC-36, RC-40, RC-42, RC-43 | approved (recommended set) | none — script-only (`sharing/apply_owd.py`) | Fresh retrieve, robustness, own work project, queue guard |
| RC-63 | approved (recommended set) | Operational Learning #2 replaced (verbatim) | ReleaseMgmt read via Metadata API retrieve; no SOAP/token handling |
| RC-64 | approved (recommended set) | Error Handling "SOAP token issues" → "Settings reads" (verbatim) | — |
| RC-12 | approved (recommended set) | Satisfied by RC-63/RC-64 and the settings script (old Phase 8/9/12 SOAP checks were removed in v14) | — |
| RC-14 | approved (recommended set) | Learning #3; Deployment Helper queue rule; Error Handling "Deploy queue stuck" | Cancel only your own deploy — check `DeployRequest.CreatedBy`; never Automated Process |
| RC-23 | approved (recommended set) | New Operational Learning #24 (verbatim) | Sandbox tooling: no jq; literal org alias |
| RC-27 | approved (recommended set) | Learning #5; Permission pattern licence note; Error Handling licence bullet (verbatim) | UnifiedCatalogCommunityUserPsl failure is informational |
| RC-50 | approved (recommended set) | Phase 1d → "Check (RC-50)" | Read ReleaseMgmt via retrieve; never infer from PSG presence |
| RC-61 | approved (recommended set) | Phase 1d "Optional features" removed (Notification sub-bullets had already moved to 1e) | — |
| RC-11 | approved (recommended set) | SLA reference: org-specific "1 of 5 Steps Completed" removed; template-org note | — |
| RC-22 | approved (recommended set) | Agentforce → "Authoring path (RC-22)" note | ITSM agents are legacy Bot/GenAi; AiAuthoringBundle not supported on this org |
| RC-24, RC-30 | approved (recommended set) | CMDB section note (PSs checked in 11a, not Pre-flight; fresh-org rule) + observed note | Old Pre-flight PS query was already removed in v14 |
| RC-26 | approved (recommended set) | Data Cloud observed note (verbatim) — now the manual 9b step per RC-91 | — |
| RC-6, RC-7, RC-13, RC-15, RC-19, RC-28, RC-51, RC-62 | approved (recommended set) | Already satisfied by the v14 restructure: Data Cloud last everywhere (RC-6); no collapsed tables remain (RC-7); Data Cloud PSs only in 9b after 9a (RC-13); Phase 12 `--wait 20` removed — settings script is async (RC-15); RC-19 check placed in the 9d note because Step 11 is kept verbatim; EinsteinAI read via the settings-script retrieve in 9c (RC-28); extra ServiceItsmIntelligenceUdd flags covered by 3e (RC-51); Phase 8 batching removed (RC-62) | — |

**Follow-on edits (direct consequence of RC-31/45, no new content):** Level 2 step 4 + target-table header scoped to fallback rows (per Echo v5 audit); Recipe Summary row `Step 0 | Browser` → `Step 0 | Programmatic (Level 1) + Browser fallback (Level 2)`; "Browser Only Steps" intro gets a one-line "Exception — Step 0" note.

**v14 follow-on edits (consequence of the restructure, no new content):** intro sentence; Feature Selection table and notes; Recipe Summary (rewritten table + "Old → new numbering" map); Guardrails #1/#3; Learnings #6 (UDD flags belong to features — RC-16 superseded), #7, #9, #13, #15, #16, #18, #19, #22; Step 0 moved after Phase 0 (content unchanged); "Browser Only Steps" heading removed; Execution Order rewritten; Deployment Helper "Phase 8" example → generic. Section names in rows above v14 refer to the structure at the time (see the numbering map in the recipe).

## Not applied — Appendix "Proposed changes (pending approval)" (2 items)

RC-4, RC-41 — both still proposed. The appendix intro now states that every listed item is still proposed (Echo's v14 note).

## Rejected / Superseded (not in appendix)

| RC-id | Reason |
|---|---|
| RC-8 | Rejected by user (Q2): no new PSGs in audit/assignments |
| RC-10, RC-29 | Superseded by RC-83 (portal 8a–8c) |
| RC-16 | Superseded by RC-70/RC-73 (each ServiceItsmIntelligenceUdd flag belongs to one feature) |
| RC-17 | Superseded by RC-59 (settings script redeploys the full retrieved file) |
| RC-18 | Superseded by RC-72 (both verifications in checks/check_agents.py) |
| RC-25 | Rejected by evidence: the Metadata API exposes exactly the 35 deployable IncidentMgmt flags |

## Evidence / org notes

- Step 0: `snapshot/step0-sharing-result.md` — deploy 0AfgL00000cAQjMSAW, 18/18 present objects at target, 6 absent skipped. Asset kept ReadWrite/Read on this org by user choice (Q6) — documented exception.
- IT Service Core, Release, Notification Service, Unified Catalog, Knowledge: `settings/*-result.md`, `docs/deploy-log.md`.
- Agentforce / SLA / Assignment Rules / Knowledge / Portal / Embedded chat / CMDB: status files in the phase folders; checks PASS as noted in each section's "Observed behavior".
- Data Cloud: turned on 2026-11-02, deploy 0AfgL00000cRYxOSAW Succeeded (`settings/CustomerDataPlatform-deploy-log.json`, `-result.md`). Background Automated Process install in progress at handoff time per Atlas (not independently verified by Sage).

## Bundle (13 files — all match Atlas's FINAL hashes; settings XML 94e19d30 since v15)

| File | SHA-256 |
|---|---|
| `recipe/checks/check_agents.py` | `472bb3cb38ad1c9526a364cf79900e0340a53b88e682cc912c4480a77dcd3dfe` |
| `recipe/checks/check_assignment_rules.py` | `456e3b1d0a02680b61a0bee59efe44f8165dca3e503ed394f759bbd8f59fbf73` |
| `recipe/checks/check_cmdb.py` | `dc1b08c5200ce74a76950cb416470e613c0628eb7171b9165dfc6a9659f611b5` |
| `recipe/checks/check_it_service_enablement.py` | `091fe523d8f584c397e662fb437853ceee70561724240f30ea0bed8d3075cab5` |
| `recipe/checks/check_knowledge.py` | `a37553c3485922620308a96a4aa91860ae11579e902ff5eaf16de53ed7d11966` |
| `recipe/checks/check_portal.py` | `d38a087cbdf2f5e62d10e330a0f03b51d01b510870678563b49ad80c0da1cfac` |
| `recipe/checks/check_sla.py` | `dd6542a2e1f923eb632d60e0dc7a070dd102d26262967041fa2bd826f584aaf2` |
| `recipe/checks/preflight.py` | `1c02845574e1992810ab28b7316890b65288107b23a2e5cd08a95b5d62e7f3c3` |
| `recipe/settings/aits-itsm-settings.xml` | `94e19d3073be942f27208a5bb0826fa06fe15cfa95e76d96933a1c114ad1cf82` |
| `recipe/settings/apply_permissions.py` | `3ce277d72801d81bb235e0b179e1f34b0999dfd77c9695c3587bfabe1be40b97` |
| `recipe/settings/apply_settings.py` | `d2a79ac6c0c55ade884c6f2eb80b81c3208891708bb87463513ddf1e6bbb5de6` |
| `recipe/sharing/aits-step0-sharing.xml` | `94768d750736644584ed1f5328a4bb85fac247c65a0ee13a0830b570a4dfefd7` |
| `recipe/sharing/apply_owd.py` | `50601b3c9eeb5faa9a8a4c93fdf021255bda2c2cfdc2048f87cd3c39e6bdb814` |

Checks at copy time: every file's hash = the source file = Atlas's stated prefix; all `.py` files parse; both XML files are well-formed; no `__pycache__`. Paths are relative to each script's folder, so the recipe's `checks/…`, `settings/…`, `sharing/…` paths work with this layout. Excluded: `_work/`, `preflight-out/`, retrieve/deploy outputs, before/after JSON, plan/result reports.

Spec gaps flagged in v14 are closed by RC-91 (platform + datacloud permission blocks; "Data Cloud User Enhanced Security" is a manual step).

## Publish plan (pending user approval — NOT executed)

Target: NEW reference "IT Service Cloud Setup Recipe v2" (version 1 reference untouched). Files: `recipe/aits-org-setup-recipe.updated.md` → `aits-org-setup-recipe.md`; `recipe/CHANGELOG.md`. The 13 bundle files are published on the public GitHub repository (folder `aits-org-setup-recipe/`, tag `v2.0`) at their relative paths. Excluded: `snapshot/`, `docs/` (org-specific evidence). Before publishing: re-run the checks (approved-only body, appendix vs recipe-changes.md, all 13 hashes vs source, no caches).

## Revisions

- v1 (2026-10-29): RC-1/2/3 applied, appendix RC-4 – RC-22. Echo audit: PASS.
- v2 (2026-10-30): appendix + RC-23 – RC-30.
- v3 – v3.2 (2026-10-30): Step 0 evidence final; appendix + RC-31 – RC-35; RC-31 conflict callout (scoped and corrected per Echo).
- v4 (2026-10-30): appendix + RC-36 – RC-41.
- v5 (2026-10-30): user-approved RC-31, RC-37, RC-44 and RC-45 applied to body, plus follow-on edits. RC-31 conflict callout removed (resolved). Appendix rebuilt: 39 items, incl. RC-42, RC-43, RC-46. Bundle hold lifted (copy last).
- v5.1 (2026-10-30): Echo audit of v5: PASS WITH 2 FIXES, both applied: Level 2 step 4/table header scoped to fallback rows; RC-37 note wording corrected (RC-46 stop rule not pre-applied).
- v6 (2026-10-30): user-approved RC-20 + RC-46 (stop-and-ask), RC-33 (Asset Controlled by Parent; RC-1 table updated, only the Asset row differs), RC-39 (Account children note) applied to body; RC-47 script-only. Appendix rebuilt: 35 items. Bundle on hold pending Asset revert.
- v6.1 (2026-10-30): Echo audit of v6: PASS. Applied: RC-47 verification note; de-duplicated "Account children" note. Asset org-exception note added (Q6: no revert). Bundle copied to `recipe/sharing/` after checks.
- v6.2 (2026-10-30): RC-35 approved → removed from appendix (34 items). Publish plan recorded (not executed).
- v7 (2026-10-30): RC-48 (Phase 0 IT Service Enablement gate) applied to body; RC-49 to appendix (35 items); check script bundled under `recipe/checks/`. Publish still on hold (more steps to come).
- v7.1 (2026-10-30): Echo audit of v7: PASS. Added Phase 0 to the Recipe Summary "Programmatic Phases" sentence (RC-48 scope). Non-blocking risks raised by Echo with Atlas: Phase 3 flag list lacks itServiceEnablement (see RC-49/RC-25); the RC-5 "Phase 0" title clashes with the new Phase 0.
- v8 (2026-10-30): RC-52/53/54 (Phase 3/5/6 via settings XML process; Slack not managed; static flag list reference-only) applied to body. RC-25 rejected (removed from appendix). Appendix rebuilt: 36 items incl. RC-50/51; RC-12 now verified. Settings bundle added. Publish on hold.
- v8.1 (2026-10-30): Echo audit of v8: FAIL (stale bundle). Re-copied settings/* (fixed 13:13:54 / 13:14:03 versions), hashes updated. Body/bundle `--confirm` mismatch recorded, pending RCs.
- v9 (2026-10-30): RC-55 applied to Phase 3 (`--confirm`, one approval per run, scaled deploy cap). Final settings files re-copied (hashes match Atlas's). Appendix re-synced: 39 items incl. RC-56/57/58, RC-5 renamed. __pycache__ removed from bundle.
- v9 audit (Echo): PASS.
- v10 (2026-10-30): RC-56/57 (Phase 3 notes), RC-58 (Learning #23), RC-59 (Learning #1 + Error Handling → settings script) applied to body. RC-17 superseded by RC-59. Appendix: 35 items. Bundle unchanged (hashes re-checked against source: 95ce123f / 01b83e15).
- v10 audit (Echo): PASS.
- v11 (2026-10-30): RC-60 applied to Phase 7 (settings script; direct-deploy + SOAP text removed). XML re-copied (ReleaseMgmt section). Appendix re-synced (RC-51 partly resolved, stays). Not changed (outside RC-60): Phase 7 "Optional features" still lists enableReleaseValidations (now set by the script); the "Batch with Phase 8" callout (see RC-16).
- v11 audit (Echo): PASS.
- v12 (2026-10-30): RC-65/66/67 applied (feature-driven IT Service Core 1a–1d; ownership table; org note) + follow-on renumbering. Appendix re-synced (39 items). Settings XML re-copied (d76523f4). apply_settings.py copied at f02be460, NOT the 345a227d Atlas named final: the source changed at 13:48:18, so this needs confirmation.
- v12.1 (2026-10-30): Atlas confirmed apply_settings.py f02be460 is NOT final (prerequisite-order defect). Publish blocked until a fixed hash arrives. XML d76523f4 confirmed final. Phase 1 vs 1a–1d naming question sent to the user by Atlas.
- v12 audit (Echo): body PASS; bundle FAIL (apply_settings.py f02be460: Change can end ON while Incident is OFF when the Incident core flag fails). Other 4 bundle files match. Naming note (Phase 1 vs 1a–1d) waits for the user's decision via Atlas.
- v13 (2026-10-30): RC-68 (per-feature failure isolation; cap +1 per feature) and RC-69 ("Phase 1" → "Pre-flight audit") applied. apply_settings.py re-copied at final 28753a3a (pending Echo re-audit). Appendix re-synced (39 items).
- v14 (2026-11-02): catch-up rebuild from Atlas's consolidated handoff. Applied RC-5 (via RC-88), RC-9, RC-68 addendum, RC-70–RC-89 (22 RCs, verbatim) and restructured the body into Pre-flight · 0 · Step 0 · 1a–1e · 3a–3e · 4a–4c · 5a–5c · 6a–6c · 7a–7b · 8a–8c · 9a–9d (last) · 10a–10c · 11a–11c. RC-8 rejected; RC-10/16/18/29 superseded. Appendix rebuilt: 33 items. Bundle: 2 stale files refreshed + 8 added (13 total, all hash-verified). Draft v13 backed up in Sage's folder.
- v14 audit (Echo): PASS (structure, approved content, bundle); notes on appendix intro wording, stale SOAP/optional-features text (RC-61–64, then proposed) and RC-90.
- v14.1 (2026-11-02): RC-91 applied (prompt template PSs 3a and Data Cloud PSs 9b via the permissions script); settings XML 3098c812; RC-26 evidence noted.
- v15 (2026-11-02): user decisions applied — the 29-RC recommended set (RC-6 7 11 12 13 14 15 19 21 22 23 24 26 27 28 30 32 34 36 38 40 42 43 50 51 61 62 63 64), RC-49 (UNTESTED), RC-90 (note), RC-89 update (9c later run, 9d follow-up run), RC-91 update (Data Cloud User Enhanced Security = manual). Original Steps 11/12 restored verbatim under 9d. Settings XML 94e19d30. Appendix: RC-4, RC-41 only. v14.1 backed up in Sage's folder.
- v15 audit (Echo): FINAL PASS (740eab10).
- v15.1 (2026-11-02): single hunk — Phase 1c "Optional features" → "Optional flags (enabled unless --required-only): …" (wording per Atlas; follows the approved RC-65 feature model; flags confirmed tier="optional" in settings/aits-itsm-settings.xml). Nothing else changed.
- v15.2 = Recipe version 2.0 (2026-11-02): version header added under the recipe title; CHANGELOG "Version 2.0" section with version 1 listed as the archived original (`recipe/archive/`, created by Atlas) and the versioning rule. Nothing else changed.
- 2.0: bundle location added — one line under the version header: GitHub `Ajeeshs2/IT-Service-Cloud`, folder `aits-org-setup-recipe/`, tag `v2.0` (version 1 = tag `v1.0`); the saved reference cannot hold the `.py` scripts. Nothing else changed.
- 2.0: published as a new recipe; bundle on public GitHub — header lines replaced (successor to "IT Service Cloud Setup Recipe" v1, which remains unchanged; clone command for tag `v2.0`); version table, rollback and publish-plan wording updated; archive folder removed by Atlas.
