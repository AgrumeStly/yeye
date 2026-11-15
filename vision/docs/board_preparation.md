# V-08板上诊断与通信接续

2026-11-09算法接续：[T2多帧／二维路线候选](offline_temporal_route.md)及[完整电脑证据](../../testing/2026-11-09_vision_temporal_route_t2/review.md)已另行交付。T2依赖电脑NumPy/OpenCV，单进程61张弯道窗口中位128.94ms／P95 158.57ms，尚不能满足现有有效路径处理时限或直接移植CanMV；不能将下面较早BP1/C2/F1结果当作T2已上板。T2始终protocol_valid=False，不改20字节协议或STM32控制。当前先查看新视频，原SD诊断保留为后续实物步骤，本轮没有新硬件动作或采集许可。

日期2026-11-08；维护视觉软件，现场责任主控。[交付证据](../../testing/2026-11-08_vision_board_prep/review.md)，[任务](../../project_planning/tasks/V-08.md)。本轮只做电脑实现／回放／生产C软件交叉验证，没有连接板卡、开启相机、采集、写main.py、UART收发或驱动电机。

## 现在可用的范围

[BP1诊断核](../src/board_observer_core.py)仅用Python基础类型，可在CanMV环境评估真实灰度缓冲扫描；没有C2全图连通域／转角和F1终点检测。diagnostic_valid只表示这套简化几何条件成立，顶层valid始终False。[独立入口](../src/observer_bench_canmv.py)默认MODE=idle、UART_ENABLED=False，不开相机／串口，不写文件。可明确选择SD已有图片诊断或30秒live诊断；后者仍需下一次实物授权和执行。本轮没有执行两者。

正式单文件位于[release/board_bundle/observer_bench_canmv.py](../../testing/2026-11-08_vision_board_prep/release/board_bundle/observer_bench_canmv.py)，无需在板上安装NumPy、OpenCV或其它电脑包。默认执行仅打印IDLE。诊断日志含取帧／SD解码、缓冲复制、算法、到UART发送完成的本地时间、GC可用堆、像素偏差、20字节十六进制及wire_valid=false。没有全车控制就绪或终点停车声称。

协议编解码及writer注入见[vision_protocol.py](../src/vision_protocol.py)。真实C2固定y120且稳定、处理≤100ms、调用者明确提供年龄<200ms，才可在显式allow_valid_path=True的电脑离线交叉验证中形成有效包；年龄缺失默认为无效。BP1入口永远不打开这个开关，不发送START／STOP。处理超限、当前观测无效、时间未知或过期都发新序号无效包。短写只发送剩余字节，0／None写入失败立即报错，不重发整包或忙等。

## 依赖、内存与时间

C2/F1依赖dataclasses、OpenCV、桌面NumPy及其连通域、轮廓／多边形、polyfit等接口；CanMV的ulab不是这些包的兼容替代。128MB为板型总内存，不能视作Python可用堆。320×240灰度一帧76800字节；C2单个int32标签图307200字节，另有二值掩码、轮廓、数组临时量、媒体缓冲及Python对象。仅这些已是数百KB，完整峰值必须实际测，不能凭总内存认定移植成功。

BP1每帧采样2480个像素建立直方图，再读取31×320×3=29760个缓冲像素做三行中值；每行最多8条黑段（28种配对），输出最多31对点，无跨帧图像缓存。Image.bytearray可能产生额外76800字节副本；入口核对长度必须恰为76800，布局未通过就拒绝。单个PC样例tracemalloc峰值153729字节包含本轮输入字节创建，是CPython分配记录，不能换算MicroPython堆或媒体内存。

本轮两圈C2电脑调用均值约17.62ms／P95约25.80ms，F1单独约0.354ms／0.786ms；BP1全部1394张约3.73ms／4.73ms。均不是板上端到端性能；F1计时不含R1/C2，全部不含图像I/O、绘制／编码。原录像间隔中位224ms、最大614ms，不满足原200ms路径超时的连续控制需求；这是带写卡采集的事实，不能推断板上识别极限。用原采集时间回放生产C状态机，首次在第10帧1.190s进入断流故障，后续有效图不自动重启，证据见sparse_capture_C_state_trace.json。

20字节在115200/8N1占线约1.74ms，50Hz仅是原目标，不代表当前能达到。单线程Python卡住时不能保证按期发包，仍依赖STM32独立200ms断流保护。本次不放宽100／200ms或调整控制策略。

## 现有协议能表达与不能表达的内容

唯一布局、CRC、序号和接收行为继续查[protocol_v1_draft.md](../../control/docs/protocol_v1_draft.md)，本页不另订字节布局。flags bit1已能表达终点候选，无需新增字段；只有当前可见且F1时序确认时置位，不用缺检或观察门通过置位，STM32当前仅记录，不自动停车。固定偏差使用原deviation_normalized、右正。

heading虽然有0.01度单位，但当前没有可信地面航向；bend虽然有0..1000，却没有经双方确认的C2映射。两者保持0，禁止把left/right轮廓提示映射成物理角度或随意把bend设>500改变演示请求。reserved和其余flags保持0。

