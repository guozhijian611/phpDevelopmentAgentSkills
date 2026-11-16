---
name: artdesignpro
description: 开发维护 Art Design Pro Vue 3 后台的 useTable、路由、菜单、权限、主题和多语言；按源码版本核对官方示例与宿主差异。
---

# Art Design Pro 开发

先读 package.json、锁文件、实际 hooks/router/locales 与相邻页面。官方文档可能混用版本，以目标源码为准；[版本与来源](references/versions.md)。

## 实现约束

- 复用 ArtTable、ArtSearchBar、弹窗、页面容器和类型/请求适配。当前核对的开源 useTable 位于 src/hooks/core/useTable.ts，导入 @/hooks/core/useTable；部分官方示例仍写 @/composables/useTable，不能直接照搬。
- 核对 apiFn 参数/结果和分页映射，优先实际函数推导泛型。列定义随语言更新；分页/筛选请求处理过期响应，避免旧结果覆盖新查询。
- 路由、菜单、权限指令按目标封装；前端显示权限不代替后端鉴权。不能把独立演示路由解析套入 SaiAdmin。
- 后台沿用语义 token、主题状态、vue-i18n 与组件库 locale，不固定白底/深色或覆盖全局主题。用户业务画布配色独立保留。
- 新 UI 文案完整本地化，表头/选项/规则使用 computed 或展示时翻译；保留宿主默认语言与 fallback，切换不重建丢失未保存表单。插件注册随安装/升级自动完成，不能只改开发机 locales。

## 参考与验证

[框架 API](references/api-guide.md)按需查 useTable、路由、主题与请求；通用 Element Plus 表不再重复维护。验证类型/构建、搜索分页、错误恢复、明暗主题、主色和运行时语言。依赖脚本按项目约定执行，不默认用 --ignore-scripts 绕过缺失生成物。
