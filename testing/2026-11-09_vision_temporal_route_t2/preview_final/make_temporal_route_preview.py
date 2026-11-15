"""T2全程预览与人工审核页：模型路线、证据强弱、小地图分别显示。"""

import argparse
from bisect import bisect_right
import math
from pathlib import Path
import shutil
import sys

import cv2
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from offline_temporal_route import GroundProjection, RoadTemplates, TemporalRouteConfig
from make_boundary_preview import chinese_panel
from replay_recovery import load
from review_recovery_inputs import digest,save


def draw_poly(canvas, points, color, dashed=False, thickness=2):
    """绘制相邻模型点；画外点由裁切处理，不把画外路径强夹在边缘。"""
    for a,b in zip(points,points[1:]):
        a=np.asarray(a);b=np.asarray(b)
        if not np.isfinite([*a,*b]).all() or np.linalg.norm(a-b)>100:
            continue
        if dashed:
            for t in np.arange(0,1,.4):
                p=np.rint(a+(b-a)*t).astype(int);q=np.rint(a+(b-a)*min(t+.2,1)).astype(int)
                cv2.line(canvas,tuple(p),tuple(q),color,thickness,cv2.LINE_AA)
        else:
            cv2.line(canvas,tuple(np.rint(a).astype(int)),tuple(np.rint(b).astype(int)),color,thickness,cv2.LINE_AA)


def marked_image(row):
    """绿橙为C2实测锚点；紫为推断边界；黄为推荐模型线，始终不冒称实测。"""
    gray=cv2.imread(row['source'],cv2.IMREAD_GRAYSCALE);assert gray is not None
    canvas=cv2.cvtColor(gray,cv2.COLOR_GRAY2BGR);t=row['temporal_route']
    for p in row['recovery_observation']['pair_samples']:
        cv2.circle(canvas,(p['left'],p['y']),1,(40,235,40),-1)
        cv2.circle(canvas,(p['right'],p['y']),1,(0,150,255),-1)
    draw_poly(canvas,t['model_left_px'],(235,75,230),True,1)
    draw_poly(canvas,t['model_right_px'],(235,75,230),True,1)
    color=(0,245,255) if t['state']!='map_prior_only' else (140,140,140)
    draw_poly(canvas,t['recommended_path_px'],color,True,2)
    return gray,canvas


def map_panel(t):
    """绘制完整名义推荐线和节点假设；图示不表示厘米级定位或实车轨迹。"""
    canvas=np.full((285,350,3),22,np.uint8)
    outer=np.array([[28,252],[28,143],[173,22],[318,143],[318,252]],np.int32)
    inner=np.array([[65,215],[65,158],[173,75],[281,158],[281,215]],np.int32)
    center=(outer+inner)//2
    cv2.polylines(canvas,[outer],True,(160,160,160),2);cv2.polylines(canvas,[inner],True,(160,160,160),2)
    cv2.polylines(canvas,[center],True,(220,220,0),2)
    nodes=['bottom_left','left_shoulder','apex_77','right_shoulder','bottom_right']
    if t['map']['node'] in nodes:
        node=nodes.index(t['map']['node'])
        cv2.circle(canvas,tuple(center[node]),9,(0,210,255),2)
    for i,p in enumerate(center):cv2.putText(canvas,str(i+1),tuple(p+np.array([7,-8])),cv2.FONT_HERSHEY_SIMPLEX,.5,(230,230,230),1)
    cv2.line(canvas,(225,215),(225,252),(220,220,220),2)
    cv2.arrowedLine(canvas,(200,233),(175,233),(220,220,0),2,tipLength=.3)
    return canvas


