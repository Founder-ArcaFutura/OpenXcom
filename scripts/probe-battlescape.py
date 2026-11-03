"""Run native copied-save destination probes; no model calls or turn advancement."""
import argparse
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / 'build/local'
DEFAULT_SAVES = ['Groudn baddle.sav', 'Ground mutons.sav', 'surrounded.sav']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def catalog(folder):
    rows = []
    for path in sorted(folder.glob('*.sav')):
        # Header-only inventory; full parsing/loading belongs to the native engine.
        header = path.read_text(encoding='utf-8-sig').split('\n---', 1)[0]
        if re.search(r'^turn:', header, re.M):
            fields = dict(re.findall(r'^(mission|turn|target): (.*)$', header, re.M))
            rows.append({'save': str(path.resolve()), **fields})
    return rows


def map_svg(result, arm):
    width, height, levels = result['mapSize']
    scale = 7
    panels = []
    for z in range(levels):
        items = []
        for node in result['nodes']:
            x, y, nz = node['position']
            if nz != z:
                continue
            color = '#d99a35' if node['objectiveAnchor'] else '#536575'
            items.append(f'<circle cx="{x*scale}" cy="{y*scale}" r="2" fill="{color}"/>')
        for order in result[arm]:
            x, y, sz = order['start']
            tx, ty, tz = order['target']
            tip = html.escape(f"Alien {order['unit']} / {order['role']} / movement {order['movementTU']} TU", quote=True)
            if sz == z:
                items.append(f'<circle cx="{x*scale}" cy="{y*scale}" r="4" fill="#7adbb5"><title>{tip}</title></circle>')
                items.append(f'<text x="{x*scale+5}" y="{y*scale-4}" fill="white" font-size="9">{order["unit"]}</text>')
            if sz == tz == z and order['pathExists']:
                # Straight connector deliberately does not purport to show the native route.
                items.append(f'<line x1="{x*scale}" y1="{y*scale}" x2="{tx*scale}" y2="{ty*scale}" stroke="#7adbb5" stroke-dasharray="3 3" opacity=".6"/>')
            if tz == z and order['node'] >= 0:
                items.append(f'<rect x="{tx*scale-3}" y="{ty*scale-3}" width="6" height="6" fill="#ee7f90"><title>{tip}</title></rect>')
        panels.append(f'<div><p>Level {z}</p><svg viewBox="-8 -12 {width*scale+24} {height*scale+24}" width="{width*scale}" height="{height*scale}" role="img" aria-label="Alien positions and proposed destinations">{"".join(items)}</svg></div>')
    return ''.join(panels)


