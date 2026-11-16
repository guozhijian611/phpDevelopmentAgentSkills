# 版本与来源

核对日期：2026-11-16。已核对 SaiAdmin 6.x 核心模板源码提交 `598178195a27a9a024a3cd20a0188d3117b9e09f`；独立 saithink/saicode 仓库 API 返回 404，未取得其可公开确认的最新版。不能宣称辅助 CLI 已验证所有商业/定制版本。

- [核心模板引擎与模板](https://github.com/saithink/saiadmin/tree/598178195a27a9a024a3cd20a0188d3117b9e09f/src/plugin/saiadmin/utils/code)。
- [前端生成目录与规范](https://saithink.top/documents/v6/front/develop.html)。

CLI 适配前确认 TableLogic::loadTable/preview/generateFile、Table/Column 模型、source/template/namespace/package_name/class_name/business_name/generate_path 字段、sa_system_menu.generate_id 关联，以及实际生成文件清单。不同模板路径或 API 必须按目标版本调整后再验收，不能只靠方法同名认定兼容。

本次修复的是辅助脚本的路径探测、独立帮助、错误退出、核心目录保护和生成/撤回所有权；不是替换宿主生成器。文件写入或菜单快照记录失败后应核对真实文件、数据库及 runtime 清单，不以重试掩盖半完成状态；旧文件没有清单时拒绝自动撤回。
