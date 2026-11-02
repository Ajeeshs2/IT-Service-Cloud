#!/usr/bin/env python3
"""Apply IT Service Cloud feature settings (IT Service Core 1a-1d, Agentforce 3a-3e) from it-service-cloud-settings.xml (bundle with the recipe).
FEATURE-driven: the user picks features (phases); only flags tagged with a selected feature change.
Self-contained: uses its own SFDX work project at settings/_work/ (never touches your project's source).
  python3 settings/apply_settings.py <org-alias> status                          # phases + current state (read-only)
  python3 settings/apply_settings.py <org-alias> plan   --features <ids>|all [--required-only]
        # ids: incident, problem, change, release (IT Service Core) · context, catalog, ucperms (Unified Catalog; ucperms via apply_permissions.py)
        #      platform, fulfiller, employee, proactive, aiextras (Agentforce)
  python3 settings/apply_settings.py <org-alias> deploy --features ... --confirm [--max-deploys N] [--assume-available]
        # REQUIRES --confirm (user-approved plan) - one approval per run. Isolates failing flags by splitting,
        # capped at 3*ceil(log2 n)+1 (+1 per feature in the file) deploys for n changed flags; failures are isolated per feature in dependency order.
        # Flags with requires="..." are skipped as "not available" unless --assume-available.
        # --retry-failed: retry isolated failures once at the end (only useful for flag-order dependencies).
  python3 settings/apply_settings.py <org-alias> verify --features ...
Prerequisites: each selected feature's required features must be selected too or already ON in the org (else abort).
--required-only: change only tier="required" flags of the selected features (default: all flags of the feature).
Availability-driven: flags listed but not present in the org's settings are skipped (not a failure).
Exit: 0 = all selected flags at target · 2 = some flags dropped or not applied because a prerequisite failed
      (see settings/<Setting>-result.md) · 1 = abort (systemic problem, bad input, or prerequisites missing before start).
"""
import json, re, subprocess, sys, time, os, shutil, xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) < 3: sys.exit(__doc__)
ORG, MODE = sys.argv[1], sys.argv[2]
ARGS = sys.argv[3:]
CONFIRM, ASSUME, RETRY = "--confirm" in ARGS, "--assume-available" in ARGS, "--retry-failed" in ARGS
MAX_OVERRIDE = int(ARGS[ARGS.index("--max-deploys") + 1]) if "--max-deploys" in ARGS else None
import math
def deploy_cap(n):
    """Enough deploys to fully isolate up to 2 failing flags (simulated worst case): 3*ceil(log2 n) + 1
    (n=5 -> 10, n=12 -> 13, n=23 -> 16, n=35 -> 19; n=1 -> 1). Normal case (no failures) = 1 deploy."""
    return MAX_OVERRIDE or (3 * math.ceil(math.log2(n)) + 1 if n > 1 else 1)
_VALOPTS = ("--max-deploys", "--features")
_pos = [a for i, a in enumerate(ARGS) if not a.startswith("--") and (i == 0 or ARGS[i - 1] not in _VALOPTS)]
ONLY = _pos[0] if _pos else None   # optional: limit to one settings file
FEAT_ARG = ARGS[ARGS.index("--features") + 1] if "--features" in ARGS else None
REQ_ONLY = "--required-only" in ARGS
STOP = {"flag": False}
import signal
def _stop(sig, frm):
    STOP["flag"] = True; print(f"\nsignal {sig}: finishing current deploy poll, then stopping (no new deploys)")
signal.signal(signal.SIGINT, _stop); signal.signal(signal.SIGTERM, _stop)
SPEC = ET.parse(os.path.join(HERE, "it-service-cloud-settings.xml")).getroot()
API = SPEC.get("apiVersion", "67.0")
SETTINGS = [s for s in SPEC.findall("setting") if not ONLY or s.get("name") == ONLY]
FEATURES = [dict(f.attrib, group=g.get("group", "")) for g in SPEC.findall("features") for f in g]
FEAT_BY_ID = {f["id"]: f for f in FEATURES}
if FEAT_ARG:
    # "all" = every non-optional feature; optional phases (e.g. 3e) run only when named explicitly
    SEL = [f["id"] for f in FEATURES if f.get("optional") != "true"] if FEAT_ARG == "all" else [x.strip() for x in FEAT_ARG.split(",") if x.strip()]
    bad = [x for x in SEL if x not in FEAT_BY_ID]
    if bad: print(f"ABORT: unknown feature(s) {bad}; valid: {list(FEAT_BY_ID)}"); sys.exit(1)
