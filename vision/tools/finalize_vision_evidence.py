"""保存本轮最终保护核验、环境／SDK来源、人工下一步样例和交付清单。"""

import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import cv2
import numpy as np

from review_recovery_inputs import ROOT,digest,save


def run():
    """只读原件与Git状态，写入本轮新证据；不提交、不触及任何板卡。"""
    output=Path('testing/2026-11-08_vision_board_prep')
    cache=Path('C:/Users/Agrum/.kendryte')
    examples=cache/'k230_canmv_examples/7b5a27e82b89a05b74ce1ece45504d18ba48f3ce95bf31d79791617e9c3b6aa6'
    stubs=cache/'k230_canmv_stubs/f6ca68a0ed02f8d29d27bcf9681581e9f71209bb'
    references=[examples/'examples/03-Machine/uart1.py',examples/'examples/08-Codes/find_datamatrices.py',
                examples/'examples/22-Others/read_image_for_display.py',stubs/'media/sensor.pyi',
                stubs/'machine.pyi',stubs/'image.pyi']
    context=output/'api_context';context.mkdir(exist_ok=True)
    save(context/'manifest.json',dict(references={str(p):digest(p) for p in references},
          cached_read_only=True,board_tools_called=False,
          examples_revision=examples.name,stubs_revision=stubs.name,
          actual_board_firmware='Only prior recorded K230D-v1.8-0; not queried this turn'))
    # 只摘录所需API原文并保留源哈希，不把缓存资源版本当实际固件验收。
    extracts={}
    for path in references:
        text=path.read_text(encoding='utf-8')
        if path.suffix=='.py':extracts[str(path)]=text
        else:
            lines=text.splitlines();selected=[]
            for i,line in enumerate(lines):
                if any(key in line for key in ('def bytearray','def get_pixel','def to_grayscale','def snapshot',
                     'def set_framesize','def set_pixformat','def __init__','def width','def height','def format',
                     'class UART:','def write(','def deinit(','def set_function')):
                    selected.extend(lines[i:i+3])
            extracts[str(path)]='\n'.join(selected)
    save(context/'api_extracts.json',extracts)
    probes=json.loads((output/'release/bp1_frames.json').read_text(encoding='utf-8'))
    spec={};exec(compile(Path('vision/src/observer_bench_canmv.py').read_text(encoding='utf-8'),
                        'observer_bench_canmv.py','exec'),spec)
    sample=[r for r in probes if r['session']=='push_full_lap_0001' and r['frame'] in spec['SD_FRAME_IDS']]
    save(output/'sd_bench_expected.json',dict(samples=sample,
         note='PC JPEG decode diagnostics only; board decoder/API/timing still pending. source hashes identify originals, not raw-buffer hashes.'))
    before=json.loads((ROOT/'protected_before.json').read_text(encoding='utf-8'))
    changes=[p for p,h in before.items() if digest(Path(p))!=h]
    prior=json.loads(Path('testing/2026-11-08_vision_curve_c1/protected_hashes.json').read_text(encoding='utf-8'))
    prior_changes=[p for p,h in prior.items() if digest(Path(p))!=h]
    control=json.loads((output/'release/control_before.json').read_text(encoding='utf-8'))
    control_changes=[p for p,h in control.items() if digest(Path(p))!=h]
    source_snapshot=Path('testing/2026-11-08_vision_recovery_c2/replay_accepted/source_snapshot')
    candidate_snapshot_ok=all(digest(Path('vision/src')/name)==digest(source_snapshot/name)
                              for name in ('offline_boundary.py','offline_curve.py','offline_recovery.py'))
    finish_snapshot_ok=digest(Path('vision/src/offline_finish.py'))==digest(Path('testing/2026-11-08_vision_finish_f1/release/source_snapshot/offline_finish.py'))
    board_manifest=json.loads((output/'release/board_bundle/manifest.json').read_text(encoding='utf-8'))
    board_sources_ok=all(digest(Path(p))==h for p,h in board_manifest['sources'].items())
    assert not changes and not prior_changes and not control_changes and candidate_snapshot_ok and finish_snapshot_ok and board_sources_ok
    new_sources=[Path(p) for p in ['vision/src/offline_recovery.py','vision/src/offline_finish.py',
        'vision/src/board_observer_core.py','vision/src/vision_protocol.py','vision/src/observer_bench_canmv.py']]
    new_tools=[p for p in Path('vision/tools').glob('*.py') if p.as_posix() not in before]
    for path in new_sources+new_tools:ast.parse(path.read_text(encoding='utf-8'))
    status=subprocess.check_output(['git','status','--short'],text=True,encoding='utf-8')
    initial=json.loads((ROOT/'workspace_before.json').read_text(encoding='utf-8'))['status']
    missing_initial=sorted(set(initial.splitlines())-set(status.splitlines()))
    assert not missing_initial
    save(output/'final_protection.json',dict(passed=True,protected_unchanged=len(before),control_tracked_unchanged=len(control),
          prior_C1_protected_unchanged=len(prior),prior_C1_changed=prior_changes,
          frozen_build_parameters_sha256=digest(Path('vision/build/offline_v02_r1/parameters.json')),
          changed_originals=changes,changed_control=control_changes,
          source_snapshot_matches=dict(R1_C1_C2=candidate_snapshot_ok,F1=finish_snapshot_ok,BP1_protocol_entry=board_sources_ok),
          code_hashes={p.as_posix():digest(p) for p in new_sources+new_tools},
          python=sys.version,opencv=cv2.__version__,numpy=np.__version__,
          cwd=str(Path.cwd()),branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip(),
          head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
          status=status,initial_git_entries_preserved=len(set(initial.splitlines())),missing_initial_git_entries=missing_initial,
          physical_actions='none; no board connection, camera, capture permission, main.py, UART, motors or STM32 build',
          uploads=False,commits=False,global_summary_updated=False))
    print(json.dumps(dict(protected=len(before),control=len(control),source_snapshots=True,new_python_syntax=len(new_sources+new_tools))))


if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    run()
