# AITS Org Setup Recipe

Automated setup of an AITS (Agentforce IT Services) org when a Salesforce org is connected via MeshMesh. Covers programmatic phases (Phases 1–9, 12) and browser/manual steps (Steps 0–3c, 6–15) for: permission audit, Data Cloud, Incident/Problem/Change/Release Management, Knowledge, Unified Catalog, Assignment Rules, Agentforce agent creation/activation, Experience Cloud site, Data Library, Enhanced Chat, Embedded Messaging, and SLA Management.

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

* If **yes**: Run Phase 2 (Data Cloud) **last** — after all other programmatic phases (3–9, 12) are complete. The Data Cloud settings deploy triggers a background `InstalledPackage` deploy by "Automated Process" that installs the `ssot` (Salesforce Standard Data Model) package. This takes \~10–30 minutes and **cannot be cancelled or re-triggered from the UI without the run failing and then retriggering provision**. By deploying Data Cloud last, there is no risk of it being accidentally cancelled when clearing a stuck deploy queue. Steps 11 and 12 (Data Library) depend on Data Cloud being fully provisioned.
* If **no**: Skip Phase 2 entirely. Also skip Step 11 (Create Data Library) and Step 12 (Connect Data Library to Agents) — these require Data Cloud.

### 2. Feature Selection

**Ask the user:** "Which features do you want to enable?" Present the following as a checklist — if the user opts out of any, skip the corresponding phases/steps:

| Feature | Phases/Steps | |---|---| | Incident Management | Phase 3, Step 1 (Assignment Rules) | | Knowledge | Phase 4 | | Problem Management | Phase 5 | | Change Management | Phase 6 | | Release Management | Phase 7 | | Unified Catalog | Phase 8 | | Agentforce Agents (IT Employee + Fulfiller) | Phase 12, Steps 6–9 | | Enhanced Chat for IT Service Employee | Step 2, Step 13 | | Self Service Portal (Experience Cloud Site) | Step 10 | | Data Library (requires Data Cloud) | Steps 11–12 | | Embedded Messaging Setup | Step 14 (manual) | | SLA Management for IT Service | Step 15 |

### 3. Permission Assignment Scope

**Inform the user:** "All permission sets and licenses will only be assigned to the currently connected user. Other users will need to be assigned separately after setup."

This applies to:

* All Permission Sets and Permission Set Groups from Phases 3–12
* The custom "Access Agents" Permission Set (Step 9)
* Queue membership (Step 13)

### 4. Strict Scope — Only Do What the Recipe Says

> **This rule applies to EVERY phase and step. No exceptions.**

* **ONLY perform actions explicitly described in a step's "Interaction flow" or "Deploy" section.** If the recipe does not instruct you to click a toggle, button, or link — do not click it.
* **DO NOT enable, toggle, or click anything** just because it appears unchecked, incomplete, or available on a page. Many Salesforce setup pages show multiple features, toggles, and sections. Ignore everything not called out in the recipe.
* **"All features" in the user's feature selection** refers ONLY to the features listed in the recipe's Feature Selection checklist (Section 2 above). It does NOT mean "enable every toggle visible in the Salesforce UI."
* **If you encounter an unchecked toggle or button** that is NOT in the recipe's instructions for the current step, leave it alone. Do not infer that it is a prerequisite or dependency unless the recipe explicitly says so.
* **If you are unsure** whether something should be enabled, STOP and ask the user before proceeding.

---

## Recipe Summary

**Programmatic Phases (Phases 1, 3–9, 12, then 2):** Automated via metadata deploy and Salesforce API. These enable org-level features, deploy settings, and assign permissions. **Phase 2 (Data Cloud) MUST be deployed LAST** — it triggers a background package install that occupies the deploy queue for \~10-30 min and cannot be cancelled. (Phases 10–11 were removed from the recipe — Slack and Microsoft Teams integrations are not covered.)

**Browser/Manual Steps (Steps 0–3c, 6–15):** Configuration that requires browser UI or manual action. Some are fully automated via browser, others require user input. (Steps 4–5 were removed from the recipe — Slack and Microsoft Teams channel setup are not covered.)

| Phase/Step | Method | Description | |---|---|---| | Phase 1 | Programmatic | Permission Set audit (read-only) | | Phase 3 | Programmatic | Incident + Problem + Change Management settings (combined deploy recommended) | | Phase 4 | Programmatic | Knowledge settings (check-first — often already enabled) | | Phase 5 | Programmatic | Problem Management settings (skip if combined in Phase 3) | | Phase 6 | Programmatic | Change Management settings (skip if combined in Phase 3) | | Phase 7 | Programmatic | Release Management settings (batch with Phase 8 recommended) | | Phase 8 | Programmatic | Unified Catalog settings (batch with Phase 7 recommended) | | Phase 9 | Programmatic | Assignment Rules (Context Service + BRE) | | Phase 12 | Programmatic | Agentforce enablement + PS assignment | | **Phase 2** | **Programmatic (LAST)** | **Data Cloud enablement — MUST be last programmatic deploy (triggers \~10-30 min background install by Automated Process that cannot be cancelled)** | | Step 0 | Browser | Configure Sharing Settings (OWD) | | Step 1 | Browser | Assignment Rules for IT Service | | Step 2 | Browser | Enhanced Chat for IT Service Employee | | Step 3 | Browser | CMDB and Service Graph Provisioning | | Step 3c | Programmatic + Browser | Verify Enhanced Chat Messaging Channel | | Step 6 | Programmatic (preferred) / Browser | Verify Agentforce IT Service Agent Templates | | Step 7 | Browser | Create Missing Agents via Wizard | | Step 8 | Programmatic | Activate Agents | | Step 9 | Programmatic | Create & Assign "Access Agents" Permission Set | | Step 10 | Programmatic | Create Experience Cloud Site (Agentic Center) | | Step 11 | Browser | Create Data Library (requires Data Cloud) | | Step 12 | Browser | Connect Data Library to Agents (requires Data Cloud) | | Step 13 | Programmatic | Verify Enhanced Chat Config (Queue/Routing/Flow) | | Step 14 | Manual | Embedded Messaging Setup (help article) | | Step 15 | Browser | SLA Management for IT Service |

---

## Operational Learnings (from live runs)

> These notes capture critical lessons from real executions. Read before running.

 1. **IncidentMgmtSettings is a shared object** — Phases 3, 5, 6 all write to it. Every deploy must include ALL 35+ boolean flags or unset flags revert to `false`. Always read-then-merge the full flag set before deploying.
 2. **ReleaseMgmtSettings is NOT queryable via Tooling API** — it requires SOAP Metadata API `readMetadata`. However, the access token from `sf org display` may be redacted or contain ANSI escape chars (Unicode 0x1b) that break SOAP XML. **Workaround:** Deploy `enableITSMReleaseMgmt=true` directly without reading first (safe — single flag) or use Python with `re.sub(r'[^\x20-\x7E]', '', token)` to strip non-printable chars.
 3. **Deploy queue contention** — consecutive deploys can get stuck in `Pending` for 2+ minutes. Always use `--async` + poll with `deploy report`. If stuck >2 min, cancel and resubmit. Batch multiple settings into a single deploy where possible.
 4. **Batch permission assignments** — assigning PS/PSGs one-by-one across phases is slow. Collect all assignments and run them in a single batch at the end.
 5. **User license incompatibilities are expected** — `UnifiedCatalogCommunityUserPsl` fails for System Administrator users (requires Community license). Log these as informational, not errors.
 6. **Combine ServiceItsmIntelligenceUdd deploys** — IT Fulfiller Agent + 14 Proactive Assistant flags + `enableSvcCtlgApexTemplate` can all go into one deploy to reduce queue contention.
 7. **Deploy `enableEinsteinGPTDeployPromptTemplatesAsActive`** with Phase 12 (Agentforce), not Phase 4 (Knowledge) — it's needed for agent prompt templates.
 8. **API version 67.0 required for ServiceItsmIntelligenceUdd** — Deploying with API v63.0 fails with "Not available for deploy for this API version". All AITS settings packages should use `<version>67.0</version>` in package.xml.
 9. **⚠️ NEVER cancel "Automated Process" deploys** — When Data Cloud is enabled, Salesforce triggers a background deploy by "Automated Process" to install the `ssot` (Salesforce Standard Data Model) `InstalledPackage`. This deploy takes \~10–30 minutes and **there is no UI or API to re-trigger it if cancelled**. Cancelling it will leave Data Cloud permanently stuck at "In Progress" on the Salesforce Foundations page. If you see an "Automated Process" deploy in the queue, **wait for it to finish** — do NOT cancel it even if it appears to block your deploys. If you have non-Automated-Process deploys stuck in `Pending`, wait for the Automated Process deploy to complete first. To avoid this conflict entirely, **deploy Data Cloud (Phase 2) as the LAST programmatic phase** so the background install runs after all other deploys are done.
