# SaiAdmin 6 插件包与安装器契约

## 资料优先级

目标运行中的 `server/plugin/saipackage` → 对应锁定版本源码 → 同版本文档。`https://saithink.top/plugin/` 标明 5.x；不能把其 `saiadmin-vue/src/views/<app>` 路径照搬到 6.x。6.x 参考项目是 `https://github.com/saithink/saiadmin6.x`，后端 `server`、前端 `saiadmin-artd`。文档建议 Node22/pnpm，PHP 最低版本须同时满足依赖锁；附带 Dockerfile 使用 PHP8.4，不代表所有历史版本强制要求8.4。

核对文件：
- `composer.lock` 中 saithink/saiadmin 和 saithink/saipackage。
- `plugin/saipackage/app/logic/InstallLogic.php`（路径、状态、版本、SQL/迁移分支）。
- `plugin/saipackage/app/logic/PluginMigrator.php`（若存在）。
- `vendor/saithink/saipackage/src/service/{Server,Depends,Terminal}.php`。
- `plugin/saipackage/app/controller/InstallController.php` 与前端插件管理 API。
- 前端 `src/utils`、菜单组件路径解析、后端认证/权限中间件。

## 标准载荷

```text
stage/
  info.ini
  config.json
  plugin/example/
    app/{admin,api,model}/...
    config/...
    db/migrations/20261115000000_create_example_items.php
    db/seeds/ExampleSeeder.php  # 可选
  saiadmin-artd/src/views/plugin/example/...
  install.sql                  # 老式 MySQL 包按需
  uninstall.sql
  update.sql
```

ZIP 内第一层就是上述内容。app 应字母开头，只含字母数字下划线；PHP 命名空间与 `plugin/example` 一致，建议统一小写 app。版本使用三段数字，递增补丁号即可；不要通过修改暂存 info.ini 假装新版本。

```ini
app = example
title = Example
about = Example plugin
author = Example author
website = https://example.com
version = 1.0.0
support = 6.x
```

6.1.0 安装器自行设置 state，发行包无需声明已安装状态。config.json 无额外依赖时使用 `{}`；有依赖时声明 `require`、`require-dev`、`dependencies`、`devDependencies` 对象。`composerConfig` 如有使用需审查其对宿主配置的影响。依赖冲突不能通过无条件覆盖来解决；检查宿主声明与锁文件，按当前安装器完成依赖安装与完成标记。

## 6.1.0 已核对的行为，其他版本重新核对

- 前端目标由 `FRONTEND_DIR` 控制，默认 `saiadmin-artd`；仅复制后端 `plugin/<app>` 与前端 `<FRONTEND_DIR>/src/views/plugin/<app>`。
- 包被解压到 `runtime/saipackage/<app>`；此处 info.ini 是安装记录，不能当作可随意删除的缓存。只删除数据库卷无法得到干净首装。
- 状态为 0未安装、1已安装、2待安装、3冲突待处理、4依赖待安装、5目录占用。上传≠安装完成。依赖待装时须安装依赖并通过对应完成接口更新，不手动改 state。
- 同版本上传会被拒绝；递增版本上传进入升级路径。升级会替换插件目录，必须测试旧文件删除和业务数据保留。
- 有 `db/migrations/*.php` 则走 PluginMigrator；否则 MySQL 使用 SQL 包，PostgreSQL 拒绝旧式 SQL 包。不能仅凭 6.x 版本号宣称支持 PostgreSQL。
- 迁移类命名空间 `plugin\<app>\db\migrations`，种子 `plugin\<app>\db\seeds`；按 Phinx 时间戳文件名与类名映射。独立记录表 `phinxlog_<app>`。不要复制全局 SaiSchema trait，按核心实现 require_once。
- 首装迁移后执行种子；升级通常不重跑种子。变更默认菜单/字典应由版本迁移负责，勿依赖重跑全部种子。种子重试也应避免重复数据。
- 卸载先回滚迁移/执行 uninstall.sql，再删除文件与暂存。只清理自身表、菜单和权限。声明卸载数据策略，开发测试可清理，客户数据处理按实际授权。
- 非已安装状态的“卸载”可能只清理暂存，并不会撤销部分安装造成的数据库/文件变化；失败恢复不要假定它能事务回滚。
- SQL 分支升级可能先执行 install.sql 再 update.sql（看 `WAIT_INSTALL` 分支）。MySQL DDL 不保证事务回滚，install.sql 须适配目标行为，测试防重复，优先迁移包。
- SQL 导入是简单逐行累积、遇行尾分号执行；避免依赖 DELIMITER、复杂过程及 mysql CLI 指令。SQL 文件缺失可能被视为无操作成功，验收必须检查真实表/菜单。
- 升级/卸载文件备份不等于数据库备份。不要将文件 ZIP 宣称为完整恢复点。

## 自动接入的生命周期落点

已验证的 Phinx 安装分支先复制插件文件，再执行迁移，之后处理依赖/安装状态；升级同样执行未应用的迁移。卸载先按逆序回滚迁移，再删除插件文件。目标版本必须重新核对这些顺序和路径解析 API，不能假定所有 6.x 安装器都有同一个通用安装回调。

需要宿主接入时，按 [自动接入与卸载](automatic-integration.md) 选择现有注册机制、正式钩子或迁移调用服务；安装/升级自动完成，正常流程不转交手动脚本。迁移回滚前的数据检查必须覆盖其后可能发生的清理，不能等宿主片段已删除后才拒绝有数据的卸载。

## 后端、前端、权限

`php webman sai:plugin example` 创建框架骨架后检查生成物。业务管理接口沿用核心授权和校验规则，公开 API 明确其访问策略。菜单 component 字段按当前前端解析器填写，按钮权限编码与后端检查一致。测试管理员和受限角色，确认隐藏按钮以外接口也拒绝越权。

新增 Composer 插件后检查 install 脚本生成文件；禁止为开发业务直接覆盖整个 saiadmin。生产项目有 `--no-scripts` 等规则时遵循项目要求，显式装载所需插件副本。在一次性官方干净基线中正常执行 Composer 插件脚本是初始化的一部分。

管理端额外要求 `info.ini` 中 `support = 6.x`（多主版本可用 `5.x|6.x`）。缺少该字段时后端上传/安装可能成功，UI却显示 undefined 并拒绝安装；打包器必须前置检查，不能只测HTTP。
