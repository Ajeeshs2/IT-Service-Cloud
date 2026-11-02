#!/usr/bin/env python3
"""Apply AITS Step 0 OWD from aits-step0-sharing.xml (bundle with the recipe).
Self-contained: creates and uses its own SFDX work project at sharing/_work/ (never touches your project's source).
  python3 sharing/apply_owd.py <org-alias> plan              # snapshot + fresh retrieve + patch + report (no org change)
  python3 sharing/apply_owd.py <org-alias> deploy [--confirm] # Level 1 programmatic deploy; failed rows -> browser-fallback.md (exit 2)
  python3 sharing/apply_owd.py <org-alias> verify            # verify only
--confirm is REQUIRED when plan found access reductions. Invalid spec rows abort the run.
Objects not present in the connected org are skipped and reported - never a failure.
Exit codes: 0 = all present objects at target; 2 = some rows need Level 2 (browser) - see browser-fallback.md; 1 = abort.
"""
import json, re, subprocess, sys, time, os, shutil, xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) < 3: sys.exit(__doc__)
ORG, MODE, CONFIRM = sys.argv[1], sys.argv[2], "--confirm" in sys.argv
SPEC = ET.parse(os.path.join(HERE, "aits-step0-sharing.xml")).getroot()
TARGETS = [t.attrib for t in SPEC.find("targets")]
INHERITED = [o.get("name") for inh in SPEC.findall("inherited") for o in inh]
WORK = os.path.join(HERE, "_work")                      # script-owned SFDX project; only this folder is ever deleted from
RETR = os.path.join(WORK, "retrieved-before")
PATCH = os.path.join(WORK, "force-app", "main", "default", "objects")
STATE = os.path.join(HERE, "plan-state.json")
RANK = {"Private": 0, "ControlledByParent": None, "Read": 1, "ReadWrite": 2, "ReadWriteTransfer": 3, "FullAccess": 4}
POLL_TIMEOUT_S = 1800

def ensure_work():
    os.makedirs(os.path.join(WORK, "force-app"), exist_ok=True)
    pj = os.path.join(WORK, "sfdx-project.json")
    if not os.path.exists(pj):
        json.dump({"packageDirectories": [{"path": "force-app", "default": True}], "name": "aits-owd-work",
                   "sourceApiVersion": SPEC.get("apiVersion", "67.0")}, open(pj, "w"))

def sf(args):
    ensure_work()
    p = subprocess.run(["sf"] + args + ["--target-org", ORG, "--json"], capture_output=True, text=True, cwd=WORK)
    try: return json.loads(p.stdout)
    except Exception: return {"status": 1, "message": (p.stderr or p.stdout)[-800:]}

def die(msg): print("ABORT:", msg); sys.exit(1)

def owd(extra=()):
    names = ",".join(f"'{o}'" for o in sorted({t['object'] for t in TARGETS} | set(extra)))
    d = sf(["data", "query", "-q", f"SELECT QualifiedApiName, InternalSharingModel, ExternalSharingModel FROM EntityDefinition WHERE QualifiedApiName IN ({names})"])
    if d.get("status") != 0: die(f"EntityDefinition query failed: {d.get('message')}")
    return {r["QualifiedApiName"]: (r["InternalSharingModel"], r["ExternalSharingModel"]) for r in d["result"]["records"]}

def read_stored(obj):
    f = os.path.join(RETR, "objects", obj, f"{obj}.object-meta.xml")
    if not os.path.exists(f): return None
    s = open(f).read()
    g = lambda tag: (re.search(f"<{tag}>([^<]+)</{tag}>", s) or [None, None])[1]
    return g("sharingModel"), g("externalSharingModel")

def reduction(cur, want):
    """Return list of 'internal'/'external' that get less permissive. Leaving ControlledByParent = model change."""
    out = []
    for i, side in enumerate(("internal", "external")):
        c, w = cur[i], want[i]
        if c is None or c == w: continue
        if RANK.get(c) is None or RANK.get(w) is None: out.append(f"{side}:{c}->{w} (model change)"); continue
        if RANK[w] < RANK[c]: out.append(f"{side}:{c}->{w}")
    return out