10. **Connection alias may change between sessions** — The Salesforce org connection alias can change between sessions (e.g. `org-o2wdej` → `org-rrvydk`). Always read the active connection alias from the current task context rather than hardcoding it from a previous session.
11. **Data Cloud provisioning is NOT visible on Deploy Status page** — The `CustomerDataPlatform.settings` deploy succeeds quickly, but actual Data Cloud provisioning is a background process (\~20-30 min) that does NOT appear as a metadata deploy on the Deploy Status page. Do not look for it there — it runs separately. Steps that depend on Data Cloud (e.g., Data Library) will show "Turn On Data Cloud" until provisioning completes.
12. **Deploy tracking log is essential** — Maintain a running log of every deploy with: Deploy ID, Phase/Step, Settings included, and Status. This enables quick recovery when deploys get stuck or are canceled — you know exactly what needs to be rerun. Format: `| Deploy ID | Phase | Settings | Status | Notes |`
13. **FlowDefinitionView doesn't find auto-provisioned routing flows** — The `RouteMsgsItEmpAgent` flow (auto-created by Enhanced Chat setup) exists in the Tooling API `Flow` object but does NOT appear in `FlowDefinitionView`. For Step 13 verification, use the direct Tooling API REST endpoint: `GET /services/data/v67.0/tooling/query?q=SELECT+Id,Definition.DeveloperName,MasterLabel,Status+FROM+Flow+WHERE+Definition.DeveloperName='RouteMsgsItEmpAgent'`
14. **Strict scope — only do what the recipe says** — Browser steps often show pages with multiple toggles, buttons, and features. ONLY interact with the specific UI elements described in each step's Interaction Flow. Do not enable, click, or toggle anything else, even if it appears unchecked or incomplete. If the recipe doesn't say to click it, don't click it. "All features" in the user's feature selection refers to the recipe's feature checklist, not every toggle visible in the Salesforce UI. When in doubt, ask the user.
15. **PSG auto-assignment eliminates redundant PS and PSL assignments** — When a Permission Set Group (PSG) is assigned to a user, Salesforce automatically assigns all contained Permission Sets AND their required Permission Set Licenses. This means you do NOT need to separately assign individual PSs or PSLs that are bundled inside a PSG. Only 6 standalone PSs (not in any PSG) require explicit assignment: `GenieAdmin`, `GenieUserEnhancedSecurity`, `BRERuntime`, `BREDesigner`, `EinsteinGPTPromptTemplateUser`, `EinsteinGPTPromptTemplateManager`. The `ContextServiceRuntimePsl` and `ContextServiceAdminPsl` PSs are bundled inside the Unified Catalog PSGs (`UnifiedCatalogAdminPsl`, `UnifiedCatalogAgentPsl`) and do NOT need separate assignment — assigning the PSGs in Phase 8 covers them automatically.
16. **Knowledge settings — check before deploying** — `Knowledge.settings` XML has a complex nested structure (`suggestedArticles` with `Case`/`WorkOrder` sub-elements) that has caused multiple deploy failures. Before attempting to deploy, **always query existing settings first** via `SELECT Metadata FROM KnowledgeSettings LIMIT 1`. If `enableKnowledge` and `enableLightningKnowledge` are already `true`, **skip the Knowledge deploy entirely**. On orgs with ITSM licenses, Knowledge is often already fully configured. This avoids deploy failures from XML structural issues and saves \~5 minutes of retry time.
17. **Use `sf api request rest` for Connect API calls, not `curl`** — The `sf org display` command returns redacted access tokens (masked with `****`), and `sf org auth show-access-token` may include ANSI escape characters. Both break `curl`-based API calls. Instead, use `sf api request rest` which handles authentication automatically: `sf api request rest '/services/data/v67.0/connect/communities' --method get --target-org <ORG>`. This eliminates all token-handling issues and works reliably for Connect API endpoints (templates, site creation, etc.).
18. **SLA predefined policies may pre-exist** — Before clicking "Create Predefined Policies" in Step 15, query whether SLA policies already exist: `SELECT Id, Name, SobjectType FROM SlaProcess WHERE SobjectType IN ('Incident','Problem','ChangeRequest')`. If policies exist, the "Create" action may fail or create duplicates. Show existing policies to the user and ask whether to proceed.
19. **Additional ITSM agents may appear** — The broad discovery query in Step 8 (`WHERE DeveloperName LIKE '%IT%' OR DeveloperName LIKE '%Fulfiller%' OR DeveloperName LIKE '%Employee%'`) may return agents beyond `ItEmployeeAssistant` and `IT_Service_Fulfiller` (e.g. `IT_Service_Employee`). These are auto-provisioned by other features and do not need to be activated or added to the Access Agents permission set. Focus on the two primary agents listed in the recipe.
20. **Copilot activation limitation** — The `sf agent activate` command only works when run from a valid SFDX project directory (requires `sfdx-project.json`). If you get `InvalidProjectWorkspaceError`, create a minimal `sfdx-project.json` with `{"packageDirectories":[{"path":"force-app","default":true}],"sourceApiVersion":"67.0"}` before running agent activation commands.
21. **Enhanced Chat toggle — click the container, not the switch** — The "Set Up Enhanced Chat for IT Service Employee" toggle element has shadow DOM click interception. Direct clicks on the toggle switch (`<input type="checkbox">`) are absorbed. To reliably toggle it, click the **parent container element** (typically the `<div>` wrapper 1-2 refs above the switch in the accessibility snapshot). This applies to several Salesforce Go toggle elements that use Lightning `lightning-primitive-input-toggle` components.
22. **⚠️ Data Cloud MUST be the last programmatic deploy** — The Data Cloud settings deploy (`CustomerDataPlatform.settings`) triggers a background `InstalledPackage` deploy by "Automated Process" that installs the `ssot` package (\~10–30 min). This background deploy occupies the deploy queue. If other deploys are submitted while it runs, they queue behind it — and if an operator cancels the Automated Process deploy to unblock the queue, Data Cloud provisioning is permanently broken (no re-trigger mechanism exists). **Execution order:** Run Phases 3–9, 12 first → then deploy Phase 2 (Data Cloud) last → wait for background provisioning to complete → then proceed with Steps 11–12 (Data Library).

---

## Phase 1: Permission Set Check (read-only audit)

**Purpose:** Verify all required Permission Sets and Permission Set Groups exist in the org before proceeding.

**How to check:**

1. Query all required Permission Sets:

   ```
   SELECT Name FROM PermissionSet WHERE IsOwnedByProfile = false AND Name IN (
     'IncidentManager','IncidentFulfiller','MajorIncidentManager',
     'ItSrvcIncChgAssocPermSet','ItSrvcIncProbAssocPermSet','ItSrvcIncRelAssocPermSet',
     'ItSrvcMajIncProposPermSet','ItSrvcIncAssocsRslvPermSet','ItSrvcRelAssocsViewPermSet',
     'ItSrvcChgAssocsRslvPermSet','ProblemManagerPermSet','ProblemFulfillerPermSet',
     'ItSrvcProbRiskAcptPermSet','ItSrvcProbRopenPermSet','ItSrvcProbChgAssocPermSet',
     'ItSrvcProbRelAssocPermSet','ItSrvcProbAssocsRslvPermSet','ItSrvcProbDeletePermSet',
     'ChangeRequestManagerPermSet','ChangeRequestFulfillerPermSet',
     'ItSrvcChgRelAssocPermSet','ItSrvcChgDeletePermSet',
     'ReleaseManagerPermSet','ReleaseGroupPermSet','ItSrvcRelDeletePermSet',
     'ItsmPortalCommunityUser','EinsteinGPTPromptTemplateUser','EinsteinGPTPromptTemplateManager',
     'ItSrvcCnfgItmOwnerPermissionSet','ItSrvcCnfgItmReadPermissionSet',
     'ItSrvcCnfgItmTypManagerPermissionSet','ItSrvcCnfgItmTypReadPermissionSet',
     'ItSrvcRelRecReadPermissionSet'
   )
   ```

2. Query all required Permission Set Groups:

   ```
   SELECT DeveloperName FROM PermissionSetGroup WHERE DeveloperName IN (
     'IncidentManagerPSG','IncidentFulfillerPSG','MajorIncidentManagerPSG',
     'ProblemManagerPSG','ProblemFulfillerPSG',
     'ChangeRequestManagerPSG','ChangeRequestFulfillerPSG',
     'ReleaseManagerPSG','ReleaseGroupPSG',
     'UnifiedCatalogAdminPsl','UnifiedCatalogAgentPsl','UnifiedCatalogCommunityUserPsl'
   )
   ```

3. Report missing items. If any are missing, the org may not have the correct licenses.

**Sharing Settings Audit:** Query OWD sharing models for every object in the Step 0 target table and compare Internal and External access against it:

```
SELECT QualifiedApiName, InternalSharingModel, ExternalSharingModel
FROM EntityDefinition
WHERE QualifiedApiName IN (
  'Account','Contract','Asset','ProductCatalog','FulfillmentOrder','Incident',
  'InventoryReservation','Knowledge__kav','Location','Product2',
  'ProductAttributeDefinition','ProductCategoryDisqual','ProductCategoryQualification',
  'ProductClassification','ProductClassificationAttr','ProductComponentGroup',
  'ProductComponentGrpOverride','ProductConfigurationFlow','ProductConfigFlowParameter',
  'ProductItem','ProductRelComponentOverride','ProductTransfer',
  'SvcCatalogRequest','ServiceRequest','Shipment',
  'BroadcastTopic','BroadcastCommunication','BroadcastCommAudience')
ORDER BY QualifiedApiName
```

Flag every object whose Internal or External value differs from the Step 0 target table (`ReadWrite` = Public Read/Write, `Read` = Public Read Only, `Private` = Private, `ControlledByParent` = Controlled by Parent) for update in Step 0. Objects missing from the result do not exist in the org — record them as skipped.

---

## Phase 2: Data Cloud (⚠️ DEPLOY LAST — after all other programmatic phases)

**Purpose:** Enable Customer Data Platform in the org.

> **⚠️ CRITICAL: Deploy this phase LAST** — after Phases 3–9, 12 are complete. The Data Cloud settings deploy triggers a background `InstalledPackage` deploy by "Automated Process" that installs the `ssot` (Salesforce Standard Data Model) package. This background deploy takes \~10–30 minutes, occupies the deploy queue, and **cannot be cancelled or re-triggered**. If cancelled, Data Cloud provisioning is permanently stuck. By deploying last, there are no subsequent deploys that could conflict with it.

