# I-04-RIGHT-ANGLE：R8返回赛道调测

2026-11-19。主控本轮明确“继续调测第一个直角右侧弯”，指定entry_r8_record.md接续，并确认“接线未变，车已供电”。沿用原任务及既有轮位；代理核对／部署视觉，主控操作RST、KEY和实物。

## 已完成的恢复

- [新鲜主板读取](r8_resume_mcu_01/capture.json)：CPU运行，Flash与归档0x02120012的BIN逐字节相同，SHA-256为2fb9d362ac92ae7b8a20e696cfddde6ff7a6435e0648c5f3ca186102efdca5f4；未下载、暂停、复位或发运动命令。读取时仍锁上次PATH3、2041ms，左右PWM0；旧bench1000ms／ground_runs1不作为本轮悬空测试结果。
- COM10相机、COM9下载器存在，初次进程核对未见Keil／CanMV占用。R8发布与生成器、155+33项既有检查manifest一致，复用离线证据，不追加同版本回归。
- [部署及读回](r8_program_deploy_01/result.json)、[部署工具](r8_program_deploy_01/deploy_source.py)：写/sdcard/right_angle_drive_r8.py，54883字节，SHA-256为23c812b040d4b71faa986616ae2cfb3cf1fca3c7090ef99b27b36ddc75d8f96b，读回逐字节一致。main.py前后相同，R7保留；/data/right_angle_logs存在。
- 正式视觉会话live_drive_10已启动，新日志/data/right_angle_logs/run_0005.jsonl，未发START。[启动时快照](r8_program_deploy_01/live_start_snapshot.json)仅证明采样时运行；后续实时状态须结合live_drive_10/status.json的last_observed_at与进程核对，不能把此归档当永久running。当前悬空／摆放视野的终端为no_current_pair，不代表地面摆好后的许可；实际处理峰值、发送间隔和源年龄须在本轮日志取回后分析。

## 双轮及唯一一次上道结果

主控悬空按RST／KEY后反馈“正常”。[本轮双轮读取](r8_bench_mcu_02/capture.json)确认1000ms、completed1、ground_runs0，左右累计1176／1180，末次反馈63.54／64.23RPM；该反馈只验收悬空现象。此前1MHz读取遇SWD No ACK，保留[r8_bench_mcu_01失败](r8_bench_mcu_01/capture.json)，改100kHz后成功；未复位或重复双轮。主控随后“已摆好”，[摆正读取](r8_positioned_mcu_01/capture.json)当前路径有效、源年龄3..4ms、UART各错误0，代理未发送START。

地面仅一次。主控原话：“这一次走一点就停下了，然后绿灯快闪”。[冻结主板](ground_07_capture/capture.json)确认0x02120012、地面启动1次、运行499ms、LAP_LINK2，当前左右PWM0；不是上次2041ms的PATH3。停车前转向-116、左右目标67.18／84.82RPM、实测83.95／94.51RPM。未完成首弯；触黑边／完全出界无单独反馈，不记零触边或动态通过。

## LINK时间线与原因

[完整分析](ground_07_review.json)、[原始窗口](ground_07_window.json)、[可复现脚本](ground_07_analysis.py)：完整run_0005有4036帧，全部JSON可解析，17个下载文件逐份哈希复核；8组前后PGM为更早的路径失效事件，不冒充本次LINK触发曝光。

- 冻结环8个不同路径序号逐一匹配序号、转向、弯度和源时间间隔，排除8位序号重复；唯一一致候选为帧3289／序号216，源时间偏移-130628..-130625ms，跨度3ms。其它候选跨度18..33ms或字段不符。
- 停车时MCU时间109631ms、最后源时间109431ms，年龄正好200ms。帧3289处理38ms、发送前年龄40ms、wire_valid=True；发送后本帧日志处理78ms（由下一帧previous_log_ms记录）、GC5ms，下一帧处理77ms／发送前年龄80ms，发送间隔164ms。下个有效包按两时钟范围估计晚于停车4..7ms；当前窗口没有撤许可事件。
- 因此本次由同步日志处理停顿叠加下一帧计算触发LINK保护；停车后相机恢复发有效包不自动解锁主板。78ms含JSON序列化、流write及潜在内部刷新，不能单独认定显式flush、卡满或介质损坏；3289非10倍数，未调用每10帧的显式flush，仅降低显式刷新频率不足以证明修复。
- 本次未保存LINK触发时同步曝光，不能用更早PATH失效图解释此次短停。额外5秒禁驱动采图仅保存当前位置：[停车后原始PGM](ground_07_stopped_view/frame.pgm)、[无损PNG](ground_07_stopped_view/frame.png)、[禁驱动计时](ground_07_stopped_view/review.json)。图已打开核实；该诊断所有wire_valid=False，没有动力动作，其峰值不冒充地面窗口。

正式视觉已通过stop.request停止；live_drive_10/result.json及status.json覆盖running=False。原始日志和图片已取回，本轮不追加试跑；主控可挪车。后续唯一工程步骤为修正同步日志阻塞对逐帧新鲜度的影响，再按改动验证；不放宽200ms／当前支持保护，不为499ms LINK先增转向。本轮未修改运行算法／协议／主板，不能宣称已修复或首弯通过；下一轮硬件动作仍需主控明确接续。

比赛依据：第三部分、图1及表1基本功能60分和报告20分。验证取消提前强转是否改善入弯，减少触黑边扣分、出界失败和无谓停车风险，以一次实际轨迹及原始日志支持后续判断；不预测官方分值。原保护、协议、主板、轮位和速度参数均未改。

来源分支codex/current-version-20261025、开始HEAD 1712cce653ecd4bffdb4700297e05ccfb810c2f8。只提交本轮恢复／双轮／一次地面结果、原始证据、分析及同任务记录；live_drive_10已结束，一并归档。任务目录.gitattributes仅对本轮证据路径禁用文本换行转换，PGM及原始终端标二进制；原始启动入口的空白也保持不改，作者文档／分析脚本另查空白。既有共享修改／历史未跟踪成果保留，未上传。
