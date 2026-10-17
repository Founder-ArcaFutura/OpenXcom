"""Replay exact frozen career-model packets with the publisher's English checkpoint."""
import csv,json,shutil
from pathlib import Path
import compact_command_probe as c

ROOT=c.ROOT
EXPECTED_BASE='891102d372688fc2a094dac56a384bc537b87c63f21f9f3dac0be2b7cbc8d86c'
OUT=ROOT/'build/local/base-laya-comparison-v1'
DOC=ROOT/'docs/experiments/base-laya-comparison-v1'

def source_rows():
    sources=[('compact',ROOT/'build/local/compact-command-v1/results.json'),
             ('adaptation',ROOT/'build/local/adaptive-responses-v2/summary.json')]
    rows=[]
    for suite,path in sources:
        data=json.loads(path.read_text())
        assert data['manifest']['model']['checkpointSha256']==c.p.e.m.V4_SHA256
        rows.extend((suite,path,row) for row in data['rows'])
    return rows

def preflight(agent,receipt):
    from laya.common import render_options
    question=receipt['question'];q=agent._to_internal(question)
    sizes=[1+len(agent.tok(' '+v.replace(agent.tok.mask_token,' '),add_special_tokens=False)['input_ids']) for v in render_options(q)]
    ins=len(agent.tok('choice question: '+q['ins'],add_special_tokens=False)['input_ids'])
    tokens=4+ins+sum(sizes)+len(agent.tok(receipt['state'],add_special_tokens=False)['input_ids'])
    if max(sizes)>49 or ins+sum(sizes)>agent.cfg['head_max_len'] or tokens>agent.cfg['max_len']:
        raise ValueError('Frozen packet exceeds base-model budget')

def load_base():
    import torch,laya
    checkpoint=ROOT/'build/local/base-laya-checkpoint'
    download=json.loads((checkpoint/'download-receipt.json').read_text())
    assert c.p.e.m.file_digest(checkpoint/'model.safetensors')==EXPECTED_BASE
    assert download['files']['model.safetensors']['sha256']==EXPECTED_BASE
    base=json.loads((checkpoint/'rl_agent_config.json').read_text())
    career=json.loads((ROOT/'build/local/laya-checkpoint/rl_agent_config.json').read_text())
    fields=('encoder','head_layers','max_len','head_max_len','temperature','temperature_by_options')
    assert all(base[k]==career[k] for k in fields),'Architecture or calibration mismatch'
    # Reuse pinned tokenizer/architecture metadata only, never overwrite the live staging area.
    for name in ('encoder','tokenizer'):
        shutil.copytree(ROOT/'build/local/laya-checkpoint'/name,checkpoint/name,dirs_exist_ok=True)
    torch.set_num_threads(4)
    agent=laya.Agent(str(checkpoint),device='cpu')
    agent.model.encoder.config.reference_compile=False
    return agent,{'checkpointSha256':EXPECTED_BASE,'repo':download['repo'],'revision':download['revision'],
        'encoderRevision':c.p.e.m.ENCODER_REVISION,'device':'cpu','torchVersion':torch.__version__,
        'layaVersion':laya.__version__,'matchingArchitectureAndCalibration':{k:base[k] for k in fields},
        'metadataSource':'Same pinned encoder/tokenizer as career comparator; base weights loaded strictly'}

def main():
    OUT.mkdir(parents=True,exist_ok=True);DOC.mkdir(parents=True,exist_ok=True)
    sources=source_rows()
    paths={Path(__file__),ROOT/'scripts/alien-command-model.py',ROOT/'scripts/campaign_plans.py',
        ROOT/'build/local/user/xcom1/Pre-Junes.sav',ROOT/'build/local/laya-checkpoint/model.safetensors',
        ROOT/'build/local/base-laya-checkpoint/rl_agent_config.json',ROOT/'build/local/base-laya-checkpoint/download-receipt.json',
        *[path for _,path,_ in sources]}
    hashes={str(path):c.p.e.m.file_digest(path) for path in paths}
    (OUT/'frozen.json').write_text(json.dumps({'hashes':hashes,'cases':len(sources),'components':sum(len(row['components']) for _,_,row in sources)},indent=2))
    agent,identity=load_base()
    for _,_,row in sources:
        for receipt in row['components']:preflight(agent,receipt)
    rows=[]
    for suite,path,career in sources:
        file=OUT/f"{suite}_{career['case']}_{career['family']}.json"
        receipts=[]
        for original in career['components']:
            q=original['question']
            _,receipt=c.p.e.m.checked_choice(agent,original['state'],q['criteria'],q['instructions'])
            assert receipt['packetSha256']==original['packetSha256'],'Paired packet content/order changed'
            assert receipt['tokenCount']==original['tokenCount'],'Paired tokenization changed'
            receipts.append(receipt)
        criteria=career['components'][0]['question']['criteria']
        choice,scores,votes,margin=c.p.aggregate_answers(receipts,criteria)
        row={'suite':suite,'case':career['case'],'family':career['family'],'choice':choice,
            'description':criteria[choice],'careerChoice':career['choice'],'careerDescription':criteria[career['choice']],
            'ruleChoice':career.get('ruleChoice'),'meanScores':scores,'careerMeanScores':career['meanScores'],
            'votes':votes,'margin':margin,'careerMargin':career['margin'],'components':receipts,
            'sourceReceiptFile':str(path),'sourceReceiptRowSha256':c.p.e.m.digest(career),'checkpointSha256':EXPECTED_BASE}
        file.write_text(json.dumps(row,indent=2));rows.append(row)
        print(json.dumps({k:row[k] for k in ('suite','case','family','description','careerDescription','margin')}),flush=True)
    assert all(c.p.e.m.file_digest(Path(path))==sha for path,sha in hashes.items())
    manifest={'model':identity,'hashes':hashes,'components':sum(len(row['components']) for row in rows),
        'liveChanged':False,'APICalls':0,'exactFrozenPacketReplay':True,'fullPortfolios':False,
        'limitation':'Publisher base is not proven to be the exact ancestor of career checkpoint; checkpoint comparison, not isolated causal attribution to career tuning'}
    (OUT/'results.json').write_text(json.dumps({'rows':rows,'manifest':manifest},indent=2))
    (DOC/'results.json').write_text(json.dumps({'rows':[{k:v for k,v in r.items() if k!='components'} for r in rows],'manifest':manifest},indent=2))
    with (DOC/'scores.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['suite','case','family','option','baseScore','careerScore','baseChosen','careerChosen'])
        for r in rows:
            for key,score in r['meanScores'].items():writer.writerow([r['suite'],r['case'],r['family'],key,score,r['careerMeanScores'][key],key==r['choice'],key==r['careerChoice']])
if __name__=='__main__':main()
