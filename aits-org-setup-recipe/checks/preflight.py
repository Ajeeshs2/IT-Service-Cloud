#!/usr/bin/env python3
"""AITS Pre-flight audit (run FIRST, every run) - READ-ONLY. Changes nothing in the org.
Usage: python3 checks/preflight.py <org-alias> [--portal-site "<name>"]
Builds a SKIP MAP: every recipe phase with its current state on the connected org and the suggested action, so the
user can choose which phases to run. Availability-driven (RC-44): features/objects not in the org are reported, never
treated as failures. Re-uses the phase checks (settings status, permissions verify, agent/SLA/assignment-rules/
knowledge/CMDB/portal checks). Pages that have no queryable state are listed as "confirm on page".
Writes ONLY to checks/preflight-out/preflight-<timestamp>.md + .json (never overwrites other evidence files).
Exit: 0 = audit completed (whatever the states) · 1 = could not run (e.g. connection problem).
"""
import json, os, subprocess, sys, time
if len(sys.argv) < 2: sys.exit(__doc__)
ORG = sys.argv[1]; A = sys.argv[2:]
SITE = A[A.index("--portal-site") + 1] if "--portal-site" in A else None
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUTDIR = os.path.join(HERE, "preflight-out"); os.makedirs(OUTDIR, exist_ok=True)
TS = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
# shared read-only settings cache for this pre-flight run (status mode only; deploy/plan always retrieve fresh)
import tempfile
os.environ["AITS_SETTINGS_CACHE"] = tempfile.mkdtemp(prefix="aits-preflight-")
import atexit, shutil as _sh
atexit.register(lambda: _sh.rmtree(os.environ.get("AITS_SETTINGS_CACHE", ""), ignore_errors=True))

def run(args, timeout=900):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr
def py(script, *args): return run([sys.executable, os.path.join(ROOT, script), ORG, *args])
def q(soql, tooling=False):
    rc, out, _ = run(["sf", "data", "query", "--target-org", ORG, "-q", soql, "--json"] + (["--use-tooling-api"] if tooling else []))
    try: d = json.loads(out)
    except Exception: return None
    return d["result"] if d.get("status") == 0 else None

skip = []     # rows: phase, feature, state, action
def row(phase, feature, state, action): skip.append({"phase": phase, "feature": feature, "state": state, "action": action})

# --- org + connection --------------------------------------------------------------------------------------------
org = q("SELECT Name, OrganizationType, IsSandbox, InstanceName FROM Organization")
if org is None: print("ABORT: cannot query the org (connection?)"); sys.exit(1)
o = org["records"][0]
rc, out, _ = run(["sf", "org", "display", "user", "--target-org", ORG, "--json"])
try: user = json.loads(out)["result"]; uname = user.get("username")
except Exception: uname = "unknown"
header = f"Org: {o['Name']} · {o['OrganizationType']} · {'sandbox' if o['IsSandbox'] else 'production'} · {o['InstanceName']} · user {uname}"

# --- deploy queue (Learning #9/#22/RC-58) --------------------------------------------------------------------------
dq = q("SELECT Id, Status, CreatedBy.Name, CreatedDate FROM DeployRequest WHERE Status IN ('Pending','InProgress') OR CreatedDate = LAST_N_DAYS:1 ORDER BY CreatedDate DESC LIMIT 10", tooling=True)
inflight = [r for r in (dq or {}).get("records", []) if r["Status"] in ("Pending", "InProgress")]
recent = [r for r in (dq or {}).get("records", []) if r["Status"] not in ("Pending", "InProgress")]
queue_note = ("IN-FLIGHT: " + ", ".join(f"{r['Id']} {r['Status']} by {(r.get('CreatedBy') or {}).get('Name')}" for r in inflight)
              + " - wait; NEVER cancel Automated Process") if inflight else "no deploys in flight"

# --- Phase 0 gate -------------------------------------------------------------------------------------------------
rc, out, _ = py("checks/check_it_service_enablement.py")
row("0", "IT Service Enablement (gate)", {0: "ON", 3: "OFF"}.get(rc, "check failed"),
    "proceed" if rc == 0 else "turn ON first (Salesforce Go page, browser) - nothing else runs until it is ON")

# --- settings-driven features (status --json) ---------------------------------------------------------------------
rc, out, _ = py("settings/apply_settings.py", "status", "--json")
try: st = json.loads(out.strip().splitlines()[-1])
except Exception: st = {}
spec_opt = {}
try:
    import xml.etree.ElementTree as ET
    sp = ET.parse(os.path.join(ROOT, "settings", "aits-itsm-settings.xml")).getroot()
    spec_opt = {f.get("id"): f.attrib for g in sp.findall("features") for f in g}
except Exception: pass
for fid, v in st.items():
    a = spec_opt.get(fid, {})
    if a.get("kind") == "permissions": continue
    tag = " [optional]" if a.get("optional") == "true" else (" [mandatory]" if a.get("mandatory") == "true" else "")
    state = f"{v['state']} ({v['on']}/{v['of']})"
    action = ("nothing to do" if v["state"].startswith("ON (all)") else
              "not in this org - skipped" if v["state"] == "not in org" else
              "select to run: settings/apply_settings.py plan/deploy --features " + fid)
    row(v["phase"], v["label"] + tag, state, action)

