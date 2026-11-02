#!/usr/bin/env python3
"""IT Service Cloud Phase 0 gate: IT Service Enablement must be ON before any other enablement.
Usage: python3 checks/check_it_service_enablement.py <org-alias>
Exit: 0 = ON (proceed) · 3 = OFF (turn it on first: Level 2 browser page below) · 1 = check failed (fallback: read the page)
Check source: Tooling API IncidentMgmtSettings.Metadata.itServiceEnablement (verified to match the Salesforce Go page
'Turn on IT Service Enablement' = On on it-service-cloud-bha853, 2026-10-30)."""
import json, subprocess, sys
PAGE = "/lightning/setup/page/feature/service-cloud-itsm-setup/home?topic=SalesforceGo"
if len(sys.argv) < 2: sys.exit(__doc__)
org = sys.argv[1]
p = subprocess.run(["sf", "data", "query", "--target-org", org, "--use-tooling-api", "--json",
                    "-q", "SELECT Metadata FROM IncidentMgmtSettings LIMIT 1"], capture_output=True, text=True)
try:
    d = json.loads(p.stdout); md = d["result"]["records"][0]["Metadata"]
except Exception:
    print(f"CHECK FAILED - could not read IncidentMgmtSettings. Fallback: open {PAGE} and read 'Turn on IT Service Enablement'.")
    sys.exit(1)
on = md.get("itServiceEnablement") is True
result = {"itServiceEnablement": md.get("itServiceEnablement"), "enableIncidentMgmt": md.get("enableIncidentMgmt"),
          "enableITSMIncidentMgmt": md.get("enableITSMIncidentMgmt"), "status": "ON" if on else "OFF"}
print(json.dumps(result))
if on:
    print("IT Service Enablement is ON - proceed. (Page badge may say 'In Progress' because of the optional 'Finish in Setup' item - not a failure.)")
    sys.exit(0)
print(f"IT Service Enablement is OFF - turn it on before any other phase: {PAGE} -> 'Turn on IT Service Enablement' toggle -> Confirm. Then re-run this check.")
sys.exit(3)
