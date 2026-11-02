#!/usr/bin/env python3
"""IT Service Cloud Agentforce agent checks (phases 3a-3c) - READ-ONLY. Reports PASS / FAIL / N/A with a fix hint; changes nothing.
Usage: python3 checks/check_agents.py <org-alias> [--features platform,fulfiller,employee] [--json out.json]
Agents are DISCOVERED, never hard-coded (RC-9):
  - Fulfiller = BotDefinition whose AgentTemplate ends with 'ITSrvcMgmtFulfiller' (any DeveloperName).
  - Employee  = the agent targeted by the Enhanced Chat routing flow RouteMsgsItEmpAgent.
  Other agents (e.g. IT_Service_Employee, Agentforce Default) are ignored if present.
Exit: 0 = all selected checks PASS · 2 = some FAIL (fix with user approval) · 1 = check could not run.
"""
import json, re, subprocess, sys
if len(sys.argv) < 2: sys.exit(__doc__)
ORG = sys.argv[1]; A = sys.argv[2:]
SEL = (A[A.index("--features") + 1].split(",") if "--features" in A else ["platform", "fulfiller", "employee"])
OUT = A[A.index("--json") + 1] if "--json" in A else None
WIZARD = "/AiCopilot/copilotStudio.app#/copilot/wizard?mode=svc_itsm_intelligence__ITSrvcMgmtFulfiller"
ITSVC_PAGE = "/lightning/setup/page/feature/service-cloud-agentforce-for-itsm/home?topic=SalesforceGo"

def q(soql, tooling=False):
    cmd = ["sf", "data", "query", "--target-org", ORG, "-q", soql, "--json"] + (["--use-tooling-api"] if tooling else [])
    p = subprocess.run(cmd, capture_output=True, text=True)
    try: d = json.loads(p.stdout)
    except Exception: return None
    return d["result"]["records"] if d.get("status") == 0 else None

rows = []
def add(phase, check, ok, detail, fix=""):
    st = "N/A" if ok is None else ("PASS" if ok else "FAIL")
    rows.append({"phase": phase, "check": check, "status": st, "detail": detail, "fix": "" if ok else fix})

me = subprocess.run(["sf", "org", "display", "user", "--target-org", ORG, "--json"], capture_output=True, text=True)
try: uid = json.loads(me.stdout)["result"]["id"]
except Exception: print("could not read connected user"); sys.exit(1)
assigned = {r["PermissionSet"]["Name"] for r in (q(f"SELECT PermissionSet.Name FROM PermissionSetAssignment WHERE AssigneeId = '{uid}'") or [])}
bots = {r["Id"]: r for r in (q("SELECT Id, DeveloperName, MasterLabel, AgentType, AgentTemplate FROM BotDefinition") or [])}
active = {r["BotDefinition"]["DeveloperName"] for r in (q("SELECT BotDefinition.DeveloperName, Status FROM BotVersion WHERE Status = 'Active'") or []) if r.get("BotDefinition")}
aa = q("SELECT Id FROM PermissionSet WHERE Name = 'Access_Agents'") or []
aa_bots = {r["SetupEntityId"] for r in (q("SELECT SetupEntityId FROM SetupEntityAccess WHERE Parent.Name = 'Access_Agents' AND SetupEntityType = 'BotDefinition'") or [])}

if "platform" in SEL:
    for ps in ("EinsteinGPTPromptTemplateUser", "EinsteinGPTPromptTemplateManager"):
        add("3a", f"{ps} assigned to connected user", ps in assigned, "assigned" if ps in assigned else "not assigned",
            f"assign permission set {ps} to the connected user")

def agent_checks(phase, label, bot):
    if not bot:
        return
    add(phase, f"{label} active", bot["DeveloperName"] in active, f"{bot['DeveloperName']} ({bot['MasterLabel']})",
        f"activate {bot['DeveloperName']} (sf agent activate --api-name {bot['DeveloperName']}, from an SFDX project)")
    add(phase, f"{label} in Access Agents permission set", bool(aa) and bot["Id"] in aa_bots,
        "granted" if bot["Id"] in aa_bots else ("Access_Agents missing" if not aa else "not granted"),
        f"add agentAccesses {bot['DeveloperName']} to Access_Agents and deploy")

if "fulfiller" in SEL:
    ful = [b for b in bots.values() if (b.get("AgentTemplate") or "").endswith("ITSrvcMgmtFulfiller")]
    add("3b", "IT Service Fulfiller agent exists (by template)", bool(ful), ", ".join(b["DeveloperName"] for b in ful) or "none",
        f"create via wizard (browser, Level 2): {WIZARD} - Company field is required")
    for b in ful: agent_checks("3b", "Fulfiller", b)

