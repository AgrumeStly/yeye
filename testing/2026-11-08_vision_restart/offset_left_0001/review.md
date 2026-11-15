# 最终安装向左平移组：完整性与偏差变化

日期：2026-11-08。任务：V-03第2组／5组。主控按前序指导采集，本对话检查原图、文件与冻结R1结果。本组3张静态图不能替代动态或总体准确率验证。

输入为`vision/data/captures/final_mount_20261108/v03_offset_left_0001/`。姿态标签offset_left来自脚本设置，现场指导为从原居中位向车辆左侧平移约5cm、方向不变；实际位移与偏航未独立测量，不作厘米标定。元数据及图像格式与居中组相同，旧原件保持只读。

执行命令：

```powershell
vision/.venv/Scripts/python.exe vision/tools/verify_capture.py vision/data/captures/final_mount_20261108/v03_offset_left_0001
vision/.venv/Scripts/python.exe vision/tools/replay_offline.py --input vision/data/captures/final_mount_20261108/v03_offset_left_0001 --output vision/build/final_mount_20261108/v03_offset_left_0001_r1 --headless
```

两项退出0：verify报告passed=true、3张320×240灰度JPEG、哈希与日志一致，session为complete、saved_count=3、cleanup_errors为空。回放3帧有效、无读取失败、3张叠加及3帧视频重新解码通过；quality=1是启发式评分，不是正确概率。关键输出为[参数](parameters.json)、[逐帧结果](frames.jsonl)、[统计](summary.json)、[哈希与参考行检查](validation.json)。完整派生物在上述vision/build目录，被Git忽略，未上传。

冻结算法、回放脚本、校验器源码哈希与居中组相同，参数JSON字节相同；未为本组调阈值、ROI、参考行或安装。采集脚本只按姿态切换POSE。

逐张看过3张原图与[叠加1](overlays/data_0001.png)、[叠加2](overlays/data_0002.png)、[叠加3](overlays/data_0003.png)。两条朝向白色道路的真实内缘在参考行附近可见，叠加基本贴合；近处右侧边界部分出画，不将画面边框当成道路内缘，也不补出缺失边界。双边支持范围从居中组y65..215缩为y65..180，但y120仍包含在观测范围内。y65／80／100／120／140各抽样行坐标见validation.json，均为算法输出，不冒充独立人工标注。

| 帧 | y120左内缘x | 右内缘x | 中点x | dx像素（图像右正） | 归一化值 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 107 | 266 | 186.5 | +27.0 | +169 |
| 2 | 107 | 267 | 187.0 | +27.5 | +172 |
| 3 | 107 | 267 | 187.0 | +27.5 | +172 |

对比居中组的dx=0：本组道路中点移向图像右侧，与前序要求的整车向左平移相符。此为当前姿态样本对图像符号关系的支持，仍需右移组和两组偏航交叉核对；不能推导转向执行器符号、真实航向角或每像素对应厘米数。没有发送任何控制命令。

当前累计核查6／15张。先保持当前相机安装与算法。下一组从原居中位置向车辆右侧约5cm（从当前左偏位到右偏位总共约向右10cm，不能只右移5cm停在居中），方向与原直道平行；POSE=offset_right采3张并下载完整会话到同一父目录。实际5cm若仅估计须记近似，车体须保持边界余量。之后再分别采居中左偏航、居中右偏航。

该检查支撑比赛基本功能60分的偏差符号正确性、少触边与可靠完赛，并为报告20分提供可追溯依据。当前仍是连续黑条静态场景；官方色块、锐角、起终点、动态、距离映射及整车运行未验，不预测得分。
