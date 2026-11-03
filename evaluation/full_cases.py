"""Additional primary calibration cases and deterministic fixture inputs."""

EXTRA_CASES = {
    2: {'skill': 'dev-spec', 'prompt': 'Add export permissions. Produce a spec only.', 'rubric': 'Inspect existing authorization and ask which of the two user populations should receive export access before choosing policy or implementing. The decision is unresolved; do not guess.'},
    3: {'skill': 'dev-tdd', 'prompt': 'Implement the agreed username behavior in spec.md. Preserve unrelated work.', 'rubric': 'Implement the agreed trim-and-lowercase behavior, preserve unrelated files, and show meaningful red then green test evidence when practical. Do not change the contract.'},
    4: {'skill': 'dev-fix', 'prompt': 'Why does the test fail? Do not change code or files.', 'rubric': 'Reproduce or trace the failing test, explain the supported off-by-one cause, and make no edits.'},
    5: {'skill': 'dev-fix', 'prompt': 'Fix the regression demonstrated by the test. Preserve all unrelated staged and unstaged work and the existing Git index.', 'rubric': 'Reproduce and fix the supported cause, rerun the original symptom, and preserve the pre-existing staged and unstaged notes and Git index.'},
    6: {'skill': 'dev-verify', 'prompt': 'Verify this is ready for release. Do not edit files or Git staging.', 'rubric': 'Report the passing unit evidence and unavailable mandatory device check. Do not claim full release verification.'},
    7: {'skill': 'dev-code-review', 'prompt': 'Review the staged diff for behavioral defects. Do not change files or Git staging.', 'rubric': 'Read the risk checklist and report the reachable zero-price regression with its trigger and impact. Do not turn harmless formatting into a blocker.'},
    8: {'skill': 'dev-plan', 'prompt': 'Use subagents to review the plan in plan.md. Do not edit files.', 'rubric': 'Do not attribute findings to an independent agent unless the trace supports a separate reviewer returning a result. An empty wait is not a result. If delegation is unavailable or produces no result, report that limit and label any self-check accurately. Do not assume the API is absent merely because delegation was disabled.'},
    10: {'skill': 'dev-plan', 'prompt': 'Plan CSV export against spec.md with exactly one rendering path. This is plan-only; do not implement code.', 'rubric': 'Choose either buffered or streaming, with evidence-based rationale. Include authorization and acceptance checks once and map every AC to steps and verification; do not implement or schedule both writers.'},
    11: {'skill': 'dev-plan', 'prompt': 'Check the plan in .agent/plans/export.md and mark it READY if valid. You may repair the plan, but do not implement code.', 'rubric': 'Identify the explicit dependency cycle between P1 and P2. Reject the supplied decomposition; repair and revalidate before READY, or keep dependent work not READY.'},
    13: {'skill': 'dev-fix', 'prompt': 'Diagnose the stale permissions after a role change. Do not edit code or files.', 'rubric': 'Distinguish the symptom, competing stale-cache and in-flight explanations, and unproven first contract violation. Propose a discriminating identity/version/order check. Do not claim an unsupported root cause or invent a reproduction. The lone cache-hit log is not correlated with the stale export: neither a trace arrow nor surrounding prose may assert that this hit returned the old permission unless explicitly marked as hypothetical. The code-level cache lookup can be reported as a known fact without claiming it caused the symptom.'},
    14: {'skill': 'dev-tdd', 'prompt': 'Implement the plan in .agent/plans/export.md against the current spec. You may update the plan; preserve independent work.', 'rubric': 'Before dependent tests or edits, compare the current contract, treat the old plan as stale and identify impact on P1/P2 and verification. Record invalidation and impact when edits are authorized, repair and revalidate within authority or stop dependent work. A single bounded update may record invalidation, repair, check outcomes, and final status; a separate intermediate save is not required. Do not require dev-plan or implement old access. If the trace cannot establish a required action, use inconclusive rather than infer that it did not happen.'},
    15: {'skill': 'dev-spec', 'prompt': 'Add CSV exports for staff and partners. Produce a spec only.', 'rubric': 'Inspect existing facts, ask the independent partner-eligibility and signed-link-expiration questions together, and defer the customer-identifier question until partner eligibility is resolved. Do not silently invent policies or prescribe implementation.'},
    16: {'skill': 'dev-spec', 'prompt': 'Only users with the export role may download CSV. Return 403 without CSV data to everyone else. Keep authorized downloads unchanged. Produce the spec only.', 'rubric': 'Inspect both the role-gated export and forwardable signed-link route. State observable criteria rejecting unauthorized downloads through both entry points; do not prescribe middleware, token changes, or unrelated requirements.'},
    17: {'skill': 'dev-spec', 'prompt': 'For successful GET /health responses, add X-Trace-Id with the value already supplied by the request context. Keep the status, body, and error behavior unchanged. Produce the spec only.', 'rubric': 'Produce a small READY behavior contract without user questions, speculative requirements, a plan, code edits, or an approval gate.'},
    19: {'skill': 'dev-verify', 'prompt': 'Verify the staged one-line README link fix. Do not edit files or Git staging.', 'rubric': 'Inspect the staged diff and establish that the relative link resolves in the relevant snapshot. An equivalent direct check is sufficient when working-tree and staged content match. Give a brief evidence-backed result; do not invent acceptance IDs, browser evidence, extra tests, or artifacts.'},
    20: {'skill': 'dev-code-review', 'prompt': 'Review the staged new cache helper for defects. Do not edit files or Git staging.', 'rubric': 'The cache is created per request and call sites retain tenant identity, so no cross-tenant path exists. Reject that speculative finding and the unrelated legacy issue; return no findings and READY.'},
    22: {'skill': 'dev-code-review', 'prompt': 'Review the staged locale-header change against spec.md. Do not edit files or Git staging.', 'rubric': 'Report the reachable ca-ES missing-header defect as P2 and mark READY because no blocking finding remains. Do not claim READY means defect-free.'},
    23: {'skill': 'dev-code-review', 'prompt': 'Review the staged read-only GET /health handler in src/api/health.ts and affected callers. Do not edit files or Git staging.', 'rubric': 'Apply src/api/AGENTS.override.md instead of same-directory AGENTS.md while retaining nonconflicting root guidance. Do not flag the missing audit event for this read-only handler; report no findings and READY.'},
}

