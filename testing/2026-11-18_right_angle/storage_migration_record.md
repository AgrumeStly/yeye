# I-04-RIGHT-ANGLE：11月19日恢复与数据分区清理

负责：本轮执行对话；实物操作及验收：主控。数据迁移、保存入口软件交付及实板无动力检查完成，尚未进行本轮动力首弯复跑；不得外推完整过弯验收。

主控要求接续昨日左侧直角弯复测，明确“照片数据放在canMV的data盘内，程序才放sdcard里，你清理一下”，并确认SD／TF卡未更换或拔动。依据比赛第三部分、图1、表1，本轮减少数据丢失和无谓停车风险，支撑基本功能60分完圈及报告20分证据；软件／存储检查不代表比赛得分或过弯通过。

## 实物核对

- [首弯Flash不符](resume_20261119_mcu_01/capture.json)：保存失败，不解释不匹配的RAM。
- [与今日直道03完全匹配](resume_20261119_mcu_02/capture.json)：StraightDualStart／0x02120003，CPU运行、PWM0，上一轮2000ms／LIMIT11。未下载、暂停、复位或发START。恢复首弯需主控在Keil切回RightAngle／0x02120012。
- [容量及原日志缺失](resume_20261119_storage_01/result.json)：/sdcard共1023744个512字节块，可用0；旧run_0012／0013按原路径已不可读。
- [文本目录枚举失败](resume_20261119_storage_02/result.json)：旧弯道目录UnicodeError，失败原样保留。
- [原始字节目录和/data容量](resume_20261119_storage_03/result.json)：/data共13496256个512字节块，当时可用13448704块；旧弯道目录唯一异常目录名为字节串`b'\xae.\x60%.!('`，不猜路径、不删除。空间已满和异常目录均属事实，不能据此断言昨日LINK的唯一根因或认定卡被更换。
- [初次盘点](resume_20261119_storage_inventory/result.json)：captures扫描超过短诊断窗口而受到IDE interrupt，不能当完整盘点；后续正式迁移按运行至完成收集。

## 迁移与清理方法

工具：[migrate_canmv_data.py](../../vision/tools/migrate_canmv_data.py)。仅处理/sdcard下captures、lap_boot_checks、lap_runtime_logs、straight_logs、right_angle_logs中的照片及日志扩展名；不操作程序、系统目录、模型，不格式化，不递归删除目录。目的地为/data/migrated_20261119_sdcard/session_NNNN，不覆盖已有文件。每个源文件分块读取到/data、SHA-256读回一致且同步后，才逐文件删除/sdcard原副本；失败和未知文件名保留。完整清单同时保存在/data及主机原始终端。

- [首次尝试](storage_migration_01/result.json)：CanMV的str.endswith不接受CPython式元组参数，所有文件保留，实际删除0；失败证据保留。已改为逐个扩展名判断。
- [正式迁移](storage_migration_02/result.json)、[逐文件哈希与结果](storage_migration_02/terminal.txt)：1197个文件、43104268字节（41.11MiB）全部复制／读回SHA-256一致后删除旧副本；1个非数据扩展名保留，1个异常弯道目录名无法解码并保留。/sdcard可用由0恢复132288个512字节块（64.59MiB），/data仍可用13311360块（约6.35GiB）；程序文件部署前的实测值，不等同修复损坏目录。空文件也按原字节迁移，不将其算作有效原图或有效日志。
- [迁移检查](storage_migration_checks/checks.json)：真实临时文件的正常迁移、目的文件损坏两种情况，验证只删除哈希一致文件、程序不变、异常名字保留；不能代替实板迁移结果。

## 新保存入口

[release_r7_storage](release_r7_storage/right_angle_drive.py)使用/data/right_angle_logs保存逐帧JSONL及失效前后PGM，程序仍放/sdcard。与R6相比，网格、识别、几何、转向和v5协议四份源文件哈希完全一致，STM32 BIN保持原0x02120012，不重新构建。新增发送间隔、上一帧日志／GC及本帧留证耗时字段，用于区分处理峰值和发送后的停顿；200ms保护、人工KEY及故障锁定保留。

[保存入口检查](storage_migration_checks/right_angle_storage_checks.json)验证/data递增日志、已存在日志不覆盖、异常不吞掉、短写拒绝、无动力副本不发许可，并复核算法文件哈希与发布一致。共10项入口检查及正常复制／损坏目的文件两种迁移场景通过。原R6算法与协议证据复用，不重复全量检查或构建；昨日原件保留。

2026-11-19实际交付核对：

- [程序部署读回](storage_program_deploy_01/result.json)：/sdcard/right_angle_drive_r7.py共53657字节，SHA-256 a91cd793735222bc2e15f7acca6f272425b7bd3ee96cde8cf13b5ccd15b9470b，与发布一致；未执行正式许可脚本。/sdcard/main.py部署前后完全一致，哈希f9a12f4ec10d1fec6ab629f3415858403b2a4d0ed4df16dfb76482f4c5fe16d8，没有更改上电行为。
- [采图前主板记录](storage_pre_camera_mcu_01/capture.json)：仍匹配直道03，停止状态及两轮PWM0；没有复位或START。
- [5秒实相机保存检查](storage_camera_check_01/review.json)：58帧全部无驱动许可，从/data/right_angle_logs/run_0001.jsonl完整取回日志及76815字节320×240灰度PGM。[原图](storage_camera_check_01/frame.pgm)、[无损PNG查看副本](storage_camera_check_01/frame_view.png)已目视核对，当前为赛道印字及左上边线，未形成有效路径，几何有效0帧；不是昨日触发原图。
- 实测峰值：processing100ms、采集开始到发送104ms、循环间隔168ms、发送间隔169ms、日志阶段92ms、GC7ms、诊断留证44ms。不能用无效视野的58帧证明有效近弯／动态时序均通过；数据盘写入也有耗时。LINK动态根因仍待同一实跑时间证据，200ms保护不变。
- 新增日志短写检查，write返回长度不符即抛错；仍每10帧flush，不为每帧额外sync。日志阶段／GC耗时记录在下一帧，没有后续帧时不补造最后一次耗时。

## 当前待验与版本

迁移完成时的直道03已由主控切回首弯12，R7正式会话live_drive_09实际启动并完成一次双轮及一次地面复测；2041ms／PATH3失败，完整[本次记录](ground_06_record.md)覆盖旧的“等待切回”步骤。当前视觉已停止，撤离前截图已存电脑；主控明确扩展入弯修正范围，继续离线开发，实板计时／下一次复跑待主控返回。不自动连续试跑。

分支codex/current-version-20261025；起点7dc0d5568768dd204b8c201a2ecf3b4e3c1ee5a6。本轮仅提交新迁移工具、R7单文件发布、必要原始记录／检查及当前操作／任务文档。三份混有原首弯历史实现的未跟踪源码right_angle_canmv.py、run_right_angle_live.py、probe_right_angle_timing.py保留原位置、不整体暂存；[来源哈希、精确R6差异及当前快照](storage_source_changes/source_hashes.json)随证据保存。其余共享修改及未跟踪历史成果保留，不上传；完整提交号在最终回报给出，不循环提交自身编号。
