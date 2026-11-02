#!/usr/bin/env python3
"""IT Service Cloud CMDB & Service Graph checks (phase 11) - READ-ONLY. Changes nothing.
Usage: python3 checks/check_cmdb.py <org-alias> [--json out.json]
11a Objects + permissions : ConfigurationItem (+ Incident/Problem link objects) queryable; CMDB permission sets
                            (ItSrvcCnfgItm*PermissionSet) assigned to the connected user. Missing objects = CMDB not provisioned.
11b Provisioning          : no queryable setting -> confirm on /lightning/setup/CMDBProvisionalSettings/home (read-only):
                            Status = Provisioned, both stages Completed. If Unprovisioned/Failed -> browser 'Provision CMDB'
                            (user approval; runs in the background - re-check later).
11c CMDB feature ON        : confirm on the Salesforce Go page service-cloud-itsm-cmdb-integration (read-only):
                            'Turn on Configuration Management Database (CMDB)' switch checked. If off -> browser 'Get Started'
                            (if shown) -> toggle -> Confirm (user approval). Other items on the page are manual/optional.
Exit: 0 = 11a PASS (11b/11c need page confirmation) · 2 = 11a FAIL · 1 = could not run.
"""
import json, subprocess, sys
if len(sys.argv) < 2: sys.exit(__doc__)
ORG = sys.argv[1]; A = sys.argv[2:]; OUT = A[A.index("--json") + 1] if "--json" in A else None
PS = ["ItSrvcCnfgItmOwnerPermissionSet", "ItSrvcCnfgItmReadPermissionSet", "ItSrvcCnfgItmTypManagerPermissionSet", "ItSrvcCnfgItmTypReadPermissionSet"]

def q(soql):
    p = subprocess.run(["sf", "data", "query", "--target-org", ORG, "-q", soql, "--json"], capture_output=True, text=True)
    try: d = json.loads(p.stdout)
    except Exception: return None
    return d["result"] if d.get("status") == 0 else None

rows = []
def add(phase, check, status, detail, nxt=""):
    rows.append({"phase": phase, "check": check, "status": status, "detail": detail, "next": nxt})

objs = q("SELECT QualifiedApiName FROM EntityDefinition WHERE QualifiedApiName IN ('ConfigurationItem','IncidentConfigurationItem','ProblemConfigurationItem')")
if objs is None: print("could not query EntityDefinition"); sys.exit(1)
have = {r["QualifiedApiName"] for r in objs["records"]}
add("11a", "CMDB objects present", "PASS" if "ConfigurationItem" in have else "FAIL", ", ".join(sorted(have)) or "none",
    "CMDB not provisioned - run 11b (Provision CMDB)")
ci = q("SELECT COUNT() FROM ConfigurationItem") if "ConfigurationItem" in have else None
add("11a", "Configuration items (info)", "INFO", str(ci["totalSize"]) if ci else "-")
me = subprocess.run(["sf", "org", "display", "user", "--target-org", ORG, "--json"], capture_output=True, text=True)
try: uid = json.loads(me.stdout)["result"]["id"]
except Exception: print("could not read connected user"); sys.exit(1)
pa = q(f"SELECT PermissionSet.Name FROM PermissionSetAssignment WHERE AssigneeId = '{uid}' AND PermissionSet.Name IN (" + ",".join(f"'{p}'" for p in PS) + ")")
got = {r["PermissionSet"]["Name"] for r in (pa or {}).get("records", [])}
miss = [p for p in PS if p not in got]
add("11a", "CMDB permission sets assigned to connected user", "PASS" if not miss else "FAIL", "all 4" if not miss else "missing: " + ", ".join(miss),
    "assign with user approval (they only exist after provisioning)")
add("11b", "CMDB provisioned", "PAGE", "confirm: /lightning/setup/CMDBProvisionalSettings/home -> Status = Provisioned")
add("11c", "CMDB feature ON", "PAGE", "confirm: Salesforce Go 'Configuration Management Database (CMDB)' -> Turn on switch checked")

w = max(len(r["check"]) for r in rows)
for r in rows:
    print(f"{r['phase']}  {r['status']:4} {r['check']:<{w}}  {r['detail']}" + (f"\n          next: {r['next']}" if r["status"] == "FAIL" and r["next"] else ""))
if OUT: json.dump(rows, open(OUT, "w"), indent=2)
sys.exit(2 if any(r["status"] == "FAIL" for r in rows) else 0)