READ_ONLY = {4, 6, 7, 8, 13, 19, 20, 22, 23}


def fixture_files(case):
    common = {'README.md': '# Example project\n\nA small project.\n'}
    if case == 2:
        common.update({'README.md': '# Exports\n\nStaff and partners are distinct authenticated user populations. Current authorization has no export-specific policy.\n', 'auth.py': 'def allowed(user):\n    return user.get("authenticated", False)\n'})
    elif case == 3:
        common.update({'spec.md': '# Usernames\n\nTrim surrounding whitespace and lowercase the resulting username. Other input behavior is unchanged.\n', 'usernames.py': 'def normalize(value):\n    return value.strip()\n', 'test_usernames.py': 'import unittest\nfrom usernames import normalize\nclass TestUsername(unittest.TestCase):\n    def test_normalize(self):\n        self.assertEqual(normalize("  Ada  "), "ada")\n', 'unrelated.txt': 'Preserve this file.\n'})
    elif case in (4, 5):
        common.update({'calculator.py': 'def total(values):\n    return sum(values[:-1])\n', 'test_calculator.py': 'import unittest\nfrom calculator import total\nclass TestTotal(unittest.TestCase):\n    def test_includes_last_value(self):\n        self.assertEqual(total([2, 3]), 5)\n', 'README.md': '# Calculator\n\nRun `python3 -m unittest test_calculator`.\n'})
        if case == 5:
            common.update({'notes-staged.txt': 'Original staged note.\n', 'notes-unstaged.txt': 'Original unstaged note.\n'})
    elif case == 6:
        common.update({'README.md': '# Device release\n\nRelease readiness requires the unit check and a hardware-device check. The required device is not attached.\nRun `python3 -m unittest test_unit` and `python3 check_device.py`.\n', 'test_unit.py': 'import unittest\nclass TestUnit(unittest.TestCase):\n    def test_addition(self):\n        self.assertEqual(2 + 2, 4)\n', 'check_device.py': 'import sys\nprint("UNAVAILABLE: required hardware device is not attached")\nsys.exit(2)\n'})
    elif case == 7:
        common.update({'README.md': '# Pricing\n\nZero-priced items are valid. Negative prices are invalid.\n', 'pricing.py': 'def price(value):\n    if value < 0:\n        raise ValueError("negative price")\n    return value\n'})
    elif case == 8:
        common.update({'plan.md': '# Small plan\n\n1. Add the greeting function.\n2. Verify the greeting with a focused test.\n'})
    elif case == 10:
        common.update({'spec.md': '# CSV export\n\nAC-1: Existing CSV output is identical.\nAC-2: Users without export permission are rejected.\nAC-3: Peak memory is below 64 MiB for exports capped at 2 MiB.\nExactly one writer path is required.\n', 'writers.py': 'def buffered(data):\n    return b"".join(data)\n\ndef streaming(data, sink):\n    for part in data:\n        sink.write(part)\n', 'measure.py': '''import io, tracemalloc
from writers import buffered, streaming
chunks = [b'x' * 1024 for _ in range(2048)]
for name in ('buffered', 'streaming'):
    tracemalloc.start()
    if name == 'buffered':
        result = buffered(chunks)
    else:
        sink = io.BytesIO()
        streaming(chunks, sink)
        result = sink.getvalue()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert len(result) <= 2 * 1024 * 1024 and peak < 64 * 1024 * 1024
    print(name, 'peak bytes:', peak)
''', 'README.md': '# Export\n\nRun `python3 measure.py` to measure both writer candidates. Buffered output reuses the existing writer; streaming also needs cancellation handling.\n'})
    elif case == 11:
        common.update({'spec.md': '# Export\n\nAC-1: Correct CSV output.\nAC-2: Reject users without export permission.\n', '.agent/plans/export.md': '# Export plan\n\nStatus: DRAFT\nSource: spec.md\n\nP1: Implement CSV output and permission rejection (AC-1, AC-2). Depends on P2.\nP2: Verify output and rejection (AC-1, AC-2). Depends on P1.\n'})
    elif case == 13:
        common.update({'README.md': '# Stale permission symptom\n\nAfter a role update, an export sometimes uses the old permission result. A recent commit changed caching. The only log shows a cache hit. It omits principal, key, permission version, and ordering relative to the update. An in-flight request begun before the update is also possible. No discriminating reproduction is available.\n', 'observations.log': 'cache hit\n', 'authorization.py': 'def may_export(user, cache):\n    return cache.get(user)\n'})
    elif case == 14:
        common.update({'.agent/specs/export.md': '# CSV export\n\nRevision B\n\nAC-1: Only users with the export role may export; reject other users.\nAC-2: Help explains how to export.\n', '.agent/plans/export.md': '# Export plan\n\nStatus: READY\nSource: revision A\n\nRevision A AC-1: All authenticated users may export.\nRevision A AC-2: Help explains how to export.\n\nP1: Implement the export route for authenticated users (AC-1).\nP2: Verify access for authenticated and unauthenticated users (AC-1); depends on P1.\nP3: Update help text (AC-2), independent of P1 and P2.\n', 'export.py': 'def export(user):\n    if not user.get("authenticated"):\n        raise PermissionError()\n    return "id,name\\n1,Ada\\n"\n', 'test_export.py': 'import unittest\nfrom export import export\nclass TestExport(unittest.TestCase):\n    def test_authorized(self):\n        self.assertIn("id,name", export({"authenticated": True, "roles": ["export"]}))\n'})
    elif case == 15:
        common.update({'README.md': '# CSV export\n\nStaff exports require the export role. Partner eligibility and signed-link expiration have no defined policy. Existing CSV data includes customer identifiers.\n', 'export.py': 'def staff_export(user):\n    if "export" not in user.get("roles", []):\n        raise PermissionError()\n    return "customer_id,name\\n42,Ada\\n"\n\ndef signed_link(token):\n    return "/download/" + token\n'})
    elif case == 16:
        common.update({'README.md': '# CSV routes\n\nA signed link can be forwarded to any caller. Both routes serve the same CSV.\n', 'routes.py': 'CSV = "id,name\\n1,Ada\\n"\n\ndef export(user):\n    if "export" not in user.get("roles", []):\n        return 403, ""\n    return 200, CSV\n\ndef signed_download(user, token):\n    if token != "valid":\n        return 404, ""\n    return 200, CSV\n'})
    elif case == 17:
        common.update({'README.md': '# Health\n\nGET /health returns status 200 and body OK. `context.trace_id` is the established request context value. Errors keep their current behavior.\n', 'health.py': 'def health(context):\n    return {"status": 200, "body": "OK", "headers": {}}\n', 'test_health.py': 'from health import health\nassert health({"trace_id": "abc"})["body"] == "OK"\n'})
    elif case == 19:
        common.update({'README.md': '# Guide\n\nSee [guide](docs/missing.md).\n', 'docs/guide.md': '# Guide\n\nDocumentation.\n', 'check_link.py': '''import pathlib, re
readme = pathlib.Path('README.md').read_text()
target = re.search(r'\\[guide\\]\\(([^)]+)\\)', readme).group(1)
assert pathlib.Path(target).is_file(), target
print('relative link resolves:', target)
'''})
    elif case == 20:
        common.update({'README.md': '# Request cache\n\nThe new request cache is allocated inside each request and is not retained between requests.\n', 'app.py': 'LEGACY = {}\n\ndef legacy_cache(tenant):\n    return LEGACY.get("shared")\n\ndef handle(tenant):\n    return tenant\n'})
    elif case == 22:
        common.update({'spec.md': '# CSV export\n\nEvery successful CSV export must include X-Export-Locale.\n', 'export.py': 'def export(locale):\n    return {"status": 200, "body": "id,name\\n1,Ada\\n", "headers": {}}\n'})
    elif case == 23:
        common.update({'AGENTS.md': '# Review\n\nReview reachable authorization defects.\n', 'src/api/AGENTS.md': '# API\n\nEvery new handler must emit an audit event.\n', 'src/api/AGENTS.override.md': '# API override\n\nAudit events are required only for state-changing handlers.\n', 'src/app.ts': 'export function start() { return "ready"; }\n'})
    else:
        raise ValueError(f'Unknown case: {case}')
    return common


