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
PORTFOLIO_PROTOCOL = "alien-strategy-laya-v2"
PORTFOLIO_PROMPT_VERSION = "search-evidence-v5"
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
                   "STR_ALIEN_ABDUCTION":3,"STR_ALIEN_TERROR":4,"STR_ALIEN_SURFACE_ATTACK":4,"STR_ALIEN_RETALIATION":2,"STR_ALIEN_BASE":6,"STR_ALIEN_INFILTRATION":6}
PORTFOLIO_DESCRIPTIONS = {
 "STR_ALIEN_RESEARCH":"Completed flight: +1 income/intelligence; no base discovery.",
 "STR_ALIEN_PROBE_MISSION":"Completed flight: +1 income/intelligence; no base discovery.",
 "STR_ALIEN_HARVEST":"Verified activity: +2 income, +1 logistics.",
 "STR_ALIEN_ABDUCTION":"Verified activity: +2 income, +1 adaptation.",
 "STR_ALIEN_TERROR":"Political pressure; exposed craft/site; no income bonus.",
 "STR_ALIEN_SURFACE_ATTACK":"Political pressure; exposed craft/site; no income bonus.",
 "STR_ALIEN_RETALIATION":"Base search: discovery only; no income; assault unavailable.",
 "STR_ALIEN_BASE":"Infrastructure; eligible logistics; recurring income unimplemented.",
 "STR_ALIEN_INFILTRATION":"Seek national control; recurring control income unimplemented."}

def portfolio_input(data):
    if not isinstance(data,dict) or set(data)!={"schemaVersion","budget","knowledge","sitrep"} or data["schemaVersion"]!=1:
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
    return b,menu,knowledge["beliefs"],validate_sitrep(data["sitrep"])


STRATEGIES = {
 "RESOURCE_ACQUISITION":("Build income and capacity with harvest, abduction, eligible bases.",{"STR_ALIEN_HARVEST","STR_ALIEN_ABDUCTION","STR_ALIEN_BASE"}),
 "POLITICAL_PRESSURE":("Weaken resistance with terror and eligible infiltration.",{"STR_ALIEN_TERROR","STR_ALIEN_SURFACE_ATTACK","STR_ALIEN_INFILTRATION"}),
 "INTELLIGENCE":("Improve awareness through research and base searches.",{"STR_ALIEN_RESEARCH","STR_ALIEN_PROBE_MISSION","STR_ALIEN_RETALIATION"}),
 "COUNTER_XCOM":("Find and disrupt XCOM; evidence-directed searches; assaults unavailable.",{"STR_ALIEN_RETALIATION"})}

