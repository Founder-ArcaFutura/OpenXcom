#!/usr/bin/env python3
"""Local Laya reconnaissance probe. Only admitted game DTOs enter the model."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PROTOCOL = "alien-recon-laya-v2"
PORTFOLIO_PROTOCOL = "alien-portfolio-laya-v1"
ENCODER_REVISION = "45bb4654a4d5aaff24dd11d4781fa46d39bf8c13"
V4_SHA256 = "bcbb891d21cf081a9d7a941b97f8b0f10cf3dac7473b4b9450fab0d07b885175"
ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "build" / "local"
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("HF_HOME", str(LOCAL / "hf-cache"))
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def file_digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def bounded_name(value):
    if not isinstance(value, str) or not 0 < len(value) <= 128:
        raise ValueError("Invalid mission/region name")
    return value

def integer(value, minimum=0, maximum=2**31-1):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("Invalid integer")
    return value

def supported_candidates(data):
    if not isinstance(data, dict) or set(data) != {"menuSource", "candidates", "beliefs", "evidence"}:
        raise ValueError("Unexpected input fields")
    if data["menuSource"] != "STATIC_RULESET_ONLY":
        raise ValueError("Unsupported menu")
    candidates, beliefs, evidence = data["candidates"], data["beliefs"], data["evidence"]
    if not all(isinstance(v, list) for v in (candidates, beliefs, evidence)):
        raise ValueError("Invalid snapshot lists")
    if len(candidates) > 64 or len(beliefs) > 64 or len(evidence) > 512:
        raise ValueError("Snapshot budget exceeded")
    ev = {}
    allowed_evidence = {"id","kind","sourceUfoId","sourceMissionId","observedAt","reportedAt","region",
                        "longitude","latitude","transmission","observationConfidence"}
    for e in evidence:
        if not isinstance(e, dict) or set(e) != allowed_evidence:
            raise ValueError("Unexpected evidence fields")
        identity = integer(e["id"], 1)
        if identity in ev: raise ValueError("Duplicate evidence")
        integer(e["sourceUfoId"], 1); integer(e["sourceMissionId"])
        bounded_name(e["region"])
        if e["kind"] != "INTERCEPTION_CONTACT" or e["transmission"] != "SURVIVING_UFO_AT_ENCOUNTER_END":
            raise ValueError("Unadmitted evidence")
        for key in ("observedAt", "reportedAt"):
            if not isinstance(e[key], str) or not 0 < len(e[key]) <= 64: raise ValueError("Invalid observation time")
        for key, lower, upper in (("longitude",0,2*math.pi),("latitude",-math.pi/2,math.pi/2)):
            value = e[key]
            if type(value) not in (int,float) or not math.isfinite(value) or not lower <= value <= upper:
                raise ValueError("Invalid observation location")
        integer(e["observationConfidence"], 0, 100)
        ev[identity] = e
    by_region = {}
    allowed_belief = {"kind","region","confidence","confidenceKind","independentSources","evidenceIds"}
    for b in beliefs:
        if not isinstance(b, dict) or set(b) != allowed_belief: raise ValueError("Unexpected belief fields")
        region = bounded_name(b["region"])
        if region in by_region: raise ValueError("Duplicate belief")
        if b["kind"] != "INTERCEPTION_OBSERVED_IN_REGION" or b["confidenceKind"] != "UNCALIBRATED_HEURISTIC":
            raise ValueError("Unsupported belief")
        integer(b["confidence"], 0, 100); integer(b["independentSources"], 1)
        ids = b["evidenceIds"]
        if not isinstance(ids, list) or not 1 <= len(ids) <= 8 or len(set(ids)) != len(ids):
            raise ValueError("Invalid belief support")
        for identity in ids:
            integer(identity, 1)
            if identity not in ev or ev[identity]["region"] != region: raise ValueError("Missing regional evidence")
        reporters = {ev[identity]["sourceUfoId"] for identity in ids}
        if len(reporters) > b["independentSources"]: raise ValueError("Inconsistent source count")
        by_region[region] = b
    result, seen = [], set()
    for c in candidates:
        if not isinstance(c, dict) or set(c) != {"mission","region"}: raise ValueError("Unexpected candidate fields")
        key = (bounded_name(c["mission"]), bounded_name(c["region"]))
        if key in seen: raise ValueError("Duplicate candidate")
        seen.add(key)
        b = by_region.get(c["region"])
        if b and b["confidence"] > 0:
            result.append((c, b))
    return sorted(result, key=lambda pair: (pair[0]["mission"], pair[0]["region"])), ev

def build_packet(data):
    candidates, evidence = supported_candidates(data)
    criteria, mapping, knowledge = {}, {}, {}
    for index, (c, b) in enumerate(candidates):
        label = "C" + str(index)
        region = c["region"].removeprefix("STR_").replace("_", " ").lower()
        mission = c["mission"].removeprefix("STR_").replace("_", " ").lower()
        if c["mission"] == "STR_ALIEN_RETALIATION":
            criteria[label] = f"Search for X-COM bases in {region}: retaliation search waves; discovery can trigger assault."
        else:
            criteria[label] = f"Gather interception reports in {region}: research flights cannot discover bases under normal rules."
        mapping[label] = (c, b)
        if b["region"] not in knowledge:
            knowledge[b["region"]] = {
                "region": region, "confidence_heuristic": b["confidence"],
                "independent_reporting_ufos": b["independentSources"],
                "reports": [{"evidence_id": identity, "ufo_id": evidence[identity]["sourceUfoId"],
                             "observed_at": evidence[identity]["observedAt"],
                             "reported_at": evidence[identity]["reportedAt"]} for identity in b["evidenceIds"]]
            }
    criteria["C" + str(len(criteria))] = "Keep the original schedule; do not propose evidence-targeted reconnaissance."
    state = canonical({"role":"Alien strategic command", "admitted_interception_knowledge":list(knowledge.values())})
    questions = {"recon": {
        "type":"choice",
        "instructions":"Choose an operation using only admitted reports. Contact gathering seeks more reports; base search risks escalating to assault after discovery. Reports do not confirm a base. Weigh information gain against commitment and uncertainty, or keep the original schedule.",
        "criteria":criteria
    }}
    return state, questions, mapping

def load_agent(checkpoint, device="cpu", expected_sha=V4_SHA256):
    import torch
    import laya
    from huggingface_hub import snapshot_download
    from huggingface_hub.errors import LocalEntryNotFoundError
    checkpoint = Path(checkpoint).resolve()
    weights = checkpoint / "model.safetensors"
    sha = file_digest(weights)
    if expected_sha and sha != expected_sha.lower():
        raise ValueError("Checkpoint hash does not match expected identity")
    cfg = json.loads((checkpoint / "rl_agent_config.json").read_text())
    if cfg["encoder"] != "answerdotai/ModernBERT-large":
        raise ValueError("This adapter currently expects the supplied ModernBERT-large checkpoint")
    stage = LOCAL / "laya-checkpoint"
    stage.mkdir(parents=True, exist_ok=True)
    staged_weights = stage / "model.safetensors"
    if not staged_weights.exists() or file_digest(staged_weights) != sha:
        shutil.copyfile(weights, staged_weights)
    shutil.copyfile(checkpoint / "rl_agent_config.json", stage / "rl_agent_config.json")
    # Only architecture/tokenizer metadata is fetched, never a replacement model.
    metadata_args = dict(revision=ENCODER_REVISION,
        allow_patterns=["config.json","tokenizer.json","tokenizer_config.json","special_tokens_map.json"],
        cache_dir=LOCAL / "hf-cache" / "hub")
    try:
        metadata = Path(snapshot_download("answerdotai/ModernBERT-large", local_files_only=True, **metadata_args))
    except LocalEntryNotFoundError:
        metadata = Path(snapshot_download("answerdotai/ModernBERT-large", **metadata_args))
    for directory in ("encoder", "tokenizer"):
        (stage / directory).mkdir(exist_ok=True)
    shutil.copyfile(metadata / "config.json", stage / "encoder" / "config.json")
    for name in ("tokenizer.json","tokenizer_config.json","special_tokens_map.json"):
        if (metadata / name).exists(): shutil.copyfile(metadata / name, stage / "tokenizer" / name)
    torch.set_num_threads(4)
    agent = laya.Agent(str(stage), device=device)
    agent.model.encoder.config.reference_compile = False
    identity = {"checkpointSha256":sha, "modelName":cfg.get("model_name",""),
                "encoderRevision":ENCODER_REVISION,"device":str(agent.device),
                "torchVersion":torch.__version__,"layaVersion":laya.__version__,
                "domainValidation":"NOT_VALIDATED_FOR_XCOM","protocol":PROTOCOL}
    return agent, identity

def predict(agent, identity, data):
    from laya.common import build_sequence, render_options
    state, questions, mapping = build_packet(data)
    out = {"schemaVersion":1, **identity, "inputSha256":digest(data),
           "packetSha256":digest({"state":state,"questions":questions}),
           "state":state,"questions":questions}
    if not mapping:
        return {**out,"status":"NO_ADMITTED_EVIDENCE"}
    if len(state) > 2000:
        return {**out,"status":"INPUT_LIMIT"}
    q = agent._to_internal(questions["recon"])
    # Reject any packet that the stock formatter would silently truncate.
    option_ids = [1+len(agent.tok(" "+v.replace(agent.tok.mask_token," "),add_special_tokens=False)["input_ids"]) for v in render_options(q)]
    instruction_ids = agent.tok("choice question: "+q["ins"],add_special_tokens=False)["input_ids"]
    head_tokens = 3 + len(instruction_ids) + sum(option_ids)
    state_tokens = len(agent.tok(state,add_special_tokens=False)["input_ids"])
    if any(n > 49 for n in option_ids) or len(instruction_ids)+sum(option_ids)>agent.cfg["head_max_len"] or head_tokens+state_tokens+1>agent.cfg["max_len"]:
        return {**out,"status":"INPUT_LIMIT","tokenBudget":{"head":head_tokens,"state":state_tokens}}
    sequence, markers = build_sequence(agent.tok,state,q,agent.cfg["max_len"],agent.cfg["head_max_len"])
    started = time.perf_counter()
    answer = agent.predict(state,questions)["answers"]["recon"]
    latency = (time.perf_counter()-started)*1000
    probabilities = answer["probabilities"]
    if set(probabilities) != set(questions["recon"]["criteria"]) or answer["choice"] not in probabilities:
        raise ValueError("Model output is outside the typed menu")
    if any(not math.isfinite(p) or p<0 or p>1 for p in probabilities.values()) or abs(sum(probabilities.values())-1)>0.01:
        raise ValueError("Invalid model probabilities")
    proposal = {"mission":"","region":"","reason":"MODEL_ABSTAIN","score":0,"evidenceIds":[]}
    status = "ABSTAIN"
    if answer["choice"] in mapping:
        candidate, belief = mapping[answer["choice"]]
        proposal = {**candidate,"reason":("SEARCH_FOR_XCOM_BASE" if candidate["mission"] == "STR_ALIEN_RETALIATION" else "GATHER_INTERCEPTION_REPORTS"),
                    "score":belief["confidence"],"evidenceIds":belief["evidenceIds"]}
        status = "PREDICTED"
    return {**out,"status":status,"answer":answer,"proposal":proposal,
            "latencyMs":round(latency,2),"tokenCount":len(sequence),"optionCount":len(markers),
            "scoreMeaning":"proposal.score is stored belief confidence; model probabilities are unvalidated for X-COM"}


PORTFOLIO_COSTS = {"STR_ALIEN_RESEARCH":2,"STR_ALIEN_PROBE_MISSION":2,"STR_ALIEN_HARVEST":3,
                   "STR_ALIEN_ABDUCTION":3,"STR_ALIEN_TERROR":4,"STR_ALIEN_SURFACE_ATTACK":4,"STR_ALIEN_RETALIATION":2}
PORTFOLIO_DESCRIPTIONS = {
 "STR_ALIEN_RESEARCH":"Research: contact reports; completed flight +1 income/intelligence.",
 "STR_ALIEN_PROBE_MISSION":"Probe: contact reports; completed flight +1 income/intelligence.",
 "STR_ALIEN_HARVEST":"Harvest: completed activity +2 income, +1 logistics.",
 "STR_ALIEN_ABDUCTION":"Abduct: completed activity +2 income, +1 adaptation.",
 "STR_ALIEN_TERROR":"Terror: political pressure, costly exposure; economic reward pending.",
 "STR_ALIEN_SURFACE_ATTACK":"Surface attack: political pressure; economic reward pending.",
 "STR_ALIEN_RETALIATION":"Base search: discovery only; no automatic assault, no income."}

def portfolio_input(data):
    if not isinstance(data,dict) or set(data)!={"schemaVersion","budget","knowledge"} or data["schemaVersion"]!=1:
        raise ValueError("Invalid portfolio envelope")
    b=data["budget"]
    fields={"policyVersion","epochMonth","difficulty","remaining","pendingBonus","intelligence","logistics","adaptation","maxOperations","assaultAvailable","terrorRewardVerified","allowance","carryCap","nextAllowance","nextBonusCap"}
    if not isinstance(b,dict) or set(b)!=fields or b["policyVersion"]!="monthly-portfolio-v1" or b["maxOperations"]!=3 or b["assaultAvailable"] is not False or b["terrorRewardVerified"] is not False:
        raise ValueError("Unsupported portfolio policy")
    for k in ("epochMonth","remaining","pendingBonus","intelligence","logistics","adaptation","allowance","carryCap","nextAllowance","nextBonusCap"): integer(b[k])
    integer(b["difficulty"],0,4)
    knowledge=data["knowledge"]
    if not isinstance(knowledge,dict) or set(knowledge)!={"menuSource","candidates","beliefs","evidence"}: raise ValueError("Invalid knowledge")
    menu=knowledge["candidates"]
    if not isinstance(menu,list) or len(menu)>128: raise ValueError("Portfolio menu budget")
    seen=set()
    for c in menu:
        if not isinstance(c,dict) or set(c)!={"mission","region"}: raise ValueError("Invalid candidate")
        key=(bounded_name(c["mission"]),bounded_name(c["region"]))
        if key in seen or key[0] not in PORTFOLIO_COSTS: raise ValueError("Unsupported/duplicate operation")
        seen.add(key)
    # Reuse the provenance validator with one candidate per region; portfolio options
    # also admit regions with no reports, which is unknown risk rather than safety.
    regional={c["region"]:c for c in menu}
    validation={**knowledge,"candidates":list(regional.values())}
    supported_candidates(validation)
    return b,menu,knowledge["beliefs"]

def checked_choice(agent,state,criteria,instructions):
    if len(criteria) == 1:
        label = next(iter(criteria))
        return label,{"state":state,"question":{"criteria":criteria},"answer":{"choice":label,"probabilities":{label:1.0}},"source":"ONLY_ELIGIBLE_REGION"}
    from laya.common import build_sequence,render_options
    question={"type":"choice","instructions":instructions,"criteria":criteria}
    q=agent._to_internal(question)
    option_ids=[1+len(agent.tok(" "+v.replace(agent.tok.mask_token," "),add_special_tokens=False)["input_ids"]) for v in render_options(q)]
    ins=len(agent.tok("choice question: "+q["ins"],add_special_tokens=False)["input_ids"])
    head=3+ins+sum(option_ids)
    state_tokens=len(agent.tok(state,add_special_tokens=False)["input_ids"])
    if any(n>49 for n in option_ids) or ins+sum(option_ids)>agent.cfg["head_max_len"] or head+state_tokens+1>agent.cfg["max_len"]:
        raise ValueError("Portfolio packet exceeds model token budget")
    sequence,_=build_sequence(agent.tok,state,q,agent.cfg["max_len"],agent.cfg["head_max_len"])
    answer=agent.predict(state,{"portfolio":question})["answers"]["portfolio"]
    ps=answer["probabilities"]
    if set(ps)!=set(criteria) or answer["choice"] not in criteria or any(not math.isfinite(v) or not 0<=v<=1 for v in ps.values()) or abs(sum(ps.values())-1)>0.01:
        raise ValueError("Invalid portfolio choice")
    return answer["choice"],{"state":state,"question":question,"answer":answer,"tokenCount":len(sequence),"packetSha256":digest({"state":state,"question":question})}

def plan_portfolio(data,choose):
    budget,menu,beliefs=portfolio_input(data)
    remaining=budget["remaining"]
    selected=[]; decisions=[]
    risks={b["region"]:{"reporters":b["independentSources"],"evidence":b["evidenceIds"]} for b in beliefs}
    for slot in range(3):
        available=[c for c in menu if c not in selected and PORTFOLIO_COSTS[c["mission"]]<=remaining]
        missions=sorted({c["mission"] for c in available})
        if not missions: break
        # Context is public rules, own resources and admitted reports only.
        state=canonical({"role":"Alien strategic command","goal":"Build sustainable campaign capacity, exert political pressure, gather intelligence, limit losses.",
                         "month":budget["epochMonth"],"remaining":remaining,"pending_next_month_bonus":budget["pendingBonus"],
                         "carry_limit":budget["carryCap"],"unused_above_carry_expires":max(0,remaining-budget["carryCap"]),"next_allowance":budget["nextAllowance"],"bonus_limit":budget["nextBonusCap"],
                         "progress":{k:budget[k] for k in ("intelligence","logistics","adaptation")},"selected":selected,
                         "interception_reports":risks,"unknown_regions":"No reports does not mean safe; losses transmit nothing.",
                         "economy":"Half allowance carry cap; next-month income cap half allowance. Growth tapers at month18. Logistics2 unlocks infrastructure; adaptation2/intelligence1 unlocks infiltration. Assault unavailable.",
                         "operations":{m:PORTFOLIO_DESCRIPTIONS[m] for m in missions}})
        criteria={"M"+str(i):m.removeprefix("STR_ALIEN_").replace("_"," ")+" cost "+str(PORTFOLIO_COSTS[m]) for i,m in enumerate(missions)}
        criteria["SAVE"]="Save remaining resources; end monthly portfolio."
        label,receipt=choose(state,criteria,"Choose a strategic objective balancing income, intelligence, pressure and risk. Saving is valid.")
        decisions.append(receipt)
        if label=="SAVE": break
        if label not in criteria or not label.startswith("M"): raise ValueError("Invalid objective")
        mission=missions[int(label[1:])]
        regions=sorted({c["region"] for c in available if c["mission"]==mission})
        criteria={"R"+str(i):r.removeprefix("STR_").replace("_"," ")+ (" reports "+str(risks[r]["reporters"]) if r in risks else " risk unknown") for i,r in enumerate(regions)}
        label,receipt=choose(canonical({"objective":mission,"remaining":remaining,"selected":selected,"reported_interceptions":risks}),criteria,
                            "Choose an operational region. Reported interception suggests exposure; missing reports mean unknown risk.")
        decisions.append(receipt)
        if label not in criteria: raise ValueError("Invalid operational region")
        operation={"mission":mission,"region":regions[int(label[1:])]}
        selected.append(operation); remaining-=PORTFOLIO_COSTS[mission]
    return {"status":"PREDICTED" if selected else "SAVE_RESOURCES","operations":selected,"remainingProposed":remaining,"decisions":decisions}

def predict_portfolio(agent,identity,data):
    started=time.perf_counter()
    result=plan_portfolio(data,lambda state,criteria,ins:checked_choice(agent,state,criteria,ins))
    return {**result,**identity,"schemaVersion":1,"protocol":PORTFOLIO_PROTOCOL,"inputSha256":digest(data),
            "latencyMs":round((time.perf_counter()-started)*1000,2),"scoreMeaning":"Unvalidated choice probabilities; engine validates entire portfolio."}

def serve(agent, identity, port):
    lock = threading.Lock()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_): pass
        def do_GET(self):
            if self.path != "/healthz": self.send_error(404); return
            body = canonical({"status":"READY",**identity,"portfolioProtocol":PORTFOLIO_PROTOCOL}).encode()
            self.send_response(200); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
        def do_POST(self):
            if self.path not in ("/recon","/portfolio"): self.send_error(404); return
            try:
                size = int(self.headers.get("Content-Length","0"))
                if not 0<size<=32768: raise ValueError("Request budget")
                data = json.loads(self.rfile.read(size))
                with lock: response = predict_portfolio(agent,identity,data) if self.path == "/portfolio" else predict(agent,identity,data)
                body = canonical(response).encode()
                self.send_response(200); self.send_header("Content-Type","application/json")
                self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError): pass
            except Exception as error:
                print("Recon classification failed:",type(error).__name__,str(error),flush=True)
                self.send_error(503,"Model proposal unavailable")
    server = ThreadingHTTPServer(("127.0.0.1",port),Handler)
    server.daemon_threads = True
    print(canonical({"status":"READY","port":port,**identity}),flush=True)
    try: server.serve_forever()
    finally: server.server_close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint",type=Path,required=True)
    parser.add_argument("--device",choices=("cpu","cuda"),default="cpu")
    parser.add_argument("--expected-sha256",default=V4_SHA256)
    parser.add_argument("--port",type=int,default=18867)
    parser.add_argument("--probe",type=Path)
    parser.add_argument("--out",type=Path)
    args = parser.parse_args()
    agent, identity = load_agent(args.checkpoint,args.device,args.expected_sha256)
    if args.probe:
        receipt = json.loads(args.probe.read_text())
        result = predict(agent,identity,receipt.get("input",receipt))
        if not args.out: raise SystemExit("--out required with --probe")
        args.out.write_text(canonical(result)+"\n",encoding="utf-8")
        print(canonical({"status":result["status"],"proposal":result.get("proposal"),"latencyMs":result.get("latencyMs"),**identity}))
    else:
        if not 1<=args.port<=65535: raise SystemExit("Invalid port")
        serve(agent,identity,args.port)

if __name__=="__main__": main()
