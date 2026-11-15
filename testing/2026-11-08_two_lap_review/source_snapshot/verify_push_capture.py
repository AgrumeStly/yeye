"""只读验证上电手推会话schema2；原静态校验器及其冻结哈希不变。"""

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np


def verify(folder):
    """核对完整结束、JPEG集合／哈希／格式、编号和单调软件时序。

    只证明采集文件可追溯，不证明实际手推路线、曝光时间、蜂鸣可闻或电池供电。
    未完成会话保留原件并拒绝通过，不自动修复计数或补写元数据。
    """
    folder = Path(folder)
    meta = json.loads((folder/'session.json').read_text(encoding='utf-8'))
    if meta.get('schema') != 2 or meta.get('version') != 'push-capture-1' or meta.get('state') != 'complete':
        raise ValueError('不是完整的手推采集会话')
    if meta.get('cleanup_errors') != [] or meta.get('stop_reason') != 'duration_reached':
        raise ValueError('收尾异常或未按时长正常停止')
    count, limit = meta['saved_count'], meta['max_frames']
    duration, interval = meta['planned_duration_ms'], meta['interval_ms']
    if (type(count) is not int or type(limit) is not int or not 1 <= count <= limit <= 4000
            or type(duration) is not int or not 100 <= duration <= 300000
            or type(interval) is not int or not 10 <= interval <= 1000
            or meta['capture_elapsed_ms'] < duration):
        raise ValueError('计数或时长配置异常')
    if (meta['width'], meta['height'], meta['pixel_format']) != (320, 240, 'grayscale'):
        raise ValueError('会话图像格式异常')
    rows = [json.loads(line) for line in (folder/'frames.jsonl').read_text(encoding='utf-8').splitlines()]
    expected = {'data_%04d.jpg' % i for i in range(1, count+1)}
    if len(rows) != count or {p.name for p in folder.glob('*.jpg')} != expected:
        raise ValueError('JPEG／日志集合不一致或残留临时图片')
    previous = None
    for i, row in enumerate(rows, 1):
        name = 'data_%04d.jpg' % i
        if row.get('frame_id') != i or row.get('file') != name or row.get('scene') != meta['scene']:
            raise ValueError('帧号／场景／文件名不一致')
        data = (folder/name).read_bytes()
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('JPEG大小／哈希不一致：'+name)
        image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_UNCHANGED)
        if image is None or image.shape != (240, 320) or image.dtype != np.uint8:
            raise ValueError('JPEG实际不是320×240单通道灰度：'+name)
        if (row['width'], row['height'], row['pixel_format']) != (320, 240, 'grayscale'):
            raise ValueError('帧格式记录异常')
        elapsed = row['elapsed_ms']
        if (type(elapsed) is not int or not 0 <= elapsed < duration
                or row['snapshot_call_ms'] < 0 or previous is not None and elapsed-previous < interval):
            raise ValueError('相邻帧时序或时间窗异常')
        previous = elapsed
    gaps = np.diff([r['elapsed_ms'] for r in rows])
    return dict(passed=True, folder=str(folder.resolve()), frames=count, scene=meta['scene'],
                planned_duration_ms=duration, capture_elapsed_ms=meta['capture_elapsed_ms'],
                observed_interval_ms=dict(median=float(np.median(gaps)), p95=float(np.percentile(gaps, 95)),
                                          maximum=int(gaps.max())) if len(gaps) else None,
                observed_fps=(count-1)*1000/(rows[-1]['elapsed_ms']-rows[0]['elapsed_ms']) if count > 1 else None,
                scope='file integrity and software timing; not exposure rate, route truth, audible beep or battery acceptance')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    print(json.dumps(verify(parser.parse_args().folder), ensure_ascii=False, indent=2))
