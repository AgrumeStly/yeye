# 智能小车项目

按“比赛要求 → 项目安排 → 分模块开发 → 整车测试 → 报告答辩”组织资料。所有文件夹使用英文名称，说明使用中文。

## 代码同步与协作

项目远端：[AgrumeStly/yeye](https://github.com/AgrumeStly/yeye)。访问范围以仓库当前设置为准；提交成员须具有相应写入权限。

在主控笔记本、视觉电脑或硬件电脑首次下载：

```bash
git clone https://github.com/AgrumeStly/yeye.git
```

每次开始开发前核对工作区与分支，处理已有修改后同步所需代码；任务在单独分支完成，分享后通过合并请求交给主控集成。`main` 用于保存团队的集成版本。Codex默认只保存、验证本地成果，主控明确要求上传当前改动后再推送。需要换电脑接续时，由主控安排上传，并记录分支和提交号；另一台电脑拉取相同分支后核对版本。

仓库保存代码、工程配置、项目文档和典型样本。`tmp/`、本机工具配置、编译缓存及原始录像已排除；原始录像通过共享存储传递，并在测试记录中注明位置。各电脑的IDE、编译器、芯片支持包和下载器驱动须另行安装。

## 从这里开始

- 看对话如何分工、各类信息以哪个文件为准：[对话分工与标准文档](project_planning/collaboration_standard.md)
- 看当前进展、阻塞与下一步：[当前状态与任务](project_planning/project_status.md)
- 学三人协作：[GitHub零基础操作手册](project_planning/github_collaboration_guide.pdf)（21页，第20页为日常速查）

- 看比赛要求：[比赛原文](competition/比赛文档.pdf)
- 看任务与截止日期：[项目规划书](project_planning/project_plan.pdf) / [可编辑文字版](project_planning/project_plan.md)
- 看三人职责：[分工大纲](project_planning/team_work_outline.pdf)

## 主目录分类

| 文件夹 | 用途 | 典型内容 |
| --- | --- | --- |
| `competition/` | 主办方资料与报名信息 | 比赛原文、补充通知、报名凭据、正式赛程 |
| `project_planning/` | 团队安排与项目管理 | 项目规划、分工、进度、会议决定、问题跟踪 |
| `hardware_preparation/` | 硬件采购、装配与维护资料 | 采购清单、实物验收、接线图、结构图、供电记录、装配照片 |
| `control/` | 主控与运动控制开发 | MCU工程、电机/编码器驱动、控制算法、通信与动作状态机 |
| `vision/` | 视觉与语音开发 | 采图、识别、路径输出、语音脚本、算法参考和样本 |
| `testing/` | 整车联调与测试证据 | 试跑日志、圈速、故障复现、测试录像、验收记录 |
| `report/` | 对外提交与答辩材料 | 报告、流程图、答辩演示、最终提交包 |
| `tmp/` | 可重新生成的中间文件 | PDF预览图、排版检查图、转换缓存 |

## 当前结构与后续约定

```text
yeye/
├── README.md
├── AGENTS.md
├── skills-lock.json
├── .agents/                     工具配置，保持原位
├── competition/
│   └── 比赛文档.pdf
├── project_planning/
│   ├── project_plan.pdf
│   ├── project_plan.md
│   ├── team_work_outline.pdf
│   └── source/                  规划文档的生成脚本
├── hardware_preparation/
│   ├── *.pdf                    硬件清单与准备资料
│   ├── source/                  硬件文档生成脚本与清单数据
│   └── archive/                 已被替代的硬件文档
├── control/
├── vision/
│   ├── PORTING_REVIEW.md        移植审查说明
│   ├── reference_code/          尚未完成移植的C示例
│   ├── references/              图像处理参考文档
│   └── data/                    图像样本与示例数据
├── testing/
├── report/
└── tmp/
    └── pdfs/                    现有预览图与制作用参考素材
```

目录按需要增加子目录，不预建大量空文件夹。主控工程已位于 `control/firmware/`；新增视觉/语音程序分别放 `vision/src/`、`vision/audio/`，这两个目录当前尚未创建。当前实现与验证状态见项目状态表。

## 文件放置规则

1. 根目录只保留导航、工作区规则和工具配置，不再散放业务文档。
2. 官方要求放 `competition/`；团队的计划与决定放 `project_planning/`。
3. 硬件资料继续遵守 `AGENTS.md`：文档放 `hardware_preparation/`，生成器放其 `source/`，被替代版本放其 `archive/`。
4. `source/` 在文档目录内专指文档生成器；软件工程使用 `firmware/` 或 `src/`，参考代码使用 `reference_code/`。
5. 模块原始样本留在模块目录；整车跨模块的测试结果统一放 `testing/`。例如一次试跑可用 `testing/2026-11-01_run01/`，集中保存日志、参数和录像。
6. 对外报告放 `report/`，正式提交包按版本放其 `release/` 下；开发源代码仍保留在所属模块目录。
7. 文件过时后放所属类别的 `archive/`，不要与当前版本混放。原始比赛资料保留原文件名；新增测试记录建议带日期。
8. `tmp/` 只应新增可重建文件。现有 `tmp/pdfs/references/` 含历史制作用参考图片，暂予保留；清理前先确认是否有其他来源，不可直接视为全部可删除。

导航和目录快照用于查找文件；当前状态统一维护在项目状态表，详细依据见对话与文档标准。
