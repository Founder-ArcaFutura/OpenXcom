"""Create isolated save fixtures; never write source campaign files."""
import argparse,hashlib,json
from pathlib import Path
import yaml
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--logistics',type=int);a=p.parse_args()
raw=a.source.read_bytes();documents=list(yaml.safe_load_all(raw.decode('utf-8-sig')))
if a.logistics is not None:documents[-1]['alienCommand']['budget']['logistics']=a.logistics
# Re-encode only owned fixtures; preserve every other parsed field.
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(yaml.safe_dump_all(documents,sort_keys=False,allow_unicode=True),encoding='utf-8')
assert hashlib.sha256(a.source.read_bytes()).digest()==hashlib.sha256(raw).digest()
print(json.dumps({'source':str(a.source),'sourceSha256':hashlib.sha256(raw).hexdigest(),'fixture':str(a.out),'logistics':a.logistics}))
