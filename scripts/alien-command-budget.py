#!/usr/bin/env python3
"""Replay recorded engine facts into a provisional monthly shadow budget."""
import argparse, calendar, hashlib, json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
def period(time,origin_year=1999):
    d=datetime.strptime(time,"%Y-%m-%d %H:%M:%S")
    return (d.year-origin_year)*12+d.month-1
def month_label(index,origin_year=1999):
    return f"{origin_year+index//12:04d}-{index%12+1:02d}"
def unlocked(policy,progress,month):
    return [name for name,c in policy['capabilities'].items() if month>=c.get('earliestMonth',0) and all(progress.get(k,0)>=v for k,v in c.get('progress',{}).items())]
def validate_policy(policy):
    if policy.get('schemaVersion')!=1 or policy.get('mode')!='SHADOW_ONLY': raise ValueError('Unsupported budget policy')
    a=policy['allocation']
    for key in ['carryNumerator','carryDenominator','bonusCapNumerator','bonusCapDenominator']:
        if type(a[key]) is not int or a[key]<0: raise ValueError('Invalid allocation integer')
    if not a['carryDenominator'] or not a['bonusCapDenominator']: raise ValueError('Invalid allocation limits')
    if len(a['profiles'])!=5: raise ValueError('Five difficulty profiles required')
    for profile in a['profiles']:
        curve=profile['monthly']
        if len(curve)!=18 or any(type(x) is not int or x<=0 for x in curve) or curve!=sorted(curve): raise ValueError('Invalid allowance transition curve')
    for name,c in policy['capabilities'].items():
        if type(c.get('earliestMonth',0)) is not int or c.get('earliestMonth',0)<0: raise ValueError('Invalid capability month')
        for dimension,value in c.get('progress',{}).items():
            if dimension not in {'intelligence','logistics','adaptation'} or type(value) is not int or value<0: raise ValueError('Invalid capability progress')
    for name,op in policy['operations'].items():
        if type(op['cost']) is not int or (op['cost']<0 or (op['cost']==0 and name!='STR_ALIEN_RETALIATION')) or type(op['bonus']) is not int or op['bonus']<0: raise ValueError('Invalid operation cost/bonus')
        if op['requires'] not in policy['capabilities']: raise ValueError('Unknown capability')
    for phase in ['search','assault']:
        op=policy[phase]
        if type(op['cost']) is not int or op['cost']<=0 or op['requires'] not in policy['capabilities']: raise ValueError('Invalid deployment phase policy')
