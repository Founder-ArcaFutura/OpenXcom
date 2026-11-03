"""Compare a native alien phase with recording off, on, and omniscient rendering on."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / 'build/local'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--save', type=Path, default=LOCAL / 'user/xcom1/Groudn baddle.sav')
    parser.add_argument('--defend', action='store_true')
    parser.add_argument('--phases', type=int, choices=range(1,7), default=1)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    source = args.save.resolve()
    before = sha(source)
    out = args.out or LOCAL / ('tactical-turn-test-' + dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    out.mkdir(parents=True, exist_ok=False)
    runtime = LOCAL / 'runtime'
    exe = runtime / 'AlienCommandTests.exe'
    manifest = {'source': str(source), 'sourceSha256': before, 'executableSha256': sha(exe),
                'scope': 'BOUNDED_NATIVE_ALIEN_PHASES_XCOM_HOLDS', 'phases': args.phases, 'defend': args.defend, 'runs': []}
    spec = importlib.util.spec_from_file_location('tactical_viewer', ROOT / 'scripts/view-tactical-telemetry.py')
    viewer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(viewer)
    expected = None
    failure = None
    try:
        for arm, telemetry, observer in [('baseline', False, False), ('telemetry', True, False), ('observer', True, True)]:
            run_root = out / arm
            master_root = run_root / 'xcom1'
            master_root.mkdir(parents=True)
            copied = master_root / 'source.sav'
            shutil.copyfile(source, copied)
            env = {key: value for key, value in os.environ.items() if not key.startswith('OPENXCOM_')}
            env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', OPENXCOM_TACTICAL_TURNS='1')
            env['OPENXCOM_TACTICAL_PHASES'] = str(args.phases)
            command = [str(exe), '-data', str(runtime), '-user', str(run_root), '-config', str(run_root),
                       '-master', 'xcom1', '-playIntro', 'false', '-useOpenGL', 'false', '-fullscreen', 'false',
                       '-tacticalTelemetry', str(telemetry).lower(), '-tacticalObserver', str(observer).lower(),
                       '-tacticalDefend', str(args.defend).lower(),
                       '-newSeedOnLoad', 'false', '-autosave', 'false', '-debug', 'false', '-traceAI', 'false',
                       '-oxceRawScreenShots', 'true',
                       '-alienCommandAudit', 'false', '-alienCommandPortfolio', 'false', '-alienCommandModelPort', '0']
            with (run_root / 'native.log').open('w', encoding='utf-8') as log:
                process = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=120)
            if process.returncode:
                raise RuntimeError(f'{arm} failed ({process.returncode}): {run_root / "native.log"}')
            result = (sha(master_root / 'final-battle.yaml'), (master_root / 'final-rng.txt').read_text())
            if expected is None:
                expected = result
            assert result == expected, f'{arm} changed final battle state or RNG'
            captures = sorted(master_root.glob('tactical-*.jsonl'))
            assert len(captures) == int(telemetry), f'{arm}: unexpected capture count'
            row = {'arm': arm, 'finalBattleSha256': result[0], 'finalRng': result[1], 'sameAsBaseline': True,
                   'copyUnchanged': sha(copied) == before}
            checkpoints = sorted(master_root.glob('checkpoint-*.sav'))
            assert len(checkpoints) == args.phases, 'Missing phase checkpoints'
            for checkpoint in checkpoints:
                turn = checkpoint.stem.split('-')[-1]
                verify_root = run_root / ('verify-' + turn)
                verify_master = verify_root / 'xcom1'
                verify_master.mkdir(parents=True)
                shutil.copyfile(checkpoint, verify_master / 'source.sav')
                verify_command = command.copy()
                for flag, value in [('-user', str(verify_root)), ('-config', str(verify_root)),
                                    ('-tacticalTelemetry', 'false'), ('-tacticalObserver', 'false'), ('-tacticalDefend', 'false')]:
                    verify_command[verify_command.index(flag)+1] = value
                verify_env = env.copy()
                verify_env.pop('OPENXCOM_TACTICAL_TURNS')
                verify_env['OPENXCOM_TACTICAL_VERIFY'] = '1'
                with (verify_root / 'native.log').open('w', encoding='utf-8') as log:
                    verified = subprocess.run(verify_command, cwd=ROOT, env=verify_env, stdout=log, stderr=subprocess.STDOUT, timeout=120)
                assert verified.returncode == 0, f'Fresh-process load failed: {verify_root}'
                expected_orders = json.loads((master_root / f'orders-{turn}.json').read_text())
                loaded_orders = json.loads((verify_master / 'loaded-orders.json').read_text())
                assert loaded_orders == expected_orders, f'Order save/load mismatch at turn {turn}'
            row['freshProcessCheckpointsVerified'] = len(checkpoints)
            if telemetry:
                capture = viewer.read_capture(captures[0])
                events = capture['events']
                assert events[-1]['event'] == 'TEST_COMPLETE'
                assert any(e['event'] == 'AI_DECISION' for e in events)
                assert any(e['event'] == 'STATE_RESOLVED' for e in events)
                assert any(e['event'] == 'SIDE_START' and e['side'] == 1 for e in events)
                assert any(e['event'] == 'SIDE_READY' and e['side'] == 1 for e in events)
                assert all(e['observer'] == observer and not e['debugMode'] for e in events)
                row['capture'] = viewer.summarize(capture)
                if args.defend:
                    ordered = [u for e in events for u in e['units'] if u.get('order', {}).get('revision', 0)>0]
                    assert ordered, 'Defence flag enabled but no orders assigned in this fixture'
                    row['orderedUnits'] = len({u['id'] for u in ordered})
                    row['orderStatuses'] = dict(__import__('collections').Counter(u['order']['status'] for u in ordered))
                    row['phaseBoundaries'] = sum(e['event']=='TEST_PHASE_COMPLETE' for e in events)
                    assert row['phaseBoundaries'] == args.phases
            manifest['runs'].append(row)
            print(f'PASS: {arm}; final battle state and RNG match baseline', flush=True)
        # Viewer admits only an incomplete final line, not corrupt complete records.
        capture_path = next((out / 'observer/xcom1').glob('tactical-*.jsonl'))
        truncated = out / 'truncated-tail.jsonl'
        truncated.write_bytes(capture_path.read_bytes() + b'{"protocol":')
        assert viewer.read_capture(truncated)['warnings']
        invalid = out / 'invalid-record.jsonl'
        invalid.write_bytes(b'{bad json}\n')
        try:
            viewer.read_capture(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError('Viewer accepted a corrupt complete record')
        manifest['partialTailAndCorruptRecordChecks'] = 'PASS'
        subprocess.run([str(LOCAL / 'laya-venv/Scripts/python.exe'), str(ROOT / 'scripts/view-tactical-telemetry.py'),
                        '--capture-dir', str(out / 'observer/xcom1'), '--out', str(out / 'review')], check=True)
    except Exception as exc:
        failure = str(exc)
        manifest['failure'] = failure
    finally:
        manifest['originalUnchanged'] = sha(source) == before
        manifest['status'] = 'PASS' if not failure and manifest['originalUnchanged'] else 'FAIL'
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'{manifest["status"]}: {out / "manifest.json"}', flush=True)
    if manifest['status'] != 'PASS':
        raise SystemExit(failure or 'Original save changed')


if __name__ == '__main__':
    main()
