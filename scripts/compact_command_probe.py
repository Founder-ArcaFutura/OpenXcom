"""Experimental stable briefing contract. Never infers objective defeat from craft loss."""
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('adaptive', ROOT/'scripts/test-adaptive-responses.py')
adaptive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adaptive)
p = adaptive.p
OUTCOMES = {'UNKNOWN', 'SCOUT_LOST', 'DISRUPTED', 'COMPLETED'}
INVESTMENTS = {
 'ABDUCTION': 'ABDUCTION cost3: activity +2 cash,+1 adaptation',
 'BASE': 'BASE cost6: surviving +1-2 cash/month, progress, influence',
 'HARVEST': 'HARVEST cost3: activity +2 cash,+1 logistics',
 'INFILTRATION': 'INFILTRATION cost6: possible pact and base',
 'RESEARCH': 'RESEARCH cost2: flight +1 cash,+1 intelligence',
 'RETALIATION': 'RETALIATION cost2: possible base discovery; assault unavailable',
 'TERROR': 'TERROR cost4: delivered political pressure; no cash',
 'SAVE': 'SAVE: defer within carry cap; excess expires'}

def outcome(status='UNKNOWN', evidence=None):
    if status not in OUTCOMES:
        raise ValueError('Unknown outcome category')
    if status != 'UNKNOWN' and not evidence:
        raise ValueError('Explicit outcome requires source evidence')
    return {'status': status, 'evidence': evidence}

def briefing(data, result=None):
    """Map known observations only; no native whole-mission outcome inferred."""
    b, _, _, s = p.e.m.portfolio_input(data)
    result = result or outcome()
    outcome(result['status'], result['evidence'])
    return {'goal': 'Conquer Earth',
        'cash': {'now': b['remaining'], 'carry': b['carryCap']},
        'capability': {k: b[k] for k in ('intelligence','logistics','adaptation')},
        'gates': {'base': 'month1 logistics2', 'infiltration': 'month2 intelligence1 adaptation2'},
        'month': b['epochMonth'],
        'commitments': [[x['mission'].removeprefix('STR_ALIEN_'),x['region'].removeprefix('STR_')] for x in s['pendingOperations'][:3]],
        'interference': [[x['region'].removeprefix('STR_'),x['count']] for x in s['lossAssignments'][:3]],
        'outcome': result['status'],
        'limits': 'Loss locations uncertain; other regions unknown. Gains conditional; cash next month/capped. Odds unknown.'}

def packet(case):
    data = case['data']; state = briefing(data, case.get('result'))
    if case.get('result'):
        state['reviewed_operation']=['TERROR','SOUTHERN_AFRICA']
    if case['stage'] == 'TARGET':
        regions = sorted(c['region'].removeprefix('STR_') for c in data['knowledge']['candidates'] if c['mission']=='STR_ALIEN_HARVEST')
        state['task'] = 'Choose harvest region; seek capacity while considering interference'
        criteria = {r: r for r in regions}
    else:
        keys = {c['mission'].removeprefix('STR_ALIEN_') for c in data['knowledge']['candidates'] if p.e.m.PORTFOLIO_COSTS[c['mission']] <= data['budget']['remaining']}
        criteria = {k: INVESTMENTS[k] for k in sorted(keys)}
        criteria['SAVE'] = INVESTMENTS['SAVE']
    return {'state': p.e.m.canonical(state), 'criteria': criteria,
            'instructions': 'Choose an executable conquest investment using known gains, commitments and evidence.'}

def reference(packet):
    """Frozen illustrative policy, not an expert or optimal strategy label."""
    s=json.loads(packet['state']); options=packet['criteria']; losses=dict(s['interference'])
    if 'task' in s:
        return min(options, key=lambda r:(losses.get(r,0),r)), 'Least assigned interference; alphabetical tie break; unknown is not proven safe'
    c=s['capability']; pending={x[0] for x in s['commitments']}
    preferences=[]
    if c['logistics']<2: preferences.append('HARVEST')
    if c['adaptation']<2: preferences.append('ABDUCTION')
    if c['intelligence']<1: preferences.append('RESEARCH')
    preferences += ['BASE','INFILTRATION','TERROR','HARVEST','ABDUCTION','RESEARCH','RETALIATION','SAVE']
    if s['outcome']=='DISRUPTED': preferences=['HARVEST','ABDUCTION']+preferences
    # Diversify an existing commitment, without asserting it is the best strategy.
    eligible=[k for k in preferences if k in options]
    return next((k for k in eligible if k not in pending),eligible[0]), 'Fill progression gaps, diversify commitments, then persistent conquest; disrupted objective favors rebuilding'

def cases():
    _, source=adaptive.native_inputs(); result=[]
    for region in ('STR_EUROPE','STR_NORTH_AFRICA'):
        data=adaptive.loss_variant(source,region,5)
        result.append({'name':'heldout_target_'+region,'pair':'location','stage':'TARGET','data':data})
    # New gate axis rather than the previously tested logistics/base transition.
    for level in (1,2):
        data=adaptive.loss_variant(source,'STR_SOUTHERN_AFRICA',3)
        data['budget']['adaptation']=level;data['budget']['intelligence']=1
        if level<2:data['knowledge']['candidates']=[c for c in data['knowledge']['candidates'] if c['mission']!='STR_ALIEN_INFILTRATION']
        result.append({'name':f'heldout_adaptation_{level}','pair':'capability','stage':'PLAN','data':data})
    for status in ('UNKNOWN','SCOUT_LOST','DISRUPTED','COMPLETED'):
        data=adaptive.loss_variant(source,'STR_SOUTHERN_AFRICA',3)
        # No unresolved parent for the synthetic completed/disrupted operation.
        data['sitrep']['pendingOperations']=[];data['sitrep']['pendingTotal']=0;data['sitrep']['pendingTruncated']=False
        data['sitrep']['operationalReview']['pendingProgress']=[]
        data['sitrep']['operationalReview']['terror_objective_waves_pending']=0
        result.append({'name':'heldout_outcome_'+status,'pair':'outcome','stage':'PLAN','data':data,
            'result': outcome(status,None if status=='UNKNOWN' else 'SYNTHETIC_EXPLICIT_OBJECTIVE_RECEIPT'),
            'note':'Same synthetic previous terror assignment; no new cash or progress implied; completed means political objective, not conquest'})
    for c in result:p.e.m.portfolio_input(c['data'])
    return result
