# R7：数据分区保存与LINK时序留证

2026-11-19，I-04-RIGHT-ANGLE。程序文件可保存/sdcard/right_angle_drive_r7.py；照片与JSONL日志保存/data/right_angle_logs。right_angle_drive.py持续提供v5路径，仍由主控KEY启动；right_angle_preview.py默认无动力、10分钟。两份manifest列出精确来源与字节哈希。

相对release_r6_final，网格、识别、几何、转向和v5协议文件字节不变；增加发送间隔、留证、上一帧日志与GC耗时字段。STM32仍为0x02120012，沿用[原HEX](../release_r6_final/right_angle.hex)和BIN，不重新构建。若板上已是12无需重刷；本轮现场实际是今日直道03，须主控先在Keil切回RightAngle。

真实/data保存检查及迁移结果见[本轮记录](../storage_migration_record.md)。新照片不能补作昨天LINK触发图，存储恢复和无动力计时不代表动力过弯通过。一次双轮悬空1秒后一次上道，RST与KEY均由主控操作。
