# 左侧首弯语音试跑

**RightAngleVoice** 使用 `0x02120013` 固件与 K230 **v7** 自启动脚本。沿用 R8 的外入、圆弧切弯、外出，左右双边或左纵边与前横边构成的当前 L 形可提供起步许可。已确认的 L 形转到出口边时，当前像素仍有支持即可短时关联续行。路径无效、通信超龄、KEY 和轮速反馈保护仍由 STM32 监督。

## 安装与上道

1. 主控保持车辆静止并隔离驱动动力。Keil5 用 **Project → Open Project** 打开 [right_angle_voice.uvprojx](../MDK-ARM/right_angle_voice.uvprojx)，选 **RightAngleVoice**，用 **Flash → Download** 下载。沿用 CMSIS-DAP／SW 及 STM32F4xx 512 KB Flash 算法，工程产物位于 `control/build/firmware/right_angle_voice/`。
2. 视觉板使用 `vision/build/right_angle_voice/main.py`，装到 `/sdcard/main.py`，沿用板上语音直道使用的关键词模型和四份 WAV。2026-11-24 本机 COM10 已完成写入和读回校验，旧直道脚本已保存。之后用车载电池给两板供电并冷启动。
3. 主控在左侧首弯前的来向直道上摆车，车头顺时针。听完“我在”后稍等约 1 秒。绿灯每约 2 秒亮约 0.4 秒表示待机收到可起步的当前路径，直接说 **Go** 上道。约 0.08 秒短闪时先核对取景和固件配对。绿灯常亮为跑动，连续快闪为故障。
4. 观察车是否连贯右转并进入出弯直道、是否碰黑边、何时停止。语音 **Stop** 撤驱动，实物 **KEY**（PA0／WKUP）可急停。故障停车后先记录位置与灯态，保留取证现场。试跑最长 12 秒，正常运行时进入下一段仍须有当前视觉路径。

重建时可用以下命令，视觉输出目录需使用新路径。

```powershell
python control/tools/build_right_angle.py --voice
python vision/tools/prepare_right_angle_bundle.py --voice --output vision/build/right_angle_voice_new
```

## 查图和停车原因

K230 每次发出 Go 后先把逐帧时序、路径状态和原始灰度图放在内存。发送 Stop 或度过本次最长期限后写入 `/data/right_angle_logs/voice_NNNN.jsonl` 及配套 PGM。前后图用于定位首次无效或本地估计图像年龄达到 200ms 的时刻。正常线路照片按阶段改变或每秒留取，超过容量时保留最近 8 张。电脑连接 CanMV 会软重启，待车停稳、写入完成后再读文件。

原始日志的 `go_sent_ms` 表示 K230 发令时间。实际接受与停车看 STM32 的 `g_lap_last`、`g_lap_diag`，用 PATH 序号和转向字段与 K230 对时。LINK（2）是路径断流或超龄，PATH（3）是现帧撤许可，LIMIT（11）是限时，VOICE_STOP（12）是收到 Stop。断电或复位前保存主板记录。上道取证记录过弯时间、路径年龄峰值和触边现象。依据比赛第三部分、图 1 和表 1，结果支撑基本功能的完赛与触边判断、额外功能中的自主语音起步，以及报告中的路径与时序说明。 [比赛原文](../../competition/比赛文档.pdf)

停车后可用 [只读 SWD 工具](../tools/lap_swd_capture.py) 的 `--profile right-angle-voice`，先比对实际 Flash 与配套 BIN，再读取冻结环与停车记录。