**Check (Tooling API):**

```
SELECT IsCustomerDataPlatformEnabled FROM CustomerDataPlatformSettings
```

**Deploy if not enabled:**

* Settings type: `CustomerDataPlatform`
* Root element: `CustomerDataPlatformSettings`
* Flag: `enableCustomerDataPlatform = true`

Settings XML:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomerDataPlatformSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableCustomerDataPlatform>true</enableCustomerDataPlatform>
</CustomerDataPlatformSettings>
```

Package.xml member: `CustomerDataPlatform` (type: `Settings`)

Deploy via `--metadata-dir` approach. Provisioning takes **10–30 minutes** in background. After deploying, **do NOT cancel any deploy in the queue** — the "Automated Process" `InstalledPackage` deploy is the Data Cloud `ssot` package being installed. Wait for it to complete before proceeding with Steps 11–12 (Data Library).

**Permission Sets to assign:**

* `GenieAdmin` (Data Cloud Admin)
* `GenieUserEnhancedSecurity` (Data Cloud User Enhanced Security)

---

## Phase 3: Incident Management

**Purpose:** Enable ITSM Incident Management features.

> **⚡ Optimization — Combined Deploy:** Phases 3, 5, and 6 all write to `IncidentMgmtSettings`. Instead of deploying three separate times (which causes \~4-6 min of deploy queue overhead), **combine all three phases into a single deploy**. Read the current settings once, merge ALL flags for Incident + Problem + Change Management, and deploy once. See the combined flag list below.

**Check (Tooling API):**

```
SELECT Metadata FROM IncidentMgmtSettings LIMIT 1
```

Verify flags: `enableITSMIncidentMgmt`, `enableIncidentValidations`, `enableAutoClosureOfChildIncident`, `enableEmailToIncident`

**Deploy:**

1. Read current `IncidentMgmtSettings` from Tooling API (`SELECT Metadata FROM IncidentMgmtSettings LIMIT 1`)
2. **CRITICAL:** The response contains 35+ boolean flags. You must include ALL of them in the deploy XML, setting the required flags to `true` while preserving every other flag's current value. If you omit flags, they revert to `false`.
3. **Recommended: Set ALL flags for Phases 3+5+6 in one deploy** — in addition to the Phase 3 flags, also set: `enableITSMProblemMgmt`, `enableProblemValidations` (Phase 5), `enableITSMChangeMgmt`, `enableRiskAssessment` (Phase 6). This eliminates two additional deploys and saves \~4-6 minutes.
4. Write merged XML as `IncidentMgmt.settings`
5. Package.xml member: `IncidentMgmt` (type: `Settings`)
6. Deploy via `--metadata-dir` with `--async` flag, then poll with `deploy report`

**Full IncidentMgmtSettings flags reference** (all must be included in every deploy):

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

**PSGs to assign:**

* `IncidentManagerPSG`
* `IncidentFulfillerPSG`
* `MajorIncidentManagerPSG`

---

## Phase 4: Knowledge

**Purpose:** Enable Knowledge and Lightning Knowledge.

**Check (Tooling API):**

```
SELECT Metadata FROM KnowledgeSettings LIMIT 1
```

Verify: `enableKnowledge = true`, `enableLightningKnowledge = true`

> **⚡ Check-first pattern (see Operational Learning #16):** On ITSM-licensed orgs, Knowledge is often **already fully configured**. If both `enableKnowledge` and `enableLightningKnowledge` are already `true` in the query results, **skip the Knowledge deploy entirely**. The `Knowledge.settings` XML has a complex nested structure (`suggestedArticles` with `Case`/`WorkOrder` sub-elements) that has caused multiple deploy failures. Avoiding an unnecessary deploy saves \~5 minutes and eliminates a common failure point.

**Deploy (only if not already enabled):** Deploy the full Knowledge.settings file with these key settings:

* enableKnowledge: true
* enableLightningKnowledge: true
* enableCreateEditOnArticlesTab: true
* enableExternalMediaContent: true
* enableKbStandardSharing: true
* enableKnowledgeArticleTextHighlights: true
* showArticleSummariesCustomerPortal: true
* showArticleSummariesInternalApp: true
* showValidationStatusField: true
* votingEnabled: true
* suggestedArticles for Case/WorkOrder: Subject field

⚠️ **Known deploy issue:** The `suggestedArticles` XML element requires precise nesting (`<suggestedArticles><sObjectType>Case</sObjectType><suggestedArticles><fieldName>Subject</fieldName></suggestedArticles></suggestedArticles>`). Incorrect structure causes deploy failures. If the deploy fails on `suggestedArticles`, try deploying without it — the core Knowledge enablement flags are more important.

Settings file: `Knowledge.settings` Package.xml member: `Knowledge` (type: `Settings`)

**Optional Feature — Einstein Knowledge Creation:** Requires deploying two additional settings:

* `EinsteinGpt`: `enableEinsteinGptPlatform = true`, `enableEinsteinGPTDeployPromptTemplatesAsActive = true`
* `IncidentMgmt`: `enableAiKnowledgeCreation = true`

**Dependencies:** Incident Management must be enabled first.

---

## Phase 5: Problem Management

**Purpose:** Enable ITSM Problem Management.

> **⚡ If combined deploy was used in Phase 3:** These flags were already deployed. Verify they are set and skip the deploy. Only run a separate deploy here if Phase 3 did NOT include the Problem Management flags.

**Check (Tooling API):**

```
SELECT Metadata FROM IncidentMgmtSettings LIMIT 1
```

Verify: `enableITSMProblemMgmt = true`, `enableProblemValidations = true`

**Deploy (only if not already included in Phase 3 combined deploy):** Same merge pattern as Incident Management — read current IncidentMgmtSettings, merge Problem flags, write `IncidentMgmt.settings`, deploy.

**PSGs to assign:**

* `ProblemManagerPSG`
* `ProblemFulfillerPSG`

**Dependencies:** Incident Management must be enabled first.

---

## Phase 6: Change Management

**Purpose:** Enable ITSM Change Management.

> **⚡ If combined deploy was used in Phase 3:** These flags were already deployed. Verify they are set and skip the deploy. Only run a separate deploy here if Phase 3 did NOT include the Change Management flags.

**Check (Tooling API):**

```
SELECT Metadata FROM IncidentMgmtSettings LIMIT 1
```

Verify: `enableITSMChangeMgmt = true`, `enableRiskAssessment = true`

**Deploy (only if not already included in Phase 3 combined deploy):** Same merge pattern — read current IncidentMgmtSettings, merge Change flags, deploy.

**Optional features:**

* `enableChgRqstCnflctDetection` (Change Request Conflict Detection)
* `enableChangeRequestValidations` (Change Request Validations)

**PSGs to assign:**

* `ChangeRequestManagerPSG`
* `ChangeRequestFulfillerPSG`

**Dependencies:** Incident Management must be enabled first.

---

## Phase 7: Release Management

**Purpose:** Enable ITSM Release Management.

> **⚡ Optimization — Batch with Phase 8:** Phase 7 (ReleaseMgmt) and Phase 8 (IndustriesContext + ServiceItsmIntelligenceUdd) can be combined into a single deploy package containing all three settings files. This eliminates one additional deploy cycle (\~2 min saved). Include `ReleaseMgmt.settings`, `IndustriesContext.settings`, and `ServiceItsmIntelligenceUdd.settings` in the same package.xml with three `<members>` entries.

**Check:** `ReleaseMgmtSettings` is NOT available via the Tooling API. It requires the SOAP Metadata API `readMetadata` call. However, the access token may contain ANSI escape characters that break SOAP XML.

**Recommended approach (direct deploy):** Since ReleaseMgmt has only one relevant flag, deploy directly without reading first:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ReleaseMgmtSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableITSMReleaseMgmt>true</enableITSMReleaseMgmt>
</ReleaseMgmtSettings>
```

**Deploy:**

* Root element: `ReleaseMgmtSettings`
* Settings file: `ReleaseMgmt.settings`
* Package.xml member: `ReleaseMgmt` (type: `Settings`)

**Alternative (SOAP read):** If you need to read first, use Python with token cleaning:

```python
import re
clean_token = re.sub(r'[^\x20-\x7E]', '', raw_token)  # strip ANSI/non-printable chars
```

**Optional features:**

* `enableReleaseValidations` (Release Validations)
* `enableNotifications` (Notification Service — under `ServiceCloudNotificationOrchestrator` settings)
  * Sub-channels: `enableEmailNotifications`, `enableInAppNotifications`, `enableSlackNotifications`, `enableTeamsNotifications`

**PSGs to assign:**

* `ReleaseManagerPSG`
* `ReleaseGroupPSG`

**Dependencies:** Change Management must be enabled first.

---

## Phase 8: Unified Catalog

**Purpose:** Enable Unified Catalog for Employee Service (Context Definitions + Service Catalog Apex Templates).

**Check (via Metadata API SOAP readMetadata):**

* `IndustriesContext` → `enableContextDefinitions`
* `ServiceItsmIntelligenceUdd` → `enableSvcCtlgApexTemplate`

**Deploy (up to 2 settings in one package):**

1. If Context Definitions needed:

```xml
<IndustriesContextSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableContextDefinitions>true</enableContextDefinitions>
</IndustriesContextSettings>
```

File: `IndustriesContext.settings`

2. If Service Catalog Apex Templates needed:

```xml
<ServiceItsmIntelligenceUddSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableSvcCtlgApexTemplate>true</enableSvcCtlgApexTemplate>
</ServiceItsmIntelligenceUddSettings>
```