def validate_sitrep(s):
    fields={"schemaVersion","period","coverage","previousStrategy","previousPortfolio","previousReceiptId","assets","lossAssignments","contacts","verifiedActivities","pendingOperations","pendingTotal","pendingTruncated","enemyRecovery","missionSuccess","operationalReview"}
    if not isinstance(s,dict) or set(s)!=fields or s["schemaVersion"]!=1: raise ValueError("Invalid sitrep fields")
    period=s["period"]
    if not isinstance(period,str) or len(period)!=7 or period[4]!="-" or not period[:4].isdigit() or not period[5:].isdigit() or not 1<=int(period[5:])<=12: raise ValueError("Invalid sitrep period")
    if s["coverage"]!="PARTIAL_FLEET_OUTCOMES" or s["enemyRecovery"]!="UNKNOWN" or s["missionSuccess"]!="NOT_INFERRED_FROM_ACTIVITY_OR_DISAPPEARANCE": raise ValueError("Unsupported outcome certainty")
    if s["previousStrategy"] not in {*STRATEGIES,"UNSPECIFIED","NO_FEASIBLE_OPERATION"}: raise ValueError("Unknown previous strategy")
    integer(s["previousReceiptId"]);integer(s["pendingTotal"])
    if type(s["pendingTruncated"]) is not bool: raise ValueError("Invalid pending coverage")
    if not isinstance(s["assets"],dict) or set(s["assets"])!={"deployed","returned","unavailable"}:raise ValueError("Invalid asset counts")
    for v in s["assets"].values():integer(v)
    for key,field in (("lossAssignments","region"),("contacts","region"),("verifiedActivities","mission")):
        rows=s[key]
        if not isinstance(rows,list) or len(rows)>64:raise ValueError("Sitrep group budget")
        seen=set()
        for row in rows:
            if not isinstance(row,dict) or set(row)!={field,"count","evidenceIds"}:raise ValueError("Invalid sitrep group")
            name=bounded_name(row[field]);integer(row["count"],1)
            if name in seen:raise ValueError("Duplicate sitrep group")
            seen.add(name);ids=row["evidenceIds"]
            if not isinstance(ids,list) or not 1<=len(ids)<=8 or len(ids)!=len(set(ids)):raise ValueError("Invalid sitrep support")
            for identity in ids:integer(identity,1)
    for key,limit,fields in (("previousPortfolio",3,{"mission","region"}),("pendingOperations",16,{"missionId","mission","region"})):
        if not isinstance(s[key],list) or len(s[key])>limit:raise ValueError("Sitrep operation budget")
        for op in s[key]:
            if not isinstance(op,dict) or set(op)!=fields:raise ValueError("Invalid owned operation")
            bounded_name(op["mission"]);bounded_name(op["region"])
            if "missionId" in op:integer(op["missionId"],1)
    if s["pendingTotal"]<len(s["pendingOperations"]) or s["pendingTruncated"]!=(s["pendingTotal"]>len(s["pendingOperations"])):raise ValueError("Inconsistent pending coverage")
    if sum(g["count"] for g in s["lossAssignments"])!=s["assets"]["unavailable"]:raise ValueError("Inconsistent loss assignment counts")
    review=s["operationalReview"]
    if not isinstance(review,dict) or set(review)!={"loss_roles","terror_objective_waves_pending","rolling_results","limits","roleSupport","pendingProgress"}:raise ValueError("Invalid operational review")
    if not isinstance(review["loss_roles"],dict) or set(review["loss_roles"])!={"PREPARATION","SEARCH","OBJECTIVE_CARRIER","UNKNOWN"}:raise ValueError("Invalid role counts")
    for count in review["loss_roles"].values():integer(count)
    if sum(review["loss_roles"].values())!=s["assets"]["unavailable"]:raise ValueError("Role counts disagree with loss coverage")
    integer(review["terror_objective_waves_pending"])
    if review["limits"]!="Partial own telemetry. Pending objective is not success; scout loss is not mission failure.":raise ValueError("Unsupported role certainty")
    history=review["rolling_results"]
    if not isinstance(history,list) or not 1<=len(history)<=2:raise ValueError("Invalid rolling history")
    previous=""
    for row in history:
        if not isinstance(row,list) or len(row)!=3 or not isinstance(row[0],str) or len(row[0])!=7 or row[0][4]!="-" or not row[0][:4].isdigit() or not row[0][5:].isdigit() or not 1<=int(row[0][5:])<=12 or row[0]<=previous or row[0]>s["period"]:raise ValueError("Invalid history period")
        previous=row[0];integer(row[1]);integer(row[2])
    if history[-1]!=[s["period"],s["assets"]["unavailable"],sum(g["count"] for g in s["verifiedActivities"])]:raise ValueError("Rolling history disagrees with native sitrep")
    support=review["roleSupport"]
    if not isinstance(support,list) or len(support)>16:raise ValueError("Role support budget")
    identities=set()
    for row in support:
        if not isinstance(row,dict) or set(row)!={"lossReceiptId","role","craftType","source"}:raise ValueError("Invalid role support")
        integer(row["lossReceiptId"],1);bounded_name(row["craftType"])
        if row["lossReceiptId"] in identities or row["role"] not in review["loss_roles"] or row["source"] not in {"UNKNOWN","EXPLICIT_NATIVE_TELEMETRY","LEGACY_OWN_SEQUENCE_MATCHED_TO_RULES"}:raise ValueError("Invalid role provenance")
        identities.add(row["lossReceiptId"])
        if row["source"]=="UNKNOWN" and (row["role"]!="UNKNOWN" or row["craftType"]!="UNKNOWN"):raise ValueError("Unsupported legacy role")
    for role,count in review["loss_roles"].items():
        if sum(row["role"]==role for row in support)>count:raise ValueError("Role support exceeds observed losses")
    progress=review["pendingProgress"]
    if not isinstance(progress,list) or len(progress)>16:raise ValueError("Progress budget")
    identities=set()
    for row in progress:
        if not isinstance(row,dict) or set(row)!={"missionId","nextWave","totalWaves","objectiveWavePending"}:raise ValueError("Invalid owned progress")
        integer(row["missionId"],1);integer(row["totalWaves"],0,65535);integer(row["nextWave"],0,row["totalWaves"])
        if type(row["objectiveWavePending"]) is not bool or row["missionId"] in identities:raise ValueError("Invalid progress identity")
        identities.add(row["missionId"])
    if identities!={o["missionId"] for o in s["pendingOperations"]}:raise ValueError("Progress disagrees with pending operations")
    return s

def bounded_regions(rows):
    ordered=sorted(rows.items(),key=lambda pair:(-pair[1],pair[0]))
    if len(ordered)<=4:return dict(ordered)
    return {"regions":dict(ordered[:4]),"other_regions":len(ordered)-4,"other_count":sum(v for _,v in ordered[4:])}

