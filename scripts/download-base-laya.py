"""Download and pin only the publisher's English Laya checkpoint for offline comparison."""
import hashlib,json,os,ssl
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
dest=ROOT/'build/local/base-laya-checkpoint'
dest.mkdir(parents=True,exist_ok=True)
# Use the OS-trusted certificate store for this process; keep TLS verification on.
if os.name=='nt':
    import certifi
    bundle=dest/'windows-trusted-ca.pem'
    pem=Path(certifi.where()).read_text()
    for store in ('ROOT','CA'):
        for cert,encoding,_ in ssl.enum_certificates(store):
            if encoding=='x509_asn':pem+='\n'+ssl.DER_cert_to_PEM_cert(cert)
    bundle.write_text(pem)
    os.environ['REQUESTS_CA_BUNDLE']=str(bundle)
os.environ['HF_HUB_DISABLE_XET']='1'
from huggingface_hub import HfApi,hf_hub_download
repo='convaiinnovations/laya'
info=HfApi().model_info(repo,files_metadata=True,token=False)
revision=info.sha
files={x.rfilename:x for x in info.siblings}
receipt={'repo':repo,'revision':revision,'files':{}}
for name in ('model.safetensors','rl_agent_config.json','README.md'):
    path=Path(hf_hub_download(repo,name,revision=revision,local_dir=dest,token=False))
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    lfs=files[name].lfs
    expected=getattr(lfs,'sha256',None) if lfs else None
    if expected:assert digest==expected,'Publisher LFS hash mismatch'
    receipt['files'][name]={'sha256':digest,'bytes':path.stat().st_size,'publisherLfsSha256':expected}
    print(json.dumps({'file':name,**receipt['files'][name]}),flush=True)
receipt['paidInferenceCalls']=0
(dest/'download-receipt.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({'revision':revision,'directory':str(dest)}),flush=True)
