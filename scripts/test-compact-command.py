"""Run frozen compact-context diagnostics against a transparent rule reference."""
import argparse,csv,json,time
from pathlib import Path
import compact_command_probe as c

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--checkpoint',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    cases=c.cases();packets={x['name']:c.packet(x) for x in cases}
    tracked=[Path(__file__),c.ROOT/'scripts/compact_command_probe.py',c.ROOT/'build/local/user/xcom1/Pre-Junes.sav',c.ROOT/'scripts/campaign_plans.py',c.ROOT/'scripts/alien-command-model.py']
    hashes={str(x):c.p.e.m.file_digest(x) for x in tracked}
    frozen={'cases':cases,'packets':packets,'hashes':hashes,'rules':{name:c.reference(packet) for name,packet in packets.items()},'heldoutMeaning':'New synthetic scenarios fixed before inference; not a blinded independent benchmark','liveChanged':False,'nativeOutcomeWiring':False}
    (args.out/'frozen.json').write_text(json.dumps(frozen,indent=2))
    agent,identity=c.p.e.m.load_agent(args.checkpoint,'cpu',c.p.e.m.V4_SHA256)
    # Validate every rotation before any prediction, preventing partial-run budgeting bias.
    from laya.common import render_options
    for packet in packets.values():
        q=agent._to_internal({'type':'choice','instructions':packet['instructions'],'criteria':packet['criteria']})
        lengths=[1+len(agent.tok(' '+v.replace(agent.tok.mask_token,' '),add_special_tokens=False)['input_ids']) for v in render_options(q)]
        ins=len(agent.tok('choice question: '+q['ins'],add_special_tokens=False)['input_ids'])
        total=4+ins+sum(lengths)+len(agent.tok(packet['state'],add_special_tokens=False)['input_ids'])
        assert max(lengths)<=49 and ins+sum(lengths)<=agent.cfg['head_max_len'] and total<=agent.cfg['max_len'],(total,lengths)
    rows=[]
    for case in cases:
        packet=packets[case['name']]
        for family in ('A','B'):
            receipts=[c.p.e.m.checked_choice(agent,packet['state'],options,packet['instructions'])[1] for options in c.p.families(packet['criteria'],family)]
            choice,scores,votes,margin=c.p.aggregate_answers(receipts,packet['criteria'])
            rule,reason=c.reference(packet)
            row={'case':case['name'],'pair':case['pair'],'family':family,'choice':choice,'ruleChoice':rule,'ruleReason':reason,'meanScores':scores,'votes':votes,'margin':margin,'components':receipts}
            rows.append(row);(args.out/(case['name']+'_'+family+'.json')).write_text(json.dumps(row,indent=2));print(json.dumps({k:row[k] for k in ('case','family','choice','ruleChoice','margin')}),flush=True)
    assert all(c.p.e.m.file_digest(Path(path))==sha for path,sha in hashes.items())
    manifest={'model':identity,'hashes':hashes,'APICalls':0,'liveChanged':False,'components':sum(len(r['components']) for r in rows),'fullPortfolios':False}
    (args.out/'results.json').write_text(json.dumps({'rows':rows,'manifest':manifest},indent=2))
    dest=c.ROOT/'docs/experiments/compact-command-v1';dest.mkdir(parents=True,exist_ok=True)
    (dest/'results.json').write_text(json.dumps({'rows':[{k:v for k,v in r.items() if k!='components'} for r in rows],'manifest':manifest},indent=2))
    with (dest/'scores.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['case','family','option','score','votes','chosen','ruleChoice'])
        for r in rows:
            for key,value in r['meanScores'].items():writer.writerow([r['case'],r['family'],key,value,r['votes'][key],key==r['choice'],r['ruleChoice']])
if __name__=='__main__':main()
