"""Build a standalone omniscient replay viewer from native tactical JSONL captures."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def read_capture(path):
    payload = path.read_bytes()
    lines = payload.splitlines()
    events, warnings = [], []
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            if index == len(lines) - 1 and not payload.endswith(b'\n'):
                warnings.append('Incomplete final record omitted; capture may still be running or was interrupted.')
                break
            raise ValueError(f'{path}: invalid record on line {index+1}')
        if event.get('protocol') != 'tactical-telemetry-v1' or 'units' not in event:
            raise ValueError(f'{path}: unsupported tactical record on line {index+1}')
        if event['sequence'] != len(events)+1:
            raise ValueError(f'{path}: non-contiguous event sequence')
        events.append(event)
    if not events:
        raise ValueError(f'{path}: no complete events')
    if events[-1]['event'] not in {'BATTLE_FINISH', 'BATTLE_ABORT', 'TEST_COMPLETE'}:
        warnings.append('Capture has no finish hook; it is a partial session or still in progress.')
    return {'name': path.name, 'source': str(path.resolve()),
            'sha256': hashlib.sha256(payload).hexdigest(), 'warnings': warnings, 'events': events}


def summarize(capture):
    events = capture['events']
    decisions = [event for event in events if event['event'] == 'AI_DECISION']
    errors = Counter(event['action']['result'] for event in events
                     if event.get('action', {}).get('result'))
    return {key: value for key, value in capture.items() if key != 'events'} | {
        'records': len(events), 'turnRange': [events[0]['turn'], events[-1]['turn']],
        'events': dict(Counter(event['event'] for event in events)),
        'aiActions': dict(Counter(event['action']['type'] for event in decisions)),
        'stateResultMessages': dict(errors),
        'observer': any(event['observer'] for event in events),
        'debugModeSeen': any(event['debugMode'] for event in events),
        'nativeCheatingSeen': any(event['nativeCheating'] for event in events)}


PAGE = r'''<!doctype html>
<html lang="en"><meta charset="utf-8"><title>Alien tactics inspector</title>
<style>
body{margin:20px;background:#111a23;color:#e5edf4;font:15px system-ui}h1{font-size:25px}button,select,input{font:inherit}button,select{padding:5px;margin:3px;background:#233544;color:#fff;border:1px solid #5f788c}input[type=range]{width:min(750px,90vw)}.layout{display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap}canvas{background:#182530;max-width:100%;border:1px solid #506678}table{border-collapse:collapse;font:13px ui-monospace,monospace}td,th{padding:5px 7px;border-bottom:1px solid #344958;text-align:left}tr[data-id]{cursor:pointer}tr.selected{background:#344d61}pre{white-space:pre-wrap;max-width:1000px;overflow-wrap:anywhere}.note{color:#adc2d1;max-width:1100px}#warning{color:#ffc475}#description{min-height:3em;max-width:1100px}label{margin-right:12px}
</style>
<h1>Alien tactics inspector</h1>
<p class="note">Omniscient observer record. AI contacts below are cached per-unit visible contacts, not a complete reconstruction of alien knowledge. Decisions are proposals; resolved states can be followed by reactions or explosions. Terrain updates at battle open and side boundaries.</p>
<label>Capture <select id="capture" aria-label="Capture"></select></label>
<div><button id="previous">Previous event</button><button id="next">Next event</button><button id="previousSide">Previous side boundary</button><button id="nextSide">Next side boundary</button></div>
<input id="timeline" type="range" min="0" value="0" aria-label="Event timeline"><span id="counter"></span>
<p id="warning"></p><p id="description"></p>
<label>Map level <select id="level" aria-label="Map level"></select></label>
<label><input id="nodes" type="checkbox" checked>Route nodes</label>
<label><input id="trail" type="checkbox" checked>Selected unit trail</label>
<p class="note">Blue: XCOM. Red: aliens. Gold: civilians. Cross: out of action. Pale squares: objects; lines: walls. Number: unit ID. Dashed arrow: requested action target, not the travelled path. Click a unit to inspect it.</p>
<div class="layout"><canvas id="map" width="600" height="600" aria-label="Tactical map"></canvas><div><p id="selected"></p><table><thead><tr><th>Unit</th><th>Side</th><th>HP</th><th>TU</th><th>Energy</th><th>AI mode</th><th>Patrol</th><th>Visible contacts</th><th>Area order</th></tr></thead><tbody id="units"></tbody></table></div></div>
<details><summary>Raw event</summary><pre id="raw"></pre></details>
<script id="data" type="application/json">__DATA__</script>
<script>
'use strict';
const captures=JSON.parse(document.getElementById('data').textContent);
const el=id=>document.getElementById(id), side=['XCOM','Alien','Civilian'], modes=['Patrol','Ambush','Combat','Escape'];
let events=[], index=0, selected=null, board=null;
const ctx=el('map').getContext('2d');
function text(id,value){el(id).textContent=value;}
function loadCapture(){events=captures[Number(el('capture').value)].events;index=0;selected=null;el('timeline').max=events.length-1;show();}
function jump(next){index=Math.max(0,Math.min(events.length-1,next));show();}
function boundary(direction){let next=index+direction;while(next>=0&&next<events.length){if(['SIDE_READY','BATTLE_OPEN'].includes(events[next].event)){jump(next);return;}next+=direction;}}
function show(){
 const event=events[index], previousLevel=Number(el('level').value)||0;
 board=null;for(let i=index;i>=0;i--){if(events[i].terrain){board=events[i];break;}}
 const size=board?board.mapSize:[60,60,1];
 el('level').replaceChildren();for(let z=0;z<size[2];z++){const option=new Option(String(z),String(z));el('level').add(option);}el('level').value=String(Math.min(previousLevel,size[2]-1));
 if(event.action&&event.action.actor>=0){selected=event.action.actor;}
 if(!event.units.some(u=>u.id===selected)){selected=event.units.find(u=>u.faction===1)?.id??null;}
 el('timeline').value=index;text('counter',`${index+1} / ${events.length}`);
 const capture=captures[Number(el('capture').value)];
 text('warning',capture.warnings.join(' ') + (event.debugMode?' Debug mode was enabled; turn handling may differ.':'') + (event.nativeCheating?' Native alien cheating flag is active.':''));
 let description=`Turn ${event.turn} · ${side[event.side]??event.side} · ${event.event} · ${event.mission}`;
 if(event.action)description+=` · Unit ${event.action.actor}: ${event.action.type} → [${event.action.target}]${event.event==='AI_DECISION'&&event.action.controller?' · '+event.action.controller:''}${event.action.result?' · result: '+event.action.result:''}`;
 text('description',description);text('raw',JSON.stringify(event,null,2));renderUnits();draw();
}
function renderUnits(){
 const event=events[index];el('units').replaceChildren();
 for(const unit of event.units){const row=document.createElement('tr');row.dataset.id=unit.id;row.className=unit.id===selected?'selected':'';
  const order=unit.order??{};
  const values=[unit.id,side[unit.faction]??unit.faction,unit.health,unit.tu,unit.energy,modes[unit.aiMode]??'—',`${unit.fromNode} → ${unit.toNode}`,unit.visibleIds.join(', ')||'—',order.revision?`${order.role} #${order.revision}: ${order.status}`:(order.status||'—')];
  for(const value of values){const cell=document.createElement('td');cell.textContent=String(value);row.append(cell);}
  row.onclick=()=>{selected=unit.id;el('level').value=String(Math.max(0,unit.position[2]));renderUnits();draw();};el('units').append(row);
 }
 const unit=event.units.find(u=>u.id===selected);text('selected',unit?`${unit.id} · ${unit.type} · position [${unit.position}] · morale ${unit.morale} · facing ${unit.direction} · ${unit.playerVisible?'visible to player':'hidden from player'}${unit.order?.revision?' · order '+unit.id+':'+unit.order.revision+' → ['+unit.order.post+'] since turn '+unit.order.assignedTurn:''}`:'Select a unit');
}
function draw(){
 const canvas=el('map'), event=events[index], z=Number(el('level').value), size=board?.mapSize??[60,60,1];
 const scale=Math.min(12,Math.floor(720/Math.max(size[0],size[1]))), pad=15;
 canvas.width=size[0]*scale+pad*2;canvas.height=size[1]*scale+pad*2;ctx.clearRect(0,0,canvas.width,canvas.height);
 const xy=p=>[pad+(p[0]+.5)*scale,pad+(p[1]+.5)*scale];
 for(const tile of board?.terrain??[]){if(tile[2]!==z)continue;const x=pad+tile[0]*scale,y=pad+tile[1]*scale,m=tile[3];
  ctx.fillStyle=m&1?'#253745':'#14202b';ctx.fillRect(x,y,scale,scale);
  if(m&8){ctx.fillStyle='#526373';ctx.fillRect(x+2,y+2,scale-3,scale-3);}
  ctx.strokeStyle='#c2ccd3';ctx.lineWidth=1;ctx.beginPath();if(m&2){ctx.moveTo(x,y);ctx.lineTo(x,y+scale);}if(m&4){ctx.moveTo(x,y);ctx.lineTo(x+scale,y);}ctx.stroke();
  if(tile[4]){ctx.fillStyle='#b8c5cf66';ctx.fillRect(x,y,scale,scale);}if(tile[5]){ctx.fillStyle='#ff8a4288';ctx.fillRect(x,y,scale,scale);}
 }
 if(el('nodes').checked)for(const node of board?.nodes??[]){if(node.position[2]!==z)continue;const [x,y]=xy(node.position);ctx.fillStyle=node.rank>=2?'#e7ad4b':'#7f8fa0';ctx.fillRect(x-1,y-1,3,3);}
 if(el('trail').checked&&selected!==null){ctx.strokeStyle='#7de2d299';ctx.lineWidth=2;ctx.beginPath();let drawing=false;for(let i=0;i<=index;i++){const unit=events[i].units.find(u=>u.id===selected);if(!unit||unit.position[2]!==z){drawing=false;continue;}const [x,y]=xy(unit.position);if(!drawing)ctx.moveTo(x,y);else ctx.lineTo(x,y);drawing=true;}ctx.stroke();}
 for(const unit of event.units){if(unit.position[2]!==z||unit.position[0]<0)continue;const [x,y]=xy(unit.position);ctx.strokeStyle=unit.id===selected?'white':'#111a23';ctx.fillStyle=['#69baff','#f27987','#ffd06b'][unit.faction]??'#aaa';ctx.lineWidth=unit.id===selected?2:1;ctx.beginPath();ctx.arc(x,y,Math.max(3,scale*.35),0,Math.PI*2);ctx.fill();ctx.stroke();
  if(unit.out){ctx.beginPath();ctx.moveTo(x-3,y-3);ctx.lineTo(x+3,y+3);ctx.moveTo(x+3,y-3);ctx.lineTo(x-3,y+3);ctx.stroke();}
  else {const angle=(unit.direction*45-90)*Math.PI/180;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+Math.cos(angle)*scale*.65,y+Math.sin(angle)*scale*.65);ctx.stroke();}
  ctx.fillStyle='#fff';ctx.font='9px monospace';ctx.fillText(String(unit.id),x+4,y-4);
 }
 const selectedUnit=event.units.find(u=>u.id===selected), post=selectedUnit?.order?.post;
 if(selectedUnit?.order?.assignedTurn>=0&&post?.[2]===z){const [tx,ty]=xy(post);ctx.strokeStyle='#ffd06b';ctx.lineWidth=2;ctx.strokeRect(tx-6,ty-6,12,12);ctx.font='11px monospace';ctx.fillStyle='#ffd06b';ctx.fillText('POST',tx+8,ty+4);}
 const action=event.action, actor=action&&event.units.find(u=>u.id===action.actor);
 if(actor&&actor.position[2]===z&&action.target[2]===z&&action.target[0]>=0){const [x,y]=xy(actor.position),[tx,ty]=xy(action.target);ctx.setLineDash([4,3]);ctx.strokeStyle='#b8f5bf';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(tx,ty);ctx.stroke();ctx.setLineDash([]);ctx.strokeRect(tx-4,ty-4,8,8);}
}
captures.forEach((capture,i)=>el('capture').add(new Option(`${capture.events[0].defendExperiment?'DEFEND':'STOCK'} · turn ${capture.events[0].turn} · ${capture.name}`,String(i))));
el('capture').onchange=loadCapture;el('timeline').oninput=()=>jump(Number(el('timeline').value));
el('previous').onclick=()=>jump(index-1);el('next').onclick=()=>jump(index+1);el('previousSide').onclick=()=>boundary(-1);el('nextSide').onclick=()=>boundary(1);
['level','nodes','trail'].forEach(id=>el(id).onchange=draw);
el('map').onclick=event=>{const rect=el('map').getBoundingClientRect(),size=board?.mapSize??[60,60,1],scale=Math.min(12,Math.floor(720/Math.max(size[0],size[1])));const x=(event.clientX-rect.left)*el('map').width/rect.width,y=(event.clientY-rect.top)*el('map').height/rect.height,z=Number(el('level').value);let nearest=null,distance=Infinity;for(const unit of events[index].units){if(unit.position[2]!==z)continue;const dx=x-(15+(unit.position[0]+.5)*scale),dy=y-(15+(unit.position[1]+.5)*scale),d=dx*dx+dy*dy;if(d<distance){nearest=unit;distance=d;}}if(nearest&&distance<scale*scale){selected=nearest.id;renderUnits();draw();}};
loadCapture();
</script></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, action='append')
    parser.add_argument('--capture-dir', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    paths = list(args.capture or [])
    if args.capture_dir:
        paths.extend(sorted(args.capture_dir.glob('tactical-*.jsonl')))
    paths = list(dict.fromkeys(path.resolve() for path in paths))
    if not paths:
        parser.error('No captures found. Supply --capture or --capture-dir.')
    captures = [read_capture(path) for path in paths]
    args.out.mkdir(parents=True, exist_ok=True)
    data = json.dumps(captures, ensure_ascii=True).replace('<', '\\u003c')
    (args.out / 'index.html').write_text(PAGE.replace('__DATA__', data), encoding='utf-8')
    summary = [summarize(capture) for capture in captures]
    (args.out / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({'captures': len(captures), 'records': sum(len(c['events']) for c in captures),
                      'viewer': str((args.out / 'index.html').resolve())}))


if __name__ == '__main__':
    main()
