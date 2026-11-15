"""T2最终交付保护与实际视频截图；只读原件，派生证据新建且拒绝覆盖。"""
import csv
import hashlib
import json
from pathlib import Path
import subprocess

import cv2


def sha(path):
    """计算文件字节哈希，避免仅依赖未跟踪文件的Git状态。"""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    """核对代码、手工审核页、基线保护、Git现场和真正MP4解码图像。"""
    root=Path(__file__).resolve().parent;output=root/'delivery_protection.json'
    assert not output.exists()
    audit=json.loads((root/'delivery_audit/delivery_checks.json').read_text(encoding='utf-8'))
    assert audit['passed']
    hashes=json.loads((root/'source_hashes.json').read_text(encoding='utf-8'))
    assert all(sha(p)==h for p,h in hashes.items())
    manual=json.loads((root/'manual_observations.json').read_text(encoding='utf-8'))
    assert manual['all_listed_pages_visually_reviewed']
    assert all(sha(root/'delivery_video'/name)==h for name,h in manual['page_sha256'].items())
    reviewed=list(csv.DictReader((root/'manual_review.csv').open(encoding='utf-8-sig')))
    assert len(reviewed)==388
    records=[json.loads(s) for s in (root/'delivery/frames.jsonl').read_text(encoding='utf-8').splitlines()]
    full=[r for r in records if r['session']=='push_full_lap_0001'];assert len(full)==732
    reviewed_frames={int(r['frame']) for r in reviewed}
    assert all(r['frame_id'] in reviewed_frames for r in full
          if not r['recovery_observation']['pair_samples'] and r['temporal_route']['state']!='map_prior_only')
    branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip()
    head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    status=subprocess.check_output(['git','status','--short'],text=True,encoding='utf-8')
    assert branch=='codex/current-version-20261025' and head=='a0733a8685db4c2b497539303bfe87fe1c1ebfe5'
    initial=json.loads(Path('testing/2026-11-08_vision_recovery_c2/workspace_before.json').read_text(encoding='utf-8'))['status'].splitlines()
    missing=sorted(set(initial)-set(status.splitlines()));assert not missing
    old_video=Path('testing/2026-11-08_vision_prediction_p1/preview_release/two_lap_predicted_boundaries_centerline.mp4')
    assert sha(old_video)=='459d89a9dfb6bac9f2e56d979675c3884bc9565cd7bdad6169e8f2f1259e0349'
    video=root/'delivery_video/two_lap_temporal_recommended_route.mp4'
    metadata=json.loads((root/'delivery_video/video_validation.json').read_text(encoding='utf-8'))
    assert sha(video)==metadata['sha256'] and metadata['decoded_frames']==1798
    frames=[];cap=cv2.VideoCapture(str(video));assert cap.isOpened()
    for ms in [14000,86500,120600]:
        cap.set(cv2.CAP_PROP_POS_MSEC,ms);ok,image=cap.read();assert ok and image.shape==(900,1600,3)
        path=root/'delivery_video'/f'actual_mp4_{ms:06d}ms.jpg';assert not path.exists()
        assert cv2.imwrite(str(path),image);frames.append(dict(ms=ms,file=path.name,sha256=sha(path)))
    cap.release()
    result=dict(passed=True,source_files_match=len(hashes),reviewed_frames=388,reviewed_pages=33,
        formal_regression_frames=len(records),all_source_video_frames=732,
        prior_P1_video_unchanged=True,protected=audit['protected'],
        original_git_entries_preserved=len(initial),missing_initial_entries=missing,
        cwd=str(Path.cwd()),branch=branch,head=head,status=status,
        video_sha256=metadata['sha256'],actual_mp4_stills=frames,
        verification_script_sha256=sha(__file__),
        physical_actions=False,uploads=False,commits=False,global_summary_updated=False)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['passed','source_files_match','reviewed_frames','reviewed_pages','original_git_entries_preserved','video_sha256']},ensure_ascii=False))


if __name__=='__main__':
    main()
