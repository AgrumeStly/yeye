# Algorithms：纯数学算法

2026-10-25建立范围说明；维护：主控／01。

用于后续不直接访问GPIO、TIM、UART或中断寄存器的数学算法，例如PID计算、滤波或路径控制计算。输入、输出、单位和采样周期须通过头文件明确，可在电脑上独立测试。

2026-10-25 C-02C新增Encoder/encoder_counter.c、encoder_counter.h：16位模差、正反向／时间回绕、64位饱和累计、counts/s和丢窗状态，使用标准C且可在电脑独立验证。未标定CPR前不计算RPM／m/s。

当前尚无独立PID／tracking实现，本目录没有pid.c、tracking.c或占位函数。现有car.c的演示请求继续留App/Car，不把它改名后宣称闭环已完成。新增算法按实际功能任务实施。