else:
    SEL = None
# mandatory features (e.g. 1e Notification Service) always join a run; if their prerequisite is neither selected
# nor ON they are dropped with a note (see check_prereqs) instead of aborting the run
MANDATORY = [f["id"] for f in FEATURES if f.get("mandatory") == "true"]
if SEL is not None:
    for m in MANDATORY:
        if m not in SEL: SEL.append(m)   # inclusion/skip note is printed in check_prereqs, after the prerequisite decision
_CACHE = {}
BLOCKED_FEATURES = {}   # feature id -> reason; set between files at deploy time (prerequisite core not ON)
LAST_BLOCKED = {}
WORK = os.path.join(HERE, "_work")
POLL_TIMEOUT_S = 1800

def die(m): print("ABORT:", m); sys.exit(1)

def ensure_work():
    os.makedirs(os.path.join(WORK, "force-app"), exist_ok=True)
    pj = os.path.join(WORK, "sfdx-project.json")
    if not os.path.exists(pj):
        json.dump({"packageDirectories": [{"path": "force-app", "default": True}], "name": "it-service-cloud-settings-work", "sourceApiVersion": API}, open(pj, "w"))

def sf(args):
    ensure_work()
    p = subprocess.run(["sf"] + args + ["--target-org", ORG, "--json"], capture_output=True, text=True, cwd=WORK)
    try: return json.loads(p.stdout)
    except Exception: return {"status": 1, "message": (p.stderr or p.stdout)[-800:]}

def safe_rm(d):
    assert os.path.abspath(d).startswith(os.path.abspath(WORK) + os.sep); shutil.rmtree(d, ignore_errors=True)

def prefetch_all():
    """One retrieve for every spec'd settings file (much faster than one retrieve per file)."""
    names = [st.get("name") for st in SPEC.findall("setting") if st.get("name") not in _CACHE]
    if not names: return
    ro = os.environ.get("IT_SERVICE_CLOUD_SETTINGS_CACHE")   # read-only shared cache (pre-flight); only honoured in status mode
    if ro and MODE == "status" and all(os.path.exists(os.path.join(ro, f"{n}.settings-meta.xml")) for n in names):
        for n in names: _CACHE[n] = open(os.path.join(ro, f"{n}.settings-meta.xml")).read()
        return
    d = os.path.join(WORK, "retrieve-all"); safe_rm(d)
    args = ["project", "retrieve", "start", "--output-dir", d, "--wait", "10"]
    for n in names: args += ["-m", f"Settings:{n}"]
    r = sf(args)
    if r.get("status") != 0 or r.get("result", {}).get("status") != "Succeeded": return   # fall back to per-file retrieve
    for n in names:
        f = os.path.join(d, "settings", f"{n}.settings-meta.xml")
        if os.path.exists(f): _CACHE[n] = open(f).read()
    if ro and MODE == "status":
        os.makedirs(ro, exist_ok=True)
        for n in names:
            if n in _CACHE: open(os.path.join(ro, f"{n}.settings-meta.xml"), "w").write(_CACHE[n])

def retrieve_cached(name):
    if name not in _CACHE and not _CACHE.get("__prefetched__"):
        _CACHE["__prefetched__"] = True; prefetch_all()
    if name not in _CACHE: _CACHE[name] = retrieve(name, "before")
    return _CACHE[name]

def org_flag(flag):
    """Current org value of a flag in any spec'd settings file (None if absent)."""
    for st in SPEC.findall("setting"):
        if any(f.get("name") == flag for f in st.findall("flag")):
            return flags_of(retrieve_cached(st.get("name"))).get(flag)
    return None