File: `ServiceItsmIntelligenceUdd.settings`

Package.xml members: `IndustriesContext`, `ServiceItsmIntelligenceUdd` (type: `Settings`)

**PSGs to assign:**

* `UnifiedCatalogAdminPsl`
* `UnifiedCatalogAgentPsl`
* `UnifiedCatalogCommunityUserPsl`

**Dependencies:** Release Management must be enabled first.

---

## Phase 9: Assignment Rules (Context Service + BRE)

**Purpose:** Enable Context Service and Business Rules Engine for IT Service assignment rules.

**Check (via Metadata API SOAP readMetadata):**

```
IndustriesContext → enableContextDefinitions
```

**Deploy:**

```xml
<IndustriesContextSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableContextDefinitions>true</enableContextDefinitions>
</IndustriesContextSettings>
```

(May already be enabled by Unified Catalog phase — check first.)

**Permission Sets to assign:**

* `BRERuntime` (Business Rules Engine Runtime) — standalone, not in any PSG
* `BREDesigner` (Business Rules Engine Designer) — standalone, not in any PSG

**Permission Set Licenses required:**

* `BRERuntime`
* `BREDesigner`

Assign PSLs first via `PermissionSetLicenseAssign`, then Permission Sets via `PermissionSetAssignment`.

> **Note:** `ContextServiceRuntimePsl` and `ContextServiceAdminPsl` do NOT need separate assignment here — they are bundled inside the Unified Catalog PSGs (`UnifiedCatalogAdminPsl`, `UnifiedCatalogAgentPsl`) assigned in Phase 8. Their required PSLs are also auto-assigned when the PSGs are assigned. See Operational Learning #15.

**Manual step:** BRE Decision Table Access must be toggled manually in Setup.

---

## Phase 12: Agentforce

**Purpose:** Enable Agentforce Platform and Einstein Generative AI.

**Check (via Metadata API SOAP readMetadata):**

* `AgentPlatform` → `enableAgentPlatform`
* `EinsteinGpt` → `enableEinsteinGptPlatform`

**Deploy (3 settings in one package):**

AgentPlatform.settings:

```xml
<AgentPlatformSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableAgentPlatform>true</enableAgentPlatform>
</AgentPlatformSettings>
```

EinsteinGpt.settings:

```xml
<EinsteinGptSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableEinsteinGptPlatform>true</enableEinsteinGptPlatform>
    <enableEinsteinGPTDeployPromptTemplatesAsActive>true</enableEinsteinGPTDeployPromptTemplatesAsActive>
</EinsteinGptSettings>
```

EinsteinAI.settings:

```xml
<EinsteinAISettings xmlns="http://soap.sforce.com/2006/04/metadata">
</EinsteinAISettings>
```

Deploy with `--wait 20` (timeout 25 min). After deploy, poll up to 20 minutes for provisioning to complete.

**Sub-features (post-enablement — deploy as a single package):**

Deploy IT Fulfiller Agent + all 14 Proactive Assistant flags + `enableSvcCtlgApexTemplate` in ONE `ServiceItsmIntelligenceUdd.settings` file to reduce deploy queue contention:

```xml
<ServiceItsmIntelligenceUddSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableSvcCtlgApexTemplate>true</enableSvcCtlgApexTemplate>
    <enableItSrvcsFulfillerAgent>true</enableItSrvcsFulfillerAgent>
    <enableProactvAsstforItSrvcs>true</enableProactvAsstforItSrvcs>
    <enableCheckIncAttrProactvAsst>true</enableCheckIncAttrProactvAsst>
    <enableIncAsgntProactvAsst>true</enableIncAsgntProactvAsst>
    <enableIncPrpsRsolSumProactvAsst>true</enableIncPrpsRsolSumProactvAsst>
    <enableIncRootCseSumProactvAsst>true</enableIncRootCseSumProactvAsst>
    <enableIncSmlrRecProactvAsst>true</enableIncSmlrRecProactvAsst>
    <enableIncSrvcPlanProactvAsst>true</enableIncSrvcPlanProactvAsst>
    <enableIncSummaryProactvAsst>true</enableIncSummaryProactvAsst>
    <enableProactivAsstForProbm>true</enableProactivAsstForProbm>
    <enableCheckProbmForAttr>true</enableCheckProbmForAttr>
    <enableCreaProbmForRootCseSum>true</enableCreaProbmForRootCseSum>
    <enableSumForProbm>true</enableSumForProbm>
    <enableAsocSmlrProbToProb>true</enableAsocSmlrProbToProb>
    <enableProposSumForProbm>true</enableProposSumForProbm>
</ServiceItsmIntelligenceUddSettings>
```

**AI Trust PII Masking (requires Data Cloud):** Check: `SELECT Metadata FROM EinsteinAISettings LIMIT 1` → `enableTrustPIIMasking` Flag for manual enablement if Data Cloud is not yet provisioned.

---

## Permission Set Assignment Pattern

**Recommended approach:** Batch all assignments into a single script at the end of all deployments, rather than assigning per-phase. This is faster and avoids partial assignment states.

**Step 1: Get the connected user's ID**

```
SELECT Id FROM User WHERE Username = '<connected-username>'
```

**Step 2: Batch-query all PS, PSG, and PSL IDs** Query all required IDs in bulk using `IN` clauses. Only standalone PSs (not bundled in any PSG) and their PSLs need explicit assignment — PSGs auto-assign their contained PSs and PSLs.

```
SELECT Id, Name FROM PermissionSet WHERE Name IN ('GenieAdmin','GenieUserEnhancedSecurity','BRERuntime','BREDesigner','EinsteinGPTPromptTemplateUser','EinsteinGPTPromptTemplateManager') AND IsOwnedByProfile = false
SELECT Id, DeveloperName FROM PermissionSetGroup WHERE DeveloperName IN ('IncidentManagerPSG','IncidentFulfillerPSG','MajorIncidentManagerPSG','ProblemManagerPSG','ProblemFulfillerPSG','ChangeRequestManagerPSG','ChangeRequestFulfillerPSG','ReleaseManagerPSG','ReleaseGroupPSG','UnifiedCatalogAdminPsl','UnifiedCatalogAgentPsl','UnifiedCatalogCommunityUserPsl')
SELECT Id, DeveloperName FROM PermissionSetLicense WHERE DeveloperName IN ('BRERuntime','BREDesigner')
```

**Step 3: Check which are already assigned**

```
SELECT PermissionSetId FROM PermissionSetAssignment WHERE AssigneeId = '<USER_ID>' AND PermissionSetId IN (...)
SELECT PermissionSetGroupId FROM PermissionSetAssignment WHERE AssigneeId = '<USER_ID>' AND PermissionSetGroupId IN (...)
SELECT PermissionSetLicenseId FROM PermissionSetLicenseAssign WHERE AssigneeId = '<USER_ID>' AND PermissionSetLicenseId IN (...)
```

**Step 4: Assign PSLs first, then PSGs, then standalone PSs**

* Assign PSLs first: Only `BRERuntime` and `BREDesigner` PSLs need explicit assignment (all other PSLs are auto-assigned by PSGs)
* Assign PSGs next: 12 PSGs covering Incident, Problem, Change, Release, and Unified Catalog (these auto-assign \~40+ PSs and PSLs)
* Assign standalone PSs last: Only 6 PSs not in any PSG: `GenieAdmin`, `GenieUserEnhancedSecurity`, `BRERuntime`, `BREDesigner`, `EinsteinGPTPromptTemplateUser`, `EinsteinGPTPromptTemplateManager`
* For PSGs, use `PermissionSetGroupId` instead of `PermissionSetId`

**Complete assignment list across all phases:**

> **PSG auto-assignment:** When a PSG is assigned, Salesforce automatically assigns all its contained Permission Sets and their required Permission Set Licenses. You do NOT need to separately assign individual PSs or PSLs that are bundled inside a PSG. Only standalone PSs (not in any PSG) need explicit assignment. See Operational Learning #15.

| Type | Name | Phase | Notes | |------|------|-------|-------| | PSG | IncidentManagerPSG | 3 | Auto-assigns: IncidentManager, ItSrvcIncChgAssocPermSet, ItSrvcIncProbAssocPermSet, ItSrvcIncRelAssocPermSet, ItSrvcMajIncProposPermSet, ItSrvcIncAssocsRslvPermSet + their PSLs | | PSG | IncidentFulfillerPSG | 3 | Auto-assigns: IncidentFulfiller + related PSs and PSLs | | PSG | MajorIncidentManagerPSG | 3 | Auto-assigns: MajorIncidentManager + related PSs and PSLs | | PSG | ProblemManagerPSG | 5 | Auto-assigns: ProblemManagerPermSet, ItSrvcProbRiskAcptPermSet, ItSrvcProbChgAssocPermSet, etc. + PSLs | | PSG | ProblemFulfillerPSG | 5 | Auto-assigns: ProblemFulfillerPermSet + related PSs and PSLs | | PSG | ChangeRequestManagerPSG | 6 | Auto-assigns: ChangeRequestManagerPermSet, ItSrvcChgRelAssocPermSet, etc. + PSLs | | PSG | ChangeRequestFulfillerPSG | 6 | Auto-assigns: ChangeRequestFulfillerPermSet + related PSs and PSLs | | PSG | ReleaseManagerPSG | 7 | Auto-assigns: ReleaseManagerPermSet, ItSrvcRelDeletePermSet, etc. + PSLs | | PSG | ReleaseGroupPSG | 7 | Auto-assigns: ReleaseGroupPermSet + related PSs and PSLs | | PSG | UnifiedCatalogAdminPsl | 8 | Auto-assigns: ContextServiceAdminPsl, ContextServiceRuntimePsl + their PSLs | | PSG | UnifiedCatalogAgentPsl | 8 | Auto-assigns: ContextServiceRuntimePsl + its PSL | | PSG | UnifiedCatalogCommunityUserPsl | 8 | ⚠️ Requires Community license — will fail for admin users | | PS | GenieAdmin | 2 | Standalone — not in any PSG | | PS | GenieUserEnhancedSecurity | 2 | Standalone — not in any PSG | | PS | BRERuntime | 9 | Standalone — not in any PSG. Requires matching PSL | | PS | BREDesigner | 9 | Standalone — not in any PSG. Requires matching PSL | | PS | EinsteinGPTPromptTemplateUser | 12 | Standalone — not in any PSG | | PS | EinsteinGPTPromptTemplateManager | 12 | Standalone — not in any PSG | | PSL | BRERuntime | 9 | Assign before matching PS | | PSL | BREDesigner | 9 | Assign before matching PS |

