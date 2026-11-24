==============================================
  K230D 存储与开发约定（请先看这个）
  最后整理：2026-11-22
==============================================

【最重要的一条：脚本和数据必须分开放】
- 脚本（.py）一律放：/sdcard/qoder_scripts/
- 大数据一律放：/data/（日志、录音、图片、视频、数据集）
- 绝对不能把录音/图片/日志写到 /sdcard，SD 卡会被撑爆，
  爆了会把系统脚本一起弄坏，整块卡都要重刷。
- 写新脚本时，凡是打开文件写入，路径先想三秒：
  这是脚本？→ /sdcard；这是数据？→ /data/自己的子目录。

【开机自启动规则】
- 只有 /sdcard/main.py 会开机自动运行，其它文件名都不会。
- 语音助手入口已改名停用：/sdcard/qoder_scripts/main_voice.py
  需要恢复语音开机自启：把 main_voice.py 复制为 /sdcard/main.py 再重启。
  需要撤销：把 /sdcard/main.py 改名或删除（切勿覆盖旧的 main.py.bak）。
- 视觉/寻路如果要自启，也走 main.py 这个唯一入口，先和队里协调。

【调试看图 / 比赛模式】
- 平时调参：跑 qoder_scripts/wifi_debug_track.py（MJPEG 8080），
  手机热点 + 浏览器 http://板子IP:8080/；画面含车道标注和读数（det ms 等）。
  单客户端；跑图传时不能再跑语音/寻路（一次一个脚本）。
- 以后整合版：寻路主循环优先；图传独立线程、只发最新帧、可降帧/关；
  语音命令排队交给主循环发。降级顺序：保寻路/停车 > 语音 > 图传。
- 场地调参：把调试版临时设为 /sdcard/main.py 自启，车自供电，手机场边看；
  调完删掉入口恢复干净。
- 正式跑分：规则禁止遥控/场外架设设备 → 关图传，只留语音；
  调参版和比赛版分开入口，避免误开。
- 兜底：USB/IDE 预览（有线），或录到 /data 回放（非实时）。
- 调试版建议把 det_ms、判定、已发命令写 /data 日志，便于对照。

【当前保留的脚本（qoder_scripts/）】
- voice_assistant.py : 常驻语音助手（小南小南/Go/Stop/Wow）
- main_voice.py      : 语音开机自启入口（当前停用）
- wifi_debug_track.py: 手机图传 S3（MJPEG 8080 + 车道标注 + 遥测）
- bench_uart_flood.py: UART 验收压力测试（连发 20B 帧，查解析器计数）
- main_nopc.py       : 无电脑现场采集工具（拍数据集用）

【examples 已精简（2026-11-22 按用户授权）】
- 已删除：除下面保留项外的演示模型、测试图片、手势库、面部库（约释放 366MB）。
- 保留：examples/kmodel/multi_kws.kmodel（语音识别用）
        examples/kmodel/kws.kmodel（以后自定义词可能用）
        examples/utils/ 的 4 个回应 wav（wozai/go_new/stop_new/wow_new）
        与语言资源 pinyin.txt / small_pinyin.txt / dict.txt / phone_map.txt
- 需要其它演示请从固件镜像恢复；不要再把大模型往 /sdcard 拷。
- 当前 /sdcard 剩余约 429MB（已用 14%）。

【禁止改动（不是我们的文件）】
- examples/（系统/固件自带；已按授权精简，勿再拷入大模型）
- libs/  res/  revision.txt
- main.py.bak  right_angle_drive_r7.py  right_angle_drive_r8.py
- vision_classify.py  main_false.py  （主控/视觉既有脚本）
- /data/right_angle_logs  /data/models  /data/migrated_20261119_sdcard
  （主控数据，未经同意不得删除）

【日志位置】
- 语音：/data/voice_test/（uart_events.log 等）
- 主控：/data/right_angle_logs/

【板子已知坑】
- /sdcard 不能被板内 MicroPython 写入（EPERM），脚本用 MCP/IDE 上传。
- 运行中脚本有时停不下来，按板上 RST 复位；停流后不要再原地改文件。
- 串口2 GH1.25-4P 线序：V(5V) R(GPIO12 RX) T(GPIO11 TX) G(GND)，
  5V 悬空不接；与 F407 USART2(PA2/PA3) 交叉接、共地。
- 20B 协议当前 TARGET_VER=5（主控 RightAngle v5）。
- 调试图传单客户端；有人看流时 /snapshot 和 /telem 会排队。
