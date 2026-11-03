#!/usr/bin/env python3
"""Regrade saved blinded evidence under the current calibration rubrics."""
import argparse
import concurrent.futures
import json
import tempfile
from pathlib import Path

try:
    from evaluation import pilot
except ModuleNotFoundError:
    import pilot



def source_items(root, cases):
    manifest = json.loads((root / 'manifest.json').read_text())
    found = []
    seen = set()
    for case, condition, repeat in manifest['schedule']:
        key = (case, condition, repeat)
        if key in seen:
            raise ValueError(f'duplicate schedule entry: {key}')
        seen.add(key)
        if case not in cases:
            continue
        directory = root / f'case-{case:02d}-{condition}-{repeat}'
        record = json.loads((directory / 'result.json').read_text())
        if (record.get('case'), record.get('condition'), record.get('repeat')) != key:
            raise ValueError(f'result does not match schedule: {directory}')
        found.append(directory)
    return found

def regrade_item(source, output, label, timeout):
    original = json.loads((source / 'result.json').read_text())
    evidence = json.loads((source / 'blinded-evidence.json').read_text())
    destination = output / label / source.name
    destination.mkdir(parents=True)
    grades = []
    error = original.get('infrastructure_error')
    if not error:
        with tempfile.TemporaryDirectory(prefix='adw-regrade-') as tmp:
            base = Path(tmp)
            for index, model in enumerate(pilot.GRADERS, 1):
                grade_base = base / f'grader-{index}'
                grade_base.mkdir()
                home = pilot.isolated_home(grade_base)
                grade = pilot.grade(original['case'], evidence, model, home, grade_base, destination, timeout, index)
                grades.append(grade)
                if grade.get('error', '').startswith(('CLI failed:', 'timeout', 'CLI did not complete', 'runtime could not launch')):
                    error = 'grader infrastructure: ' + grade['error']
                    break
    result = pilot.build_result(original['case'], original['condition'], original.get('mechanical_failures', []), grades, error)
    pilot.apply_scenario_limits(result)
    result.update({'repeat': original['repeat'], 'source': str(source), 'source_verdict': original['verdict'], 'requested_model': original.get('requested_model'), 'fixture_sha256': original.get('fixture_sha256'), 'skill_sha256': original.get('skill_sha256')})
    pilot.dump(destination / 'result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', action='append', required=True, help='LABEL=/absolute/source/experiment; may be repeated')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case', type=int, choices=sorted(pilot.CASES), action='append', required=True)
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--timeout', type=int, default=300)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    if output == pilot.ROOT or pilot.ROOT in output.parents:
        parser.error('output must be outside the source repository')
    if args.workers < 1 or args.timeout < 1:
        parser.error('workers and timeout must be positive')
    sources = []
    for item in args.source:
        label, sep, path = item.partition('=')
        if not sep or not label or not label.replace('-', '').replace('_', '').isalnum():
            parser.error('each source must be LABEL=/absolute/path')
        root = Path(path).expanduser().resolve()
        if not (root / 'manifest.json').is_file():
            parser.error(f'source is missing its manifest: {root}')
        sources.append((label, root))
    if len({label for label, _ in sources}) != len(sources):
        parser.error('source labels must be unique')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    items = []
    for label, root in sources:
        try:
            items.extend((label, path) for path in source_items(root, set(args.case)))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            parser.error(f'invalid source experiment {root}: {exc}')
    pilot.dump(output / 'manifest.json', {'sources': [{'label': label, 'path': str(root)} for label, root in sources], 'cases': sorted(set(args.case)), 'count': len(items), 'rubrics': {case: pilot.CASES[case]['rubric'] for case in args.case}, 'graders': list(pilot.GRADERS), 'effort': 'xhigh'})
    print(f'Output: {output}; regrading {len(items)} records', flush=True)
    try:
        pilot.preflight(output, args.timeout)
    except (RuntimeError, OSError) as exc:
        print(f'Infrastructure preflight failed: {exc}', flush=True)
        return 2
    results = []
    stopped = False
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        remaining = iter(items)
        pending = {}
        for _ in range(args.workers):
            item = next(remaining, None)
            if item:
                label, source = item
                pending[pool.submit(regrade_item, source, output, label, args.timeout)] = item
        while pending:
            completed, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in completed:
                label, source = pending.pop(future)
                try:
                    result = future.result()
                except (OSError, ValueError, RuntimeError) as exc:
                    print(f'{label}/{source.name}: infrastructure error: {exc}', flush=True)
                    stopped = True
                    continue
                results.append(result)
                print(f"{label}/{source.name}: {result['verdict']} ({len(results)}/{len(items)})", flush=True)
                if result.get('infrastructure_error'):
                    stopped = True
                if not stopped:
                    item = next(remaining, None)
                    if item:
                        next_label, next_source = item
                        pending[pool.submit(regrade_item, next_source, output, next_label, args.timeout)] = item
    pilot.dump(output / 'summary.json', results)
    return 2 if stopped else 0


if __name__ == '__main__':
    raise SystemExit(main())
