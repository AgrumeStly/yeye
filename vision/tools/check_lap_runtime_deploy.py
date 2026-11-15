"""以假Session检查固定候选写入门槛及字节回读；不连接或写真实板卡。"""
import argparse
import base64
import json
from pathlib import Path

from canmv_runtime_deploy import deploy, CANDIDATE_HASH, CANDIDATE, BACKUP, CONTINUOUS_HASH, CONTINUOUS_CANDIDATE
from canmv_runtime_probe import TRACE_HASH, TRACE_CANDIDATE


class FakeSession:
    def __init__(self, *, running=False, wrong_current=False, boot=False, bad_readback=False):
        self.requests = []; self.writes = 0; self.running = running
        self.raw = b'unknown startup' if wrong_current else BACKUP.read_bytes()
        self.boot = boot; self.bad_readback = bad_readback
    def request(self, method, params=None, timeout=None):
        self.requests.append((method, params))
        if method == 'scriptRunning': return dict(running=self.running)
        if method == 'io.queryFileStat':
            exists = self.boot if params['path'] == '/sdcard/boot.py' else True
            return dict(exists=exists, type='file', size=4 if self.boot and params['path'].endswith('boot.py') else len(self.raw))
        if method == 'io.readFile':
            raw = b'boot' if params['path'].endswith('boot.py') else self.raw
            return dict(dataBase64=base64.b64encode(raw[params['offset']:params['offset']+params['size']]).decode())
        if method == 'io.writeFile':
            assert params['path'] == '/sdcard/main.py'
            self.writes += 1
            self.raw = b'corrupt' if self.bad_readback else base64.b64decode(params['dataBase64'])
            return dict(success=True)
        raise AssertionError('unexpected RPC ' + method)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    checks = []
    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))
        if not ok: raise AssertionError(name)
    folder = args.output / 'success'; folder.mkdir()
    session = FakeSession(); result = deploy(session, folder, CANDIDATE_HASH)
    check('only_one_fixed_main_write', session.writes == 1 and session.raw == CANDIDATE.read_bytes())
    check('exact_before_and_after_files', (folder/'before_main.py').read_bytes() == BACKUP.read_bytes() and (folder/'readback_main.py').read_bytes() == CANDIDATE.read_bytes())
    check('no_run_START_or_delete_RPC', {m for m, _ in session.requests} <= {'scriptRunning', 'io.queryFileStat', 'io.readFile', 'io.writeFile'})
    check('readback_and_unverified_cold_boot_distinct', result['exact_readback'] and not result['script_executed'] and not result['cold_boot_verified'])
    folder = args.output/'continuous_success'; folder.mkdir()
    session = FakeSession(); session.raw = CANDIDATE.read_bytes()
    result = deploy(session, folder, CONTINUOUS_HASH, 'continuous-v2')
    check('continuous_upgrade_exact_source_and_true_prior_backup', session.writes == 1 and session.raw == CONTINUOUS_CANDIDATE.read_bytes()
          and (folder/'before_main.py').read_bytes() == CANDIDATE.read_bytes())
    check('continuous_upgrade_never_runs_source', result['runtime_version'] == 'continuous-v2' and not result['script_executed'])
    folder = args.output/'trace_success'; folder.mkdir()
    session = FakeSession(); session.raw = CONTINUOUS_CANDIDATE.read_bytes()
    result = deploy(session, folder, TRACE_HASH, 'trace-v3')
    check('trace_exact_source_and_v2_backup', session.writes == 1 and session.raw == TRACE_CANDIDATE.read_bytes()
          and (folder/'before_main.py').read_bytes() == CONTINUOUS_CANDIDATE.read_bytes())
    check('trace_only_fixed_file_write_never_runs', result['runtime_version'] == 'trace-v3' and not result['script_executed'] and
          {m for m,_ in session.requests} <= {'scriptRunning','io.queryFileStat','io.readFile','io.writeFile'})
    for name, options, approval in (('trace_running',{'running':True},TRACE_HASH),
                                    ('trace_unknown',{'wrong_current':True},TRACE_HASH),
                                    ('trace_wrong_hash',{},CONTINUOUS_HASH)):
        folder=args.output/name; folder.mkdir(); session=FakeSession(**options)
        if not options: session.raw=CONTINUOUS_CANDIDATE.read_bytes()
        try:
            deploy(session,folder,approval,'trace-v3'); rejected=False
        except (ValueError,RuntimeError): rejected=True
        check(name+'_refused_before_write',rejected and session.writes==0)
    for name, settings, approved, expected_writes in (
        ('wrong_approval', {}, 'other', 0), ('running_script', {'running': True}, CANDIDATE_HASH, 0),
        ('unknown_main', {'wrong_current': True}, CANDIDATE_HASH, 0), ('unknown_boot', {'boot': True}, CANDIDATE_HASH, 0),
        ('bad_readback', {'bad_readback': True}, CANDIDATE_HASH, 1)):
        folder = args.output/name; folder.mkdir(); session = FakeSession(**settings)
        try:
            deploy(session, folder, approved); rejected = False
        except (ValueError, RuntimeError): rejected = True
        check(name+'_rejected_at_correct_stage', rejected and session.writes == expected_writes)
        if name == 'wrong_approval': check('wrong_approval_has_no_RPC', not session.requests)
        if name == 'unknown_main': check('unknown_main_evidence_saved', (folder/'before_main.py').read_bytes() == b'unknown startup')
    (args.output/'checks.json').write_text(json.dumps(dict(checks=checks, fake_session_only=True, physical_board_used=False), indent=2), encoding='utf-8')
    print(len(checks), 'deployment boundary checks PASS; fake Session only')


if __name__ == '__main__': main()