具体缺口：v1不能区分当前实测／历史推断／未知，不能携带局部y范围／近场中点、减速／停车建议及原因、采集时间／数据年龄、终点事件ID／图像观察门／全车越线确认或接收回执。建议这些诊断状态将来由00协调、主控与01共同确认后采用独立诊断消息或明确版本扩展；当前只打印本地日志，不借保留位／heading／bend偷偷扩协议。STATUS无回包，不能把发送成功当接收或执行成功。

## 无动力联调检查表（未来，当前未执行）

连接前提：电机动力物理断开，保持已确认下载器／Keil5；确认3.3V逻辑、公共地、TX/RX交叉且不跨接5V电源。STM32资源入口为PA2/TX、PA3/RX（实际丝印A02/A03按pin_plan核对）；板上K230 UART物理引脚仍未冻结，不能照抄缓存示例IO3/IO4。UART_CONFIG保持None，缺少已核实映射会在启动相机前拒绝。HardwareBench默认BOARD_UART_ENABLE=0，本次未改；真正互通前需另有明确授权的01配置／构建／下载及接线证据，不能直接拿SpeedSprint等电机目标代替。

| 检查项 | 无动力操作与预期 | 保存证据 |
| --- | --- | --- |
| CRC／格式 | 固定中心包及123456789向量，20字节、小端、CRC=29B1；坏CRC不刷新路径 | 双端原始字节、解析接受／拒绝计数 |
| 分包／连包／噪声 | 7+13字节拼成1包，连包2包，噪声后重同步 | 收发时间与accepted／rejected |
| 偏差符号 | +600右偏时原演示左请求较高；−600相反；只看Watch，不接电机 | error、left_request、right_request、安装侧别 |
| 有效性 | 实时当前固定行才有效；BP1诊断全部flags bit0=0；低质量39或处理101ms不能运行 | flags、confidence、processing_ms、g_car |
| 序号 | 每type独立；255→0前进，重复／倒退不刷新；静默≥200ms才重建基线 | sequence_time、last_sequence、duplicates |
| START | 无新鲜路径拒绝；有效、质量≥40、处理≤100ms、年龄<200ms才进RUNNING模型 | starts_rejected、state、path_time |
| STOP | 合法STOP始终停，重复／旧STOP也生效；旧START不能越过新STOP | command、state、reason、请求归零 |
| 无效／断流 | 新无效路径立即FAULT；停止发送达到200ms则FAULT；恢复数据不自动启动 | 本地毫秒、最后路径时间、FAULT及请求归零 |
| 终点候选 | flags bit1只记录，不能自动解释为整车越线或停车验收 | 包、F1状态、Watch字段；不作车尾结论 |

固定13份包见[uart_fixtures/fixtures.json](../../testing/2026-11-08_vision_board_prep/uart_fixtures/fixtures.json)。它们只用于独立场景检查，须按场景重置状态；不要盲目顺序连续发送全部文件。`recognition_packets.bin/json`为1394张真实电脑结果的字节映射，source_age=0明确是离线模拟，不能直接当实时UART流或完整循迹输入。当前没有提供会自动打开实体端口的批量START脚本。

Keil未来观察入口：Project → Open Project打开control/MDK-ARM/yeye_control.uvprojx，选择HardwareBench；Debug → Start/Stop Debug Session；View → Watch Windows → Watch 1，查看g_car、g_parser及g_control_ticks。只有相应UART启用配置实际构建／下载并核对后才有意义；当前不指导更换SPL、下载器或工程链路。

## 主控下一步唯一人工动作：用SD已有30张做板上诊断回放

此动作不需要去场地、补拍或接STM32 UART。主控保持电机动力断开、UART_ENABLED=False和现有main.py／采集许可不动。在本地工作副本打开上述独立单文件，把MODE从idle改为sd_replay（保留冻结交付文件）；通过CanMV扩展手动运行当前脚本，不选择保存为main.py／离线自启动。输入仅为/sdcard/captures/push_full_lap_0001已有图片，源码中的30个编号只是回放选片。

预期自然运行结束并打印30行JSON，全部wire_valid=false，source_kind=sd_decode_not_camera。对照[sd_bench_expected.json](../../testing/2026-11-08_vision_board_prep/sd_bench_expected.json)核对诊断偏差和有效性；板上JPEG解码可能有像素舍入差异，差异必须回报，不能先放宽。保存完整终端（含错误和清理信息）、板型／固件、所运行副本哈希、30行算法／复制／取图时间、free_before／free_after最小值。若报缓冲布局或API不兼容，保存原错误并停止该次诊断，不重启采集或覆盖main.py。

这一次只验证移植子集的SD解码／API／内存／运行时，不验相机实时端到端性能。随后才按真实结果决定live诊断／完整C2/F1移植；UART实物及带动力整车均另验。比赛基本功能60分、额外功能40分相关终点链路及报告20分分别需要后续实物证据，本次软件检查不折算实测得分。
