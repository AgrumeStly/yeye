"""V-06独立P1单边预测候选：当前黑带角色关联＋有限历史图像路宽。

预测不是当前观测，不改R1/C1/C2任何字段，不输出电机或有效协议路径。
模型仅假设短时间内同一图像行的路宽变化有限；弯道与相机运动可能
破坏该假设，因此必须按真实时间到期、关联歧义／突变撤销，并另行
做隐藏已知边界的误差评估。所有坐标像素、时间毫秒，禁止未来帧。
"""

from dataclasses import asdict,dataclass
import math

import cv2
import numpy as np

from offline_boundary import BoundaryDetector


@dataclass(frozen=True)
class PredictionConfig:
    """当前练习场开发门槛，非官方规则／概率置信区间／实车控制参数。"""

    max_width_age_ms:int=1500  # 每一行从最后直接双边计时，单边不能续命。
    role_memory_ms:int=700
    capture_gap_ms:int=700
    min_points:int=6
    min_span_px:int=25
    component_area:int=80
    component_span:int=25
    role_margin_px:float=10.
    role_base_gate_px:float=12.
    role_max_gate_px:float=55.
    edge_rate_px_s:float=180.
    base_uncertainty_px:float=4.
    uncertainty_growth_px_s:float=20.


def extract_candidates(gray,threshold):
    """从本帧黑带连通域提取两种朝白路面的内缘假设，保留角色未知。

    R1的三行中值／局部对比黑段是实际图像证据，连通域只验证段归属。
    同一连通域的两种朝向不能当道路双边；最终角色由历史唯一匹配。
    返回候选是诊断中间量，不能直接称可信道路边界。
    """
    if gray is None or gray.shape!=(240,320) or gray.dtype!=np.uint8 or threshold is None:
        return []
    mask=(gray<=threshold).astype(np.uint8);mask[:30]=0;mask[216:]=0
    _,labels,stats,_=cv2.connectedComponentsWithStats(mask,connectivity=8)
    strong={i for i in range(1,len(stats)) if stats[i,cv2.CC_STAT_AREA]>=80 and
            max(stats[i,cv2.CC_STAT_WIDTH],stats[i,cv2.CC_STAT_HEIGHT])>=25}
    _,rows=BoundaryDetector()._runs(gray)
    groups={}
    for row in rows:
        y=row['y']
        for run in row['runs']:
            for role,x,inset,contrast in [('left',run['end'],-1,run['rc']),
                                           ('right',run['start'],1,run['lc'])]:
                if contrast<12 or not 3<x<316:continue
                component=int(labels[y,x+inset])
                if component not in strong:continue
                groups.setdefault((component,role),[]).append(dict(y=y,x=x))
    results=[]
    for (component,role),points in groups.items():
        points=sorted(points,key=lambda p:p['y'])
        # 同一域在同一行有多条黑段时不凭排序选分支；留给未来二维关联。
        if len({p['y'] for p in points})!=len(points):continue
        if len(points)<6 or points[-1]['y']-points[0]['y']<25:continue
        # 连通域可能同时包含印字横臂与斜臂。若相邻锚点跳过长水平段，
        # 不能让中位误差掩盖分支切换；沿用R1的有限斜移门槛整段拒绝。
        if any(b['y']-a['y']>15 or abs(b['x']-a['x'])>2.8*(b['y']-a['y'])+3
               for a,b in zip(points,points[1:])):continue
        results.append(dict(component=component,role_hypothesis=role,points=points))
    return results


