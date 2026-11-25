# 起点直道、左侧直角弯和钝角弯

联合版配对为 STM32 **JointAngleVoice `0x02120018`** 与 K230 **v12**。按比赛图 1 顺时针行驶，从虚线起点驶向赛道左侧，两次均右转。直角转向 90°。钝角处约 141° 的车道内角对应约 39° 的车头转角，按图 1 估算。 [比赛原文](../../competition/比赛文档.pdf)

## 赛车线和轮速

直道近中区复用 StraightVoice 的当前双边拟合及 STM32 直道控制，使用旧算法的采样行，直接计算车头与车道的横偏和方向。远区每约 70 ms 抽样判断前方是否出现折角迹象。双边稳定时只有远区提示才进入完整弯道搜索。出现遮挡或近中区不再满足直道约束时，再以完整网格复核当前边线。实际当前弯臂与入口方向一致后，才根据前视点进入赛车线。设计参考近区纠偏、远区预瞄以及目标点曲率跟踪。 [近远区视觉研究](https://www.cs.drexel.edu/~dds26/publications/Salvucci-Perc04.pdf) [Coulter 路径跟踪](https://www.ri.cmu.edu/publication_view.html?pub_id=278)

首弯沿用实际通过过弯的 v9 圆弧，半径 30、外偏 5 个投影代理单位。联络直道采用偏置 2，随车头观测和平滑差速接入钝角的圆弧，钝角半径上限 58。钝角计算以车道半宽 25、线路到最近边界最小距离 21 作为几何约束。实际车体扫掠和物理间距待实车确认。 [v9 实跑参数](../../testing/2026-11-18_right_angle/voice_v9_pass_baseline/parameters.md) [赛车线算法](../../vision/src/right_angle_racing.py)

双边可靠时，直道共同轮速目标由 80 提到 **100 RPM**。直角弯按当前入弯距离降至约 60 RPM，钝角弯内名义约 73 RPM，单轮目标上限仍为 112 RPM。当前多行重测到同一条直道边且白走廊支持当前路线时，按 62 RPM 续行，实测单边逐帧更新自己的 240 ms 期限。一般单侧关联仍按 50 RPM，短时白走廊 40 RPM。单帧模型未匹配且未明确看到预测路线被阻断时，等待下一帧，STM32 仍对最后一张实际源图执行 200 ms 监督。车辆通过钝角出口后以正常 STOP 结束本段，保留 40 秒总上限、实物 KEY（PA0／WKUP）急停、语音 Stop、确证路径阻断和轮速异常保护。

## 配对准备

1. 主控在 Keil5 用 **Project → Open Project** 打开 [joint_angle_voice.uvprojx](../MDK-ARM/joint_angle_voice.uvprojx)，选择 **JointAngleVoice**，使用 **Flash → Download**。配套固件已构建，输出目录为 `control/build/firmware/joint_angle_voice/`。沿用 CMSIS-DAP／SW 与 STM32F4xx 512 KB Flash 下载算法。
2. K230 使用 v12 右单边兼容修订。该修订只改变 K230 的右向像素扫描，沿用 STM32 `0x02120018`。语音模型及已有就绪／Stop 音频仍取板上资源。“收到”随 `main.py` 一起交付，程序上电预载；无需热点、手机或图传。如需重新生成，使用 `python vision/tools/prepare_right_angle_bundle.py --joint --output vision/build/joint_angle_voice_v12_rail_fix`，输出目录须用新路径。 [K230 装板回执](../../testing/2026-11-25_joint_angle_voice/v12_rail_fix_receipt.json)
3. 配对后，主控在虚线起点摆车，车头顺时针，听到“我在”、待机绿灯约每两秒亮 0.4 秒时，直接说 **Go**。视觉一识别便播放“收到”，随后以新鲜路径序号发 START。绿灯常亮表示跑动，连续快闪表示故障。车过钝角出口后以正常 STOP 结束本段。

K230 日志在 `/data/right_angle_logs/voice_NNNN.jsonl`，记录处理分区、候选数、支持格数、发送与跳过、置信度、前帧源年龄和脚本退出异常。STM32 `g_joint_stop` 留存停车瞬间的路径序号、标志、置信度、处理耗时和各类证据年龄，配合原轮速／PWM 冻结环。实车验收观察区段用时、接触黑边次数、最小车体余量及 Go 应答延迟。该段用于改善表 1 基本功能的时间与触线表现，语音应答对应额外功能。 [v11 停车位置](../../testing/2026-11-25_joint_angle_voice/v11_stop_position.png) [比赛原文](../../competition/比赛文档.pdf)