def make_canvas(row,header,footer,cache):
    """1600×900原图／推荐路线／候选鸟瞰；下方给状态与完整地图。"""
    gray,marked=marked_image(row);t=row['temporal_route'];model=t['model']
    canvas=np.full((900,1600,3),18,np.uint8);canvas[:70]=header
    canvas[70:550,:640]=cv2.resize(gray,(640,480),interpolation=cv2.INTER_NEAREST)[...,None]
    canvas[70:550,640:1280]=cv2.resize(marked,(640,480),interpolation=cv2.INTER_NEAREST)
    templates=RoadTemplates(GroundProjection(),TemporalRouteConfig())
    bev,visible,_=templates.evidence(gray,float(row['threshold'] or 90))
    world=np.full((*bev.shape,3),30,np.uint8)
    world[visible]=(190-bev[visible]*.65).astype(np.uint8)[:,None]
    path=np.asarray(t['recommended_path_ground_full']);points=np.column_stack([path[:,0]+100,150-path[:,1]])
    draw_poly(world,points,(0,245,255) if t['state']!='map_prior_only' else (140,140,140),True,1)
    cv2.line(world,(0,138),(200,138),(130,90,90),1)
    cv2.circle(world,(100,150),3,(0,0,255),-1)
    cv2.arrowedLine(world,(100,150),(100,137),(0,0,255),1)
    canvas[70:374,1280:]=cv2.resize(world,(320,304),interpolation=cv2.INTER_NEAREST)
    if 'bev_legend' not in cache:
        cache['bev_legend']=chinese_panel(320,176,[(8,29,'局部路线包含近端盲区',20,(1,.9,.5)),
            (8,60,'红点：车头；横线下为盲区',18,(.85,.85,.85)),
            (8,91,'灰线：无足够支持的名义路线',17,(.85,.85,.85)),
            (8,122,'候选平面并非全图标定',18,(.9,.75,.75)),
            (8,153,'圆弧半径／车体余量尚待实测',17,(.85,.85,.85))])
    canvas[374:550,1280:]=cache['bev_legend']
    canvas[560:845,10:360]=map_panel(t)
    state=t['state'];key=(state,t['map']['node'],t['map']['lap_observation'])
    if key not in cache:
        names={'current_supported_model':'模型获当前黑带支持：边界及路线仍为几何推断',
               'history_prediction':'当前支持不足：仅使用有限运动补偿历史预测',
               'map_prior_only':'仅剩名义路线先验：不能按此控制，需停车／重新定位'}
        cache[key]=chinese_panel(1220,105,[(10,30,names[state],24,(1,.85,.2)),
            (10,67,f"地图节点假设：{t['map']['node']}；已观察终点 {t['map']['finish_observations']} 次；比赛只跑1圈",20,(.85,.9,1)),
            (10,98,'左下青线：完整名义行驶线；黄圈：节点假设，非精确车辆位置。',18,(.8,.8,.8))])
    canvas[560:665,375:1595]=cache[key]
    lines=[f"Frame {row['frame_id']:04d}   t={row['timestamp_ms']/1000:.3f}s   R1 y120: "+(f"{row['deviation_px']:+.1f}px" if row['valid'] else 'INVALID'),
        f"T2 current support L/R: {model['current_side_support'][0]:.2f} / {model['current_side_support'][1]:.2f}   fitted turn: {model['angle_deg']:.1f} deg",
        f"Motion: {t['motion']['inliers']} inliers; available={t['motion']['available']}  history={t['history_frames']}  yaw diagnostic={t['yaw_total_deg']:.1f} deg",
        f"PC algorithm: {row['t2_pc_algorithm_ms']:.1f}ms   Control-ready: NO   Vehicle clearance verified: NO"]
    for i,line in enumerate(lines):cv2.putText(canvas,line,(385,700+35*i),cv2.FONT_HERSHEY_SIMPLEX,.57,(225,225,225),1,cv2.LINE_AA)
    canvas[850:900]=footer
    return canvas


