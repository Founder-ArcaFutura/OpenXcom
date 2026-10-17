"""Descriptive paired factorial contrasts; no statistical independence claims."""

import argparse,collections,itertools,json

from pathlib import Path

import importlib.util

ROOT=Path(__file__).resolve().parents[1]

spec=importlib.util.spec_from_file_location('factorial',ROOT/'scripts/test-conquest-factorial.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)



def metrics(row,data):

 ops=row['operations'];counts=collections.Counter(o['mission'].removeprefix('STR_ALIEN_') for o in ops);spent=data['budget']['remaining']-row['remainingProposed']

 return {**{name:counts[name] for name in ('RESEARCH','HARVEST','ABDUCTION','TERROR','INFILTRATION','RETALIATION')},'spend':spent,'spendFraction':spent/data['budget']['remaining'],'deferAll':int(not ops),'operationCount':len(ops),'missionTypes':len(counts)}

def contrasts(cells,keys):

 result={}

 for size in range(1,5):

  for subset in itertools.combinations(f.FACTORS,size):

   effect={k:0. for k in keys}

   for condition,values in cells.items():

    config=dict(zip(f.FACTORS,map(int,condition)));sign=(-1)**(size-sum(config[x] for x in subset))

    for k in keys:effect[k]+=sign*values[k]*(2**size/16)

   result[' x '.join(subset)]=effect

 return result



def main():

 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)

 source=json.loads((a.input/'summary.json').read_text());rows=source['rows'];assert len(rows)==255

 data={month.name:json.loads((month/'input.json').read_text()) for month in a.input.glob('1999-*')}

 annotated=[];max_tokens=0;new_inferences=automatic=cache_hits=0

 for row in rows:

  assert row['status']!='REJECTED',row

  packet=data[row['decision'][:7]];f.n.w.validate(row['operations'],packet)

  assert row['remainingProposed']==packet['budget']['remaining']-sum(f.e.m.PORTFOLIO_COSTS[x['mission']] for x in row['operations'])

  annotated.append({**row,'metrics':metrics(row,packet)})

  receipt=json.loads((a.input/row['decision'][:7]/(row['condition']+'-'+row['order']+'.json')).read_text())

  for d in receipt['decisions']:

   max_tokens=max(max_tokens,d.get('tokenCount',0))

   if d.get('inferenceSource')=='EXACT_ORDERED_PACKET_CACHE':cache_hits+=1

   elif d.get('source')=='ONLY_ELIGIBLE_CHOICE':automatic+=1

   else:new_inferences+=1

 for manifest in a.input.glob('1999-*/manifest.json'):

  m=json.loads(manifest.read_text());assert f.e.m.file_digest(m['source'])==m['sourceSha256']

  for name,sha in m['scripts'].items():assert f.e.m.file_digest(ROOT/name)==sha

  assert f.e.m.digest(data[manifest.parent.name])==m['pairedInputSha256']

 keys=list(annotated[0]['metrics']);cells={};by_condition={};by_order={}

 for condition in ['live_wording',*[f.code(c) for c in f.configurations()]]:

  group=[r for r in annotated if r['condition']==condition];assert len(group)==15

  by_condition[condition]={'mean':{k:sum(r['metrics'][k] for r in group)/15 for k in keys},'totals':{k:sum(r['metrics'][k] for r in group) for k in keys},'exactAgreementAllOrders':0,'mixAgreementAllOrders':0,'terrorPresenceAllOrders':0}

  for month in data:

   rs=[r for r in group if r['decision'].startswith(month)];assert len(rs)==3

   by_condition[condition]['exactAgreementAllOrders']+=int(all(r['operations']==rs[0]['operations'] for r in rs))

   by_condition[condition]['mixAgreementAllOrders']+=int(all(collections.Counter(o['mission'] for o in r['operations'])==collections.Counter(o['mission'] for o in rs[0]['operations']) for r in rs))

   by_condition[condition]['terrorPresenceAllOrders']+=int(all(r['metrics']['TERROR']>0 for r in rs))

  if condition!='live_wording':cells[condition]=by_condition[condition]['mean']

 effects=contrasts(cells,keys)

 for order in f.ORDERS:

  group=[r for r in annotated if r['condition']!='live_wording' and r['order']==order]

  by_order[order]={k:sum(r['metrics'][k] for r in group)/len(group) for k in keys}

 by_order_effects={}

 for order in f.ORDERS:

  cell={condition:{k:sum(r['metrics'][k] for r in annotated if r['condition']==condition and r['order']==order)/5 for k in keys} for condition in cells}

  by_order_effects[order]=contrasts(cell,keys)

 by_month={}

 for month in data:

  cell={condition:{k:sum(r['metrics'][k] for r in annotated if r['condition']==condition and r['decision'].startswith(month))/3 for k in keys} for condition in cells}

  by_month[month]=contrasts(cell,keys)

 wording_effect={k:by_condition['0000']['mean'][k]-by_condition['live_wording']['mean'][k] for k in keys}
 result={'wordingEffect':wording_effect,'conditionStats':by_condition,'contrasts':effects,'byOrder':by_order,'byOrderContrasts':by_order_effects,'byMonthContrasts':by_month,'rows':annotated,'validation':{'portfolios':255,'legal':255,'sourceAndScriptHashesUnchanged':True,'maxTokens':max_tokens,'newModelInferences':new_inferences,'uncachedAutomaticDecisions':automatic,'cacheReuses':cache_hits,'runtimeNewCalls':source['newCalls'],'runtimeCacheHits':source['cacheHits']},'interpretation':'Deterministic fixed-state prompt sensitivity; no p-values, quality score or alternate campaign simulation.'}

 assert source['newCalls']==new_inferences+automatic;assert source['cacheHits']==cache_hits

 (a.out/'results.json').write_text(json.dumps(result,indent=2))

 import os
 os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'build/local/matplotlib-factorial'))
 import matplotlib

 matplotlib.use('Agg')

 import matplotlib.pyplot as plt

 import numpy as np

 conditions=['live_wording',*[f.code(c) for c in f.configurations()]];months=sorted(data)

 fig,axes=plt.subplots(1,3,figsize=(13,10),sharey=True)

 for ax,order in zip(axes,f.ORDERS):

  grid=np.zeros((17,5));labels={}

  for i,condition in enumerate(conditions):

   for j,month in enumerate(months):

    row=next(r for r in annotated if r['condition']==condition and r['order']==order and r['decision'].startswith(month))

    grid[i,j]=row['metrics']['TERROR'];labels[i,j]='S' if row['metrics']['deferAll'] else str(row['metrics']['TERROR'])

  im=ax.imshow(grid,cmap='Purples',vmin=0,vmax=4,aspect='auto')

  for (i,j),label in labels.items():ax.text(j,i,label,ha='center',va='center',color='white' if grid[i,j]>=3 else '#202020',fontsize=9)

  ax.set_xticks(range(5),['Feb','Mar','Apr','May','Jun']);ax.set_yticks(range(17),['live wording',*[f.code(c) for c in f.configurations()]])

  ax.set_title(order);ax.set_xlabel('Recorded decision state')

  ax.set_xticks(np.arange(-.5,5,1),minor=True);ax.set_yticks(np.arange(-.5,17,1),minor=True);ax.grid(which='minor',color='#dddddd',linewidth=.5);ax.tick_params(which='minor',bottom=False,left=False)

 axes[0].set_ylabel('Condition: C S P T (0=off, 1=on)')

 fig.suptitle('Selected terror missions per portfolio - not campaign success',fontsize=14)

 fig.text(.5,.025,'S = save everything. C: remove research cash; S bit: research saturation; P: productive bonus; T: terror reward.\nFixed campaign snapshots; no mission outcomes simulated.',ha='center',fontsize=9)

 fig.subplots_adjust(left=.13,right=.89,bottom=.11,top=.93,wspace=.12)

 fig.colorbar(im,cax=fig.add_axes([.91,.3,.015,.4]),ticks=range(5),label='Terror missions selected')

 fig.savefig(a.out/'terror-matrix.png',dpi=150);fig.savefig(a.out/'terror-matrix.svg');plt.close(fig)



 print(json.dumps(result['validation']));print('MAIN EFFECTS')

 for factor in f.FACTORS:print(factor,json.dumps(effects[factor]))

 print('ORDER MEANS',json.dumps(by_order))

 print('CONDITIONS')

 for condition,stats in by_condition.items():print(condition,json.dumps(stats))

if __name__=='__main__':main()

