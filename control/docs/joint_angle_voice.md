# 起点直道、左侧直角弯和钝角弯

联合版配对为 STM32 **JointAngleVoice `0x02120016`** 与 K230 **v10**。按比赛图 1 顺时针行驶，从虚线起点驶向赛道左侧，两次均右转。直角转向 90°。钝角处约 141° 的车道内角对应约 39° 的车头转角，按图 1 估算。 [比赛原文](../../competition/比赛文档.pdf)

## 赛车线和轮速

`1992776093.mp4` 的约 5–8 秒抽帧中，v9 已驶出直角弯，车靠近出口外侧黑边。联合版将名义外偏从 5 降到 2 个投影代理单位，第一弯出口与第二弯入口以相同偏置相切。圆弧半径上限分别为 30 和 58。计算还以车道半宽 25、线路到最近边界最小距离 21 作为几何约束，限制圆弧靠近内角的程度。该值用于给车身和跟踪误差留余量，车头投影、实际车体扫掠和视频中的物理间距仍待测。 [主控视频](../../1992776093.mp4) [赛车线算法](../../vision/src/right_angle_racing.py)

双边可靠时，直道共同轮速最高 80 RPM；直角弯按当前入弯距离约降至 60 RPM，钝角弯内名义约 69 RPM。只见当前外侧两臂时上限 60 RPM，只有当前已关联边线时上限 50 RPM，短时白走廊上限 40 RPM。直角出口的方向及侧向位置与钝角入弯线相符，并有两条弯臂的像素支持时，视觉才切换弯型。出口持续确认约 450 ms 后，视觉发送正常 STOP。40 秒是 STM32 总运行上限。实物 KEY（PA0／WKUP）急停、语音 Stop、200 ms 链路监督、路径撤销和轮速异常保护继续生效。

## 配对准备

1. 主控在 Keil5 用 **Project → Open Project** 打开 [joint_angle_voice.uvprojx](../MDK-ARM/joint_angle_voice.uvprojx)，选择 **JointAngleVoice**。准备下载时使用 **Project → Build Target** 和 **Flash → Download**，沿用 CMSIS-DAP／SW 与 STM32F4xx 512 KB Flash 下载算法。
2. 视觉使用 `python vision/tools/prepare_right_angle_bundle.py --joint --output vision/build/joint_angle_voice_v10` 生成配对 `main.py` 和哈希清单。输出目录须用新路径。自动安装条件具备时，先备份 K230 的 `/sdcard/main.py`，安装并读回联合版。语音模型及已有就绪／Stop 音频仍取板上资源。“收到”随 `main.py` 一起交付，程序上电预载；无需热点、手机或图传。
3. 配对后，主控在虚线起点摆车，车头顺时针，听到“我在”、待机绿灯约每两秒亮 0.4 秒时，直接说 **Go**。视觉一识别便播放“收到”，随后以新鲜路径序号发 START。绿灯常亮表示跑动，连续快闪表示故障。车过钝角出口后以正常 STOP 结束本段。

本轮只生成了 K230 配对文件，按主控要求没有执行功能测试、STM32 构建或实车跑动。赛段完成、用时、接触黑边次数、车身最小余量及 Go 到“收到”的实际延迟均待主控验收。后续归档可用 `/data/right_angle_logs/voice_NNNN.jsonl` 的 `road_section`、`confidence` 和 `previous_source_age_ms` 匹配视频及主板停车码。该段用于改善表 1 基本功能的时间与触线表现，语音应答对应额外功能。 [比赛原文](../../competition/比赛文档.pdf)
