"""Extract and mechanically validate manual responses; no model calls or execution."""
import argparse,collections,hashlib,importlib.util,json,re,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--responses',type=Path,default=ROOT/'llm_responses')
 p.add_argument('--packet',type=Path,default=ROOT/'docs/experiments/reference-planner-probe-v1/frozen_packet.json')
 p.add_argument('--out',type=Path,default=ROOT/'docs/experiments/reference-planner-probe-v1/analysis')
 a=p.parse_args();packet=json.loads(a.packet.read_text(encoding='utf-8-sig'))
 spec=importlib.util.spec_from_file_location('check',ROOT/'scripts/check-reference-portfolio.py')
 checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
 costs={'STR_ALIEN_RESEARCH':2,'STR_ALIEN_HARVEST':3,'STR_ALIEN_ABDUCTION':3,'STR_ALIEN_TERROR':4,'STR_ALIEN_RETALIATION':2,'STR_ALIEN_INFILTRATION':6,'STR_ALIEN_BASE':6}
 rows=[]
 for path in sorted(a.responses.glob('*.md')):
  raw=path.read_bytes();text=raw.decode('utf-8-sig');found=[]
  # Decode objects only; never evaluate transcript content or silently repair
  # operations. Markdown fences and export escape tags can wrap valid JSON.
  for match in re.finditer(r'\{',text):
   try:value,end=json.JSONDecoder().raw_decode(text[match.start():])
   except json.JSONDecodeError:continue
   if isinstance(value,dict) and 'operations' in value:found.append(value)
  if len(found)!=1:raise ValueError(f'{path.name}: expected exactly one portfolio, found {len(found)}')
  response=found[0]
  try:validation=checker.validate(response,packet)
  except (ValueError,KeyError,TypeError) as error:validation={'legal':False,'error':str(error)}
  actual=sum(costs[o['mission']] for o in response['operations'])
  rows.append({'file':path.name,'sha256':hashlib.sha256(raw).hexdigest(),
   'providerLabelFromFilename':path.stem.rsplit('_',1)[0],'runLabelFromFilename':path.stem.rsplit('_',1)[1],
   'modelVersion':'NOT_RECORDED','promptIdentity':'NOT_VERIFIED_FROM_TRANSCRIPTS',
   'portfolio':response,'validation':validation,
   'ineligibleOperations':[o for o in response['operations'] if o not in packet['eligibleOperations']],
   'arithmeticCorrect':type(response.get('total_cost')) is int and type(response.get('remaining')) is int and response['total_cost']==actual and response['remaining']==packet['nativeInput']['budget']['remaining']-actual})
 providers=sorted({r['providerLabelFromFilename'] for r in rows})
 summary={'runs':len(rows),'legal':sum(x['validation']['legal'] for x in rows),
  'arithmeticCorrect':sum(x['arithmeticCorrect'] for x in rows),
  'byProvider':{k:{'runs':sum(r['providerLabelFromFilename']==k for r in rows),'legal':sum(r['providerLabelFromFilename']==k and r['validation']['legal'] for r in rows)} for k in providers},
  'missionRuns':dict(collections.Counter(m for r in rows for m in {o['mission'] for o in r['portfolio']['operations']})),
  'spendingMedian':statistics.median(x['portfolio']['total_cost'] for x in rows),
  'referenceDecision':packet['decisionTime'],'newAPIorInferenceCalls':0,
  'setup':{'independentFreshChats':'USER_CONFIRMED','incognitoOrTemporary':'USER_REPORTED_WHERE_POSSIBLE','fullPromptIdentity':'NOT_VERIFIED_FROM_TRANSCRIPTS','modelsAndModes':'NOT_RECORDED'},
  'reviewLimits':'Single campaign state; manual model samples, not independent campaign outcomes. Narrative review is separate and unblinded.'}
 a.out.mkdir(parents=True,exist_ok=True)
 (a.out/'structural-results.json').write_text(json.dumps({'packetSha256':hashlib.sha256(a.packet.read_bytes()).hexdigest(),'summary':summary,'runs':rows},indent=2),encoding='utf-8')
 for row in rows:assert hashlib.sha256((a.responses/row['file']).read_bytes()).hexdigest()==row['sha256'],'Transcript changed'
 print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
