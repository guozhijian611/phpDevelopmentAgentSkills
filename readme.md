# PHP 与前端开发 Agent Skills

面向 PHP / Webman / SaiAdmin、Vue 后台和 uni-app 的开发 skills，以及直接同步的宝塔官方 skill。安装所需的完整目录，Agent 按目标项目源码、锁文件和约定工作；不会因为更新本仓库就自动升级你的业务项目。

## 技能目录

| Skill | 用途 | 本次更新（2026-11-16） |
| --- | --- | --- |
| [saiadmin](saiadmin/SKILL.md) | SaiAdmin 6 业务分层、权限与页面开发 | 主题、多语言、迁移及插件发行分工 |
| [saiadmin6-plugin](saiadmin6-plugin/SKILL.md) | 可安装 ZIP、自动接入与生命周期 | 保留自动接入、备份、升级/卸载保护和独立 Docker 验证 |
| [saicode](saicode/SKILL.md) | 表装载、字段/关联、CRUD 生成与撤回 | 可搬移 CLI、独立帮助、预检、生成所有权与撤回保护 |
| [webman](webman/SKILL.md) | Webman 服务、路由、进程与数据库 | 2.1 协程/连接池、事务与请求隔离，2.2 路由边界 |
| [thinkorm](thinkorm/SKILL.md) | ThinkORM 查询、模型、关联和事务 | 区分 3.x/4.x、Entity 分层与宿主适配 |
| [artdesignpro](artdesignpro/SKILL.md) | Vue 后台、useTable、主题和国际化 | 修正实际 hook 路径，核对泛型与宿主差异 |
| [elementplus](elementplus/SKILL.md) | Element Plus 组件与交互 | 版本门槛、弃用 API、主题/locale 和无障碍 |
| [unibest](unibest/SKILL.md) | uni-app 多端项目与 CLI | 核对 base/main 快照，独立源码获取及历史排错边界 |
| [btpanel](btpanel/SKILL.md) | 宝塔面板与 MCP 接入、运维和部署 | 直接同步 aaPanel 官方新版，保持上游内容不变 |

自维护 skills 的入口保留决策和约束，长 API/模板表移到各自 `references` 按需读取。具体版本、官方链接和核对边界见各目录的 `references/versions.md`；`upstream-lock.json` 记录本次核对的源码提交。

## 安装与使用

以 Codex 用户级目录为例，首次安装某个 skill（保留其 scripts、references、assets 和 agents）：

```sh
git clone https://github.com/guozhijian611/phpDevelopmentAgentSkills.git
cd phpDevelopmentAgentSkills
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R ./saiadmin6-plugin "${CODEX_HOME:-$HOME/.codex}/skills/"
# 其它自维护 skill 可按需将目录名替换为 saiadmin、saicode 等
```

其它 Agent 使用其对应的技能目录。已有同名自定义版本先核对差异再更新；不要整仓覆盖技能目录。新会话中显式调用，例如：

```text
使用 $saiadmin 和 $saicode 开发当前 SaiAdmin 6 业务模块。
先检查实际表结构、菜单、权限、生成器版本与目标目录，再预览和生成。
前端遵守宿主主题及多语言约定，切换语言不能丢失表单输入。
```

发行独立插件时：

```text
使用 $saiadmin6-plugin 开发可独立安装的插件。
安装和升级自动完成必要接入，不要求用户额外跑接入脚本。
在独立 Docker 环境验证最终 ZIP 的首次安装、升级、卸载保护与失败恢复。
```

### 宝塔官方同步方式

