# AI生成skills说明

## saiadmin6-plugin

[SaiAdmin 6 插件开发 skill](saiadmin6-plugin/SKILL.md)，用于开发、打包和验收可通过 saipackage 安装的独立插件。重点覆盖发行 ZIP 与安装生命周期，配合已有的 [saiadmin](saiadmin/SKILL.md)、[saicode](saicode/SKILL.md) 等开发规范使用。

> **更新时间**：2026-11-16

### 功能与默认要求

- 安装、升级自动完成必要的宿主接入，例如语言注册与插件入口，不要求用户手工改文件或额外运行接入脚本。
- 优先使用宿主注册机制或正式生命周期钩子；必要时核实安装顺序，由 Phinx 迁移调用幂等接入服务。包含预检、备份、失败回退与已知旧接入接管。
- 卸载先检查业务数据，再清理插件拥有的资源和宿主片段，保留用户其它改动；不支持的宿主结构明确报错。
- 前端遵守宿主明暗主题、主色、组件和多语言约定；切换语言不丢失未保存业务输入，不改写用户画布配色。
- 提供可反复创建的独立 Docker 实验室，隔离源码、网络、数据库和依赖卷，支持 MySQL / PostgreSQL 测试。
- 提供 ZIP 打包校验、Phinx 首装/升级示例，以及可迁移性自检；验收涵盖首装、重复上传、升级、卸载重装和失败恢复。

自动接入仅处理必要的源码注册与安装生命周期；依赖安装和管理端构建仍沿用宿主原有流程。具体插件支持哪些宿主版本、数据库及浏览器行为，须以最终 ZIP 实测为准。

### 安装与调用

Codex 首次安装示例，将完整 skill 目录放入 skills 目录，保留其中的 `references`、`scripts` 和 `assets`：

```sh
git clone https://github.com/guozhijian611/phpDevelopmentAgentSkills.git
cd phpDevelopmentAgentSkills
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R ./saiadmin6-plugin "${CODEX_HOME:-$HOME/.codex}/skills/"
```

安装后在新会话中调用，例如：

```text
使用 $saiadmin6-plugin 开发 SaiAdmin 6 独立插件。
先检查我提供的宿主源码与安装器版本，前端遵守宿主主题和多语言约定。
安装、升级自动完成必要接入，不要要求用户手动跑接入脚本。
在独立 Docker 环境中验证最终 ZIP 的首次安装、升级、卸载清理及失败恢复。
```

使用其它支持 skills 的 Agent 时，将整个目录放入其对应的技能目录。直接运行下述辅助脚本不要求先安装 skill。

### 运行示例与自检

以下命令在本仓库根目录执行，需要 Python 3.9+；完整自检还需要 Docker Compose，但不会启动业务容器：

```sh
# 生成 1.0.0 首装包和 1.0.1 升级包，输出到仓库外
python3 saiadmin6-plugin/scripts/build_example.py --output-dir ../saiadmin6-plugin-examples

# 验证搬移后的脚本、示例 ZIP、非法包拒绝、源码排除及双库 Compose 配置
python3 saiadmin6-plugin/scripts/self_test.py

# 没有 Docker 时仅做文件级检查
python3 saiadmin6-plugin/scripts/self_test.py --skip-docker
```

示例包是安装器/Phinx 验证夹具，不是可直接用于生产的完整业务插件。运行真实安装测试时还需准备明确指定的 SaiAdmin 6 源码基线、Docker 和依赖下载网络；脚本不依赖此前会话的临时目录、账号或端口。自检通过不等于业务插件已通过双库安装和浏览器验收。

| 参考 | 内容 |
| --- | --- |
| [插件契约](saiadmin6-plugin/references/plugin-contract.md) | ZIP 允许路径、安装状态、迁移、依赖与权限 |
| [自动接入与卸载](saiadmin6-plugin/references/automatic-integration.md) | 生命周期落点、幂等、备份、升级接管、卸载和失败回退 |
| [前端集成约定](saiadmin6-plugin/references/frontend-conventions.md) | 宿主主题、多语言及运行时切换要求 |
| [Docker 实验室](saiadmin6-plugin/references/docker-lab.md) | 基线准备、独立环境、上传安装和定向清理 |
| [验收矩阵](saiadmin6-plugin/references/acceptance.md) | 首装、升级、卸载、自动接入、主题、多语言和权限 |
| [来源与验证范围](saiadmin6-plugin/references/sources-and-validation.md) | 已核对版本、历史实测及独立分发边界 |

---

## unibest

