# Tests：电脑模型与逻辑验证

2026-10-25从control/tests迁移至Tests/Host；维护：主控／01。

Host保存原test_*.c和fakes子目录。4个测试文件中直接包含真实.c的6个相对路径已同步更新；fake搜索路径仍先于真实设备头，电脑不访问板卡。

执行入口继续在tools中：run_host_tests、run_motor_bench_tests、run_motor_bench_startup_tests、run_motor_bench_pwm_diag_tests、run_motor_continuous_tests、run_motor_direct_tests（均为.ps1）。六个脚本共运行八组程序，Continuous与Direct各含启动回归。

输出留control/build，验证摘要见[validation.md](../docs/validation.md)。电脑模型不替代实际电压、波形或起转验收。