def run(input_path,output,cards_only=False):
    """完整732帧均按真实时间展示；审核页涵盖全部关键无效区间及过渡帧。"""
    output.mkdir(parents=True,exist_ok=False);rows=load(input_path)
    source_hash=digest(Path(__file__));shutil.copy2(Path(__file__),output/Path(__file__).name)
    full=[r for r in rows if r['session']=='push_full_lap_0001'];assert len(full)==732
    header=chinese_panel(1600,70,[(15,27,'T2多帧／二维路线候选：左原图，中推荐线，右候选鸟瞰（平面几何尚待标定验证）',24,(1,1,1)),
        (15,57,'绿／橙点：C2当前边界；紫虚线：模型边界；黄虚线：推荐路线；灰线：仅先验。全部为离线手推回放。',20,(.85,.85,.85))])
    footer=chinese_panel(1600,50,[(15,32,'仅当前与历史；不按帧号计弯；地图与路线仍有误差；全图度量、车体余量、K230实时和动力循迹未验收。',20,(.85,.85,.85))])
    cache={}
    critical=[(88,148),(167,196),(237,308),(335,425),(448,490),(496,527),(532,590)]
    selected=[r for r in full if any(a<=r['frame_id']<=b for a,b in critical)]
    pages=[]
    for start in range(0,len(selected),12):
        cards=[]
        for row in selected[start:start+12]:
            _,marked=marked_image(row)
            card=cv2.copyMakeBorder(marked,25,30,0,0,cv2.BORDER_CONSTANT)
            t=row['temporal_route'];model=t['model']
            cv2.putText(card,f"f{row['frame_id']} {row['timestamp_ms']/1000:.2f}s {t['map']['node']}",(4,17),cv2.FONT_HERSHEY_SIMPLEX,.35,(255,255,255),1)
            cv2.putText(card,f"angle{model['angle_deg']:.0f} L/R {model['current_side_support'][0]:.2f}/{model['current_side_support'][1]:.2f}",(4,283),cv2.FONT_HERSHEY_SIMPLEX,.4,(255,255,255),1)
            cards.append(card)
        while len(cards)%4:cards.append(np.zeros_like(cards[0]))
        image=np.vstack([np.hstack(cards[i:i+4]) for i in range(0,len(cards),4)])
        path=output/f'audit_{start//12+1:02d}.jpg';assert cv2.imwrite(str(path),image)
        pages.append(dict(file=path.as_posix(),frames=[r['frame_id'] for r in selected[start:start+12]]))
    save(output/'audit_index.json',pages)
    if cards_only:return
    video=output/'two_lap_temporal_recommended_route.mp4'
    writer=cv2.VideoWriter(str(video),cv2.VideoWriter_fourcc(*'mp4v'),10,(1600,900));assert writer.isOpened()
    times=[r['timestamp_ms'] for r in full];count=math.ceil((times[-1]+100)/100);mapping=[];previous=None
    try:
        for step in range(count):
            index=max(0,bisect_right(times,step*100)-1)
            if previous!=index:
                frame=make_canvas(full[index],header,footer,cache);previous=index
            writer.write(frame);mapping.append(full[index]['frame_id'])
    finally:writer.release()
    cap=cv2.VideoCapture(str(video));decoded=0
    while True:
        ok,frame=cap.read()
        if not ok:break
        assert frame.shape==(900,1600,3);decoded+=1
    cap.release();assert decoded==count and len(set(mapping))==732
    for index in [0,99,119,175,279,389,414,514,575]:
        assert cv2.imwrite(str(output/f'example_{full[index]["frame_id"]:04d}.jpg'),make_canvas(full[index],header,footer,cache))
    save(output/'video_validation.json',dict(passed=True,sha256=digest(video),duration_s=decoded/10,
        decoded_frames=decoded,source_frames=len(set(mapping)),input_sha256=digest(input_path),
        all_source_ids=mapping,display_fps=10,originals_untouched=True,preview_source_sha256=source_hash))
    print(dict(video=video.as_posix(),duration=decoded/10,frames=decoded))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--cards-only',action='store_true')
    a=p.parse_args();run(a.input,a.output,a.cards_only)
