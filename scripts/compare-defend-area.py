"""Compare stock and persistent area orders on the same disposable save and RNG."""
import argparse
from collections import Counter
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save', type=Path, default=ROOT / 'build/local/user/xcom1/Three off the ramp.sav')
    parser.add_argument('--phases', type=int, choices=range(1,7), default=3)
    args = parser.parse_args()
    out = ROOT / 'build/local' / ('defend-comparison-' + dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    out.mkdir()
    captures, results = [], []
    for arm in ['stock', 'defend']:
        arm_root = out / arm
        command = [sys.executable, str(ROOT / 'scripts/test-tactical-telemetry.py'), '--save', str(args.save),
                   '--phases', str(args.phases), '--out', str(arm_root)]
        if arm == 'defend':
            command.append('--defend')
        process = subprocess.run(command, cwd=ROOT)
        if process.returncode:
            (out / 'manifest.json').write_text(json.dumps({'status': 'FAIL', 'failedArm': arm,
                                                          'source': str(args.save.resolve())}, indent=2), encoding='utf-8')
            raise SystemExit(f'Comparison stopped: {arm} failed; see {arm_root}')
        manifest = json.loads((arm_root / 'manifest.json').read_text())
        capture = next((arm_root / 'observer/xcom1').glob('tactical-*.jsonl'))
        captures.append(capture)
        events = [json.loads(line) for line in capture.read_text().splitlines()]
        boundaries = [e for e in events if e['event'] == 'TEST_PHASE_COMPLETE']
        results.append({'arm': arm, 'initialRng': events[0]['rng'], 'initialUnits': events[0]['units'],
                        'originalUnchanged': manifest['originalUnchanged'],
                        'actions': dict(Counter(e['action']['type'] for e in events if e['event']=='AI_DECISION')),
                        'orderTransitions': sum(e['event']=='ORDER_TRANSITION' for e in events),
                        'movementSteps': sum(e['event']=='MOVE_STEP' for e in events),
                        'boundaries': [{'turn': e['turn'], 'activeHostiles': sum(not u['out'] and u['faction']==1 for u in e['units']),
                                        'activeXcom': sum(not u['out'] and u['faction']==0 for u in e['units']),
                                        'orderedUnits': [{'unit': u['id'], 'position': u['position'], 'out': u['out'], 'faction': u['faction'], **u['order']} for u in e['units'] if u.get('order',{}).get('revision',0)>0]}
                                       for e in boundaries]})
    assert results[0]['initialRng'] == results[1]['initialRng'], 'Arms started from different RNG states'
    assert results[0]['initialUnits'] == results[1]['initialUnits'], 'Arms started from different unit states'
    for result in results:
        result.pop('initialUnits')
    receipt = {'status': 'PASS', 'scope': 'MATCHED_SAVE_XCOM_HOLDS_NOT_TACTICAL_SUPERIORITY',
               'source': str(args.save.resolve()), 'phases': args.phases, 'results': results}
    (out / 'manifest.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    lines = ['# Persistent area-order comparison', '', 'Same source save and initial RNG. XCOM holds position. Each arm also passed recording/observer parity and native order save/load checks.', '',
             '| Arm | Movement steps | AI choices | Order transitions | Active hostiles by boundary |', '|---|---:|---|---:|---|']
    for result in results:
        lines.append(f"| {result['arm']} | {result['movementSteps']} | {result['actions']} | {result['orderTransitions']} | {[b['activeHostiles'] for b in result['boundaries']]} |")
    lines += ['', 'Counts describe behavior, not better tactics. The observation policy, contact interruptions, and a holding human side limit this test. There are no learned decisions or independent campaign samples here.', '',
              'Full order identities, destinations and statuses at every boundary are in manifest.json. Native captures, logs, copied checkpoints and per-arm replay viewers are retained below this folder.', '']
    (out / 'REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    viewer_command = [sys.executable, str(ROOT / 'scripts/view-tactical-telemetry.py'), '--out', str(out / 'review')]
    for capture in captures:
        viewer_command.extend(['--capture', str(capture)])
    subprocess.run(viewer_command, check=True)
    print(f'Comparison: {out / "REPORT.md"}', flush=True)


if __name__ == '__main__':
    main()
