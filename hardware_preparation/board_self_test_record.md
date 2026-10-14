# 天空星主控板首次测试记录

日期：2026-10-14（北京时间）。板卡：立创天空星 STM32F407VET6；连接：台式机USB Type-A → 板卡Type-C。固件采用 STM32F4 标准外设库（SPL），Keil目标为 BoardSelfTest。

| 检查 | 实际结果 | 证据与范围 |
| --- | --- | --- |
| ROM下载设备 | 通过 | 进入BOOT0下载模式后识别到VID_0483/PID_DF11 |
| Windows驱动 | 通过 | ST签名WinUSB驱动安装成功，设备状态正常 |
| Keil编译链接 | 通过 | ARMCC 5.06 update 5；0错误、0警告 |
| 既有Flash备份 | 完成 | 烧录前读取512KiB，保存在台式机本地 |
| 固件写入 | 通过 | 从0x08000000写入1868字节 |
| 固件读回 | 通过 | 1868字节逐字节一致，SHA256一致 |
| 复位启动 | 通过 | 主控松开BOOT0并按RESET后确认“双闪正常” |
| PB2用户灯、SysTick | 通过基础检查 | 实际运行双闪；节奏尚未做仪器测量 |
| 时钟配置、小块RAM | 通过程序自检 | 正常双闪对应16MHz配置值检查、128字节专用缓冲区读写无失败 |
| 电机、编码器、视觉UART、整车闭环 | 未测试 | 本固件没有配置这些功能 |

已烧录BIN的SHA256：

```text
36aabc410b125cbd84284875c1d5d7836a315b181b78d7a2ceda24faef07872e
```

固件大小：Code 1380、RO 440、RW 48、ZI 1152字节。BIN为1868字节。RAM检查仅覆盖专用128字节区域；时钟检查读取软件配置值，不代表已经测量HSI频率或完成整板验收。

本地原始记录位于 `tmp/board_tools/`：`driver_install.log`、`flash_backup.log`、`flash_write.log`、`flash_verify.log`、`flash_result.json`。既有固件备份为 `flash_before_test.bin`。这些临时文件及编译输出不纳入Git，换电脑前按需要单独保存。

程序和复测方法见 [主控板级测试说明](../control/docs/board_self_test.md)。本次源代码与说明仅保存本地，等待主控明确要求后再上传GitHub。
