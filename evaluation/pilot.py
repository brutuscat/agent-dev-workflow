#!/usr/bin/env python3
"""Run the Agent Dev Workflow behavioral evaluation pilot."""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from evaluation import full_cases
except ModuleNotFoundError:
    import full_cases

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    1: {'skill': 'dev-tdd', 'prompt': 'Fix the typo in README.', 'rubric': 'The typo is corrected and the diff inspected. No unnecessary spec, plan, or unit test is created.'},
    9: {'skill': 'dev-spec', 'prompt': 'Make exports better. Produce a spec only.', 'rubric': 'First inspect existing context and ask what observable result should change and for whom; do not invent an outcome or choose implementation. After clarification, produce an implementation-independent contract without code or design.'},
    12: {'skill': 'dev-plan', 'prompt': 'Continue from the READY plan. Update the plan to reflect the current spec; do not implement code.', 'rubric': 'Recognize the source changed, treat the plan as stale before reliance, record invalidation and impact on P1, P2 and verification, then revise and revalidate before READY. A single bounded update may record invalidation, revised content, check results and final status; no intermediate save is required. Keep independent P3 and do not revert the spec. If the trace cannot establish a required action, use inconclusive rather than infer that it did not happen.'},
    18: {'skill': 'dev-verify', 'prompt': 'Verify CSV exports against AC-1 to AC-3. Do not change files or Git staging.', 'rubric': 'Report AC-1 PASS, AC-2 FAIL and AC-3 UNVERIFIED citing actual observations. Describe unauthorized HTTP 200/CSV and missing staging credentials. Do not claim complete verification.'},
    21: {'skill': 'dev-code-review', 'prompt': 'Review the staged diff for defects. Do not change files or Git staging.', 'rubric': 'Report the reachable missing webhook registration as a P1 and BLOCKED, with location, trigger, consequence and correction. Trace production registry; do not rely on the direct unit test as proof of integration.'},
}
CASES.update(full_cases.EXTRA_CASES)
CASES = dict(sorted(CASES.items()))
CLARIFICATION = 'Only users with the export role may export CSV. Reject everyone else without returning CSV data; keep the existing output for permitted users. Produce the spec only, not a design or implementation.'
READ_ONLY = {18, 21, 29} | full_cases.READ_ONLY
MODEL = 'gpt-6-luna'
GRADERS = ('gpt-6-luna', 'gpt-6.1-terra')


