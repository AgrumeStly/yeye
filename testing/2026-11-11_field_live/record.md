# I-02：现场实时视觉与历史证据复用

日期：2026-11-11。责任：主控现场操作，本对话保存执行证据；不代替00更新全局状态。

## 本轮已取得的新增事实

主控回复“是的已就位”，按前序明确操作上下文确认已在最终场地直道、相机安装保持、电机动力XT30断开、两逻辑板沿用DAPLink／电脑USB供电。本轮仅运行10秒live_no_drive，没有按KEY启动、有效路径放行、烧录或改写板上main.py。

[straight_center_01](straight_center_01/summary.json)正常完成并保存5张原始预览JPEG。终端打印17条样本（全部无效帧及每10个有效帧打印），其中13条有效候选的steering均+43；所有打印样本wire_valid及drive_allowed均false。打印样本processing为43..57ms、相邻周期65..88ms；不外推全部帧统计或实际纠偏正确性。预览帧号来自IDE传输，不等于算法索引，不宣称逐帧精确配对。尚未验证地面运动或整圈。

## 主控指出重复后的流程纠正

助手随后提出左移约5cm重做静态方向验证，主控指出此前已做。核对[V-03](../../project_planning/tasks/V-03.md)和[五姿态总报告](../2026-11-08_vision_restart/static_review.md)，2026-11-08最终安装五姿态15张已齐全：居中参考行偏差0，左移约+27..+27.5px，右移−24.5px，左右偏航分别+32及−44.5px。此前[L1检查](../2026-11-09_low_speed_lap/l1_checks_06/checks.json)及[runtime_r4检查](../2026-11-09_low_speed_lap/runtime_r4_checks/checks.json)也已复用真实样本验证候选方向。

因此撤回本次左偏摆位要求，不把既有五姿态重新列为未做。旧静态图像偏差、软件方向检查、固定输入悬空差速和真实视觉带动车轮分别保留各自证据范围。当前R5与既有结果的对应关系可优先用保存的原图及源码在电脑核对；没有明确新问题时不要求主控重采整套姿态。光照变化或新版本需要验证时，应先指出具体疑点及最少补测范围。

下一阶段聚焦尚无证据的真实视觉到主板再到轮速的完整链路，之后才是短距离地面运动；车载逻辑供电／冷启动仍需单独验证。不得因省略重复姿态而直接放行地面整圈。比赛关联为基本功能60分中的可靠完赛及避免触边／出界，现有诊断不折算实测得分。

## 最新接续执行：真实相机有效路径到主板

主控澄清“摄像头移动”为整车挪位，已放回赛道中间，相机在车上的安装没有移动。未重采五姿态。电脑方向复核见[direction_review_01](direction_review_01/review.md)：复用R5原42项及15张原图／5张现场预览，只做针对性合成时刻回放；转向右正与左右轮映射一致。旧R1偏航通过不等同R5四帧内取得许可，后续按有限搜索实际重捕获证据判断。

新增prepare_lap_visual_link.py及助手live_link_isolated／live_link_suspended显式模式。默认禁止驱动；许可模式只接受冻结R5实时相机，动力隔离或悬空／09／3000ms／当前校准门槛在连接前检查，保留所有算法与故障监督，不发START、不写main.py。两次电脑检查器自身失败及修复分别保留visual_link_checks_01／02；[55项入口检查](visual_link_checks_03/checks.json)及[原助手30项回归](helper_regression_01/checks.json)通过。没有更改STM32固件或重烧。

本轮有专用CanMV连接器可用，重新检测K230 COM10／v1.8-0；主机串口枚举另见DAPLink COM9。无脚本所有权冲突，实跑使用专用连接器，不并开旧后端。一次CIM端口查询权限拒绝不影响专用连接器和串口枚举结果，没有据此做板卡通过声明。

主控未重开Keil，按动力隔离下打开LowSpeedLap→Reset CPU→Run5秒操作后提供[零基线原图](visual_link_isolated_01/baseline_watch.png)：revision09、speed_fault0、state0／reason0、received／path_valid／PWM0；其余run_ms3000、phase0／error0／UART0按“其他符合预期”人工确认。

[真实相机动力隔离窗口](visual_link_isolated_01/summary.json)实跑120秒正常完成，结束running=false；精确执行源码SHA256 `664428762ea755b3937defdb348aae74cbd8e3825129de4391ad1e686b4dccb1`。日志167条抽样，最高index1630，163条有效样本，前4帧无效，后段steering／bend从+43／343变为0／0；processing27..59ms、日志样本周期46..87ms。不是总帧统计。IDE图传关闭，无新图，不写SD／main.py。旧mcp_terminal_snapshot.json保留中段快照，最终完整文本在mcp_terminal_final.json和terminal.txt。

主控实报steering0／bend0与后段发送值一致，补核接收计数递增、path_valid、UART0及两PWM0后回复“符合预期”。[接收反馈](visual_link_isolated_01/stm32_review.json)按人工初验记录，未补造独立received总数或截图，未单独归档读数时刻。正常结束STOP清路径许可是预期，后续不能复用过期许可启动。

当前一步：脚本已结束，专用连接器保持会话；主控只需驱动OFF／XT30断开时支稳底盘、确认两轮完全悬空，未指导接动力或按KEY。之后按当前复位后phase0恢复两次500ms单轮校准，才运行真实视觉悬空入口。车载带载／冷启动／持续入口、地面短线／弯／一圈均待验；任务保持进行中。

