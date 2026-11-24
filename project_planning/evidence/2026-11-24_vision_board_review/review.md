# 2026-11-24视觉板成果阅读与进度核对

主控要求先完整阅读视觉与DeepSeek已放到板上的成果，再更新进度。本报告依据实际读出的项目代码、资源和历史日志；本轮不运行这些应用，不代替主控验收。任务：[TASK-20261124-01-vision-board-review](../../tasks/TASK-20261124-01-vision-board-review.md)。

## 当前结论

语音已经从“仅有交接说明”推进到**板上有独立识别／应答／UART发送源码和部分历史识别日志**。新增图传和采集工具也已实读。语音、路径和图传仍分别运行；实际语音启动车辆、接管后3秒内停稳、两条自选指令及与循迹并行的完整链路仍待验证。当前S2首弯问题没有新的修复版本或成功证据。

设备实读为COM10、K230D Lushanpi Lite 128M、固件K230D-v1.8-0-gc2d1f5cc994c206d0032aaf6aaf09332f3dc3c4c。主机时间2026-11-24，板内文件mtime存在2025／2026混用，不据其推定开发先后或测试日期。根目录没有`/sdcard/main.py`，板上开发说明也明确语音入口已改名停用；不将源码头部“开机常驻”当成当前自启动事实。

## 已读源码与实际作用

以下均为本次保存的板上副本，不是新增正式运行源码。所有原文件大小／SHA-256和读取前后元数据见[review.json](review.json)、[collection.json](collection.json)，汇总见[summary.json](summary.json)。系统库和官方示例全集未逐份审阅。

| 板上文件 | 已读实现 | 可以确认的进度及边界 |
| --- | --- | --- |
| `/sdcard/qoder_scripts/voice_assistant.py` | 16kHz单声道录音，每块4800采样；KPU `multi_kws`与缓存做关键词识别，阈值0.5、冷却800ms；GPIO10功放，UART2 GPIO11／12、115200；四类事件对应WAV | 小南小南→回应；Go→三帧v5 START再回应；Stop→三帧v5 STOP再回应；Wow→回应。没有相机、路径包、收包／执行回执或判圈 |
| `/sdcard/qoder_scripts/main_voice.py` | `exec`读取上述助手，打印中断／异常 | 当前为独立入口备份，不是`main.py`，未启用上电自启 |
| `/sdcard/qoder_scripts/wifi_debug_track.py` | 灰度320×240、Sensor2、按条带黑块及地平线筛选、两组点拟合；MJPEG 8080，网页／单图／遥测JSON | 目标12fps，输出`valid/err/conf/det_ms`；不初始化UART、不发路径或运动命令。本轮没有实际帧率／浏览器画面证据；源码声称桌面328帧验证，原报告未提供 |
| `/sdcard/qoder_scripts/bench_uart_flood.py` | 等10秒后连续8秒发送v5 STOP帧 | 已有压力发送工具；本轮无F407解析器计数或实际运行记录，不是UART联调已通过 |
| `/sdcard/qoder_scripts/main_nopc.py` | 预热后等待3秒、蜂鸣提示，计划300张320×240灰度原图，默认不保存调试图，目标周期200ms，输出`/data/captures/dataset` | 工具源码已存在；当前目标目录清单为空，不推定已经采满300张；每次上电执行取决于是否复制到main.py |
| `/data/final_sampling_gc2093/01_spot_gray.py` | calib模式两张／static五张、锁曝光、原图与调试图分开、CSV | 已有静态采图工具；配置Sensor1；不能直接与当前Sensor2视觉入口混用 |
| `/data/final_sampling_gc2093/02_motion_gray.py` | 蜂鸣、300张连续灰度采集、原图／调试图／CSV，当前目标100ms | 连续采集工具存在；读出的动态CSV损坏，实际张数／间隔待核实 |
| `/data/final_sampling_gc2093/03_reference_color.py` | 1280×960 RGB565参考照片及CSV，安装高度／俯角当前为0占位 | 有彩色参考采集工具，不是高度／俯角已测或全图标定 |
| `/sdcard/main_false.py` | 直道300张采图，200ms目标、Sensor1、水平／垂直翻转、5秒等待 | 另一份独立采集版本；不是当前自启动入口。与Sensor2不翻转的正式R8视野约定不同 |
| `/sdcard/vision_classify.py` | TF图片的蔬菜分类示例，CHW／AI2D／KPU，硬编码9张示例 | 文件头“相机损坏”“9/9、2–3ms”是旧注释，无当前测试证据；不是赛道识别成果。当前清单未找到所需`veg_cls.kmodel`，不当作可直接运行的当前能力 |
| `/sdcard/mcp_script.py` | 打印空闲内存和分类脚本大小 | 存在性探针，无循迹／语音功能 |
| `/sdcard/right_angle_drive_r7.py`、`right_angle_drive_r8.py` | 既有v5首弯合并应用；已阅读R8及R7差异，含网格／当前L／圆弧路径／UART／日志与清理 | 与仓库`release_r7_storage`和`release_r8_entry`分别逐字节一致；R8仍同步写日志，不能记录为这次已修复时序阻塞 |
| `/sdcard/main.py.bak` | 既有trace-v3整圈候选备份 | 与仓库`runtime_trace_candidate_03/main.py`逐字节一致；不是本次新增或当前启用入口 |