if "employee" in SEL:
    ch = q("SELECT Id, IsActive FROM MessagingChannel WHERE DeveloperName = 'ItEmpAgentChannel'") or []
    add("3c", "Enhanced Chat channel ItEmpAgentChannel active", bool(ch) and ch[0]["IsActive"], "active" if ch and ch[0]["IsActive"] else ("missing" if not ch else "inactive"),
        f"turn on 'Set Up Enhanced Chat for IT Service Employee' (browser, Level 2): {ITSVC_PAGE}")
    qu = q("SELECT Id, QueueRoutingConfigId FROM Group WHERE Type = 'Queue' AND DeveloperName = 'ItEmpAgentMsgQueue'") or []
    add("3c", "Queue ItEmpAgentMsgQueue with routing config", bool(qu) and bool(qu[0]["QueueRoutingConfigId"]), "ok" if qu and qu[0]["QueueRoutingConfigId"] else ("missing" if not qu else "no routing config"),
        "re-run Enhanced Chat setup, or assign routing config ItEmpAgentRoutingCnfg to the queue")
    if qu:
        objs = {r["SobjectType"] for r in (q(f"SELECT SobjectType FROM QueueSobject WHERE QueueId = '{qu[0]['Id']}'") or [])}
        add("3c", "Queue supports MessagingEndUser + MessagingSession", {"MessagingEndUser", "MessagingSession"} <= objs, ", ".join(sorted(objs)) or "none",
            "add Messaging User and Messaging Session as supported objects on the queue")
        mem = {r["UserOrGroupId"] for r in (q(f"SELECT UserOrGroupId FROM GroupMember WHERE GroupId = '{qu[0]['Id']}'") or [])}
        add("3c", "Connected user is a direct queue member", uid in mem, "member" if uid in mem else "not a direct member",
            f"add GroupMember (GroupId={qu[0]['Id']}, UserOrGroupId={uid})")
    fl = q("SELECT Id, Status FROM Flow WHERE Definition.DeveloperName = 'RouteMsgsItEmpAgent' AND Status = 'Active'", tooling=True) or []
    add("3c", "Routing flow RouteMsgsItEmpAgent active", bool(fl), "active" if fl else "missing/inactive",
        f"re-run Enhanced Chat setup (browser, Level 2): {ITSVC_PAGE}")
    ec_ok = bool(ch) and ch[0]["IsActive"] and bool(qu) and bool(qu[0]["QueueRoutingConfigId"]) and bool(fl)
    add("3c", "Enhanced Chat set up (channel + queue/routing + flow)", ec_ok, "complete" if ec_ok else "incomplete - see rows above",
        "Level 2 browser, with user approval: " + ITSVC_PAGE + " -> 'Enable IT Service Agent Templates' -> toggle ONLY "
        "'Set Up Enhanced Chat for IT Service Employee' (click the container around the switch, Learning #21) -> Confirm; "
        "do NOT touch the IT Service Employee / IT Service Fulfiller / Specialized templates toggles; provisioning takes a few "
        "minutes - re-run this check until channel, queue, routing and flow PASS")
    emp = None
    if fl:
        md = q(f"SELECT Metadata FROM Flow WHERE Id = '{fl[0]['Id']}'", tooling=True) or []
        ids = sorted(set(re.findall(r"0Xx[A-Za-z0-9]{15}", json.dumps(md[0]["Metadata"])))) if md else []
        emp = next((bots[i] for i in ids if i in bots), None)
        add("3c", "Employee agent discovered from routing flow", bool(emp), f"{emp['DeveloperName']} ({emp['MasterLabel']})" if emp else "flow targets no known agent",
            "check the routing flow's agent; re-run Enhanced Chat setup")
    agent_checks("3c", "Employee agent", emp)

if any(s in SEL for s in ("fulfiller", "employee")):
    add("3b/3c", "Access_Agents assigned to connected user", "Access_Agents" in assigned, "assigned" if "Access_Agents" in assigned else "not assigned",
        "sf org assign permset --name Access_Agents")
ignored = [b["DeveloperName"] for b in bots.values() if not (b.get("AgentTemplate") or "").endswith("ITSrvcMgmtFulfiller")
           and not any(r["detail"].startswith(b["DeveloperName"] + " ") for r in rows if r["check"].startswith("Employee agent discovered"))]

w = max(len(r["check"]) for r in rows) if rows else 10
for r in rows:
    print(f"{r['phase']:5} {r['status']:4}  {r['check']:<{w}}  {r['detail']}" + (f"\n             fix: {r['fix']}" if r["fix"] else ""))
print("ignored agents (not used by the recipe):", ", ".join(ignored) or "none")
if OUT: json.dump({"rows": rows, "ignored": ignored}, open(OUT, "w"), indent=2)
sys.exit(2 if any(r["status"] == "FAIL" for r in rows) else 0)