[官方仓库 aaPanel/btpanel-skills](https://github.com/aaPanel/btpanel-skills) 当前已改为 **btpanel 主 skill + 内置配套 skills**，通过 MCP 管理网站、文件、数据库、Docker 等。旧 `btpanel_files` / `btpanel_phpsite` 目录已移除，不再维护旧 Python API 客户端；已有安装需按新版官方说明切换入口，旧 token/YAML 不会被本仓库自动迁移或启用。

本次同步提交为 `4e069027109537f8b704ec2d3b1b1ce60be5c1e5`，`btpanel/` 内完整保留上游 SKILL、README、LICENSE、helper、来源记录和配套 skills，未修改内容。逐文件 SHA256 记在 [upstream-lock.json](upstream-lock.json)，校验会检测缺失、额外文件和内容漂移。官方说明主维护站已迁移 CNB，GitHub 用于同步和发行；参见 [官方 README](btpanel/README.md)。

安装新版主 skill 可使用官方命令：

```sh
npx skills add aaPanel/btpanel-skills
```

配套 skills 在 `btpanel/assets/bt-skills/`，按官方说明选择所需项目部署或排障技能。仓库自检仅验证完整性、语法和帮助入口，不执行宝塔安装器、不连接服务器、不写入 Agent 的 MCP 凭据配置。

## SaiCode 辅助 CLI

帮助可在任意目录执行，不要求宿主或数据库：

```sh
php saicode/scripts/saicode_generate.php --help
```

其它命令需要已准备的宿主；显式目录优先于 `SERVER_DIR` 和当前目录探测：

```sh
php saicode/scripts/saicode_generate.php menus --server-dir /path/to/server
php saicode/scripts/saicode_generate.php preview --id 1 --server-dir /path/to/server
php saicode/scripts/saicode_generate.php generate --id 1 --dry-run --server-dir /path/to/server
php saicode/scripts/saicode_generate.php generate --id 1 --server-dir /path/to/server
php saicode/scripts/saicode_generate.php rollback --id 1 --server-dir /path/to/server
# 只有核对预览后才执行撤回；同时清理生成配置可另加 --clean
php saicode/scripts/saicode_generate.php rollback --id 1 --apply --server-dir /path/to/server
```

生成前拒绝覆盖无清单的已有文件；成功后保存目标文件哈希和菜单快照。撤回默认只读，执行时拒绝用户已修改的文件/菜单；数据库清理失败会恢复本次移动的文件，备份保留。不能自动接管旧生成文件，不能将文件/DDL/菜单视为全局事务。CLI 的 `load` 当前限定 MySQL；商业/定制生成器的 API 和实际输出路径须在目标宿主另行验证。

## 插件示例与 Docker 实验室

以下从仓库根执行，需要 Python 3.9+，不依赖历史临时目录：

```sh
python3 saiadmin6-plugin/scripts/build_example.py --output-dir ../saiadmin6-plugin-examples
python3 saiadmin6-plugin/scripts/self_test.py
# 无 Docker 时只运行文件级检查
python3 saiadmin6-plugin/scripts/self_test.py --skip-docker
```

两版 Phinx 示例包用于首装、升级测试，不是生产业务插件。真实测试还需用户明确指定的 SaiAdmin 基线、Docker、Composer/前端依赖和网络。环境每轮独立创建，只清理对应 Compose 项目，不运行全局 prune。

详细说明：[安装器契约](saiadmin6-plugin/references/plugin-contract.md)、[自动接入与卸载](saiadmin6-plugin/references/automatic-integration.md)、[前端约定](saiadmin6-plugin/references/frontend-conventions.md)、[Docker 实验室](saiadmin6-plugin/references/docker-lab.md)、[验收矩阵](saiadmin6-plugin/references/acceptance.md)。源码接入自动化不等于自动完成宿主依赖安装、生产构建或部署。

## 仓库验证

依赖 Python 3.9+、PyYAML、PHP CLI；完整配置自检需 Docker Compose。可通过 uv 临时提供 YAML 依赖，或在自己的 Python 环境安装 PyYAML：

```sh
uv run --with PyYAML python tools/verify.py
# 没有 Docker 时跳过 Compose 配置校验
uv run --with PyYAML python tools/verify.py --skip-docker
```

验证包括 skill 元数据/本地引用、宝塔上游文件完整性、Python/PHP 语法、独立 CLI 帮助、SaiCode 临时宿主回归、插件脚本迁移与示例 ZIP。GitHub Actions 执行同一检查。测试不代表每个框架 API 或业务插件均已通过真实数据库、浏览器或生产验收；历史实测与本轮文件/夹具检查分开记录。

仓库根 `参考手册/` 保留历史离线资料，不作为当前上游版本保证，也不是单独安装 skill 的必需依赖。需要源码时按各 skill 的版本记录使用用户项目或官方锁定链接。宝塔遵循其目录内 MIT LICENSE；其它材料保留原有来源，第三方文档/代码的权利以其上游许可为准。
