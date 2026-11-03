"""Index copied-save experiment candidates without modifying source files."""
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, action='append', help='Repeat for save folders. Default: development saves and inspection sessions.')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    local = ROOT / 'build/local'
    roots = args.root or [local / 'user', *sorted(local.glob('tactical-session-*'))]
    out = args.out or local / ('tactical-catalog-' + dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    out.mkdir(parents=True, exist_ok=False)
    rows, failures, by_hash = [], [], {}
    loader = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
    for path in sorted({p.resolve() for root in roots for ext in ('*.sav', '*.asav') for p in root.rglob(ext)}):
        try:
            payload = path.read_bytes()
            digest = hashlib.sha256(payload).hexdigest()
            if digest in by_hash:
                by_hash[digest]['paths'].append(str(path))
                continue
            docs = list(yaml.load_all(payload.decode('utf-8-sig'), Loader=loader))
            header, body = docs[0], docs[-1]
            battle = body.get('battleGame')
            row = {'sha256': digest, 'paths': [str(path)], 'name': header.get('name', path.stem),
                   'kind': 'BATTLE' if battle else 'GEOSCAPE', 'master': path.parent.name,
                   'gameTime': header.get('time'), 'mission': header.get('mission'), 'target': header.get('target')}
            if battle:
                active = [u for u in battle.get('units', []) if u.get('status', 0) not in (6, 7, 10)]
                aliens = [u for u in active if u.get('faction') == 1]
                row.update(turn=battle.get('turn'), side=battle.get('side'),
                           activeByFaction=dict(Counter(str(u.get('faction')) for u in active)),
                           alienTypes=dict(Counter(u.get('genUnitType', 'UNKNOWN') for u in aliens)),
                           injuredAliens=sum(u.get('health', 0) < u.get('currStats', {}).get('health', 0) for u in aliens),
                           savedCombatModes=sum(u.get('AI', {}).get('AIMode') == 2 for u in aliens),
                           mapSize=[battle.get('width'), battle.get('length'), battle.get('height')],
                           defendCandidate=header.get('mission') in ('STR_UFO_CRASH_RECOVERY', 'STR_UFO_GROUND_ASSAULT') and bool(aliens))
                # Target labels are only grouping hints: separate campaigns can reuse IDs.
                row['encounterHint'] = '|'.join(str(row.get(k)) for k in ('master', 'mission', 'target'))
            assert path.read_bytes() == payload, 'Source changed while being indexed'
            rows.append(row)
            by_hash[digest] = row
        except Exception as exc:
            failures.append({'path': str(path), 'error': str(exc)})
    result = {'protocol': 'tactical-save-catalog-v1', 'uniqueSaves': len(rows),
              'scope': 'READ_ONLY_SAVE_METADATA_NOT_NATIVE_REPLAY', 'saves': rows, 'failures': failures,
              'limits': 'Exact hashes identify duplicates. Encounter hints, cached modes and saves are not independent battle samples or complete contact knowledge.'}
    (out / 'catalog.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    lines = ['# Tactical save catalogue', '', 'Read-only metadata. Exact duplicates share a hash; encounter labels are grouping hints, not independent samples.', '',
             '| Save | Kind | Mission | Turn | Active aliens | Injured | Saved combat mode | Defence candidate |', '|---|---|---|---:|---:|---:|---:|---|']
    for row in rows:
        label = str(row['name']).replace('|', '/')
        lines.append(f"| {label} | {row['kind']} | {row.get('mission') or ''} | {row.get('turn', '')} | {row.get('activeByFaction', {}).get('1', '')} | {row.get('injuredAliens', '')} | {row.get('savedCombatModes', '')} | {row.get('defendCandidate', '')} |")
    (out / 'REPORT.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps({'uniqueSaves': len(rows), 'battleSaves': sum(r['kind']=='BATTLE' for r in rows),
                      'defendCandidates': sum(r.get('defendCandidate', False) for r in rows), 'failures': len(failures), 'output': str(out)}))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
