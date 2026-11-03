import json
import tempfile
import unittest
from unittest import mock
import subprocess
import shutil
from pathlib import Path

from evaluation import pilot, regrade


class PilotTests(unittest.TestCase):
    def test_fixture_integrity(self):
        with tempfile.TemporaryDirectory() as root:
            for case in pilot.CASES:
                target = Path(root) / str(case)
                pilot.create_fixture(case, target)
                self.assertEqual(pilot.validate_fixture(case, target), [], case)

    def test_all_documented_cases_have_fixtures(self):
        self.assertEqual(set(pilot.CASES), set(range(1, 24)))
        with tempfile.TemporaryDirectory() as root:
            for case in range(1, 24):
                repo = Path(root) / str(case)
                pilot.create_fixture(case, repo)
                self.assertEqual(pilot.validate_fixture(case, repo), [], case)

    def test_regression_fixture_preserves_unrelated_staged_and_unstaged_work(self):
        with tempfile.TemporaryDirectory() as root:
            repo = Path(root) / 'repo'
            pilot.create_fixture(5, repo)
            before = pilot.snapshot(repo)
            self.assertIn('notes-staged.txt', before['index_diff'])
            self.assertIn('notes-unstaged.txt', before['worktree_diff'])
            (repo / 'notes-unstaged.txt').write_text('overwritten')
            self.assertIn('unrelated work changed', pilot.mechanical_checks(5, before, pilot.snapshot(repo)))

    def test_experiment_model_configuration(self):
        args = pilot.cli_args('gpt-6.1-sol', 'medium')
        self.assertIn('gpt-6.1-sol', args)
        self.assertIn('model_reasoning_effort=medium', args)

    def test_held_out_fixture_has_clear_conditional_dependency(self):
        with tempfile.TemporaryDirectory() as root:
            repo = Path(root) / 'repo'
            pilot.create_fixture(24, repo)
            self.assertEqual(pilot.validate_fixture(24, repo), [])
            self.assertIn('without a portal', (repo / 'README.md').read_text())

    def test_new_held_out_fixtures_have_decidable_contracts(self):
        with tempfile.TemporaryDirectory() as root:
            for case in (25, 26, 27, 28, 29):
                repo = Path(root) / str(case)
                pilot.create_fixture(case, repo)
                self.assertEqual(pilot.validate_fixture(case, repo), [], case)

    def test_verification_fixture_checks_real_export_behavior(self):
        with tempfile.TemporaryDirectory() as root:
            repo = Path(root) / 'repo'
            pilot.create_fixture(18, repo)
            self.assertEqual(pilot.validate_fixture(18, repo), [])
            (repo / 'export.py').write_text('def download(user):\n    return 403, ""\n')
            errors = pilot.validate_fixture(18, repo)
            self.assertTrue(any('authorized check has wrong exit status' in error for error in errors))

    def test_schedule_reproducible_and_balanced(self):
        schedule = pilot.schedule(3, 42)
        self.assertEqual(schedule, pilot.schedule(3, 42))
        self.assertEqual(len(schedule), 138)
        self.assertEqual(len(set(schedule)), 138)
        for case in pilot.CASES:
            self.assertEqual(sum(row[0] == case for row in schedule), 6)

    def test_resume_preserves_completed_and_retries_infrastructure_failures(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root)
            items = [(1, 'control', 1), (1, 'skill', 1), (2, 'control', 1)]
            for label, record in [('case-01-control-1', {'case': 1, 'condition': 'control', 'repeat': 1, 'verdict': 'pass', 'infrastructure_error': None}), ('case-01-skill-1', {'case': 1, 'condition': 'skill', 'repeat': 1, 'verdict': 'inconclusive', 'infrastructure_error': 'timeout'})]:
                directory = output / label
                directory.mkdir()
                (directory / 'result.json').write_text(json.dumps(record))
            completed, pending = pilot.resume_schedule(output, items)
            self.assertEqual(len(completed), 1)
            self.assertEqual(pending, [(1, 'skill', 1), (2, 'control', 1)])
            self.assertTrue((output / 'case-01-skill-1-attempt-1/result.json').exists())
            self.assertTrue((output / 'case-01-control-1/result.json').exists())

    def test_multiple_held_out_cases_are_selected_without_duplicates(self):
        selected = pilot.held_out_cases(['invoice-no-access', 'invoice-access', 'invoice-no-access'])
        self.assertEqual(set(selected), {25, 28})
        self.assertEqual(pilot.held_out_cases('conditional-questions'), {24: pilot.full_cases.HELD_OUT_CASE})

    def test_schedule_condition_filter(self):
        rows = pilot.filtered_schedule(2, 42, cases={15}, conditions={'skill'})
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(case == 15 and condition == 'skill' for case, condition, _ in rows))

    def test_verdict_does_not_hide_uncertainty(self):
        valid_pass = {'verdict': 'pass', 'reason': 'supported', 'evidence': ['turn1:1']}
        valid_fail = {'verdict': 'fail', 'reason': 'defect', 'evidence': ['turn1:2']}
        self.assertEqual(pilot.combine([], [valid_pass, valid_pass]), 'pass')
        self.assertEqual(pilot.combine([], [valid_pass, valid_fail]), 'inconclusive')
        self.assertEqual(pilot.combine(['unauthorized edit'], [valid_pass, valid_pass]), 'fail')
        self.assertEqual(pilot.combine([], [valid_pass, {}]), 'inconclusive')
        self.assertEqual(pilot.combine([], [valid_pass, valid_pass], infrastructure_error='timeout'), 'inconclusive')
        self.assertEqual(pilot.combine([], [{'verdict':'pass','reason':'x','evidence':[]}, valid_pass]), 'inconclusive')

    def test_read_only_snapshot_preserves_staged_and_untracked(self):
        with tempfile.TemporaryDirectory() as root:
            repo = Path(root) / 'repo'
            pilot.create_fixture(21, repo)
            before = pilot.snapshot(repo)
            self.assertTrue(before['index_diff'])
            self.assertEqual(pilot.mechanical_checks(21, before, pilot.snapshot(repo)), [])
            (repo / 'extra.txt').write_text('new')
            self.assertIn('unauthorized edit', pilot.mechanical_checks(21, before, pilot.snapshot(repo)))

    def test_redaction_and_jsonl_errors(self):
        self.assertNotIn('dev-code-review', pilot.blind_text('using /tmp/skills/dev-code-review/SKILL.md'))
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'events.jsonl'
            path.write_text('{invalid}\n')
            self.assertRaises(ValueError, pilot.read_events, path)

    def test_citations_must_resolve_to_supplied_evidence(self):
        known = {'turn1:1', 'turn1:10', 'file:spec.md'}
        self.assertEqual(pilot.normalize_citations(['turn1:10: finding', 'file:spec.md supports it'], known), ['file:spec.md', 'turn1:10'])
        self.assertEqual(pilot.normalize_citations(['turn1:1', 'turn1:11'], known), [])

    def test_result_records_timeout_and_invalid_grades(self):
        result = pilot.build_result(18, 'control', [], [{}, {}], 'timeout')
        self.assertEqual(result['verdict'], 'inconclusive')
        self.assertEqual(result['infrastructure_error'], 'timeout')

    def test_preflight_rejects_skill_contamination(self):
        pilot.assert_skill_inventory([], None)
        pilot.assert_skill_inventory(['dev-tdd'], 'dev-tdd')
        with self.assertRaises(RuntimeError):
            pilot.assert_skill_inventory(['dev-tdd'], None)
        with self.assertRaises(RuntimeError):
            pilot.assert_skill_inventory(['dev-tdd', 'dev-spec'], 'dev-tdd')

    def test_report_keeps_inconclusive_outcomes_distinct(self):
        results = [{'case': 1, 'condition': 'control', 'repeat': 1, 'verdict': 'fail'}, {'case': 1, 'condition': 'skill', 'repeat': 1, 'verdict': 'inconclusive'}]
        with tempfile.TemporaryDirectory() as root:
            pilot.report(Path(root), results, 42)
            report = (Path(root) / 'report.md').read_text()
            self.assertIn('Case 1: difference ranges from +0.0% to +100.0%', report)
            self.assertIn('not confidence intervals', report)

    def test_skill_delivery_checked_from_actual_session_input(self):
        with tempfile.TemporaryDirectory() as root:
            home = Path(root)
            sessions = home / 'sessions'
            sessions.mkdir()
            skill = (pilot.ROOT / 'skills/dev-tdd/SKILL.md').read_text()
            record = {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user', 'content': [{'text': skill}]}}
            (sessions / 'session.jsonl').write_text(json.dumps(record) + '\n')
            self.assertEqual(pilot.verify_skill_delivery(home, 'dev-tdd'), ['dev-tdd'])
            with self.assertRaises(RuntimeError):
                pilot.verify_skill_delivery(home, None)
            record['payload']['content'][0]['text'] = 'request only'
            (sessions / 'session.jsonl').write_text(json.dumps(record) + '\n')
            self.assertEqual(pilot.verify_skill_delivery(home, None), [])
            with self.assertRaises(RuntimeError):
                pilot.verify_skill_delivery(home, 'dev-tdd')

    @unittest.skipUnless(shutil.which('bwrap') and Path('/var/tmp').is_dir(), 'requires Linux bwrap')
    def test_isolation_hides_rubrics_and_external_output(self):
        with tempfile.TemporaryDirectory(prefix='adw-test-', dir='/tmp') as scratch, tempfile.TemporaryDirectory(prefix='adw-output-', dir='/var/tmp') as output:
            base, output = Path(scratch), Path(output)
            home = base / 'codex-home'
            home.mkdir()
            (output / 'grader.txt').write_text('private')
            command = ['/bin/sh', '-c', 'test ! -e "$1" && test ! -e "$2"', 'sh', str(pilot.ROOT / 'references/calibration-cases.md'), str(output / 'grader.txt')]
            result = pilot.run_command(command, base, pilot.env_for(home, output), 10)
            self.assertEqual(result['exit_code'], 0, result['stderr'])

    def test_snapshot_does_not_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            repo = root / 'repo'
            pilot.create_fixture(21, repo)
            private = root / 'private.txt'
            private.write_text('private content')
            (repo / 'link').symlink_to(private)
            state = pilot.snapshot(repo)
            self.assertTrue(state['files']['link'].startswith('symlink:'))
            self.assertNotIn('private content', json.dumps(state))

    def test_capture_session_calls_keeps_patch_and_ignores_messages(self):
        with tempfile.TemporaryDirectory() as root:
            home = Path(root) / 'codex-home'
            sessions = home / 'sessions'
            sessions.mkdir(parents=True)
            records = [
                {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user', 'content': [{'text': 'private user text'}]}},
                {'type': 'response_item', 'payload': {'type': 'custom_tool_call', 'name': 'apply_patch', 'call_id': 'call-1', 'input': '*** Update File: plan.md\n+Status: STALE'}},
                {'type': 'response_item', 'payload': {'type': 'custom_tool_call_output', 'call_id': 'call-1', 'output': 'patch applied'}},
            ]
            (sessions / 'one.jsonl').write_text(''.join(json.dumps(item) + '\n' for item in records))
            captured = pilot.capture_session_calls(home)
            self.assertEqual(len(captured), 1)
            self.assertIn('Status: STALE', captured[0]['input'])
            self.assertEqual(captured[0]['output'], 'patch applied')
            self.assertNotIn('private user text', json.dumps(captured))

    def test_resume_requires_workspace_write_on_each_turn(self):
        good = {'sandbox_policy': {'type': 'workspace-write'}}
        bad = {'sandbox_policy': {'type': 'read-only'}}
        self.assertIsNone(pilot.validate_turn_contexts([good, good], 2))
        self.assertIsNotNone(pilot.validate_turn_contexts([good, bad], 2))
        self.assertIsNotNone(pilot.validate_turn_contexts([good], 2))
        self.assertIsNotNone(pilot.validate_turn_contexts([good, good, bad], 2))

    def test_session_provenance_preserves_real_child_result(self):
        with tempfile.TemporaryDirectory() as root:
            home = Path(root) / 'codex-home'
            sessions = home / 'sessions'
            sessions.mkdir(parents=True)
            root_records = [
                {'type': 'session_meta', 'payload': {'id': 'root-1', 'source': 'exec'}},
                {'type': 'response_item', 'payload': {'type': 'function_call', 'name': 'spawn_agent', 'call_id': 'call-1', 'arguments': '{"task_name":"reviewer"}'}},
                {'type': 'response_item', 'payload': {'type': 'function_call_output', 'call_id': 'call-1', 'output': '{"task_name":"/root/reviewer"}'}},
            ]
            child_records = [
                {'type': 'session_meta', 'payload': {'id': 'child-1', 'source': {'subagent': {'thread_spawn': {'parent_thread_id': 'root-1', 'agent_path': '/root/reviewer'}}}}},
                {'type': 'event_msg', 'timestamp': '2026-01-01T00:00:00Z', 'payload': {'type': 'task_complete', 'last_agent_message': 'Reviewer result: found a defect.'}},
                {'type': 'event_msg', 'timestamp': '2026-01-01T00:01:00Z', 'payload': {'type': 'task_complete', 'last_agent_message': 'Follow-up: one more detail.'}},
            ]
            for name, records in (('root.jsonl', root_records), ('child.jsonl', child_records)):
                (sessions / name).write_text(''.join(json.dumps(record) + '\n' for record in records))
            provenance = pilot.session_provenance(home, 'root-1')
            self.assertEqual(provenance['root_session_id'], 'root-1')
            self.assertEqual(provenance['children'][0]['parent_session_id'], 'root-1')
            self.assertTrue(provenance['children'][0]['has_completed_result'])
            self.assertIn('found a defect', provenance['children'][0]['completions'][0]['result'])
            self.assertEqual(len(provenance['children'][0]['completions']), 2)
            self.assertEqual(provenance['collaboration_calls'][0]['result'], {'task_name': '/root/reviewer'})
            self.assertEqual(provenance['collaboration_calls'][0]['targets']['task_name'], 'reviewer')

    def test_provenance_preserves_followup_targets_and_redacts_auth(self):
        with tempfile.TemporaryDirectory() as root:
            home = Path(root) / 'codex-home'
            sessions = home / 'sessions'
            sessions.mkdir(parents=True)
            secret = 'secret-token-that-must-not-appear-12345'
            (home / 'auth.json').write_text(json.dumps({'access_token': secret}))
            root_records = [
                {'type': 'session_meta', 'payload': {'id': 'root-1', 'source': 'exec'}},
                {'type': 'response_item', 'timestamp': '2026-01-01T00:02:00Z', 'payload': {'type': 'function_call', 'name': 'followup_task', 'call_id': 'call-2', 'arguments': json.dumps({'target': '/root/reviewer', 'message': secret})}},
                {'type': 'response_item', 'payload': {'type': 'function_call_output', 'call_id': 'call-2', 'output': json.dumps({'message': secret})}},
            ]
            child_records = [
                {'type': 'session_meta', 'payload': {'id': 'child-1', 'source': {'subagent': {'thread_spawn': {'parent_thread_id': 'root-1', 'agent_path': '/root/reviewer'}}}}},
                {'type': 'event_msg', 'timestamp': '2026-01-01T00:01:00Z', 'payload': {'type': 'task_complete', 'last_agent_message': secret}},
            ]
            for name, records in (('root.jsonl', root_records), ('child.jsonl', child_records)):
                (sessions / name).write_text(''.join(json.dumps(r) + '\n' for r in records))
            provenance = pilot.session_provenance(home, 'root-1')
            self.assertEqual(provenance['collaboration_calls'][0]['targets']['target'], '/root/reviewer')
            self.assertEqual(provenance['collaboration_calls'][0]['timestamp'], '2026-01-01T00:02:00Z')
            self.assertNotIn(secret, json.dumps(provenance))

    def test_provenance_marks_unrelated_child_and_retains_order(self):
        with tempfile.TemporaryDirectory() as root:
            home = Path(root) / 'codex-home'
            sessions = home / 'sessions'
            sessions.mkdir(parents=True)
            records = {
                'root.jsonl': [
                    {'type': 'session_meta', 'payload': {'id': 'root-1', 'source': 'exec'}},
                    {'type': 'response_item', 'timestamp': '2026-01-01T00:00:00Z', 'payload': {'type': 'message', 'role': 'assistant', 'content': [{'text': 'A reviewer found a defect.'}]}},
                    {'type': 'response_item', 'timestamp': '2026-01-01T00:02:00Z', 'payload': {'type': 'function_call', 'name': 'followup_task', 'call_id': 'f', 'arguments': json.dumps({'target': '/root/reviewer'})}},
                ],
                'child.jsonl': [
                    {'type': 'session_meta', 'payload': {'id': 'child-1', 'source': {'subagent': {'thread_spawn': {'parent_thread_id': 'root-1', 'agent_path': '/root/reviewer'}}}}},
                    {'type': 'event_msg', 'timestamp': '2026-01-01T00:01:00Z', 'payload': {'type': 'task_complete', 'turn_id': 'turn-1', 'last_agent_message': 'First review.'}},
                ],
                'unrelated.jsonl': [
                    {'type': 'session_meta', 'payload': {'id': 'unrelated', 'source': {'subagent': {'thread_spawn': {'parent_thread_id': 'other-root', 'agent_path': '/other/reviewer'}}}}},
                    {'type': 'event_msg', 'payload': {'type': 'task_complete', 'last_agent_message': 'Unrelated result.'}},
                ],
            }
            for name, entries in records.items():
                (sessions / name).write_text(''.join(json.dumps(r) + '\n' for r in entries))
            data = pilot.session_provenance(home, 'root-1')
            by_id = {child['session_id']: child for child in data['children']}
            self.assertTrue(by_id['child-1']['linked_to_root'])
            self.assertFalse(by_id['unrelated']['linked_to_root'])
            self.assertEqual(by_id['child-1']['completions'][0]['turn_id'], 'turn-1')
            self.assertLess(data['parent_messages'][0]['timestamp'], by_id['child-1']['completions'][0]['timestamp'])
            self.assertGreater(data['collaboration_calls'][0]['timestamp'], by_id['child-1']['completions'][0]['timestamp'])

    def test_explicit_self_review_rejects_delegation(self):
        self.assertEqual(pilot.provenance_checks(29, {'collaboration_calls': []}), [])
        self.assertIn('unauthorized delegation', pilot.provenance_checks(29, {'collaboration_calls': [{'name': 'spawn_agent'}]}))
        self.assertEqual(pilot.provenance_checks(8, {'collaboration_calls': [{'name': 'spawn_agent'}]}), [])

    def test_unavailable_scenario_does_not_hide_read_only_failure(self):
        grade = {'verdict': 'pass', 'reason': 'review returned', 'evidence': ['session_provenance']}
        result = pilot.apply_scenario_limits(pilot.build_result(8, 'skill', ['unauthorized edit'], [grade, grade]))
        self.assertEqual(result['verdict'], 'fail')
        self.assertTrue(result['scenario_limit'])
        unknown = pilot.apply_scenario_limits(pilot.build_result(8, 'skill', [], [grade, grade]))
        self.assertEqual(unknown['verdict'], 'inconclusive')
        self.assertEqual(unknown['attribution_verdict'], 'pass')

    def test_report_excludes_invalid_precondition_from_comparisons(self):
        results = [pilot.apply_scenario_limits({'case': 8, 'condition': condition, 'repeat': 1, 'verdict': 'pass', 'mechanical_failures': []}) for condition in ('control', 'skill')]
        with tempfile.TemporaryDirectory() as root:
            pilot.report(Path(root), results, 42)
            text = (Path(root) / 'report.md').read_text()
            self.assertIn('Case 8: excluded', text)
            self.assertIn('unavailable-subagent-API', text)

    def test_root_turn_context_excludes_child_sandbox(self):
        with tempfile.TemporaryDirectory() as root:
            home = Path(root)
            sessions = home / 'sessions'
            sessions.mkdir()
            for name, ident, sandbox in [('root', 'root-1', 'workspace-write'), ('child', 'child-1', 'read-only')]:
                records = [{'type': 'session_meta', 'payload': {'id': ident}}, {'type': 'turn_context', 'payload': {'model': 'm', 'sandbox_policy': {'type': sandbox}}}]
                (sessions / (name + '.jsonl')).write_text(''.join(json.dumps(r) + '\n' for r in records))
            contexts = pilot.session_contexts(home, 'root-1')
            self.assertEqual(len(contexts), 1)
            self.assertIsNone(pilot.validate_turn_contexts(contexts, 1))
            self.assertEqual(pilot.runtime_metadata(home, 'root-1')['runtime_reported_model'], 'm')
            self.assertIsNone(pilot.runtime_metadata(home, 'missing')['runtime_reported_model'])

    def test_failed_process_creation_is_infrastructure_error(self):
        event = {'type': 'item.completed', 'item': {'aggregated_output': 'Failed to create unified exec process: Permission denied'}}
        result = {'exit_code': 0, 'timeout': False, 'stdout': json.dumps(event) + '\n' + json.dumps({'type': 'turn.completed'}), 'stderr': ''}
        self.assertEqual(pilot.inspect_run(result), 'runtime could not launch shell commands')

    def test_regrade_uses_manifest_schedule_not_archived_attempts(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            (root / 'manifest.json').write_text(json.dumps({'schedule': [[9, 'skill', 1]]}))
            for name in ('case-09-skill-1', 'case-09-skill-1-attempt-1'):
                folder = root / name
                folder.mkdir()
                (folder / 'result.json').write_text(json.dumps({'case': 9, 'condition': 'skill', 'repeat': 1}))
            found = regrade.source_items(root, {9})
            self.assertEqual([p.name for p in found], ['case-09-skill-1'])

    def test_regrade_preserves_original_and_uses_current_evidence(self):
        grade = {'verdict': 'pass', 'reason': 'supported', 'evidence': ['turn1:1']}
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            source, output = root / 'source', root / 'out'
            source.mkdir()
            original = {'case': 8, 'condition': 'skill', 'repeat': 1, 'verdict': 'fail', 'mechanical_failures': [], 'infrastructure_error': None}
            (source / 'result.json').write_text(json.dumps(original))
            (source / 'blinded-evidence.json').write_text(json.dumps({'turn1:1': 'evidence'}))
            def fake_home(base):
                home = base / 'codex-home'
                home.mkdir()
                return home
            with mock.patch.object(pilot, 'isolated_home', side_effect=fake_home), mock.patch.object(pilot, 'grade', return_value=grade):
                result = regrade.regrade_item(source, output, 'test', 1)
            self.assertEqual(result['verdict'], 'inconclusive')
            self.assertEqual(result['attribution_verdict'], 'pass')
            self.assertEqual(result['source_verdict'], 'fail')
            self.assertEqual(json.loads((source / 'result.json').read_text()), original)
            self.assertTrue((output / 'test/source/result.json').exists())

    def test_subprocess_timeout_is_inconclusive(self):
        with mock.patch('subprocess.run', side_effect=subprocess.TimeoutExpired(['codex'], 1, output=b'partial')):
            result = pilot.run_command(['codex'], Path('/tmp'), {}, 1)
        self.assertTrue(result['timeout'])
        self.assertEqual(result['stdout'], 'partial')
        self.assertEqual(pilot.inspect_run(result), 'timeout')

    def test_fake_run_supports_clarification_and_blinded_evidence(self):
        captured = []
        commands = []
        def fake_home(base, skill=None):
            home = base / 'codex-home'
            home.mkdir()
            return home
        def fake_cli(args, cwd, env, timeout, input_text=None):
            commands.append(args)
            events = [{'type': 'thread.started', 'thread_id': 'session'}, {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'What outcome do you want?'}}, {'type': 'turn.completed'}]
            return {'exit_code': 0, 'timeout': False, 'stdout': ''.join(json.dumps(e) + '\n' for e in events), 'stderr': ''}
        def fake_grade(case, evidence, model, home, cwd, out, timeout, index):
            captured.append(evidence)
            return {'verdict': 'pass', 'reason': 'supported', 'evidence': ['turn1:2']}
        with tempfile.TemporaryDirectory() as root, mock.patch.object(pilot, 'isolated_home', side_effect=fake_home), mock.patch.object(pilot, 'skill_inventory', return_value=['dev-spec']), mock.patch.object(pilot, 'verify_skill_delivery', return_value=['dev-spec']), mock.patch.object(pilot, 'session_contexts', return_value=[{'sandbox_policy': {'type': 'workspace-write'}}] * 2), mock.patch.object(pilot, 'session_provenance', return_value={'children': [], 'collaboration_calls': []}), mock.patch.object(pilot, 'run_command', side_effect=fake_cli), mock.patch.object(pilot, 'grade', side_effect=fake_grade):
            result = pilot.run_case(9, 'skill', 1, Path(root), 1, 'gpt-6.1-sol', 'medium')
            self.assertEqual(result['requested_model'], 'gpt-6.1-sol')
            self.assertEqual(result['reasoning_effort'], 'medium')
            self.assertEqual(result['verdict'], 'pass')
            self.assertEqual(len(result['turns']), 2)
            self.assertIn('sandbox_mode=\"workspace-write\"', commands[1])
            self.assertEqual(len(captured), 2)
            self.assertIn('clarification', captured[0])
            self.assertNotIn('dev-spec', json.dumps(captured[0]))

    def test_fake_review_modification_fails(self):
        def fake_home(base, skill=None):
            home = base / 'codex-home'
            home.mkdir()
            return home
        def fake_cli(args, cwd, env, timeout, input_text=None):
            (cwd / 'extra.txt').write_text('unauthorized')
            return {'exit_code': 0, 'timeout': False, 'stdout': '{"type":"turn.completed"}\n', 'stderr': ''}
        grade = {'verdict': 'pass', 'reason': 'supported', 'evidence': ['turn1:1']}
        with tempfile.TemporaryDirectory() as root, mock.patch.object(pilot, 'isolated_home', side_effect=fake_home), mock.patch.object(pilot, 'skill_inventory', return_value=[]), mock.patch.object(pilot, 'verify_skill_delivery', return_value=[]), mock.patch.object(pilot, 'session_contexts', return_value=[{'sandbox_policy': {'type': 'workspace-write'}}]), mock.patch.object(pilot, 'session_provenance', return_value={'children': [], 'collaboration_calls': []}), mock.patch.object(pilot, 'run_command', side_effect=fake_cli), mock.patch.object(pilot, 'grade', return_value=grade):
            result = pilot.run_case(21, 'control', 1, Path(root), 1)
            self.assertEqual(result['verdict'], 'fail')
            self.assertIn('unauthorized edit', result['mechanical_failures'])


if __name__ == '__main__':
    unittest.main()
