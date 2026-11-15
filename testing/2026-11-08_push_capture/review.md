# V-06：上电蜂鸣提示手推采集交付

日期：2026-11-08。主控本轮要求编写车载电池上电、延迟、蜂鸣开始／结束的摄像程序，并明确手推起止点。本对话完成代码、电脑模型、现有USB连接下短时板测、完整下载检查及自启动文件部署，不操作电机或修改STM32。

## 实际交付

- [源码](../../vision/src/capture_push_canmv.py)：独立可运行，准备15秒、开始1长音、记录45秒、文件与资源收尾成功后2长音、失败5短音×2组；当前场景corner_77。不依赖旧采集脚本，不修改冻结R1／C1或静态采集程序。
- [操作说明与路线](../../vision/docs/capture_push.md)：从左侧入口斜直道内角前约60cm开始，顺时针手推完整锐角，到车头对准出口并沿出口前进约40cm结束；先停推等完成提示再关电。这是队内采样安排，不是官方赛道新增标记或运动轨迹验收。
- [PC校验器](../../vision/tools/verify_push_capture.py)、[故障模型](../../vision/tools/test_push_capture.py)：独立schema2，原schema1校验器不变。
- 正式版本已保存`/sdcard/main.py`，写入前/sdcard和根目录列举显示没有main.py／boot.py；未删改旧mcp_script.py、vision_classify.py、main_false.py及captures。使用CanMV save_main_py工具成功；[板上回读源码](deployed_main.py)10989字节，移除本地文档字符串后AST逐项一致。扩展自动去掉注释／文档字符串，因此两份文件字节哈希不同属于预期；[交付清单](delivery.json)记录各SHA-256。

## 已做验证

实板：COM10、CanMV K230D Lushanpi Lite 128M、K230D-v1.8-0-gc2d1f5cc994c206d0032aaf6aaf09332f3dc3c4c。先读取本机CanMV示例／stubs和厂家PWM、离线启动文档；os.uname()报告k230d_canmv_lushanpi_lite，蜂鸣器用GPIO61／PWM1，statvfs报告可用113410048字节（约108MiB）。

1. 临时运行[短测源码](board_smoke_source.py)：只将scene改board_smoke、准备改1秒、采集改3秒、预热改10帧；正式配置仍15秒／45秒／30帧。
2. 终端完整执行PUSH_START、BEEPER、PUSH_PREPARE、PUSH_RECORDING、PUSH_FILES_CLOSED、PUSH_DONE，无新异常，最终script_running=false。[筛选终端](board_smoke_terminal_filtered.txt)只保留本轮标记行；原缓冲混有之前静态采样记录，不把旧输出算本次结果。蜂鸣PWM调用成功不等于主控已经确认听见。
3. 新会话`/sdcard/captures/push_board_smoke_0001`的27个文件全部下载到[board_smoke](board_smoke/)；其中25张JPEG、session.json、frames.jsonl。元数据complete、cleanup_errors=[]、stop_reason=duration_reached，采集软件窗口3001ms；全部哈希／320×240单通道灰度解码／时序通过，见[校验结果](board_smoke_verification.json)。首张原图已查看，为当前室内场地静止画面，不是手推或锐角正确率证据。
4. 实测保存间隔中位113.5ms、p95约157ms、最大182ms，首末帧软件时间平均约8.50张／秒；目标100ms间隔不保证10fps，实际曝光／K230识别实时性不由此推断。
5. 执行`vision/.venv/Scripts/python.exe vision/tools/test_push_capture.py`退出0，13项通过：限时／回绕、成功提示晚于释放与元数据落盘、重复新建不覆盖、预检写卡失败不发开始提示、中途卡满保留部分、主动中断、无卡、空间不足、清理失败、最终元数据失败、实际图像格式错误、错误标签／帧数保护、复制后损坏检测及EEXIST替换。部分断言合并在同一测试中。
6. 再次检查前序C1 protected_hashes.json中870个原件／证据／冻结源码字节全部未改。没有重复覆盖旧证据或运行旧全量回归。

保存main.py后未重启板卡，最后查询script_running=false；首次真实冷启动、脱离USB后的电池供电、45秒长采、提示音实际听感及主控手推路线覆盖都待现场确认。程序不包含UART或电机控制，但不能阻止另一个主控板应用驱动电机，现场须实际断开电机动力。视觉板电池供电路径尚无本轮实测记录，已异步询问主控，不能将待回答当确认。

## 版本、规则与接续

目录D:/projects/projectsyeye，分支codex/current-version-20261025，来源HEAD a0733a8685db4c2b497539303bfe87fe1c1ebfe5。本轮及大量前序共享改动未提交／未上传，保留control和其它共享文件；未切分支、更新00全局摘要或远端。当前新增自启动main.py是本轮上电采样明确请求的落实，覆盖前序“本轮不写main.py”的阶段边界；没有重刷、格式化、删除旧应用或自动带动力试跑。

依据比赛第三部分、图1及评分表：50cm净宽、顺时针一圈≤5分钟、触边扣分／完全出界失败，基本功能60分、报告20分。本项补连续进出锐角的视场证据、避免虚假完成提示，预期支持定位迟转／失线／文字错配并减少后续出界风险，无官方得分收益或实车通过结论。

当前下一步：主控核对视觉板车载稳压供电方式并按操作说明执行一趟锐角手推，完整保留新会话；本对话收到数据后做schema2校验与R1／C1回放，检查单边缺失持续区间及出口恢复。V-06仍进行中，尚未验收自动通过。
