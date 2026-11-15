# 最终安装左偏航组：视场与单行偏差限制

日期：2026-11-08。任务：V-03第4组／5组。主控按前序指导保持车体中心居中、车头向左小幅偏转约5°采3张；实际角度、平移残差未独立测量，只记定性／近似。标签heading_left来自脚本配置，不是视觉测量的航向角。

原件`vision/data/captures/final_mount_20261108/v03_heading_left_0001/`保持只读。执行：

```powershell
vision/.venv/Scripts/python.exe vision/tools/verify_capture.py vision/data/captures/final_mount_20261108/v03_heading_left_0001
vision/.venv/Scripts/python.exe vision/tools/replay_offline.py --input vision/data/captures/final_mount_20261108/v03_heading_left_0001 --output vision/build/final_mount_20261108/v03_heading_left_0001_r1 --headless
```

两项退出0。完整性passed=true，3张320×240灰度JPEG、实际哈希与日志一致、session complete、saved_count=3、cleanup_errors为空。R1源码／回放器／校验器哈希与居中组相同，参数JSON字节相同；未调阈值、ROI、参考行或安装。回放3帧有效，无读取失败，3张叠加及视频3帧重新解码通过。

证据：[validation.json](validation.json)、[参数](parameters.json)、[逐帧结果](frames.jsonl)、[统计](summary.json)，以及逐张查看的[叠加1](overlays/data_0001.png)、[叠加2](overlays/data_0002.png)、[叠加3](overlays/data_0003.png)。已查看3张原图，尺子未出现。完整派生物保留vision/build中的上述路径，Git忽略，未上传。

参考行y120两侧道路内缘均可见，叠加贴合；左内缘x=109、右内缘x=274，中点191.5，3帧dx均+32px、归一化+201。双边观测支持y65..195，近处右边界部分出画，算法未用图像边框充当缺失内缘。抽样行y65／80／100／120／140坐标见validation.json，均为算法输出，不冒充独立人工标注。quality=1为启发式分值，不是准确概率。

与居中0、左移+27..+27.5、右移−24.5相比，左偏航也使当前参考行中点偏向图像右方，符合车头左偏的定性变化。单行偏差同时受横向位置与朝向影响，无法单凭+32推定横向厘米数或真实航向角；本次不下发控制、不改变协议或主控参数。车辆左偏航标签也不直接定义物理航向正负号。

目前累计12／15张。下一组保持车体中心原居中位置，先将车头回到平行道路，再使整车车头向右小幅偏转约5°，尽量不平移，相机相对车身固定。POSE=heading_right采3张并下载；角度未测就记近似。电机动力保持断开，车体须留边界余量。

比赛关联：支撑基本功能60分的朝向变化下视场／偏差检查与少触边、可靠完赛，保存报告20分证据。尚未完成全部五姿态，也未验证官方色块、锐角、终点、动态模糊或整车跑圈，不预测得分。