**Known user license incompatibilities (informational, not errors):**

* `UnifiedCatalogCommunityUserPsl` — requires Community license, will fail for System Administrator users

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
   * If a deploy sits in `Pending` status for >2 minutes, cancel it (`sf project deploy cancel --job-id <id>`) and resubmit
   * **Batch multiple settings** into a single deploy where possible (e.g., Phase 8 combines IndustriesContext + ServiceItsmIntelligenceUdd)
   * Allow 15-30 seconds between polls

5. **Multiple settings in one deploy:** Add multiple `<members>` entries to the same package.xml and include all settings files in the `settings/` directory.

---

## Execution Order & Dependencies

```
Phase 1:  Permission Check + Sharing Settings Audit (no deps)
Phase 2:  Data Cloud (no deps, runs in parallel — 20-30 min provisioning)
Phase 3:  Incident + Problem + Change Management (COMBINED deploy — no deps)
Phase 4:  Knowledge (depends on Phase 3 — check-first, often skip)
Phase 5:  Problem Management (SKIP if combined in Phase 3)
Phase 6:  Change Management (SKIP if combined in Phase 3)
Phase 7+8: Release Mgmt + Unified Catalog (BATCH into one deploy — depends on Phase 3)
Phase 9:  Assignment Rules / Context Service (no deps)
Phase 12: Agentforce (no deps, but deploy EARLY — 20 min provisioning)
```

**Optimized execution order (recommended):**

1. **Phase 1** — Permission audit (fast, no deps)
2. **Phase 2** — Data Cloud (kick off immediately, 20-30 min background provisioning)
3. **Phase 12** — Agentforce (kick off early, up to 20 min provisioning) ← **moved earlier**
4. **Phase 3** — Combined Incident+Problem+Change deploy (single deploy, \~2 min)
5. **Phase 4** — Knowledge (check-first; often already enabled, skip deploy)
6. **Phase 7+8** — Release Mgmt + Unified Catalog (batched deploy, \~2 min)
7. **Phase 9** — Assignment Rules / Context Service
8. **Permission assignments** — batch all at the end
9. **Browser steps** — Steps 0, 1, 2, 3, 3c, 6-15 after all deploys complete

**Parallelization:**

* Phase 2 (Data Cloud) and Phase 12 (Agentforce) can run immediately and in parallel with everything — both have long provisioning times, so start early
* Phases 9 has no dependencies on ITSM phases
* Combined Phase 3 eliminates the 3→5 and 3→6 sequential dependencies
* Phase 7+8 batch depends on Phase 3 (Change Management required for Release Management)

---

## Error Handling

* **Already enabled:** Always check status before deploying — skip if already complete
* **Merge pattern:** For IncidentMgmtSettings, always read current metadata first, merge new flags, then deploy. **Include ALL 35+ flags** in every deploy or unset flags revert to `false`
* **Provisioning delays:** Data Cloud (20-30 min) and Agentforce (up to 20 min) require polling
* **Manual steps:** CMDB and BRE Decision Table Access cannot be automated — flag for user action
* **Missing licenses:** If Permission Sets/PSGs don't exist, the org may lack required licenses — stop and inform user
* **Deploy queue stuck:** If deploy stays in `Pending` for >2 minutes, cancel and resubmit. Batch multiple settings into single deploys to reduce queue contention
* **SOAP token issues:** Access tokens from `sf org display` may be redacted; tokens from `sf org auth show-access-token` may contain ANSI escape chars (0x1b). Use Python with `re.sub(r'[^\x20-\x7E]', '', token)` to clean tokens for SOAP calls, or skip SOAP reads for single-flag settings like ReleaseMgmt
* **User license incompatibilities:** `UnifiedCatalogCommunityUserPsl` will fail for System Administrator users — this is expected and should be logged as informational, not as errors

---

## Browser Only Steps

> These steps cannot be automated via API or metadata deploy. They must be performed in the Salesforce Setup UI (browser). Execute these after all programmatic phases are complete.

### Step 0: Configure Sharing Settings (Organization-Wide Defaults)

**Purpose:** Set the Organization-Wide Default (OWD) sharing settings for AITS-related objects so that records are accessible across the organization as needed.

**URL:** `/lightning/setup/SecuritySharing/home`

**Page verification:** The page title should show **"Sharing Settings"** with a heading **"Organization-Wide Sharing Defaults"** and an **"Edit"** button next to it.

**Important: Metadata deploy does NOT work for OWD on standard/managed objects.** Deploying `CustomObject` metadata with `sharingModel`/`externalSharingModel` tags may report success but does not actually change the OWD. This step MUST be done via the browser UI.

**Interaction flow:**

**Scope: ONLY perform the actions listed below. Do not interact with any other toggles, buttons, or sections on this page.**

1. Navigate to the URL above
2. Click the **"Edit"** button next to "Organization-Wide Sharing Defaults"
3. The page loads an edit form with two columns per object:
   * **Default Internal Access** (first dropdown, labeled `"ObjectName : Default Access"`)
   * **Default External Access** (second dropdown, unlabeled — immediately to the right)
4. Locate each object and set **both** Internal and External dropdowns as shown below
5. **Note:** External access cannot be more permissive than Internal access — set Internal first, then External

**Target Organization-Wide Defaults (set every row exactly as shown):**

| Object (UI Label) | Default Internal Access | Default External Access | Notes |
|---|---|---|---|
| Account and Contract | Public Read/Write | Public Read Only | Single row on the page (covers both Account and Contract) |
| Asset | Public Read/Write | Public Read Only | |
| Catalog | Public Read/Write | Public Read Only | |
| Fulfillment Order | Public Read/Write | Private | Skip if absent |
| Incident | Public Read Only | Public Read Only | |
| Inventory Reservation | Controlled by Parent | Private | Skip if absent |
| Knowledge | Public Read/Write | Public Read Only | Usually already correct — verify |
| Location | Public Read/Write | Public Read/Write | |
| Product | Public Read/Write | Public Read Only | |
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
| Broadcast Topic | Public Read Only | Public Read Only | |
| Broadcast Communication | Public Read Only | Public Read Only | |
| Broadcast Communication Audience | Public Read Only | Public Read Only | |

**Objects that may be absent (skip if not in the list):**

| Object (UI Label) | Notes |
|---|---|
| Fulfillment Order, Inventory Reservation, Product Item, Product Item Additional Transaction, Product Transfer, Shipment | Require Field Service / Order Management. Not present on orgs without those features — skip and note which were skipped in the run report. |
| Product Configuration Section | May not exist — skip if not in the dropdown list |

6. After setting all dropdowns, scroll to the top or bottom and click **"Save"**
7. If the save fails with validation errors, look for the error messages — they typically indicate objects where Internal = `Controlled by Parent` but External = `Private` (a pre-existing org issue). Fix those by setting External to `Controlled by Parent` to match Internal, then save again.

