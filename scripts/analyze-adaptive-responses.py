"""Export auditable aggregate and component tables from matched diagnostics."""
import csv
import json
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
probe = runpy.run_path(str(ROOT / 'scripts/test-adaptive-responses.py'))
p = probe['p']
raw = ROOT / 'build/local/adaptive-responses-v2'
out = ROOT / 'docs/experiments/adaptive-responses-v1'
summary = json.loads((raw / 'summary.json').read_text())
aggregate, components = [], []
for row in summary['rows']:
    packet = json.loads((raw / row['case'] / 'packet.json').read_text())
    label, means, votes, margin = p.aggregate_answers(row['components'], packet['criteria'])
    assert label == row['choice'] and means == row['meanScores'] and votes == row['votes']
    assert abs(margin - row['margin']) < 1e-12
    for key, description in packet['criteria'].items():
        aggregate.append(dict(case=row['case'], family=row['family'], option=key,
                              description=description, meanScore=means[key], votes=votes[key],
                              chosen=key == label, margin=margin))
    for i, receipt in enumerate(row['components']):
        for key, score in receipt['answer']['probabilities'].items():
            components.append(dict(case=row['case'], family=row['family'], rotation=i,
                                   option=key, score=score, source=receipt['inferenceSource']))
for name, rows in [('scores.csv', aggregate), ('component-scores.csv', components)]:
    with (out / name).open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
for path, digest in summary['manifest']['sources'].items():
    assert p.e.m.file_digest(Path(path)) == digest
assert p.e.m.file_digest(ROOT / 'build/local/user/xcom1/Pre-Junes.sav') == 'd095e3dd2850ee74751309d8a7570356aff20577b12916b434a3345f296d3ec7'
(out / 'results.json').write_text(json.dumps({'manifest': summary['manifest'], 'rows': [
    {k: v for k, v in row.items() if k not in ('components', 'orders')} for row in summary['rows']]}, indent=2))
print(json.dumps([dict(case=r['case'], family=r['family'], description=r['description'], margin=r['margin']) for r in summary['rows']], indent=2))
