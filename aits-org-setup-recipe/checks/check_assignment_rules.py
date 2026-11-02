#!/usr/bin/env python3
"""AITS Assignment Rules checks (phases 6a-6c) - READ-ONLY. Changes nothing.
Usage: python3 checks/check_assignment_rules.py <org-alias> [--json out.json]
6a Context Service      : IndustriesContext.enableContextDefinitions (same flag as phase 4a) - via settings/apply_settings.py status --json.
6b BRE permissions      : run settings/apply_permissions.py <org> verify --features bre (licences + permission sets) - summarised here.
6c Decision Table Access: no queryable/deployable setting exists. Evidence = an Active DecisionTable AND the IT Service sample
                          expression set (Sample_Assignment_Rule_for_Incident) exist. Confirm on the page (Level 2, read-only):
                          "Assignment Rules for IT Service" -> "Turn on Assignment Rules for IT Service" = On, both sub-steps Success.
                          If not on: browser -> 'Try Again' / 'Turn On' -> Confirm (user approval).
Exit: 0 = 6a-6c PASS · 2 = something FAIL · 1 = check could not run.
"""
import json, os, subprocess, sys
if len(sys.argv) < 2: sys.exit(__doc__)
ORG = sys.argv[1]; A = sys.argv[2:]; OUT = A[A.index("--json") + 1] if "--json" in A else None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "/lightning/setup/page/feature/service-cloud-itsm-assignment-rules/home?topic=SalesforceGo"

def q(soql):
    p = subprocess.run(["sf", "data", "query", "--target-org", ORG, "-q", soql, "--json"], capture_output=True, text=True)
    try: d = json.loads(p.stdout)
    except Exception: return None
    return d["result"]["records"] if d.get("status") == 0 else None

rows = []
def add(phase, check, ok, detail, nxt=""):
    rows.append({"phase": phase, "check": check, "status": "PASS" if ok else "FAIL", "detail": detail, "next": "" if ok else nxt})

p = subprocess.run([sys.executable, os.path.join(ROOT, "settings", "apply_settings.py"), ORG, "status", "--json", "--features", "context"], capture_output=True, text=True)
try: ctx = json.loads(p.stdout.strip().splitlines()[-1]).get("context", {})
except Exception: print("could not read Context Service status"); sys.exit(1)
add("6a", "Context Service (enableContextDefinitions)", ctx.get("coreValue") == "true", ctx.get("state", "unknown"),
    "run settings/apply_settings.py <org> plan|deploy --features context (phase 4a)")

p = subprocess.run([sys.executable, os.path.join(ROOT, "settings", "apply_permissions.py"), ORG, "verify", "--features", "bre"], capture_output=True, text=True)
lines = [l for l in p.stdout.splitlines() if l.startswith(("psl:", "ps:"))]
add("6b", "BRE licences + permission sets assigned", p.returncode == 0 and bool(lines), f"{sum('assigned ' in l for l in lines)}/{len(lines)} assigned" if lines else (p.stdout or p.stderr)[-120:],
    "run settings/apply_permissions.py <org> plan|deploy --features bre --confirm")

dt = q("SELECT DeveloperName, Status FROM DecisionTable WHERE Status = 'Active'")
es = q("SELECT DeveloperName FROM ExpressionSetDefinition WHERE DeveloperName = 'Sample_Assignment_Rule_for_Incident'")
if dt is None or es is None: print("could not query DecisionTable / ExpressionSetDefinition"); sys.exit(1)
add("6c", "Active decision table exists", bool(dt), ", ".join(r["DeveloperName"] for r in dt) or "none",
    f"confirm on the page (read-only): {PAGE}; if 'BRE Decision Table Access' is not Success -> 'Try Again'/'Turn On' -> Confirm (with user approval)")
add("6c", "IT Service sample assignment rule exists", bool(es), "Sample_Assignment_Rule_for_Incident" if es else "missing",
    f"confirm on the page (read-only): {PAGE}")

w = max(len(r["check"]) for r in rows)
for r in rows:
    print(f"{r['phase']}  {r['status']:4} {r['check']:<{w}}  {r['detail']}" + (f"\n          next: {r['next']}" if r["next"] else ""))
print(f"Page confirmation (Level 2, read-only): {PAGE} -> 'Turn on Assignment Rules for IT Service' = On, 2 sub-steps Success. "
      "Badge 'In Progress' = manual 'Set Up the Basics' items, not a failure.")
if OUT: json.dump(rows, open(OUT, "w"), indent=2)
sys.exit(2 if any(r["status"] == "FAIL" for r in rows) else 0)