## 真实相机悬空运行已取得，R6修复与主控暂停位置（最新）

主控回复“已悬空”，依次确认动力接通后静止／PWM0、左轮单次500ms前进校准、右轮单次500ms前进校准和phase2／error0／state1／UART0／3000ms。各次操作只安排一个现场动作，未重复旧固定输入台架。

随后[visual_link_suspended_01](visual_link_suspended_01/stm32_review.json)以冻结R5真实相机运行，十分钟仅输入等待，主板单次仍3000ms。主控单次KEY后提供[原始快照](visual_link_suspended_01/last_run_watch.png)，valid1、elapsed_ms3000、LIMIT11；左右目标39.6526489／40.1313553RPM、反馈40.3884392／39.9326859RPM、撤驱动前PWM20.1%／19.7%、起步补偿各1样本，并反馈轮子符合预期。之后驱动OFF、当前两PWM0／UART0的明确步骤获“是”确认。验收一次真实相机到UART到独立轮速及自动停止的悬空链路；不是连续500ms稳定统计、大幅差速、地面或一圈。

本对话在该实物测试后主动结束自己的剩余相机等待窗口，确认running=false；因此summary中的normal_completion=false属于预期人工缩短窗口，不是主板LIMIT失败，也不当600秒持续运行通过。原始终端分块保留，避免MCP缓冲增长覆盖前段，见session_result.json。主板没有重烧／改参数。

### R5斜线误删已定位并准备R6

两张旧偏航原图各50次合成输入仍unknown，网格内一侧边界消失。源码用整个组件的横向包围盒宽度判断ROI上沿宽厚背景，斜向真实边界因从近到远横跨多列被整条误删；原左／右偏航图剩余黑格72／62、双边参照均0。R6改为只计算ROI上沿这一行的实际黑格宽度，保留原面积、组件分离、白走廊、模板支持、连续双帧及全部协议时限，不补画像素。

独立[board_bundle_runtime_r6](board_bundle_runtime_r6/manifest.json)SHA256 `de2341cafcdadf2d843a566dafeef28ae4439c041aec15f7ee709e7afd738fcf`，R5冻结文件未动；修改源vision/src/lite_lap_route.py有中文原因和边界注释。原[42项回归](runtime_r6_checks_01/checks.json)及[37项偏航原图检查](runtime_r6_yaw_checks_01/checks.json)通过；左右偏航第二帧分别+273／−364、当前双边，单带／文字负例仍拒绝。额外检查核对每个保留黑格均来自原灰度采样，未虚构边界。全部只是电脑原图模型，不能冒充动态性能。

入口扩展R5／R6固定白名单哈希，新增[65项检查](visual_link_checks_04/checks.json)通过。随后保持驱动OFF，不按KEY，实际执行[runtime_r6_board_no_drive_01](runtime_r6_board_no_drive_01/summary.json)10秒：正常DONE、全部wire_valid／drive_allowed=false，16条日志样本、最高index130，processing43..72ms、日志周期73..107ms，未放宽门槛。保存并查看1张原始预览；第二次取新图时脚本已结束返回available=false，未重复运行补图。悬空视场不当作地面动态证据。

### 主控明确暂停

主控随后对驱动ON且仍悬空、phase2／error0／state1／UART0／PWM0／run_ms3000回复“符合”，启动[runtime_r6_suspended_01](runtime_r6_suspended_01/intent.json)真实相机窗口，已发出有效双边路径。仅指导主控一次KEY三秒试验，**尚未回报是否按键及实物结果**；随后主控说“先暂停一会继续”。不能推定已做、未做或通过。

收到暂停后立即停止本对话自己的脚本（原finally尽力STOP），只读取终端并确认running=false，显式断开专用连接器。暂停前日志105条样本、最高index1010、算法38..54ms、周期60..93ms；主动中断后normal_completion=false，非十分钟持续运行验收。详见[pause.json](runtime_r6_suspended_01/pause.json)。已指导主控驱动OFF、拔XT30并保持车辆稳固悬空，**物理断开尚无完成反馈**；没有继续启动或新设备写入。

暂停前另生成[runtime_r6_cold_boot_candidate](runtime_r6_cold_boot_candidate/README.md)持续相机main草稿，SHA256 `397d6a7d91983bffe7655704e727e458ca35f2b0910982dcdf53ad72e8aa5db1`。仅本地生成及语法检查，新增日志包装尚未做边界模型／实板RAM／写盘耗时检查，未部署、未请求写入。板上main仍10秒禁止驱动自检。恢复后先处理R6悬空是否已执行／结果，再补草稿检查与真实当前main备份，展示具体部署／回读步骤后取得写入授权；车载带载／冷启动、地面短直道／单弯／锐角和顺时针一圈全部未验。暂停期间不继续独立实现或测试。

供电资料只做了官方网页核查：立创FAQ仍没有明确给出本次5.20V允许容差，不能当两板带载合格；亚博介绍网页无可提取正文，沿用已归档标称资料。未改线／带载测量，也未用标准K230原理图代替Lite实物电压验收。参考[立创FAQ](https://wiki.lckfb.com/zh-hans/lushan-pi-k230/faq.html)、[原理图说明](https://wiki.lckfb.com/zh-hans/lushan-pi-k230/open-source-hardware/diagram.html)、[官方对比页](https://openkits-wiki.easyeda.com/storage/html/k230-vs-k230d/index.html)，恢复后仍须完成供电实际证据。