**Known pre-existing validation issues (may vary by org):** When saving, the page may flag errors on objects unrelated to AITS (e.g., Compliance Control Version, Compliance Policy Version, Regulation Version, Validation Procedure Version). These have `Controlled by Parent` internally but `Private` externally, which is invalid. Set their External access to `Controlled by Parent` to resolve.

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
  'Account','Contract','Asset','ProductCatalog','FulfillmentOrder','Incident',
  'InventoryReservation','Knowledge__kav','Location','Product2',
  'ProductAttributeDefinition','ProductCategoryDisqual','ProductCategoryQualification',
  'ProductClassification','ProductClassificationAttr','ProductComponentGroup',
  'ProductComponentGrpOverride','ProductConfigurationFlow','ProductConfigFlowParameter',
  'ProductItem','ProductRelComponentOverride','ProductTransfer',
  'SvcCatalogRequest','ServiceRequest','Shipment',
  'BroadcastTopic','BroadcastCommunication','BroadcastCommAudience'
)
ORDER BY QualifiedApiName
```

Compare each row to the target table above using these API values: Public Read/Write = `ReadWrite`, Public Read Only = `Read`, Private = `Private`, Controlled by Parent = `ControlledByParent`. A missing row means the object does not exist in the org (expected for the "skip if absent" objects). Product Item Additional Transaction is not in the query — verify it visually on the Sharing Settings page.

**UI-to-API name mapping:**

| UI Label | API Name |
|---|---|
| Account and Contract | Account, Contract |
| Asset | Asset |
| Catalog | ProductCatalog |
| Fulfillment Order | FulfillmentOrder (unverified — absent in reference org) |
| Incident | Incident |
| Inventory Reservation | InventoryReservation (unverified — absent in reference org) |
| Knowledge | Knowledge__kav |
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
| Broadcast Topic | BroadcastTopic |
| Broadcast Communication | BroadcastCommunication |
| Broadcast Communication Audience | BroadcastCommAudience |

**Note:** "Catalog" on the Sharing Settings page is `ProductCatalog`. `SvcCatalogItemDef` is a different object (Service Catalog Item Definition) and is not part of this step.

### Step 1: Assignment Rules for IT Service

**Purpose:** Enable Context Service and BRE Decision Table Access for IT Service assignment rules.

> **⚡ Auto-complete behavior:** After Phase 9 deploys Context Service (`enableContextDefinitions`), the "Context Service" sub-step on this page auto-completes to ✅. Only "BRE Decision Table Access" typically requires manual action. If you visit this page after Phase 9 and see all sub-steps showing ✅ Complete, **no action is needed** — skip this step entirely.

**URL:** `/lightning/setup/page/feature/service-cloud-itsm-assignment-rules/home?topic=SalesforceGo`

**Page verification:** The breadcrumb at top should show **"Salesforce Go > Assignment Rules for IT Service"**. If it does not, stop and verify you have the correct URL and org.

**What you'll see:**

* Header: "Assignment Rules for IT Service"
* A "Turn on Assignment Rules for IT Service" card with sub-steps
* Progress indicator showing completion status (e.g. "1 of 3 Steps Completed")

**Sub-steps on the page:**

1. **Turn on Assignment Rules** — Contains two sub-tasks:
   * **Context Service** — May already show ✅ (auto-enabled from Phase 9 deploy)
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
* If the step fails repeatedly, verify that the Context Service PSL and BRE PSLs are assigned to the user (Phase 9 permissions)
* If the page shows "Feature not available", the org may lack the required ITSM licenses

### Step 2: Set Up Enhanced Chat for IT Service Employee

**Purpose:** Enable Omni-Channel and Enhanced Chat for IT Service Employee agents. This turns on persistent messaging so Agentforce agents can answer employee questions for IT troubleshooting, service requests, and incident tracking.

**URL:** `/lightning/setup/page/feature/service-cloud-agentforce-for-itsm/home?topic=SalesforceGo`

**Page verification:** Breadcrumb should show **"Salesforce Go > Agentforce for IT Service"**. The page header should read **"Agentforce for IT Service"** with description "Empower employees to self-serve or create incidents with Agentforce..."

**What you'll see on the page:**

* **Turn on Agentforce** section (should already show "On" with ✅ Success for Agentforce Studio)
* **Enable IT Service Agent Templates** section with three sub-options:
  * IT Service Employee (toggle) — ⛔ DO NOT TOUCH. Do not enable this toggle. It is NOT part of this recipe.
  * IT Service Fulfiller (toggle — may already be checked ✅ from Phase 12) — ⛔ DO NOT TOUCH. Already handled programmatically in Phase 12.
  * **Set Up Enhanced Chat for IT Service Employee** (toggle — ✅ this is the ONLY toggle to enable in this step)
* **Enable Specialized IT Service Agent Templates** section (separate, below) — ⛔ DO NOT TOUCH. Do not enable any toggles in this section. It is NOT part of this recipe.

**Interaction flow:**

**⚠️ CRITICAL: On this page, ONLY enable the "Set Up Enhanced Chat for IT Service Employee" toggle. Do NOT enable "IT Service Employee", "IT Service Fulfiller", or "Specialized Agent Templates for Employee" toggles — those are either handled programmatically in other phases or are not part of this recipe.**

1. Navigate to the URL above
2. Scroll down to find **"Set Up Enhanced Chat for IT Service Employee"** under the "Enable IT Service Agent Templates" section
3. Click the **Enable/Disable Feature** toggle switch next to it
   * **Note:** The switch element itself may be intercepted by a parent container — click the container/label area around the toggle if the switch doesn't respond directly
4. A confirmation dialog appears: **"Turn on Set Up Enhanced Chat for IT Service Employee?"**
   * Dialog message: "It takes a few minutes to turn on this feature for you. When it's ready, you can configure settings and give users access."
5. Click **"Confirm"**
6. **Do NOT wait for completion** — this step provisions Omni-Channel and related configuration, which can take several minutes in the background

**Expected result after confirming:**

* The toggle shows as checked/enabled
* Background provisioning begins (Omni-Channel setup, messaging configuration)
* The page may show progress indicators or sub-steps appearing under the section
* A toast notification may appear confirming the feature was turned on

**Troubleshooting:**

* If the toggle doesn't respond to clicks, try clicking the **parent container element** (1-2 refs above the switch in the accessibility snapshot) rather than the switch element itself — see Operational Learning #21 about shadow DOM click interception on Lightning toggle components
* If provisioning fails, return to the page later and look for a "Try Again" button (similar to Assignment Rules pattern)
* This feature requires Agentforce to already be turned on (the "Turn on Agentforce" section must show "On")

### Step 3: CMDB and Service Graph Provisioning

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

**Post-provisioning — Step 3b: Turn on CMDB Feature**

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

1. Start CMDB provisioning (Step 3 — click "Provision CMDB")
2. Move on to other browser steps (Enhanced Chat, Assignment Rules, etc.)
3. Come back to check provisioning status
4. Once provisioned, navigate to the CMDB integration page (Step 3b) and turn it on

**Post-enablement:** The CMDB permission sets (`ItSrvcCnfgItmOwnerPermissionSet`, `ItSrvcCnfgItmReadPermissionSet`, `ItSrvcCnfgItmTypManagerPermissionSet`, `ItSrvcCnfgItmTypReadPermissionSet`) can be assigned to users.

### Step 3c: Verify Enhanced Chat Messaging Channel

**Purpose:** After Enhanced Chat provisioning completes (Step 2), verify the MessagingChannel was created correctly and User Verification is enabled on the Embedded Messaging configuration.

**Prerequisites:** Step 2 (Set Up Enhanced Chat for IT Service Employee) must have completed provisioning (not just confirmed — the background provisioning must finish).

**Verification flow:**

**Scope: This is a VERIFICATION step — read and observe only. Do not enable, toggle, or click any features unless explicitly instructed below.**

1. **Query MessagingChannel to confirm creation:**

   ```
   SELECT Id, DeveloperName, MasterLabel, IsActive
   FROM MessagingChannel
   WHERE DeveloperName = 'ItEmpAgentChannel'
   ```

   * **Expected result:** One record with `DeveloperName = 'ItEmpAgentChannel'`, `MasterLabel = 'IT Employee Agent Channel'`, `IsActive = true`
   * If no record is found, Enhanced Chat provisioning has not completed yet — wait and retry
   * Save the `Id` value for the next step

2. **Navigate to the Embedded Messaging setup page:**

   **URL:** `/lightning/setup/LiveMessageSetup/<MessagingChannelId>/view?lightning__channelType=EmbeddedMessaging`

   Replace `<MessagingChannelId>` with the Id from the query above (e.g. `0Mjxxxxxxxxxx`).

3. **Verify channel configuration on the page:**

   * **Channel Name:** "IT Employee Agent Channel"
   * **Developer Name:** "ItEmpAgentChannel"
   * **User Verification:** ✅ Checkbox "Add User Verification" should be **checked**
   * **"End chat when session ends":** Should be **disabled** (this is automatically disabled when User Verification is on)
   * **Flow Definition:** "Route Messages to IT Employee Agent For Enhanced Chat"
   * **Fallback Queue:** "IT Employee Agent Messaging Queue"
   * **Omni-Channel Routing:** Should be configured

4. **If User Verification is NOT checked:**

   * Click the "Add User Verification" checkbox to enable it
   * Save the page if a save action is required
   * Note: Enabling User Verification automatically disables "End chat when session ends"

**Expected result:**

* MessagingChannel exists with `IsActive = true`
* User Verification is checked ✅
* Channel is fully configured with routing flow and fallback queue

**Troubleshooting:**

* If the MessagingChannel query returns no results, Enhanced Chat provisioning is still running — return to Step 2's page to check status
* If `IsActive = false`, the channel was created but not activated — check the Embedded Messaging setup page for errors
* If the Embedded Messaging setup page shows an error, verify that Omni-Channel was successfully provisioned as part of Step 2

### Step 6: Verify Agentforce IT Service Agent Templates

**Purpose:** After IT Service Employee (Step 2 / Enhanced Chat) and IT Service Fulfiller (Phase 12 programmatic enablement) features are turned on, verify that both have agents provisioned under "Build and Manage Agent". This determines whether additional browser steps are needed to create agents.

> **⚡ Programmatic alternative (recommended):** This verification can be done entirely via SOQL without opening a browser:
>
> ```
> SELECT Id, DeveloperName, MasterLabel FROM BotDefinition
> WHERE DeveloperName LIKE '%IT%' OR DeveloperName LIKE '%Fulfiller%' OR DeveloperName LIKE '%Employee%'
> ```
>
> If the query returns agents for both IT Employee and IT Fulfiller, skip the browser verification and proceed directly to Step 8 (activation). Only open the browser if the query returns no results or you need to debug missing agents.

**Prerequisites:**

* Step 2 (Set Up Enhanced Chat for IT Service Employee) must have completed provisioning
* IT Service Fulfiller must be turned on (done programmatically in Phase 12 via `enableItSrvcsFulfillerAgent` flag in `ServiceItsmIntelligenceUdd` settings)

**URL (browser fallback):** `/lightning/setup/page/feature/service-cloud-agentforce-for-itsm/home?topic=SalesforceGo`

**Page verification:** Breadcrumb should show **"Salesforce Go > Agentforce for IT Service"**. Header: **"Agentforce for IT Service"**.

**What you'll see on the page:**

* **Turn on Agentforce** section (should show "On" with ✅ for Agentforce Studio)
* **Enable IT Service Agent Templates** section with three sub-features:
  * **IT Service Employee** — toggle checked ✅, with progress indicator (e.g. "2 of 2 Steps Completed")
  * **IT Service Fulfiller** — toggle checked ✅, with progress indicator (e.g. "1 of 3 Steps Completed" or "3 of 3 Steps Completed")
  * **Set Up Enhanced Chat for IT Service Employee** — toggle checked ✅, with progress indicator

**Verification flow:**

**Scope: This is a VERIFICATION step — read and observe only. Do not enable, toggle, or click any features on this page. Only check status and note the results.**

1. Navigate to the URL above

2. **Verify IT Service Employee feature is turned on** — toggle should show checked ✅

3. **Expand IT Service Employee** by clicking the "IT Service Employee" heading/button

4. Look for the **"Build and Manage Agent"** sub-step:

   * ✅ **Pass:** Shows **"1 active agent, 0 inactive agents"** or **"0 active agents, 1 inactive agent"** — at least one agent exists
   * ❌ **Fail:** Shows **"0 agents"** — agent needs to be created (requires additional browser steps)

5. Note the copilot builder link URL if present (e.g. `/AiCopilot/copilotStudio.app#/copilot/builder?copilotId=...`) — this will be used later for agent configuration