def compact_sitrep(s):
    # Source IDs/full rows remain in the exact native input receipt; this is a
    # deterministic bounded projection, not a model-generated narrative.
    return {"period":s["period"],"coverage":s["coverage"],"previous_strategy":s["previousStrategy"],
            "previous_portfolio":[[o["mission"].removeprefix("STR_ALIEN_"),o["region"].removeprefix("STR_")] for o in s["previousPortfolio"]],
            "assets":s["assets"],"loss_assignments":bounded_regions({g["region"].removeprefix("STR_"):g["count"] for g in s["lossAssignments"]}),
            "completed_activities":{g["mission"].removeprefix("STR_ALIEN_"):g["count"] for g in s["verifiedActivities"]},
            "pending":s["pendingTotal"],"enemy_recovery":"UNKNOWN"}

def checked_choice(agent,state,criteria,instructions):
    if len(criteria) == 1:
        label = next(iter(criteria))
        return label,{"state":state,"question":{"criteria":criteria},"answer":{"choice":label,"probabilities":{label:1.0}},"source":"ONLY_ELIGIBLE_CHOICE"}
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

def search_region_pool(regions, risks, sitrep):
    """Use persistent admitted contacts, then uncertain recent assignment losses.

    This is an explicit targeting constraint, not inferred base coordinates.
    Keep all regions for exploration only when neither source covers the menu.
    """
    reported=[r for r in regions if r in risks]
    if reported:return reported,"SURVIVING_INTERCEPTION_REPORTS"
    losses={g["region"] for g in sitrep["lossAssignments"]}
    assigned=[r for r in regions if r in losses]
    if assigned:return assigned,"RECENT_LOSS_ASSIGNMENTS_UNCERTAIN"
    return regions,"NO_MATCHING_EVIDENCE_EXPLORATION"

