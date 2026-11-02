#!/usr/bin/env python3
"""AITS Self-service portal checks (phase 8) - READ-ONLY. Changes nothing.
Usage: python3 checks/check_portal.py <org-alias> [--site "<site name>"] [--json out.json]
8a Self Service Portal ON : no queryable setting -> confirm on the Salesforce Go page (Level 2, read-only):
                            /lightning/setup/page/feature/service-cloud-itsm-self-service-portal/home?topic=SalesforceGo
                            "Turn on Self Service Portal" = On. If off: browser Turn On -> Confirm (user approval).
8b Portal site            : lists candidate sites (Connect API templateName = Agentic Center or Agentforce Employee Center;
                            Embedded Service sites are chat deployments and are excluded). With --site, checks that site exists.
                            No site chosen yet -> ask the user which to use, or create one (name + URL suffix from the user).
8c Published              : the chosen site's status is Live; otherwise publish only with user approval.
Exit: 0 = chosen site exists and is Live (or candidates listed when no --site) · 2 = chosen site missing / not Live · 1 = could not run.
"""
import json, subprocess, sys
if len(sys.argv) < 2: sys.exit(__doc__)
ORG = sys.argv[1]; A = sys.argv[2:]
SITE = A[A.index("--site") + 1] if "--site" in A else None
OUT = A[A.index("--json") + 1] if "--json" in A else None
PORTAL_TEMPLATES = ("Agentic Center", "Agentforce Employee Center")
p = subprocess.run(["sf", "api", "request", "rest", "/services/data/v67.0/connect/communities", "--method", "GET", "--target-org", ORG],
                   capture_output=True, text=True)
try: sites = json.loads(p.stdout).get("communities", [])
except Exception: print("could not read sites:", (p.stderr or p.stdout)[-200:]); sys.exit(1)
cands = [s for s in sites if s.get("templateName") in PORTAL_TEMPLATES]
other = [s for s in sites if s not in cands]
print("8b candidate portal sites:")
for s in cands: print(f"   {s['name']:28} {s.get('templateName'):28} {s.get('status'):18} {s.get('siteUrl')}")
print("   excluded (not portals):", ", ".join(f"{s['name']} ({s.get('templateName')})" for s in other) or "none")
rows = [{"phase": "8a", "check": "Self Service Portal ON", "status": "PAGE", "detail": "confirm on the Salesforce Go page (read-only)"}]
code = 0
if SITE:
    hit = next((s for s in sites if s["name"] == SITE), None)
    ok_exist = bool(hit) and hit.get("templateName") in PORTAL_TEMPLATES
    rows.append({"phase": "8b", "check": f"Chosen portal '{SITE}' exists with a portal template", "status": "PASS" if ok_exist else "FAIL",
                 "detail": f"{hit.get('templateName')} · {hit.get('siteUrl')}" if hit else "not found"})
    live = bool(hit) and hit.get("status") == "Live"
    rows.append({"phase": "8c", "check": f"'{SITE}' published (Live)", "status": "PASS" if live else "FAIL",
                 "detail": hit.get("status") if hit else "-", })
    code = 0 if (ok_exist and live) else 2
else:
    rows.append({"phase": "8b", "check": "Portal chosen", "status": "ASK", "detail": f"{len(cands)} candidate(s) - ask the user which to use (or create one)"})
for r in rows: print(f"{r['phase']}  {r['status']:5} {r['check']}  {r['detail']}")
if OUT: json.dump({"rows": rows, "candidates": cands}, open(OUT, "w"), indent=2)
sys.exit(code)