6. **Verify IT Service Fulfiller feature is turned on** — toggle should show checked ✅

7. **Expand IT Service Fulfiller** by clicking the "IT Service Fulfiller" heading/button

8. Look for the **"Build and Manage Agent"** sub-step:

   * ✅ **Pass:** Shows **"1 active agent, 0 inactive agents"** or **"0 active agents, 1 inactive agent"** — at least one agent exists
   * ❌ **Fail:** Shows **"0 agents"** — agent needs to be created (requires additional browser steps)

9. Note the wizard link URL if agent creation is needed (e.g. `/AiCopilot/copilotStudio.app#/copilot/wizard?mode=svc_itsm_intelligence__ITSrvcMgmtFulfiller`)

**Decision point:**

* **Both have agents** → Proceed to next steps (agent configuration, activation)
* **IT Service Employee missing agent** → Additional browser steps needed to create the employee agent via the wizard link
* **IT Service Fulfiller missing agent** → Additional browser steps needed to create the fulfiller agent via the wizard link (`/AiCopilot/copilotStudio.app#/copilot/wizard?mode=svc_itsm_intelligence__ITSrvcMgmtFulfiller`)
* **Both missing agents** → Both agents need to be created through the wizard before proceeding

**IT Service Fulfiller additional sub-steps (visible when expanded):** The Fulfiller section may show additional incomplete steps beyond "Build and Manage Agent":

* **Configure Proactive Assistance** — checkbox (may be disabled until agent is created)
* Other configuration steps depending on org state

**Troubleshooting:**

* If a feature toggle is not checked (turned off), it was not enabled programmatically — check Phase 12 deploy logs
* If the page shows "0 agents" for IT Service Employee despite Enhanced Chat being enabled, the provisioning may still be in progress — wait a few minutes and refresh
* If the "Build and Manage Agent" step shows "Step incomplete" with "0 agents", the agent template was not auto-provisioned and must be created manually through the wizard link

### Step 7: Create Missing Agentforce IT Service Agents via Wizard

**Purpose:** If Step 6 verification found that IT Service Employee or IT Service Fulfiller is missing an agent (shows "0 agents" under "Build and Manage Agent"), create the missing agent(s) using the Agentforce agent creation wizard.

**Prerequisites:**

* Step 6 verification completed — you know which agent(s) are missing
* The corresponding feature must be turned on (toggle checked ✅) before the wizard link becomes available

**Critical: Authentication requirement** The wizard runs inside the `/AiCopilot/copilotStudio.app` application which requires frontdoor URL authentication. **Direct navigation to the wizard URL will redirect to a login page.** You must:

1. Use `openSalesforceOrg` with the wizard path to get a frontdoor-authenticated URL
2. Navigate to the frontdoor URL which will authenticate and redirect to the wizard

**Wizard URL patterns:**

* **IT Service Fulfiller:** `/AiCopilot/copilotStudio.app#/copilot/wizard?mode=svc_itsm_intelligence__ITSrvcMgmtFulfiller`
* **IT Service Employee:** `/AiCopilot/copilotStudio.app#/copilot/wizard?mode=svc_itsm_intelligence__ITSrvcMgmtEmployee` (pattern — confirm from the "Go" button link on the Agentforce for IT Service page)

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

### Step 8: Activate Agentforce IT Service Agents (programmatic)

**Purpose:** Activate both IT Service agents (IT Employee Assistant and IT Service Fulfiller) so they are live and available.

**This step is fully programmatic — no browser needed.**

**Prerequisites:**

* Step 6/7 completed — both agents exist (created via wizard or auto-provisioned)
* Must run from a valid SFDX project directory (has `sfdx-project.json`), otherwise `sf agent activate` fails with `InvalidProjectWorkspaceError`

**Agent API names:**

| Agent Label | DeveloperName (API Name) | BotDefinition ID | |---|---|---| | IT Employee Assistant | `ItEmployeeAssistant` | (varies per org) | | IT Service Fulfiller | `IT_Service_Fulfiller` | (varies per org) |

> **Note:** The discovery query may return additional agents beyond these two (e.g. `IT_Service_Employee`). These are auto-provisioned by other features and do not need to be activated or included in the Access Agents permission set unless specifically required. Focus on the two agents listed above.

**Discovery — find the agent API names:** Query `BotDefinition` to find the IT Service agents:

```
SELECT Id, DeveloperName, MasterLabel FROM BotDefinition
WHERE DeveloperName LIKE '%IT%' OR DeveloperName LIKE '%Fulfiller%' OR DeveloperName LIKE '%Employee%'
```

**Check current status:** Query `BotVersion` to see which agents are already active:

```
SELECT BotDefinition.DeveloperName, BotDefinition.MasterLabel, Status, VersionNumber
FROM BotVersion
WHERE BotDefinition.DeveloperName IN ('ItEmployeeAssistant','IT_Service_Fulfiller')
```

**Activation command:**

```
sf agent activate --api-name <DeveloperName> --target-org <ORG> --json
```

Run this for each agent that has `Status = 'Inactive'`:

```
sf agent activate --api-name ItEmployeeAssistant --target-org <ORG> --json
sf agent activate --api-name IT_Service_Fulfiller --target-org <ORG> --json
```

> **Note:** See Operational Learning #20 — this command requires a valid SFDX project directory.

Expected success response:

```json
{ "status": 0, "result": { "success": true, "version": 1 } }
```

**Verification:** Re-query `BotVersion` to confirm both agents now show `Status = 'Active'`.

**Observed behavior on this org:**

* IT Employee Assistant was already active (auto-activated after Enhanced Chat provisioning)
* IT Service Fulfiller was inactive after wizard creation — activated successfully via `sf agent activate`
* Both agents confirmed active after activation

**Troubleshooting:**

* **`InvalidProjectWorkspaceError`:** You're not in an SFDX project directory. Navigate to a directory with `sfdx-project.json` or create a minimal one.
* **Agent already active:** `sf agent activate` on an already-active agent is a no-op — safe to run idempotently.
* **Agent not found:** Verify the `DeveloperName` matches exactly (case-sensitive). Query `BotDefinition` to confirm.

### Step 9: Create and Assign "Access Agents" Permission Set (programmatic)

**Purpose:** Create a custom Permission Set that grants Agent Access for both IT Employee Assistant and IT Service Fulfiller agents, then assign it to the connected user.

**This step is fully programmatic — no browser needed.**

**Prerequisites:**

* Step 8 completed — both agents are active
* Must run from a valid SFDX project directory

**Permission Set XML:**

Create file `force-app/main/default/permissionsets/Access_Agents.permissionset-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <agentAccesses>
        <agentName>ItEmployeeAssistant</agentName>
        <enabled>true</enabled>
    </agentAccesses>
    <agentAccesses>
        <agentName>IT_Service_Fulfiller</agentName>
        <enabled>true</enabled>
    </agentAccesses>
    <description>Grants access to IT Employee Assistant and IT Service Fulfiller Agentforce agents</description>
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

**Verification:**

```
SELECT PermissionSet.Name, PermissionSet.Label, Assignee.Username
FROM PermissionSetAssignment
WHERE PermissionSet.Name = 'Access_Agents'
```

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
* **Agent name mismatch:** The `agentName` values must match the `DeveloperName` from `BotDefinition` exactly. Query `BotDefinition` to confirm the correct names.
* **Permission set already exists:** If deploying to an org that already has this permission set, the deploy will update it (not create a duplicate).
* **Assignment failure — already assigned:** `sf org assign permset` fails if the user already has the permission set. This is safe to ignore.

### Step 10: Self Service Portal — Create Experience Cloud Site with Agentic Center Template (programmatic)

**Purpose:** Verify Self Service Portal is turned on and create an Experience Cloud site using the "Agentic Center" template to provide employees a self-service portal for IT incidents, cases, and service requests.

**This step is fully programmatic — no browser needed.**

**Prerequisites:**

* Self Service Portal feature must be turned on (verify via browser at `/lightning/setup/page/feature/service-cloud-itsm-self-service-portal/home?topic=SalesforceGo`)
* Digital Experiences must be enabled in the org

**Step 1 — Verify Self Service Portal is on:** Navigate (browser) to: `/lightning/setup/page/feature/service-cloud-itsm-self-service-portal/home?topic=SalesforceGo` Confirm "Turn on Self Service Portal" shows "On" with 100% progress.

**Step 2 — Check for existing sites:**

```
SELECT Id, Name, UrlPathPrefix, Status FROM Network ORDER BY Name
```

Look for any site using an "Agentic Center" or "Agentforce Employee Center" template. If one already exists, skip site creation.

**Step 3 — List available templates (Connect API via `sf api request rest`):**

```
sf api request rest '/services/data/v67.0/connect/communities/templates' --method get --target-org <ORG>
```

Verify `"Agentic Center"` is in the response. If not, inform the user and skip — the template may not be provisioned in the org.

> **⚠️ Use `sf api request rest`, NOT `curl`** — see Operational Learning #17. The `sf org display` command returns redacted access tokens that break `curl` calls. `sf api request rest` handles authentication automatically.

**Step 4 — Create the site (Connect API via `sf api request rest`):**

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

**Step 5 — Poll for completion:**

```
SELECT Id, Name, Status, Error FROM BackgroundOperation WHERE Id = '<jobId>'
```

Poll every 5-10 seconds until `Status = 'Complete'`. If `Error` is not null, the creation failed.

**Step 6 — Verify site created:**

```
SELECT Id, Name, UrlPathPrefix, Status FROM Network WHERE Name = '<SITE_NAME>'
```

Expected: Status = `UnderConstruction` (site is created but not yet published).

**User input required:** Before creating, ask the user for:

1. **Portal name** (e.g. "Employee Service Portal")
2. **URL suffix** (e.g. "helpdesk" → `https://<org>.my.site.com/helpdesk`)

