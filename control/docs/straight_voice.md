# 脱机语音直道试跑

目标 **StraightVoice**，固件标识 **0x02120004**，配对 **K230 v6 main.py**。说 **Go** 后，STM32依据新拍的双边直道进入原 R2 循迹，默认 80 RPM，最多 2 秒。说 **Stop** 撤驱动。实物 **KEY**（PA0／WKUP）用于急停，按着 KEY 时也会拒绝起步。

## 安装

1. 主控稳固支起小车，双轮离地。主板继续用驱动板 5V，DAPLink 仍为 DIO（SWDIO）、CLK（SWCLK）、GND。在 Keil5 用 **Project → Open Project** 打开 [straight_voice.uvprojx](../MDK-ARM/straight_voice.uvprojx)，选 **StraightVoice**，用 **Flash → Download** 下载。如需配置下载器，在 **Project → Options for Target → Debug** 选 **CMSIS-DAP Debugger**，**Settings → Debug** 选择 **SW**，下载算法使用项目中配置的 STM32F4xx 512 KB Flash。
2. 视觉板仍接电脑 USB 时，用 CanMV 停止旧会话。把本地产物 `vision/build/straight_voice/main.py` 原样存到 K230 的 `/sdcard/main.py`。写前保留 SD 卡上已有的同名文件，并核对 `boot.py` 没有接管相机或串口。沿用板上已有的 `/sdcard/examples/kmodel/multi_kws.kmodel` 和 `/sdcard/examples/utils/` 内四个语音 WAV。只需保存到卡上，最终由冷启动进入脚本。
3. 主控关闭驱动电源并隔离电池，拔掉视觉板电脑 USB 和 DAPLink。沿用主板 5V 供电，把驱动板稳压 **5V／GND** 接到视觉板 **5V0／GND**。由硬件核实针脚、极性和带载电压。UART2 沿用 K230 丝印 **2** 的串口座，**T→主板 A03、R→主板 A02、G→主板 GND，V 悬空**。两板都接好后再用车载电池通电。详见[车载供电](../../hardware_preparation/onboard_power.md)、[UART 实物接线](../../hardware_preparation/low_speed_lap_wiring.md)及[立创供电与 UART 说明](https://wiki.lckfb.com/zh-hans/lushan-pi-k230/faq.html)。

用于重新生成的命令，输出目录须为新目录。

```powershell
python vision/tools/prepare_straight_bundle.py --voice --output vision/build/straight_voice_new
```

## 一次悬空，随后一次上道

1. 仅靠车载电池冷启动。相机保持能看到当前直道两侧，在双轮离地的情况下等主板绿灯每约 2 秒出现一次较长闪亮（约 0.4 秒），两轮应保持静止。短闪约 0.08 秒表示缺当前双边许可，连续快闪表示锁故障。无需 KEY 手势，也无需唤醒词。
2. 主控说一次 **Go**，两轮应同时向前转。可在两轮开始后立即说 **Stop**，确认撤驱动。没有识别到 Stop 时原 2 秒限时仍有效。悬空确认后待轮子停稳、播报完毕。
3. 主控把车顺时针摆在已确认的直道中央，车头对齐，给 2 秒运动和滑行留足空间。等双边许可再次出现，说一次 **Go**。观察是否沿线纠偏、碰线或提前停车。KEY 在需要时可立即撤驱动。任何失线、链路或编码器故障均停止并锁定，记录原因后再处理。

Go 命中马上请求下一帧启动，已有 Go 应答在 2 秒窗口结束后播放，以免播报拖延控车。Stop 先发送停车再播放，测试时可用视频测量从说 Stop 到车轮实际停稳的时间。UART 当前没有执行回执，播报表示本地识别，实际运动和停稳以观察及 STM32 结果为准。

可取 STM32 的 `g_lap_last` 停车记录及 K230 的 `/data/straight_voice.log`。正常 2 秒限停为 LIMIT（11），语音停车为 VOICE_STOP（12）。K230 记录已发送请求、失效许可及运行窗口内的最大图像周期和语音处理耗时。看灯和撤 PWM 只能定位状态，实体停稳、音量和清晰度由主控观察。

比赛第三部分和表 1 的额外功能包含独立语音启动、接管和应答。直道结果也可用于记录基本功能环节的触边与失线风险。当前验证范围为单段 2 秒，正式终点接管、3 秒停稳、完整一圈及比赛得分仍待实车证明。 [比赛原文](../../competition/比赛文档.pdf)