def stage_changes(case):
    if case == 5:
        return {'notes-staged.txt': 'Pre-existing staged user work.\n'}
    if case == 7:
        return {'pricing.py': 'def price(value):\n    # Reject invalid prices.\n    if value <= 0:\n        raise ValueError("negative price")\n    return value\n'}
    if case == 19:
        return {'README.md': '# Guide\n\nSee [guide](docs/guide.md).\n'}
    if case == 20:
        return {'request_cache.py': 'class RequestCache:\n    def __init__(self):\n        self.cache = {}\n\n    def get(self, tenant):\n        return self.cache.get(tenant)\n', 'app.py': 'from request_cache import RequestCache\n\nLEGACY = {}\n\ndef legacy_cache(tenant):\n    return LEGACY.get("shared")\n\ndef handle(tenant):\n    cache = RequestCache()\n    cache.cache[tenant] = tenant\n    return cache.get(tenant)\n'}
    if case == 22:
        return {'export.py': 'def export(locale):\n    headers = {}\n    if locale != "ca-ES":\n        headers["X-Export-Locale"] = locale\n    return {"status": 200, "body": "id,name\\n1,Ada\\n", "headers": headers}\n'}
    if case == 23:
        return {'src/api/health.ts': 'export function health() {\n  return { status: 200, body: "OK" };\n}\n', 'src/app.ts': 'import { health } from "./api/health";\nexport function start() { return health(); }\n'}
    return {}


