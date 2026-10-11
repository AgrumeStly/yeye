# Hardware preparation

## 目录范围与项目状态

本目录保存硬件采购、准备、装配、供电、接线与维护资料。用户已于2026-10-11确认硬件购买完成；下文历史采购方案中的价格、预算与待选型表述为当时记录，不代表当前采购状态。实物型号、到货、装配和测试情况以之后的验收记录为准。

项目整体计划已移至 [project_planning](../project_planning/README.md)，不再与硬件准备资料混放。比赛原文位于 [competition](../competition/比赛文档.pdf)。

- `source/`：硬件文档生成器和清单数据。
- `archive/`：已被替代的硬件文档。
- 装配图、接线图及验收资料后续可按需放入 `assembly/`。

## Personal purchase lists

The following allocation follows `hardware_purchase_list.pdf`, as requested by the team:

- `purchase_list_control.pdf`: control teammate, estimated parts CNY 207.8, one page.
- `purchase_list_vision.pdf`: vision teammate, estimated parts CNY 211.0, one page.
- `purchase_list_hardware.pdf`: hardware teammate, estimated parts CNY 207.0, two pages including the expanded wiring and fastener lists.
- `source/generate_team_purchase_lists.py`: editable generator.
- `source/team_purchase_allocation.json`: quantities and buyers mapped to the 19 original BOM items.

All original quantities are covered exactly. The two USB cables are split one each between control and vision. Parts total CNY 625.8, plus the original shared CNY 20 shipping/price allowance. Prices are carried forward from the source document and have not been re-quoted. Actual costs can be pooled and divided equally after purchase.

## Current planning document

- `hardware_modules_overview.pdf`: current module-level checklist, dated 2026-10-10. Organizes vision, control, communication, drive, mechanics, power, installation, voice functions, and preparation tools. No model, manufacturer, or price selections are made in this document.
- `source/generate_modules_overview.py`: editable generator for the module-level checklist.

Selection and budgeting will be reviewed separately, as requested by the team.

## Previous detailed proposal

- `hardware_purchase_list.pdf`: previous seven-page purchase proposal, dated 2026-10-10, retained for reference.
- `source/generate_purchase_list.py`: editable ReportLab generator.
- `source/purchase_bom.json`: quantities, fixed model/specification selections, and budget estimates.

The previous proposal uses STM32F407VET6, Lite-K230D with GC2093, two Yahboom MD310Z20_7.4V motors, classic rubber wheels, and an AT8236 Standard driver. These selections do not constrain the restarted planning process.

Parts are budgeted at CNY 625.8, plus CNY 20 for shipping/price differences. CNY 645.8 exceeds the accepted CNY 600 budget; this is disclosed in the PDF and is not an approved budget increase. Only explicitly marked official display prices were verified. Other prices are estimates. Tools and practice-track materials are excluded.

The car has not been assembled or tested. Weight, envelope, and speed are design targets. Read the detailed purchasing variants and small-parts list before ordering.

## Earlier documents

`archive/` retains previous generic N20/DRV8833 and earlier-budget documents for reference. They are superseded and should not be mixed with the current purchase list.

All new folders use English names.