UI = {"ReadWrite": "Public Read/Write", "Read": "Public Read Only", "Private": "Private", "ControlledByParent": "Controlled by Parent"}

def validate(t):
    """Return (block_reason, warning). Only spec errors block; approved combos only warn."""
    i, e = t["internal"], t["external"]
    if RANK.get(i) is not None and RANK.get(e) is not None and RANK[e] > RANK[i]:
        return "invalid spec: External more permissive than Internal", None
    if i == "ControlledByParent" and e != "ControlledByParent":
        return None, "Internal=ControlledByParent with External=" + e + " (user-approved; if the org rejects it the row goes to browser fallback)"
    return None, None

def plan():
    before = owd(INHERITED); json.dump(before, open(os.path.join(HERE, "owd-before.json"), "w"), indent=2)
    present = [t for t in TARGETS if t["object"] in before]
    deployable = [t for t in present if t["deployAs"] == "self"]
    # P1: always start from a clean retrieve; abort if it fails
    ensure_work()
    for d in (RETR, PATCH):  # both are inside WORK (script-owned) - safe to clear
        assert os.path.abspath(d).startswith(os.path.abspath(WORK) + os.sep)
        shutil.rmtree(d, ignore_errors=True)
    args = ["project", "retrieve", "start", "--output-dir", RETR, "--wait", "10"]
    for t in deployable: args += ["-m", f"CustomObject:{t['object']}"]
    r = sf(args)
    if r.get("status") != 0 or r.get("result", {}).get("status") != "Succeeded": die(f"retrieve failed: {r.get('message') or r.get('result', {}).get('status')}")
    rows, todo, reductions, blocked = [], [], [], []
    for t in TARGETS:
        o = t["object"]; want = (t["internal"], t["external"])
        if o not in before: rows.append((o, "not in org", "-", "skipped (not a failure)")); continue
        if t["deployAs"] != "self": rows.append((o, before[o], read_stored(o), f"follows {t['deployAs']}")); continue
        cur = read_stored(o)
        if cur is None: die(f"{o}: object-meta.xml missing from fresh retrieve")
        if cur == want: rows.append((o, before[o], cur, "already at target")); continue
        blk, warn = validate(t)
        if blk: blocked.append((o, blk)); rows.append((o, before[o], cur, blk.upper())); continue
        if warn: print("WARN", o, warn)
        s = open(os.path.join(RETR, "objects", o, f"{o}.object-meta.xml")).read()
        s = re.sub(r"<sharingModel>[^<]+</sharingModel>", f"<sharingModel>{want[0]}</sharingModel>", s)
        if "<externalSharingModel>" in s:
            s = re.sub(r"<externalSharingModel>[^<]+</externalSharingModel>", f"<externalSharingModel>{want[1]}</externalSharingModel>", s)
        else:
            s = s.replace("<sharingModel>", f"<externalSharingModel>{want[1]}</externalSharingModel>\n    <sharingModel>", 1)
        os.makedirs(os.path.join(PATCH, o), exist_ok=True)
        open(os.path.join(PATCH, o, f"{o}.object-meta.xml"), "w").write(s)
        red = reduction(cur, want)
        if red: reductions.append((o, red))
        todo.append(o); rows.append((o, before[o], cur, f"PATCH -> {want}" + (f" [REDUCES {', '.join(red)}]" if red else "")))
    for r_ in rows: print(" | ".join(map(str, r_)))
    json.dump({"todo": todo, "reductions": reductions, "blocked": blocked}, open(STATE, "w"), indent=2)
    absent = [t["object"] for t in TARGETS if t["object"] not in before]
    print(f"\npatched {len(todo)} · reductions {len(reductions)} · blocked {len(blocked)} · not in org (skipped) {len(absent)}")
    if reductions or blocked:
        print("Confirm with the user, then run: deploy --confirm")
    print("Inherited from Account (will follow any Account change): " + ", ".join(f"{o}={before.get(o)}" for o in INHERITED if o in before))

