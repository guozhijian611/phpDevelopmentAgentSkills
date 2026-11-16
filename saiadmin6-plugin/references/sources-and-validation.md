# 来源与验证范围

核对日期：基础实验室为 2026-11-15；自动接入规则补充于 2026-11-16。以下记录是验证证据，不保证其他版本行为相同。

## 官方资料

- [6.x 安装](https://saithink.top/documents/v6/install.html)
- [6.x 内置命令](https://saithink.top/documents/v6/console.html)
- [插件规范](https://saithink.top/plugin/intro.html)：旧5.x文档，路径以6.x源码为准。
- [6.x基线仓库](https://github.com/saithink/saiadmin6.x)，提交 b697986e7838dab87463c7597b2787cb3c0d1a7d。
- [saipackage6.1.0源码](https://github.com/saithink/saipackage/tree/a8cb24f76b29b1bc7b1b94c426c7471168e5bfa2)。
- SaiAdmin6.1.5源码提交598178195a27a9a024a3cd20a0188d3117b9e09f。

## 已完成验证

- PHP8.4，MySQL8.4、PostgreSQL17，两套隔离源码、网络与数据库。PostgreSQL镜像为amd64模拟运行，不能据此评价ARM原生性能。
- 核心初始化通过；SQL型插件与Phinx型插件的首装、升级、卸载重装、数据隔离。
- Phinx插件经真实HTTP上传和安装；升级保留数据且不重复灌种子，卸载删除业务表、插件迁移记录表和菜单。拒绝旧式SQL包在PG安装；拒绝错误命名空间后可清理暂存并重装正确包。
- Node22 / pnpm10.11.0前端依赖安装、vue-tsc及Vite生产构建通过，存在上游构建警告。
- MySQL浏览器：正常验证码登录，上传ZIP、安装、菜单更新、业务页面显示种子数据、卸载重装、升级至1.0.1并保留数据。PG使用HTTP验证，没有另行做完整浏览器登录。
- 修正示例遗漏的support=6.x，并在打包器中强制检查；后端直装成功不能证明UI兼容检查通过。
- 原安装器立即重载可导致HTTP连接关闭；临时副本应用延迟重载补丁后HTTP生命周期通过。补丁只针对明确匹配的源码，不是通用生产修复。

## 可重复运行

所有可执行脚本通过自身位置寻找assets，不读取以上测试曾用的目录、账号、镜像或端口。
`python3 scripts/self_test.py` 会在新目录复制整个Skill并验证示例ZIP、打包拒绝行为、两种数据库Compose配置、复制排除规则、补丁可重复执行。需要Python3.9+和Docker Compose；可用--skip-docker仅运行文件级检查。
`python3 scripts/build_example.py --output-dir OUTPUT` 生成1.0.0与1.0.1包；示例发行文件都在assets/phinx-fixture内。

运行依赖仍需用户准备Docker、网络和明确指定的SaiAdmin6基线。第三方依赖不随Skill打包。示例不是完整业务权限测试，任意插件需按验收矩阵另行验证。

## 自动接入的补充依据（2026-11-16）

依据已发行 Board Studio 2.1.1 的源码与双库验收记录，新增 [自动接入与卸载](automatic-integration.md)，并将其设为默认交付要求，替换旧的必要时提供手动接入步骤。可运行的现有 Phinx 示例只演示表/菜单迁移，不需要额外宿主接入；不将它误称为自动接入故障测试。

Board Studio 在 SaiAdmin 6.1.5 / saipackage 6.1.0 的已验证 Phinx 安装分支通过 PHP 迁移调用幂等服务，完成真实 ZIP 首装、升级、备份、保护卸载、空库清理与失败恢复；旧版已接入和未接入均覆盖。两套实际安装的宿主管理端构建及类型检查通过，MySQL 空库卸载后完整构建通过。完整证据及锁定提交链接见上述参考；这些是该插件的历史实测，不代表 skill 自检会重新运行双库或浏览器测试，也不把此安装分支推广为所有 6.x 核心的能力。

## 独立分发检查

Skill已迁移到新目录执行self_test.py，通过两版示例ZIP生成、兼容字段校验、敏感文件/符号链接拒绝、MySQL及PostgreSQL Compose配置、源码排除规则和重载补丁幂等检查。没有使用旧测试目录的文件。附带脚本只依赖Python标准库；Docker Compose是环境验证所需外部命令。新建实验室需要明确的--source输入，示例打包不需要SaiAdmin源码。

附带Dockerfile已直接从官方php:8.4-cli-bookworm和composer:2构建成功；容器内验证pdo_mysql、pdo_pgsql、pcntl、posix、zip、intl、mbstring、gd、curl、DOM/XML和redis扩展加载，Composer命令可用。镜像本身不打入Skill压缩包，首次使用需联网构建。
