"""Verify native reconciliation, selected operation links and model admission on a copied save."""
import argparse,importlib.util,json
from pathlib import Path
import yaml

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--learned',action='store_true');args=parser.parse_args()
    spec=importlib.util.spec_from_file_location('ledger_model',Path(__file__).with_name('alien-command-model.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    save=list(yaml.safe_load_all((args.root/'xcom1/transition-result.sav').read_text(encoding='utf-8-sig')))[-1]
    audit=[json.loads(raw) for raw in save['alienCommand']['audit']]
    decision=next(e for e in reversed(audit) if e['kind']=='portfolio')
    assert decision['status'] in {'PORTFOLIO_EXECUTED','SAVED_RESOURCES'}
    m.portfolio_input(decision['input'])
    before=decision['input']['operationLedger'];period=decision['gameTime'][:7]
    reviews=[e for e in audit if e['kind']=='monthly_reconciliation' and e['period']==period]
    assert len(reviews)==1 and reviews[0]['ledger']==before
    after=json.loads((args.root/'xcom1/transition-ledger.json').read_text())
    m.validate_operation_ledger(after)
    by_id={row['missionId']:row for row in after['operations']}
    for operation_id in decision['missionIds']:
        row=by_id[operation_id]
        assert row['decisionReceiptId']==decision['id'] and row['coverage']=='COMPLETE_FROM_ASSIGNMENT'
    response=json.loads(decision['response'])
    if args.learned:
        assert response['portfolioPromptVersion']=='progressive-portfolio-v10'
        assert response['inputSha256']==m.digest(decision['input'])
        assert response['status'] in {'PREDICTED','SAVE_RESOURCES'}
    summary={'period':period,'status':decision['status'],'linkedOperations':len(decision['missionIds']),
        'reviewedOperations':len(before['operations']),'reviewedVerifiedGains':sum(row['outcome']=='GAIN_VERIFIED' for row in before['operations']),
        'legacyPartialOperations':sum(row['coverage']=='PARTIAL_LEGACY' for row in before['operations']),
        'inputBytes':len(m.canonical(decision['input']).encode()),
        'maxModelTokens':max((row.get('tokenCount',0) for row in response.get('decisions',[])),default=0),
        'learned':args.learned,'snapshotMatchesModelInput':True,'duplicateReconciliation':False}
    (args.root/'review/validation.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary))
if __name__=='__main__':main()
