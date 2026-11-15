# 2044ms反向停车后的最少取证补充

状态：原失败保留，补齐取证能力；根因尚未解决，不能记作地面恢复或完整一圈。

## 已取得证据

- `fault_capture_01/capture.json`确认09固件一次地面RUN在2044ms以LAP_REVERSE5结束，当前零PWM、硬件及UART错误0。缺少原始触发采样和精确对应相机帧，不能凭滤波轮速正值判误报。
- `board_readback_01`实际取回明确run_0009，2796084字节，SHA256 b93c84e6e89bc727833d48eae5d4275306cf887c3efc999b0b9cdca94935a495；run_0010为后来USB启动，另存34314字节，不混作地面。main读取仍为v2原哈希，未runScript取代上电运行。读出时IDE中断的是当前USB会话，不能回写成先前地面日志相机异常。
- `log_review.json`统计8218条日志样本／最高帧33240，2777条wire有效样本，处理30..77ms；所有无效及每十个有效帧才打印，不能计算准确率。长会话有7处相邻抽样转向跨零且相差超过600，包含人为摆放等未定位时间，不把其当本次2秒窗口因果证明。
- `no_drive_scene_01`是在已隔离车载5V0和UART T/R、驱动OFF／XT30断开、DAPUSB拔开后，仅K230电脑USB的10秒真实禁驱动预览。15条样本／最高算法帧120，12条有效候选均current_pair／steering-55／bend355，处理45..68ms；所有wire_valid／drive_allowed为false，正常完成，5张原图。现场图显示两侧黑边及中央白走廊；不能由静止稳定外推移动稳定。

## STM32 0B／0C候选

保持SPL、既有目标及保护。仅LowSpeedLap应用增加1952字节固定环：每20ms记录真实原始左右delta／counts_per_s、归一化raw RPM、上一目标／PWM、当前转向／bend／来源及路径时间，保留最后32个窗口约640ms。所有RUN出口共用原save_result冻结点，故障／待机／新相机包不覆盖；仅新合法人工RUN或复位清有效计数。不改反向-5RPM判据、无反馈300ms、KEY、UART、源年龄、起步补偿或输出限幅。

短目标 `LowSpeedLap` 为 **0x0211000B／3000ms／40RPM**；Track为0x0211000C／300000ms，仅构建，未经本轮地面放行。原09 AXF／BIN及三份源文件先保存在mcu09_backup。新两目标Keil构建均0错误0警告，主机346项场景断言及生产UART驱动检查通过；反向触发样本入环、冻结不覆盖、环回绕、合法新RUN重置和双轮映射模型已检。`diagnostic_checks_02/checks.json`按实际ARMCC DWARF核对60／1952字节布局和SWD解码。增加耗时尚待实板DWT读数，软件模型不替代中断时序验收。

SWD工具仍不复位／halt／resume／写Flash，改成先核对Flash与当前AXF/BIN再解码RAM，防止主控尚未下载0B时按新地址读旧09数据。新增时间戳、冻结环和原有DWT时序读取。

短版BIN SHA256 1fc5ee49f6265499802fb6e5a3983542a4a60337a75fb8c05747d650433e4a28；Track BIN SHA256 f525047b839976e59a0612e2d53e810cfd8e76ec1a66f7c42cfb203c2ddead72。**代理没有下载STM32，实际Flash最后仍为09。**

## K230取证v3已部署

`runtime_trace_candidate_03/main.py`为36244字节，SHA256 **f9a12f4ec10d1fec6ab629f3415858403b2a4d0ed4df16dfb76482f4c5fe16d8**。只添加逐帧会话elapsed_ms、实际PATH序号／编码年龄及候选parameters／score／threshold；R6检测器、LapSender与保护的AST完全一致，不平滑或改转向。连续输入不自动START，每10帧flush，异常仍STOP退出，无自动重试。

46项入口／日志／故障模型及18项固定部署边界检查通过。`runtime_trace_board_probe_01`同源仅改30秒／禁驱动，实际run_0011含380个连续算法帧（1..380），会话0..29971ms，处理23..74ms、周期47..149ms、编码年龄24..77ms，序号0..255回绕检查通过，所有驱动许可false，正常completed。首次离线复核误把封包前年龄等同UART发送后to_send，断言失败另存trace_review_failed_01.json；改按真实时间边界复核通过，没有重跑相机或改原件。

按已有自动main修改授权，`runtime_trace_deploy_03/result.json`实际备份v2并单次写main、逐字节完整回读一致，boot仍不存在，写后running=false。没有runScript、START、Flash或远程上传。本轮v3实板禁驱动成立，v3物理冷启动／有效驱动和新增0B实际运动均尚未验证。

## 当前现场与一个下一步

主控已确认全车断电后隔离K230车载5V0及UART T/R，随后只接K230电脑USB。当前驱动OFF／XT30断开／DAPUSB不接，STM32不供电；K230USB供电、main为v3、后端已关闭。电机六芯保持原接法，车辆最后在地面，尚未得到重新悬空反馈。

下一步仅让主控将两只驱动轮稳固悬空，再在全断电下恢复车载5V0／UART原接线与仅SWD信号的DAP，并按Keil人工下载LowSpeedLap 0B（不是Track）；代理不烧录或启动电机。因断电／下载只补必要两次500ms校准，先读取0B／3000ms／故障0／DWT时序与稳定双边，再决定最少地面复测。不重做五姿态、通信探针、三次直行与左右固定台架。

本改进对应比赛第三部分图1及基本功能60分：使地面失败可定位，支撑完圈成功率并避免触边／出界；没有实测加分或完圈结论，全局汇总留00。
