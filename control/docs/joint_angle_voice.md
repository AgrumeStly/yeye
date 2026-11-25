# 起点直道、左侧直角弯和钝角弯

联合版配对为 STM32 **JointAngleVoice `0x02120017`** 与 K230 **v11**。按比赛图 1 顺时针行驶，从虚线起点驶向赛道左侧，两次均右转。直角转向 90°。钝角处约 141° 的车道内角对应约 39° 的车头转角，按图 1 估算。 [比赛原文](../../competition/比赛文档.pdf)

## 赛车线和轮速

`1992776093.mp4` 的约 5–8 秒抽帧中，v9 已驶出直角弯，车靠近出口外侧黑边。联合版将名义外偏从 5 降到 2 个投影代理单位，第一弯出口与第二弯入口以相同偏置相切。圆弧半径上限分别为 30 和 58。计算还以车道半宽 25、线路到最近边界最小距离 21 作为几何约束，限制圆弧靠近内角的程度。该值用于给车身和跟踪误差留余量，车头投影、实际车体扫掠和视频中的物理间距仍待测。 [主控视频](../../1992776093.mp4) [赛车线算法](../../vision/src/right_angle_racing.py)

双边可靠时，直道共同轮速目标由 80 提到 **100 RPM**。直角弯按当前入弯距离降至约 60 RPM，钝角弯内名义约 73 RPM，单轮目标上限仍为 112 RPM。当前多行重测到同一条直道边且白走廊支持当前路线时，按 62 RPM 续行，实测单边逐帧更新自己的 240 ms 期限。一般单侧关联仍按 50 RPM，短时白走廊 40 RPM。单帧模型未匹配且未明确看到预测路线被阻断时，等待下一帧，STM32 仍对最后一张实际源图执行 200 ms 监督。车辆通过钝角出口后以正常 STOP 结束本段，保留 40 秒总上限、实物 KEY（PA0／WKUP）急停、语音 Stop、确证路径阻断和轮速异常保护。

## 配对准备

1. 主控在 Keil5 用 **Project → Open Project** 打开 [joint_angle_voice.uvprojx](../MDK-ARM/joint_angle_voice.uvprojx)，选择 **JointAngleVoice**，使用 **Flash → Download**。配套固件已构建，输出目录为 `control/build/firmware/joint_angle_voice/`。沿用 CMSIS-DAP／SW 与 STM32F4xx 512 KB Flash 下载算法。
2. K230 使用 v11。语音模型及已有就绪／Stop 音频仍取板上资源。“收到”随 `main.py` 一起交付，程序上电预载；无需热点、手机或图传。如需重新生成，使用 `python vision/tools/prepare_right_angle_bundle.py --joint --output vision/build/joint_angle_voice_v11`，输出目录须用新路径。 [K230 装板回执](../../testing/2026-11-25_joint_angle_voice/v11_receipt.json)
3. 配对后，主控在虚线起点摆车，车头顺时针，听到“我在”、待机绿灯约每两秒亮 0.4 秒时，直接说 **Go**。视觉一识别便播放“收到”，随后以新鲜路径序号发 START。绿灯常亮表示跑动，连续快闪表示故障。车过钝角出口后以正常 STOP 结束本段。

v10 首跑实读为 5.999 秒 `LINK 2`。最后有效路径源图到停车约 71 ms，双轮有反馈，弱观测证据过期比持续断流更符合记录。赛段完成、用时、接触黑边次数、车身最小余量及 Go 到“收到”的实际延迟均待主控验收。后续归档可用 `/data/right_angle_logs/voice_NNNN.jsonl` 的 `road_section`、`confidence` 和 `previous_source_age_ms` 匹配视频及主板停车码。该段用于改善表 1 基本功能的时间与触线表现，语音应答对应额外功能。 [v10 冻结记录](../../testing/2026-11-25_joint_angle_voice/v10_first_stop_swd.json) [比赛原文](../../competition/比赛文档.pdf)
