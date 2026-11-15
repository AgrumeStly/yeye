"""完整两圈P1预览：实测双边／当前单带／预估边界与中线分层显示。"""

import argparse
from bisect import bisect_right
import math
from pathlib import Path
import shutil

import cv2
import numpy as np

from make_boundary_preview import chinese_panel
from replay_recovery import load
from review_recovery_inputs import digest,save


def dashed_line(image,a,b,color):
    """图像坐标实线段内分成虚线，保留画外坐标交给画布裁切，不夹成假边。"""
    a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float)
    length=float(np.linalg.norm(b-a))
    if length<1:return
    direction=(b-a)/length
    for start in np.arange(0,length,7):
        p=a+direction*start;q=a+direction*min(length,start+3.5)
        cv2.line(image,tuple(np.rint(p).astype(int)),tuple(np.rint(q).astype(int)),color,1,cv2.LINE_AA)


def make_canvas(row,header,footer,cache):
    """右侧只在独立预测层画紫／黄虚线；原R1无效状态继续原样展示。"""
    gray=cv2.imread(row['source'],cv2.IMREAD_GRAYSCALE)
    assert gray is not None and digest(Path(row['source']))==row['source_sha256']
    original=cv2.cvtColor(gray,cv2.COLOR_GRAY2BGR);marked=original.copy()
    observed=row['recovery_observation']['pair_samples'];p1=row['prediction_observation']
    for x in range(0,320,12):cv2.line(marked,(x,120),(min(319,x+6),120),(140,140,140),1)
    for a,b in zip(observed,observed[1:]):
        if b['y']-a['y']<=15:
            for side,color in [('left',(30,220,30)),('right',(0,150,255))]:
                cv2.line(marked,(a[side],a['y']),(b[side],b['y']),color,1)
    for p in observed:
        cv2.circle(marked,(p['left'],p['y']),1,(30,220,30),-1)
        cv2.circle(marked,(p['right'],p['y']),1,(0,150,255),-1)
        cv2.circle(marked,(round((p['left']+p['right'])/2),p['y']),1,(255,255,0),-1)
    for p in p1['observed_single_boundary']:
        cv2.circle(marked,(p['x'],p['y']),2,(255,255,255),1)
    predictions=p1['estimated_pairs']
    for a,b in zip(predictions,predictions[1:]):
        if b['y']-a['y']>15:continue
        missing=a['estimated_role']
        dashed_line(marked,(a[missing],a['y']),(b[missing],b['y']),(255,80,240))
        dashed_line(marked,((a['left']+a['right'])/2,a['y']),((b['left']+b['right'])/2,b['y']),(0,255,255))
    # 每段至少6个实际行；加空心预测点，避免短线段的虚线节距被误看成实测。
    for p in predictions:
        missing=p['estimated_role']
        cv2.circle(marked,(round(p[missing]),p['y']),2,(255,80,240),1)
        cv2.circle(marked,(round((p['left']+p['right'])/2),p['y']),2,(0,255,255),1)
    canvas=np.zeros((720,1280,3),np.uint8);canvas[:80]=header
    canvas[80:560,:640]=cv2.resize(original,(640,480),interpolation=cv2.INTER_NEAREST)
    canvas[80:560,640:]=cv2.resize(marked,(640,480),interpolation=cv2.INTER_NEAREST)
    if predictions:
        state='存在历史几何预估：紫虚线为估计边界，黄虚线为估计中线；不是实测或控制轨迹'
        color=(1,.85,.25)
    elif observed:
        state='当前直接双边观测可用；绿色／橙色为当前接受的内缘，青色为对应中点'
        color=(.35,1,.5)
    else:
        state='当前未知：角色关联不足、时间过长或画面突变；预估已撤销'
        color=(1,.35,.3)
    if state not in cache:cache[state]=chinese_panel(1280,50,[(20,33,state,21,color)])
    canvas[560:610]=cache[state]
    measured='INVALID' if not row['valid'] else f"{row['deviation_px']:+.1f}px"
    predicted='NONE' if p1['estimated_deviation_px'] is None else f"{p1['estimated_deviation_px']:+.1f}px"
    cv2.putText(canvas,f"Frame {row['frame_id']:04d}  capture t={row['timestamp_ms']/1000:.3f}s   R1 y120: {measured}   P1 y120 estimate: {predicted}",
                (20,637),cv2.FONT_HERSHEY_SIMPLEX,.55,(235,235,235),1,cv2.LINE_AA)
    age='NONE' if p1['model_age_max_ms'] is None else f"{p1['model_age_max_ms']}ms / limit 1500ms"
    outside=sum(not p['estimated_edge_in_image'] for p in predictions)
    cv2.putText(canvas,f"Historical width age: {age}   role: {p1['inferred_role'] or 'unknown'}   estimated points outside image: {outside}",
                (20,667),cv2.FONT_HERSHEY_SIMPLEX,.54,(225,225,225),1,cv2.LINE_AA)
    canvas[680:720]=footer
    return canvas