基于 unibest 官方文档生成的 uni-app 多端开发技能，包含脚手架创建、路由配置、tabbar 策略、UI 库、请求封装、App 打包和 CLI 开发规范。

> **生成时间**: 2026-05-28

### 参考资料

| 文档         | 链接                                      | 内容                                 |
| ------------ | ----------------------------------------- | ------------------------------------ |
| 官方文档     | https://unibest.tech/                     | unibest 完整开发文档                 |
| 文档源码     | https://github.com/unibest-tech/unibest-docs | VitePress 文档源码                   |
| 项目源码     | https://github.com/feige996/unibest       | unibest / create-unibest 项目源码    |
| 本地参考手册 | 参考手册/unibest-docs/docs               | 已下载的 Markdown 文档               |
| 本地模板源码 | 参考手册/unibest                         | 已浅克隆的 unibest base 模板源码     |

### 生成内容

- 项目定位与 `main` / `base` 分支说明
- `pnpm create unibest` 创建项目、追加 Feature、指定 UI / 平台
- 运行发布命令与 H5 / 小程序 / App 输出目录
- `pages.config.ts`、`manifest.config.ts`、`definePage`、layout、`App.ku.vue` 配置规则
- Tabbar 策略、状态同步和动态图标注意事项
- UI 库选型，重点覆盖 `wot-ui-v2`
- UnoCSS、iconfont、SVG 跨端限制
- 请求封装、上传、多后端地址和 OpenAPI 生成
- Pinia 持久化、登录策略、token 认证建议
- i18n、环境变量、App/HBuilderX、原生插件处理
- FAQ 排错清单、升级策略、create-unibest CLI 开发流程
- 已补充 `references/source-map.md`、`references/workflows.md`、`references/troubleshooting.md` 三份深度参考

---

## saiadmin6.0

基于 SaiAdmin 6.0 官方文档生成的开发技能，包含前后端开发规范和模板。

> **生成时间**: 2026-02-08

### 参考资料

| 文档           | 链接                                                 | 内容                                 |
| -------------- | ---------------------------------------------------- | ------------------------------------ |
| SAI 组件库文档 | https://saithink.top/documents/v6/front/sai.html     | 21个前端组件使用说明                 |
| 插件功能开发   | https://saithink.top/documents/v6/front/develop.html | 前端页面开发流程                     |
| 框架介绍       | https://saithink.top/documents/v6/back/              | 后端目录结构和命令行工具             |
| 分层架构指南   | https://saithink.top/documents/v6/back/develop.html  | Controller/Logic/Model/Validate 模板 |

### 生成内容

- 📁 前后端目录结构规范
- 🔧 后端开发模板 (Controller/Logic/Model/Validate/Route)
- 🎨 前端开发模板 (API/主页面/搜索组件/编辑弹窗)
- 🎛️ SAI 组件库详细配置 (21个组件 Props)
- 🏗️ 后端基类详解 (BaseController/LogicInterface)
- 🔓 OpenController 无需登录控制器
- 🎯 前端开发规范 (组件命名/权限控制/TypeScript)
- ⚡ 最佳实践和快速开发清单

---

## webman

基于 Webman 官方文档生成的高性能 PHP 框架开发技能，包含核心功能和常用组件使用方法。

> **生成时间**: 2026-02-08

### 参考资料

| 文档     | 链接                                  | 内容                |
| -------- | ------------------------------------- | ------------------- |
| 官方手册 | https://www.workerman.net/doc/webman/ | Webman 完整开发文档 |
| GitHub   | https://github.com/walkor/webman      | 项目源码            |

### 生成内容

- 📦 框架简介与安装运行
- 📂 目录结构规范
- 🎮 控制器 (生命周期/参数绑定)
- 🛣️ 路由 (闭包/类路由/路由参数/路由分组)
- 🔒 中间件 (身份验证/跨域处理)
- 📥 请求处理 (GET/POST/Header/Cookie/文件上传)
- 📤 响应处理 (JSON/XML/视图/重定向)
- 🗄️ 数据库 (Laravel 风格查询构建器)
- 📊 模型 (Eloquent 风格 ORM)
- 🔐 Session 管理
- 📝 日志系统
- ⚠️ 异常处理
- 🎨 视图引擎 (Twig/Blade/ThinkPHP)
- 📱 多应用支持
- ⚙️ 自定义进程 (WebSocket/定时任务)
- 📡 事件系统 (webman-event)
- ✅ 验证器 (ThinkPHP/Workerman)
- 📄 分页组件
- 🔑 权限控制 (Casbin)
- 🚀 部署建议 (Nginx/Supervisor)

---

## thinkorm

