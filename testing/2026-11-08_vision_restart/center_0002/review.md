# 最终安装居中3张：文件校验与冻结R1检查

日期：2026-11-08。任务：V-04首次完整采集校验，V-03五姿态中的居中组。主控执行现场采样，本对话检查下载原件及离线回放。此处结论只适用这3张静态原图。

## 输入及完整性

原件：`vision/data/captures/final_mount_20261108/v03_center_0002/`，3张JPEG、session.json、frames.jsonl，共5个文件。文件哈希、字节数、源码哈希、抽样行坐标见[validation.json](validation.json)。原件未修改。

运行：

```powershell
vision/.venv/Scripts/python.exe vision/tools/verify_capture.py vision/data/captures/final_mount_20261108/v03_center_0002
vision/.venv/Scripts/python.exe vision/tools/replay_offline.py --input vision/data/captures/final_mount_20261108/v03_center_0002 --output vision/build/final_mount_20261108/v03_center_0002_r1 --headless
```

两条命令退出0。校验passed=true、frames=3，实际JPEG均为320×240单通道uint8。会话version=capture-canmv-2，state=complete，saved_count=requested_count=3，cleanup_errors为空。实际图像哈希均与板载逐帧日志一致。记录的snapshot结束时刻间隔为507／508ms，snapshot调用耗时16／16／14ms；这些是软件边界时间，不是曝光时刻、真实固定帧率或控制延迟。

姿态标签center来自脚本设置，按前序居中摆正指导采集，未独立测量实际横向偏差或偏航。主控报告安装离地约20cm、角度约50°、最近能见车头前方约15cm；角度基准与逐行距离未核实，session中高度／角度仍为null。原图中已无先前尺子。

## 原图与检测检查

逐张看过3张原图及[叠加1](overlays/data_0001.png)、[叠加2](overlays/data_0002.png)、[叠加3](overlays/data_0003.png)。3张构图近似，双侧黑条可见；叠加左右边界贴合朝向白色道路的内缘，未将场外纹理或同一黑条两侧作为道路双边。远处弯折位于上方，本次不验收完整转角进出。

冻结R1源码与默认参数未修改，保存[parameters.json](parameters.json)、[frames.jsonl](frames.jsonl)、[summary.json](summary.json)。3帧valid=true，quality=1.0；quality为算法启发式分值，不是正确概率。y65..215有连续双边支持，y120包含在观测范围内。抽样行在3帧中一致，以下均为算法坐标，不是独立人工标注真值：

| 图像行y | 左内缘x | 右内缘x | 中点x |
| ---: | ---: | ---: | ---: |
| 65 | 109 | 205 | 157 |
| 80 | 101 | 214 | 157.5 |
| 100 | 91 | 226 | 158.5 |
| 120 | 80 | 239 | 159.5 |
| 140 | 70 | 251 | 160.5 |

因此3帧在y120的dx均为0px，归一化偏差为0。图像中线会随y略变，不据此宣布相机零偏航或车辆精确位于道路中心。不能用这3张近似静止帧计算泛化准确率；结果仅支持当前居中视场下参考行有真实双边和可用中点。

视频3帧重新解码通过。人为播放速度10fps，不作采集帧率；电脑detect均值约43.51ms，也不代表K230D速度。完整派生物留`vision/build/final_mount_20261108/v03_center_0002_r1/`，该路径被Git忽略；本目录保存可复核的关键输出，尚未上传。

## 验收边界和下一步

V-04的取图、预览、保存、下载与文件完整性链路已有本组实际证据；旧应用清理仍未执行，不将整个视觉重启视为完成。V-03当前仅取得居中3／15张，左右平移和左右偏航均待采；保留现有安装、R1观察行及算法参数，不急于修改控制算法。

下一组：主控保持电机动力断开，从当前居中参考位置将整车向车辆左侧平移约5cm，车头朝向不变、相机不单独转动，保证车体仍有边界余量；以POSE=offset_left采3张，下载新完整会话到final_mount_20261108父目录。5cm是队内采样起点，实际若只估计就记录近似，不编造精确位移。之后结合人工场景与图像中点检查符号，不先预设实际镜像关系。

此步骤支撑比赛基本功能60分中的少触边／可靠完赛，并为报告20分提供证据。当前仅连续黑条直道场景；官方5cm黑色色块、锐角、起终点线、动态模糊、整车投影及真实跑圈仍未验收，不预测得分或下发运动命令。