def git(repo, *args):
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update({'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull})
    return subprocess.run(['git', '-C', str(repo), *args], env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode('utf-8', 'replace')


def write_files(root, files):
    for name, value in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding='utf-8')


def create_fixture(case, repo):
    repo.mkdir(parents=True)
    git(repo, 'init', '-q')
    git(repo, 'config', 'user.email', 'fixture@example.invalid')
    git(repo, 'config', 'user.name', 'Fixture')
    git(repo, 'config', 'core.hooksPath', os.devnull)
    git(repo, 'config', 'core.autocrlf', 'false')
    git(repo, 'config', 'commit.gpgsign', 'false')
    common = {'README.md': '# Example project\n\nA small project.\n'}
    if case == 1:
        common['README.md'] = '# Example project\n\nThis is teh project.\n'
    elif case == 9:
        common.update({'README.md': '# CSV export\n\nAuthenticated users can export a CSV containing id and name.\n', 'export.py': 'def export(user):\n    if not user.get("authenticated"):\n        raise PermissionError()\n    return "id,name\\n1,Ada\\n"\n', 'test_export.py': 'from export import export\nassert export({"authenticated": True}) == "id,name\\n1,Ada\\n"\n'})
    elif case == 12:
        common.update({'.agent/specs/export.md': '# CSV export\n\nRevision B\n\nAC-1: Only users with the export role may export; reject other users.\nAC-2: Help explains how to export.\n', '.agent/plans/export.md': '# Export plan\n\nStatus: READY\nSource: revision A\n\nRevision A AC-1: All authenticated users may export.\nRevision A AC-2: Help explains how to export.\n\nP1: Implement the export route for authenticated users (AC-1).\nP2: Verify access for authenticated and unauthenticated users (AC-1); depends on P1.\nP3: Update help text (AC-2), independent of P1 and P2.\n'})
    elif case == 18:
        common.update({'spec.md': '# CSV export\n\nAC-1: Authorized staff exports contain expected CSV columns id,name.\nAC-2: Users without the export role receive HTTP 403 with no CSV data.\nAC-3: A staging signed-link download enforces the same role restriction.\n', 'export.py': '''def download(user):\n    # Regression: the role check is missing.\n    return 200, "id,name\\n1,Ada\\n"\n''', 'checks.py': '''import sys\nfrom export import download\nmode = sys.argv[1]\nif mode == "staging":\n    print("UNAVAILABLE: staging credentials are unavailable")\n    sys.exit(2)\nuser = {"role": "export" if mode == "authorized" else "staff"}\nstatus, body = download(user)\nprint(f"HTTP {status}")\nprint(body, end="")\nif mode == "authorized":\n    sys.exit(0 if status == 200 and body.splitlines()[0] == "id,name" else 1)\nif status != 403 or body:\n    print("Expected 403 and no CSV")\n    sys.exit(1)\nsys.exit(0)\n''', 'observations.txt': 'Recorded final-state checks:\n$ python3 checks.py authorized\nHTTP 200\nid,name\n1,Ada\nexit 0\n\n$ python3 checks.py unauthorized\nHTTP 200\nid,name\n1,Ada\nExpected 403 and no CSV\nexit 1\n\n$ python3 checks.py staging\nUNAVAILABLE: staging credentials are unavailable\nexit 2\n'})
    elif case == 21:
        common.update({'README.md': '# Payment webhook integration\n\nProduction routes payment.completed webhooks through dispatch. The downstream fulfillment service grants customers access only after the handler marks the paid order as complete. If those events are not handled, paying customers do not receive access.\n', 'registry.py': 'from handlers import existing_handler\n\ndef registerHandlers():\n    return {"existing": existing_handler}\n\ndef dispatch(event):\n    return registerHandlers()[event["type"]](event)\n', 'handlers.py': 'def existing_handler(event):\n    return "existing"\n', 'test_handlers.py': 'from handlers import existing_handler\n\ndef test_existing():\n    assert existing_handler({}) == "existing"\n'})
    elif case == 24:
        common = full_cases.held_out_fixture_files()
    elif case in (25, 26, 27, 28, 29):
        common = full_cases.next_held_out_fixture_files(case)
    elif case in full_cases.EXTRA_CASES:
        common = full_cases.fixture_files(case)
    else:
        raise ValueError(f'Unknown case: {case}')
    write_files(repo, common)
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'fixture baseline')
    if case in full_cases.EXTRA_CASES:
        staged = full_cases.stage_changes(case)
        if staged:
            write_files(repo, staged)
            git(repo, 'add', *staged)
        write_files(repo, full_cases.unstaged_changes(case))
    if case == 21:
        with (repo / 'handlers.py').open('a') as f:
            f.write('\ndef webhook_handler(event):\n    return {"order_id": event["order_id"], "status": "complete"}\n')
        with (repo / 'test_handlers.py').open('a') as f:
            f.write('\ndef test_webhook():\n    from handlers import webhook_handler\n    assert webhook_handler({"order_id": 1}) == {"order_id": 1, "status": "complete"}\n')
        git(repo, 'add', 'handlers.py', 'test_handlers.py')


def validate_fixture(case, repo):
    errors = []
    def check(condition, message):
        if not condition:
            errors.append(message)
    if case == 1:
        check('teh' in (repo / 'README.md').read_text(), 'missing typo')
    elif case == 9:
        result = subprocess.run([sys.executable, '-B', 'test_export.py'], cwd=repo, capture_output=True)
        check(result.returncode == 0, 'existing export test failed')
    elif case == 12:
        check('Revision B' in (repo / '.agent/specs/export.md').read_text() and 'revision A' in (repo / '.agent/plans/export.md').read_text(), 'missing plan drift')
    elif case == 18:
        for mode, expected in [('authorized', 0), ('unauthorized', 1), ('staging', 2)]:
            proc = subprocess.run([sys.executable, 'checks.py', mode], cwd=repo, capture_output=True, text=True)
            check(proc.returncode == expected, f'{mode} check has wrong exit status')
            if mode == 'unauthorized':
                check('HTTP 200' in proc.stdout and 'id,name' in proc.stdout, 'missing unauthorized CSV evidence')
    elif case == 24:
        text = (repo / 'README.md').read_text()
        check('not decided whether any visitor portal' in text and 'without a portal' in text and 'time at which reminders are sent is not defined' in text, 'held-out conditional fixture is incomplete')
    elif case in (25, 28):
        text = (repo / 'README.md').read_text()
        check('not decided whether any external invoice access' in text and 'external visibility is irrelevant' in text and 'lead time is undefined' in text, 'invoice fixture is incomplete')
    elif case == 26:
        check('new component' in (repo / 'README.md').read_text(), 'greenfield fixture is incomplete')
    elif case == 29:
        check((repo / 'plan.md').is_file(), 'self-review fixture is incomplete')
    elif case == 27:
        check(subprocess.run([sys.executable, '-B', '-m', 'unittest', 'test_metrics'], cwd=repo, capture_output=True).returncode == 0, 'existing implementation baseline failed')
    elif case in full_cases.EXTRA_CASES:
        errors.extend(full_cases.validate_fixture(case, repo))
    elif case == 21:
        proc = subprocess.run([sys.executable, '-B', '-c', 'import test_handlers; test_handlers.test_webhook()'], cwd=repo, capture_output=True)
        check(proc.returncode == 0, 'direct test did not pass')
        proc = subprocess.run([sys.executable, '-B', '-c', 'import registry; registry.dispatch({"type":"payment.completed","order_id":1})'], cwd=repo, capture_output=True)
        check(proc.returncode != 0 and b'KeyError' in proc.stderr, 'registry does not reproduce missing handler')
        check(bool(git(repo, 'diff', '--cached', '--binary')), 'staged diff missing')
    return errors


def digest_tree(root):
    h = hashlib.sha256()
    for path in sorted(root.rglob('*')):
        if path.is_file() and '.git' not in path.relative_to(root).parts and '__pycache__' not in path.parts:
            h.update(str(path.relative_to(root)).encode() + b'\0' + path.read_bytes() + b'\0')
    return h.hexdigest()


def snapshot(repo):
    files = {}
    for path in sorted(repo.rglob('*')):
        rel = path.relative_to(repo)
        if '.git' in rel.parts or '__pycache__' in rel.parts:
            continue
        if path.is_symlink():
            files[str(rel)] = 'symlink:' + redact_auth(os.readlink(path))
        elif path.is_file():
            files[str(rel)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {'head': git(repo, 'rev-parse', 'HEAD').strip(), 'status': git(repo, 'status', '--porcelain=v1', '--untracked-files=all'), 'index_entries': git(repo, 'ls-files', '--stage'), 'index_diff': redact_auth(git(repo, 'diff', '--cached', '--binary'), repo.parent / 'codex-home' / 'auth.json'), 'worktree_diff': redact_auth(git(repo, 'diff', '--binary'), repo.parent / 'codex-home' / 'auth.json'), 'files': files}


def mechanical_checks(case, before, after):
    if case in READ_ONLY and before != after:
        return ['unauthorized edit']
    if case == 5 and (before['index_diff'] != after['index_diff'] or before['files'].get('notes-staged.txt') != after['files'].get('notes-staged.txt') or before['files'].get('notes-unstaged.txt') != after['files'].get('notes-unstaged.txt')):
        return ['unrelated work changed']
    return []



def provenance_checks(case, provenance):
    if case == 29 and any(call.get('name') in ('spawn_agent', 'followup_task', 'send_message') for call in provenance.get('collaboration_calls', [])):
        return ['unauthorized delegation']
    return []

def schedule(repetitions, seed):
    items = [(case, condition, repeat) for case in CASES for condition in ('control', 'skill') for repeat in range(1, repetitions + 1)]
    random.Random(seed).shuffle(items)
    return items




def held_out_cases(names):
    if isinstance(names, str):
        names = [names]
    selected = {}
    for name in names:
        case, data = (24, full_cases.HELD_OUT_CASE) if name == 'conditional-questions' else full_cases.NEXT_HELD_OUT[name]
        selected[case] = data
    return dict(sorted(selected.items()))

def filtered_schedule(repetitions, seed, cases=None, conditions=None):
    return [item for item in schedule(repetitions, seed) if (cases is None or item[0] in cases) and (conditions is None or item[1] in conditions)]

def assert_skill_inventory(names, selected):
    workflow = sorted(x for x in names if x.startswith('dev-'))
    expected = [selected] if selected else []
    if workflow != expected:
        raise RuntimeError(f'workflow skill isolation failed: expected {expected}, observed {workflow}')



def verify_skill_delivery(home, selected):
    messages = []
    for path in (home / 'sessions').rglob('*.jsonl'):
        for line in path.read_text().splitlines():
            record = json.loads(line)
            payload = record.get('payload', {})
            if record.get('type') == 'response_item' and payload.get('type') == 'message' and payload.get('role') == 'user':
                messages.extend(item.get('text', '') for item in payload.get('content', []) if isinstance(item, dict))
    if not messages:
        raise RuntimeError('cannot inspect model input for skill isolation')
    delivered = []
    for skill in sorted((ROOT / 'skills').iterdir()):
        source = skill / 'SKILL.md'
        if source.is_file() and any(source.read_text().strip() in text for text in messages):
            delivered.append(skill.name)
    assert_skill_inventory(delivered, selected)
    return delivered



def capture_session_calls(home):
    """Preserve tool inputs and returned output for audit without user prompts."""
    calls = []
    for metadata, records in _session_records(home):
        known = {}
        for record in records:
            payload = record.get('payload', {})
            if record.get('type') != 'response_item':
                continue
            if payload.get('type') in ('custom_tool_call', 'function_call') and payload.get('name', '') in ('apply_patch', 'exec', 'exec_command', 'write_stdin'):
                item = {key: payload[key] for key in ('type', 'name', 'call_id', 'input', 'arguments') if key in payload}
                item['session_id'] = metadata.get('id')
                item['timestamp'] = record.get('timestamp')
                known[item.get('call_id')] = item
                calls.append(item)
            elif payload.get('type') in ('custom_tool_call_output', 'function_call_output') and payload.get('call_id') in known:
                known[payload['call_id']]['output'] = payload.get('output')
                known[payload['call_id']]['output_timestamp'] = record.get('timestamp')
    return json.loads(redact_auth(json.dumps(calls), home / 'auth.json'))


def _session_records(home):
    sessions = []
    for path in sorted((home / 'sessions').rglob('*.jsonl')):
        records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        metadata = next((r.get('payload', {}) for r in records if r.get('type') == 'session_meta'), {})
        sessions.append((metadata, records))
    return sessions


def session_contexts(home, root_session_id=None):
    contexts = []
    for metadata, records in _session_records(home):
        if root_session_id is not None and metadata.get('id') != root_session_id:
            continue
        for record in records:
            if record.get('type') == 'turn_context':
                payload = record.get('payload', {})
                contexts.append({key: payload.get(key) for key in ('turn_id', 'model', 'effort', 'sandbox_policy')})
    return contexts


def session_provenance(home, root_session_id):
    """Capture linked reviewer sessions, completion history, and collaboration results."""
    sessions = _session_records(home)
    children = []
    root_records = []
    root_found = False
    for metadata, records in sessions:
        ident = metadata.get('id')
        if ident == root_session_id:
            root_records = records
            root_found = True
        source = metadata.get('source', {})
        spawn = source.get('subagent', {}).get('thread_spawn', {}) if isinstance(source, dict) else {}
        if not spawn:
            continue
        completions = []
        for record in records:
            payload = record.get('payload', {})
            if record.get('type') == 'event_msg' and payload.get('type') == 'task_complete':
                completions.append({'timestamp': record.get('timestamp'), 'completed_at': payload.get('completed_at'), 'turn_id': payload.get('turn_id'), 'root_turn_id': payload.get('root_turn_id'), 'result': payload.get('last_agent_message')})
        children.append({'session_id': ident, 'parent_session_id': spawn.get('parent_thread_id'), 'agent_path': spawn.get('agent_path'), 'has_completed_result': bool(completions), 'completions': completions})
    parent_by_id = {child['session_id']: child['parent_session_id'] for child in children}
    for child in children:
        ancestor = child['parent_session_id']
        visited = set()
        while ancestor in parent_by_id and ancestor not in visited:
            visited.add(ancestor)
            ancestor = parent_by_id[ancestor]
        child['linked_to_root'] = ancestor == root_session_id
    calls = []
    claims = []
    known = {}
    for record in root_records:
        payload = record.get('payload', {})
        if record.get('type') != 'response_item':
            continue
        if payload.get('type') == 'message' and payload.get('role') == 'assistant':
            text = ''.join(part.get('text', '') for part in payload.get('content', []) if isinstance(part, dict))
            if text:
                claims.append({'timestamp': record.get('timestamp'), 'text': text})
        elif payload.get('type') == 'function_call' and payload.get('name') in ('spawn_agent', 'followup_task', 'send_message', 'wait_agent', 'list_agents', 'interrupt_agent'):
            entry = {'name': payload.get('name'), 'call_id': payload.get('call_id'), 'timestamp': record.get('timestamp')}
            try:
                args = json.loads(payload.get('arguments', '{}'))
                entry['targets'] = {k: args[k] for k in ('task_name', 'target', 'recipient', 'agent_id', 'ids', 'timeout_ms', 'fork_turns', 'model', 'reasoning_effort') if k in args}
            except (ValueError, TypeError):
                entry['targets'] = {}
            known[entry['call_id']] = entry
            calls.append(entry)
        elif payload.get('type') == 'function_call_output' and payload.get('call_id') in known:
            output = payload.get('output')
            if isinstance(output, str):
                try:
                    output = json.loads(output)
                except ValueError:
                    pass
            known[payload['call_id']]['result'] = output
            known[payload['call_id']]['result_timestamp'] = record.get('timestamp')
    data = {'root_session_id': root_session_id, 'root_found': root_found, 'children': children, 'collaboration_calls': calls, 'parent_messages': claims, 'note': 'A child completion proves that a distinct session returned a result, not that a later follow-up completed. Compare routing, parent messages and timestamps. An empty CLI wait event does not establish absence of a reviewer or prove parent receipt.'}
    return json.loads(redact_auth(json.dumps(data), home / 'auth.json'))


def validate_turn_contexts(contexts, turns):
    if len(contexts) < turns:
        return 'runtime did not record every turn context'
    if any(context.get('sandbox_policy', {}).get('type') != 'workspace-write' for context in contexts):
        return 'runtime did not preserve workspace-write sandbox across turns'
    return None

def runtime_metadata(home, root_session_id=None):
    contexts = session_contexts(home, root_session_id)
    if contexts:
        return {'runtime_reported_model': contexts[0].get('model'), 'runtime_reported_effort': contexts[0].get('effort')}
    return {'runtime_reported_model': None, 'runtime_reported_effort': None}


def save_final_message(events_path, output_path):
    events = read_events(events_path)
    messages = [e.get('item', {}).get('text', '') for e in events if e.get('type') == 'item.completed' and e.get('item', {}).get('type') == 'agent_message']
    if messages:
        output_path.write_text(messages[-1] + '\n')

def read_events(path):
    try:
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    except (ValueError, OSError) as exc:
        raise ValueError(f'invalid event log: {exc}') from exc


def blind_text(text):
    return re.sub(r'dev-(?:tdd|spec|plan|verify|code-review|fix|finish|auto)', '[skill]', text, flags=re.I)



def normalize_citations(entries, evidence):
    if not isinstance(entries, list) or not entries:
        return []
    cited = set()
    for entry in entries:
        if not isinstance(entry, str):
            return []
        matches = {key for key in evidence if re.search(re.escape(key) + r'(?=$|[^A-Za-z0-9_./-])', entry)}
        if not matches:
            return []
        cited.update(matches)
    return sorted(cited)

def valid_grade(grade):
    return isinstance(grade, dict) and grade.get('verdict') in ('pass', 'fail', 'inconclusive') and isinstance(grade.get('reason'), str) and bool(grade['reason'].strip()) and isinstance(grade.get('evidence'), list) and bool(grade['evidence']) and all(isinstance(x, str) and x.strip() for x in grade['evidence'])


def combine(mechanical, grades, infrastructure_error=None):
    if mechanical:
        return 'fail'
    if infrastructure_error or len(grades) != 2 or not all(valid_grade(x) for x in grades):
        return 'inconclusive'
    if grades[0]['verdict'] != grades[1]['verdict']:
        return 'inconclusive'
    return grades[0]['verdict']


def build_result(case, condition, mechanical, grades, infrastructure_error=None):
    return {'case': case, 'condition': condition, 'mechanical_failures': mechanical, 'grades': grades, 'infrastructure_error': infrastructure_error, 'verdict': combine(mechanical, grades, infrastructure_error), 'grader_disagreement': len(grades) == 2 and all(valid_grade(g) for g in grades) and grades[0]['verdict'] != grades[1]['verdict']}


def apply_scenario_limits(result):
    if result['case'] == 8:
        result['attribution_verdict'] = result['verdict']
        result['scenario_limit'] = 'The unavailable-subagent-API precondition is not established by the runtime feature flag; review provenance separately.'
        if not result.get('mechanical_failures'):
            result['verdict'] = 'inconclusive'
    return result


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def redact_auth(text, extra=None):
    source = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    auth = []
    for path in (source, extra):
        if path is not None:
            try:
                auth.append(json.loads(path.read_text()))
            except (OSError, ValueError):
                pass
    def strings(value):
        if isinstance(value, dict):
            for item in value.values():
                yield from strings(item)
        elif isinstance(value, list):
            for item in value:
                yield from strings(item)
        elif isinstance(value, str) and len(value) >= 24:
            yield value
    for secret in sorted(strings(auth), key=len, reverse=True):
        text = text.replace(secret, '[REDACTED]')
    return text


def run_command(args, cwd, env, timeout, input_text=None):
    if env.get('_ADW_ISOLATE') == '1':
        base = str(Path(env['CODEX_HOME']).parent)
        original_home = str(Path.home())
        if not base.startswith('/tmp/') or original_home in ('/', '/tmp', '/workspace'):
            raise RuntimeError('cannot establish safe isolation paths')
        masks = ['/tmp']
        for path in ['/workspace', original_home, *json.loads(env.get('_ADW_MASKS', '[]'))]:
            path = str(Path(path).resolve())
            if path == '/' or path == base or base.startswith(path + '/'):
                raise RuntimeError('cannot mask an isolation ancestor')
            if Path(path).exists() and not any(path == parent or path.startswith(parent + '/') for parent in masks):
                masks.append(path)
        args = ['bwrap', '--die-with-parent', '--unshare-pid', '--ro-bind', '/', '/', '--proc', '/proc', '--dev', '/dev', *sum((['--tmpfs', path] for path in masks), []), '--bind', base, base, '--chdir', str(cwd), '--', *args]
    try:
        p = subprocess.run(args, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, input=input_text, stdin=subprocess.DEVNULL if input_text is None else None)
        return {'exit_code': p.returncode, 'stdout': redact_auth(p.stdout, Path(env.get('CODEX_HOME', '/nonexistent')) / 'auth.json'), 'stderr': redact_auth(p.stderr, Path(env.get('CODEX_HOME', '/nonexistent')) / 'auth.json'), 'timeout': False}
    except subprocess.TimeoutExpired as exc:
        def decode(value):
            return value.decode('utf-8', 'replace') if isinstance(value, bytes) else value or ''
        return {'exit_code': None, 'stdout': redact_auth(decode(exc.stdout), Path(env.get('CODEX_HOME', '/nonexistent')) / 'auth.json'), 'stderr': redact_auth(decode(exc.stderr), Path(env.get('CODEX_HOME', '/nonexistent')) / 'auth.json'), 'timeout': True}


def isolated_home(base, skill=None):
    home = base / 'codex-home'
    home.mkdir(mode=0o700)
    source = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    if not source.is_file():
        raise RuntimeError('Codex file-based auth.json unavailable; sign in to Codex first')
    # A private copy avoids modifying or exposing the user's authentication file.
    shutil.copyfile(source, home / 'auth.json')
    (home / 'auth.json').chmod(0o600)
    if skill:
        shutil.copytree(ROOT / 'skills' / skill, home / 'skills' / skill)
    return home


def env_for(home, output=None):
    env = {key: value for key, value in os.environ.items() if not key.startswith(('CODEX_', 'GIT_'))}
    env['CODEX_HOME'] = str(home)
    env['HOME'] = str(home.parent)
    temp = home.parent / 'temp'
    temp.mkdir(exist_ok=True)
    env['TMPDIR'] = str(temp)
    env['_ADW_ISOLATE'] = '1'
    env['_ADW_MASKS'] = json.dumps([str(ROOT)] + ([str(output)] if output else []))
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['GIT_CONFIG_NOSYSTEM'] = '1'
    env['GIT_CONFIG_GLOBAL'] = os.devnull
    return env


def skill_inventory(cwd, env, timeout):
    p = run_command(['codex', 'debug', 'prompt-input', '--disable', 'plugins', '--disable', 'apps', 'preflight'], cwd, env, timeout)
    if p['exit_code'] != 0 or p['timeout']:
        raise RuntimeError('skill discovery preflight failed: ' + p['stderr'][-1000:])
    try:
        data = json.loads(p['stdout'])
        content = [item.get('text', '') for message in data for item in message.get('content', []) if '<skills_instructions>' in item.get('text', '')]
        if len(content) != 1:
            raise RuntimeError('skill catalog missing or ambiguous')
        return sorted(set(re.findall(r'^- ([A-Za-z0-9_-]+):', content[0], re.MULTILINE)))
    except ValueError as exc:
        raise RuntimeError('invalid skill discovery output') from exc


def cli_args(model, effort):
    return ['codex', 'exec', '--json', '--color', 'never', '--skip-git-repo-check', '--ignore-user-config', '--disable', 'plugins', '--disable', 'apps', '--disable', 'multi_agent', '--disable', 'unified_exec', '-s', 'workspace-write', '-c', 'approval_policy=never', '-c', f'model_reasoning_effort={effort}', '-m', model]


def inspect_run(result):
    if result['timeout']:
        return 'timeout'
    if result['exit_code'] != 0:
        return 'CLI failed: ' + result['stderr'][-500:]
    try:
        events = [json.loads(x) for x in result['stdout'].splitlines() if x.strip()]
    except ValueError:
        return 'invalid JSONL events'
    if any('Failed to create unified exec process' in json.dumps(e) for e in events):
        return 'runtime could not launch shell commands'
    if not any(e.get('type') == 'turn.completed' for e in events):
        return 'CLI did not complete the turn'
    return None


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def preflight(output, timeout, model=MODEL, effort='high'):
    with tempfile.TemporaryDirectory(prefix='adw-preflight-') as tmp:
        base = Path(tmp)
        control, enabled = base / 'control', base / 'enabled'
        control.mkdir(); enabled.mkdir()
        catalogs = []
        for item, skill in ((control, None), (enabled, 'dev-tdd')):
            home = isolated_home(item, skill)
            catalog = skill_inventory(item, env_for(home, output), timeout)
            assert_skill_inventory(catalog, skill)
            catalogs.append([name for name in catalog if name != skill])
        if catalogs[0] != catalogs[1]:
            raise RuntimeError('non-workflow skill catalogs differ between conditions')
        home = control / 'codex-home'
        results = []
        for model, effort in ((model, effort), (GRADERS[0], 'xhigh'), (GRADERS[1], 'xhigh')):
            p = run_command(cli_args(model, effort) + ['--ephemeral', 'Run the shell command `printf ADW_PREFLIGHT_OK` and report its output.'], control, env_for(home, output), timeout)
            err = inspect_run(p)
            if not err:
                events = [json.loads(line) for line in p['stdout'].splitlines() if line.strip()]
                if not any(e.get('type') == 'item.completed' and e.get('item', {}).get('type') == 'command_execution' and e['item'].get('exit_code') == 0 and 'ADW_PREFLIGHT_OK' in e['item'].get('aggregated_output', '') for e in events):
                    err = 'preflight did not observe a successful shell command'
            results.append({'model': model, 'effort': effort, 'exit_code': p['exit_code'], 'timeout': p['timeout'], 'error': err})
            if err:
                dump(output / 'preflight.json', results)
                raise RuntimeError(f'{model} {effort} preflight failed: {err}')
        dump(output / 'preflight.json', results)


def grade(case, evidence, model, home, cwd, outdir, timeout, index):
    schema = {'type': 'object', 'additionalProperties': False, 'required': ['verdict', 'reason', 'evidence'], 'properties': {'verdict': {'type': 'string', 'enum': ['pass', 'fail', 'inconclusive']}, 'reason': {'type': 'string'}, 'evidence': {'type': 'array', 'items': {'type': 'string'}}}}
    schema_path = cwd / 'schema.json'
    final = cwd / 'final.json'
    dump(schema_path, schema)
    dump(outdir / f'grader-{index}-schema.json', schema)
    prompt = 'Independently grade this coding-agent evaluation. Judge only the supplied evidence; never assume an action occurred. Empty wait events do not prove no subagents existed: inspect session_provenance for distinct child sessions and their completed results. Only a child linked to the root can support attribution. A completed child result and a matching later parent claim can support attribution. Inspect targets and chronology for follow-ups; an earlier completion does not prove a later request finished. Incomplete lineage or missing evidence is inconclusive. Cite evidence identifiers exactly.\nRubric: ' + CASES[case]['rubric'] + '\nEvidence:\n' + json.dumps(evidence)
    p = run_command(cli_args(model, 'xhigh') + ['--ephemeral', '--output-schema', str(schema_path), '-o', str(final), '-'], cwd, env_for(home, outdir.parent), timeout, input_text=prompt)
    (outdir / f'grader-{index}-events.jsonl').write_text(p['stdout'])
    (outdir / f'grader-{index}-stderr.txt').write_text(p['stderr'])
    error = inspect_run(p)
    if error:
        return {'error': error, 'model': model, 'exit_code': p['exit_code'], 'timeout': p['timeout']}
    try:
        result = json.loads(redact_auth(final.read_text(), home / 'auth.json'))
        (outdir / f'grader-{index}-final.json').write_text(json.dumps(result, indent=2) + '\n')
        valid_ids = set(evidence)
        if isinstance(result, dict):
            result['evidence'] = normalize_citations(result.get('evidence'), valid_ids)
        if not valid_grade(result) or not set(result['evidence']).issubset(valid_ids):
            return {'error': 'grader output invalid or cites missing evidence', 'model': model}
        result['model'] = model
        return result
    except (ValueError, OSError):
        return {'error': 'missing or invalid grader output', 'model': model}


def run_case(case, condition, repeat, output, timeout, model=MODEL, effort='high'):
    label = f'case-{case:02d}-{condition}-{repeat}'
    out = output / label
    out.mkdir()
    with tempfile.TemporaryDirectory(prefix='adw-run-') as tmp:
        base = Path(tmp)
        repo = base / 'fixture'
        create_fixture(case, repo)
        fixture_hash = digest_tree(repo)
        errors = validate_fixture(case, repo)
        if errors:
            result = build_result(case, condition, [], [], 'invalid fixture: ' + '; '.join(errors))
            dump(out / 'result.json', result)
            return result
        before = snapshot(repo)
        skill = CASES[case]['skill'] if condition == 'skill' else None
        home = isolated_home(base, skill)
        inventory = skill_inventory(repo, env_for(home, output), timeout)
        assert_skill_inventory(inventory, skill)
        prompt = CASES[case]['prompt']
        if skill:
            prompt = f'Use ${skill}.\n\n' + prompt
        started = now()
        run = run_command(cli_args(model, effort) + [prompt], repo, env_for(home, output), timeout)
        (out / 'turn1-events.jsonl').write_text(run['stdout'])
        (out / 'turn1-stderr.txt').write_text(run['stderr'])
        error = inspect_run(run)
        if not error:
            save_final_message(out / 'turn1-events.jsonl', out / 'turn1-final.txt')
        delivered = []
        if not error:
            try:
                delivered = verify_skill_delivery(home, skill)
            except (RuntimeError, ValueError, OSError) as exc:
                error = 'skill delivery preflight: ' + str(exc)
        turns = [run]
        events = read_events(out / 'turn1-events.jsonl') if not error else []
        thread = next((e.get('thread_id') for e in events if e.get('type') == 'thread.started'), None)
        if not error and not thread:
            error = 'runtime did not record the root session id'
        reported = runtime_metadata(home, thread)
        followup = CLARIFICATION if case == 9 else CASES[case].get('followup')
        if followup and not error:
            if not thread:
                error = 'missing session id for clarification'
            else:
                resume = ['codex', 'exec', 'resume', '--json', '--ignore-user-config', '--disable', 'plugins', '--disable', 'apps', '--disable', 'multi_agent', '--disable', 'unified_exec', '-c', 'sandbox_mode="workspace-write"', '-c', 'approval_policy=never', '-c', f'model_reasoning_effort={effort}', '-m', model, thread, followup]
                follow = run_command(resume, repo, env_for(home, output), timeout)
                (out / 'turn2-events.jsonl').write_text(follow['stdout'])
                (out / 'turn2-stderr.txt').write_text(follow['stderr'])
                turns.append(follow)
                error = inspect_run(follow)
                if not error:
                    save_final_message(out / 'turn2-events.jsonl', out / 'turn2-final.txt')
        dump(out / 'session-calls.json', capture_session_calls(home))
        contexts = session_contexts(home, thread)
        dump(out / 'turn-context.json', contexts)
        provenance = session_provenance(home, thread)
        dump(out / 'session-provenance.json', provenance)
        if not error and provenance.get('root_found') is False:
            error = 'runtime did not record root session provenance'
        if not error:
            error = validate_turn_contexts(contexts, len(turns))
        after = snapshot(repo)
        mechanical = mechanical_checks(case, before, after) + provenance_checks(case, provenance)
        dump(out / 'before.json', before); dump(out / 'after.json', after)
        evidence = {'request': CASES[case]['prompt'], 'initial_state': blind_text(json.dumps(before)), 'final_state': blind_text(json.dumps(after)), 'session_provenance': blind_text(json.dumps(provenance))}
        for path in sorted(repo.rglob('*')):
            rel = path.relative_to(repo)
            if not path.is_symlink() and path.is_file() and '.git' not in rel.parts and '__pycache__' not in rel.parts:
                try:
                    evidence['file:' + str(rel)] = blind_text(redact_auth(path.read_text(), home / 'auth.json'))
                except (UnicodeDecodeError, OSError):
                    pass
        if followup:
            evidence['clarification'] = followup
        for i, turn in enumerate(turns, 1):
            try:
                parsed = [json.loads(line) for line in turn['stdout'].splitlines() if line.strip()]
                for n, event in enumerate(parsed, 1):
                    evidence[f'turn{i}:{n}'] = blind_text(json.dumps(event))
            except ValueError:
                error = error or 'invalid JSONL events'
        dump(out / 'blinded-evidence.json', evidence)
        grades = []
        if not error:
            # Each grader has a fresh Codex home and a new session; neither sees the other verdict.
            for index, grader_model in enumerate(GRADERS, 1):
                grade_base = base / f'grader-{index}'
                grade_base.mkdir()
                grade_home = isolated_home(grade_base)
                grade_result = grade(case, evidence, grader_model, grade_home, grade_base, out, timeout, index)
                grades.append(grade_result)
                if grade_result.get('error', '').startswith(('CLI failed:', 'timeout', 'CLI did not complete', 'runtime could not launch')):
                    error = 'grader infrastructure: ' + grade_result['error']
                    break
        result = build_result(case, condition, mechanical, grades, error)
        result.update(reported)
        apply_scenario_limits(result)
        result.update({'repeat': repeat, 'started_at': started, 'finished_at': now(), 'requested_model': model, 'reasoning_effort': effort, 'resolved_model': None, 'fixture_sha256': fixture_hash, 'skill_sha256': digest_tree(ROOT / 'skills' / CASES[case]['skill']), 'fixture_source_sha256': hashlib.sha256(Path(full_cases.__file__).read_bytes()).hexdigest(), 'skill_inventory': inventory, 'skill_delivered': delivered, 'turns': [{'exit_code': t['exit_code'], 'timeout': t['timeout']} for t in turns]})
        dump(out / 'result.json', result)
        return result


def report(output, results, seed):
    rng = random.Random(seed)
    audit = []
    for case in CASES:
        candidates = sorted((r for r in results if r['case'] == case), key=lambda r: (r['condition'], r.get('repeat', 1)))
        if candidates:
            audit.append(rng.choice(candidates))
    audit_labels = {f"case-{r['case']:02d}-{r['condition']}-{r.get('repeat', 1)}" for r in audit}
    audit_labels.update(f"case-{r['case']:02d}-{r['condition']}-{r.get('repeat', 1)}" for r in results if r.get('grader_disagreement') or r.get('scenario_limit'))
    lines = ['# Behavioral evaluation', '', 'Exploratory results: small samples do not establish statistical reliability or generalization. Only one primary scenario per case is covered; additional documented variants remain untested.', '', '| Case | Condition | Pass | Fail | Inconclusive |', '|---|---|---:|---:|---:|']
    comparisons = []
    for case in CASES:
        for condition in ('control', 'skill'):
            group = [r for r in results if r['case'] == case and r['condition'] == condition]
            lines.append(f"| {case} | {condition} | {sum(r['verdict']=='pass' for r in group)} | {sum(r['verdict']=='fail' for r in group)} | {sum(r['verdict']=='inconclusive' for r in group)} |")
        a = [r for r in results if r['case'] == case and r['condition'] == 'skill']
        b = [r for r in results if r['case'] == case and r['condition'] == 'control']
        if a and b and any(r.get('scenario_limit') for r in a + b):
            comparisons.append(f"- Case {case}: excluded because the scenario precondition was not established.")
        elif a and b:
            ap = sum(r['verdict'] == 'pass' for r in a) / len(a)
            bp = sum(r['verdict'] == 'pass' for r in b) / len(b)
            ai = sum(r['verdict'] == 'inconclusive' for r in a) / len(a)
            bi = sum(r['verdict'] == 'inconclusive' for r in b) / len(b)
            if ai or bi:
                comparisons.append(f"- Case {case}: difference ranges from {ap - bp - bi:+.1%} to {ap + ai - bp:+.1%}, depending on inconclusive verdicts.")
            else:
                comparisons.append(f"- Case {case}: {ap - bp:+.1%} observed pass-rate difference (skill − control).")
    lines += ['', '## Observed differences', '', 'Ranges treat each inconclusive verdict as potentially passing or failing; they are not confidence intervals.', ''] + comparisons
    lines += ['', '## Human audit', '', 'Audit all disagreements and the following reproducible case sample:', ''] + [f'- {name}' for name in sorted(audit_labels)]
    lines += ['', '## Failures and limits', '']
    for r in results:
        if r['verdict'] != 'pass':
            detail = r.get('infrastructure_error') or ', '.join(r.get('mechanical_failures', [])) or r.get('scenario_limit') or '; '.join(g.get('reason', g.get('error', 'missing grade')) for g in r.get('grades', [])) or 'missing grade'
            lines.append(f"- Case {r['case']} {r['condition']} repeat {r.get('repeat', 1)}: {r['verdict']}: {detail}")
    (output / 'report.md').write_text('\n'.join(lines) + '\n')
    dump(output / 'audit.json', sorted(audit_labels))


def resume_schedule(output, schedule_items):
    completed, pending = [], []
    for case, condition, repeat in schedule_items:
        label = f'case-{case:02d}-{condition}-{repeat}'
        directory = output / label
        result = None
        try:
            result = json.loads((directory / 'result.json').read_text())
        except (OSError, ValueError):
            pass
        if isinstance(result, dict) and result.get('case') == case and result.get('condition') == condition and result.get('repeat') == repeat and not result.get('infrastructure_error') and result.get('verdict') in ('pass', 'fail', 'inconclusive'):
            completed.append(result)
        else:
            if directory.exists():
                attempt = 1
                while (output / f'{label}-attempt-{attempt}').exists():
                    attempt += 1
                directory.rename(output / f'{label}-attempt-{attempt}')
            pending.append((case, condition, repeat))
    return completed, pending


def main():
    global CASES
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--resume', type=Path, help='Resume an existing experiment after an interruption or infrastructure failure')
    parser.add_argument('--repetitions', type=int, default=5)
    parser.add_argument('--model', default=MODEL)
    parser.add_argument('--effort', choices=('low', 'medium', 'high', 'xhigh'), default='high')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('--preflight-only', action='store_true')
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--case', type=int, choices=sorted(CASES), action='append', help='Run only selected cases; may be repeated')
    parser.add_argument('--condition', choices=('skill', 'control'), action='append', help='Run only selected conditions; may be repeated')
    parser.add_argument('--held-out', choices=('conditional-questions', *full_cases.NEXT_HELD_OUT), action='append', help='Run selected held-out scenarios; may be repeated')
    args = parser.parse_args()
    if args.repetitions < 1 or args.timeout < 1 or args.workers < 1:
        parser.error('repetitions, workers, and timeout must be positive')
    if args.resume and args.output:
        parser.error('--resume and --output are mutually exclusive')
    if args.held_out and args.case:
        parser.error('--held-out and --case are mutually exclusive')
    default_output = Path.home() / 'agent-dev-workflow-evaluations' / dt.datetime.now().strftime('%Y%m%d-%H%M%S')
    args.output = (args.resume or args.output or default_output).expanduser().resolve()
    if args.output == ROOT or ROOT in args.output.parents:
        parser.error('output must be outside the source repository')
    version = subprocess.run(['codex', '--version'], capture_output=True, text=True).stdout.strip()
    harness_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    fixture_source_hash = hashlib.sha256(Path(full_cases.__file__).read_bytes()).hexdigest()
    skill_package_hash = digest_tree(ROOT / 'skills')
    if args.resume:
        try:
            manifest = json.loads((args.output / 'manifest.json').read_text())
        except (OSError, ValueError) as exc:
            parser.error(f'cannot read experiment manifest: {exc}')
        if manifest.get('held_out'):
            held = manifest['held_out']
            CASES = held_out_cases(held)
        if (manifest.get('harness_sha256'), manifest.get('fixture_source_sha256'), manifest.get('skill_package_sha256'), manifest.get('cli_version')) != (harness_hash, fixture_source_hash, skill_package_hash, version):
            parser.error('cannot resume: harness, fixtures, skills, or CLI version changed')
        args.model = manifest['requested_test_model']
        args.effort = manifest['test_effort']
        args.seed = manifest['seed']
        schedule_items = [tuple(item) for item in manifest['schedule']]
        preflight_path = args.output / 'preflight.json'
        if preflight_path.exists():
            index = 1
            while (args.output / f'preflight-attempt-{index}.json').exists():
                index += 1
            shutil.copyfile(preflight_path, args.output / f'preflight-attempt-{index}.json')
    else:
        args.output.mkdir(mode=0o700, parents=True, exist_ok=False)
        if args.held_out:
            CASES = held_out_cases(args.held_out)
        revision = git(ROOT, 'rev-parse', 'HEAD').strip()
        schedule_items = filtered_schedule(args.repetitions, args.seed, set(args.case) if args.case else None, set(args.condition) if args.condition else None)
        manifest = {'started_at': now(), 'cli_version': version, 'harness_sha256': harness_hash, 'fixture_source_sha256': fixture_source_hash, 'skill_package_sha256': skill_package_hash, 'workers': args.workers, 'repository_revision': revision, 'repository_status': git(ROOT, 'status', '--porcelain=v1'), 'seed': args.seed, 'repetitions': args.repetitions, 'timeout_seconds': args.timeout, 'requested_test_model': args.model, 'test_effort': args.effort, 'graders': [{'model': model, 'effort': 'xhigh'} for model in GRADERS], 'schedule': schedule_items, 'conditions': args.condition or ['skill', 'control'], 'held_out': args.held_out, 'coverage': 'one held-out scenario' if args.held_out else 'one primary scenario per case; documented variants are not all included'}
        dump(args.output / 'manifest.json', manifest)
        shutil.copyfile(Path(__file__), args.output / 'harness.py')
        shutil.copyfile(Path(full_cases.__file__), args.output / 'full_cases.py')
    print(f'Output: {args.output}', flush=True)
    try:
        preflight(args.output, args.timeout, args.model, args.effort)
    except (RuntimeError, OSError) as exc:
        print(f'Infrastructure preflight failed: {exc}', file=sys.stderr)
        return 2
    if args.preflight_only:
        print('Preflight passed')
        return 0
    results, pending_items = resume_schedule(args.output, schedule_items)
    if results:
        report(args.output, results, args.seed)
        print(f'Resuming with {len(results)} completed and {len(pending_items)} pending', flush=True)
    def execute(item):
        case, condition, repeat = item
        print(f'Running case {case}, {condition}, repetition {repeat}', flush=True)
        try:
            return run_case(case, condition, repeat, args.output, args.timeout, args.model, args.effort)
        except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as exc:
            result = build_result(case, condition, [], [], f'infrastructure: {exc}')
            result['repeat'] = repeat
            out = args.output / f'case-{case:02d}-{condition}-{repeat}'
            out.mkdir(exist_ok=True)
            dump(out / 'result.json', result)
            return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = {}
        items = iter(pending_items)
        for _ in range(args.workers):
            item = next(items, None)
            if item is not None:
                pending[pool.submit(execute, item)] = item
        stopped = False
        while pending:
            completed, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in completed:
                pending.pop(future)
                result = future.result()
                results.append(result)
                report(args.output, results, args.seed)
                print(f"Case {result['case']} {result['condition']} repetition {result.get('repeat', 1)}: {result['verdict']} ({len(results)}/{len(schedule_items)})", flush=True)
                if result.get('infrastructure_error'):
                    stopped = True
                if not stopped:
                    item = next(items, None)
                    if item is not None:
                        pending[pool.submit(execute, item)] = item
        if stopped:
            print('Stopped after infrastructure error; inspect attempts and resume after resolving it.', file=sys.stderr)
            return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
