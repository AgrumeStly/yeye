# 左侧首弯语音试跑

**RightAngleVoice** 使用 `0x02120014` 固件与 K230 **v8** 自启动脚本。走线沿用 R8 的外入、圆弧切弯、外出。绿灯就绪、主控说 Go 后按图像证据选择路线。

| 手机画面 | 路线来源 | 共同轮速参考上限 |
| --- | --- | --- |
| PAIR | 当前双边，走已确认的双边路线 | 80 RPM，随曲率减速 |
| L CORNER | 当前左纵边和前横边直接拟合折角，计算右转圆弧 | 60 RPM |
| ONE EDGE | 当前单边校正朝向与位置，沿最近可信弯道模型续行 | 50 RPM |
| SHORT PRED | 当前白走廊仍支持最近预测线，短时降低速度继续 | 40 RPM |

单边最多使用 1200ms 内的双边或 L 形锚点。短预测还要求 240ms 内有实测边线且当前预计经过的位置保持白色。两板独立监督，弱预测无法起步，路径阻断、来源超龄、KEY 和轮速反馈仍受保护。

## 安装与上道

1. 主控保持车辆静止并隔离驱动动力。Keil5 用 **Project → Open Project** 打开 [right_angle_voice.uvprojx](../MDK-ARM/right_angle_voice.uvprojx)，选 **RightAngleVoice**，用 **Flash → Download** 下载。沿用 CMSIS-DAP／SW 及 STM32F4xx 512 KB Flash 算法，工程产物位于 `control/build/firmware/right_angle_voice/`。
2. 执行对话按 [默认部署规则](../../AGENTS.md#视觉板默认部署) 安装视觉程序。COM10 已将 `vision/build/right_angle_voice_v8_fast_preview/main.py` 装入 `/sdcard/main.py`，逐字节读回一致。板上沿用现有关键词模型和四份 WAV。主控开队友原热点，退出 IDE、断开下载器和 USB，用车载电池给两板供电并冷启动。
3. 主控在左侧首弯前的来向直道上摆车，车头顺时针。听完“我在”后稍等约 1 秒。绿灯每约 2 秒亮约 0.4 秒表示待机收到可起步的当前路径，直接说 **Go** 上道。约 0.08 秒短闪时先核对取景和固件配对。绿灯常亮为跑动，连续快闪为故障。
4. 观察车是否连贯右转并进入出弯直道、是否碰黑边、何时停止。语音 **Stop** 撤驱动，实物 **KEY**（PA0／WKUP）可急停。故障停车后先记录位置与灯态，保留取证现场。试跑最长 12 秒，正常运行时进入下一段仍须有当前视觉路径。

重建时可用以下命令，视觉输出目录需使用新路径。

```powershell
python control/tools/build_right_angle.py --voice
python vision/tools/prepare_right_angle_bundle.py --voice --output vision/build/right_angle_voice_new
```

## 手机实时看图

手机与 K230 在队友原热点的同一网络。浏览器打开 K230 的 IP 和端口 `8080`，例如 `http://192.168.1.123:8080/`。实际 IP 查热点已连接设备列表，或查 K230 启动终端的 `[PHONE]` 行。画面叠加同一帧的推荐路线、阶段、置信度、UART 序号、转向和许可。首页可旋转画面。

手机流沿用队友的 MJPEG 形式，使用控车同一次采样。先发路径和处理口令，再非阻塞发图。JPEG 间隔至少 83ms，单次最多发送 8192 字节。等待 Go 时按间隔更新；Go 命中后的下一帧优先完成发令，跑动窗口仍按时序预算跳过耗时帧。网络慢时丢弃预览连接。实际帧率随板上计算、无线状况而变。热点凭据存于板上的 `/sdcard/right_angle_wifi.json`。替换热点时由主控更新板上配置。比赛评分跑使用车载自主循迹与语音，按场地条款关闭研发图传，可将该配置的 `enabled` 设置为 `false`。 [比赛原文](../../competition/比赛文档.pdf)

## 查图和停车原因

K230 每次发出 Go 后先把逐帧时序、路径状态和原始灰度图放在内存。发送 Stop 或度过本次最长期限后写入 `/data/right_angle_logs/voice_NNNN.jsonl` 及配套 PGM。前后图用于定位首次无效或本地估计图像年龄达到 200ms 的时刻。正常线路照片按阶段改变或每秒留取，超过容量时保留最近 8 张。电脑连接 CanMV 会软重启，待车停稳、写入完成后再读文件。

原始日志的 `go_sent_ms` 表示 K230 发令时间。实际接受与停车看 STM32 的 `g_lap_last`、`g_lap_diag`，用 PATH 序号和转向字段与 K230 对时。LINK（2）是路径断流、帧或预测证据超龄，PATH（3）是现帧撤许可，LIMIT（11）是限时，VOICE_STOP（12）是收到 Stop。断电或复位前保存主板记录。上道取证记录过弯时间、路径年龄峰值、触边和手机图传耗时。依据比赛第三部分、图 1 和表 1，结果支撑基本功能的完赛与触边判断、额外功能中的自主语音起步，以及报告中的路径与时序说明。 [比赛原文](../../competition/比赛文档.pdf)

停车后可用 [只读 SWD 工具](../tools/lap_swd_capture.py) 的 `--profile right-angle-voice`，先比对实际 Flash 与配套 BIN，再读取冻结环与停车记录。
