"""绘制当前L1模型与原图的工程审核页；只画真实投影范围，不夹造边界。"""
import argparse
import json
from pathlib import Path
import cv2
import numpy as np


def project(x,z):
    if z<=2: return None
    y=(7802.22222222222-38.11111111111108*z)/(z+15.555555555555546)
    px=159.5+x*(y+38.11111111111108)/48.
    if 0<=px<320 and 0<=y<240: return round(px),round(y)
    return None


def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--output',required=True)
    p.add_argument('--session',default='push_full_lap_0001'); args=p.parse_args()
    rows=[json.loads(x) for x in Path(args.input).read_text(encoding='utf-8').splitlines()]
    output=Path(args.output); output.mkdir(parents=True,exist_ok=False)
    source=Path('vision/data/captures/final_mount_20261108')/args.session
    video=cv2.VideoWriter(str(output/'l1_preview.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),10,(640,520))
    frames=[]
    for index,row in enumerate(rows):
        gray=cv2.imread(str(source/row['file']),0); color=cv2.cvtColor(gray,cv2.COLOR_GRAY2BGR)
        points=[project(*point) for point in row['route']]
        for a,b in zip(points,points[1:]):
            if a is not None and b is not None: cv2.line(color,a,b,(0,220,255),2)
        for point in points:
            if point is not None: cv2.circle(color,point,3,(0,220,255),-1)
        canvas=np.zeros((520,640,3),np.uint8); canvas[:480]=cv2.resize(color,(640,480))
        text=f"{index+1} {row['source']} steer={row['steering']} valid={row['valid']}"
        cv2.putText(canvas,text,(5,502),cv2.FONT_HERSHEY_SIMPLEX,.48,(255,255,255),1)
        video.write(canvas)
        if index%12==0 or (index>0 and row['source']!=rows[index-1]['source']): frames.append(canvas)
    video.release()
    for page in range(0,len(frames),12):
        sheet=np.zeros((520*3,640*4,3),np.uint8)
        for j,frame in enumerate(frames[page:page+12]): sheet[j//4*520:(j//4+1)*520,j%4*640:(j%4+1)*640]=frame
        cv2.imwrite(str(output/f'page_{page//12:02d}.jpg'),sheet)
    print('review pages',(len(frames)+11)//12,'video uses 10Hz display only; source acquisition rate unchanged')


if __name__=='__main__': main()