def report(out, runs):
    lines = ['# Battlescape destination probe', '',
             'Native route feasibility only. No units moved, turns advanced, shots fired, or model called.', '',
             '| Save | Seed | Active aliens | Stock patrol routes within current TU | Assigned posts (requiring movement) | Hold fallbacks |',
             '|---|---:|---:|---:|---:|---:|']
    sections = []
    for run in runs:
        if run['status'] != 'PASS':
            lines.append(f'| {Path(run["source"]).name} | {run["seed"]} | FAILED: see log | | | |')
            continue
        result = json.loads((out / run['directory'] / 'xcom1/tactical-probe.json').read_text())
        baseline = result['baseline']
        orders = result['coordinated']
        assigned = sum(order['node'] >= 0 for order in orders)
        moves = sum(order['movementTU'] > 0 for order in orders)
        lines.append(f'| {Path(run["source"]).name} | {run["seed"]} | {len(orders)} | {sum(o["fitsCurrentTU"] for o in baseline)} | {assigned} ({moves}) | {len(orders)-assigned} |')
        title = html.escape(f'{Path(run["source"]).name} — seed {run["seed"]}, turn {result["turn"]}')
        sections.append(f'<h2>{title}</h2><div class="arms"><section><h3>Stock patrol destination probe</h3>{map_svg(result, "baseline")}</section><section><h3>Scripted shared defence</h3>{map_svg(result, "coordinated")}</section></div>')
    lines += ['', 'Stock results probe patrol selection, including existing destinations; they do not invoke the full combat AI. Patrol destinations can intentionally require multiple turns.', '',
              'Saved route nodes omit original segment IDs. Objective anchors are guard-ranked nodes (rank >= 2) inside blocks identified as UFOs by the saved map layout. This footprint inference is not recovered original node provenance. Shared defence assigns the closest two thirds of aliens to those anchors and the remainder to outside nodes within eight tiles of anchors. Assignments are greedy and deterministic, with three-tile separation between newly assigned destinations. Each move preserves 12 TU where available; this is a fixed movement reserve, not a verified firing/reaction budget. Units without a valid post hold position.', '',
              'This tests node-level allocation, not cover quality, mutual support, path conflicts, maintained orders, or victory. Current occupants remain in place during planning. A fallback holder may obstruct an earlier assignment; simultaneous movement is not tested. No enemy positions are supplied to the assignment scorer, but native occupancy/pathfinding checks use loaded battle state. This is not a fog-of-war certification.', '',
              'Snapshots are from one player campaign, often already in contact and on the player side. Saved current TU is used without refreshing the aliens; this is not a fresh alien-turn budget. Seed variants are not independent battles. Stock patrols may span multiple turns, whereas the scripted assignments must fit the immediate budget, so counts are not a measure of superiority. The map shows node anchors and straight destination connectors, not terrain or walked routes. Cross-level connectors are omitted. Full native direction sequences are retained in JSON.', '',
              'Next gate: execute persistent orders through real alien turns on disposable copies, with contact interrupts and a fixed player policy, before comparing combat outcomes.', '']
    (out / 'REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    page = '''<!doctype html><meta charset="utf-8"><title>Battlescape destination probe</title>
<style>body{background:#121b24;color:#e0e7ee;font:15px system-ui;margin:24px}.arms{display:flex;gap:32px;flex-wrap:wrap}section{border:1px solid #425465;padding:16px}svg{background:#192632;max-width:100%;height:auto}h2{margin-top:40px}p{max-width:1000px}</style>
<h1>Battlescape destination probe</h1><p>Destination feasibility only. No combat or movement executed. Gold dots: UFO nodes. Grey dots: other route nodes. Green circles: aliens and IDs. Pink squares: proposed posts. Dashed lines connect start to destination; they are not walked paths. Hover for role and TU cost.</p>'''
    (out / 'map.html').write_text(page + ''.join(sections), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save', type=Path, action='append', help='Repeat for several UFO battles; defaults to three local snapshots.')
    parser.add_argument('--save-dir', type=Path, default=LOCAL / 'user/xcom1')
    parser.add_argument('--list', action='store_true', help='List available battlescape headers and exit.')
    parser.add_argument('--seeds', type=int, nargs='+', default=[1, 7, 23])
    parser.add_argument('--out', type=Path)
    parser.add_argument('--build', action='store_true', help='Build the native test harness from existing engine objects.')
    args = parser.parse_args()
    if args.list:
        print(json.dumps(catalog(args.save_dir), indent=2))
        return
    if any(seed <= 0 or seed > 2**64-1 for seed in args.seeds):
        parser.error('Seeds must be between 1 and 2^64-1.')
    saves = [p.resolve() for p in (args.save or [args.save_dir / name for name in DEFAULT_SAVES])]
    for save in saves:
        if not save.is_file():
            parser.error(f'Save not found: {save}')
    runtime = LOCAL / 'runtime'
    if args.build:
        subprocess.run([r'C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe',
                        str(ROOT / 'tests/AlienCommandTests.vcxproj'), '/nologo', '/v:minimal',
                        '/p:Configuration=Release', '/p:Platform=x64', '/p:PreferredToolArchitecture=x64'], check=True, cwd=ROOT)
    exe = runtime / 'AlienCommandTests.exe'
    if not exe.exists():
        parser.error('Build the engine with scripts/setup-local.ps1, then use --build.')
    out = (args.out or LOCAL / ('tactical-probe-' + dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))).resolve()
    # Results must be new, preventing accidental replacement of saves or earlier receipts.
    out.mkdir(parents=True, exist_ok=False)
    runs = []
    repeated_results = {}
    coordinated_results = {}
    manifest = {'protocol': 'battlescape-destinations-v1', 'executableSha256': sha(exe),
                'sourceHashes': {str(p.relative_to(ROOT)): sha(p) for p in
                                 [ROOT / 'tests/BattlescapeProbe.h', ROOT / 'tests/AlienCommandTests.cpp', Path(__file__),
                                  ROOT / 'src/Battlescape/AIModule.cpp', ROOT / 'src/Battlescape/Pathfinding.cpp',
                                  ROOT / 'src/Savegame/SavedBattleGame.cpp']},
                'catalog': catalog(args.save_dir), 'runs': runs}
    for save_index, source in enumerate(saves):
        original_hash = sha(source)
        for seed_index, seed in enumerate(args.seeds):
            directory = f'save-{save_index:02}-seed-{seed_index:02}-{seed}'
            run_root = out / directory
            master_root = run_root / 'xcom1'
            master_root.mkdir(parents=True)
            copied = master_root / 'source.sav'
            shutil.copyfile(source, copied)
            env = os.environ.copy()
            for key in list(env):
                if key.startswith('OPENXCOM_'):
                    env.pop(key)
            env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy',
                       OPENXCOM_BATTLESCAPE_PROBE='1', OPENXCOM_BATTLESCAPE_SEED=str(seed))
            run = {'source': str(source), 'sourceSha256': original_hash, 'seed': seed,
                   'directory': directory, 'status': 'FAIL'}
            try:
                with (run_root / 'native.log').open('w', encoding='utf-8') as log:
                    process = subprocess.run([str(exe), '-data', str(runtime), '-user', str(run_root), '-config', str(run_root),
                                              '-master', 'xcom1', '-playIntro', 'false', '-useOpenGL', 'false',
                                              '-fullscreen', 'false', '-alienCommandPortfolio', 'false', '-alienCommandModelPort', '0'],
                                             cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=120)
                run['exitCode'] = process.returncode
                if process.returncode == 0:
                    result = json.loads((master_root / 'tactical-probe.json').read_text())
                    assert result['battleStateUnchanged'] and result['rngUnchanged']
                    assert all(o['pathExists'] and o['movementTU'] <= max(0, o['currentTU']-12)
                               and o['movementEnergy'] <= o['currentEnergy'] for o in result['coordinated'])
                    canonical = json.dumps(result, sort_keys=True)
                    key = (str(source), seed)
                    if key in repeated_results:
                        assert repeated_results[key] == canonical, 'Same save/seed did not reproduce exactly'
                        run['exactRepeatVerified'] = True
                    repeated_results[key] = canonical
                    coordinated = json.dumps(result['coordinated'], sort_keys=True)
                    if str(source) in coordinated_results:
                        assert coordinated_results[str(source)] == coordinated, 'Scripted arm depends on baseline seed'
                        run['coordinatedSeedIndependenceVerified'] = True
                    coordinated_results[str(source)] = coordinated
                    run['status'] = 'PASS'
            except (subprocess.TimeoutExpired, OSError, ValueError, AssertionError) as exc:
                run['error'] = str(exc)
            finally:
                run['originalUnchanged'] = sha(source) == original_hash
                run['copyUnchanged'] = sha(copied) == original_hash
                runs.append(run)
                (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
            print(f'{run["status"]}: {source.name}, seed {seed}', flush=True)
            if not run['originalUnchanged'] or not run['copyUnchanged']:
                raise RuntimeError(f'Save integrity check failed: {source}')
    report(out, runs)
    print(f'Report: {out / "REPORT.md"}\nMap: {out / "map.html"}', flush=True)
    if any(run['status'] != 'PASS' for run in runs):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
