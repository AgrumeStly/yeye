"""V-02 R1逐帧比较与可复现审核素材生成；不改写首版输出和原始采集。"""

import argparse
import csv
import json
from pathlib import Path
import shutil

import cv2
import numpy as np


def read_records(folder):
    """读取数字顺序JSONL；本轮固定325个源编号，缺失或重复即失败。"""
    records = [json.loads(s) for s in (folder/'frames.jsonl').read_text(encoding='utf-8').splitlines()]
    assert [r['frame_id'] for r in records] == list(range(1,326))
    return records


def span(points, axis):
    """返回可见候选在指定像素轴上的跨度；不是标定长度或识别真值。"""
    return max(p[axis] for p in points)-min(p[axis] for p in points) if points else 0


def main():
    """对同源帧比较有效性和支持范围，另生成原图／首版／R1三列视频。

    比较表只陈述算法输出变化；是否是真边界仍由原图目视审核确认。
    所有恢复有效帧自动加入审核列表，强制拒绝案例与其连续邻帧也加入。
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,default=Path('vision/build/offline_v02'))
    parser.add_argument('--output',type=Path,default=Path('vision/build/offline_v02_r1'))
    parser.add_argument('--evidence',type=Path,default=Path('testing/2026-11-07_vision_offline/r1'))
    args = parser.parse_args()
    before, after = read_records(args.baseline), read_records(args.output)
    rows = []
    for old,new in zip(before,after):
        assert old['source_sha256'] == new['source_sha256'] and old['source'] == new['source']
        pairs = new['pair_samples']
        ribbons = new['visible_ribbons']
        rows.append(dict(frame_id=new['frame_id'],source=new['source'],source_sha256=new['source_sha256'],
                         old_valid=old['valid'],r1_valid=new['valid'],old_reasons=';'.join(old['reasons']),
                         r1_reasons=';'.join(new['reasons']),old_deviation_px=old['deviation_px'],
                         r1_deviation_px=new['deviation_px'],old_pair_points=len(old['pair_samples']),
                         r1_pair_points=len(pairs),old_pair_y_span=span(old['pair_samples'],'y'),
                         r1_pair_y_span=span(pairs,'y'),ribbon_count=len(ribbons),
                         old_selected_boundary_points=len(old['left'])+len(old['right']),
                         ribbon_edge_points=sum(len(r['upper'])+len(r['lower']) for r in ribbons),
                         ribbon_x_span=max([span(r['upper'],'x') for r in ribbons],default=0),
                         old_reference_supported=any(p['y']==120 for p in old['pair_samples']),
                         r1_reference_supported=any(p['y']==120 for p in pairs)))
    args.evidence.mkdir(parents=True,exist_ok=True)
    with (args.evidence/'frame_changes.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.evidence/'frame_changes.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    up = [r['frame_id'] for r in rows if not r['old_valid'] and r['r1_valid']]
    down = [r['frame_id'] for r in rows if r['old_valid'] and not r['r1_valid']]
    deviations = [abs(r['r1_deviation_px']-r['old_deviation_px']) for r in rows if r['old_valid'] and r['r1_valid']]
    summary = dict(baseline_valid=sum(r['old_valid'] for r in rows),r1_valid=sum(r['r1_valid'] for r in rows),
                   invalid_to_valid=up,valid_to_invalid=down,unchanged_validity=325-len(up)-len(down),
                   max_deviation_change_on_common_valid_px=max(deviations),
                   frames_with_supplemental_ribbons=sum(bool(r['ribbon_count']) for r in rows),
                   interpretation='published old-data regression; validity/support counts are not accuracy')
    (args.evidence/'comparison_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    coverage = []
    for y in range(65,216,5):
        coverage.append(dict(y=y,baseline=sum(any(p['y']==y for p in r['pair_samples']) for r in before),
                             r1=sum(any(p['y']==y for p in r['pair_samples']) for r in after)))
    (args.evidence/'pair_row_coverage.json').write_text(json.dumps(coverage,indent=2)+'\n',encoding='utf-8')
    ids = sorted(set(up+down+[1,31,71,131,201,241]+
                     [n+d for n in [41,61,81,111,171,191,211,251,281,301] for d in [-1,0,1]]))
    (args.evidence/'selection.json').write_text(json.dumps(dict(ids=ids,invalid_to_valid=up,valid_to_invalid=down,
        selection='mandatory centers +/-1 consecutive neighbors; six baseline successes; all changed validity frames; old-data regression only'),indent=2)+'\n',encoding='utf-8')
    sheets = args.evidence/'comparison_sheets'
    sheets.mkdir(exist_ok=True)
    selected = {}
    video_path = args.output/'comparison.mp4'
    fps = json.loads((args.output/'summary.json').read_text(encoding='utf-8'))['preview_fps']
    video = cv2.VideoWriter(str(video_path),cv2.VideoWriter_fourcc(*'mp4v'),fps,(960,350))
    assert video.isOpened(), 'comparison MP4 encoder failed'
    try:
        for old,new in zip(before,after):
            raw = cv2.imread(new['source'])
            raw = cv2.copyMakeBorder(raw,0,90,0,0,cv2.BORDER_CONSTANT)
            cv2.putText(raw,f"RAW {new['frame_id']:04d}",(4,265),cv2.FONT_HERSHEY_SIMPLEX,.5,(255,255,255),1)
            tile = np.hstack([raw,cv2.imread(str(args.baseline/old['overlay'])),
                             cv2.imread(str(args.output/new['overlay']))])
            if new['frame_id'] in ids:
                selected[new['frame_id']] = tile
            preview = cv2.copyMakeBorder(tile,20,0,0,0,cv2.BORDER_CONSTANT)
            for x,label in [(4,'RAW'),(324,'BASELINE'),(644,'R1 - preview speed only')]:
                cv2.putText(preview,label,(x,15),cv2.FONT_HERSHEY_SIMPLEX,.4,(255,255,255),1)
            video.write(preview)
    finally:
        video.release()
    for j in range(0,len(ids),4):
        assert cv2.imwrite(str(sheets/f'group_{j//4+1:02d}.jpg'),np.vstack([selected[n] for n in ids[j:j+4]]))
    cases = args.evidence/'cases'
    cases.mkdir(exist_ok=True)
    for n in [1,31,61,71,81,111,124,131,171,191,201,211,241,251,281,301]:
        assert cv2.imwrite(str(cases/f'compare_{n:04d}.png'),selected[n])
    # 检查三列视频实际可解码数，不能仅凭文件存在宣称可播放。
    decoded = 0
    capture = cv2.VideoCapture(str(video_path))
    while capture.isOpened():
        ok, _ = capture.read()
        if not ok:
            break
        decoded += 1
    capture.release()
    assert decoded == 325, f'comparison video frame count: {decoded}'
    for name in ['parameters.json','summary.json']:
        shutil.copyfile(args.output/name,args.evidence/name)
    summary.update(comparison_video_decoded_frames=decoded,review_selected_frames=len(ids))
    (args.evidence/'comparison_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    main()
