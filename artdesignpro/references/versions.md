# 版本与来源

核对日期：2026-11-16。开源源码提交 `f3aaf58eec1a0e988f162352c33862327a484f95`；package.json 的 version 为 0.0.0，不能拿它当正式发行号。该快照要求 Node >=20.19、pnpm >=8.8，依赖 Vue ^3.5.21、Element Plus ^2.11.2、vue-i18n ^9.14；具体解析结果仍以目标锁文件为准。

- [核对的源码](https://github.com/Daymychen/art-design-pro/tree/f3aaf58eec1a0e988f162352c33862327a484f95)。
- [实际 useTable](https://github.com/Daymychen/art-design-pro/blob/f3aaf58eec1a0e988f162352c33862327a484f95/src/hooks/core/useTable.ts)。
- [官方 useTable 文档](https://www.artd.pro/docs/zh/guide/hooks/use-table.html)。
- [官方国际化](https://www.artd.pro/docs/zh/guide/in-depth/locale.html)。

官方 useTable 文档仍有 @/composables/useTable，但此快照在 @/hooks/core/useTable；本 skill 已修正参考示例。实际函数的泛型从 apiFn 推导，不把旧文档里的 useTable<Row> 当作所有版本通用签名。locale 文档也混有 language/locales/JSON 与 src/locales/TS 两种描述，以目标源码为准。生成页面保留宿主已有 i18n，不复制官网示例重新初始化全局 locale/fallback。
