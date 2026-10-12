# 主控基础工程验证记录

日期：2026-10-12，北京时间。范围：到货前软件验证；无赛车、板卡或电机接入。

| 项目 | 方法 | 结果 |
| --- | --- | --- |
| Keil LogicDemo | Keil5.24a / ARMCC5.06u5实际编译链接 | 0错误、0警告；Code1860、RO424、RW12、ZI1108字节 |
| Keil HardwareBench | 同环境实际编译链接 | 0错误、0警告；Code1612、RO424、RW16、ZI1104字节 |
| 链接布局 | 核对Keil生成scatter文件 | FLASH0x08000000/0x80000，SRAM0x20000000/0x20000 |
| UART可选分支 | ARMCC单独编译board.c，BOARD_UART_ENABLE=1 | 编译通过；串口接收中断和缓冲代码未做板上验证 |
| PC通信与状态机 | GCC，C99，Wall/Wextra/Wconversion/Werror/pedantic | 55项检查全部通过 |
| Python编码示例 | 输出直道、无效路径、START、STOP、STATUS的20字节包 | 生成成功；直道固定字节向量与C编码器匹配 |
| Keil模拟器运行 | 命令行自动调试尝试 | 未取得日志；窗口检查工具不可用，模拟器执行待主控按说明人工确认 |
| 实物下载与控制 | 硬件尚未到货 | 未测试 |

## 电脑端实际输出

```text
PASS parser: CRC, split/concatenated frames, noise, corruption, truncation, format/range checks
PASS state: explicit start/stop, demands, duplicate/old frames, timeout, no auto-restart, invalid path, delayed processing, transport error, counter wrap/reboot
PASS end-to-end: wire bytes -> parser -> state; corrupted updates cannot keep vehicle running
PASS all 55 checks
```

覆盖：CRC标准向量与固定包、负数解码、分包/连包/噪声、截断恢复、字段越界、无路径拒绝启动、转向演示输出、重复帧不续命、200ms边界、晚到数据不能掩盖超时、恢复数据不自动启动、STOP优先和延迟START、低质量路径、处理耗时、接收故障、序号及毫秒计数回绕、板卡重启后序号基线重建。

不将电脑逻辑检查当成实车性能：HSI误差、实际帧率、UART引脚/电平、上下电、下载器连接、电机方向、编码器、PID、真实制动距离、一圈判定与语音链路均待硬件到货后验证。

原始可重建输出在control/build和control/firmware/build，Git忽略。主控修改通信或状态机后重新执行tools/run_host_tests.ps1和两个Keil目标编译，记录新的验证结果。