基于 ThinkORM 3.0 官方文档生成的 PHP ORM 开发技能，包含数据库操作、模型定义、关联查询等核心功能。

> **生成时间**: 2026-02-08

### 参考资料

| 文档     | 链接                                   | 内容                  |
| -------- | -------------------------------------- | --------------------- |
| 官方手册 | https://doc.thinkphp.cn/@think-orm     | ThinkORM 完整开发文档 |
| GitHub   | https://github.com/top-think/think-orm | 项目源码              |

### 生成内容

- 📦 框架简介与安装配置
- ⚙️ 数据库连接配置 (单机/分布式/读写分离)
- 🔍 查询数据 (单条/多条/字段值/分批处理/游标查询)
- ➕ 新增数据 (单条/批量/获取自增ID)
- ✏️ 更新数据 (save/update/自增自减/SQL函数)
- ❌ 删除数据 (硬删除/软删除)
- 🔗 链式操作 (where/field/order/limit/join 等)
- 📊 聚合查询 (count/max/min/avg/sum)
- 💰 事务处理 (自动事务/手动事务)
- 📋 模型定义 (表名/主键/时间戳)
- 🔄 获取器/修改器 (自动字段处理)
- 🔧 类型转换 (integer/array/json/enum 等)
- 🔎 搜索器 (封装查询条件)
- 📏 查询范围 (预定义查询条件)
- 🗑️ 软删除 (delete_time 标记)
- 🔒 只读字段
- 📝 JSON 字段操作
- 📡 模型事件 (增删改查回调)
- 🔗 模型关联 (一对一/一对多/多对多/远程/多态)
- 📥 预载入查询 (解决 N+1 问题)
- 📊 关联统计 (withCount/withSum 等)
- 💾 查询缓存/字段缓存
- 🎯 最佳实践和代码片段

---

## artdesignpro

基于 Art Design Pro 官方文档生成的 Vue 3 企业级中后台开发技能，包含现代化 UI 设计和高效开发工具。

> **生成时间**: 2026-02-08

### 参考资料

| 文档     | 链接                                         | 内容                    |
| -------- | -------------------------------------------- | ----------------------- |
| 官方文档 | https://www.artd.pro/                        | Art Design Pro 完整文档 |
| GitHub   | https://github.com/Daymychen/art-design-pro  | 项目源码                |
| Gitee    | https://gitee.com/lingchen163/art-design-pro | 国内镜像                |

### 生成内容

- 📦 技术栈说明 (Vue 3/TypeScript/Vite/Element Plus/Tailwind CSS)
- 📂 项目结构规范
- 🛣️ 路由和菜单配置 (静态路由/动态路由/权限控制)
- 📊 useTable 组合式函数 (智能缓存/分页/刷新策略)
- 🔍 ArtSearchBar 搜索栏组件 (20+种表单控件)
- 🔐 权限控制 (hasAuth/v-auth/v-roles)
- 🎨 主题配置 (CSS 变量/Tailwind 工具类/主题切换)
- 🎯 图标使用 (Iconify/Remix Icon)
- 📡 API 接口规范
- ⚙️ 环境变量配置
- 📝 Git 提交规范 (Commitizen)

---

## elementplus

基于 Element Plus 官方文档生成的 Vue 3 UI 组件库速查手册，涵盖中后台开发常用组件 API。

> **生成时间**: 2026-02-08

### 参考资料

| 文档     | 链接                                         | 内容                  |
| -------- | -------------------------------------------- | --------------------- |
| 官方文档 | https://element-plus.org/                    | Element Plus 完整文档 |
| GitHub   | https://github.com/element-plus/element-plus | 项目源码              |

### 生成内容

- 📊 Table 表格 (属性/列配置/事件/方法)
- 📝 Form 表单 (验证规则/方法调用/自定义校验)
- 💬 Dialog 对话框 (属性/插槽/事件)
- 🔽 Select 选择器 (单选/多选/远程搜索/分组)
- ⌨️ Input 输入框 (类型/插槽/事件)
- 📄 Pagination 分页 (布局/事件)
- ⚠️ MessageBox 弹框 (alert/confirm/prompt)
- 📤 Upload 上传 (钩子函数/照片墙/拖拽)
- 🌲 TreeSelect 树选择器 (懒加载/多选)
- 📅 DatePicker 日期选择器 (类型/快捷选项)
- 🔗 Cascader 级联选择器 (懒加载/可选任意级)
- 🌳 Tree 树形控件 (筛选/拖拽/自定义节点)
- 🔧 工具函数 (ElMessage/ElNotification/ElLoading)