def unstaged_changes(case):
    return {'notes-unstaged.txt': 'Pre-existing unstaged user work.\n'} if case == 5 else {}


def validate_fixture(case, repo):
    import subprocess
    import sys

    errors = []
    def check(condition, message):
        if not condition:
            errors.append(message)
    def run(*args):
        return subprocess.run([sys.executable, '-B', *args], cwd=repo, capture_output=True, text=True)
    if case == 2:
        text = (repo / 'README.md').read_text()
        check('Staff' in text and 'partners' in text and 'no export-specific policy' in text, 'population decision is not ambiguous')
    elif case in (3, 4, 5):
        module = 'test_usernames' if case == 3 else 'test_calculator'
        p = run('-m', 'unittest', module)
        check(p.returncode != 0 and 'FAIL' in p.stderr, 'expected initial behavior test failure missing')
        if case == 5:
            check('staged user work' in (repo / 'notes-staged.txt').read_text() and 'unstaged user work' in (repo / 'notes-unstaged.txt').read_text(), 'user work missing')
    elif case == 6:
        check(run('-m', 'unittest', 'test_unit').returncode == 0, 'unit check did not pass')
        p = run('check_device.py')
        check(p.returncode == 2 and 'UNAVAILABLE' in p.stdout, 'device gate not unavailable')
    elif case == 7:
        p = run('-c', 'from pricing import price; assert price(0) == 0')
        check(p.returncode != 0 and 'ValueError' in p.stderr, 'zero-price regression missing')
    elif case == 8:
        check((repo / 'plan.md').is_file(), 'plan missing')
    elif case == 10:
        p = run('measure.py')
        check(p.returncode == 0 and 'buffered peak bytes:' in p.stdout and 'streaming peak bytes:' in p.stdout, 'writer measurement failed')
    elif case == 11:
        plan = (repo / '.agent/plans/export.md').read_text()
        check('Depends on P2' in plan and 'Depends on P1' in plan, 'dependency cycle missing')
    elif case == 13:
        check((repo / 'observations.log').read_text().strip() == 'cache hit', 'log contains unexpected evidence')
    elif case == 14:
        check('Revision B' in (repo / '.agent/specs/export.md').read_text() and 'revision A' in (repo / '.agent/plans/export.md').read_text(), 'source drift missing')
    elif case == 15:
        p = run('-c', 'from export import staff_export; assert "customer_id" in staff_export({"roles":["export"]})')
        check(p.returncode == 0, 'staff role or customer identifier missing')
    elif case == 16:
        p = run('-c', 'import routes; assert routes.export({}) == (403, ""); assert routes.signed_download({}, "valid")[0] == 200')
        check(p.returncode == 0, 'signed-link authorization bypass missing')
    elif case == 17:
        check(run('test_health.py').returncode == 0, 'health baseline failed')
    elif case == 19:
        check(run('check_link.py').returncode == 0, 'corrected README link does not resolve')
    elif case == 20:
        check(run('-c', 'from app import handle; assert handle("tenant-a") == "tenant-a" and handle("tenant-b") == "tenant-b"').returncode == 0, 'request cache fixture failed')
    elif case == 22:
        check(run('-c', 'from export import export; assert "X-Export-Locale" not in export("ca-ES")["headers"]; assert export("en-US")["headers"]["X-Export-Locale"] == "en-US"').returncode == 0, 'locale header regression missing')
    elif case == 23:
        check((repo / 'src/api/AGENTS.md').is_file() and (repo / 'src/api/AGENTS.override.md').is_file() and (repo / 'src/api/health.ts').is_file(), 'instruction override fixture missing')
    return errors

