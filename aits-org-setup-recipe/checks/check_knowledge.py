#!/usr/bin/env python3
"""AITS Knowledge readiness check (phase 7b) - READ-ONLY. Changes nothing.
Usage: python3 checks/check_knowledge.py <org-alias> [--json out.json]
Checks: Knowledge ON (7a core, via settings/apply_settings.py status --json) · connected user has Knowledge User ·
Knowledge__kav has the ITSM fields Details, Issue, Resolution, Root Cause, Workaround (needed by the Data Library) ·
article record types present · published article count (info).
Fix (only with user approval): set User.UserPermissionsKnowledgeUser = true on the connected user. Missing fields/record
types are reported (they come with the IT Service package/template; the recipe does not create them).
Exit: 0 = all PASS · 2 = something FAIL · 1 = check could not run.
"""
import json, os, subprocess, sys
if len(sys.argv) < 2: sys.exit(__doc__)
ORG = sys.argv[1]; A = sys.argv[2:]; OUT = A[A.index("--json") + 1] if "--json" in A else None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = {"Details__c": "Details", "Issue__c": "Issue", "Resolution__c": "Resolution", "Root_Cause__c": "Root Cause", "Workaround__c": "Workaround"}

def q(soql):
    p = subprocess.run(["sf", "data", "query", "--target-org", ORG, "-q", soql, "--json"], capture_output=True, text=True)
    try: d = json.loads(p.stdout)
    except Exception: return None
    return d["result"] if d.get("status") == 0 else None

rows = []
def add(check, status, detail, nxt=""):
    rows.append({"phase": "7b", "check": check, "status": status, "detail": detail, "next": nxt})

p = subprocess.run([sys.executable, os.path.join(ROOT, "settings", "apply_settings.py"), ORG, "status", "--json", "--features", "knowledge"], capture_output=True, text=True)
try: k = json.loads(p.stdout.strip().splitlines()[-1]).get("knowledge", {})
except Exception: print("could not read Knowledge status"); sys.exit(1)
add("Knowledge ON (7a)", "PASS" if k.get("coreValue") == "true" else "FAIL", f"{k.get('state')} ({k.get('on')}/{k.get('of')} flags)",
    "run settings/apply_settings.py <org> plan|deploy --features knowledge")

me = subprocess.run(["sf", "org", "display", "user", "--target-org", ORG, "--json"], capture_output=True, text=True)
try: uid = json.loads(me.stdout)["result"]["id"]
except Exception: print("could not read connected user"); sys.exit(1)
u = q(f"SELECT UserPermissionsKnowledgeUser FROM User WHERE Id = '{uid}'")
if u is None: print("could not read user"); sys.exit(1)
ku = u["records"][0]["UserPermissionsKnowledgeUser"]
add("Connected user is a Knowledge User", "PASS" if ku else "FAIL", str(ku), f"with user approval: sf data update record --sobject User --record-id {uid} --values \"UserPermissionsKnowledgeUser=true\"")

f = q("SELECT QualifiedApiName FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = 'Knowledge__kav'")
have = {r["QualifiedApiName"] for r in (f or {}).get("records", [])}
miss = [lab for api, lab in FIELDS.items() if api not in have]
add("ITSM article fields (Details, Issue, Resolution, Root Cause, Workaround)", "PASS" if not miss else "FAIL",
    "all present" if not miss else "missing: " + ", ".join(miss), "fields come with the IT Service setup; report to the user (Data Library needs them)")

rt = q("SELECT DeveloperName FROM RecordType WHERE SobjectType = 'Knowledge__kav'")
names = [r["DeveloperName"] for r in (rt or {}).get("records", [])]
add("Article record types", "PASS" if names else "INFO", ", ".join(names) or "none (single default type)")

c = q("SELECT COUNT() FROM Knowledge__kav WHERE PublishStatus = 'Online'")
add("Published articles", "INFO", str((c or {}).get("totalSize", "unknown")), "")

w = max(len(r["check"]) for r in rows)
for r in rows:
    print(f"7b  {r['status']:4} {r['check']:<{w}}  {r['detail']}" + (f"\n          next: {r['next']}" if r["status"] == "FAIL" and r["next"] else ""))
if OUT: json.dump(rows, open(OUT, "w"), indent=2)
sys.exit(2 if any(r["status"] == "FAIL" for r in rows) else 0)