def feature_state(fid):
    if FEAT_BY_ID[fid].get("kind") == "permissions":
        return "see apply_permissions.py", 0, 0, None
    flags = [(st.get("name"), f) for st in SPEC.findall("setting") for f in st.findall("flag")
             if f.get("feature") == fid and f.get("manage", "true") != "false"]
    vals = [flags_of(retrieve_cached(n)).get(f.get("name")) for n, f in flags]
    pres = [v for v in vals if v is not None]
    on = sum(v == "true" for v in pres)
    core = org_flag(FEAT_BY_ID[fid]["core"]) if FEAT_BY_ID[fid].get("core") else ("true" if on else "false")
    state = "not in org" if not pres else ("ON (all)" if on == len(pres) else ("OFF" if core != "true" else "ON (partial)"))
    return state, on, len(pres), core

def status():
    if "--json" in ARGS:   # machine-readable; with --features only those features' settings files are retrieved
        out = {}
        for f in FEATURES:
            if SEL is not None and f["id"] not in SEL: continue
            st, on, n, core = feature_state(f["id"])
            out[f["id"]] = {"phase": f["phase"], "label": f["label"], "state": st, "on": on, "of": n, "core": f.get("core"), "coreValue": core}
        print(json.dumps(out)); return
    print("Group | Phase | Feature | Requires | State | Flags on")
    for f in FEATURES:
        st, on, n, core = feature_state(f["id"])
        print(f"{f['group']} | {f['phase']} | {f['label']} ({f['id']}){' [optional]' if f.get('optional') == 'true' else ''} | {f.get('requires') or '-'} | {st} | {on}/{n}")
    print("Select with --features <ids>|all (Phase 0 IT Service Enablement must be ON first: checks/check_it_service_enablement.py)")

def check_prereqs():
    missing = []
    for fid in list(SEL):
        if fid in MANDATORY:
            reqs = [r for r in FEAT_BY_ID[fid].get("requires", "").split(",") if r]
            unmet = [r for r in reqs if r not in SEL and FEAT_BY_ID[r].get("core") and org_flag(FEAT_BY_ID[r]["core"]) != "true"]
            if unmet:
                SEL.remove(fid); print(f"NOTE {FEAT_BY_ID[fid]['phase']} {FEAT_BY_ID[fid]['label']} (mandatory) skipped this run: needs {', '.join(FEAT_BY_ID[r]['label'] for r in unmet)} (not selected and not ON)")
            else:
                print(f"NOTE {FEAT_BY_ID[fid]['phase']} {FEAT_BY_ID[fid]['label']} (mandatory) included")
            continue
        for req in [r for r in FEAT_BY_ID[fid].get("requires", "").split(",") if r]:
            if req not in SEL and FEAT_BY_ID[req].get("core") and org_flag(FEAT_BY_ID[req]["core"]) != "true":
                missing.append(f"{FEAT_BY_ID[fid]['label']} needs {FEAT_BY_ID[req]['label']} (not selected and not ON in org)")
    if missing: die("prerequisites not met: " + "; ".join(missing) + " - add the feature to --features or ask the user")
    print("prerequisites OK for:", ", ".join(FEAT_BY_ID[x]["label"] for x in SEL))

def in_scope(f):
    return SEL is not None and f.get("feature") in SEL and (not REQ_ONLY or f.get("tier") == "required")

def retrieve(name, tag):
    d = os.path.join(WORK, f"retrieve-{tag}"); safe_rm(d)
    r = sf(["project", "retrieve", "start", "-m", f"Settings:{name}", "--output-dir", d, "--wait", "10"])
    if r.get("status") != 0 or r.get("result", {}).get("status") != "Succeeded": die(f"retrieve Settings:{name} failed: {r.get('message')}")
    f = os.path.join(d, "settings", f"{name}.settings-meta.xml")
    if not os.path.exists(f): die(f"Settings:{name} not returned by org")
    return open(f).read()

def flags_of(xml): return dict(re.findall(r"<(\w+)>(true|false)</\1>", xml))