`/data`中有三份程序，尚未统一到板上开发说明约定的`/sdcard/qoder_scripts`。本次按原位读取，没有迁移／覆盖。旧程序和新程序关系已记录，不能仅按文件名选择运行。

## 语音资源与历史证据

[resources.json](resources.json)记录模型、WAV及语音日志原件的读取清单，模型与音频原件保留本机。主程序实际加载`/sdcard/examples/kmodel/multi_kws.kmodel`，374640字节、SHA-256 `e8966b1daa5bd86b533cd2c6467a7a1c35e3d5b1359f12366bf5fba66cac4987`，与`/data/models/multi_kws.kmodel`相同；另有`kws.kmodel`，本助手不加载。模型标签语义来自代码映射与历史输出，本轮未运行模型或追溯训练资料。

四份回应文件均可读取为16kHz、16位、单声道PCM WAV：`wozai.wav` 0.550秒，`go_new.wav` 2.424秒，`stop_new.wav` 2.232秒，`wow_new.wav` 3.264秒。助手代码将单声道转入双声道右路播放。文件存在及格式不证明车载扬声器实际清晰；本轮没有试听或试播。

- [events.log](board_snapshot/data/voice_test/events.log)：94条chunk输出，包含“小南小南0.998、Go0.999、Stop1.000”各一次识别事件，结束为`Exception('IDE interrupt',)`。这是板上留存的历史日志；不是识别准确率测试、不是本轮新实测，也没有Wow识别事件。
- [uart_events.log](board_snapshot/data/voice_test/uart_events.log)：88条心跳，最高`chunk1760`，采样输出均为background；没有`[识别]`或`[UART]`事件，结束为IDE中断。不能由没有事件推定当时说过指令或识别失败，也不能推定UART发帧已成功。
- 两份日志格式不同，前者逐chunk输出，和当前助手每20块输出的代码不一致；无源码哈希／会话日期绑定，不能把旧识别日志认证为当前最终源码完整运行通过。
- `/data/voice_test/session.wav`为0字节，无法回听输入。日志未给识别开始、发帧／接收、车轮停稳的统一时轴，不能据此证明3秒接管要求。

## 采集资料

[collection.json](collection.json)清单与CSV表明`spot_gray`有20张原图＋20张调试图，CSV20条记录均标`c02_d020_center／20cm／0偏航／0横偏`；`reference_color`有两张照片及两条CSV记录。本轮未下载或目视核验这些图片，不用标签推定多距离标定或真实安装尺寸。

`/data/captures/d01_straight_run01`通过官方`io.listDir`枚举超时；单独读取的[collect_log.csv](board_snapshot/data/captures/d01_straight_run01/collect_log.csv)为30395字节，包含非UTF-8字节，表头、字段名及数值均有损坏，UTF-8在偏移11失败。按原字节保留，不能可靠计算帧数、采样间隔或据此认定源码注释中的328帧验证通过。根因未确定，可能涉及存储或读取链路，不能断言是哪一方损坏；本任务不修卡、不删除、不重采。

## 对比赛能力与下一步的影响

