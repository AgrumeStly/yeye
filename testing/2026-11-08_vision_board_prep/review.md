# V-08：板上诊断与通信的离线交付

日期2026-11-08；职责视觉软件／相关电脑验证，现场责任主控；不接替00。来源分支codex/current-version-20261025、HEAD a0733a8685db4c2b497539303bfe87fe1c1ebfe5。本轮本地未提交未上传，原件／冻结基线和共享修改保留，未操作任何实体设备或00摘要。

## 交付及实际验证

- [board_observer_core.py](../../vision/src/board_observer_core.py)：BP1基础类型灰度诊断核，实际回放1394张。旧325诊断159张、最终五姿态15张、V-06静态9张、完整77°272张、两圈552张满足其诊断几何；没有将R1原无效提升为BP1诊断有效。它仍不是C2的等价移植，protocol valid始终False。1007张与R1均有诊断偏差的帧，差值均值约0.151px、最大1px，是算法一致性残差，不是真值误差。
- [observer_bench_canmv.py](../../vision/src/observer_bench_canmv.py)与[独立打包文件](release/board_bundle/observer_bench_canmv.py)：默认idle、UART关闭，不开相机／串口／写卡；可明确选择SD已有图或30秒live诊断，输出分阶段耗时、堆、偏差、无效包。本轮只实际运行了电脑idle和[11项fake API入口模型](entry_model_tests.json)，没有实板执行。
- [vision_protocol.py](../../vision/src/vision_protocol.py)：唯一20字节协议编码与writer注入发送，两个type独立序号，短写处理，年龄未知／≥200ms、处理>100ms或无当前固定行支持时发新序号无效；heading／bend保留0。没有自动START／STOP。
- [正式44项检查](release/validation.json)：固定黄金包及CRC，1000组与原Python参考编码器逐字节一致；新编码的1394个真实C2/F1结果包全部通过原生产C解析器，837包仅在离线模拟新鲜度下满足有效条件，22包含当前确认的终点候选。不是板上发包数、UART互通或准确率。
- [生产C交叉适配器](../../vision/tools/protocol_cross_harness.c)实际编译并调用未修改的protocol.c／car.c，验证分包、连包、噪声、坏CRC、左右符号、独立／重复／回绕／重启序号、START／STOP优先、无效和断流故障、数据恢复不自动启动。原有[test_control.c](../../control/Tests/Host/test_control.c)也按原源码重建并运行，[55项原测试通过](production_control_tests.txt)。全部是主机模型，无硬件输出。
- [13份固定夹具](uart_fixtures/fixtures.json)、[真实识别包](release/recognition_packets.json)、[原采集时序C状态轨迹](release/sparse_capture_C_state_trace.json)和[30张SD诊断期望](sd_bench_expected.json)可审查。原录像按真实采集间隔回放生产状态机，在第10帧1.190s触发断流；不能拿4Hz写卡录像当满足200ms更新的实时识别。

BP1电脑算法均值约3.73ms、P95约4.73ms，单例CPython tracemalloc峰值153729字节；这些不表示K230D性能或MicroPython／媒体内存。C2/F1的依赖、最低数组量、运算量、端到端待测项目见[板上接续文档](../../vision/docs/board_preparation.md)。板型128MB不能当可用Python堆。F1和C2完整连通域／转角没有被偷偷替换成这个子集，完整路径缺口继续保留。

## 版本、保护及限制

[final_protection.json](final_protection.json)复核3616份原件／冻结源码／既有证据字节不变，并另核对前序C1的870份保护文件（含冻结build参数）均匹配，两清单有重合不能相加。本阶段136份control已跟踪文件哈希前后不变；R1/C1/C2、F1及BP1／协议／入口的交付源码与正式快照一致。开始时65条Git状态全部保留，没有从HEAD恢复文件。源码哈希、实际环境、分支／HEAD与最终Git状态都在该文件。

[api_context](api_context/)保存本机只读CanMV缓存示例／stubs的版本、文件哈希和所需API摘录。没有调用board_info、connect、run、预览、文件写入、许可或串口等板卡工具。实际固件只沿用既有K230D-v1.8-0记录，缓存API仍需实板验证。本轮电脑安装PyMuPDF 1.26.6用于PDF审核；完整工具依赖见vision/requirements-review.txt，pip check通过。

run_01保留32位MinGW DLL无法载入64位Python的WinError193现场；随后改用独立C主机进程完成交叉验证。run_02为初版通过结果；release补充“年龄未知默认无效”的检查，为正式交付。未通过的初次加载不冒充验证成功，也不改STM32来绕过环境问题。

## 当前阻塞与下一步

未验：完整C2/F1在CanMV的等价移植、实体API／内存／端到端周期、K230 UART引脚映射与STM32实物互通、车体几何／车尾越线、动力循迹和自动停车。HardwareBench UART仍默认关闭，K230侧接线未冻结；本轮不改控制策略、增益或双方协议。

v1已有终点候选bit1，但不能表达局部观测范围、历史／未知、减速停车原因、终点事件／观察门、全车越线或数据年龄等。具体缺口与待共同确认建议、无动力CRC／序号／偏差／有效性／START／STOP／无效／断流检查表，均在[板上接续文档](../../vision/docs/board_preparation.md)，没有擅自占保留位。

主控下一步唯一人工动作为：保持电机动力断开及UART关闭，手动运行独立脚本的SD已有30张诊断回放，保存完整终端、所运行副本哈希、时间与堆数据；不补拍，不写main.py，不开启采集许可。具体前提、操作、预期和异常证据见上述文档末节。此后才依据真实数据推进live／UART，不把本次离线结果包装为整车可用。

比赛关联：第三部分／图1基本完赛60分需要避免错配、触边／出界与断流失控；终点候选通信支撑额外功能40分中冲线自动停车相关研发；复现与失败记录支撑报告20分。没有实测分数收益，不补造扣分公式或额外功能分项值。