def plan_portfolio(data,choose):
    budget,menu,beliefs,sitrep=portfolio_input(data)
    remaining=budget["remaining"]
    selected=[]; decisions=[]
    risks={b["region"]:{"reporters":b["independentSources"],"evidence":b["evidenceIds"]} for b in beliefs}
    search_regions,search_basis=search_region_pool(sorted({c["region"] for c in menu if c["mission"]=="STR_ALIEN_RETALIATION"}),risks,sitrep)
    menu=[c for c in menu if c["mission"]!="STR_ALIEN_RETALIATION" or c["region"] in search_regions]
    affordable=[c for c in menu if PORTFOLIO_COSTS[c["mission"]]<=remaining]
    strategies={k:description for k,(description,preferred) in STRATEGIES.items() if any(c["mission"] in preferred for c in affordable)}
    if not strategies:
        return {"strategy":"NO_FEASIBLE_OPERATION","status":"SAVE_RESOURCES","operations":[],"remainingProposed":remaining,"decisions":[]}
    strategy_state=canonical({"goal":"Conquer Earth: build alien capacity and weaken resistance.","budget":remaining,"carry_limit":budget["carryCap"],"expires_if_idle":max(0,remaining-budget["carryCap"]),
                              "progress":{k:budget[k] for k in ("intelligence","logistics","adaptation")},"sitrep":compact_sitrep(sitrep),
                              "reported_exposure":bounded_regions({b["region"].removeprefix("STR_"):b["independentSources"] for b in beliefs}),
                              "uncertainty":"Own losses do not confirm enemy locations or captures. Activity completion is not whole-mission success."})
    strategy_data=json.loads(strategy_state)
    review={k:sitrep["operationalReview"][k] for k in ("loss_roles","terror_objective_waves_pending","rolling_results","limits")}
    strategy_data["operational_review"]=review
    strategy_state=canonical(strategy_data)
    strategy,receipt=choose(strategy_state,strategies,"Choose this month's conquest strategy using observed results and resources. Strategies guide mixed portfolios, not mandatory retaliation.")
    if strategy not in strategies:raise ValueError("Invalid strategy choice")
    decisions.append({**receipt,"stage":"STRATEGY"})
    for slot in range(3):
        available=[c for c in menu if c not in selected and PORTFOLIO_COSTS[c["mission"]]<=remaining]
        missions=sorted({c["mission"] for c in available})
        if not missions:break
        selected_summary=[[c["mission"].removeprefix("STR_ALIEN_"),c["region"].removeprefix("STR_")] for c in selected]
        state=canonical({"goal":"Conquer Earth","strategy":strategy,"strategy_purpose":STRATEGIES[strategy][0],
                         "remaining":remaining,"carry_limit":budget["carryCap"],"expires_if_idle":max(0,remaining-budget["carryCap"]),
                         "next_allowance":budget["nextAllowance"],"pending_bonus":budget["pendingBonus"],"next_bonus_cap":budget["nextBonusCap"],
                         "recent_results":{"unavailable_craft":sitrep["assets"]["unavailable"],"verified_activities":sum(g["count"] for g in sitrep["verifiedActivities"]),"pending":sitrep["pendingTotal"]},
                         "selected":selected_summary,"operations":{m.removeprefix("STR_ALIEN_"):PORTFOLIO_DESCRIPTIONS[m] for m in missions},
                         "tradeoff":"Saving delays conquest; excess expires. Lost craft: no refund. Productive rewards require verified activity."})
        criteria={"M"+str(i):m.removeprefix("STR_ALIEN_").replace("_"," ")+" cost "+str(PORTFOLIO_COSTS[m]) for i,m in enumerate(missions)}
        criteria["SAVE"]=f"Defer investment: carry {min(remaining,budget['carryCap'])}, forfeit {max(0,remaining-budget['carryCap'])}; no new missions."
        state_data=json.loads(state)
        state_data["operational_review"]=review
        state_data["deferral"]="Money alone cannot unlock bases/infiltration; verified productive activity earns prerequisites."
        if len(missions)>5:
            # Remove repeated strategy prose for the wider late-campaign menu;
            # exact strategy purpose remains in its preceding decision receipt.
            state_data.pop("strategy_purpose")
            state_data["tradeoff"]="No refunds; productive rewards require verified activity."
            state_data["deferral"]="Unlocks require productive activity."
            state_data["operational_review"]={k:v for k,v in review.items() if k!="limits"}
            state_data["tradeoff"]="Pending is not success; scout loss is not failure; no refunds."
        state=canonical(state_data)
        label,receipt=choose(state,criteria,"Choose investment or deferral. Compare affordable productive missions against carry, forfeiture and pending commitments; do not invent future gains.")
        decisions.append({**receipt,"stage":"OPERATION"})
        if label=="SAVE":break
        if label not in criteria or not label.startswith("M"):raise ValueError("Invalid objective")
        mission=missions[int(label[1:])]
        regions=sorted({c["region"] for c in available if c["mission"]==mission})
        targeting="STRATEGIC_TARGET"
        if mission=="STR_ALIEN_RETALIATION":
            targeting=search_basis
        criteria={"R"+str(i):r.removeprefix("STR_").replace("_"," ")+(" reports "+str(risks[r]["reporters"]) if r in risks else " exposure unknown") for i,r in enumerate(regions)}
        state=canonical({"strategy":strategy,"objective":mission,"remaining":remaining,"selected":selected_summary,
                         "surviving_reports":{r.removeprefix("STR_"):v["reporters"] for r,v in risks.items()},
                         "own_losses_by_assignment":{g["region"].removeprefix("STR_"):g["count"] for g in sitrep["lossAssignments"]},
                         "uncertainty":"Loss assignments are own tasking regions, not hidden encounter locations. Missing reports do not mean safe."})
        if mission=="STR_ALIEN_RETALIATION":
            state_data=json.loads(state)
            state_data["search_basis"]=targeting
            state_data["search_goal"]="Locate XCOM near interception evidence; assignment losses are weaker clues, not confirmed interception positions."
            state=canonical(state_data)
        label,receipt=choose(state,criteria,"Choose a region for this operation. Weigh reported exposure and own losses against the strategy; cause of losses remains uncertain.")
        decisions.append({**receipt,"stage":"REGION","targetingBasis":targeting,"eligibleRegions":regions})
        if label not in criteria:raise ValueError("Invalid operational region")
        operation={"mission":mission,"region":regions[int(label[1:])]}
        selected.append(operation);remaining-=PORTFOLIO_COSTS[mission]
    return {"strategy":strategy,"status":"PREDICTED" if selected else "SAVE_RESOURCES","operations":selected,"remainingProposed":remaining,"decisions":decisions}

def predict_portfolio(agent,identity,data):
    started=time.perf_counter()
    result=plan_portfolio(data,lambda state,criteria,ins:checked_choice(agent,state,criteria,ins))
    return {**result,**identity,"schemaVersion":1,"protocol":PORTFOLIO_PROTOCOL,"portfolioPromptVersion":PORTFOLIO_PROMPT_VERSION,"inputSha256":digest(data),
            "latencyMs":round((time.perf_counter()-started)*1000,2),"scoreMeaning":"Unvalidated choice probabilities; engine validates entire portfolio."}

def serve(agent, identity, port):
    lock = threading.Lock()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*_): pass
        def do_GET(self):
            if self.path != "/healthz": self.send_error(404); return
            body = canonical({"status":"READY",**identity,"portfolioProtocol":PORTFOLIO_PROTOCOL,"portfolioPromptVersion":PORTFOLIO_PROMPT_VERSION}).encode()
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
