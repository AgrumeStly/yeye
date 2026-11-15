# 最终安装向右平移组：完整性与左右方向比较

日期：2026-11-08。任务：V-03第3组／5组。主控执行现场采集，本对话校验原件、逐张查看图像并回放冻结R1。输入`vision/data/captures/final_mount_20261108/v03_offset_right_0001/`，原件未修改。

现场指导为从原居中位置向车辆右侧平移约5cm、车头方向不变。标签offset_right为脚本配置，实际位移和偏航未独立测量，不作精确厘米标定。

## 命令与验证结果

```powershell
vision/.venv/Scripts/python.exe vision/tools/verify_capture.py vision/data/captures/final_mount_20261108/v03_offset_right_0001
vision/.venv/Scripts/python.exe vision/tools/replay_offline.py --input vision/data/captures/final_mount_20261108/v03_offset_right_0001 --output vision/build/final_mount_20261108/v03_offset_right_0001_r1 --headless
```

两条命令退出0。完整性passed=true，3张实际320×240灰度JPEG，哈希与日志一致，session为complete，saved_count=3，无cleanup_errors。回放3帧有效，无读取失败，3张叠加及3帧视频解码通过。算法、回放与校验器源码哈希与居中组相同，参数JSON字节也相同，未调阈值／ROI／参考行／安装。

关键证据：[validation.json](validation.json)、[参数](parameters.json)、[逐帧结果](frames.jsonl)、[统计](summary.json)，以及已逐张查看的[叠加1](overlays/data_0001.png)、[叠加2](overlays/data_0002.png)、[叠加3](overlays/data_0003.png)。完整派生物在上述vision/build目录，被Git忽略，未上传。

## 图像与偏差

3张原图无先前尺子。参考行处两条边界内缘均可见，叠加贴合朝向白路面的内缘；近处左边界部分出画，算法不将图像边框当内缘。双边支持为y65..195，y120仍在支持范围内。y65／80／100／120／140的算法坐标保存在validation.json，不能称为独立人工真值。3帧y120左内缘x=55、右内缘x=215，中点x=135，dx=135−159.5=−24.5px，归一化−154。质量1.0是启发式分值，不是正确概率。

| 场景 | 3帧y120偏差（像素，图像右正） | 双边支持y范围 |
| --- | --- | --- |
| 居中 | 0／0／0 | 65..215 |
| 整车左移 | +27／+27.5／+27.5 | 65..180 |
| 整车右移 | −24.5／−24.5／−24.5 | 65..195 |

当前三组支持“整车左移时道路中心偏向图像右侧，整车右移时偏向图像左侧”。两侧幅度不完全相等，实际摆位与微小偏航未独立测量，不由此推断镜头畸变、车体机械误差或控制增益。不能据两侧数值建立像素到厘米换算，也不能据图像偏差直接认定转向执行器符号。

## 当前进度与下一步

累计9／15张，3种平移姿态已取得，左右偏航待验。下一项：主控保持电机动力断开，将车体中心回原居中位置，再围绕车体中心附近让整车车头向左小幅偏转，目标约5°，尽量不平移。相机相对车身固定，采POSE=heading_left的3张。角度未测量就记近似／定性；之后采居中右偏航组，继续保持原安装与R1默认参数。

比赛关联：支撑基本功能60分的偏差方向正确性、可靠完赛与减少触边，以及报告20分的可核查证据。3组静态有效不等于识别准确率、距离／航向标定或整车验收；官方色块间隙、锐角、终点、动态及真实跑圈待验，旧应用清理未执行。