# --- permission phases (verify -> permissions-verify.md only) -----------------------------------------------------
perm_feats = [b.get("feature") for b in sp.findall("permissions")] if spec_opt else []
if perm_feats:
    rc, out, _ = py("settings/apply_permissions.py", "verify", "--features", ",".join(perm_feats))
    items = [l for l in out.splitlines() if l.startswith(("psl:", "ps:", "psg:"))]
    n_ok = sum(" assigned " in l and "not assigned" not in l for l in items); n_abs = sum("not in org" in l for l in items)
    missing = [l.split()[0] for l in items if "not assigned" in l]
    row("perm", "Permission sets / groups / licences (connected user)", f"{n_ok} assigned · {len(missing)} missing · {n_abs} not in org",
        "nothing to do" if not missing else "select to run: settings/apply_permissions.py plan/deploy --features <phase> (missing: " + ", ".join(missing) + ")")

# --- sharing (read-only EntityDefinition vs spec; ControlledByParent rows need a retrieve to confirm) --------------
try:
    sh = ET.parse(os.path.join(ROOT, "sharing", "aits-step0-sharing.xml")).getroot()
    tg = [t.attrib for t in sh.find("targets")]
    ed = q("SELECT QualifiedApiName, InternalSharingModel, ExternalSharingModel FROM EntityDefinition WHERE QualifiedApiName IN (" + ",".join(f"'{t['object']}'" for t in tg) + ")")
    cur = {r["QualifiedApiName"]: (r["InternalSharingModel"], r["ExternalSharingModel"]) for r in (ed or {}).get("records", [])}
    present = [t for t in tg if t["object"] in cur]
    diff = [t["object"] for t in present if "ControlledByParent" not in (t["internal"], t["external"]) and cur[t["object"]] != (t["internal"], t["external"])]
    cbp = [t["object"] for t in present if "ControlledByParent" in (t["internal"], t["external"])]
    row("S0", "Sharing defaults", f"{len(present)} objects in org · {len(diff)} differ · {len(tg) - len(present)} not in org",
        ("nothing to do" if not diff else "run sharing/apply_owd.py plan → deploy --confirm (differ: " + ", ".join(diff) + ")")
        + (f"; Controlled-by-Parent row(s) {', '.join(cbp)} need sharing/apply_owd.py plan to confirm (EntityDefinition shows inherited values)" if cbp else ""))
except Exception as e:
    row("S0", "Sharing defaults", "check failed", str(e)[:120])

# --- read-only phase checks ----------------------------------------------------------------------------------------
def chk(phase, label, script, *args, ok="all checks PASS", page_note=""):
    rc, out, err = py(script, *args)
    fails = [l.strip() for l in out.splitlines() if " FAIL " in l]
    opts = [l.strip() for l in out.splitlines() if " OPTIONAL " in l]
    state = ok if rc == 0 else ("check failed: " + (out or err)[-120:].strip() if rc == 1 else f"{len(fails)} FAIL")
    action = "nothing to do" if rc == 0 else ("see check output" if rc == 1 else "fix with approval: " + "; ".join(f.split("  ")[0] for f in fails)[:200])
    if opts: action += f" · {len(opts)} optional item(s) not done"
    if page_note: action += " · " + page_note
    row(phase, label, state, action)
chk("3a-3c", "Agentforce agents & Enhanced Chat", "checks/check_agents.py")
chk("5", "SLA Management", "checks/check_sla.py", page_note="page badge 'In Progress' = optional items")
chk("6", "Assignment Rules", "checks/check_assignment_rules.py", page_note="6c: confirm on Assignment Rules page")
chk("7b", "Knowledge readiness", "checks/check_knowledge.py")
chk("11", "CMDB & Service Graph", "checks/check_cmdb.py", page_note="11b/11c: confirm on provisioning + CMDB pages")
if SITE: chk("8", f"Self-service portal ({SITE})", "checks/check_portal.py", "--site", SITE, page_note="8a: confirm on Self Service Portal page")
else:
    rc, out, _ = py("checks/check_portal.py")
    n = sum(1 for l in out.splitlines() if l.startswith("   ") and ("Agentic Center" in l or "Employee Center" in l))
    row("8", "Self-service portal", f"{n} candidate site(s)", "ask the user which site to use (or create one); 8a: confirm on page")
row("10", "Embedded chat on the portal", "10a/10b via Tooling; 10c manual", "follow help article for the widget (manual)")

# --- Data Cloud (last) ------------------------------------------------------------------------------------------------
dc = q("SELECT IsCustomerDataPlatformEnabled FROM CustomerDataPlatformSettings", tooling=True)
dcv = (dc or {}).get("records", [{}])[0].get("IsCustomerDataPlatformEnabled") if dc and dc.get("records") else None
row("9", "Data Cloud (runs LAST) + Data Library", "ON" if dcv else ("OFF" if dcv is False else "unknown"),
    "nothing to do" if dcv else "select to run LAST (10–30 min background install; never cancel Automated Process)")

# --- output -----------------------------------------------------------------------------------------------------------
order = lambda r: (r["phase"] not in ("0",), r["phase"])
lines = [f"# AITS Pre-flight audit — {TS}", "", header, f"Deploy queue: {queue_note}", "",
         "| Phase | Feature | State on this org | Suggested action |", "|---|---|---|---|"]
lines += [f"| {r['phase']} | {r['feature']} | {r['state']} | {r['action']} |" for r in skip]
lines += ["", "Read-only: nothing was changed. Choose the phases to run; each runs plan → user approval → deploy --confirm → verify."]
md = os.path.join(OUTDIR, f"preflight-{TS}.md"); open(md, "w").write("\n".join(lines) + "\n")
json.dump({"ts": TS, "org": o, "user": uname, "queue": {"inflight": inflight, "recent": recent[:5]}, "skipMap": skip},
          open(os.path.join(OUTDIR, f"preflight-{TS}.json"), "w"), indent=2, default=str)
print("\n".join(lines)); print(f"\nwritten: {md}")
