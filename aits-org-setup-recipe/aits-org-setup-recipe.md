# AITS Org Setup Recipe

**Recipe version 2.0 — 2026-11-02** — successor to the "IT Service Cloud Setup Recipe" (version 1), which remains available unchanged.

**Bundle (scripts and specs):** public GitHub repository `https://github.com/Ajeeshs2/IT-Service-Cloud`, folder `aits-org-setup-recipe/`, tag `v2.0`. Before running, get the bundle: `git clone --branch v2.0 https://github.com/Ajeeshs2/IT-Service-Cloud.git && cd IT-Service-Cloud/aits-org-setup-recipe` — all commands in this recipe run from that folder (keep the checks/, settings/, sharing/ layout). Version 1 is also tag `v1.0`.

Automated setup of an AITS (Agentforce IT Services) org when a Salesforce org is connected via MeshMesh. Covers a read-only pre-flight audit, then feature-driven phases run only when selected: 0 IT Service Enablement (gate), Step 0 Sharing, 1a–1e IT Service Core, 3a–3e Agentforce, 4a–4c Unified Catalog, 5a–5c SLA Management, 6a–6c Assignment Rules, 7a–7b Knowledge, 8a–8c Self-service portal, 9a–9d Data Cloud (always last), 10a–10c Embedded chat, 11a–11c CMDB & Service Graph. Settings, sharing and permission changes run through the bundled scripts (`settings/`, `sharing/`); read-only checks live in `checks/`.

---

## Prerequisites

* Salesforce org connected via MeshMesh (salesforce-core connection)
* Org must have ITSM / IT Service Management licenses provisioned
* System Administrator access on the connected org
* API version: 67.0

---

## Guardrails — Ask Before Running

> **These questions MUST be asked at the start of every run, before any execution begins.**

### 1. Data Cloud Enablement

**Ask the user:** "Do you want to enable Data Cloud? If yes, we'll deploy it as the LAST programmatic phase so its background provisioning doesn't interfere with other deploys."

* If **yes**: Run Data Cloud (Phases 9a–9d) **last** — after all other programmatic phases are complete. The Data Cloud settings deploy triggers a background `InstalledPackage` deploy by "Automated Process" that installs the `ssot` (Salesforce Standard Data Model) package. This takes \~10–30 minutes and **cannot be cancelled or re-triggered from the UI without the run failing and then retriggering provision**. By deploying Data Cloud last, there is no risk of it being accidentally cancelled when clearing a stuck deploy queue. Phase 9d (Data Library) depends on Data Cloud being fully provisioned.
* If **no**: Skip Phases 9a–9d entirely (9d Data Library requires Data Cloud).

### 2. Feature Selection

**Ask the user:** "Which features do you want to enable?" Present the following as a checklist — if the user opts out of any, skip the corresponding phases/steps:

| Feature | Phases |
|---|---|
| Incident Management | 1a |
| Problem Management (needs Incident) | 1b |
| Change Management (needs Incident) | 1c |
| Release Management (needs Change) | 1d |
| Agentforce Platform | 3a |
| IT Service Fulfiller agent (needs 3a + Incident) | 3b |
| IT Employee Assistant incl. Enhanced Chat (needs 3a) | 3c |
| Proactive Assistant (needs 3b) | 3d |
| Optional AI features — *optional*, only if named | 3e |
| Unified Catalog | 4a–4c |
| SLA Management (5c optional) | 5a–5c |
| Assignment Rules | 6a–6c |
| Knowledge | 7a–7b |
| Self-service portal | 8a–8c |
| Data Cloud incl. Data Library — always last (9c optional) | 9a–9d |
| Embedded chat on the portal (10c manual) | 10a–10c |
| CMDB & Service Graph | 11a–11c |

> **All phases are feature-driven:** only the selected features run; unselected features are never changed. For each run, also ask *all features* vs *required only*. Start every run with the Pre-flight audit — its skip map shows each phase's current state. `--features all` excludes optional phases (3e, 9c).

> **Mandatory, always run:** Phase 0 (IT Service Enablement gate) and Phase 1e (Notification Service).


### 3. Permission Assignment Scope

**Inform the user:** "All permission sets and licenses will only be assigned to the currently connected user. Other users will need to be assigned separately after setup."

This applies to:

* All Permission Sets, Permission Set Groups and licences of the selected phases (1a–1d, 3a, 4c, 6b, 9b)
* The custom "Access Agents" Permission Set (3b/3c)
* Queue membership (3c)

No additional PSGs (e.g. ItsmPortalUserPSG, EmployeeHub*, SetupWithAgentforceUserPsg) are audited or assigned (RC-77).

### 4. Strict Scope — Only Do What the Recipe Says

> **This rule applies to EVERY phase and step. No exceptions.**

* **ONLY perform actions explicitly described in a step's "Interaction flow" or "Deploy" section.** If the recipe does not instruct you to click a toggle, button, or link — do not click it.
* **DO NOT enable, toggle, or click anything** just because it appears unchecked, incomplete, or available on a page. Many Salesforce setup pages show multiple features, toggles, and sections. Ignore everything not called out in the recipe.
* **"All features" in the user's feature selection** refers ONLY to the features listed in the recipe's Feature Selection checklist (Section 2 above). It does NOT mean "enable every toggle visible in the Salesforce UI."
* **If you encounter an unchecked toggle or button** that is NOT in the recipe's instructions for the current step, leave it alone. Do not infer that it is a prerequisite or dependency unless the recipe explicitly says so.
* **If you are unsure** whether something should be enabled, STOP and ask the user before proceeding.

### 5. Availability-Driven Run — Missing Objects Are Never Failures

> **This rule applies to EVERY phase and step.**

Every step checks what exists in the connected org and drives the run from that. Objects/features that are not present are skipped and reported as *not in org* — never as a failure. The run report lists present / at target / changed / skipped / fallback.

---

## Recipe Summary

**How a run works:** Pre-flight audit (read-only skip map) → user selects phases → for each selected phase: check → plan → user approval → apply → verify. Settings, sharing and permission changes are programmatic (Level 1) through the bundled scripts; browser actions (Level 2) are used only where no API exists or a check fails, always with user approval. **Data Cloud (9a) is the LAST programmatic deploy** — it triggers a background package install that occupies the deploy queue for \~10–30 min and must never be cancelled. (Slack and Microsoft Teams integrations are not covered.)

| Phase | Method | Description |
|---|---|---|
| Pre-flight audit | Read-only script | `checks/preflight.py` — skip map for every phase; runs first, every run |
| 0 | Check script (+ Browser if OFF) | IT Service Enablement gate — must be ON before any other phase |
| Step 0 | Programmatic (Level 1) + Browser fallback (Level 2) | Sharing Settings (OWD) |
| 1a–1e | Settings + permissions scripts | IT Service Core: Incident, Problem, Change, Release, Notification Service (1e mandatory) |
| 3a–3e | Settings script + agent checks; Browser for the Fulfiller wizard / Enhanced Chat | Agentforce (3e optional) |
| 4a–4c | Settings + permissions scripts | Unified Catalog |
| 5a–5c | Check script + Browser | SLA Management (5c optional) |
| 6a–6c | Settings + permissions scripts + check; Browser fallback | Assignment Rules |
| 7a–7b | Settings script + check | Knowledge |
| 8a–8c | Check script + page; create a site only if the user chooses | Self-service portal |
| 9a–9d | Settings script (LAST) + Browser (9d) | Data Cloud, Data Library (9c optional) |
| 10a–10c | Checks + manual (10c) | Embedded chat on the portal |
| 11a–11c | Check script + Browser | CMDB & Service Graph |

**Old → new numbering:** Phase 1 → Pre-flight audit · Phase 2 → 9a–9b · Phases 3/5/6/7 → 1a/1b/1c/1d · Phase 4 → 7a · Phase 8 → 4a–4c · Phase 9 → 6a–6b · Phase 12 → 3a (PII masking → 9c) · Step 1 → 6c · Step 2 → 3c · Steps 3/3b → 11b/11c · Steps 3c, 6, 13 → `checks/check_agents.py` (3a–3c) · Step 7 → 3b · Steps 8/9 → 3b/3c fixes · Step 10 → 8a–8c · Steps 11/12 → 9d · Step 14 → 10a–10c · Step 15 → 5a–5c.

---

## Operational Learnings (from live runs)

> These notes capture critical lessons from real executions. Read before running.

 1. **IncidentMgmtSettings is shared by Phases 1a, 1b and 1c.** Never hand-build its XML. Use `settings/apply_settings.py` — it retrieves the org's current settings file (Metadata API), changes only spec-listed flags and redeploys the full file, so unlisted flags are preserved. Do not build deploy XML from the Tooling API read (it returns extra, non-deployable fields).
 2. **ReleaseMgmtSettings — read via Metadata API retrieve** — ReleaseMgmtSettings is not in the Tooling API; read it with a Metadata API retrieve — the settings script does this (RC-12 verified). No SOAP or token handling needed.
 3. **Deploy queue contention** — consecutive deploys can get stuck in `Pending` for 2+ minutes. Always use `--async` + poll with `deploy report`. If stuck >2 min, cancel and resubmit **only your own deploy** — check `DeployRequest.CreatedBy` first and never cancel a deploy created by Automated Process (RC-14). Batch multiple settings into a single deploy where possible.
 4. **Batch permission assignments** — assigning PS/PSGs one-by-one across phases is slow. Collect all assignments and run them in a single batch at the end.
 5. **User license incompatibilities are expected** — `UnifiedCatalogCommunityUserPsl` may fail for System Administrator users depending on licensing — treat failure as informational (RC-27).
 6. **ServiceItsmIntelligenceUdd flags belong to features** — each flag is owned by exactly one phase (3b/3c/3d/3e, 4b). The settings script combines all selected features that share a settings file into one deploy.
 7. **Deploy `enableEinsteinGPTDeployPromptTemplatesAsActive`** with Phase 3a (Agentforce Platform), not Phase 7a (Knowledge) — it's needed for agent prompt templates.
 8. **API version 67.0 required for ServiceItsmIntelligenceUdd** — Deploying with API v63.0 fails with "Not available for deploy for this API version". All AITS settings packages should use `<version>67.0</version>` in package.xml.
 9. **⚠️ NEVER cancel "Automated Process" deploys** — When Data Cloud is enabled, Salesforce triggers a background deploy by "Automated Process" to install the `ssot` (Salesforce Standard Data Model) `InstalledPackage`. This deploy takes \~10–30 minutes and **there is no UI or API to re-trigger it if cancelled**. Cancelling it will leave Data Cloud permanently stuck at "In Progress" on the Salesforce Foundations page. If you see an "Automated Process" deploy in the queue, **wait for it to finish** — do NOT cancel it even if it appears to block your deploys. If you have non-Automated-Process deploys stuck in `Pending`, wait for the Automated Process deploy to complete first. To avoid this conflict entirely, **deploy Data Cloud (Phase 9a) as the LAST programmatic phase** so the background install runs after all other deploys are done.
