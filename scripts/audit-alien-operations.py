"""Export the last native monthly reconciliation from a save without modifying it."""
import argparse,csv,hashlib,json
from pathlib import Path
import yaml

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();source=args.save.resolve();payload=source.read_bytes()
    documents=list(yaml.safe_load_all(payload.decode('utf-8-sig')))
    events=[json.loads(event) for event in documents[-1].get('alienCommand',{}).get('audit',[])]
    reviews=[event for event in events if event.get('kind')=='monthly_reconciliation']
    if not reviews:raise SystemExit('No native monthly reconciliation in this save yet. Advance through a monthly portfolio decision with the ledger build.')
    review=reviews[-1];args.out.mkdir(parents=True,exist_ok=True)
    output={'sourceSaveSha256':hashlib.sha256(payload).hexdigest(),'snapshotScope':'BEFORE_MONTHLY_DECISION',
            'review':review,'laterPortfolios':[event for event in events if event.get('kind')=='portfolio' and event['id']>review['id']]}
    (args.out/'monthly-review.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
    rows=review['ledger']['operations']
    fields=['missionId','decisionReceiptId','mission','region','cost','coverage','lifecycle','outcome','cashEarned','progressEarned','gainAt','unavailable','deliveryFact','lastEventAt']
    with (args.out/'operations.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    assert source.read_bytes()==payload,'Source save changed during read-only export'
    print(json.dumps({'period':review['period'],'operations':len(rows),'total':review['ledger']['total'],'truncated':review['ledger']['truncated'],'output':str(args.out),'sourceUnchanged':True}))
if __name__=='__main__':main()
