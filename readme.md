# AI生成skills说明

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