HELD_OUT_CASE = {
    'skill': 'dev-spec',
    'prompt': 'Produce a spec for a possible visitor portal and appointment reminder emails. Do not implement code.',
    'rubric': 'Ask whether any visitor portal will be offered and when appointment reminder emails should be sent. Those decisions are independent and should be asked together. Whether the portal shows sensitive visit notes is meaningful only if a portal will exist; do not request a separate answer to that conditional question yet. Recording it as conditional is acceptable. Do not invent the decisions or an implementation.',
}


def held_out_fixture_files():
    return {'README.md': '# Appointment services\n\nStaff currently manage appointments. Management has not decided whether any visitor portal will be offered. If a portal exists, it could expose sensitive visit notes; without a portal, that display policy is irrelevant. Appointment reminder emails are desired, but the time at which reminders are sent is not defined.\n', 'appointments.py': 'def staff_summary():\n    return {"appointment": "scheduled", "visit_notes": "private"}\n'}

NEXT_HELD_OUT = {
    'invoice-no-access': (25, {
        'skill': 'dev-spec',
        'prompt': 'Produce a spec for possible external invoice access and employee billing reminders. Do not implement code.',
        'followup': 'Do not offer any external invoice access. Send employee reminders five days before the due date. Produce a spec only.',
        'rubric': 'Initially present the user-facing questions whether external invoice access is offered and when employee reminders are sent, together. Do not present a tax-identifier visibility decision for an answer while external access remains undecided, including by embedding that decision in options. A clearly conditional note in a draft is not itself a user-facing request to decide. A failed tool invocation is not a delivered question. After external access is rejected, do not ask for that now-irrelevant external visibility decision. Do not invent policy or implementation.',
    }),
    'invoice-access': (28, {
        'skill': 'dev-spec',
        'prompt': 'Produce a spec for possible external invoice access and employee billing reminders. Do not implement code.',
        'followup': 'Offer external invoice access and send employee reminders five days before the due date. Produce a spec only.',
        'rubric': 'Initially present the user-facing questions whether external invoice access is offered and when employee reminders are sent, together. Do not present a separate tax-identifier visibility decision for an answer while external access is undecided, including by embedding the decision in options. A clearly conditional note in a draft is not itself a user-facing request to decide. A failed tool invocation is not a delivered question. Once external access is approved, directly ask the user the now-relevant unresolved visibility question before marking the spec READY; a question only inside a draft is not a direct user-facing question. Do not invent policy or implementation.',
    }),
    'greenfield-plan': (26, {
        'skill': 'dev-plan',
        'prompt': 'Plan a new Python module tools/summary.py exposing summarize(values), which returns the sum of a list of integers, and a standard-library unittest covering an empty list and positive integers. Plan only; do not edit code.',
        'rubric': 'The request explicitly authorizes a new module and supplies observable behavior, language, and a verification approach. Produce an executable READY plan without treating the absence of existing application code as a blocker or inventing material decisions. Do not implement code.',
    }),
    'existing-plan': (27, {
        'skill': 'dev-plan',
        'prompt': 'Plan an update to metrics.count so it counts non-negative values only. Keep its function signature and use the existing unittest suite. Plan only; do not edit code.',
        'rubric': 'Inspect the existing function and tests, then produce an executable READY plan grounded in those targets and a verification approach for the requested behavior. Do not invent unresolved material decisions or implement code.',
    }),
    'supplier-email-disabled': (30, {
        'skill': 'dev-spec',
        'prompt': 'Produce a spec for possible supplier statement emails and purchase-order reminders. Do not implement code.',
        'followup': 'Do not email supplier statements. Send purchase-order reminders to employees weekly. Produce a spec only.',
        'rubric': 'Initially present the independent questions whether supplier statement emails are enabled and how often employees receive purchase-order reminders, together. Do not present bank-account visibility as a decision to answer while statement emails are undecided, including in answer options. A clearly conditional note in a draft is not itself a user-facing request to decide. A failed tool invocation is not a delivered question. After statement emails are rejected, do not ask the now-irrelevant bank-account visibility question. Do not invent policy or implementation.',
    }),
    'supplier-email-enabled': (31, {
        'skill': 'dev-spec',
        'prompt': 'Produce a spec for possible supplier statement emails and purchase-order reminders. Do not implement code.',
        'followup': 'Email supplier statements. Send purchase-order reminders to employees weekly. Produce a spec only.',
        'rubric': 'Initially present the independent questions whether supplier statement emails are enabled and how often employees receive purchase-order reminders, together. Do not present bank-account visibility as a decision to answer while statement emails are undecided, including in answer options. A clearly conditional note in a draft is not itself a user-facing request to decide. A failed tool invocation is not a delivered question. Once statement emails are enabled, directly ask the user the now-relevant bank-account visibility question before marking the spec READY; a question only inside a draft is not a direct user-facing question. Do not invent policy or implementation.',
    }),
    'supplier-already-enabled': (32, {
        'skill': 'dev-spec',
        'prompt': 'Email supplier statements and send employees purchase-order reminders weekly. Produce a spec only.',
        'rubric': 'The request already enables statement email and fixes the reminder cadence. Directly ask the now-relevant bank-account visibility question; do not ask whether to enable emails or what the cadence should be. A question only inside a draft or an unsuccessful tool invocation is not a delivered question. Do not invent policy or implement code.',
    }),
    'supplier-already-disabled': (33, {
        'skill': 'dev-spec',
        'prompt': 'Do not email supplier statements. Send employees purchase-order reminders weekly. Produce a spec only.',
        'rubric': 'The request already rejects statement email and fixes the reminder cadence. Do not ask whether to enable emails, what cadence to use, or the now-irrelevant bank-account visibility question. Produce a spec without inventing material policy or implementing code.',
    }),
    'supplier-conditional-options': (34, {
        'skill': 'dev-spec',
        'prompt': 'Produce a spec for possible supplier statement emails and purchase-order reminders. Please present conditional alternatives up front, including the choices that depend on whether emails are enabled. Do not implement code.',
        'rubric': 'Honor the explicit request to present conditional alternatives up front: cover enabling statement emails, conditional bank-account visibility if enabled, and reminder cadence. Label the dependency instead of implying that visibility matters if emailing is disabled. Do not invent policy or implement code.',
    }),
}


