# 首次入口检查失败（仅电脑）

2026-11-11：`isolated_all_other_R5_code_preserved`断言失败。未连接板卡或运行相机。
原因：检查器反向还原配置时全局替换ALLOW_DRIVE=True，也误改了R5原注释中同样的文字；候选生成本身未放宽门槛。修复检查器只匹配独立配置行，后续结果另存visual_link_checks_02，不覆盖本次失败。
