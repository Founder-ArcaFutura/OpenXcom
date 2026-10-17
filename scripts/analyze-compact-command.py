"""Recompute results and export complete component scores for the compact probe."""
import csv
import json
from pathlib import Path
import compact_command_probe as c

root=c.ROOT/'build/local/compact-command-v1'
dest=c.ROOT/'docs/experiments/compact-command-v1'
data=json.loads((root/'results.json').read_text())
frozen=json.loads((root/'frozen.json').read_text())
assert len(data['rows'])==16
for path,sha in data['manifest']['hashes'].items():assert c.p.e.m.file_digest(Path(path))==sha
assert c.p.e.m.file_digest(c.ROOT/'build/local/user/xcom1/Pre-Junes.sav')=='d095e3dd2850ee74751309d8a7570356aff20577b12916b434a3345f296d3ec7'
components=[]
for row in data['rows']:
    packet=frozen['packets'][row['case']]
    choice,scores,votes,margin=c.p.aggregate_answers(row['components'],packet['criteria'])
    assert (choice,scores,votes,margin)==(row['choice'],row['meanScores'],row['votes'],row['margin'])
    assert c.reference(packet)[0]==row['ruleChoice']
    orders=c.p.families(packet['criteria'],row['family'])
    assert len(orders)==len(row['components'])
    for i,(r,order) in enumerate(zip(row['components'],orders)):
        assert r['state']==packet['state'] and list(r['question']['criteria'])==list(order)
        for key,score in r['answer']['probabilities'].items():
            components.append([row['case'],row['family'],i,key,score,r['tokenCount'],r['packetSha256']])
with (dest/'component-scores.csv').open('w',newline='') as f:
    writer=csv.writer(f);writer.writerow(['case','family','rotation','option','score','tokens','packetSha256']);writer.writerows(components)
stats={'components':data['manifest']['components'],'maxTokens':max(r['tokenCount'] for row in data['rows'] for r in row['components']),
       'familyAgreement':sum(a['choice']==b['choice'] for a,b in zip(data['rows'][::2],data['rows'][1::2])),
       'ruleAgreement':sum(row['choice']==row['ruleChoice'] for row in data['rows']),
       'choiceTable':[{k:row[k] for k in ('case','family','choice','ruleChoice','margin')} for row in data['rows']]}
(dest/'checks.json').write_text(json.dumps(stats,indent=2))
print(json.dumps(stats,indent=2))