class SingleBoundaryPredictor:
    """每行分别保存直接观测路宽和边界位置；单边只更新可见侧角色位置。"""

    def __init__(self,config=None):
        self.config=config or PredictionConfig();self.reset()

    def reset(self):
        """会话／时钟／超时／突变清空全部模型，不能用旧会话宽度补新图。"""
        self.session=None;self.last_ms=None;self.widths={};self.roles={'left':{},'right':{}}

    def parameters(self):return asdict(self.config)

    def _associate(self,candidates,role,now,dt):
        """与历史同y锚点比较，唯一且连续的黑带才关联；不按图像左右猜角色。"""
        c=self.config;matches=[]
        gate=min(c.role_max_gate_px,c.role_base_gate_px+c.edge_rate_px_s*dt/1000)
        for candidate in candidates:
            if candidate['role_hypothesis']!=role:continue
            previous=self.roles[role]
            common=[p for p in candidate['points'] if p['y'] in previous and
                    0<=now-previous[p['y']]['ms']<=c.role_memory_ms]
            if len(common)<c.min_points:continue
            errors=[abs(p['x']-previous[p['y']]['x']) for p in common]
            error=float(np.median(errors))
            if error>gate or max(errors)>gate*1.5:continue
            matches.append((error,candidate))
        matches.sort(key=lambda item:item[0])
        if not matches:return None,'no_continuous_role_match'
        if len(matches)>1 and matches[1][0]-matches[0][0]<c.role_margin_px:
            return None,'ambiguous_component_role'
        return dict(candidate=matches[0][1],median_edge_shift_px=matches[0][0],gate_px=gate),None

    def update(self,timestamp_ms,session_key,current_pairs,candidates,edge_jump=False):
        """只用当前双边／当前黑带和过去模型，输出独立predicted状态。

        已观测同一y双边时更新该行宽度；缺一侧时用当前可见内缘加减该
        行最近实测宽度。没有该行历史就不外推宽度。预测点保留画外坐标，
        不截成画内假边界；显示端可标“估计在画外”。没有真实时间、长
        断流、角色歧义或超过硬时限即不给预测。未知与预测都不算valid。
        """
        c=self.config
        output=dict(revision='v06-p1',state='unknown',estimated_pairs=[],estimated_centerline=[],
             observed_single_boundary=[],inferred_role=None,missing_role=None,model_age_max_ms=None,
             estimated_y120_px=None,estimated_deviation_px=None,uncertainty_px=None,
             reason=None,time_reset=None,assumption='finite_historical_width_at_same_image_row',
             control_ready=False,protocol_valid=False,full_turn_path_available=False)
        time_ok=(isinstance(timestamp_ms,(int,float)) and not isinstance(timestamp_ms,bool) and
                 math.isfinite(timestamp_ms) and timestamp_ms>=0 and session_key is not None)
        reason=None
        if not time_ok:reason='missing_real_capture_time'
        elif self.session!=session_key:reason='session_changed'
        elif self.last_ms is not None and timestamp_ms<=self.last_ms:reason='clock_not_increasing'
        elif self.last_ms is not None and timestamp_ms-self.last_ms>c.capture_gap_ms:reason='capture_gap_timeout'
        elif edge_jump:reason='C2_direct_edge_jump'
        if reason:self.reset();output['time_reset']=reason
        if not time_ok:output['reason']=reason;return output
        now=timestamp_ms;dt=now-self.last_ms if self.last_ms is not None else 0
        # 先保存当前实测，只有双边直接观测能刷新宽度时间。
        direct_rows={p['y'] for p in current_pairs}
        for p in current_pairs:
            self.widths[p['y']]=dict(width=p['right']-p['left'],ms=now)
            for side in ('left','right'):self.roles[side][p['y']]=dict(x=p[side],ms=now)
        self.widths={y:v for y,v in self.widths.items() if now-v['ms']<=c.max_width_age_ms}
        matched={};failures={}
        for side in ('left','right'):
            matched[side],failures[side]=self._associate(candidates,side,now,dt)
        if all(matched.values()) and matched['left']['candidate']['component']==matched['right']['candidate']['component']:
            matched={'left':None,'right':None};failures={'left':'same_band_two_faces','right':'same_band_two_faces'}
        by_role={side:{p['y']:p['x'] for p in item['candidate']['points']} if item else {}
                 for side,item in matched.items()}
        estimates=[];visible=[];used_roles=set()
        for y,model in sorted(self.widths.items()):
            if y in direct_rows:continue
            roles=[s for s in ('left','right') if y in by_role[s]]
            if len(roles)!=1:continue
            side=roles[0];other='right' if side=='left' else 'left';x=by_role[side][y]
            width=model['width'];missing=x+width if side=='left' else x-width
            left,right=(x,missing) if side=='left' else (missing,x)
            if not 55<=right-left<=300:continue
            age=now-model['ms'];uncertainty=c.base_uncertainty_px+c.uncertainty_growth_px_s*age/1000
            estimates.append(dict(y=y,left=float(left),right=float(right),observed_role=side,
                  estimated_role=other,model_age_ms=age,width_source_ms=model['ms'],
                  uncertainty_px=uncertainty,estimated_edge_in_image=0<=missing<=319))
            visible.append(dict(y=y,x=x,role=side,component=matched[side]['candidate']['component']))
            used_roles.add(side)
        # 每个连续区间至少6行和25px，禁止把零散印字锚点串成预测路径。
        blocks=[];block=[]
        for p in estimates:
            if block and (p['y']-block[-1]['y']>15 or p['observed_role']!=block[-1]['observed_role']):
                blocks.append(block);block=[]
            block.append(p)
        if block:blocks.append(block)
        accepted=[p for block in blocks if len(block)>=c.min_points and
                  block[-1]['y']-block[0]['y']>=c.min_span_px for p in block]
        if accepted:
            accepted_rows={p['y'] for p in accepted}
            roles={p['observed_role'] for p in accepted}
            if len(roles)==1:
                side=next(iter(roles))
                output.update(state='historical_geometry_prediction',estimated_pairs=accepted,
                  estimated_centerline=[dict(x=(p['left']+p['right'])/2,y=p['y']) for p in accepted],
                  observed_single_boundary=[p for p in visible if p['y'] in accepted_rows],
                  inferred_role=side,missing_role='right' if side=='left' else 'left',
                  model_age_max_ms=max(p['model_age_ms'] for p in accepted),
                  uncertainty_px=max(p['uncertainty_px'] for p in accepted))
                reference=next((p for p in accepted if p['y']==120),None)
                if reference:
                    output['estimated_y120_px']=(reference['left']+reference['right'])/2
                    output['estimated_deviation_px']=output['estimated_y120_px']-159.5
            else:output['reason']='mixed_side_role_blocks'
        if output['state']=='unknown':
            output['reason']=output['reason'] or ('current_direct_observation' if current_pairs else
                 ('no_unexpired_width_model' if not self.widths else 'role_or_support_insufficient'))
        # 当前被连续关联的可见边只更新角色位置，不刷新另一侧／路宽年龄。
        for side,item in matched.items():
            if item:
                for p in item['candidate']['points']:
                    if p['y'] in self.widths:self.roles[side][p['y']]=dict(x=p['x'],ms=now)
        self.session=session_key;self.last_ms=now
        return output