10. **Connection alias may change between sessions** — The Salesforce org connection alias can change between sessions (e.g. `org-o2wdej` → `org-rrvydk`). Always read the active connection alias from the current task context rather than hardcoding it from a previous session.
11. **Data Cloud provisioning is NOT visible on Deploy Status page** — The `CustomerDataPlatform.settings` deploy succeeds quickly, but actual Data Cloud provisioning is a background process (\~20-30 min) that does NOT appear as a metadata deploy on the Deploy Status page. Do not look for it there — it runs separately. Steps that depend on Data Cloud (e.g., Data Library) will show "Turn On Data Cloud" until provisioning completes.
12. **Deploy tracking log is essential** — Maintain a running log of every deploy with: Deploy ID, Phase/Step, Settings included, and Status. This enables quick recovery when deploys get stuck or are canceled — you know exactly what needs to be rerun. Format: `| Deploy ID | Phase | Settings | Status | Notes |`
13. **FlowDefinitionView doesn't find auto-provisioned routing flows** — The `RouteMsgsItEmpAgent` flow (auto-created by Enhanced Chat setup) exists in the Tooling API `Flow` object but does NOT appear in `FlowDefinitionView`. `checks/check_agents.py` (3c) checks this automatically; for manual verification use the direct Tooling API REST endpoint: `GET /services/data/v67.0/tooling/query?q=SELECT+Id,Definition.DeveloperName,MasterLabel,Status+FROM+Flow+WHERE+Definition.DeveloperName='RouteMsgsItEmpAgent'`
14. **Strict scope — only do what the recipe says** — Browser steps often show pages with multiple toggles, buttons, and features. ONLY interact with the specific UI elements described in each step's Interaction Flow. Do not enable, click, or toggle anything else, even if it appears unchecked or incomplete. If the recipe doesn't say to click it, don't click it. "All features" in the user's feature selection refers to the recipe's feature checklist, not every toggle visible in the Salesforce UI. When in doubt, ask the user.
15. **PSG auto-assignment eliminates redundant PS and PSL assignments** — When a Permission Set Group (PSG) is assigned to a user, Salesforce automatically assigns all contained Permission Sets AND their required Permission Set Licenses. This means you do NOT need to separately assign individual PSs or PSLs that are bundled inside a PSG. Only 6 standalone PSs (not in any PSG) require explicit assignment: `GenieAdmin`, `GenieUserEnhancedSecurity`, `BRERuntime`, `BREDesigner`, `EinsteinGPTPromptTemplateUser`, `EinsteinGPTPromptTemplateManager`. The `ContextServiceRuntimePsl` and `ContextServiceAdminPsl` PSs are bundled inside the Unified Catalog PSGs (`UnifiedCatalogAdminPsl`, `UnifiedCatalogAgentPsl`) and do NOT need separate assignment — assigning the PSGs in Phase 4c covers them automatically.
16. **Knowledge settings (7a) run through the settings script** — `Knowledge.settings` has a nested `suggestedArticles` structure (`Case`/`WorkOrder` sub-elements) that caused deploy failures when the XML was hand-built. Retrieve-patch-deploy keeps that block exactly as retrieved, which removes the XML-structure failure risk (RC-81).
17. **Use `sf api request rest` for Connect API calls, not `curl`** — The `sf org display` command returns redacted access tokens (masked with `****`), and `sf org auth show-access-token` may include ANSI escape characters. Both break `curl`-based API calls. Instead, use `sf api request rest` which handles authentication automatically: `sf api request rest '/services/data/v67.0/connect/communities' --method get --target-org <ORG>`. This eliminates all token-handling issues and works reliably for Connect API endpoints (templates, site creation, etc.).
18. **SLA predefined policies may pre-exist** — Before clicking "Create Predefined Policies" (phase 5b; `checks/check_sla.py` does this check), query whether SLA policies already exist: `SELECT Id, Name, SobjectType FROM SlaProcess WHERE SobjectType IN ('Incident','Problem','ChangeRequest')`. If policies exist, the "Create" action may fail or create duplicates. Show existing policies to the user and ask whether to proceed.
19. **Discover the agents — never hard-code names** — the Employee agent = the agent the Enhanced Chat routing flow targets (discover; never hard-code). Other agents such as IT_Service_Employee may or may not exist on an org — ignore them (availability-driven, RC-44). Fulfiller name also discovered from the org.
20. **Copilot activation limitation** — The `sf agent activate` command only works when run from a valid SFDX project directory (requires `sfdx-project.json`). If you get `InvalidProjectWorkspaceError`, create a minimal `sfdx-project.json` with `{"packageDirectories":[{"path":"force-app","default":true}],"sourceApiVersion":"67.0"}` before running agent activation commands.
21. **Enhanced Chat toggle — click the container, not the switch** — The "Set Up Enhanced Chat for IT Service Employee" toggle element has shadow DOM click interception. Direct clicks on the toggle switch (`<input type="checkbox">`) are absorbed. To reliably toggle it, click the **parent container element** (typically the `<div>` wrapper 1-2 refs above the switch in the accessibility snapshot). This applies to several Salesforce Go toggle elements that use Lightning `lightning-primitive-input-toggle` components.
22. **⚠️ Data Cloud MUST be the last programmatic deploy** — The Data Cloud settings deploy (`CustomerDataPlatform.settings`) triggers a background `InstalledPackage` deploy by "Automated Process" that installs the `ssot` package (\~10–30 min). This background deploy occupies the deploy queue. If other deploys are submitted while it runs, they queue behind it — and if an operator cancels the Automated Process deploy to unblock the queue, Data Cloud provisioning is permanently broken (no re-trigger mechanism exists). **Execution order:** Run all other phases first → then deploy Data Cloud (9a) last → wait for background provisioning to complete → then proceed with Phase 9d (Data Library).
23. **After any interruption or rejected action, check what already ran** — Long-running, multi-deploy actions are separate, resumable steps. After ANY interruption or rejected action, query `DeployRequest` (Tooling, last 15 min) before continuing — deploys may already have run.
24. **Sandbox tooling** — jq is not installed in the execution sandbox — parse `--json` output with python3. Pass the org alias literally in every command (shell variables for the org are blocked).

---

## Pre-flight audit (read-only) — runs first, every run

**Pre-flight audit** — `python3 checks/preflight.py <ORG> [--portal-site <name>]` (read-only, ~2–3 min). Prints a **skip map** — every phase with its state on the connected org and the suggested action — plus org/user and the deploy queue (in-flight deploys listed; never cancel Automated Process). It re-uses the phase checks: Phase 0 gate, settings `status --json` for all features (optional/mandatory tagged), permissions verify for all permission phases, sharing (EntityDefinition vs spec; Controlled-by-Parent rows named for confirmation via apply_owd plan), agents/Enhanced Chat, SLA, Assignment Rules, Knowledge readiness, CMDB, portal, embedded chat (manual 10c), Data Cloud. Writes only `checks/preflight-out/preflight-<ts>.md/.json`; never overwrites phase evidence. The user then selects which phases to run.

apply_settings retrieves all settings files in ONE request; during a pre-flight, read-only `status` calls share one cached copy (`AITS_SETTINGS_CACHE`, honoured in status mode only — plan/deploy always retrieve fresh).

Hardening: apply_permissions drops AITS_SETTINGS_CACHE for its prerequisite status call; pre-flight removes its temp cache at exit

**What the sharing part checks (manual equivalent, reference):**

Query OWD sharing models for every object in the Step 0 target table and compare Internal and External access against it:

```
SELECT QualifiedApiName, InternalSharingModel, ExternalSharingModel
FROM EntityDefinition
WHERE QualifiedApiName IN (
  'Account','Contract','Asset','ProductCatalog','FulfillmentOrder',
  'InventoryReservation','Location','Product2',
  'ProductAttributeDefinition','ProductCategoryDisqual','ProductCategoryQualification',
  'ProductClassification','ProductClassificationAttr','ProductComponentGroup',
  'ProductComponentGrpOverride','ProductConfigurationFlow','ProductConfigFlowParameter',
  'ProductItem','ProductRelComponentOverride','ProductTransfer',
  'SvcCatalogRequest','ServiceRequest','Shipment')
ORDER BY QualifiedApiName
```