def wait_queue(max_wait_s=POLL_TIMEOUT_S):
    """Wait while any deploy is in flight. NEVER cancels anything (esp. Automated Process / Data Cloud ssot install)."""
    t0 = time.time()
    while True:
        d = sf(["data", "query", "--use-tooling-api", "-q", "SELECT Id, Status, CreatedBy.Name FROM DeployRequest WHERE Status IN ('Pending','InProgress')"])
        recs = (d.get("result") or {}).get("records", [])
        if not recs: return
        for r in recs: print("in-flight deploy:", r["Id"], r["Status"], (r.get("CreatedBy") or {}).get("Name"), "- waiting (never cancel)")
        if time.time() - t0 > max_wait_s: die("deploy queue still busy after timeout; retry later (do NOT cancel Automated Process deploys)")
        time.sleep(30)

def submit(objs):
    """Deploy object-meta.xml files (atomic). Returns (status, failed_object_names, job_id)."""
    wait_queue()
    args = ["project", "deploy", "start", "--async"]
    for o in objs: args += ["--source-dir", os.path.join(PATCH, o, f"{o}.object-meta.xml")]
    r = sf(args); jid = r.get("result", {}).get("id"); print("deploy submitted:", jid, objs if len(objs) < 4 else f"{len(objs)} objects", r.get("message", ""))
    if not jid: die(f"deploy not submitted (systemic - e.g. auth/connection): {r.get('message')}")
    t0 = time.time()
    while True:
        time.sleep(20)
        rep = sf(["project", "deploy", "report", "--job-id", jid]); res = rep.get("result", {})
        print(time.strftime("%H:%M:%S"), res.get("status"), res.get("numberComponentsDeployed"), "/", res.get("numberComponentsTotal"))
        if res.get("done") or res.get("status") in ("Succeeded", "Failed", "Canceled", "SucceededPartial"): break
        if time.time() - t0 > POLL_TIMEOUT_S: die(f"poll timeout; check job {jid} (do NOT cancel Automated Process deploys)")
    json.dump(rep, open(os.path.join(HERE, f"deploy-result-{jid}.json"), "w"), indent=2)
    fails = (res.get("details") or {}).get("componentFailures") or []
    fails = fails if isinstance(fails, list) else [fails]
    for f in fails: print("FAIL", f.get("fullName"), f.get("problem"))
    failed = sorted({f.get("fullName") for f in fails if f.get("fullName") in objs})
    status = res.get("status")
    if status != "Succeeded" and not failed:  # no component-level failure -> systemic (timeout/auth/queue); browser won't help
        die(f"deploy {jid} {status} without component failures - systemic issue; fix and re-run (do NOT cancel Automated Process deploys)")
    LOG.append({"jobId": jid, "status": status, "objects": objs, "failed": failed})
    return status, failed, jid

LOG = []

def deploy():
    """Level 1 = programmatic. Failures are isolated and handed to Level 2 (browser) - the run does not stop."""
    st = json.load(open(STATE)); todo = list(st["todo"])
    if st["reductions"] and not CONFIRM: die("plan has access reductions; re-run with --confirm after user approval")
    if st["blocked"]: die("plan has invalid spec rows (External more permissive than Internal): " + str(st["blocked"]) + " - fix aits-step0-sharing.xml; the UI cannot apply them either")
    fallback = {}
    remaining = todo
    for attempt in range(3):  # atomic deploy: drop failed objects and redeploy the rest
        if not remaining: break
        status, failed, jid = submit(remaining)
        if status == "Succeeded": remaining = []; break
        for o in failed: fallback[o] = f"programmatic deploy failed (job {jid})"
        remaining = [o for o in remaining if o not in failed]
    for o in remaining: fallback[o] = "programmatic deploy not completed"
    mism = verify()
    if mism:  # reductions apply after async sharing recalculation (~2 min observed)
        print("mismatches found - re-checking in 120s (sharing recalculation)"); time.sleep(120); mism = verify()
    after = json.load(open(os.path.join(HERE, "owd-after.json")))
    for t in TARGETS:
        o = t["object"]
        if o in after and tuple(after[o]) != (t["internal"], t["external"]) and o not in fallback:
            fallback[o] = "still mismatched after programmatic deploy + recalculation wait"
    json.dump(LOG, open(os.path.join(HERE, "deploy-log.json"), "w"), indent=2)
    write_fallback(fallback)
    if fallback: print(f"LEVEL 2 REQUIRED: {len(fallback)} row(s) -> sharing/browser-fallback.md"); sys.exit(2)
    print("ALL PRESENT OBJECTS AT TARGET - no browser fallback needed")