**Observed behavior on this org:**

* Self Service Portal was turned on (1 of 2 steps completed — site creation was the missing step)
* "Agentic Center" template was available in the templates list
* Site creation via Connect API completed successfully in \~15 seconds
* Site created with Status = "UnderConstruction" (needs publishing separately)

**Troubleshooting:**

* **Template not found:** The "Agentic Center" template may not be provisioned. Check if "Agentforce Employee Center" is available as an alternative. If neither exists, inform user and skip.
* **URL suffix conflict:** If the URL path prefix is already in use by another site, creation will fail. Choose a different suffix.
* **BackgroundOperation stuck in "Running":** Wait longer — site creation can take up to 60 seconds. If stuck >2 minutes, check for errors.
* **Digital Experiences not enabled:** The Connect API will fail if Digital Experiences is not enabled in the org. Enable it first via Setup → Digital Experiences → Settings.

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

1. IT Employee Assistant (`ItEmployeeAssistant`)
2. IT Service Fulfiller (`IT_Service_Fulfiller`)

---

**Agent Builder URLs:**

* IT Employee Assistant: `/AiCopilot/copilotStudio.app#/copilot/builder?copilotId=<ItEmployeeAssistant_ID>`
* IT Service Fulfiller: `/AiCopilot/copilotStudio.app#/copilot/builder?copilotId=<IT_Service_Fulfiller_ID>`

To find the copilot IDs:

```
SELECT Id, DeveloperName, MasterLabel FROM BotDefinition
WHERE DeveloperName IN ('ItEmployeeAssistant','IT_Service_Fulfiller')
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
WHERE BotDefinition.DeveloperName IN ('ItEmployeeAssistant','IT_Service_Fulfiller')
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

### Step 13: Verify Enhanced Chat Configuration — Queue, Routing, and Flow (programmatic)

**Purpose:** The "Set Up Enhanced Chat for IT Service Employee" feature auto-provisions a queue, routing configuration, and a routing flow. This step verifies all three components exist and are correctly configured, and fixes any issues.

**This step is fully programmatic.**

**Prerequisites:**

* "Set Up Enhanced Chat for IT Service Employee" must have been enabled (from the Agentforce for IT Service page). If it failed or was not enabled, **skip this step entirely**.

---

**Verification 1 — Queue: ITEmpAgentMsgQueue**

Query the queue:

```
SELECT Id, Name, DeveloperName, QueueRoutingConfigId
FROM Group
WHERE Type = 'Queue' AND DeveloperName = 'ItEmpAgentMsgQueue'
```

**Expected:**

* Name: `IT Employee Agent Messaging Queue`
* DeveloperName: `ItEmpAgentMsgQueue`
* QueueRoutingConfigId: should be populated (not null)

**Check queue supported objects:**

```
SELECT Id, SobjectType FROM QueueSobject WHERE QueueId = '<QueueId>'
```

Must include both:

* ✅ `MessagingEndUser` (Messaging User)
* ✅ `MessagingSession`

**Check queue members:**

```
SELECT Id, UserOrGroupId FROM GroupMember WHERE GroupId = '<QueueId>'
```

The connected user should be a member. If not, add them:

```
sf data create record --sobject GroupMember \
  --values "GroupId=<QueueId> UserOrGroupId=<UserId>" \
  --target-org <ORG>
```

Note: The auto-provisioning may add a Role group rather than the user directly. Adding the user as a direct member ensures they can receive routed messages.

---

**Verification 2 — Routing Configuration: ItEmpAgentRoutingCnfg**

Query the routing config (using the `QueueRoutingConfigId` from the queue):

```
SELECT Id, DeveloperName, MasterLabel, RoutingPriority, RoutingModel, CapacityPercentage
FROM QueueRoutingConfig
WHERE DeveloperName = 'ItEmpAgentRoutingCnfg'
```

**Expected values:** | Field | Expected Value | |---|---| | MasterLabel | IT Employee Agent Routing Configuration | | RoutingPriority | 1 | | RoutingModel | MostAvailable | | CapacityPercentage | 50 (or configured value) |

**If routing config is missing**, create one:

1. Navigate to Setup → Routing Configurations (browser)
2. Click New
3. Configure:
   * Name: `IT Employee Agent Routing Configuration`
   * Routing Priority: `1`
   * Routing Model: `Most Available`
   * Capacity Type: `Inherited`
   * Units of Capacity: `10`
4. Click Save
5. Assign it to the queue by updating the queue's `QueueRoutingConfigId`

---

**Verification 3 — Flow: RouteMsgsItEmpAgent**

Query via Tooling API:

```
GET /services/data/v67.0/tooling/query?q=
  SELECT Id, Definition.DeveloperName, MasterLabel, Status, VersionNumber
  FROM Flow
  WHERE Definition.DeveloperName='RouteMsgsItEmpAgent'
  ORDER BY VersionNumber DESC LIMIT 5
```

**Expected:**

* MasterLabel: `Route Messages to IT Employee Agent For Enhanced Chat`
* Status: `Active`

If the flow is missing or inactive, the Enhanced Chat setup did not complete successfully. The flow is auto-created by the setup wizard and cannot easily be recreated manually — re-run the Enhanced Chat setup from the Agentforce for IT Service page.

---

**Observed behavior on this org:**

* ✅ Queue `ItEmpAgentMsgQueue` exists with both `MessagingEndUser` and `MessagingSession` objects
* ⚠️ Queue member was a Role group only — connected user was added as a direct member
* ✅ Routing config `ItEmpAgentRoutingCnfg` exists with Priority=1, Model=MostAvailable, Capacity=50%
* ✅ Routing config is assigned to the queue (`QueueRoutingConfigId` populated)
* ✅ Flow `RouteMsgsItEmpAgent` exists and is Active (v1)

**Troubleshooting:**

* **Queue not found:** Enhanced Chat setup did not complete. Re-enable from the Agentforce for IT Service page.
* **Queue missing objects:** Use browser to edit the queue and add `Messaging User` and `Messaging Session` as supported objects.
* **Routing config not assigned to queue:** The queue's `QueueRoutingConfigId` is null. Edit the queue in Setup and select the routing configuration.
* **Flow not found or inactive:** The routing flow is auto-provisioned. If missing, the Enhanced Chat setup must be re-run. If inactive, activate it via Setup → Flows.
* **FlowDefinition SOQL not supported:** Use Tooling API (`/services/data/v67.0/tooling/query`) to query Flow/FlowDefinition instead of standard SOQL.

### Step 14: Complete Embedded Messaging Setup for Employee Portal (manual)

**Purpose:** Configure the Embedded Messaging deployment that connects the Experience Cloud site (Employee Service Portal) to the IT Employee Assistant agent via the Enhanced Chat channel. This enables the chat widget on the portal.

**This step is MANUAL — too many org-specific variables for automation.**

This step involves configuring Embedded Service Deployments, messaging channels, and linking them to the Experience Cloud site. The configuration depends on the specific site name, URL, messaging channel IDs, and other org-specific values that vary between environments.

**Reference:** Follow the Salesforce Help article for complete instructions: https://help.salesforce.com/s/articleView?id=service.it_srvcs_embedded_msgng_manual_steps.htm&type=5

**Prerequisites:**

* Step 10 completed — Experience Cloud site created (e.g. "Employee Service Portal" at `/helpdesk`)
* Step 13 completed — Enhanced Chat queue, routing config, and flow verified
* Both IT Service agents are active (Step 8)

### Step 15: SLA Management for IT Service (browser)

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

**3. (Optional) Create Predefined Policies:**

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
* Page shows "1 of 5 Steps Completed" for the automated section
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
* **Turn On fails:** Verify that Incident Management (Phase 3) is enabled. SLA Management depends on ITSM features being active.
* **Create Predefined Policies — Save button stays disabled:** At least one checkbox must be checked before Save becomes enabled.
* **Checkbox click doesn't register:** Click the label text next to the checkbox rather than the checkbox input itself — the input element is intercepted by a container span.
* **Dialog buttons disabled after Save:** This is normal — the system is processing. Wait for the dialog to close automatically.