"""Verify exact paired replay and export base/career component comparisons."""
import csv,json
from pathlib import Path
import compact_command_probe as c

ROOT=c.ROOT
raw=ROOT/'build/local/base-laya-comparison-v1'
dest=ROOT/'docs/experiments/base-laya-comparison-v1'
data=json.loads((raw/'results.json').read_text())
assert len(data['rows'])==32 and data['manifest']['components']==238
assert c.p.e.m.file_digest(ROOT/'build/local/base-laya-checkpoint/model.safetensors')==data['manifest']['model']['checkpointSha256']
for path,sha in data['manifest']['hashes'].items():assert c.p.e.m.file_digest(Path(path))==sha
original={}
for suite,file in [('compact','compact-command-v1/results.json'),('adaptation','adaptive-responses-v2/summary.json')]:
    for row in json.loads((ROOT/'build/local'/file).read_text())['rows']:
        original[(suite,row['case'],row['family'])]=row
components=[]
stats={'components':238,'maxTokens':0,'suites':{},'choices':[]}
for row in data['rows']:
    career=original[(row['suite'],row['case'],row['family'])]
    assert c.p.e.m.digest(career)==row['sourceReceiptRowSha256']
    criteria=career['components'][0]['question']['criteria']
    choice,scores,votes,margin=c.p.aggregate_answers(row['components'],criteria)
    assert (choice,scores,votes,margin)==(row['choice'],row['meanScores'],row['votes'],row['margin'])
    for i,(base,old) in enumerate(zip(row['components'],career['components'])):
        assert base['packetSha256']==old['packetSha256']
        assert base['state']==old['state'] and list(base['question']['criteria'].items())==list(old['question']['criteria'].items())
        assert base['tokenCount']==old['tokenCount']
        stats['maxTokens']=max(stats['maxTokens'],base['tokenCount'])
        for key,value in base['answer']['probabilities'].items():
            components.append([row['suite'],row['case'],row['family'],i,key,value,old['answer']['probabilities'][key],base['packetSha256']])
    stats['choices'].append({k:row[k] for k in ('suite','case','family','description','careerDescription','margin','careerMargin')})
for suite in ('compact','adaptation'):
    rows=[r for r in data['rows'] if r['suite']==suite]
    pairs={name:[r for r in rows if r['case']==name] for name in {r['case'] for r in rows}}
    stats['suites'][suite]={'aggregates':len(rows),'baseCareerChoiceAgreement':sum(r['choice']==r['careerChoice'] for r in rows),
        'baseFamilyAgreement':sum(p[0]['choice']==p[1]['choice'] for p in pairs.values()),
        'careerFamilyAgreement':sum(p[0]['careerChoice']==p[1]['careerChoice'] for p in pairs.values())}
with (dest/'component-scores.csv').open('w',newline='') as f:
    writer=csv.writer(f);writer.writerow(['suite','case','family','rotation','option','baseScore','careerScore','packetSha256']);writer.writerows(components)
with (dest/'choices.csv').open('w',newline='') as f:
    writer=csv.writer(f);writer.writerow(['suite','case','family','baseChoice','careerChoice','baseMargin','careerMargin'])
    for row in data['rows']:writer.writerow([row[k] for k in ('suite','case','family','description','careerDescription','margin','careerMargin')])
(dest/'checks.json').write_text(json.dumps(stats,indent=2))
print(json.dumps(stats,indent=2))