Flag every object whose Internal or External value differs from the Step 0 target table (`ReadWrite` = Public Read/Write, `Read` = Public Read Only, `Private` = Private, `ControlledByParent` = Controlled by Parent) for update in Step 0. Objects missing from the result do not exist in the org — record them as skipped (*not in org*), never as a failure (Guardrail #5).

Asset is usually Controlled by Parent; EntityDefinition reports the inherited Account values — verify with the retrieved object-meta.xml (the script does this automatically).

---

## Phase 0: IT Service Enablement (gate)

**Phase 0 — IT Service Enablement (gate).** Must be ON before any other phase or step.

**Check (programmatic):** `python3 checks/check_it_service_enablement.py <ORG>` — reads Tooling `SELECT Metadata FROM IncidentMgmtSettings LIMIT 1` → `itServiceEnablement`. Exit 0 = ON → proceed; exit 3 = OFF → turn on first; exit 1 = check failed → read the page.

**Page:** `/lightning/setup/page/feature/service-cloud-itsm-setup/home?topic=SalesforceGo` — breadcrumb "Salesforce Go > IT Service Enablement"; section **"Turn on IT Service Enablement"** shows **On** when enabled; required sub-step "Manage User Access" (assign IT Service permission sets).

The page header badge can say **"In Progress"** even when enabled — it reflects the optional "Unlock Advanced Functionality → Finish in Setup" item. Not a failure; do not click it (strict scope).

**If OFF (RC-49, UNTESTED):** If Phase 0 reports OFF: Level 1 is not available (itServiceEnablement is not in the deployable IncidentMgmt settings file) → Level 2 browser: Salesforce Go 'IT Service Enablement' page → Turn on → Confirm, then re-run checks/check_it_service_enablement.py. UNTESTED: confirm on the first org where it is OFF; every later IncidentMgmt deploy preserves the value because the script redeploys the retrieved file.

---

## Step 0: Configure Sharing Settings (Organization-Wide Defaults)

**Purpose:** Set the Organization-Wide Default (OWD) sharing settings for AITS-related objects so that records are accessible across the organization as needed.

**Execution model — two levels:** Level 1 (programmatic) is the default. Level 2 (browser) is used **only** for the rows listed in the generated `sharing/browser-fallback.md`. Both levels use the same target table below.

### Level 1 — Programmatic (default)

Targets are defined in `sharing/aits-step0-sharing.xml` (bundled with this recipe) and applied by `sharing/apply_owd.py`. The script retrieves each target object's `CustomObject` metadata fresh, patches **only** `sharingModel`/`externalSharingModel`, and deploys the object-meta.xml files only (no fields or list views).

1. `python3 sharing/apply_owd.py <org-alias> plan` — snapshot + fresh retrieve + patch + report. **No org change.**
2. List all reductions from `plan` output to the user and get approval before `deploy --confirm`.
3. `python3 sharing/apply_owd.py <org-alias> deploy --confirm` — async deploy. Failed objects are isolated (atomic deploy → failed ones removed, rest redeployed). Rows still mismatched after the ~2 min sharing-recalculation wait are added to `sharing/browser-fallback.md`.
4. `python3 sharing/apply_owd.py <org-alias> verify`

Exit codes: `0` = all present objects at target; `2` = Level 2 fallback needed (see `sharing/browser-fallback.md`); `1` = abort.

Invalid specs (External more permissive than Internal) abort the run. Systemic deploy failures (auth, timeout, no component errors) abort and are retried after fixing — they do not go to browser fallback.

Absent objects are skipped and reported as *not in org* — never as a failure (Guardrail #5).

Reductions (e.g. RW→Read) may not show in EntityDefinition until sharing recalculation completes (~2 min observed). Re-verify after 2 min before reporting mismatches. (RC-32)

Contract has no own `externalSharingModel`; it follows Account — deploy Account only (RC-34).

### Level 2 — Browser fallback (only rows in `sharing/browser-fallback.md`)

Follow this flow **only** for the rows listed in `sharing/browser-fallback.md`, then run `python3 sharing/apply_owd.py <org-alias> verify`.

**URL:** `/lightning/setup/SecuritySharing/home`

**Page verification:** The page title should show **"Sharing Settings"** with a heading **"Organization-Wide Sharing Defaults"** and an **"Edit"** button next to it.

**Interaction flow:**

**Scope: ONLY perform the actions listed below. Do not interact with any other toggles, buttons, or sections on this page.**

1. Navigate to the URL above
2. Click the **"Edit"** button next to "Organization-Wide Sharing Defaults"
3. The page loads an edit form with two columns per object:
   * **Default Internal Access** (first dropdown, labeled `"ObjectName : Default Access"`)
   * **Default External Access** (second dropdown, unlabeled — immediately to the right)
4. For each row listed in `sharing/browser-fallback.md`, set **both** Internal and External as shown in the target table below
5. **Note:** External access cannot be more permissive than Internal access — set Internal first, then External

**Target Organization-Wide Defaults (reference values — Level 1 applies all present rows, Level 2 only the fallback rows):**

| Object (UI Label) | Default Internal Access | Default External Access | Notes |
|---|---|---|---|
| Account and Contract | Public Read/Write | Public Read Only | Single row on the page (covers both Account and Contract) |
| Product | Public Read/Write | Public Read Only | |
| Catalog | Public Read/Write | Public Read Only | |
| Fulfillment Order | Public Read/Write | Private | Skip if absent |
| Inventory Reservation | Controlled by Parent | Private | Skip if absent |
| Location | Public Read/Write | Public Read/Write | |
| Product Attribute Definition | Public Read/Write | Public Read Only | |
| Product Category Disqualification | Public Read/Write | Public Read Only | |
| Product Category Qualification | Public Read/Write | Public Read Only | |
| Product Classification | Public Read Only | Public Read Only | |
| Product Classification Attribute | Public Read Only | Public Read Only | |
| Product Component Group | Public Read/Write | Public Read Only | |
| Product Component Group Override | Public Read/Write | Public Read Only | |
| Product Configuration Flow | Public Read/Write | Public Read Only | |
| Product Configuration Flow Parameter | Public Read/Write | Public Read/Write | |
| Product Item | Public Read/Write | Public Read Only | Skip if absent |
| Product Item Additional Transaction | Public Read/Write | Public Read Only | Skip if absent |
| Product Related Component Override | Public Read/Write | Public Read Only | |
| Product Transfer | Public Read Only | Public Read Only | Skip if absent |
| Service Catalog Request | Public Read/Write | Public Read Only | |
| Service Request | Public Read/Write | Public Read/Write | |
| Shipment | Public Read/Write | Public Read/Write | Skip if absent |
| Asset | Controlled by Parent | Controlled by Parent | Follows Account (user decision 2026-10-30, RC-33) |

> ⚠️ Product Classification and Product Classification Attribute targets are Public Read Only internally. On orgs where they are currently Public Read/Write this *reduces* internal access — confirm with the user before saving. (RC-21)

**Inventory Reservation:** Untested — the object was absent on the reference org. If the deploy rejects this combination, the row goes to the Level 2 browser fallback list.

**Account children:** Changing Account also changes its Controlled-by-Parent children (Contact, Order, Asset). E.g. Account External Private→Public Read Only widens Contact and Order external access. `plan` and `verify` report these inherited objects before/after; no extra confirmation is needed (RC-39).

**Objects that may be absent (skip if not in the list):**

| Object (UI Label) | Notes |
|---|---|
| Fulfillment Order, Inventory Reservation, Product Item, Product Item Additional Transaction, Product Transfer, Shipment | Require Field Service / Order Management. Not present on orgs without those features — skip and report them as *not in org* (never a failure, Guardrail #5). |
| Product Configuration Section | May not exist — skip if not in the dropdown list |

6. After setting all dropdowns, scroll to the top or bottom and click **"Save"**
7. If the save fails with validation errors on objects NOT in the target table, STOP and show the errors to the user. Only change those rows after explicit user approval (Guardrail #4 — strict scope). Log which rows were changed.
8. If Save is rejected for a row listed in `sharing/browser-fallback.md`, STOP and ask the user — do not change values.

**Known pre-existing validation issues (may vary by org):** When saving, the page may flag errors on objects unrelated to AITS (e.g., Compliance Control Version, Compliance Policy Version, Regulation Version, Validation Procedure Version) that have `Controlled by Parent` internally but `Private` externally. Do **not** fix these automatically — STOP, show the errors to the user, and change them only with explicit approval (step 7).

**Expected result after save:**

* Page returns to read-only Sharing Settings view
* All target objects show the correct Internal and External access levels
* A background sharing recalculation begins (may take time depending on org data volume)
* Use the "Background Jobs" link on the page to monitor recalculation progress

**Verification query (post-save):**

```
SELECT QualifiedApiName, InternalSharingModel, ExternalSharingModel
FROM EntityDefinition
WHERE QualifiedApiName IN (
  'Account','Contract','Asset','ProductCatalog','FulfillmentOrder',
  'InventoryReservation','Location','Product2',
  'ProductAttributeDefinition','ProductCategoryDisqual','ProductCategoryQualification',
  'ProductClassification','ProductClassificationAttr','ProductComponentGroup',
  'ProductComponentGrpOverride','ProductConfigurationFlow','ProductConfigFlowParameter',
  'ProductItem','ProductRelComponentOverride','ProductTransfer',
  'SvcCatalogRequest','ServiceRequest','Shipment'
)
ORDER BY QualifiedApiName
```

Compare each row to the target table above using these API values: Public Read/Write = `ReadWrite`, Public Read Only = `Read`, Private = `Private`, Controlled by Parent = `ControlledByParent`. A missing row means the object does not exist in the org (expected for the "skip if absent" objects). Product Item Additional Transaction is not in the query — verify it visually on the Sharing Settings page.

Rows whose target is Controlled by Parent (Asset; Inventory Reservation internal) show the parent's values in EntityDefinition. Verify them from the retrieved object-meta.xml; `apply_owd.py verify` does this automatically (RC-47).

**UI-to-API name mapping:**

| UI Label | API Name |
|---|---|
| Account and Contract | Account, Contract |
| Asset | Asset |
| Catalog | ProductCatalog |
| Fulfillment Order | FulfillmentOrder (unverified — absent in reference org) |
| Inventory Reservation | InventoryReservation (unverified — absent in reference org) |
| Location | Location |
| Product | Product2 |
| Product Attribute Definition | ProductAttributeDefinition |
| Product Category Disqualification | ProductCategoryDisqual |
| Product Category Qualification | ProductCategoryQualification |
| Product Classification | ProductClassification |
| Product Classification Attribute | ProductClassificationAttr |
| Product Component Group | ProductComponentGroup |
| Product Component Group Override | ProductComponentGrpOverride |
| Product Configuration Flow | ProductConfigurationFlow |
| Product Configuration Flow Parameter | ProductConfigFlowParameter |
| Product Item | ProductItem (unverified — absent in reference org) |
| Product Item Additional Transaction | n/a — verify in org |
| Product Related Component Override | ProductRelComponentOverride |
| Product Transfer | ProductTransfer (unverified — absent in reference org) |
| Service Catalog Request | SvcCatalogRequest |
| Service Request | ServiceRequest |
| Shipment | Shipment (unverified — absent in reference org) |

**Note:** "Catalog" on the Sharing Settings page is `ProductCatalog`. `SvcCatalogItemDef` is a different object (Service Catalog Item Definition) and is not part of this step.

**Observed behavior on this org (it-service-cloud-bha853):** Asset was decoupled from Account during the 2026-10-30 run and is kept at Public Read/Write / Public Read Only by user choice (no revert). This org is a documented exception to the recipe default (Controlled by Parent / Controlled by Parent, RC-33), so `verify` here reports Asset as an **expected mismatch**.

---

## IT Service Core (Phases 1a–1e — feature-driven)

**IT Service Core** features are shown to the user as phases and run only if selected: **1a Incident Management**, **1b Problem Management** (needs Incident), **1c Change Management** (needs Incident), **1d Release Management** (needs Change). Phase 0 (IT Service Enablement) is always first. Show the current state with `settings/apply_settings.py <ORG> status`, ask the user which phases to deploy (and *all features* vs *required only* per run), then `plan --features <ids>` → user approval → `deploy --features <ids> --confirm` → `verify`. Unselected features are never changed. Selected features in the same Salesforce settings file (Incident/Problem/Change share IncidentMgmt) are combined into one deploy automatically. A selected feature whose prerequisite is neither selected nor already ON aborts the run with a message; Release is re-checked against the org after the IncidentMgmt deploy.

The first deploy is a single try with all selected flags (normal case = 1 deploy per file). On failure, flags are isolated per feature in dependency order (Incident → Problem/Change → Release), splitting only inside a feature; a feature whose prerequisite core flag is not ON is marked "not applied — prerequisite X is not ON" and never deployed; the optional retry skips those flags. Cap = 3·ceil(log2 n)+1 plus 1 per feature in the file.

Phase **1e Notification Service** is mandatory and joins every run (RC-85).

1. `python3 settings/apply_settings.py <org-alias> status` — phases + current state (read-only)
2. Ask the user which phases to deploy (`incident`, `problem`, `change`, `release` or `all`) and *all features* vs *required only* (`--required-only`)
3. `python3 settings/apply_settings.py <org-alias> plan --features <ids> [--required-only]` — fresh retrieve + diff (no org change)
4. `python3 settings/apply_settings.py <org-alias> deploy --features <ids> --confirm` — only after the user approves the plan (once per run)
5. `python3 settings/apply_settings.py <org-alias> verify --features <ids>`

**Numbering:** Phases 1a / 1b / 1c / 1d were previously numbered Phase 3 / 5 / 6 / 7.

**Script rules (all settings phases):**

* Prerequisites — (1) flag-level `requiresFeature` counts a selected prerequisite only if its core is in the same file (re-checked per feature during isolation) — a core in an earlier file must already be ON in the org; (2) between files, features whose prerequisite did not turn ON are excluded from later files even when the file also holds unblocked features (e.g. Fulfiller when Incident failed, 3e when the platform failed); (3) blocking is transitive (Proactive Assistant blocked when the Fulfiller is blocked). Blocked flags are reported "not applied — prerequisite … is not ON"; exit 2.
* Exit codes — If a later settings file's prerequisite failed (e.g. Release when Change core failed), its flags are marked "not applied — prerequisite … is not ON", its result file is still written, the run continues and exits 2 (report, don't fail — RC-44); exit 1 is reserved for systemic problems, bad input or prerequisites missing before start.
* `--features all` — feature attribute `optional="true"` (3e); `all` = every non-optional feature; optional phases run only when named; status marks them [optional]
* Status / permissions — `apply_settings.py status --json [--features <ids>]` gives machine-readable feature state (retrieves only the needed files); `apply_permissions.py` reads prerequisites from it instead of scraping text (fails closed); `plan/deploy --features all` prints a NOTE that 4c is a permissions phase run by `apply_permissions.py`; PSG status is shown per row and a non-"Updated" PSG is warned about before assignment.
* Safety — with_flags() asserts each managed flag appears exactly once in the retrieved settings XML; otherwise the run aborts ("refusing to patch; fix the spec") — protects against nested same-name booleans (Knowledge.settings has 5 nested booleans today, none managed).

**Permissions (RC-77):** Each feature phase lists its permission set groups in the spec (`<permissions feature=…>`): Incident (IncidentManagerPSG, IncidentFulfillerPSG, MajorIncidentManagerPSG), Problem (ProblemManagerPSG, ProblemFulfillerPSG), Change (ChangeRequestManagerPSG, ChangeRequestFulfillerPSG), Release (ReleaseManagerPSG, ReleaseGroupPSG), Unified Catalog 4c (3 UC PSGs). They are assigned to the connected user with `settings/apply_permissions.py <ORG> plan|deploy --confirm|verify --features <ids>` — only for selected phases; absent PSGs skipped; rejections reported. No additional PSGs (e.g. ItsmPortalUserPSG, EmployeeHub*, SetupWithAgentforceUserPsg) are audited or assigned.

**Feature ownership of shared IncidentMgmt flags:**

| Feature | Flags owned |
|---|---|
| Incident (1a) | core/validations/auto-close/Email-to-Incident (+AI, save, de-dup attachments)/Chat-to-Incident AI/major incident parent/requestor messaging/AI Knowledge creation/copy configuration items/privilege assignment/broadcasts (site banner, alert, email; Slack not managed) and Incident priority matrix+override |
| Problem (1b) | core/validations/auto-create Problem/Problem priority matrix+override |
| Change (1c) | core/risk assessment/validations/conflict detection + 4 conflict checks/Change priority matrix+override |
| Release (1d) | all 3 ReleaseMgmt flags |

**Observed behavior on this org:** it-service-cloud-bha853: user selected all IT Service Core features (Incident/Problem/Change = all flags, Release = all 3, user-requested). `status` shows all four phases ON. Notification Service (1e) deployed (3 flags).

---

## Phase 1a: Incident Management (formerly Phase 3)

**Purpose:** Enable ITSM Incident Management features.

**Check (Tooling API):**

```
SELECT Metadata FROM IncidentMgmtSettings LIMIT 1
```

Verify flags: `enableITSMIncidentMgmt`, `enableIncidentValidations`, `enableAutoClosureOfChildIncident`, `enableEmailToIncident`

**Deploy (Level 1 — programmatic, XML process):**

Phase 1a uses `settings/aits-itsm-settings.xml` + `settings/apply_settings.py <ORG> status|plan|deploy|verify --features incident` (see "IT Service Core" above). The script retrieves the org's current IncidentMgmt settings (Metadata API — the deployable 35 flags), sets only spec-listed flags to target, preserves everything else, deploys async, and isolates failing flags per feature in dependency order, splitting only inside a feature (failed flags are reported, the rest is applied; RC-68). Target = ALL flags of the selected features true except those marked manage=false (only tier="required" flags with `--required-only`).

1. `python3 settings/apply_settings.py <org-alias> plan --features incident` — fresh retrieve + diff (no org change)
2. `python3 settings/apply_settings.py <org-alias> deploy --features incident --confirm` — only after the user approves the `plan` output from step 1 (once per run); isolates failing flags; verify
3. `python3 settings/apply_settings.py <org-alias> verify --features incident`

Exit codes: `0` = all present flags at target; `2` = some flags dropped (see `settings/IncidentMgmt-result.md`); `1` = abort.

`deploy` requires `--confirm` — the user approves the `plan` output once per run (flags to change, any true→false reductions, worst-case deploy count). Failing flags are isolated by splitting the batch; a half already known to fail (its sibling succeeded) is split without re-deploying it. The run is capped at `3 × ceil(log2 n) + 1` deploys for n changed flags (n=5 → 10, 12 → 13, 23 → 16, 35 → 19), plus 1 per feature in the file (RC-68), which fully isolates up to 2 failing flags. Normal case = 1 deploy. If the cap is reached the run stops cleanly: applied flags stay, the rest are listed as *not attempted*, exit 2; continuing = fresh `plan` + one new approval. Optional `--retry-failed` re-tries isolated failures once (flag-order dependencies).

Each deploy is logged immediately to `settings/<Setting>-deploy-log.jsonl` (on submit and on finish). On interrupt (SIGINT/SIGTERM) the script finishes the current poll and submits nothing new.

Flags with `requires=` (e.g. Slack broadcasts) are skipped as *not available* unless `--assume-available` (availability-driven, Guardrail #5 / RC-44).

**Slack broadcasts:** Do not manage `enableSlackBroadcastType` (Slack is out of scope for this recipe). Spec marks it manage="false"; the org value is preserved.

**Full IncidentMgmtSettings flags reference** (reference only — execution goes through the script above, which retrieves and patches the org's settings; do not build deploy XML from this list):

```
enableAiKnowledgeCreation, enableAlertBroadcastType, enableAutoClosureOfChildIncident,
enableAutoCreationOfProblem, enableChangePriorityMatrix, enableChangePriorityOverride,
enableChangeRequestValidations, enableChatToIncidentAi, enableChgCnfcltForMaintSchd,
enableChgCnflctForChgOwner, enableChgCnflctForCnfgItems, enableChgCnflctForMoratSchd,
enableChgRqstCnflctDetection, enableCnfgItemCopyForRecords, enableDedupE2IncidentAttachment,
enableEmailBroadcastType, enableEmailToIncident, enableEmailToIncidentAi,
enableITSMChangeMgmt, enableITSMIncidentMgmt, enableITSMMajorIncParent,
enableITSMProblemMgmt, enableIncPriorityMatrix, enableIncPriorityOverride,
enableIncidentMgmt, enableIncidentValidations, enableMiawForRequestorAgent,
enablePrivilegeAssignment, enableProbPriorityMatrix, enableProbPriorityOverride,
enableProblemValidations, enableRiskAssessment, enableSaveE2IncidentAttachment,
enableSiteBannerBroadcastType, enableSlackBroadcastType
```

**Permissions (RC-77):** `settings/apply_permissions.py <org-alias> plan|deploy --confirm|verify --features incident` assigns IncidentManagerPSG, IncidentFulfillerPSG, MajorIncidentManagerPSG to the connected user (only when selected; absent PSGs skipped; rejections reported).

---

## Phase 1b: Problem Management (formerly Phase 5)

**Purpose:** Enable ITSM Problem Management.

**Check (Tooling API):**

```
SELECT Metadata FROM IncidentMgmtSettings LIMIT 1
```

Verify: `enableITSMProblemMgmt = true`, `enableProblemValidations = true`

**Deploy:** `settings/apply_settings.py <org-alias> plan|deploy|verify --features problem` (see "IT Service Core"). If selected together with Incident/Change, combined into one IncidentMgmt deploy automatically.

**Permissions (RC-77):** `settings/apply_permissions.py <org-alias> plan|deploy --confirm|verify --features problem` assigns ProblemManagerPSG, ProblemFulfillerPSG to the connected user (only when selected; absent PSGs skipped; rejections reported).

**Dependencies:** Incident Management must be enabled first.

---

## Phase 1c: Change Management (formerly Phase 6)

**Purpose:** Enable ITSM Change Management.

**Check (Tooling API):**

```
SELECT Metadata FROM IncidentMgmtSettings LIMIT 1
```

Verify: `enableITSMChangeMgmt = true`, `enableRiskAssessment = true`

**Deploy:** `settings/apply_settings.py <org-alias> plan|deploy|verify --features change` (see "IT Service Core"). If selected together with Incident/Problem, combined into one IncidentMgmt deploy automatically.

**Optional flags (enabled unless --required-only):** enableChgRqstCnflctDetection + the 4 conflict checks, enableChangeRequestValidations, Change priority matrix/override

**Permissions (RC-77):** `settings/apply_permissions.py <org-alias> plan|deploy --confirm|verify --features change` assigns ChangeRequestManagerPSG, ChangeRequestFulfillerPSG to the connected user (only when selected; absent PSGs skipped; rejections reported).

**Dependencies:** Incident Management must be enabled first.

---

## Phase 1d: Release Management (formerly Phase 7)

**Purpose:** Enable ITSM Release Management.

**Deploy (Level 1 — programmatic, XML process):** Phase 1d runs `settings/apply_settings.py <ORG> plan --features release` → user approval → `deploy --features release --confirm` → verify. Spec section `ReleaseMgmt` sets `enableITSMReleaseMgmt` (required), `enableReleaseValidations` and `enableReleaseEventCreation` to true. Prerequisite: Change Management ON (Phase 1c, selected or already ON). Replaces the 'direct deploy without reading first' and SOAP read workaround (RC-12).

1. `python3 settings/apply_settings.py <org-alias> plan --features release` — fresh retrieve + diff (no org change)
2. `python3 settings/apply_settings.py <org-alias> deploy --features release --confirm` — only after the user approves the plan (once per run)
3. `python3 settings/apply_settings.py <org-alias> verify --features release`

Same approval, deploy-cap, logging and exit-code rules as Phase 1a.

**Check (RC-50):** read ReleaseMgmt via metadata retrieve (`settings/apply_settings.py <org-alias> status --features release`); never infer from PSG presence — Release Management can be OFF on template orgs even when the Release PSGs are assigned.


**Permissions (RC-77):** `settings/apply_permissions.py <org-alias> plan|deploy --confirm|verify --features release` assigns ReleaseManagerPSG, ReleaseGroupPSG to the connected user (only when selected; absent PSGs skipped; rejections reported).

**Dependencies:** Change Management must be enabled first.

---

## Phase 1e: Notification Service [mandatory]

**1e Notification Service** [mandatory — always runs] — settings file ServiceCloudNotificationOrchestrator: enableNotifications (core), enableEmailNotifications, enableInAppNotifications (all required). Slack and Teams channels are not managed (`manage="false"`, requires Slack / Microsoft Teams — out of the recipe's scope). Prerequisite Incident Management: if Incident is neither selected nor ON, 1e is skipped with a note (the run does not abort); if Incident fails in the same run, 1e is held back.

`python3 settings/apply_settings.py <org-alias> plan|deploy --confirm|verify --features notify` (joins every run automatically: feature attribute `mandatory="true"`).

**Observed behavior on this org:** deploy Succeeded (3 flags); plan all = 0 changes.

**Follow-on template deploy (RC-90, note):** the notification email templates are customer-customised, so the recipe does NOT create or fix them — out of scope. The recipe notes that enabling Notification Service may trigger a Salesforce follow-on template deploy whose result can differ; on it-service-cloud-bha853 it failed and 0 of 28 templates exist (left as is). The cancelled follow-on after 4b is recorded as an observation only.

---

## Agentforce (Phases 3a–3e — feature-driven)

**Agentforce** phases, shown with status and run only if selected: **3a Agentforce Platform** (AgentPlatform.enableAgentPlatform, EinsteinGpt.enableEinsteinGptPlatform + enableEinsteinGPTDeployPromptTemplatesAsActive; prompt template permission sets) — needs Phase 0. **3b IT Service Fulfiller agent** (enableItSrvcsFulfillerAgent; agent exists → create via wizard if missing; activate; Access Agents) — needs 3a + Incident. **3c IT Employee Assistant** (enableItSrvcsEmployeeAgent; Enhanced Chat; channel/queue/routing/flow checks; activate; Access Agents) — needs 3a. **3d Proactive Assistant** (master + 7 Incident + 6 Problem flags; Problem flags need Problem Management) — needs 3b. **3e Optional AI features** (Incident Triage agent, Employee agent setup, 4 Einstein assignment/creation flags, service plan quick action) — needs 3a. Optional: offered in the selection list but never run unless the user picks it (user 2026-10-30; left OFF on it-service-cloud-bha853). Data Library (Steps 11/12) stays with Data Cloud (last).

`--features platform,fulfiller,employee,proactive,aiextras`; flags with `requiresFeature` (Problem flags of 3d/3e, Change flag of 3e) are "not applied" unless that feature is selected or ON. Not managed: enableSvcCtlgApexTemplate (Unified Catalog phase, later), enableCoexistFeature (purpose unclear).

1. `python3 settings/apply_settings.py <org-alias> status --features platform,fulfiller,employee,proactive,aiextras` (read-only)
2. `python3 settings/apply_settings.py <org-alias> plan --features <ids>` → user approval → `deploy --features <ids> --confirm` → `verify --features <ids>`
3. `python3 checks/check_agents.py <org-alias> [--features platform,fulfiller,employee]` (read-only)

**Agent checks (RC-72):** Run `checks/check_agents.py <ORG> [--features platform,fulfiller,employee]` (read-only). It discovers the agents (Fulfiller by template `…ITSrvcMgmtFulfiller`; Employee = the agent targeted by the routing flow `RouteMsgsItEmpAgent`), ignores any other agents, and reports PASS/FAIL with a fix hint for: prompt template permission sets (3a); Fulfiller exists / active / in Access Agents (3b); Enhanced Chat channel active, queue + routing config, queue objects, user is a direct member, routing flow active, Employee agent discovered / active / in Access Agents (3c); Access_Agents assigned. Fixes are applied only with user approval: programmatic where possible (activate, Access Agents, queue member), browser Level 2 for the Fulfiller wizard and Enhanced Chat setup.

**Agent names (RC-9):** the Employee agent = the agent the Enhanced Chat routing flow targets (discover; never hard-code). Other agents such as IT_Service_Employee may or may not exist on an org — ignore them (availability-driven, RC-44). Fulfiller name also discovered from the org. Below, `<FULFILLER_AGENT>` and `<EMPLOYEE_AGENT>` stand for the discovered DeveloperNames.

**Observed behavior on this org:** status = 3a–3d ON, 3e OFF (0/7, left OFF by user choice). `checks/check_agents.py` 14/14 PASS; ignored: IT_Service_Employee, Copilot_for_Salesforce. Employee agent = `ItEmployeeAssistant` (svc_emp_intelligence, Active, targeted by the routing flow); `IT_Service_Employee` (svc_itsm_intelligence, Inactive, unused).

**Authoring path (RC-22):** the ITSM agents are legacy Bot/GenAi agents; AiAuthoringBundle (Agent Script) is not supported on this org — maintain them with the legacy path.

### Phase 3a: Agentforce Platform (formerly Phase 12)

AgentPlatform.enableAgentPlatform, EinsteinGpt.enableEinsteinGptPlatform + enableEinsteinGPTDeployPromptTemplatesAsActive via the settings script (`--features platform`) — needs Phase 0. Prompt template permission sets (EinsteinGPTPromptTemplateUser, EinsteinGPTPromptTemplateManager) are assigned to the connected user with `settings/apply_permissions.py <org-alias> plan|deploy --confirm|verify --features platform` (RC-91) and checked by `checks/check_agents.py`. AI Trust PII masking moved to 9c.

### Phase 3b: IT Service Fulfiller agent

enableItSrvcsFulfillerAgent (`--features fulfiller`); agent exists → create via wizard if missing; activate; Access Agents — needs 3a + Incident.

#### Level 2 — create the Fulfiller via the wizard (formerly Step 7)

**Purpose:** If `checks/check_agents.py` reports the Fulfiller missing (3b), create it with the Agentforce agent creation wizard — with user approval. The Employee agent is not created here: it is provisioned by Enhanced Chat (3c) and discovered from the routing flow (RC-9).

**Prerequisites:**

* `checks/check_agents.py` run — the Fulfiller row FAILs (agent missing)
* The corresponding feature must be turned on (toggle checked ✅) before the wizard link becomes available

**Critical: Authentication requirement** The wizard runs inside the `/AiCopilot/copilotStudio.app` application which requires frontdoor URL authentication. **Direct navigation to the wizard URL will redirect to a login page.** You must:

1. Use `openSalesforceOrg` with the wizard path to get a frontdoor-authenticated URL
2. Navigate to the frontdoor URL which will authenticate and redirect to the wizard

**Wizard URL patterns:**

* **IT Service Fulfiller:** `/AiCopilot/copilotStudio.app#/copilot/wizard?mode=svc_itsm_intelligence__ITSrvcMgmtFulfiller`

**Alternative entry point:** On the Agentforce for IT Service page, expand the feature section and click the **"Go"** button next to "Build and Manage Agent" — this links directly to the wizard URL.

**Wizard flow (4 steps):**

**Scope: ONLY perform the actions listed below. Do not interact with any other toggles, buttons, or sections on this page.**

**Step 1 of 4 — Select Agent:**

* Page shows "Which agent are you building?" with radio button options
* The correct agent template is **auto-selected** based on the wizard `mode` parameter (e.g. "IT Service Management Fulfiller")
* **Action:** Click **"Next"** — no changes needed

**Step 2 of 4 — Select Agent Subagents:**

* Page shows "Which of these subagents should your agent use?" with checkboxes
* For IT Service Fulfiller, 4 subagents are **pre-selected by default**:
  * ✅ Incident Management
  * ✅ Problem Management
  * ✅ Change Request Management
  * ✅ Release Management
* **Action:** Click **"Next"** — keep all defaults selected

**Step 3 of 4 — Customize Agent:**

* Page shows agent configuration fields pre-filled with defaults:
  * **Agent Name** — pre-filled (e.g. "IT Service Management Fulfiller")
  * **Agent Developer Name** — pre-filled (e.g. "IT_Service_Management_Fulfiller")
  * **Agent Description** — pre-filled with descriptive text
  * **Role** — pre-filled
  * **Company** — ⚠️ **REQUIRED but left BLANK by default** — must be filled in
  * **Company Description** — optional
* **Action:** Fill in the **Company** field (use the org's company name or a generic name like "IT Services") and click **"Next"**

**Step 4 of 4 — Select Language and Tone:**

* Page shows language and tone options:
  * **Language:** English (default)
  * **Tone:** Casual (default, selected), Formal, or Custom
* **Action:** Click **"Finish"** — keep defaults

**After wizard completes:**

* The agent is created in **INACTIVE** state
* The browser redirects to the **Agentforce Builder** page for the newly created agent
* The builder URL pattern: `/AiCopilot/copilotStudio.app#/copilot/builder?copilotId=<ID>&versionId=<VID>`
* ⚠️ **beforeunload dialog:** When navigating away from the Agentforce Builder, a browser `beforeunload` dialog ("Leave site? Changes you made may not be saved") will appear. This must be accepted/dismissed to proceed.

**Verification:** After creating the agent, navigate back to the Agentforce for IT Service page: `/lightning/setup/page/feature/service-cloud-agentforce-for-itsm/home?topic=SalesforceGo` Expand the feature section and confirm:

* "Build and Manage Agent" now shows **"1 inactive agent"** instead of "0 agents"
* The "Go" link now points to the builder URL instead of the wizard URL

**Observed behavior on this org:**

* IT Service Employee: Already had 1 agent provisioned automatically after Enhanced Chat setup — no wizard needed
* IT Service Fulfiller: Had 0 agents after programmatic enablement — wizard was required to create the agent
* After wizard creation, Fulfiller showed "1 inactive agent" with a new copilotId

**Troubleshooting:**

* **Wizard redirects to login page:** You didn't use frontdoor authentication. Re-authenticate via `openSalesforceOrg` with the wizard path.
* **Step 3 "Company" field validation:** The wizard will not proceed without a value in the Company field. Fill in any company name.
* **beforeunload dialog blocks navigation:** Use dialog-accept to dismiss the "Leave site?" dialog when navigating away from the builder.
* **Agent created but not visible on IT Service page:** Refresh the Agentforce for IT Service page. The page may cache the previous state. Click "Sync Progress" button if available.
* **Wizard shows different subagents than expected:** The available subagents depend on which features/licenses are provisioned in the org. The 4 listed above are the standard IT Service Fulfiller subagents.

#### Activate agents (programmatic fix, formerly Step 8)

**Purpose:** Activate the discovered Fulfiller (3b) and Employee (3c) agents when `checks/check_agents.py` reports them inactive — with user approval.

**This step is fully programmatic — no browser needed.**

**Prerequisites:**

* Both agents exist (Fulfiller created via wizard if it was missing; Employee provisioned by Enhanced Chat)
* Must run from a valid SFDX project directory (has `sfdx-project.json`), otherwise `sf agent activate` fails with `InvalidProjectWorkspaceError`

**Agent names:** discovered by `checks/check_agents.py` (RC-9) — never hard-coded. Below, `<FULFILLER_AGENT>` and `<EMPLOYEE_AGENT>` stand for the discovered DeveloperNames.

**Activation command:**

```
sf agent activate --api-name <DeveloperName> --target-org <ORG> --json
```

Run this for each agent `checks/check_agents.py` reports inactive:

```
sf agent activate --api-name <EMPLOYEE_AGENT> --target-org <ORG> --json
sf agent activate --api-name <FULFILLER_AGENT> --target-org <ORG> --json
```

> **Note:** See Operational Learning #20 — this command requires a valid SFDX project directory.

Expected success response:

```json
{ "status": 0, "result": { "success": true, "version": 1 } }
```

**Verification:** re-run `checks/check_agents.py` (RC-72).

**Observed behavior on this org** (Employee = `ItEmployeeAssistant`):

* IT Employee Assistant was already active (auto-activated after Enhanced Chat provisioning)
* IT Service Fulfiller was inactive after wizard creation — activated successfully via `sf agent activate`
* Both agents confirmed active after activation

**Troubleshooting:**

* **`InvalidProjectWorkspaceError`:** You're not in an SFDX project directory. Navigate to a directory with `sfdx-project.json` or create a minimal one.
* **Agent already active:** `sf agent activate` on an already-active agent is a no-op — safe to run idempotently.
* **Agent not found:** Use the DeveloperName reported by `checks/check_agents.py` (case-sensitive).

#### Access Agents permission set (programmatic fix, formerly Step 9)

**Purpose:** If `checks/check_agents.py` reports an agent missing from Access Agents or Access_Agents unassigned, create/update the custom Permission Set that grants Agent Access to the discovered Fulfiller and Employee agents, then assign it to the connected user — with user approval.

**This step is fully programmatic — no browser needed.**

**Prerequisites:**

* Both agents are active
* Must run from a valid SFDX project directory

**Permission Set XML:**

Create file `force-app/main/default/permissionsets/Access_Agents.permissionset-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <agentAccesses>
        <agentName><EMPLOYEE_AGENT></agentName>
        <enabled>true</enabled>
    </agentAccesses>
    <agentAccesses>
        <agentName><FULFILLER_AGENT></agentName>
        <enabled>true</enabled>
    </agentAccesses>
    <description>Grants access to the IT Employee Assistant and IT Service Fulfiller Agentforce agents</description>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Access Agents</label>
</PermissionSet>
```

**Critical XML element ordering:** `agentAccesses` elements MUST appear first in the PermissionSet XML, before `classAccesses`, `description`, `fieldPermissions`, `label`, `objectPermissions`, etc. This follows the Salesforce Metadata API schema order.

**Deploy:**

```
sf project deploy start \
  --source-dir force-app/main/default/permissionsets/Access_Agents.permissionset-meta.xml \
  --target-org <ORG> --wait 10 --json
```

**Assign to connected user:**

```
sf org assign permset --name Access_Agents --target-org <ORG> --json
```

To assign to a specific user:

```
sf org assign permset --name Access_Agents --onbehalfof user@example.com --target-org <ORG> --json
```

**Verification:** re-run `checks/check_agents.py` (RC-72).

**Idempotency check:** Before creating, query whether it already exists:

```
SELECT Id, Name, Label FROM PermissionSet WHERE Name = 'Access_Agents'
```

If it exists, skip creation and go straight to assignment. If already assigned, `sf org assign permset` will report a failure (duplicate assignment) which is safe to ignore.

**Observed behavior on this org:**

* Permission set created successfully with both agent accesses
* Deployed as a new component (created=true)
* Assigned to the connected user
* No license required (License: None)

**Troubleshooting:**

* **Deploy queue contention:** First deploy attempt may get stuck/canceled. Retry — the second attempt usually succeeds immediately.
* **Agent name mismatch:** The `agentName` values must match the DeveloperNames discovered by `checks/check_agents.py` exactly.
* **Permission set already exists:** If deploying to an org that already has this permission set, the deploy will update it (not create a duplicate).
* **Assignment failure — already assigned:** `sf org assign permset` fails if the user already has the permission set. This is safe to ignore.

### Phase 3c: IT Employee Assistant (incl. Enhanced Chat)

enableItSrvcsEmployeeAgent (`--features employee`); Enhanced Chat; channel/queue/routing/flow checks; activate; Access Agents — needs 3a.

Phase **3c** first runs `checks/check_agents.py <ORG> --features employee`. Its row 'Enhanced Chat set up (channel + queue/routing + flow)' PASSes only when the messaging channel ItEmpAgentChannel is active, the queue ItEmpAgentMsgQueue has a routing config, and the routing flow RouteMsgsItEmpAgent is active. Only if it FAILs (and with user approval): Level 2 browser on 'Agentforce for IT Service' → 'Enable IT Service Agent Templates' → toggle ONLY 'Set Up Enhanced Chat for IT Service Employee' (click the container around the switch, Learning #21) → Confirm. Do NOT touch the IT Service Employee / IT Service Fulfiller / Specialized templates toggles. Provisioning creates channel, queue, routing config, routing flow and the Embedded Service deployment + site in the background (a few minutes) — re-run the check until all rows PASS, then the Employee agent is discovered from the routing flow. No settings flag turns Enhanced Chat on (ServiceItsmIntelligenceUdd.enableItSrvcsEmpSetup is OFF on an org where Enhanced Chat is fully set up).

#### Level 2 reference — Enhanced Chat page (formerly Step 2)

**Purpose:** Enable Omni-Channel and Enhanced Chat for IT Service Employee agents. This turns on persistent messaging so Agentforce agents can answer employee questions for IT troubleshooting, service requests, and incident tracking.

**URL:** `/lightning/setup/page/feature/service-cloud-agentforce-for-itsm/home?topic=SalesforceGo`

**Page verification:** Breadcrumb should show **"Salesforce Go > Agentforce for IT Service"**. The page header should read **"Agentforce for IT Service"** with description "Empower employees to self-serve or create incidents with Agentforce..."

**What you'll see on the page:**

* **Turn on Agentforce** section (should already show "On" with ✅ Success for Agentforce Studio)
* **Enable IT Service Agent Templates** section with three sub-options:
  * IT Service Employee (toggle) — ⛔ DO NOT TOUCH. Do not enable this toggle. It is NOT part of this recipe.
  * IT Service Fulfiller (toggle — may already be checked ✅ from 3b) — ⛔ DO NOT TOUCH. Already handled programmatically in 3b.
  * **Set Up Enhanced Chat for IT Service Employee** (toggle — ✅ this is the ONLY toggle to enable in this step)
* **Enable Specialized IT Service Agent Templates** section (separate, below) — ⛔ DO NOT TOUCH. Do not enable any toggles in this section. It is NOT part of this recipe.

**Interaction flow:** see phase 3c above (RC-87) — toggle ONLY "Set Up Enhanced Chat for IT Service Employee", with user approval, and only if its check row FAILs.

**Expected result after confirming:**

* The toggle shows as checked/enabled
* Background provisioning begins (Omni-Channel setup, messaging configuration)
* The page may show progress indicators or sub-steps appearing under the section
* A toast notification may appear confirming the feature was turned on

**Troubleshooting:**

* If the toggle doesn't respond to clicks, try clicking the **parent container element** (1-2 refs above the switch in the accessibility snapshot) rather than the switch element itself — see Operational Learning #21 about shadow DOM click interception on Lightning toggle components
* If provisioning fails, return to the page later and look for a "Try Again" button (similar to Assignment Rules pattern)
* This feature requires Agentforce to already be turned on (the "Turn on Agentforce" section must show "On")

### Phase 3d: Proactive Assistant

Master + 7 Incident + 6 Problem flags (`--features proactive`); Problem flags need Problem Management — needs 3b.

### Phase 3e: Optional AI features [optional]

Incident Triage agent, Employee agent setup, 4 Einstein assignment/creation flags, service plan quick action (`--features aiextras`) — needs 3a. Offered in the selection list but never run unless the user picks it; `--features all` excludes it (RC-74).

---

## Unified Catalog (Phases 4a–4c — feature-driven)

**Unified Catalog** phases, run only if selected: **4a Context Service** (IndustriesContext.enableContextDefinitions; shared with Assignment Rules) — needs Phase 0. **4b Service catalog Apex templates** (ServiceItsmIntelligenceUdd.enableSvcCtlgApexTemplate) — needs 4a. **4c Unified Catalog permissions** — assign PSGs UnifiedCatalogAdminPsl, UnifiedCatalogAgentPsl, UnifiedCatalogCommunityUserPsl to the connected user with `settings/apply_permissions.py <ORG> plan|deploy --confirm|verify --features ucperms`; a PSG not in the org is skipped, an assignment the org rejects is reported (not fatal) — needs 4a. Release Management is NOT a prerequisite (removed; nothing in these settings depends on it). The recipe creates no catalog items.

1. Settings (4a/4b): `python3 settings/apply_settings.py <org-alias> plan --features context,catalog` → user approval → `deploy --features context,catalog --confirm` → `verify`
2. Permissions (4c): `python3 settings/apply_permissions.py <org-alias> plan|deploy --confirm|verify --features ucperms`

`plan/deploy --features all` (settings script) prints a NOTE that 4c is a permissions phase run by `apply_permissions.py`; PSG status is shown per row and a non-"Updated" PSG is warned about before assignment (RC-75).

**Observed behavior on this org:** deployed 2026-10-30 with user approval — 4b Apex templates ON, 4c UnifiedCatalogAgentPsl assigned; verify OK, plan all = 0 changes.

---

## SLA Management (Phases 5a–5c)

**5a Turn on SLA Management** — check: Entitlement settings `enableEntitlements` + `enableEntitlementVersioning` = true and the page section 'Turn on SLA Management for IT Service' = On (sub-steps Simplified SLA Setup + SLA Versioning). If off: Level 2 browser 'Turn On' → Confirm (Level 1 settings deploy is untested). **5b Predefined policies** — check: SlaProcess exists for Incident, Problem and ChangeRequest. If all exist → done; do NOT click 'Create' (the page checkbox can stay unchecked even when policies exist; Create is irreversible). If missing → ask the user, then browser Create for the missing objects only. **5c Milestones related list on record pages** — report only (manual, optional). Manage SLA Policies / Auto Entitlement Rules remain manual. The page badge 'In Progress' reflects optional items — not a failure.

5c is an optional step, run only on user request.

**Check (RC-78):** `checks/check_sla.py <ORG>` (read-only): 5a Entitlement settings; 5b SLA policy per Incident/Problem/ChangeRequest (never click 'Create' when all exist); 5c Milestones related list per record page — OPTIONAL (the Milestone Tracker component is a different thing and is reported as info).

On template orgs the predefined SLA policies often already exist — check 5b before any browser action (RC-11).

**Observed behavior on this org:** page On 100%; policies active for all three objects; the Create checkbox stays unchecked; Milestones related list absent on the record pages (5c not done; the Milestone Tracker component is present on all 5 pages).

### Level 2 reference — SLA Management page (formerly Step 15)

**Purpose:** Enable SLA Management for IT Service to define service-level agreements for Incident, Problem, and Change Request records. This turns on Simplified SLA Setup and SLA Versioning, and optionally creates predefined SLA policies.

**This step requires browser.**

**URL:** `/lightning/setup/page/feature/service-cloud-itsm-manage-sla-policies/home?topic=SalesforceGo`

**Page verification:** Breadcrumb should show **"Salesforce Go > SLA Management for IT Service"**. Header: **"SLA Management for IT Service"** with description "Manage your service-level agreements to give your employees the level of support you've promised them and improve service reps efficiency."

**Browser flow:**

**Scope: ONLY perform the actions listed below. Do not interact with any other toggles, buttons, or sections on this page.**

**1. Check current state:**

* If the page shows a **"Get Started"** button → click it to reveal the Turn On section
* If the page already shows **"Turn on SLA Management for IT Service"** with **"On"** → SLA Management is already enabled, skip to step 3

**2. Turn on SLA Management:**

* The page shows **"Turn on SLA Management for IT Service"** section with a **"Turn On"** button
* Two sub-steps are listed in Pending state:
  * ⏳ Turn on Simplified SLA Setup
  * ⏳ Turn on SLA Versioning
* Click **"Turn On"**
* A confirmation dialog appears: **"Turn on SLA Management for IT Service?"**
  * Message: "It takes a few minutes to turn on this feature for you. When it's ready, you can configure settings and give users access."
* Click **"Confirm"**
* Both sub-steps should complete quickly:
  * ✅ Turn on Simplified SLA Setup — Success
  * ✅ Turn on SLA Versioning — Success
  * Progress: 100%

**3. (5b) Create Predefined Policies — only for objects without a policy:**

⛔ **If `checks/check_sla.py` shows a policy for Incident, Problem and ChangeRequest, do NOT click "Create"** (RC-76) — the page checkbox can stay unchecked even when policies exist.

⚠️ **ASK THE USER BEFORE THIS STEP — this action is IRREVERSIBLE.**

> **⚡ Pre-check (see Operational Learning #18):** Before creating policies, query whether SLA policies already exist:
>
> ```
> SELECT Id, Name, SobjectType FROM SlaProcess WHERE SobjectType IN ('Incident','Problem','ChangeRequest')
> ```
>
> If policies already exist, show them to the user and confirm whether to proceed. Creating duplicates may cause confusion.

The page shows a "Set Up the Basics" section with a **"Create Predefined Policies"** sub-step and a **"Create"** button. This creates 3 standard SLA policies (one each for Incident, Problem, and Change Request) without any actions configured. Once created, these policies cannot be removed.

**If user approves:**

* Click **"Create"** next to "Create Predefined Policies"
* A dialog appears: **"Configure predefined SLA policies for the following objects:"**
  * ☐ Incident
  * ☐ Problem
  * ☐ Change Request
  * Warning: "You can't revert your selections when you save the changes"
* Check all three checkboxes (click the labels, not the checkbox inputs directly — the checkbox is intercepted by its container)
* The **"Save"** button becomes enabled once at least one checkbox is checked
* Click **"Save"**
* Both buttons (Cancel and Save) become disabled during processing
* After processing completes, the dialog closes
* The checkboxes will show as checked and disabled on subsequent opens (confirming creation)

**If user declines:**

* Skip this sub-step. Policies can be created manually later via the SLA Policies setup page.

**Expected result after completion:**

* **"Turn on SLA Management for IT Service"** shows **"On"** with Progress: 100%
* Both automation sub-steps show ✅ Success
* Remaining manual steps (Add Components to Lightning Pages, Manage SLA Policies, Manage Auto Entitlement Rules) are left for the user

**Remaining manual configuration (not automated by recipe):**

* **Add Components, Fields, and Actions to Lightning Record Pages** — Add the Milestones related lists to Incident record pages
* **Manage SLA Policies and SLA Milestones** — Configure policies and milestones in Setup → SLA Policies
* **Manage Auto Entitlement Rules** — Set up auto-apply rules so policies are automatically applied to records

**Observed behavior on this org:**

* Page initially showed "Get Started" button — clicked to reveal the Turn On section
* SLA Management turned on successfully — both sub-steps completed immediately (Simplified SLA Setup ✅, SLA Versioning ✅)
* Predefined Policies created for all 3 objects (Incident, Problem, Change Request) — user approved
* On re-opening the Create dialog, all checkboxes showed as checked and disabled (confirming irreversibility)

**Troubleshooting:**

* **"Get Started" button doesn't appear:** The feature may already be turned on. Check if the page shows "On" status.
* **Turn On fails:** Verify that Incident Management (Phase 1a) is enabled. SLA Management depends on ITSM features being active.
* **Create Predefined Policies — Save button stays disabled:** At least one checkbox must be checked before Save becomes enabled.
* **Checkbox click doesn't register:** Click the label text next to the checkbox rather than the checkbox input itself — the input element is intercepted by a container span.
* **Dialog buttons disabled after Save:** This is normal — the system is processing. Wait for the dialog to close automatically.

---

## Assignment Rules (Phases 6a–6c)

**6a Context Service** — same as 4a (IndustriesContext.enableContextDefinitions); not deployed twice. **6b Business rules engine permissions** — permission set licences BRERuntime + BREDesigner, then permission sets BRERuntime + BREDesigner, assigned to the connected user (licences first); via the permissions script with --confirm. **6c BRE Decision Table Access** — check: an active DecisionTable and the IT Service sample expression set (Sample_Assignment_Rule_for_Incident) exist; if not, Level 2 browser: Assignment Rules for IT Service page → 'Try Again'/'Turn On' → Confirm. No queryable setting exists for Decision Table Access, so the page is the fallback source of truth.

1. 6a: `python3 settings/apply_settings.py <org-alias> plan|deploy --confirm|verify --features context` (same feature as 4a — skip if already ON)
2. 6b: `python3 settings/apply_permissions.py <org-alias> plan|deploy --confirm|verify --features bre` (licences → permission sets)
3. Check: `python3 checks/check_assignment_rules.py <org-alias>` (read-only)

**Permissions script (RC-80):** result file per mode — deploy → permissions-result.md, plan → permissions-plan.md, verify → permissions-verify.md (read-only checks such as check_assignment_rules.py call verify); `<ps requiresPsl="…">` is reported "not applied — licence … not assigned" and not attempted when its licence could not be assigned.

**Observed behavior on this org:** 6a ON; 6b licences + permission sets assigned; 6c active decision table + Sample_Assignment_Rule_for_Incident present; page shows Turn on = On with both sub-steps Success.

### Level 2 reference — Assignment Rules page (formerly Step 1, 6c fallback)

**Purpose:** Enable Context Service and BRE Decision Table Access for IT Service assignment rules.

> **⚡ Auto-complete behavior:** After 6a/4a deploys Context Service (`enableContextDefinitions`), the "Context Service" sub-step on this page auto-completes to ✅. Only "BRE Decision Table Access" typically requires manual action. If you visit this page after 6a and see all sub-steps showing ✅ Complete, **no action is needed** — skip this step entirely.

**URL:** `/lightning/setup/page/feature/service-cloud-itsm-assignment-rules/home?topic=SalesforceGo`

**Page verification:** The breadcrumb at top should show **"Salesforce Go > Assignment Rules for IT Service"**. If it does not, stop and verify you have the correct URL and org.

**What you'll see:**

* Header: "Assignment Rules for IT Service"
* A "Turn on Assignment Rules for IT Service" card with sub-steps
* Progress indicator showing completion status (e.g. "1 of 3 Steps Completed")

**Sub-steps on the page:**

1. **Turn on Assignment Rules** — Contains two sub-tasks:
   * **Context Service** — May already show ✅ (auto-enabled by 6a/4a)
   * **BRE Decision Table Access** — Must be enabled manually in Setup UI

**Interaction flow:**

**Scope: ONLY perform the actions listed below. Do not interact with any other toggles, buttons, or sections on this page.**

1. Navigate to the URL above
2. Look for the "Turn on Assignment Rules for IT Service" section
3. If status shows "Complete" for both Context Service and BRE Decision Table Access → no action needed
4. If BRE Decision Table Access shows ⏳ Pending or ❌ Error:
   * Look for a **"Try Again"** button on the page
   * Click **"Try Again"**
   * A confirmation dialog will appear asking to confirm the action
   * Click **"Confirm"** in the dialog
5. Wait for both sub-steps to show ✅ (typically completes within 5-10 seconds)

**Expected result:**

* Context Service: ✅ Success
* BRE Decision Table Access: ✅ Success
* Progress: 100% (or "Step Completed")
* Toast notification: **"Assignment Rules for IT Service was turned on and is ready to configure"**

**Troubleshooting:**

* If "Try Again" doesn't appear, the page may show a **"Turn On"** button instead — click that
* If the step fails repeatedly, verify that the Context Service PSL and BRE PSLs are assigned to the user (6b permissions)
* If the page shows "Feature not available", the org may lack the required ITSM licenses

---

## Knowledge (Phases 7a–7b)

**7a Knowledge settings** — spec section `Knowledge` (feature `knowledge`, core enableKnowledge): enableKnowledge, enableLightningKnowledge (required) + enableCreateEditOnArticlesTab, enableExternalMediaContent, enableKbStandardSharing, enableKnowledgeArticleTextHighlights, showArticleSummariesCustomerPortal, showArticleSummariesInternalApp, showValidationStatusField, votingEnabled (optional). Runs through the settings script: retrieve-patch-deploy keeps the nested `suggestedArticles` block exactly as retrieved, which removes the recipe's XML-structure failure risk (Learning #16). **7b Knowledge readiness check** (read-only): connected user has Knowledge User; Knowledge__kav has the ITSM fields Details, Issue, Resolution, Root Cause, Workaround (needed by the Data Library); record types; published article count. Fix with approval: set Knowledge User on the connected user. AI Knowledge creation stays with phase 1a (IncidentMgmt) and needs Knowledge ON.

1. 7a: `python3 settings/apply_settings.py <org-alias> plan|deploy --confirm|verify --features knowledge`
2. 7b: `python3 checks/check_knowledge.py <org-alias>` (read-only)

**Observed behavior on this org:** all 10 Knowledge flags already true; Knowledge User true; 5 ITSM fields present; 8 published articles.

---

## Self-service portal (Phases 8a–8c)

**8a Self Service Portal ON** — no queryable setting; confirm on the Salesforce Go page (read-only): 'Turn on Self Service Portal' = On. If off: browser Turn On → Confirm (user approval). **8b Portal site** — `checks/check_portal.py <ORG>` lists candidate sites by template (Connect API `templateName` = Agentic Center or Agentforce Employee Center; Embedded Service sites are chat deployments and excluded). Ask the user which existing site to use; create a new one (Connect API, name + URL suffix from the user) only if they choose to. Either template is valid — the Salesforce Go page recommends Agentforce Employee Center / Employee Portal, the original recipe used Agentic Center. **8c Published** — chosen site Live; publish only with user approval.

The chosen site is the target for Embedded chat (phase 10).

Check: `python3 checks/check_portal.py <org-alias> [--site "<site name>"]` (read-only).

**Observed behavior on this org:** the user chose **ITSMPortal** (Agentic Center, Live, site root) as this org's portal; page On 100%; 8b/8c PASS.

### Reference — create a new site (only if the user chooses; formerly Step 10)

**Step 1 — List available templates (Connect API via `sf api request rest`):**

```
sf api request rest '/services/data/v67.0/connect/communities/templates' --method get --target-org <ORG>
```

Verify `"Agentic Center"` is in the response. If not, inform the user and skip — the template may not be provisioned in the org.

> **⚠️ Use `sf api request rest`, NOT `curl`** — see Operational Learning #17. The `sf org display` command returns redacted access tokens that break `curl` calls. `sf api request rest` handles authentication automatically.

**Step 2 — Create the site (Connect API via `sf api request rest`):**

```
sf api request rest '/services/data/v67.0/connect/communities' --method post --body '{"name":"<SITE_NAME>","urlPathPrefix":"<URL_SUFFIX>","templateName":"Agentic Center"}' --target-org <ORG>
```

The response includes a `jobId` for async tracking:

```json
{
  "jobId": "08Pxxxxxxxxx",
  "message": "Your site is almost ready. To track the site creation status, query the BackgroundOperation object...",
  "name": "<SITE_NAME>"
}
```

**Step 3 — Poll for completion:**

```
SELECT Id, Name, Status, Error FROM BackgroundOperation WHERE Id = '<jobId>'
```

Poll every 5-10 seconds until `Status = 'Complete'`. If `Error` is not null, the creation failed.

**Step 4 — Verify site created:**

```
SELECT Id, Name, UrlPathPrefix, Status FROM Network WHERE Name = '<SITE_NAME>'
```

Expected: Status = `UnderConstruction` (site is created but not yet published).

**User input required:** Before creating, ask the user for:

1. **Portal name** (e.g. "Employee Service Portal")
2. **URL suffix** (e.g. "helpdesk" → `https://<org>.my.site.com/helpdesk`)

**Troubleshooting:**

* **Template not found:** The "Agentic Center" template may not be provisioned. Check if "Agentforce Employee Center" is available as an alternative. If neither exists, inform user and skip.
* **URL suffix conflict:** If the URL path prefix is already in use by another site, creation will fail. Choose a different suffix.
* **BackgroundOperation stuck in "Running":** Wait longer — site creation can take up to 60 seconds. If stuck >2 minutes, check for errors.
* **Digital Experiences not enabled:** The Connect API will fail if Digital Experiences is not enabled in the org. Enable it first via Setup → Digital Experiences → Settings.

---

## Data Cloud (Phases 9a–9d — ALWAYS LAST)

**9a Turn on Data Cloud** — settings spec feature `datacloud` (CustomerDataPlatform.enableCustomerDataPlatform), placed LAST in file order; plan → user approval → deploy --confirm. The deploy itself is quick; it then triggers a background 'Automated Process' InstalledPackage deploy (ssot, ~10–30 min). **Never cancel it.** Wait with read-only polling (DeployRequest by Automated Process; IsCustomerDataPlatformEnabled; ssot package) — nothing else may deploy meanwhile. **9b Data Cloud permissions** — GenieAdmin (and GenieUserEnhancedSecurity only if it exists after provisioning) to the connected user via the permissions script. **9c AI Trust PII masking** [optional] — EinsteinAI.enableTrustPIIMasking; run it in a LATER run, after Data Cloud provisioning has completed (if selected together with 9a on a fresh org it is held back as "prerequisite not ON", because provisioning is asynchronous). **9d Data Library** — runs only AFTER Data Cloud provisioning has completed, as a separate follow-up run (user 2026-11-02: "post the Data Cloud enablement we will ask the agent to do that"). Uses the existing browser steps unchanged (original Step 11 Create Data Library "ITSM Knowledge" and Step 12 Connect Data Library to Agents and Reactivate) — they are kept verbatim, no rewrite needed; agent names come from RC-9 discovery.

1. 9a: `python3 settings/apply_settings.py <org-alias> plan --features datacloud` → user approval → `deploy --features datacloud --confirm`; then read-only polling until the Automated Process install finishes
2. 9b: `python3 settings/apply_permissions.py <org-alias> plan|deploy --confirm|verify --features datacloud` — GenieAdmin (RC-91). **Manual (RC-91):** after Data Cloud provisioning completes, an admin assigns permission set "Data Cloud User Enhanced Security" in Setup → Permission Sets → Manage Assignments, to the users who need it (it does not exist before provisioning).
3. 9c (optional, in a LATER run after provisioning has completed): `--features piimask`
4. 9d: separate follow-up run after provisioning has completed — Level 2 browser steps below, each with user approval

**Observed behavior on this org:** Data Cloud turned on 2026-11-02 (deploy 0AfgL00000cRYxOSAW Succeeded; enableCustomerDataPlatform false → true). Per Atlas's handoff, the Automated Process install was still in progress at that time — never cancel it. GenieUserEnhancedSecurity appeared after Data Cloud was enabled (RC-26 — Assign GenieUserEnhancedSecurity only if it exists after Data Cloud provisioning; otherwise log informational. → now the manual 9b step, RC-91).

> **Run only after Data Cloud provisioning has completed, as a separate follow-up run.** Provisioned check: `SELECT IsCustomerDataPlatformEnabled FROM CustomerDataPlatformSettings` = true (RC-19). The two browser steps below are the original recipe text, kept verbatim; only the agent names use the RC-9 placeholders `<FULFILLER_AGENT>` / `<EMPLOYEE_AGENT>` (discovered by `checks/check_agents.py`).

### Step 11: Create Agentforce Data Library — ITSM Knowledge (browser — requires Data Cloud)

**Purpose:** Create an Agentforce Data Library that indexes Knowledge articles so agents can search and retrieve ITSM knowledge when resolving incidents, problems, and service requests.

**This step requires browser — no programmatic API available for Data Library creation.**

**Prerequisites:**

* **Data Cloud must be provisioned** in the org. If Data Cloud is not enabled, **skip this step entirely**.
* Both IT Service agents must be created (Step 7/8)
* Access Agents permission set assigned to user (Step 9)
* Knowledge must be enabled (Phase 4 programmatic setup)

**How to check if Data Cloud is provisioned:** Query for Data Cloud permission sets or check Setup:

```
SELECT Id, Name FROM PermissionSet WHERE Name LIKE '%DataCloud%' OR Name LIKE '%Cdp%' LIMIT 5
```

Or navigate to Setup → Data Cloud. If the section is absent or shows an enablement prompt, Data Cloud is not provisioned — skip this step.

**URL:** `/lightning/setup/EinsteinDataLibrary/home`

**Browser flow:**

**Scope: ONLY perform the actions listed below. Do not interact with any other toggles, buttons, or sections on this page.**

**1. Navigate to Agentforce Data Library:** Setup → Search "Agentforce Data Library" or navigate directly to `/lightning/setup/EinsteinDataLibrary/home`

**2. Create new library:**

* Click **"New Library +"** button
* **Name:** `ITSM Knowledge`
* The **API Name** field auto-populates based on the Name (e.g. `ITSM_Knowledge`)
* Click **Save**

**3. Configure the library:** After saving, you'll be taken to the library configuration page.

* **Select Data Type:** Choose **Knowledge**

* **Identifying Field(s):** Select the following:

  * ✅ Title
  * ✅ Summary

* **Content Fields:** Check the following:

  * ✅ Details
  * ✅ Issue
  * ✅ Resolution
  * ✅ Root Cause
  * ✅ Workaround

* Click **Save**

**4. Wait for indexing:** ⚠️ **This step can take 5 minutes or more.** After clicking Save, the page will show a processing/indexing indicator. **Wait for the page to finish and confirm the library was saved.** Do not navigate away during this process.

**Verification:** After the save completes, the library should appear in the Agentforce Data Library list at `/lightning/setup/EinsteinDataLibrary/home` with:

* Name: ITSM Knowledge
* Data Type: Knowledge
* Status: Active/Ready (or similar)

**Observed behavior on this org:**

* ⚠️ **Not tested** — Data Cloud was not provisioned on the connected org, so this step was skipped.
* This step is documented from the setup guide and should be validated on an org with Data Cloud enabled.

**Troubleshooting:**

* **Data Library page not found / blank:** Data Cloud is not provisioned. Skip this step.
* **Knowledge not available as Data Type:** Knowledge may not be enabled. Verify Knowledge is enabled in Setup → Knowledge Settings.
* **Content fields not visible:** The Knowledge article type may not have the expected fields (Details, Issue, Resolution, Root Cause, Workaround). These are standard ITSM Knowledge fields — verify they exist on the Knowledge object.
* **Save takes too long:** The indexing process can take 5+ minutes. If it exceeds 10 minutes with no progress, refresh and check if the library was created.
* **"Identifying Fields" or "Content Fields" options differ:** Field availability depends on the Knowledge article record type and field configuration. Select the closest matching fields available.

### Step 12: Connect Data Library to Agents and Reactivate (browser — requires Data Cloud)

**Purpose:** Connect the ITSM Knowledge Data Library (created in Step 11) to both IT Service agents so they can search Knowledge articles when resolving issues. Requires deactivating, configuring, and reactivating each agent.

**This step requires browser — no programmatic API available for Data Library assignment in the Agent Builder.**

**Prerequisites:**

* **Data Cloud must be provisioned** — if not, skip this step entirely
* Step 11 completed — ITSM Knowledge Data Library created and indexing finished
* Both agents exist and are active (Steps 7/8)

**Repeat the following flow for EACH agent:**

1. IT Employee Assistant (`<EMPLOYEE_AGENT>`)
2. IT Service Fulfiller (`<FULFILLER_AGENT>`)

---

**Agent Builder URLs:**

* IT Employee Assistant: `/AiCopilot/copilotStudio.app#/copilot/builder?copilotId=<EMPLOYEE_AGENT_ID>`
* IT Service Fulfiller: `/AiCopilot/copilotStudio.app#/copilot/builder?copilotId=<FULFILLER_AGENT_ID>`

To find the copilot IDs:

```
SELECT Id, DeveloperName, MasterLabel FROM BotDefinition
WHERE DeveloperName IN ('<EMPLOYEE_AGENT>','<FULFILLER_AGENT>')
```

**Alternative entry point:** Setup → Agentforce Agents → click the agent name → click **"Open in Builder"** (top right)

⚠️ **Authentication:** The Agent Builder runs inside `/AiCopilot/copilotStudio.app` which requires frontdoor URL authentication. Use `openSalesforceOrg` with the builder path to get an authenticated URL.

---

**Browser flow (per agent):**

**Scope: ONLY perform the actions listed below. Do not interact with any other toggles, buttons, or sections on this page.**

**1. Navigate to the Agent Builder:**

* Go to Setup → Agentforce Agents (or use `/lightning/setup/CopilotStudioAssistants/home`)
* Click the agent name (e.g. "IT Employee Assistant")
* Click **"Open in Builder"** button in the top right

**2. Deactivate the agent:**

* In the top right of the Builder, click **"Deactivate"**
* This is required to allow changes to be saved
* Wait for deactivation to complete

**3. Connect the Data Library:**

* In the **left panel**, click **"Data"** tab
* Under **"Data Library"** section, select the library you created: **ITSM Knowledge**
* At the bottom of the page, click **"Save"**

**4. (Optional) Enable Public Knowledge Articles:**

* Still on the Data tab, switch to the **"Knowledge Settings"** sub-tab
* Toggle **"Use Public Knowledge Articles"** to **ON**
* Click **Save** if prompted

**5. Reactivate the agent:**

* In the top right, click **"Activate"**
* If a popup appears (e.g. "Some actions may not be configured"), click **"Ignore & Activate"**
* Wait for activation to complete

**6. Navigate away:**

* ⚠️ A **beforeunload dialog** ("Leave site? Changes you made may not be saved") may appear when navigating away from the Builder. Accept/dismiss it to proceed.

---

**Repeat for second agent:** After completing the flow for IT Employee Assistant, repeat the exact same steps for IT Service Fulfiller.

**Verification:** After connecting the library to both agents:

* Each agent's Builder → Data tab should show "ITSM Knowledge" selected under Data Library
* Both agents should be in Active state
* On the Agentforce for IT Service page (`/lightning/setup/page/feature/service-cloud-agentforce-for-itsm/home?topic=SalesforceGo`), both agents should show as active

**Programmatic verification** (optional):

```
SELECT BotDefinition.DeveloperName, BotDefinition.MasterLabel, Status
FROM BotVersion
WHERE BotDefinition.DeveloperName IN ('<EMPLOYEE_AGENT>','<FULFILLER_AGENT>')
```

Both should show `Status = 'Active'`.

**Observed behavior on this org:**

* ⚠️ **Not tested** — Data Cloud was not provisioned on the connected org, so this step was skipped.
* This step is documented from the setup guide and should be validated on an org with Data Cloud enabled.

**Troubleshooting:**

* **"Data" tab not visible in Builder:** Data Cloud may not be provisioned or the agent may not support Data Library connections. Verify Data Cloud is enabled.
* **ITSM Knowledge library not in dropdown:** The library may still be indexing (Step 11). Wait for indexing to complete and refresh the Builder.
* **Save fails after selecting library:** Ensure the agent is deactivated first. The Builder does not allow saving changes to an active agent.
* **"Ignore & Activate" popup:** This appears when some agent actions/topics are not fully configured. It's safe to ignore for initial setup — the agent will function with whatever actions are configured.
* **beforeunload dialog:** When navigating away from the Builder, accept the "Leave site?" dialog. This is standard Builder behavior and does not indicate unsaved changes if you already clicked Save.
* **Agent stays inactive after activation:** Check for errors in the Builder. Some configuration issues can prevent activation. Review the agent's topics and actions for any warnings.

---

## Embedded chat on the portal (Phases 10a–10c)

**10a Deployment** — check EmbeddedServiceConfig (Tooling) for the Enhanced Chat deployment (here ItEmpAgentChannel: Web, EmbeddedMessaging, enabled). **10b Framing** — check SiteIframeWhiteListUrl on the deployment's ESW site includes the portal domain (`*.site.com` covers my.site.com portals); add it with user approval if missing. **10c Widget on the portal** — Aura sites (e.g. Agentic Center ITSMPortal): needs 'Enable ExperienceBundle Metadata API' (Digital Experiences > Settings) to read/patch the site's theme `embeddedMessagingConfig` / `embeddedMessagingEswLiveAgentDevName` / `embeddedMessagingSiteEndpoint`; otherwise Experience Builder (browser) → Settings → Embedded Messaging → select the deployment → Publish. LWR sites: head markup snippet from Setup > Embedded Service Deployments > Install Code Snippet. Publish the site after changes (with approval). Help article remains the reference: service.it_srvcs_embedded_msgng_manual_steps.

10a and 10b are checked programmatically; **10c is a MANUAL step** (help article). The target site is the portal chosen in 8b.

**Reference:** Salesforce Help — https://help.salesforce.com/s/articleView?id=service.it_srvcs_embedded_msgng_manual_steps.htm&type=5

**Observed behavior on this org:** 10a PASS (ItEmpAgentChannel: Web, EmbeddedMessaging, enabled); 10b PASS (`*.site.com`); the user confirmed the widget is on ITSMPortal.

---

## CMDB & Service Graph (Phases 11a–11c)

**11a** `checks/check_cmdb.py <ORG>` (read-only): CMDB objects (ConfigurationItem, Incident/Problem link objects) present, CMDB permission sets assigned to the connected user; configuration item count (info). **11b** provisioning — no setting exists; confirm on CMDBProvisionalSettings (Status Provisioned, both stages Completed); if not: browser 'Provision CMDB' with user approval, runs in the background, re-check later. **11c** CMDB feature — confirm on the Salesforce Go CMDB page ('Turn on CMDB' switch ON); if off: browser 'Get Started' (if shown) → toggle → Confirm with user approval. Other page items (base configuration, auto discovery, CI-to-Asset, CI workflows) are manual/optional and never clicked.

Check: `python3 checks/check_cmdb.py <org-alias>` (read-only; 11b/11c need page confirmation).

The CMDB permission sets only exist after CMDB provisioning, so they are checked in 11a, not in the Pre-flight audit — on fresh orgs they would show as false "missing" (RC-24; fresh-org rule, RC-30).

**Observed behavior on this org:** Provisioned (Oct 16), both stages Completed; CMDB feature ON; auto-copy ON; 0 configuration items; 4 CMDB permission sets + 2 PSGs assigned (they already exist here because CMDB is provisioned — RC-30).

### Level 2 reference — provisioning and feature pages (formerly Steps 3/3b)

**Purpose:** Provision CMDB (Configuration Management Database) and Service Graph to enable configuration item tracking for IT Service Management.

**URL:** `/lightning/setup/CMDBProvisionalSettings/home`

**Page verification:** The main content area should show **"CMDB and Service Graph Provisioning Settings"** with description "View the current provisioning status of CMDB and service graph, start or retry provisioning..."

**What you'll see on the page:**

* **Provisioning Status** card showing:
  * Status: `Unprovisioned` / `Provisioned` / `In Progress`
  * Last Run On / Last Run By / Job Status
* **CMDB Provisioning** card with two provisioning stages:
  * Step 1: Licenses Applied
  * Step 2: CMDB Services Enabled
* A **"Provision CMDB"** button (if not yet provisioned or if previous attempt failed)

**Interaction flow:**

**Scope: ONLY perform the actions listed below. Do not interact with any other toggles, buttons, or sections on this page.**

1. Navigate to the URL above
2. Check the **Provisioning Status** section:
   * If **Status = "Provisioned"** → no action needed, skip this step
   * If **Status = "Unprovisioned"** or **Job Status = "Failed"** → proceed to step 3
   * If **Status = "In Progress"** → provisioning is already running, use "Refresh Status" button to check
3. Click the **"Provision CMDB"** button
4. The button becomes disabled and a **"Refresh Status"** button appears
5. **Do NOT wait for completion** — provisioning runs in the background and can take several minutes
6. The provisioning stages will update:
   * Step 1: Licenses Applied → typically completes quickly
   * Step 2: CMDB Services Enabled → may take several minutes

**Expected result after clicking Provision CMDB:**

* Job Status changes to "In Progress"
* Step 1: Licenses Applied — ✅ Completed (may already be done from a previous attempt)
* Step 2: CMDB Services Enabled — ⏳ Provisioning In Progress
* "Provision CMDB" button becomes disabled
* "Refresh Status" button appears to poll for completion

**Known issue:** Provisioning can fail at Step 2 ("CMDB Services Enabled"). If this happens:

* The page shows "Provisioning Failed" with message "This step couldn't be completed. Retry provisioning."
* The "Provision CMDB" button reappears — click it to retry
* Step 1 (Licenses Applied) typically stays completed across retries — only Step 2 re-runs

**Post-provisioning — 11c: Turn on CMDB Feature**

After CMDB provisioning completes (Status = "Provisioned"), you must also enable the CMDB feature via the Salesforce Go setup page:

**URL:** `/lightning/setup/page/feature/service-cloud-itsm-cmdb-integration/home?topic=SalesforceGo`

**Page verification:** Breadcrumb should show **"Salesforce Go > Configuration Management Database (CMDB)"**. Header: **"Configuration Management Database (CMDB)"**.

**Interaction flow:**

**Scope: ONLY perform the actions listed below. Do not interact with any other toggles, buttons, or sections on this page.**

1. Navigate to the URL above
2. If the page shows a **"Get Started"** button → click it. This transforms the page to show the enable toggle.
3. After clicking "Get Started", a **"Turn on Configuration Management Database (CMDB)"** section appears with an Enable/Disable toggle
4. Click the **Enable/Disable Feature** toggle
5. A confirmation dialog appears: **"Turn on Configuration Management Database (CMDB)?"**
   * Message: "It takes a few minutes to turn on this feature for you."
6. Click **"Confirm"**
7. The toggle becomes checked — feature is now enabled

**Execution order note:** Since CMDB provisioning takes several minutes, the recommended flow is:

1. Start CMDB provisioning (11b — click "Provision CMDB", with user approval)
2. Move on to other phases
3. Come back to check provisioning status
4. Once provisioned, navigate to the CMDB integration page (11c) and turn it on (with user approval)

**Post-enablement:** The CMDB permission sets (`ItSrvcCnfgItmOwnerPermissionSet`, `ItSrvcCnfgItmReadPermissionSet`, `ItSrvcCnfgItmTypManagerPermissionSet`, `ItSrvcCnfgItmTypReadPermissionSet`) can be assigned to users.

---

## Permission Set Assignment Pattern

Each feature phase lists its permission set groups in the spec (`<permissions feature=…>`): Incident (IncidentManagerPSG, IncidentFulfillerPSG, MajorIncidentManagerPSG), Problem (ProblemManagerPSG, ProblemFulfillerPSG), Change (ChangeRequestManagerPSG, ChangeRequestFulfillerPSG), Release (ReleaseManagerPSG, ReleaseGroupPSG), Unified Catalog 4c (3 UC PSGs). They are assigned to the connected user with `settings/apply_permissions.py <ORG> plan|deploy --confirm|verify --features <ids>` — only for selected phases; absent PSGs skipped; rejections reported. No additional PSGs (e.g. ItsmPortalUserPSG, EmployeeHub*, SetupWithAgentforceUserPsg) are audited or assigned.

**Other permissions are handled in their phases:** prompt template permission sets (3a — permissions script `--features platform`, RC-91), Access Agents (3b/3c), BRE licences + permission sets (6b — permissions script, licences first), Knowledge User (7b fix with approval), Data Cloud GenieAdmin (9b — permissions script `--features datacloud`) and "Data Cloud User Enhanced Security" (9b — manual, after provisioning; RC-91), CMDB permission sets (checked in 11a).

> **PSG auto-assignment:** When a PSG is assigned, Salesforce automatically assigns all its contained Permission Sets and their required Permission Set Licenses. See Operational Learning #15.

**Known user license incompatibilities (informational, not errors):**

* `UnifiedCatalogCommunityUserPsl` — may fail for System Administrator users depending on licensing — treat failure as informational (RC-27)

---

## Deployment Helper Pattern

All settings deployments use the `--metadata-dir` approach:

1. Create temp directory with:

   ```
   /tmp/deploy-<name>/
   ├── settings/
   │   └── <SettingName>.settings    (the XML body)
   └── package.xml                   (references the settings member)
   ```

2. Package.xml template:

   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <Package xmlns="http://soap.sforce.com/2006/04/metadata">
       <types>
           <members>SETTING_MEMBER_NAME</members>
           <name>Settings</name>
       </types>
       <version>67.0</version>
   </Package>
   ```

3. **Always use `--async`** to submit the deploy, then poll with `deploy report`:

   * Submit: `sf project deploy start --metadata-dir <dir> --target-org <ORG> --async`
   * Poll: `sf project deploy report --job-id <id> --target-org <ORG>`
   * Check for `"status": "Succeeded"` or `"status": "Failed"` in JSON response

4. **Queue contention handling:**

   * Salesforce processes one deploy at a time per org
   * If your own deploy sits in `Pending` status for >2 minutes, cancel it (`sf project deploy cancel --job-id <id>`) and resubmit — check `DeployRequest.CreatedBy` first; never cancel a deploy created by Automated Process (RC-14)
   * **Batch multiple settings** into a single deploy where possible (the settings script combines selected features that share a settings file)
   * Allow 15-30 seconds between polls

5. **Multiple settings in one deploy:** Add multiple `<members>` entries to the same package.xml and include all settings files in the `settings/` directory.

---

## Execution Order & Dependencies

```
Pre-flight audit   read-only, every run → skip map → user selects phases
Phase 0            IT Service Enablement GATE (must be ON before any other phase)
Step 0             Sharing Settings (Level 1 programmatic, Level 2 fallback)
1a–1e              IT Service Core: 1a Incident · 1b Problem (needs 1a) · 1c Change (needs 1a) · 1d Release (needs 1c) · 1e Notification Service (mandatory; needs 1a)
3a–3e              Agentforce: 3a Platform · 3b Fulfiller (needs 3a + 1a) · 3c Employee Assistant (needs 3a) · 3d Proactive (needs 3b) · 3e optional (needs 3a)
4a–4c              Unified Catalog: 4a Context Service · 4b Apex templates (needs 4a) · 4c permissions (needs 4a)
5a–5c              SLA Management (5c optional)
6a–6c              Assignment Rules: 6a = 4a · 6b BRE permissions · 6c Decision Table Access
7a–7b              Knowledge (no Incident prerequisite; AI Knowledge creation in 1a needs 7a)
8a–8c              Self-service portal
9a–9d              Data Cloud — LAST programmatic deploy; never cancel the Automated Process install (9c optional)
10a–10c            Embedded chat on the portal (10c manual)
11a–11c            CMDB & Service Graph
```

The settings script deploys its files in spec order (Knowledge first, … CustomerDataPlatform last) and combines selected features that share a file into one deploy; prerequisites are enforced on what actually turned ON (see "Script rules" under IT Service Core).

---

## Error Handling

* **Already enabled:** Always check status before deploying — skip if already complete
* **Settings changes:** always via `settings/apply_settings.py <ORG> plan` → user approval → `deploy --confirm` → `verify` (RC-52/55).
* **Provisioning delays:** Data Cloud (20-30 min) and Agentforce (up to 20 min) require polling
* **Manual steps:** CMDB and BRE Decision Table Access cannot be automated — flag for user action
* **Missing licenses:** If Permission Sets/PSGs don't exist, the org may lack required licenses — stop and inform user
* **Deploy queue stuck:** If your own deploy stays in `Pending` for >2 minutes, cancel and resubmit — check `DeployRequest.CreatedBy` first; never cancel an Automated Process deploy (RC-14). Batch multiple settings into single deploys to reduce queue contention
* **Settings reads:** use Metadata API retrieve via the settings script; do not use SOAP readMetadata or hand-cleaned tokens.
* **User license incompatibilities:** `UnifiedCatalogCommunityUserPsl` may fail for System Administrator users depending on licensing — treat failure as informational (RC-27)

---

## Appendix — Proposed changes (pending approval)

> Not applied to the body of this recipe. Copied verbatim from the run's recipe-changes log. Every item listed here is still **proposed** and needs user approval before it is applied; approved, rejected and superseded changes are recorded in CHANGELOG.md.

#### RC-4 API name for Product Item Additional Transaction
- **Type:** add
- **Current text:** mapping `| Product Item Additional Transaction | n/a — verify in org |`; object absent from both queries.
- **New text (proposed):** mapping `ProductItemTransaction (unverified — absent in reference org)`; add `'ProductItemTransaction'` to Phase 1 audit + Step 0 verification queries.
- **Source:** Atlas inference — API name NOT verified (object absent on this org); flagged by Echo
- **Status:** proposed (unverified)

#### RC-41 Add Contact/Order (Account children) to Phase 1 audit + Step 0 verification queries as informational
- **Type:** add · **Source:** RC-39 · **Status:** proposed
