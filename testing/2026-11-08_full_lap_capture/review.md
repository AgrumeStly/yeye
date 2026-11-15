# V-06：上电整圈手推采集交付

后续实采已完成：主控手推两圈并确认整车越过终点后停下，完整文件已下载校验，见[两圈接收与回放](../2026-11-08_two_lap_review/review.md)。许可已消耗，当前不再是本页部署时“已开启一次许可”的状态；首次真实采集正常收尾，但蜂鸣听感／物理电源操作细节没有新反馈。

日期：2026-11-08。主控要求“写一个拍整圈的代码，跟拍77度弯类似”。本轮沿用已实采的蜂鸣采集流程，独立新增整圈入口并切换现有板上main.py；现场手推由主控执行，不启动正式采样、不操作STM32或电机。

## 后续防误拍保护（当前板上版本）

主控指出Type-C重连也会上电，已在同一整圈源码加入`run_once_if_armed()`：只接受`/sdcard/full_lap_capture.arm`内精确的`full_lap_once_v1`加换行，先删除／同步许可，再调用原采集流程；缺失或残缺许可保持待机，其他读卡／删除／同步错误禁止进入相机。失败不会自动重建许可。不能识别供电来源，重新开启后下一次Type-C上电也会使用许可。

- [21项电脑检查](startup_verification.json)通过，入口许可7项涵盖缺失／正常／残缺、采集失败、读／删／同步异常；复用原13项采图故障模型，并实际用临时文件跑完整180秒虚拟采集1800张，随后二次入口不增加拍摄或改任何模型原件。可复现命令：`vision/.venv/Scripts/python.exe vision/tools/test_full_lap_capture.py`。相机／时钟为模型，非实板长采。
- 重新保存main.py并回读至[当前板上源码](deployed_once_main.py)，AST与本地去除文档字符串后相同，见[deployment_once.json](deployment_once.json)。原先[deployed_main.py](deployed_main.py)和[deployment.json](deployment.json)保留为首版历史。
- 在尚无许可时，实体板连续两次执行已保存main.py，都输出`[FULL_LAP_STANDBY] Not armed; existing captures untouched`并停止；前后captures目录逐项清单一致，没有新建会话，见[standby_board_check.json](standby_board_check.json)。这是执行入口验证，尚未物理拔插Type-C或电源重启。
- 两次待机验证完成后才写入一次许可，回读内容正确，末次running=false；供主控下一次现场上电使用。没有消耗正式采样许可、启动相机、蜂鸣或整圈采集。需要重拍时先检查部分文件，再由电脑明确重新开启，旧会话不删除。

这项保护避免重连时误采、误选会话或占满存储，支撑基本功能60分的可靠视觉开发与报告20分的证据追溯；不代表取得官方加分或自动完赛。以下14项及首次部署内容为加入保护前历史，当前以本节为准。

## 变更与交付

- [整圈源码](../../vision/src/capture_full_lap_canmv.py)：可单文件保存为main.py，无电脑端模块依赖。SCENE=full_lap，准备15秒、采集180秒、100ms最小间隔、MAX_FRAMES=2400、启动余量64MiB；其余相机、蜂鸣、原子文件提交、故障及收尾流程沿用77°版本。
- [操作说明](../../vision/docs/capture_full_lap.md)：起终点前开始、完整顺时针一圈、回到虚线越线后再前进一小段、原地等双长音后关电。保存的是连续JPEG与日志，电脑另生成视频；程序不自动判断完成一圈。
- 原77°源码保持，[此前板上main.py](previous_main.py)已先读取备份；[本次板上回读](deployed_main.py)与本地去除文档字符串后的AST一致。扩展自动压缩注释／文档字符串，字节不要求相同。

## 实际检查与边界

1. 已读项目技能、协作标准、状态页、V-06、当前视觉入口，以及比赛全文／图1／评分表；先读取本机CanMV资源概览、灰度snapshot示例和machine.pyi的PWM定义。未新增硬件API。
2. 把已有13项故障模型绑定到新增整圈入口，全部通过；另运行完整180000ms虚拟采集，真实临时文件共1800张模型JPEG经既有schema2校验通过。准备期15000ms、开始／结束提示和时钟回绕检查通过。共14项，见[verification.json](verification.json)。未新增或改旧测试／校验器；这不是实板180秒或实际路线验收。
3. COM10，CanMV K230D Lushanpi Lite 128M，固件v1.8-0。写入前查询running=false，回读原main.py确认corner_77／45000ms后本地备份；调用save_main_py保存整圈源码，回读确认full_lap／180000ms／2400／64MiB。见[deployment.json](deployment.json)，包含源码／回读／备份哈希与AST核验。
4. 仅运行无相机／蜂鸣／运动控制的statvfs空间查询，得到`[FULL_LAP_SPACE] 101515264`（约96.8MiB）；末次查询running=false。终端缓冲带有旧IDE interrupt记录，不作为本次查询或整圈程序失败；本轮标记单独保存于[space_check.txt](space_check.txt)。
5. 未重启板卡、启动整圈正式采集、删除旧文件或改boot.py；相机安装、冻结R1／C1、STM32及全局摘要未改。真实长采、冷启动、声音听感与路线覆盖由主控现场核验；两声结束音只证明写卡／收尾成功。

## 比赛依据与接续

比赛第三部分与图1要求顺时针一圈≤5分钟、触边扣分／完全出界失败；基本功能60分、报告20分。本项补齐全圈观测、定位弯道失线和起终点识别问题，预期降低后续触边／出界风险，不承诺官方得分。180秒是采样配置，不是官方新时限；现场连续黑条不能代替官方离散色块验收。

来源分支codex/current-version-20261025，HEAD a0733a8685db4c2b497539303bfe87fe1c1ebfe5。共享既有改动全部保留，仅本地保存与板上采样入口切换，未提交／上传、切分支或跨聊天发送。下一步为主控按操作说明手推整圈，收到新会话后检查文件完整性与全部路段覆盖，再进行离线算法开发。V-06仍进行中。
