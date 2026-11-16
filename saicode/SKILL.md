---
name: saicode
description: 使用 SaiAdmin 6 的 SaiCode 装载表、配置字段关联、预览和生成 CRUD，或通过可搬移 CLI 执行带文件所有权保护的生成与撤回。
---

# SaiCode 生成与安全撤回

先核对宿主 TableLogic、模型字段、模板和版本，以及数据库、前端目录和所属菜单。生成器可能来自商业/定制包，不能假设与文档相同；[来源与适用范围](references/versions.md)。

## 开发流程

先查询菜单和已有配置，确认目标 namespace/包/表；禁止生成到 saiadmin、saicode、saipackage。装载与配置后先 preview，不猜菜单 ID、不覆盖现有业务文件。CLI 的 load 当前只支持 MySQL，其它数据库用宿主已验证的装载接口。

生成后核对文件 diff、菜单按钮、权限、API、关联和校验。前端复用宿主主题 token 与 i18n，表头/规则响应式更新，语言切换不丢输入；修改目标模板或生成结果，不保留硬编码文案作为最终实现。发行插件时首装/升级自动接入，卸载保护数据，不要求用户额外跑接入脚本。

生成结果默认接入系统账号/角色及菜单、按钮/API 权限点，前后端编码一致；权限记录安装幂等、升级保留授权、卸载仅清自身资源。逐实体确认记录归属，适用 DataScope 时检查真实 ORM/BaseLogic、角色 data_scope/部门关系和可信 created_by，并在 Logic 显式启用，重新生成后仍保留；缺少能力须声明依赖或实现受测适配，不默认跳过。共享表说明替代策略，不强加创建者隔离。

不能仅加 scope 属性：新增归属来自服务端，普通更新不可更换所有者；自定义查询、导出/统计、联表、批量、子资源也要受限，并叠加租户/业务归属。用普通账号覆盖五种适用范围、越权 ID、伪造归属、空角色/部门、多角色和缓存失效，不能把生成成功或菜单显示当作权限验收。

## 可搬移 CLI

脚本以自身位置找资源，不依赖旧 .agent/skills 布局。从任意目录调用，路径替换为实际安装位置：

```sh
php /path/to/saicode/scripts/saicode_generate.php --help
php /path/to/saicode/scripts/saicode_generate.php menus --server-dir /path/to/server
php /path/to/saicode/scripts/saicode_generate.php preview --id 1 --server-dir /path/to/server
php /path/to/saicode/scripts/saicode_generate.php generate --id 1 --dry-run --server-dir /path/to/server
```

--server-dir 优先，其次 SERVER_DIR，最后探测当前目录或其 server 子目录。宿主需有 vendor、bootstrap、plugin/saicode；--help 不加载宿主/数据库。支持 --key=value 与 --key value。完整字段与关联命令见 [API 参考](references/api-guide.md)。

## 生成和撤回保护

预检拒绝路径穿越、符号链接、核心插件和无记录的已有文件。成功生成后在宿主 runtime/saicode-skill 保存目标、文件哈希与菜单快照；再次生成只覆盖本工具记录且未被修改的文件。需核对宿主实际输出路径；不宣称文件、菜单和 DDL 有全局事务。

rollback --id 1 默认只读预览；已核对后用 --apply 执行，--clean 同时清理生成配置。先检查全部文件与菜单；任何改动均拒绝。文件先移到备份，数据库清理失败则恢复本次移动的文件，成功后备份保留。不递归删除插件目录，不猜测接管无清单的历史文件。权限缓存与服务重载按宿主方式处理。

无需真实宿主的回归：python3 /path/to/saicode/tests/test_cli.py。测试使用一次性文件与宿主夹具，不代替真实生成器、数据库和浏览器验收。