def with_flags(xml, flags):
    for k, v in flags.items():
        n = len(re.findall(f"<{k}>(?:true|false)</{k}>", xml))
        if n != 1: die(f"flag {k} appears {n} times in the retrieved settings file (expected exactly 1) - refusing to patch; fix the spec")
        xml = re.sub(f"<{k}>(true|false)</{k}>", f"<{k}>{v}</{k}>", xml)
    return xml

def wait_queue():
    t0 = time.time()
    while True:
        d = sf(["data", "query", "--use-tooling-api", "-q", "SELECT Id, Status, CreatedBy.Name FROM DeployRequest WHERE Status IN ('Pending','InProgress')"])
        recs = (d.get("result") or {}).get("records", [])
        if not recs: return
        for r in recs: print("in-flight deploy:", r["Id"], r["Status"], (r.get("CreatedBy") or {}).get("Name"), "- waiting (never cancel)")
        if time.time() - t0 > POLL_TIMEOUT_S: die("deploy queue busy after timeout (do NOT cancel Automated Process deploys)")
        time.sleep(30)

def log_event(name, ev):
    """Append immediately so an interrupt never loses what already ran."""
    f = os.path.join(HERE, f"{name}-deploy-log.jsonl")
    ev["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(f, "a") as fh: fh.write(json.dumps(ev) + "\n")

def deploy_xml(name, xml):
    """Deploy one settings file. Returns (ok, problem_text, job_id)."""
    d = os.path.join(WORK, "force-app", "main", "default", "settings"); os.makedirs(d, exist_ok=True)
    f = os.path.join(d, f"{name}.settings-meta.xml"); open(f, "w").write(xml)
    wait_queue()
    r = sf(["project", "deploy", "start", "--source-dir", f, "--async"])
    jid = r.get("result", {}).get("id")
    if not jid: die(f"deploy not submitted (systemic): {r.get('message')}")
    log_event(name, {"event": "submitted", "job": jid})
    t0 = time.time()
    while True:
        time.sleep(15)
        rep = sf(["project", "deploy", "report", "--job-id", jid]); res = rep.get("result", {})
        if res.get("done") or res.get("status") in ("Succeeded", "Failed", "Canceled", "SucceededPartial"): break
        if time.time() - t0 > POLL_TIMEOUT_S: die(f"poll timeout on {jid} (do NOT cancel Automated Process deploys)")
    fails = (res.get("details") or {}).get("componentFailures") or []
    fails = fails if isinstance(fails, list) else [fails]
    prob = "; ".join(str(x.get("problem")) for x in fails)
    log_event(name, {"event": "finished", "job": jid, "status": res.get("status"), "problem": prob})
    if res.get("status") != "Succeeded" and not fails: die(f"deploy {jid} {res.get('status')} without component failures - systemic")
    return res.get("status") == "Succeeded", prob, jid

def plan_one(s):
    name = s.get("name"); cur_xml = retrieve_cached(name); cur = flags_of(cur_xml)
    json.dump(cur, open(os.path.join(HERE, f"{name}-before.json"), "w"), indent=2)
    flags = [f for f in s.findall("flag") if f.get("manage", "true") != "false" and in_scope(f)]
    out_of_scope = [f.get("name") for f in s.findall("flag") if not in_scope(f) and f.get("manage", "true") != "false"]
    unavailable = {f.get("name"): f.get("requires") for f in flags if f.get("requires") and not ASSUME}
    prereq_blocked = {}
    here = {f.get("name") for f in s.findall("flag")}
    for f in flags:   # flag-level prerequisite, e.g. Problem flags of the Proactive Assistant
        rf = f.get("requiresFeature")
        if not rf: continue
        core = FEAT_BY_ID[rf]["core"]
        if org_flag(core) == "true": continue
        # Selected prerequisite counts only if it will be applied in THIS file's deploy (re-checked per feature
        # during isolation) or we are only planning. At deploy time a core from an EARLIER file must already be ON.
        if rf in SEL and (core in here or MODE == "plan"): continue
        prereq_blocked[f.get("name")] = FEAT_BY_ID[rf]["label"]
    for f in flags:   # whole feature blocked because a prerequisite in an EARLIER file did not turn ON
        if f.get("feature") in BLOCKED_FEATURES and f.get("name") not in prereq_blocked:
            prereq_blocked[f.get("name")] = BLOCKED_FEATURES[f.get("feature")].split("prerequisite ", 1)[-1].replace(" is not ON", "")
    LAST_BLOCKED.clear(); LAST_BLOCKED.update({k: f"not applied - prerequisite {v} is not ON" for k, v in prereq_blocked.items()})
    want = {f.get("name"): f.get("target") for f in flags if f.get("name") not in unavailable and f.get("name") not in prereq_blocked}
    unmanaged = [f.get("name") for f in s.findall("flag") if f.get("manage") == "false"]
    absent = [k for k in want if k not in cur]
    change = {k: v for k, v in want.items() if k in cur and cur[k] != v}
    extra = [k for k in cur if k not in want and k not in out_of_scope and k not in unmanaged and k not in prereq_blocked and k not in unavailable]
    for k in unmanaged: print(f"   not managed (manage=false): {k}={cur.get(k, 'not in org')}")
    for k, req in unavailable.items(): print(f"   not available (requires {req}; use --assume-available to try): {k}")
    for k, lab in prereq_blocked.items(): print(f"   not applied - prerequisite {lab} is not selected or ON: {k}")
    reductions = [k for k, v in change.items() if cur[k] == "true" and v == "false"]
    if reductions: print(f"   REDUCTIONS (true->false) - user must approve: {reductions}")
    nfeat = len({f.get("feature") for f in s.findall("flag") if f.get("name") in change})
    print(f"   deploys: 1 if all succeed; up to {deploy_cap(len(change)) + nfeat if change else 0} (cap: {len(change)} flags, {nfeat} features) if failures need isolating")
    print(f"== {name}: {len(cur)} flags in org · {len(change)} to change · {len(want) - len(change) - len(absent)} already at target · {len(absent)} not in org (skipped) · {len(extra)} unlisted (preserved)")
    for k, v in change.items(): print(f"   {k}: {cur[k]} -> {v}")
    for k in absent: print(f"   skip (not in org): {k}")
    for k in extra: print(f"   preserved (not in spec): {k}={cur[k]}")
    if out_of_scope: print(f"   preserved (feature not selected): {len(out_of_scope)} flags")
    return name, cur_xml, change

def deploy_one(s):
    name, base, change = plan_one(s)
    pre_dropped = dict(LAST_BLOCKED)
    if not change: print("nothing to change"); return verify_one(s, pre_dropped)
    if not CONFIRM: die("deploy requires --confirm (show the plan above to the user and get approval first)")
    applied, dropped, log = {}, {}, []
    count = {"n": 0}; MAX_DEPLOYS = deploy_cap(len(change)) + len({f.get("feature") for f in s.findall("flag") if f.get("name") in change})
    def attempt(batch, known_fail=False, split=True):
        """Split-and-retry. known_fail=True: parent failed and sibling half succeeded, so this batch
        must contain a failing flag - skip deploying it whole and split straight away (saves 1 deploy per level)."""
        nonlocal base
        if not known_fail:
            if STOP["flag"] or count["n"] >= MAX_DEPLOYS:
                why = "stopped by signal" if STOP["flag"] else f"deploy cap {MAX_DEPLOYS} reached"
                dropped.update({k: f"not attempted - {why}" for k in batch}); return False
            count["n"] += 1
            ok, prob, jid = deploy_xml(name, with_flags(base, batch))
            log.append({"job": jid, "flags": sorted(batch), "ok": ok, "problem": prob}); print(f"   deploy {jid}: {'Succeeded' if ok else 'Failed'} ({len(batch)} flags) {prob[:200]}")
            if ok: base = with_flags(base, batch); applied.update(batch); return True
            last_problem[0] = prob
            if not split: return False   # single try only (top-level whole-batch attempt)
        if len(batch) == 1: dropped.update({k: last_problem[0] for k in batch}); return False
        items = sorted(batch.items()); mid = len(items) // 2
        first_ok = attempt(dict(items[:mid]))
        attempt(dict(items[mid:]), known_fail=first_ok)
        return False
    last_problem = [""]
    # Normal case: one deploy with everything. On failure, isolate along FEATURE boundaries in dependency
    # order (spec order: incident -> problem -> change -> release), so a dependent feature is never applied
    # while its prerequisite failed. Inside a feature, split-and-retry as usual.
    feat_of = {f.get("name"): f.get("feature") for f in s.findall("flag")}
    rf_of = {f.get("name"): f.get("requiresFeature") for f in s.findall("flag") if f.get("requiresFeature")}
    if not attempt(change, split=False):
        dropped.clear()  # the whole-batch failure is not a verdict on individual flags
        order = [f["id"] for f in FEATURES]
        for fid in order:
            group = {k: v for k, v in change.items() if feat_of.get(k) == fid and k not in applied}
            for k in list(group):   # flag-level prerequisite inside the same file
                rf = rf_of.get(k)
                if rf and flags_of(base).get(FEAT_BY_ID[rf]["core"]) != "true" and org_flag(FEAT_BY_ID[rf]["core"]) != "true":
                    dropped[k] = f"not applied - prerequisite {FEAT_BY_ID[rf]['label']} is not ON"; group.pop(k)
            if not group: continue
            reqs = [r for r in FEAT_BY_ID[fid].get("requires", "").split(",") if r]
            blocked = [r for r in reqs if FEAT_BY_ID[r].get("core") and flags_of(base).get(FEAT_BY_ID[r]["core"]) != "true" and org_flag(FEAT_BY_ID[r]["core"]) != "true"]
            if blocked:
                why = "not applied - prerequisite " + ", ".join(FEAT_BY_ID[r]["label"] for r in blocked) + " is not ON"
                dropped.update({k: why for k in group}); print(f"   {FEAT_BY_ID[fid]['label']}: {why}"); continue
            attempt(group)
    if RETRY and dropped and not STOP["flag"] and count["n"] < MAX_DEPLOYS:  # optional: retry once (flag dependencies)
        retry = {k: change[k] for k in dropped if not dropped[k].startswith(("not attempted", "not applied"))}
        if retry:
            for k in retry: dropped.pop(k)
            print("   retrying failed flags once:", sorted(retry)); attempt(retry)
    print(f"   deploys used: {count['n']} / cap {MAX_DEPLOYS}")
    json.dump(log, open(os.path.join(HERE, f"{name}-deploy-log.json"), "w"), indent=2)
    dropped.update(pre_dropped)
    return verify_one(s, dropped)

def verify_one(s, dropped):
    name = s.get("name"); after = flags_of(retrieve(name, "after"))
    json.dump(after, open(os.path.join(HERE, f"{name}-after.json"), "w"), indent=2)
    bf = os.path.join(HERE, f"{name}-before.json"); before = json.load(open(bf)) if os.path.exists(bf) else {}
    rows = [f"# {name} settings - result (features: {','.join(SEL) if SEL else 'all'})", "", "| Flag | Feature/Tier | Label | Before | Target | After | Result |", "|---|---|---|---|---|---|---|"]
    ok = mism = skipped = 0
    for f in s.findall("flag"):
        k, t = f.get("name"), f.get("target")
        if SEL is not None and not in_scope(f) and f.get("manage") != "false":
            rows.append(f"| {k} | {f.get('feature')}/{f.get('tier')} | {f.get('label')} | {before.get(k, '?')} | not selected | {after.get(k, 'not in org')} | ⏸ feature not selected (unchanged) |"); continue
        if f.get("manage") == "false": rows.append(f"| {k} | {f.get('tier')} | {f.get('label')} | {before.get(k, '?')} | not managed | {after.get(k, 'not in org')} | ⏸ not managed ({f.get('note', '')[:80]}) |"); continue
        if k not in after: skipped += 1; rows.append(f"| {k} | {f.get('tier')} | {f.get('label')} | - | {t} | not in org | ⏭ skipped |"); continue
        res = "✅" if after[k] == t else "❌ " + (dropped.get(k, "mismatch")[:120])
        ok += after[k] == t; mism += after[k] != t
        rows.append(f"| {k} | {f.get('feature')}/{f.get('tier')} | {f.get('label')} | {before.get(k, '?')} | {t} | {after[k]} | {res} |")
    rows.append(f"\nPresent: {ok + mism} · At target: {ok} · Not at target: {mism} · Not in org (skipped): {skipped}")
    open(os.path.join(HERE, f"{name}-result.md"), "w").write("\n".join(rows)); print("\n".join(rows[-1:]))
    return mism

def scoped_settings():
    return [s for s in SETTINGS if any(in_scope(f) for f in s.findall("flag"))]

def main():
    if MODE == "status": return status()
    if SEL is None:
        status(); die("no features selected - ask the user which phases to run, then pass --features")
    check_prereqs()
    for fid in SEL:
        if FEAT_BY_ID[fid].get("kind") == "permissions":
            print(f"NOTE {FEAT_BY_ID[fid]['phase']} {FEAT_BY_ID[fid]['label']}: permissions phase - not done by this script. "
                  f"Run: python3 settings/apply_permissions.py <org> {MODE} --features {fid}" + (" --confirm" if MODE == "deploy" else ""))
    todo = scoped_settings()   # spec order = dependency order (IncidentMgmt before ReleaseMgmt)
    if MODE == "plan":
        for s in todo: plan_one(s)
    elif MODE in ("deploy", "verify"):
        bad = 0
        for i, s in enumerate(todo):
            if MODE == "deploy" and i > 0:
                _CACHE.clear()  # re-read the org (prefetch marker cleared too -> fresh retrieve): an earlier file may have turned a prerequisite ON (or failed to)
                here = {f.get("name") for f in s.findall("flag")}
                blocked = {}
                for fid in {f.get("feature") for f in s.findall("flag") if in_scope(f)}:
                    for req in [r for r in FEAT_BY_ID[fid].get("requires", "").split(",") if r]:
                        if FEAT_BY_ID[req].get("core") and FEAT_BY_ID[req]["core"] not in here and org_flag(FEAT_BY_ID[req]["core"]) != "true":
                            blocked[fid] = f"not applied - prerequisite {FEAT_BY_ID[req]['label']} is not ON"
                BLOCKED_FEATURES.update(blocked)
                grew = True
                while grew:  # transitive: a feature that needs a blocked feature is blocked too (e.g. proactive -> fulfiller)
                    grew = False
                    for f2 in FEATURES:
                        if f2["id"] in SEL and f2["id"] not in BLOCKED_FEATURES:
                            hit = [r for r in (f2.get("requires") or "").split(",") if r in BLOCKED_FEATURES]
                            if hit:
                                BLOCKED_FEATURES[f2["id"]] = f"not applied - prerequisite {FEAT_BY_ID[hit[0]]['label']} is not ON"
                                if any(in_scope(x) and x.get("feature") == f2["id"] for x in s.findall("flag")): blocked[f2["id"]] = BLOCKED_FEATURES[f2["id"]]
                                grew = True
                if blocked:  # report, don't fail (RC-44): mark, write the result file, continue, exit 2
                    for fid, why in blocked.items(): print(f"   {FEAT_BY_ID[fid]['label']}: {why}")
                    json.dump(flags_of(retrieve_cached(s.get("name"))), open(os.path.join(HERE, f"{s.get('name')}-before.json"), "w"), indent=2)
                    dropped = {f.get("name"): blocked[f.get("feature")] for f in s.findall("flag") if in_scope(f) and f.get("feature") in blocked}
                    if all(f.get("feature") in blocked for f in s.findall("flag") if in_scope(f)):
                        bad += max(1, verify_one(s, dropped)); continue
            bad += deploy_one(s) if MODE == "deploy" else verify_one(s, {})
        sys.exit(2 if bad else 0)
    else: sys.exit(__doc__)

main()