def evaluate(events,active,as_of,policy,origin_year=1999,difficulty=2):
    validate_policy(policy)
    if type(difficulty) is not int or difficulty not in range(5): raise ValueError('Invalid difficulty')
    profile=policy['allocation']['profiles'][difficulty]
    last=period(as_of,origin_year)
    if last<0: raise ValueError('Campaign origin must be January 1999 or later')
    missions={}; searches=set(); assaults=set(); gains=set(); progress=defaultdict(int); rows=[]; warnings=[]; receipts=[]
    facts=defaultdict(list); ids=set()
    for e in events:
        if e.get('schemaVersion')!=1 or not isinstance(e.get('id'),int): raise ValueError('Invalid event identity/schema')
        if e['id'] in ids: raise ValueError('Duplicate audit event ID')
        ids.add(e['id'])
        m=period(e['gameTime'],origin_year)
        if m<0 or m>last: raise ValueError('Event outside save campaign range')
        facts[m].append(e)
    native_starts={e['missionId'] for e in events if e.get('kind')=='budget_fact' and e.get('event')=='MISSION_COMMITTED'}
    if any(e.get('kind')=='decision' and e.get('execution',{}).get('status')=='MISSION_CREATED' and e['execution']['missionId'] not in native_starts for e in events):
        warnings.append({'reason':'LEGACY_START_COVERAGE_INCOMPLETE','detail':'Older decision receipts cover scheduled missions; other historical starts and completed outcomes may be missing.'})
    carry=0; due_bonus=0
    for month in range(last+1):
        a=policy['allocation']; base=profile['monthly'][min(month,17)]
        earned=min(due_bonus,base*a['bonusCapNumerator']//a['bonusCapDenominator'])
        available=base+carry+earned; balance=available; next_bonus=0; committed=0
        capabilities=unlocked(policy,progress,month)
        for e in sorted(facts[month],key=lambda e:(e['gameTime'],e['id'])):
            execution=e.get('execution',{})
            start=e.get('kind')=='budget_fact' and e.get('event')=='MISSION_COMMITTED'
            legacy=e.get('kind')=='decision' and execution.get('status')=='MISSION_CREATED'
            if start or legacy:
                mid=e['missionId'] if start else execution['missionId']
                name=e['mission'] if start else execution['mission']
                if mid in missions:
                    if missions[mid]['mission']!=name: raise ValueError('Conflicting mission identity')
                    continue
                op=policy['operations'].get(name)
                missions[mid]={'mission':name,'month':month,'status':'RECORDED_COMMITMENT'}
                if not op:
                    warnings.append({'missionId':mid,'reason':'UNPRICED_OPERATION','mission':name});continue
                reasons=[]
                if op['requires'] not in capabilities: reasons.append('CAPABILITY_LOCKED')
                if balance<op['cost']: reasons.append('INSUFFICIENT_ALLOCATION')
                before=balance;balance-=op['cost'];committed+=op['cost']
                receipts.append({'event':'MISSION_COST','missionId':mid,'mission':name,'time':e['gameTime'],'cost':op['cost'],'before':before,'after':balance,'eligibility':'WOULD_BLOCK' if reasons else 'WOULD_ALLOW','reasons':reasons,'basis':'ENGINE_START' if start else 'LEGACY_DECISION_RECEIPT'})
            elif e.get('kind')=='budget_fact' and e.get('event') in {'BASE_SEARCH_COMMITTED','BASE_ASSAULT_COMMITTED'}:
                mid=e['missionId'];uid=e['sourceUfoId']
                if mid not in missions:
                    warnings.append({'missionId':mid,'reason':'PHASE_KNOWN_START_TIME_UNKNOWN'})
                    missions[mid]={'mission':e['mission'],'month':None,'status':'START_TIME_UNKNOWN_PHASE_KNOWN'}
                if uid<=0: raise ValueError('Deployment requires unique UFO identity')
                search=e['event']=='BASE_SEARCH_COMMITTED'
                if search:
                    if mid in searches: continue
                    searches.add(mid)
                else:
                    if uid in assaults: continue
                    assaults.add(uid)
                op=policy['search' if search else 'assault'];reasons=[]
                if op['requires'] not in capabilities: reasons.append('CAPABILITY_LOCKED')
                if balance<op['cost']: reasons.append('INSUFFICIENT_ALLOCATION')
                before=balance;balance-=op['cost'];committed+=op['cost']
                receipts.append({'event':'SEARCH_COST' if search else 'ASSAULT_COST','missionId':mid,'sourceUfoId':uid,'time':e['gameTime'],'cost':op['cost'],'before':before,'after':balance,'eligibility':'WOULD_BLOCK' if reasons else 'WOULD_ALLOW','reasons':reasons,'basis':'ENGINE_SEARCH_UFO_SPAWN' if search else 'ENGINE_ASSAULT_UFO_SPAWN'})
            elif e.get('kind')=='budget_fact' and e.get('event') in {'RESEARCH_FLIGHT_COMPLETED','PRODUCTIVE_ACTIVITY_COMPLETED'}:
                mid=e['missionId'];name=e['mission'];op=policy['operations'].get(name)
                if not op or e['event']!=op.get('gainEvent'): continue
                if mid not in missions:
                    warnings.append({'missionId':mid,'reason':'GAIN_WITHOUT_RECORDED_START'});continue
                if missions[mid]['mission']!=name: raise ValueError('Gain mission identity mismatch')
                if mid in gains: continue
                gains.add(mid);next_bonus+=op['bonus']
                if op['progress']: progress[op['progress']]+=1
                receipts.append({'event':'VERIFIED_GAIN','missionId':mid,'mission':name,'time':e['gameTime'],'bonusNextMonth':op['bonus'],'progressDimension':op['progress'],'basis':e['event']})
        carry=min(max(balance,0),base*a['carryNumerator']//a['carryDenominator'])
        rows.append({'month':month_label(month,origin_year),'baseAllocation':base,'carryIn':available-base-earned,'earnedBonus':earned,'available':available,'committed':committed,'remaining':balance,'carryOut':carry,'bonusPendingNextMonth':next_bonus,'capabilitiesAtStart':capabilities})
        due_bonus=next_bonus
    for m in active:
        if m['uniqueID'] not in missions:
            warnings.append({'missionId':m['uniqueID'],'mission':m['type'],'reason':'ACTIVE_MISSION_WITHOUT_START_TIME_OR_COST_RECEIPT'})
    return {'schemaVersion':1,'mode':'SHADOW_ONLY','policyVersion':policy['policyVersion'],'asOf':as_of,'campaignOriginYear':origin_year,'difficulty':difficulty,'difficultyProfile':profile['name'],'monthly':rows,'progress':dict(progress),'capabilitiesNow':rows[-1]['capabilitiesAtStart'],'capabilitiesForNextAllocation':unlocked(policy,progress,last+1),'coverageComplete':not warnings,'receipts':receipts,'coverageWarnings':warnings,'verifiedGainMissionCount':len(gains),'earthIncomeStatus':policy.get('incomeDesign',{}).get('status','NOT_YET_ACCOUNTED'),'rules':'Actual recorded commitments are charged even when the prototype would block them; missing outcomes never earn bonuses.'}
def main():
    import yaml
    p=argparse.ArgumentParser();p.add_argument('--save',required=True,type=Path);p.add_argument('--policy',type=Path,default=ROOT/'config'/'alien-command-budget.json');p.add_argument('--output',type=Path);a=p.parse_args()
    raw=a.save.read_bytes();sha=hashlib.sha256(raw).hexdigest();docs=list(yaml.safe_load_all(raw));header,body=docs
    t=header['time'];asof=f"{t['year']:04d}-{t['month']:02d}-{t['day']:02d} {t['hour']:02d}:{t['minute']:02d}:{t['second']:02d}"
    policy=json.loads(a.policy.read_text());events=[json.loads(e) for e in body.get('alienCommand',{}).get('audit',[])]
    mods=header.get('mods',[])
    origin=2040 if any(str(m).startswith('xcom2 ') for m in mods) else 1999
    result=evaluate(events,body.get('alienMissions',[]),asof,policy,origin,body['difficulty'])
    result.update({'sourceSave':str(a.save.resolve()),'sourceSha256':sha,'policySha256':hashlib.sha256(a.policy.read_bytes()).hexdigest(),'sourceUnchanged':hashlib.sha256(a.save.read_bytes()).hexdigest()==sha})
    output=a.output or ROOT/'build'/'local'/'budget-reports'/(a.save.stem+'.budget.json');output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'report':str(output.resolve()),'currentMonth':result['monthly'][-1],'verifiedGainMissionCount':result['verifiedGainMissionCount'],'coverageWarnings':result['coverageWarnings'],'sourceUnchanged':result['sourceUnchanged']},indent=2))
if __name__=='__main__':main()
