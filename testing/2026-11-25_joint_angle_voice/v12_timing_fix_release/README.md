# 联合过弯 v12 路径接收修订配对包

2026-11-25 版本归档，任务 `I-04-RIGHT-ANGLE`。来源提交 `39d6cfee4d7fb21483b61467452cc232f6fa3f41`，STM32 **JointAngleVoice 0x02120019** 配 K230 **v12**。STM32 已构建，K230 的 161,421 字节入口已写入并读回一致。该次回执中的 STM32 下载状态为未下载，两弯实车待主控验收。 [原任务](../../../project_planning/tasks/I-04-RIGHT-ANGLE.md) [装板回执](../v12_timing_fix_receipt.json)

| 文件 | SHA-256 |
| --- | --- |
| [K230 main.py](main.py) | `c4283811e545f20a7c4a11782266a54390f134b67ad501044079cf32a5103186` |
| [STM32 BIN](joint_angle_voice.bin) | `f11c601193bbdaaadc77e559565d1a5abd11f61b897a7425b7ce0b9c9b5401f8` |
| [STM32 HEX](joint_angle_voice.hex) | `df0985df36afc211884e9ca7fcfda0e626c255da3cac096804f7f61797622398` |

[视觉清单](main.py.manifest.json)列出合成入口所用源码和“收到”音频。修改时从源文件重新生成，方法见[配对说明](../../../control/docs/joint_angle_voice.md)。STM32 源工程为 [JointAngleVoice](../../../control/MDK-ARM/joint_angle_voice.uvprojx)。

语音初始化读取板上 `/sdcard/examples/kmodel/multi_kws.kmodel` 及 `/sdcard/examples/utils/` 下的 `wozai.wav`、`go_new.wav`、`stop_new.wav`、`wow_new.wav`。换板时核对实际 CanMV 固件和这五个文件。原板资源保留在板上及本机采集归档。 [资源记录](../../../project_planning/evidence/2026-11-24_vision_board_review/resources.json) [读取实现](../../../vision/src/voice_keywords.py)

同日另有[赛道车辆照片](../11-25-1.jfif)及[直角弯短视频原件](../../../1992776093.mp4)。视频已在 I-04 联合 v10 的设计记录中用于观察首弯出弯位置。照片和视频的实际试跑固件及同次日志待核。
