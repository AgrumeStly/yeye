"""BP1可移植灰度诊断核，只使用Python基础类型，不依赖OpenCV／NumPy。

该核仅迁移固定参考行周围的黑段／双边几何诊断；没有C2全图连通域与
双侧转角验证，也没有F1终点模块。因此diagnostic_valid绝不能当协议
PATH_VALID；顶层valid始终False。用于先测API、内存、时延和像素符号，
不是完整识别替代，也不是可上车轨迹。输入缓冲只读，不留前帧图像。
"""


def _median(values):
    """短灰度序列中位数；偶数时取中间两数平均，仅用于诊断阈值。"""
    ordered=sorted(values);n=len(ordered)
    return ordered[n//2] if n%2 else (ordered[n//2-1]+ordered[n//2])/2


def _threshold(pixels):
    """ROI每4列／5行采样直方图，计算大津与65百分位上限。

    与电脑R1全ROI阈值不同，必须在回归表单独比较，不能称逐像素等价。
    最多2480次缓冲读取及256次阈值循环，不复制完整图像。
    """
    hist=[0]*256
    for y in range(65,216,5):
        for x in range(0,320,4):hist[pixels[y*320+x]]+=1
    total=sum(hist);total_sum=sum(i*count for i,count in enumerate(hist))
    lower_count=0;lower_sum=0;best=-1;otsu=0;percentile=255;seen=0
    for i,count in enumerate(hist):
        seen+=count
        if seen>=total*.65 and percentile==255:percentile=i
        lower_count+=count;lower_sum+=i*count
        upper_count=total-lower_count
        if lower_count and upper_count:
            between=(lower_sum/lower_count-(total_sum-lower_sum)/upper_count)**2*lower_count*upper_count
            if between>best:best=between;otsu=i
    return max(20,min(100,otsu,percentile-18))


def detect_gray(pixels,width=320,height=240):
    """输入连续单通道uint8缓冲，320×240／76800字节；所有坐标像素。

    每5行取三行中值；黑段3..55px、白内侧对比≥12灰度级、两条实际
    黑段之间55..300px且白内部；多解不强选，最多两行中断、有限斜移。
    至少6行／25px、透视增长≥0.2且覆盖y120才给诊断偏差。未扫描二维
    连通域，不能证明两段属于不同道路边界；所有结果保持诊断身份。
    """
    output=dict(revision='board-probe-bp1',valid=False,quality=0.,diagnostic_valid=False,
                deviation_px=None,deviation_normalized=None,reference_y=120,pair_samples=[],
                threshold=None,reason='diagnostic_subset_not_C2',control_ready=False,
                full_turn_path_available=False,finish_state='not_ported')
    if width!=320 or height!=240 or pixels is None or len(pixels)!=76800:
        output['reason']='unsupported_gray_buffer';return output
    threshold=_threshold(pixels);output['threshold']=threshold
    best=[];chain=[];missing_rows=0
    for y in range(65,216,5):
        profile=bytearray(320)
        for x in range(320):
            a=pixels[(y-1)*320+x];b=pixels[y*320+x];c=pixels[(y+1)*320+x]
            profile[x]=a+b+c-min(a,b,c)-max(a,b,c)
        runs=[];start=None
        for x in range(321):
            dark=x<320 and profile[x]<=threshold
            if dark and start is None:start=x
            if not dark and start is not None:
                end=x-1
                if 3<=end-start+1<=55:
                    value=_median(profile[start:end+1])
                    lc=_median(profile[max(0,start-8):start])-value if start>3 else -1
                    rc=_median(profile[end+1:min(320,end+9)])-value if end<316 else -1
                    if max(lc,rc)>=12:runs.append((start,end,lc,rc))
                start=None
        # 复杂文字行直接拒绝，限制每行最多8条黑段，避免组合数失控。
        pairs=[]
        if len(runs)<=8:
            for i,left in enumerate(runs):
                for right in runs[i+1:]:
                    lx,rx=left[1],right[0]
                    if not 3<lx<rx<316 or not 55<=rx-lx<=300 or min(left[3],right[2])<12:continue
                    if sum(v<=threshold for v in profile[lx+2:rx-1])/max(1,rx-lx-3)>.08:continue
                    pairs.append(dict(y=y,left=lx,right=rx))
        if len(pairs)!=1:
            missing_rows+=1
            if missing_rows>2:
                if len(chain)>len(best):best=chain
                chain=[]
            continue
        pair=pairs[0]
        if chain and (pair['y']-chain[-1]['y']>15 or max(abs(pair[s]-chain[-1][s]) for s in ('left','right'))>2.8*(pair['y']-chain[-1]['y'])+3):
            if len(chain)>len(best):best=chain
            chain=[]
        chain.append(pair);missing_rows=0
    if len(chain)>len(best):best=chain
    output['pair_samples']=best
    if len(best)<6 or best[-1]['y']-best[0]['y']<25:return output
    ys=[p['y'] for p in best];widths=[p['right']-p['left'] for p in best]
    mean_y=sum(ys)/len(ys);mean_width=sum(widths)/len(widths)
    growth=sum((y-mean_y)*(w-mean_width) for y,w in zip(ys,widths))/sum((y-mean_y)**2 for y in ys)
    density=len(best)/((ys[-1]-ys[0])/5+1)
    quality=min(1.,len(best)/12)*density
    if growth<.2 or quality<.45 or not ys[0]<=120<=ys[-1]:return output
    upper=max((p for p in best if p['y']<=120),key=lambda p:p['y'])
    lower=min((p for p in best if p['y']>=120),key=lambda p:p['y'])
    if lower['y']-upper['y']>15:return output
    middle_a=(upper['left']+upper['right'])/2;middle_b=(lower['left']+lower['right'])/2
    middle=middle_a if upper['y']==lower['y'] else middle_a+(middle_b-middle_a)*(120-upper['y'])/(lower['y']-upper['y'])
    deviation=middle-159.5
    output.update(diagnostic_valid=True,deviation_px=deviation,
                  deviation_normalized=max(-1000,min(1000,round(deviation/159.5*1000))),quality=quality)
    return output
