#!/usr/bin/env python3
"""IT Service Cloud permission phases (e.g. 1a-1d PSGs, 4c Unified Catalog, 6b business rules engine) from it-service-cloud-settings.xml <permissions>.
Assigns permission set licences (<psl>), permission sets (<ps>) and permission set groups (<psg>) - in that order -
to the CONNECTED user only (recipe Guardrail #3). Availability-driven: a PSG that does
not exist in the org is skipped (not a failure). An assignment the org rejects (e.g. licence type) is reported, not fatal.
  python3 settings/apply_permissions.py <org-alias> plan   --features ucperms
  python3 settings/apply_permissions.py <org-alias> deploy --features ucperms --confirm
  python3 settings/apply_permissions.py <org-alias> verify --features ucperms
Prerequisites (feature requires=...) are checked against the org via settings/apply_settings.py logic (core flag ON).
Result file: deploy -> permissions-result.md · plan -> permissions-plan.md · verify -> permissions-verify.md (checks never overwrite deploy evidence).
Exit: 0 = all available items assigned · 2 = some not assigned · 1 = abort."""
import json, os, subprocess, sys, time, xml.etree.ElementTree as ET
HERE = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) < 3: sys.exit(__doc__)
ORG, MODE, A = sys.argv[1], sys.argv[2], sys.argv[3:]
CONFIRM = "--confirm" in A
SEL = A[A.index("--features") + 1].split(",") if "--features" in A else None
SPEC = ET.parse(os.path.join(HERE, "it-service-cloud-settings.xml")).getroot()
FEAT = {f.get("id"): f.attrib for g in SPEC.findall("features") for f in g}
def die(m): print("ABORT:", m); sys.exit(1)
def sf(args):
    p = subprocess.run(["sf"] + args + ["--target-org", ORG, "--json"], capture_output=True, text=True)
    try: return json.loads(p.stdout)
    except Exception: return {"status": 1, "message": (p.stderr or p.stdout)[-500:]}
def q(soql):
    d = sf(["data", "query", "-q", soql]); 
    if d.get("status") != 0: die(f"query failed: {d.get('message')}")
    return d["result"]["records"]