def run(input_path,output):
    """覆盖完整732张与全部单边失效段，按真实软件时间保持已有原图。"""
    output.mkdir(parents=True,exist_ok=False)
    rows=load(input_path)
    full=[r for r in rows if r['session']=='push_full_lap_0001'];assert len(full)==732
    header=chinese_panel(1280,80,[(20,29,'完整两圈：当前观测 + 预估边界／中线（独立P1候选，非控制轨迹）',23,(1,1,1)),
        (20,63,'左：原图；白圈：关联到的当前单带',18,(.85,.85,.85)),
        (660,63,'右：绿／橙实测，紫虚线估计边界，黄虚线估计中线',17,(.85,.85,.85))])
    footer=chinese_panel(1280,40,[(20,27,'仅用当前与历史；不借未来帧补线；灰线y120；模型到期撤销；电脑离线／手推，尚未动力验收。',17,(.75,.75,.75))])
    video_path=output/'two_lap_predicted_boundaries_centerline.mp4'
    writer=cv2.VideoWriter(str(video_path),cv2.VideoWriter_fourcc(*'mp4v'),10,(1280,720));assert writer.isOpened()
    times=[r['timestamp_ms'] for r in full];count=math.ceil((times[-1]+100)/100)
    last=None;canvas=None;cache={};mapping=[]
    try:
        for step in range(count):
            index=max(0,bisect_right(times,step*100)-1)
            if last!=index:canvas=make_canvas(full[index],header,footer,cache);last=index
            writer.write(canvas);mapping.append(full[index]['frame_id'])
    finally:writer.release()
    decoder=cv2.VideoCapture(str(video_path));decoded=0
    while True:
        ok,image=decoder.read()
        if not ok:break
        assert image.shape==(720,1280,3);decoded+=1
    decoder.release();assert decoded==count and len(set(mapping))==732
    # 所有自然单边预测逐张制作审核页，不把有预测输出自动等同于正确。
    cards=[];indices=[]
    for row in rows:
        if row['prediction_observation']['estimated_pairs']:
            cards.append(cv2.resize(make_canvas(row,header,footer,cache),(640,360),interpolation=cv2.INTER_AREA))
            indices.append(dict(session=row['session'],frame=row['frame_id']))
    pages=[]
    for start in range(0,len(cards),12):
        chunk=cards[start:start+12]
        while len(chunk)%3:chunk.append(np.zeros_like(chunk[0]))
        path=output/f'prediction_audit_{start//12+1:02d}.jpg'
        assert cv2.imwrite(str(path),np.vstack([np.hstack(chunk[i:i+3]) for i in range(0,len(chunk),3)]))
        pages.append(dict(path=path.as_posix(),frames=indices[start:start+12]))
    save(output/'audit_index.json',pages)
    examples=[next(r for r in full if r['prediction_observation']['estimated_pairs']),
              next(r for r in full if r['prediction_observation']['estimated_pairs'] and not r['recovery_observation']['pair_samples']),
              next(r for r in full if r['frame_id']==135)]
    for row in examples:assert cv2.imwrite(str(output/f"example_{row['frame_id']:04d}.jpg"),make_canvas(row,header,footer,cache))
    shutil.copy2(Path(__file__),output/'make_prediction_preview.py')
    save(output/'validation.json',dict(passed=True,file=video_path.as_posix(),sha256=digest(video_path),
        width=1280,height=720,display_fps=10,decoded_frames=decoded,duration_s=decoded/10,
        all_source_frames_shown=len(set(mapping)),unique_sources=732,prediction_audit_frames=len(indices),
        input_sha256=digest(input_path),mapping_source_frame=mapping,
        scope='Complete recorded two-lap visualization, past-only estimates dashed and distinct from observed boundaries; not complete validated trajectory'))
    print(dict(video=video_path.as_posix(),duration_s=decoded/10,decoded=decoded,audit_pages=len(pages)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();run(args.input,args.output)
