"""Check a manually supplied JSON portfolio against a frozen probe; never executes it."""
import argparse,json
from pathlib import Path

def validate(response,packet):
 costs={'STR_ALIEN_RESEARCH':2,'STR_ALIEN_HARVEST':3,'STR_ALIEN_ABDUCTION':3,'STR_ALIEN_TERROR':4,'STR_ALIEN_RETALIATION':2,'STR_ALIEN_INFILTRATION':6,'STR_ALIEN_BASE':6}
 b=packet['nativeInput']['budget'];ops=response['operations']
 if not isinstance(ops,list) or len(ops)>b['maxOperations']:raise ValueError('Operation capacity exceeded')
 seen=set();spent=0
 for op in ops:
  if not isinstance(op,dict) or set(op)!={'mission','region'} or op not in packet['eligibleOperations']:raise ValueError('Ineligible operation')
  pair=(op['mission'],op['region'])
  if pair in seen:raise ValueError('Duplicate operation')
  seen.add(pair);spent+=costs[op['mission']]
 if spent>b['remaining']:raise ValueError('Over budget')
 if type(response['total_cost']) is not int or type(response['remaining']) is not int or response['total_cost']!=spent or response['remaining']!=b['remaining']-spent:raise ValueError('Incorrect totals')
 return {'legal':True,'operations':len(ops),'spent':spent,'remaining':b['remaining']-spent,'carryIfNoFurtherSpend':min(b['remaining']-spent,b['carryCap']),'expiresIfNoFurtherSpend':max(0,b['remaining']-spent-b['carryCap']),'strategicMerit':'NOT_SCORED','nativeExecution':False}

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('response',type=Path);p.add_argument('--packet',type=Path,default=Path(__file__).resolve().parents[1]/'docs/experiments/reference-planner-probe-v1/frozen_packet.json');a=p.parse_args()
 try:print(json.dumps(validate(json.loads(a.response.read_text(encoding='utf-8-sig')),json.loads(a.packet.read_text(encoding='utf-8-sig'))),indent=2))
 except (ValueError,KeyError,TypeError) as error:raise SystemExit('INVALID: '+str(error))