def log(ev):
    ev["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(os.path.join(HERE, "permissions-log.jsonl"), "a") as fh: fh.write(json.dumps(ev) + "\n")
if not SEL: die("no features selected - pass --features (e.g. ucperms)")
blocks = [b for b in SPEC.findall("permissions") if b.get("feature") in SEL]
if not blocks: die(f"no <permissions> block for {SEL}")
# prerequisites: core flag of each required feature must be ON in the org (structured status; retrieves only the needed file)
for b in blocks:
    reqs = [r for r in (FEAT[b.get("feature")].get("requires") or "").split(",") if r]
    if not reqs: continue
    env = {k: v for k, v in os.environ.items() if k != "IT_SERVICE_CLOUD_SETTINGS_CACHE"}   # a permission write never rests on a cached read
    p = subprocess.run([sys.executable, os.path.join(HERE, "apply_settings.py"), ORG, "status", "--json", "--features", ",".join(reqs)], capture_output=True, text=True, env=env)
    try: stj = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception: die(f"could not read prerequisite status: {(p.stdout or p.stderr)[-300:]}")
    for req in reqs:
        if (stj.get(req) or {}).get("coreValue") != "true":
            die(f"{FEAT[b.get('feature')]['label']} needs {FEAT[req]['label']} ON first (state: {(stj.get(req) or {}).get('state', 'unknown')})")
u = sf(["org", "display", "user"]); uid = (u.get("result") or {}).get("id") or die("could not read connected user")
rows, bad = [], 0
def do_assign(kind, name, sobject, values):
    """Create one assignment (deploy mode, --confirm required). Logged immediately; rejection reported, not fatal."""
    global bad
    if not CONFIRM: die("deploy requires --confirm (show the plan to the user first)")
    r = sf(["data", "create", "record", "--sobject", sobject, "--values", values])
    ok = r.get("status") == 0
    log({"kind": kind, "name": name, "ok": ok, "message": (r.get("message") or "")[:300]})
    rows.append((f"{kind}:{name}", "assigned" if ok else "not assigned", "✅ assigned" if ok else f"❌ {(r.get('message') or '')[:160]}")); bad += not ok

PSL_OK = set()   # licences assigned (already or in this run) - a <ps requiresPsl="X"> is skipped if X is not here
def handle(kind, name, exists_id, assigned, sobject, values, extra="", needs_psl=None):
    global bad
    label = f"{kind}:{name}"
    if exists_id is None: rows.append((label, "not in org", "skipped (not a failure)")); return
    if needs_psl and needs_psl not in PSL_OK and not assigned:
        rows.append((label, "not assigned", f"not applied - licence {needs_psl} not assigned")); bad += 1; return
    if assigned: rows.append((label, "assigned", "already at target" + extra)); return
    if MODE != "deploy":
        rows.append((label, "not assigned", "WILL ASSIGN" if MODE == "plan" else "❌ not assigned")); bad += MODE == "verify"; return
    do_assign(kind, name, sobject, values)

inlist = lambda xs: "(" + ",".join(f"'{x}'" for x in xs) + ")"
for b in blocks:
    # order: licences -> permission sets -> permission set groups (a permission set may need its licence first)
    psl = [e.get("name") for e in b.findall("psl")]
    if psl:
        ex = {r["DeveloperName"]: r["Id"] for r in q("SELECT Id, DeveloperName FROM PermissionSetLicense WHERE DeveloperName IN " + inlist(psl))}
        hv = {r["PermissionSetLicenseId"] for r in q(f"SELECT PermissionSetLicenseId FROM PermissionSetLicenseAssign WHERE AssigneeId = '{uid}'")}
        for n in psl:
            handle("psl", n, ex.get(n), ex.get(n) in hv, "PermissionSetLicenseAssign", f"AssigneeId={uid} PermissionSetLicenseId={ex.get(n)}")
            if ex.get(n) in hv or (rows and rows[-1][0] == f"psl:{n}" and rows[-1][1] == "assigned") or (MODE == "plan" and ex.get(n)): PSL_OK.add(n)
    ps = [e.get("name") for e in b.findall("ps")]; ps_req = {e.get("name"): e.get("requiresPsl") for e in b.findall("ps")}
    if ps:
        ex = {r["Name"]: r["Id"] for r in q("SELECT Id, Name FROM PermissionSet WHERE IsOwnedByProfile = false AND Name IN " + inlist(ps))}
        hv = {r["PermissionSetId"] for r in q(f"SELECT PermissionSetId FROM PermissionSetAssignment WHERE AssigneeId = '{uid}'")}
        for n in ps: handle("ps", n, ex.get(n), ex.get(n) in hv, "PermissionSetAssignment", f"AssigneeId={uid} PermissionSetId={ex.get(n)}", needs_psl=ps_req.get(n))
    names = [e.get("name") for e in b.findall("psg")]
    if names:
        rp = q("SELECT Id, DeveloperName, Status FROM PermissionSetGroup WHERE DeveloperName IN " + inlist(names))
        ex = {r["DeveloperName"]: r["Id"] for r in rp}; st = {r["DeveloperName"]: r.get("Status") for r in rp}
        hv = {r["PermissionSetGroupId"] for r in q(f"SELECT PermissionSetGroupId FROM PermissionSetAssignment WHERE AssigneeId = '{uid}' AND PermissionSetGroupId != null")}
        for n in names:
            if n in ex and ex[n] not in hv and st.get(n) not in ("Updated", None):
                print(f"WARN {n}: PSG status {st.get(n)} - assignment may be rejected until it finishes updating")
            handle("psg", n, ex.get(n), ex.get(n) in hv, "PermissionSetAssignment", f"AssigneeId={uid} PermissionSetGroupId={ex.get(n)}", f" (PSG status {st.get(n)})")
print(f"{'Item':38} {'state':14} result")
for r in rows: print(f"{r[0]:38} {r[1]:14} {r[2]}")
RESULT = {"deploy": "permissions-result.md", "plan": "permissions-plan.md", "verify": "permissions-verify.md"}.get(MODE, "permissions-other.md")
open(os.path.join(HERE, RESULT), "w").write("| Item | State | Result |\n|---|---|---|\n" + "\n".join(f"| {a} | {b} | {c} |" for a, b, c in rows) + "\n")
sys.exit(2 if bad else 0)
