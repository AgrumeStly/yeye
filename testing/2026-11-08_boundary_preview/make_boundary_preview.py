"""V-06原图／边界对照预览；读取冻结结果绘图，不重新调参或操作相机。

绿色／橙色仅绘制C2当前接受的左右内缘，青色为对应同帧中点；失效时
不补线、不画历史边界。人工播放使用10Hz保持原帧，依原采集软件时间
分配时长，不把旧10fps逐图视频当真实采集速度或板上实时性能。
"""

import argparse
from bisect import bisect_right
import hashlib
import json
import math
from pathlib import Path
import shutil

import cv2
import fitz
import numpy as np


def sha(path):
    """按文件字节计算来源与输出哈希，不依赖Git是否跟踪。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


def chinese_panel(width,height,lines):
    """利用已安装PDF库渲染中文字幕；只生成派生图，不编辑采集原图。"""
    doc=fitz.open();page=doc.new_page(width=width,height=height)
    page.draw_rect(page.rect,color=None,fill=(.055,.065,.08))
    for x,y,text,size,color in lines:
        page.insert_text((x,y),text,fontname='china-s',fontsize=size,color=color)
    pix=page.get_pixmap(alpha=False)
    image=cv2.cvtColor(np.frombuffer(pix.samples,dtype=np.uint8).reshape(height,width,3),cv2.COLOR_RGB2BGR)
    doc.close();return image


def canvas_for(row,header,footer,status_cache):
    """两侧使用相同原图；右侧只标当前实测锚点及其范围内的连线。

    固定y120偏差是否有效单独显示，不把较近／较远中点偷换成此偏差。
    连线只连接间隔≤15px的同侧实测锚点，不超出已观测段。
    """
    source=Path(row['source'])
    assert sha(source)==row['source_sha256'],str(source)
    gray=cv2.imread(str(source),cv2.IMREAD_UNCHANGED)
    assert gray is not None and gray.shape==(240,320) and gray.dtype==np.uint8
    original=cv2.cvtColor(gray,cv2.COLOR_GRAY2BGR);marked=original.copy()
    obs=row['recovery_observation'];pairs=obs['pair_samples']
    for x in range(0,320,12):cv2.line(marked,(x,120),(min(x+6,319),120),(150,150,150),1)
    for a,b in zip(pairs,pairs[1:]):
        if b['y']-a['y']<=15:
            for side,color in [('left',(40,235,40)),('right',(0,155,255))]:
                cv2.line(marked,(a[side],a['y']),(b[side],b['y']),color,1)
    for p in pairs:
        cv2.circle(marked,(p['left'],p['y']),2,(40,235,40),-1)
        cv2.circle(marked,(p['right'],p['y']),2,(0,155,255),-1)
        cv2.circle(marked,(round((p['left']+p['right'])/2),p['y']),1,(255,255,0),-1)
    image=np.zeros((720,1280,3),np.uint8)
    image[:80]=header
    image[80:560,:640]=cv2.resize(original,(640,480),interpolation=cv2.INTER_NEAREST)
    image[80:560,640:]=cv2.resize(marked,(640,480),interpolation=cv2.INTER_NEAREST)
    state=('当前双边观测不足：不补线；停车建议状态' if not pairs else
           ('当前局部双边可见；固定y120偏差无效' if not row['valid'] else
            ('当前双边及固定y120偏差可用；时序已确认' if obs['temporal_state']=='stable_observation' else
             '当前双边可见；等待时序重新确认')))
    if state not in status_cache:
        color=(1,.35,.3) if not pairs else ((1,.8,.2) if not row['valid'] or obs['temporal_state']!='stable_observation' else (.3,1,.5))
        status_cache[state]=chinese_panel(1280,50,[(20,34,state,24,color)])
    image[560:610]=status_cache[state]
    cv2.putText(image,f"Frame {row['frame_id']:04d}   capture t={row['timestamp_ms']/1000:.3f}s",
                (20,638),cv2.FONT_HERSHEY_SIMPLEX,.7,(240,240,240),1,cv2.LINE_AA)
    deviation='INVALID' if not row['valid'] else f"{row['deviation_px']:+.1f}px"
    ys='NONE' if not pairs else str(obs['y_range'])
    cv2.putText(image,f"y120 offset: {deviation}    C2 observed y: {ys}    turn hint: {obs['turn_hint'] or 'unknown'}",
                (20,668),cv2.FONT_HERSHEY_SIMPLEX,.58,(220,220,220),1,cv2.LINE_AA)
    image[680:720]=footer
    return image


def make_video(rows,destination,title):
    """输出原软件时间近似1倍速MP4，重采样只重复已有曝光帧。

    10Hz显示量化使切换最多延后100ms，开头不足首帧时间显示首帧；
    最后图保持到最后采集软件时间后100ms，不补造未记录曝光。
    """
    header=chinese_panel(1280,80,[(20,29,title,22,(1,1,1)),
       (20,64,'左：采集原图',20,(.85,.85,.85)),
       (660,64,'右：当前左边界（绿）／右边界（橙）／对应中点（青）',18,(.85,.85,.85))])
    footer=chinese_panel(1280,40,[(20,27,'电脑离线／手推素材；灰虚线为y120参考行；历史推断不画成当前边界；尚未板上实时或自动过弯验收。',17,(.75,.75,.75))])
    times=[r['timestamp_ms'] for r in rows]
    assert all(t is not None for t in times) and all(a<b for a,b in zip(times,times[1:]))
    count=math.ceil((times[-1]+100)/100)
    writer=cv2.VideoWriter(str(destination),cv2.VideoWriter_fourcc(*'mp4v'),10,(1280,720))
    assert writer.isOpened()
    last=None;canvas=None;cache={};mapping=[]
    try:
        for step in range(count):
            index=max(0,bisect_right(times,step*100)-1)
            if index!=last:
                canvas=canvas_for(rows[index],header,footer,cache);last=index
            writer.write(canvas)
            mapping.append(dict(display_ms=step*100,source_frame=rows[index]['frame_id'],capture_ms=times[index]))
    finally:writer.release()
    video=cv2.VideoCapture(str(destination));decoded=0
    while True:
        ok,frame=video.read()
        if not ok:break
        assert frame.shape==(720,1280,3)
        decoded+=1
    video.release();assert decoded==count
    return dict(file=destination.as_posix(),sha256=sha(destination),source_frames=len(rows),
                first_frame=rows[0]['frame_id'],last_frame=rows[-1]['frame_id'],
                decoded_frames=decoded,display_fps=10,duration_s=count/10,display_mapping=mapping)


def main(output):
    """仅新目录落盘，保留已有视频、原图、算法和证据，不重复执行识别。"""
    output.mkdir(parents=True,exist_ok=False)
    source=Path('testing/2026-11-08_vision_recovery_c2/replay_accepted/frames.jsonl')
    before=sha(source)
    records=[json.loads(line) for line in source.read_text(encoding='utf-8').splitlines()]
    full=[r for r in records if r['session']=='push_full_lap_0001']
    corner=[r for r in records if r['session']=='push_corner_77_0001' and r['frame_id']<=75]
    assert len(full)==732 and len(corner)==75
    protected={r['source']:r['source_sha256'] for r in full+corner}
    for file in ['vision/src/offline_boundary.py','vision/src/offline_curve.py','vision/src/offline_recovery.py']:
        protected[file]=sha(Path(file))
    save(output/'protected_before.json',protected)
    videos=[make_video(corner,output/'corner_boundary_preview.mp4','77°弯预览：入弯 → 单边／未知 → 双边恢复（原软件时间）'),
            make_video(full,output/'two_lap_boundary_preview.mp4','完整两圈边界识别预览（732张；原软件时间约1倍速）')]
    assert sha(source)==before and all(sha(Path(p))==h for p,h in protected.items())
    # 保存三个代表帧方便核对字幕／颜色／失效清空，视频本身也已全量解码。
    header=chinese_panel(1280,80,[(20,29,'边界识别预览：左原图／右当前观测',24,(1,1,1)),
        (20,64,'绿色：左内缘；橙色：右内缘；青色：当前双边中点。',20,(.85,.85,.85))])
    footer=chinese_panel(1280,40,[(20,27,'电脑离线；只画当前观测；不证明自动过弯或整车可用。',18,(.75,.75,.75))])
    for frame_id in (98,120,143):
        row=next(r for r in full if r['frame_id']==frame_id)
        assert cv2.imwrite(str(output/f'preview_frame_{frame_id:04d}.jpg'),canvas_for(row,header,footer,{}))
    shutil.copy2(Path(__file__),output/'make_boundary_preview.py')
    save(output/'validation.json',dict(passed=True,source_results_sha256=before,
         protected_unchanged=len(protected),videos=videos,source_algorithm_changed=False,
         timing='10Hz sample-and-hold from original software capture times; not 10fps exposure or on-board performance',
         scope='visualization of existing C2 current observations; no new inference or ground truth'))
    print(json.dumps([{k:v for k,v in item.items() if k!='display_mapping'} for item in videos],ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args().output)
