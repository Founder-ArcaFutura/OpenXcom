"""Scripted portfolio transport fixture. Not evidence of learned strategy."""
import argparse,json
from http.server import BaseHTTPRequestHandler,HTTPServer
p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=18870);p.add_argument('--mode',choices=['valid','save','invalid','duplicate','overbudget','invalidstrategy'],required=True);a=p.parse_args()
SHA='bcbb891d21cf081a9d7a941b97f8b0f10cf3dac7473b4b9450fab0d07b885175'
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  if self.path=='/recon':
   result={'schemaVersion':1,'checkpointSha256':SHA,'status':'NO_ADMITTED_EVIDENCE'}
  else:
   menu=data['knowledge']['candidates'];ops=[]
   search=next(c for c in menu if c['mission']=='STR_ALIEN_RETALIATION')
   for c in menu:
    if c['mission'] in ['STR_ALIEN_RESEARCH','STR_ALIEN_PROBE_MISSION','STR_ALIEN_RETALIATION'] and c not in ops:
     ops.append(c)
     if len(ops)==3:break
   ops[2]=search
   if a.mode=='save':ops=[]
   if a.mode=='invalid':ops[2]={'mission':'STR_SECRET','region':'STR_HIDDEN_BASE'}
   if a.mode=='duplicate':ops[2]=ops[0]
   if a.mode=='overbudget':
    costly=[c for c in menu if c['mission'] in ['STR_ALIEN_TERROR','STR_ALIEN_SURFACE_ATTACK']]
    ops=costly[:3]
   result={'schemaVersion':1,'protocol':'alien-strategy-laya-v2','checkpointSha256':SHA,'strategy':'INTELLIGENCE','status':'PREDICTED' if ops else 'SAVE_RESOURCES','operations':ops}
   if a.mode=='invalidstrategy':result['strategy']='SECRET_OMNISCIENT_ASSAULT'
  body=json.dumps(result).encode();self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
HTTPServer(('127.0.0.1',a.port),Handler).serve_forever()