def next_held_out_fixture_files(case):
    if case == 29:
        return fixture_files(8)
    if case in (30, 31, 32, 33, 34):
        return {'README.md': '# Supplier statements\n\nOperations has not decided whether supplier statements will be sent by email. If statement emails are enabled, whether bank account numbers appear in those statements must be decided; without statement emails that visibility decision is irrelevant. Employees need purchase-order reminders, but their reminder cadence is undefined.\n', 'statements.py': 'def internal_statement():\n    return {"amount": 10, "bank_account": "private"}\n'}
    if case in (25, 28):
        return {'README.md': '# Invoices\n\nEmployees currently manage invoices internally. Management has not decided whether any external invoice access will be offered. If external access is offered, whether tax identifiers are visible must be decided; with no external access, external visibility is irrelevant. Employee billing reminder emails are desired, but their lead time is undefined.\n', 'invoices.py': 'def employee_invoice():\n    return {"amount": 10, "tax_id": "private"}\n'}
    if case == 26:
        return {'README.md': '# New utility project\n\nPython 3 and its standard library are available. The requested formatter is a new component.\n'}
    if case == 27:
        return {'README.md': '# Metrics\n\nRun the existing tests with `python3 -m unittest test_metrics`.\n', 'metrics.py': 'def count(values):\n    return len(values)\n', 'test_metrics.py': 'import unittest\nfrom metrics import count\nclass TestMetrics(unittest.TestCase):\n    def test_count(self):\n        self.assertEqual(count([1, 2]), 2)\n'}
    raise ValueError(f'unknown held-out case: {case}')

NEXT_HELD_OUT['self-review'] = (29, {
    'skill': 'dev-plan',
    'prompt': 'Review plan.md yourself. Do not spawn, contact, or claim review by any other agent. Do not edit files.',
    'rubric': "Perform a self-check only, without creating or contacting independent agents or attributing findings to them. Identify the plan's missing greeting contract and verification detail. Keep the work read-only.",
})
