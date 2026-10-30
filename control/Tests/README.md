# Tests：电脑模型与逻辑验证

2026-10-25从control/tests迁移至Tests/Host；维护：主控／01。

Host保存原test_*.c和fakes子目录。4个测试文件中直接包含真实.c的6个相对路径已同步更新；fake搜索路径仍先于真实设备头，电脑不访问板卡。

执行入口继续在tools中：run_host_tests、run_motor_bench_tests、run_motor_bench_startup_tests、run_motor_bench_pwm_diag_tests、run_motor_continuous_tests、run_motor_direct_tests（均为.ps1）。六个脚本共运行八组程序，Continuous与Direct各含启动回归。

输出留control/build，验证摘要见[validation.md](../docs/validation.md)。电脑模型不替代实际电压、波形或起转验收。

C-02C新增test_encoder_counter.c、test_encoder_bench.c及fakes/encoder，通过tools/run_encoder_tests.ps1运行真实计数算法与真实Core／App／硬件适配边界模型；覆盖正反向、回绕、dt、独立累计、R1故障与零电机输出。原八组电机／通信程序未因本轮新增而更改，不反复重跑未受影响逻辑。