def write_fallback(fb):
    path = os.path.join(HERE, "browser-fallback.md")
    if not fb:
        open(path, "w").write("# Browser fallback\n\nNot needed - all present objects reached target programmatically.\n"); return
    by = {t["object"]: t for t in TARGETS}
    lines = ["# Browser fallback (Level 2) - Step 0 Sharing", "",
             "Setup > Sharing Settings (`/lightning/setup/SecuritySharing/home`) > **Edit** next to Organization-Wide Sharing Defaults.",
             "Set Internal first, then External. Change ONLY these rows, then **Save**. If Save errors on rows not listed here: STOP and ask the user. If Save is rejected for a listed row (e.g. Inventory Reservation Controlled by Parent / Private): STOP and ask the user - do not change the values.", "",
             "| UI row | Default Internal Access | Default External Access | Reason |", "|---|---|---|---|"]
    for o, why in fb.items():
        t = by[o]; lines.append(f"| {t['uiLabel']} | {UI[t['internal']]} | {UI[t['external']]} | {why} |")
    lines += ["", "After saving, re-run: `python3 sharing/apply_owd.py <org> verify` (allow ~2 min for recalculation)."]
    open(path, "w").write("\n".join(lines))

def stored_now(objs):
    """EntityDefinition shows inherited values for ControlledByParent objects - re-retrieve those to verify."""
    if not objs: return {}
    d = os.path.join(WORK, "verify-retrieve"); shutil.rmtree(d, ignore_errors=True)
    args = ["project", "retrieve", "start", "--output-dir", d, "--wait", "10"]
    for o in objs: args += ["-m", f"CustomObject:{o}"]
    r = sf(args)
    if r.get("status") != 0: die(f"verify retrieve failed: {r.get('message')}")
    out = {}
    for o in objs:
        f = os.path.join(d, "objects", o, f"{o}.object-meta.xml")
        if os.path.exists(f):
            s_ = open(f).read(); g = lambda tag: (re.search(f"<{tag}>([^<]+)</{tag}>", s_) or [None, None])[1]
            out[o] = (g("sharingModel"), g("externalSharingModel"))
    return out

def verify():
    after = owd(INHERITED)
    cbp = [t["object"] for t in TARGETS if t["object"] in after and "ControlledByParent" in (t["internal"], t["external"])]
    for o, v in stored_now(cbp).items(): after[o] = v
    json.dump(after, open(os.path.join(HERE, "owd-after.json"), "w"), indent=2)
    bf = os.path.join(HERE, "owd-before.json"); before = json.load(open(bf)) if os.path.exists(bf) else {}
    ok = mism = skipped = 0; out = ["| Object | Before (Int/Ext) | Target | After (Int/Ext) | Result |", "|---|---|---|---|---|"]
    for t in TARGETS:
        o = t["object"]; want = (t["internal"], t["external"])
        if o not in after: skipped += 1; out.append(f"| {o} | not in org | {want[0]}/{want[1]} | not in org | ⏭ skipped (not a failure) |"); continue
        a = tuple(after[o]); b = tuple(before.get(o, ("?", "?")))
        res = "✅ match" if a == want else "❌ mismatch"; ok += a == want; mism += a != want
        out.append(f"| {o} | {b[0]}/{b[1]} | {want[0]}/{want[1]} | {a[0]}/{a[1]} | {res} |")
    if INHERITED:
        out += ["", "Inherited from Account (informational, not changed directly):", "| Object | Before (Int/Ext) | After (Int/Ext) |", "|---|---|---|"]
        for o in INHERITED:
            if o in after: b = before.get(o, ("?", "?")); out.append(f"| {o} | {b[0]}/{b[1]} | {after[o][0]}/{after[o][1]} |")
    out.append(f"\nPresent in org: {ok + mism} · Matches: {ok} · Mismatches: {mism} · Not in org (skipped): {skipped}")
    open(os.path.join(HERE, "owd-verify.md"), "w").write("\n".join(out)); print("\n".join(out))
    return mism

{"plan": plan, "deploy": deploy, "verify": verify}.get(MODE, lambda: sys.exit(__doc__))()
