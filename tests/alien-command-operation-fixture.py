"""Scripted HTTP transport fixture; never represents learned model performance."""
import argparse, json, importlib.util
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
spec=importlib.util.spec_from_file_location("packet",Path(__file__).resolve().parents[1]/"scripts"/"alien-command-model.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
p=argparse.ArgumentParser();p.add_argument("--port",type=int,default=18868);p.add_argument("--mode",choices=["research","base","abstain","invalid"],required=True);a=p.parse_args()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def do_POST(self):
  data=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
  state,questions,mapping=m.build_packet(data)
  if a.mode=="abstain":
   proposal={"mission":"","region":"","reason":"MODEL_ABSTAIN","score":0,"evidenceIds":[]};status="ABSTAIN"
  else:
   candidate,belief=next((c,b) for c,b in mapping.values() if (c["mission"]=="STR_ALIEN_RETALIATION")== (a.mode=="base"))
   proposal={**candidate,"reason":"FIXTURE_OPERATION_TEST","score":belief["confidence"],"evidenceIds":belief["evidenceIds"]};status="PREDICTED"
   if a.mode=="invalid": proposal["evidenceIds"]=[999999]
  body=json.dumps({"schemaVersion":1,"checkpointSha256":m.V4_SHA256,"status":status,"state":state,"answer":{"probabilities":{"A":0.5,"B":0.5}},"proposal":proposal}).encode()
  self.send_response(200);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
HTTPServer(("127.0.0.1",a.port),Handler).serve_forever()
