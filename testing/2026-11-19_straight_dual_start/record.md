# I-03-STRAIGHT-ASSIST：昨日直道基线的双轮启动适配与复跑

日期：2026-11-19。分支：`codex/current-version-20261025`，来源HEAD `74a45ef81f2165e4e53cf43bc45d349564bca42b`。主控本轮要求“现在重新试昨天跑直线的最终版本”，在说明02原版仍需逐轮配对后明确“适配双轮启动”。本轮继续原任务；不接管总管、不改全局摘要、不上传。

## 实现及比赛关联

新增独立 [StraightDualStart工程](../../control/MDK-ARM/straight_dual_start.uvprojx)，版本 **0x02120003**。STRAIGHT_DUAL_START_TARGET仅开放已经在首弯实现的固定映射／双轮启动监督；仍定义STRAIGHT_ASSIST_TARGET，保持昨日直道v3、视觉R2、80RPM／2000ms、PI6／8、轮速滤波1/2、差速补偿、50%上限及故障保护。首次KEY为双轮60RPM／1000ms，只有完整正反馈通过才开放下一次KEY上道。悬空不依赖视觉；地面失线／源年龄200ms保护不放宽，STOP、KEY、反向、超速、无反馈及看门狗保留。

沿用11月18日真实直道映射，不通过双轮同时转动猜左右。原02工程／产物保留；原首弯及低速目标行为不改。比赛第三部分、图1、表1要求顺时针自主完圈、触边扣分及出界失败；本项复核直道段可靠性、减少错版本及错误映射风险，支撑基本功能60分的完圈／用时和报告20分的证据。没有官方分数、圈时或新增得分声明。

## 软件与构建

- 新目标244项软件断言通过，覆盖首次双轮无视觉、固定映射、1秒完成、STOP／KEY中断、卡键、错误映射、单轮无反馈、反向、超速、复位清资格、地面v3互斥／200ms／失线及原2秒限时。
- 原直道893、首弯601、低速347项及生产UART检查通过。模型是软件证据，不作为实测轮速或地面改善。
- 新版及原StraightAssist、RightAngle、LowSpeedLap、LowSpeedLapTrack共五目标构建0错误0警告。原四目标BIN重建后SHA256全部与本轮前一致，见 [review.json](review.json)；构建／测试日志见 [checks](checks)。
- 新BIN SHA256：`44aa78ec12deb3443bb85f1347f4cd6ce17ed2ac1877e1727d748b9c35525c16`。冻结AXF／HEX／BIN见 [firmware](firmware)，构建源哈希见 [build_source_hashes.json](build_source_hashes.json)。

## 真实板级与现场经过

初次主板未供电，SWD No ACK原失败保留。主控说“现在主板有电了”后，[powered读取](mcu_powered_before_download/capture.json)确认原板仍首弯12版，零PWM、故障0，未自动烧录／复位。

主控“下载好了”后，[首次读取](mcu_after_download_01/capture.json)确认Flash完全匹配03，但RAM是下载后尚未初始化的残留，拒收为运行基线。主控人工RST一次并反馈“已复位”；[复位后读取](mcu_after_reset_01/capture.json)确认版本03、毫秒递增、80RPM／2000ms、phase2、待双轮测试、全部输出及故障0。

主控首次KEY悬空后反馈“正常”。[dual_bench_01](dual_bench_01/capture.json)确认完整1000ms以LIMIT11结束，completed1／stage2、正向净计数1173／1178，末帧测得64.13／64.87RPM；当前PWM0。此为悬空反馈，不称地面60RPM性能。

已运行 [live_drive_01](live_drive_01/run.json)，COM10、原v3视觉R2、不发START、不改main.py。执行源码SHA256为`3bdfd1603182740ced8035b2a0f793eb88bb9d0f38756ece0f15e80348db86b4`，与昨日R2 manifest一致，原归档文件仅CRLF／LF换行字节差异；函数源码与六个源模块哈希一致。主控放好车后1MHz SWD两次No ACK失败保留；新增只读工具频率选项，默认仍1MHz，显式100kHz [live_ready_03_slow](live_ready_03_slow/capture.json)成功。真实收包1087→1103、源年龄18～47ms、当前双边有效、悬空资格保留、零PWM／故障0，随后给主控一次80RPM／2秒操作指引。

主控地面反馈原话：**“正常”**。[ground_01_capture](ground_01_capture/capture.json)确认最后一次真实运行2000ms，LIMIT11正常撤驱动，Flash与03完全一致、硬件及UART错误0。末帧左右目标82.4236／77.5764RPM，测得88.5855／83.8415RPM，PWM26.2%／25.9%；这是末帧，不能当全程恒定转速。冻结环保留1377～1997ms的32个20ms样本，该窗口全为当前有效双边。

取证时ground_runs=2、starts_rejected=1，双轮通过后至少有两次地面RUN被接纳及一次启动被拒；主控未逐次描述，最新结果和冻结环只覆盖最后一次，不能写成“仅启动一次”或“两次全程均成功”。不为解释计数追加试跑，也不推测此前动作及停因。地面距离、明显摆动次数、触边次数、横向偏移未单独量化；主控“正常”不扩写成无摇摆／触边0／完整圈验收。

## 相机日志与收工

停车数据先保存，再通过本次stop.request正常请求停止相机会话；[result.json](live_drive_01/result.json)记录stopped_by_control_file=true。终端中的IDE interrupt是本轮人工停止请求的退出，不当运行中算法故障。主机 [terminal.txt](live_drive_01/terminal.txt)／[backend.jsonl](live_drive_01/backend.jsonl)及完整执行源码保留。

随后仅连接官方后端读取SD，不运行新脚本；[visual_evidence/review.json](visual_evidence/review.json)确认scriptRunning=false，但`/sdcard/straight_logs/run_0009.jsonl`存在且size0，下载校验拒绝。**没有取得完整逐帧视觉SD日志**；原因未核实，不能把主机每10帧打印当完整逐帧证据。此与昨日首弯已记录的空SD日志现象并列保留，本轮不扩展为SD修复任务、不新增硬件测试。

## 本地提交范围与剩余现场

共享checkout开始时已包含此前直道／首弯未提交实现及大量未跟踪依赖。6个本轮修改的共享实现文件在HEAD中缺少此前相关实现，直接暂存完整文件会夹带历史成果，不能安全生成独立可编译的仅本轮源码提交。本轮保留这6个文件工作区现场，精确“本轮开始→本轮结束”补丁归档为 [adaptation.patch](adaptation.patch)，配套 [shared_source_hashes.json](shared_source_hashes.json)记录前后原字节哈希；补丁针对本轮开始的共享现场，**不能假称可直接应用到来源HEAD即完整恢复**。

本地提交仅含明确新增的工程／构建及测试工具／专用测试、操作单、同任务更新、适配补丁及本轮固件和原始证据。共享实现、原直道未跟踪依赖及其他任务修改不一并暂存。后续交付使用本地现有工程和冻结固件；远端干净检出不能据本次提交独立恢复原直道全部环境。最终提交号由对话回报，不在本文件循环提交。

当前成果：软件／构建通过，主控已确认悬空与地面现象“正常”，最后一次2秒正常LIMIT有实读证据；正式验收范围仍由主控明确，不代作整车验收。停止复测，原80RPM／2秒参数保持。主控如需继续调整须明确新范围；视觉已停，下次需重新启用新会话。没有上传、合并或改写历史。
