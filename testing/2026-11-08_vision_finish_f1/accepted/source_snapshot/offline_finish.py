"""V-07独立终点候选：路内横向虚线几何＋真实采集时间事件。

只输出看到虚线／经过相机观察区域，不输出全车越线、圈数或停车决定。
图像坐标为像素；所有时序毫秒。帧号、文件名和未来图像均不作判据。
"""

from dataclasses import asdict, dataclass
from itertools import combinations
import math

import cv2
import numpy as np


@dataclass(frozen=True)
class FinishConfig:
    """练习场开发参数，未验证官方分离色块及其它虚线规格。"""

    top: int = 65
    bottom: int = 232
    min_width: int = 8
    max_width: int = 68
    max_height: int = 14
    min_aspect: float = 3.
    max_slope: float = .22
    line_residual_px: float = 3.
    min_road_fraction: float = .32
    min_gap_ratio: float = .25
    max_gap_ratio: float = 2.5
    initial_clear_ms: int = 1500
    confirm_ms: int = 150
    exit_y: int = 180
    exit_clear_ms: int = 600
    rearm_clear_ms: int = 1500
    gap_reset_ms: int = 700
    max_y_rate_px_s: float = 180.
    jump_margin_px: float = 25.


class FinishDetector:
    """视觉输入与时序解耦，调用方提供同帧R1实测诊断及真实时间。"""

    def __init__(self,config=None):
        self.config=config or FinishConfig()
        self.reset()

    def reset(self):
        """新会话／长断流后回到起点防误触发，不恢复过期事件。"""
        self.session=None;self.last_ms=None
        self.armed=False;self.clear_since=None
        self.track=None;self.next_event=1

    def parameters(self):
        return asdict(self.config)

    @staticmethod
    def _corridor(gray,y,height,road,threshold):
        """从横线邻域实际灰度扫描测双边，避免横线连接两带破坏连通域。

        只在邻近行测得真实黑段，不按固定路宽补边。与同帧R1已测双边
        锚点作有限距离关联，防止把背景文字两段当道路。用于终点形态
        约束，不回填弯道中线，也不把邻行坐标称该行精确地面映射。
        """
        path=road.get('pair_samples',[])
        if not path:return None
        for sample_y in (round(y)-height-3,round(y)+height+3):
            if not 65<=sample_y<=232:continue
            profile=np.median(gray[sample_y-1:sample_y+2],axis=0)
            mask=profile<=threshold
            changes=np.diff(np.r_[False,mask,False].astype(np.int8))
            runs=[(int(a),int(b-1)) for a,b in zip(np.flatnonzero(changes==1),np.flatnonzero(changes==-1))
                  if 3<=b-a<=55]
            anchor=min(path,key=lambda p:abs(p['y']-sample_y))
            if abs(anchor['y']-sample_y)>55:continue
            options=[]
            for left,right in combinations(runs,2):
                lx,rx=left[1],right[0]
                if not 3<lx<rx<316 or not 55<=rx-lx<=300:continue
                if mask[lx+2:rx-1].mean()>.08:continue
                distance=abs(lx-anchor['left'])+abs(rx-anchor['right'])
                if max(abs(lx-anchor['left']),abs(rx-anchor['right']))<=65:
                    options.append((distance,lx,rx))
            if options:
                _,left,right=min(options)
                return dict(left=left,right=right,measured_y=sample_y)
        return None

    def observe(self,gray,road):
        """同帧几何：至少两条分离、相近尺寸、路内共线的横向黑短划。

        文字通常在道路外；连续转角带缺分离白间隙；反光通常为亮纹。
        这些是启发式约束，不保证所有纹样可分，不将质量数值当概率。
        """
        c=self.config
        result=dict(visible=False,y=None,dashes=[],corridor=None,reason='no_road_supported_dash_group')
        if gray is None or gray.shape!=(240,320) or gray.dtype!=np.uint8:
            result['reason']='unsupported_image';return result
        if not road.get('valid') or road.get('threshold') is None:
            result['reason']='road_not_currently_supported';return result
        threshold=road['threshold']
        mask=(gray<=threshold).astype(np.uint8)
        mask[:c.top]=0;mask[c.bottom+1:]=0
        _,labels,stats,centers=cv2.connectedComponentsWithStats(mask,connectivity=8)
        dashes=[]
        for i in range(1,len(stats)):
            x,y,w,h,area=map(int,stats[i]);cx,cy=map(float,centers[i])
            if (not c.min_width<=w<=c.max_width or not 1<=h<=c.max_height or
                    w/h<c.min_aspect or area/(w*h)<.45 or y<=c.top or y+h>c.bottom):continue
            corridor=self._corridor(gray,cy,h,road,threshold)
            if corridor and x>=corridor['left']+3 and x+w<=corridor['right']-2:
                dashes.append(dict(x=x,y=y,width=w,height=h,cx=cx,cy=cy,corridor=corridor))
        groups=[]
        for first,second in combinations(dashes,2):
            dx=second['cx']-first['cx']
            if abs(dx)<15:continue
            slope=(second['cy']-first['cy'])/dx
            if abs(slope)>c.max_slope:continue
            group=sorted([d for d in dashes if abs(d['cy']-(first['cy']+slope*(d['cx']-first['cx'])))<=c.line_residual_px],key=lambda d:d['x'])
            if not 2<=len(group)<=5:continue
            widths=[d['width'] for d in group]
            if max(widths)/min(widths)>2.2:continue
            gaps=[b['x']-a['x']-a['width'] for a,b in zip(group,group[1:])]
            mean_width=float(np.mean(widths))
            if any(not c.min_gap_ratio<=gap/mean_width<=c.max_gap_ratio for gap in gaps):continue
            corridor=group[len(group)//2]['corridor']
            span=group[-1]['x']+group[-1]['width']-group[0]['x']
            if span/(corridor['right']-corridor['left'])<c.min_road_fraction:continue
            groups.append((len(group),span,group,corridor))
        if groups:
            _,_,group,corridor=max(groups,key=lambda g:(g[0],g[1]))
            result.update(visible=True,y=float(np.mean([d['cy'] for d in group])),
                          dashes=group,corridor=corridor,reason=None)
        return result

    def update(self,observation,timestamp_ms,session_key,road_valid=True):
        """真实时间状态机：起点抑制→待检测→确认一次→观察区经过→清空再武装。

        确认需两帧及≥150ms；重复候选不重复发事件。只有先向下移动到
        y180则报经过图像观察门；随后在道路仍可观测时缺检≥600ms只报
        近处标记随后未观测到，不认定已经离开整个ROI。道路失效不作为
        越线依据。超过700ms采集间隔／时钟倒退／会话改变清空。
        """
        c=self.config
        time_ok=(isinstance(timestamp_ms,(int,float)) and not isinstance(timestamp_ms,bool)
                 and math.isfinite(timestamp_ms) and timestamp_ms>=0 and session_key is not None)
        reason=None
        if not time_ok:reason='missing_capture_time'
        elif session_key!=self.session:reason='session_changed'
        elif self.last_ms is not None and timestamp_ms<=self.last_ms:reason='clock_not_increasing'
        elif self.last_ms is not None and timestamp_ms-self.last_ms>c.gap_reset_ms:reason='capture_gap_timeout'
        if reason:self.reset()
        now=timestamp_ms if time_ok else None
        output=dict(observation=observation,state='unknown',armed=self.armed,event=None,event_id=None,
                    passage_event=None,gate_event=None,reset_reason=reason,
                    whole_vehicle_crossed=None,automatic_stop=False)
        if not time_ok:return output
        self.session=session_key;self.last_ms=now
        visible=observation['visible'] and road_valid
        if not self.armed:
            if visible or not road_valid:
                self.clear_since=None
                output['state']='start_line_suppressed' if visible else 'initial_guard'
            else:
                if self.clear_since is None:self.clear_since=now
                if now-self.clear_since>=c.initial_clear_ms:self.armed=True;self.clear_since=None
                output['state']='armed' if self.armed else 'initial_guard'
            output['armed']=self.armed
            return output
        track=self.track
        if visible:
            self.clear_since=None
            y=observation['y']
            if track:
                dt=now-track['last_ms']
                if y<track['last_y']-30 or abs(y-track['last_y'])>c.jump_margin_px+c.max_y_rate_px_s*dt/1000:
                    if not track['confirmed']:self.track=None;track=None
                    else:
                        output.update(state='incoherent_observation_suppressed',event_id=track['id'])
                        return output
            if track is None:
                track=dict(first_ms=now,last_ms=now,first_y=y,last_y=y,max_y=y,count=0,
                           confirmed=False,passed=False,gate_crossed=False,id=None)
                self.track=track
            track.update(last_ms=now,last_y=y,max_y=max(track['max_y'],y),count=track['count']+1)
            if not track['confirmed'] and track['count']>=2 and now-track['first_ms']>=c.confirm_ms:
                track['confirmed']=True;track['id']=self.next_event;self.next_event+=1
                output['event']='finish_line_seen'
            if track['confirmed'] and not track['gate_crossed'] and track['first_y']<c.exit_y<=y:
                track['gate_crossed']=True
                output['gate_event']='passed_image_y180_gate'
            output.update(state='finish_line_seen' if track['confirmed'] else 'candidate',event_id=track['id'])
        elif track:
            if not road_valid:
                self.clear_since=None
                output.update(state='temporarily_unobserved',event_id=track['id'])
                if now-track['last_ms']>c.gap_reset_ms:
                    self.track=None;self.armed=False
                return output
            if self.clear_since is None:self.clear_since=now
            clear_ms=now-self.clear_since
            if (track['confirmed'] and not track['passed'] and track['max_y']>=c.exit_y and
                    track['max_y']-track['first_y']>=10 and clear_ms>=c.exit_clear_ms):
                track['passed']=True;output['passage_event']='near_marker_then_unobserved'
            output.update(state='near_marker_then_unobserved' if track['passed'] else 'temporarily_unobserved',event_id=track['id'])
            if clear_ms>=c.rearm_clear_ms:self.track=None;output['state']='armed'
        else:
            output['state']='armed'
        output['armed']=self.armed
        return output

    def detect(self,gray,road,timestamp_ms,session_key):
        """完整逐帧入口，无文件系统／串口／相机副作用。"""
        return self.update(self.observe(gray,road),timestamp_ms,session_key,bool(road.get('valid')))
