#!/usr/bin/env python3
"""IT Service Cloud SLA Management checks (phases 5a-5c) - READ-ONLY. Reports PASS / FAIL / OPTIONAL with a next step; changes nothing.
Usage: python3 checks/check_sla.py <org-alias> [--json out.json]
5a Turn on SLA Management : Entitlement settings enableEntitlements + enableEntitlementVersioning = true.
                             If OFF -> Level 2 browser: SLA page 'Turn On' -> Confirm (settings deploy untested).
5b Predefined policies     : an SlaProcess exists for Incident, Problem and ChangeRequest (any name).
                             If all exist -> done. NEVER click 'Create Predefined Policies' then (irreversible; the page
                             checkbox can stay unchecked even when policies exist). If some are missing -> ask the user,
                             then create only the missing ones in the browser.
5c Milestones related list : OPTIONAL step - each Incident/Problem/ChangeRequest record page (FlexiPage) is checked for a
                             Milestones RELATED LIST (the Milestone Tracker component support:milestones is reported as info only). Missing -> reported as OPTIONAL (not a failure); add only on user request.
Exit: 0 = 5a and 5b PASS (5c may be optional/not done) · 2 = 5a or 5b FAIL · 1 = check could not run.
"""
import json, re, subprocess, sys
if len(sys.argv) < 2: sys.exit(__doc__)
ORG = sys.argv[1]; A = sys.argv[2:]; OUT = A[A.index("--json") + 1] if "--json" in A else None
PAGE = "/lightning/setup/page/feature/service-cloud-itsm-manage-sla-policies/home?topic=SalesforceGo"
OBJS = ("Incident", "Problem", "ChangeRequest")

def q(soql, tooling=False):
    cmd = ["sf", "data", "query", "--target-org", ORG, "-q", soql, "--json"] + (["--use-tooling-api"] if tooling else [])
    p = subprocess.run(cmd, capture_output=True, text=True)
    try: d = json.loads(p.stdout)
    except Exception: return None
    return d["result"]["records"] if d.get("status") == 0 else None

rows = []
def add(phase, check, status, detail, nxt=""):
    rows.append({"phase": phase, "check": check, "status": status, "detail": detail, "next": nxt})

es = q("SELECT Metadata FROM EntitlementSettings LIMIT 1", tooling=True)
if es is None: print("could not read EntitlementSettings"); sys.exit(1)
md = es[0]["Metadata"] if es else {}
for flag, label in (("enableEntitlements", "Entitlements / Simplified SLA setup"), ("enableEntitlementVersioning", "SLA versioning")):
    ok = md.get(flag) is True
    add("5a", f"{label} ({flag})", "PASS" if ok else "FAIL", str(md.get(flag)),
        "" if ok else f"browser (Level 2): {PAGE} -> 'Turn on SLA Management for IT Service' -> Turn On -> Confirm")

sla = q("SELECT Name, SobjectType, IsActive, IsVersionDefault FROM SlaProcess") or []
missing = []
for o in OBJS:
    hits = [r for r in sla if r["SobjectType"] == o]
    active = [r for r in hits if r["IsActive"]]
    if not hits: missing.append(o)
    add("5b", f"SLA policy exists for {o}", "PASS" if hits else "FAIL",
        ", ".join(f"{r['Name']}{' (active)' if r['IsActive'] else ' (inactive)'}" for r in hits) or "none",
        "" if hits else "ask the user, then browser: SLA page -> Create Predefined Policies -> tick ONLY the missing objects -> Save (irreversible)")
    if hits and not active:
        add("5b", f"SLA policy for {o} active", "OPTIONAL", "exists but inactive", "activate in Setup > Entitlement Processes if wanted")
if not missing:
    add("5b", "Do not click 'Create Predefined Policies'", "INFO", "all three policies exist; the page checkbox may still show unchecked", "")

pages = q("SELECT Id, DeveloperName, EntityDefinitionId FROM FlexiPage WHERE Type = 'RecordPage' AND EntityDefinitionId IN ('Incident','Problem','ChangeRequest')", tooling=True) or []
for o in OBJS:
    ps = [p for p in pages if p["EntityDefinitionId"] == o]
    if not ps:
        add("5c", f"Milestones related list on {o} record page", "OPTIONAL", "no custom record page (default page in use)", "optional: add Milestones related list on user request"); continue
    for p in ps:
        m = q(f"SELECT Metadata FROM FlexiPage WHERE Id = '{p['Id']}'", tooling=True) or []
        js = json.dumps(m[0]["Metadata"]) if m else ""
        # the SLA page asks for the Milestones RELATED LIST (a related-list component whose relatedListApiName contains
        # "Milestone"); the Milestone Tracker component (support:milestones) is a different thing - reported as info only
        has_rl = bool(re.search(r'"relatedListApiName", "value": "[^"]*Milestone[^"]*"', js))
        tracker = '"componentName": "support:milestones"' in js
        add("5c", f"Milestones related list on {p['DeveloperName']}", "PASS" if has_rl else "OPTIONAL",
            ("present" if has_rl else "not on page") + ("; Milestone Tracker component present" if tracker else ""),
            "" if has_rl else "optional: add the Milestones related list to this record page on user request (page deploy, with approval)")

w = max(len(r["check"]) for r in rows)
for r in rows:
    print(f"{r['phase']}  {r['status']:8} {r['check']:<{w}}  {r['detail']}" + (f"\n             next: {r['next']}" if r["next"] else ""))
print("Manual (not checked): manage SLA policies and milestones; auto entitlement rules. Page badge 'In Progress' = optional items, not a failure.")
if OUT: json.dump(rows, open(OUT, "w"), indent=2)
sys.exit(2 if any(r["status"] == "FAIL" for r in rows if r["phase"] in ("5a", "5b")) else 0)
