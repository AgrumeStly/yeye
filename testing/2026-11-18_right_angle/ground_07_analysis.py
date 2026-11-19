"""关联R8一次地面短停：以完整冻结窗口排除8位序号重复，不修改控制策略。"""
import hashlib
import json
from pathlib import Path
import struct
import zlib

folder = Path(__file__).resolve().parent
captured = json.loads((folder/'ground_07_capture/capture.json').read_text(encoding='utf-8'))
sample = captured['samples'][0]
trace = sample['diagnostic_trace']
raw_log = (folder/'ground_07_camera/run_0005.jsonl').read_bytes()
rows = [json.loads(line) for line in raw_log.decode('utf-8').splitlines()]
frames = {row['index']: row for row in rows if 'index' in row}
last = trace['samples'][-1]
unique_packets = {row['path_sequence']: row for row in trace['samples']}
candidates = []
for frame in frames.values():
    if frame['path_sequence'] != last['path_sequence'] or frame['steering'] != last['steering']:
        continue
    offsets = []
    matched = True
    for sequence, mcu in unique_packets.items():
        index = frame['index'] - ((last['path_sequence'] - sequence) % 256)
        camera = frames.get(index)
        matched = matched and camera is not None and all(camera[key] == mcu[key]
            for key in ('path_sequence', 'steering', 'bend'))
        if camera is not None:
            offsets.append(mcu['path_at'] - camera['elapsed_ms'])
    candidates.append(dict(index=frame['index'], all_packet_fields_match=matched,
        offsets_ms=offsets, offset_range_ms=max(offsets)-min(offsets)))

# 两个毫秒时钟、包内年龄和UART量化不要求完全相同；本轮唯一候选的8个
# 源时间偏移跨度3ms，其余重复序号候选为18..33ms或字段不匹配。
# 5ms仅为本次离线关联筛选，绝不改变200ms运行保护或声称通用时钟精度。
matches = [row for row in candidates if row['all_packet_fields_match'] and row['offset_range_ms'] <= 5]
assert len(matches) == 1
matched = matches[0]
before = frames[matched['index']]
after = frames[before['index']+1]
minimum_offset = min(matched['offsets_ms'])
maximum_offset = max(matched['offsets_ms'])
stop = trace['stop_at_ms']
arrival = [after['elapsed_ms']+after['to_send_ms']+offset for offset in (minimum_offset, maximum_offset)]
window = [row for index, row in frames.items() if before['index']-12 <= index <= after['index']+8]
assert captured['flash_matches_bin'] and trace['frozen'] == 1
assert sample['last_run']['elapsed_ms'] == 499 and trace['stop_reason'] == 2
assert stop-last['path_at'] == 200
assert before['index'] == 3289 and before['wire_valid'] and after['wire_valid']
assert before['to_send_ms'] == 40 and after['send_interval_ms'] == 164
assert after['previous_log_ms'] == 78 and after['processing_ms'] == 77
assert arrival[0] > stop
events = [row for row in rows if row.get('event') == 'path_lost']
assert not any(before['index']-12 <= row['after_index'] <= after['index']+8 for row in events)

fetch = json.loads((folder/'ground_07_camera/fetch.json').read_text(encoding='utf-8'))
assert fetch['completed']
for item in fetch['files']:
    path = folder/'ground_07_camera'/item['remote'].rsplit('/', 1)[1]
    raw = path.read_bytes()
    assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']

def png_chunk(kind, data):
    return struct.pack('>I', len(data))+kind+data+struct.pack('>I', zlib.crc32(kind+data) & 0xffffffff)

# 仅做逐像素无损格式转换以便查看；停车后5秒禁驱动采图不替代短停触发曝光。
view = folder/'ground_07_stopped_view/frame.pgm'
pgm = view.read_bytes()
assert pgm[:15] == b'P5\n320 240\n255\n' and len(pgm) == 76815
pixels = pgm[15:]
scanlines = b''.join(b'\0'+pixels[row*320:(row+1)*320] for row in range(240))
png = b'\x89PNG\r\n\x1a\n'+png_chunk(b'IHDR', struct.pack('>IIBBBBB', 320, 240, 8, 0, 0, 0, 0))
png += png_chunk(b'IDAT', zlib.compress(scanlines))+png_chunk(b'IEND', b'')
view.with_suffix('.png').write_bytes(png)
result = dict(user_report='这一次走一点就停下了，然后绿灯快闪',
    actual_revision=hex(sample['g_speed_revision']), last_run=sample['last_run'],
    frozen_trace_summary={key:value for key,value in trace.items() if key != 'samples'},
    wire_errors=sample['uart'], json_lines=len(rows), frames=len(frames),
    repeated_sequence_candidates=candidates, matched_last_frame=before, next_frame=after,
    source_to_mcu_offsets_ms=matched['offsets_ms'], source_age_at_stop_ms=stop-last['path_at'],
    next_send_mcu_estimate_ms=arrival, next_send_after_stop_ms=[value-stop for value in arrival],
    whole_session_maxima_ms={key:max(row.get(key) or 0 for row in frames.values()) for key in
        ('processing_ms', 'to_send_ms', 'send_interval_ms', 'previous_log_ms', 'previous_gc_ms', 'evidence_ms')},
    stopped_view=dict(file=str(view.relative_to(folder)), sha256=hashlib.sha256(pgm).hexdigest(),
        trigger_exposure=False),
    conclusion='499ms LINK2；最后路径源年龄200ms。帧3289发送后日志耗时78ms，叠加下一帧77ms处理，下一有效包发送约晚于停车4..7ms；本窗口无路径许可失效事件。',
    limitations=['78ms是序列化、write及可能流内部刷新的合计，不单独证明显式flush或存储介质硬件故障。',
        '帧3289不是10倍数，未调用每10帧的显式flush；因此仅减少显式flush频率不足以证明修复。',
        '关联为8个源时间偏移的范围估计，未改写原时钟，不声称示波器级到达精度。',
        '本次LINK触发时无同步曝光图；8组原图对应更早路径失效，停车后照片单列。',
        '未完成首弯，触边与完全出界未取得主控单独确认，不写零触边或通过。'])
(folder/'ground_07_review.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
(folder/'ground_07_window.json').write_text(json.dumps(window, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(dict(frames=len(frames), linked_index=before['index'], elapsed_ms=499,
    reason='LINK2', source_age_at_stop_ms=200, next_send_after_stop_ms=result['next_send_after_stop_ms'],
    verified_downloads=len(fetch['files'])), ensure_ascii=False))
