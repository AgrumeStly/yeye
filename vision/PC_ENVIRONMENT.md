# 视觉电脑开发环境与安装记录

2026-11-08离线接续补记：为实际读取／渲染比赛PDF，在现有vision/.venv安装PyMuPDF 1.26.6；原OpenCV／NumPy／pySerial版本保持，pip check通过。完整本轮审核／回放工具依赖见[requirements-review.txt](requirements-review.txt)（原requirements-pc.txt另加此包）；算法模块本体不依赖PDF库，部分审核工具共用输入归档辅助模块时仍需安装。此依赖仅电脑使用，不安装到CanMV。[本轮证据](../testing/2026-11-08_vision_board_prep/review.md)。

日期：2026-11-06（北京时间）。负责角色：主控；本对话按主控“帮我安装”的授权完成电脑软件安装和本地检查。本页记录环境，不变更全局职责、STM32 固件、跨板协议或既有测试结论。

## 已准备的软件

| 项目 | 本机版本与位置 | 本轮结果 |
| --- | --- | --- |
| VS Code | 1.144.0，`D:\Program Files (x86)\Microsoft VS Code\Code.exe` | 复用已有安装 |
| 嘉楠 CanMV 扩展 | `kendryte747.canmv-vscode` 0.9.10 | 官方扩展已安装，Windows x64 后端文件存在；开发板连接待验证 |
| Python／Pylance 扩展 | `ms-python.python`、`ms-python.vscode-pylance` | 已有，无需重复安装 |
| 电脑端 Python | 3.13.6，`C:\Users\Agrum\AppData\Local\Programs\Python\Python313\python.exe` | 复用；单独创建 `vision/.venv/` |
| NumPy | 2.5.4 | 已从官方 PyPI 安装到独立环境 |
| OpenCV Python 包 | `opencv-python` 5.0.0.93，`cv2.__version__` 为 5.0.0 | 已从官方 PyPI 安装到独立环境 |
| pySerial | 3.5 | 已从官方 PyPI 安装到独立环境 |
| Git | 2.50.1.windows.1 | 复用已有安装 |
| Keil5／ARMCC | UV4 5.24a，ARMCC 5.06.0，`D:\software\Keil5\` | 文件存在，复用现有安装；本轮未构建固件 |
| K230BurningTool | 2.2.4，`vision/build/tools/k230-burning-tool-2.2.4/bin/K230BurningTool.exe` | 官方 Windows normal 包已解压，便携版无需系统安装；本轮未启动 GUI 或执行烧录 |
| Edge／Chrome | 已安装 | 可使用官方网页 IDE |

系统默认 `python` 指向另一个 Python 3.15。本项目视觉环境明确使用上述 3.13.6；本轮未更改系统 PATH 或默认 Python。

## 主控如何开始

1. 在 VS Code 中选择“文件 → 从文件打开工作区”，打开 [vision.code-workspace](vision.code-workspace)。也可在项目根目录终端执行 `code vision/vision.code-workspace`。
2. 工作区已指向 `.venv/Scripts/python.exe`；新建终端会优先使用该环境。若 VS Code 曾缓存其他解释器，运行 `Python: Select Interpreter`，选择 `D:\projects\projectsyeye\vision\.venv\Scripts\python.exe`。
3. 电脑端图片分析、日志与串口工具使用此 Python。CanMV 板上脚本使用 CanMV 扩展运行，不能把电脑安装的 OpenCV 当成板上图像接口。
4. 收到视觉板后先保留现有 TF 卡和采图程序。主控确认适合连接后，再在命令面板运行 `CanMV: Connect Board`／`CanMV: 连接开发板`。匹配固件的示例和代码提示资源需在实际连接后核对，不预设未知固件版本。
5. 备用工具可直接打开上述 `K230BurningTool.exe`。网页替代入口为 [CanMV IDE Web](https://wiki.lckfb.com/storage/html/canmv-web-ide/)。同一串口一次只由一个工具占用。

Windows 正常运行模式通常使用系统 USB CDC 驱动。本轮未更换任何设备驱动；如果以后需要烧录且 `K230 USB Boot Device` 未安装 WinUSB，再按官方教程对该设备单独安装。固件必须匹配 Lite-K230D 板型，并先备份已有数据。

## 本地验证证据

本轮实际运行通过：

- `vision/.venv/Scripts/python.exe -m pip check`：`No broken requirements found.`
- 导入 OpenCV、NumPy 和 pySerial，并读取实际版本。
- 对合成黑白图执行二值化、轮廓提取，核对矩形位置与尺寸。
- PNG 编解码往返后像素一致。
- 读取官方赛道图，尺寸为 1000×1020 像素、3 通道。
- pySerial `loop://` 收发20字节一致；这是内存回环，未打开任何实体 COM 口。
- 工作区 JSON 可解析，解释器、Keil 和烧录工具路径存在。

检查程序位于本机 `vision/build/verify_pc_environment.py`，原始结果位于 `vision/build/pc_environment_check.json`。`build/` 与 `.venv/` 按现有 Git 规则忽略，跨设备不会自动同步。正式实拍采图、K230D 与 STM32 实物串口、视觉帧率和整车循迹仍待验证。

备用工具下载压缩包 SHA-256：`92a8aeaff25725cd61d2d1b1fcd3d28a159383b53d13151dc20a2d6d75759ac8`。此为本机计算的归档标识，不是独立厂商签名验证。

## 重建电脑 Python 环境

在项目根目录 PowerShell 执行，已有环境可直接执行第二条：

```powershell
& 'C:\Users\Agrum\AppData\Local\Programs\Python\Python313\python.exe' -m venv vision/.venv
vision/.venv/Scripts/python.exe -m pip install --only-binary=:all: --index-url https://pypi.org/simple -r vision/requirements-pc.txt
vision/.venv/Scripts/python.exe -m pip check
```

其他电脑将第一条解释器路径替换为实际 Python 3.13 路径。[requirements-pc.txt](requirements-pc.txt)固定本轮验证版本。

## 比赛得分关联与边界

依据[比赛要求及评分表](../competition/比赛文档.md)和[赛道图](../competition/assets/track_figure_1.jpg)：图像回放支撑边界／锐角识别与基本功能60分，串口工具支撑控制联调和额外功能40分中的语音／停车链路，版本与日志支撑报告20分。预期作用是减少环境问题、通信错误和无法复现的调参，避免影响完赛与触边风险；本次验收指标是依赖一致、图像实际可处理、软件回环正确，不能据此声称已有实测得分收益或整车通过。

## 官方来源

- [立创快速上手：开发环境、板型、驱动和固件区别](https://wiki.lckfb.com/zh-hans/lushan-pi-k230/quick-start.html)
- [嘉楠 CanMV 扩展源码与安装要求](https://github.com/kendryte/canmv-vscode-extension/tree/main/extension)
- [K230BurningTool 官方下载目录](https://download.kendryte.com/developer/tools/k230_burningtool/v2.2.4/)，下载文件为 `K230BurningTool-windows-normal-v2.2.4-0-g2de4350.zip`
- [OpenCV Python 包](https://pypi.org/project/opencv-python/)、[NumPy](https://pypi.org/project/numpy/)、[pySerial](https://pypi.org/project/pyserial/)