依据[比赛第三部分／图1／表1](../../../competition/比赛文档.md)，优先保住基本功能60分对应的顺时针5分钟内一圈与投影／触边约束，同时逐项完善额外功能40分；源码和可复核证据支撑报告20分。官方没有公布语音各分项分值，本次不报预计已得几分。

| 要求／风险 | 当前事实 | 后续需要的结果与证据 |
| --- | --- | --- |
| 语音启动 | 有真实识别事件和START封包源码；仓库`lap_motion_receive`仍对START计`starts_rejected`，没有运动许可；本轮未读STM32 Flash | 主控指派后协调允许状态和启动接口，留真实识别→接收→允许出发的证据，保留既有保护；避免把发送端回应误当车辆已执行 |
| 接管后3秒内停稳 | STOP先于播报发送；发送函数未检查`uart.write`返回值，无ACK；STM32合法STOP会撤驱动，仍不等于停稳 | 实际冲线后语音时刻、识别／接收、减速与停稳同轴证据；避免虚报40分功能或因处理阻塞延误停车 |
| 清晰语音应答 | 四个回应资源与播放代码存在，历史日志写startup播放；当前没有可复听输出证据 | 车端实际识别与清晰回应，区分请求收到和动作已完成 |
| 不少于2条自选指令 | 明确的额外词仅Wow；唤醒词“小南小南”能否作为另一条独立创意指令尚无语义／演示定义 | 视觉与主控明确两条自选语义及现场演示；不先判已满足官方数量要求 |
| 语音与循迹同时工作 | 当前是独立应用；录音块本身300ms，串行WAV播放0.55–3.264秒期间不做下一次识别；R8路径保护200ms且已有关联日志阻塞失败 | 后续执行任务解决并发／排队／UART唯一发送者，记录路径源年龄和最长发包空档；不能简单把阻塞语音循环塞入路径循环 |
| 车线／首弯／整圈 | S3的`err`取支持最多那条边界在y200的x，既不固定左／右，也不是双边中心线；未接UART。R7／R8字节未变 | 图传只作诊断，不能把S3 err直接替换现有转向；继续原I-04时序问题，之后再验完整首弯与整圈 |
| 图传与比赛边界 | 只有调试HTTP输出，无遥控接口；源码和板上说明拟用于手机调参 | 不能要求正式测试场外架设设备或依赖外部处理；正式运行方式仍按官方规则及主控确认，不能把板上README当补充规则 |
| 证据与版本可靠性 | 动态CSV损坏、声音原录音为空；UART日志以`w`覆盖，缺时间／源码绑定；词分数不是统计准确率 | 后续任务保留原会话、版本和必要时序，减少重测、丢证和报告误写；本次不扩展修改实现 |

## 本次读取行为与交付范围

实际RPC仅有`connectBoard/scriptRunning/io.listDir/io.queryFileStat/io.readFile/disconnectBoard`；请求审计及原始RPC哈希在[summary.json](summary.json)。没有发出`runScript`、`io.writeFile`、删除或运动请求。每次连接／断开均出现软重启输出，连接后`running=false`不证明连接前状态；本轮不是不打断设备的旁路观察。最后已断开后端，没有恢复自启动或任何应用。

第一次扩展读取存在命令行JSON参数解析失败，记录为[failed_argument_review.json](failed_argument_review.json)，此后固定读取目录。目录枚举超时原样留在collection清单，不因主流程结束标记`completed=true`而当作该目录读取成功。

新应用代码全文已读；R7／R8／旧启动备份核对一致，复用已归档版本证据。本次未运行应用测试或整车验证，仅核对本地快照、既有版本、资源格式、日志、文档路径和Git范围，结果见[checks.json](checks.json)。

图传原文件含队内热点口令，原件与含其Base64的RPC仅保留本机并由本目录`.gitignore`排除；提交[脱敏图传副本](board_snapshot/sdcard/qoder_scripts/wifi_debug_track.redacted.py)、原件哈希和请求审计。模型／WAV及顺带读出的固件示例词典原件也保留本机，仓库仅记录清单；敏感原件不随Git交接。其余项目源码／必要日志快照按原字节保存，不能直接把证据副本作为新的部署入口。
