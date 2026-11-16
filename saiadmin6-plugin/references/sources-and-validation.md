# 来源与验证范围

核对日期：基础实验室为 2026-11-15；自动接入、权限与 PostgreSQL 回归补充于 2026-11-16。以下记录是验证证据，不保证其他版本行为相同。

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
`python3 scripts/self_test.py` 在新目录复制整个 skill，验证四个示例 ZIP、离线权限登记/协议状态、打包拒绝、双库 Compose、复制排除和补丁幂等。需要 Python 3.9+、PHP 8.4/PDO SQLite 与 Docker Compose；--skip-docker 跳过 Compose 解析，不跳过 PHP 测试。
`python3 scripts/build_example.py --output-dir OUTPUT` 生成1.0.0与1.0.1包；示例发行文件都在assets/phinx-fixture内。

运行依赖仍需用户准备Docker、网络和明确指定的SaiAdmin6基线。第三方依赖不随Skill打包。示例不是完整业务权限测试，任意插件需按验收矩阵另行验证。

## 自动接入的补充依据（2026-11-16）

依据已发行 Board Studio 2.1.1 的源码与双库验收记录，新增 [自动接入与卸载](automatic-integration.md)，并将其设为默认交付要求，替换旧的必要时提供手动接入步骤。可运行的现有 Phinx 示例只演示表/菜单迁移，不需要额外宿主接入；不将它误称为自动接入故障测试。

Board Studio 在 SaiAdmin 6.1.5 / saipackage 6.1.0 的已验证 Phinx 安装分支通过 PHP 迁移调用幂等服务，完成真实 ZIP 首装、升级、备份、保护卸载、空库清理与失败恢复；旧版已接入和未接入均覆盖。两套实际安装的宿主管理端构建及类型检查通过，MySQL 空库卸载后完整构建通过。完整证据及锁定提交链接见上述参考；这些是该插件的历史实测，不代表 skill 自检会重新运行双库或浏览器测试，也不把此安装分支推广为所有 6.x 核心的能力。

## 独立分发检查

Skill 已迁移到新目录执行 self_test.py；示例生成、兼容字段、敏感文件/符号链接拒绝、双库配置、复制排除与重载补丁检查不读取历史会话文件。Python 脚本仅用标准库；离线权限用 PHP/PDO SQLite，实际环境需要 Docker 与宿主依赖。新建实验室显式输入 --source，示例打包不需要 SaiAdmin 源码。

附带Dockerfile已直接从官方php:8.4-cli-bookworm和composer:2构建成功；容器内验证pdo_mysql、pdo_pgsql、pcntl、posix、zip、intl、mbstring、gd、curl、DOM/XML和redis扩展加载，Composer命令可用。镜像本身不打入Skill压缩包，首次使用需联网构建。

## SaiStore CLI（2026-11-16）

新增 [登录与上传说明](saistore-upload.md) 和 [协议证据](saistore-protocol.json)。核对真实后台可见表单、已登录列表请求与公开前端资源，公开验证码接口实测成功。CLI 由用户手工输入验证码和隐藏密码，将 access/refresh token 成对保存到工作区外的私有目录；没有可确认的刷新路由时不猜测调用。

本机 HTTP 夹具覆盖登录/cookie、密码与令牌脱敏、权限/站点绑定、HTTP/重定向边界、ZIP 预检、multipart、版本/图片/回执与独立审核。未用真实账号验证 CLI 登录或提交任何真实应用/版本/审核，不能把夹具测试写成商店实测。真实登录由用户在终端完成，真实写入仅在具体应用、包和目标范围已明确授权后执行。

## 系统与数据权限参考（2026-11-16）

检查给定 `数据权限.zip` 的 8 个载荷文件，归纳为 [权限点与 DataScope 接入](permissions-data-scope.md)。原包 SHA256 为 `6b2ae4caac60404d5878bfa8505b45ae59884455c43232a641d46eea85cb0ae6`，其中 ThinkORM BaseLogic SHA256 为 `7329d70af894d0dbd5978daf3c6d4bd9d29f4378c665cb40529d633509316caa`。包没有精确发行版本及标准业务包元数据；没有执行其 install.sql 或覆盖宿主，也不把原始包作为 skill 的依赖/附件分发。

在一次性目录中以 PHP 替身提供身份缓存、父类及只记录条件的查询对象，直接加载给定 BaseLogic，三个断言通过：空角色列表返回无条件查询；同实例先后为用户 11/22 调用，本人范围混入两个 ID；全部+本人角色最终按本人过滤。此探针只复现基类条件构造，不涉及数据库、权限中间件或浏览器，不代表完整安全验收。源码另确认数据权限按钮使用 core:role:menu、后端使用 core:role:data，以及固定菜单 ID 的 SQL 等差异。

参考包自身不含 BaseModel；创建者赋值与只读字段另核对前述 SaiAdmin 6.1.5 基线的 BaseModel，不能据此保证自定义模型/原始 SQL 安全。补充的要求覆盖能力预检、权限点迁移、角色与部门缓存、归属字段、自定义查询及受限账号矩阵。原有 labphinx 仍是生命周期夹具；下面新增的 labpermit 才演示业务权限，两者不混算。

## Board Studio 2.2.0 与独立权限示例

依据已发布的提交 9367d71430a0d132c2f398510fabd88e80628fa9，补充 [权限/PG 排错](runtime-pitfalls.md)：JSON 拒绝、响应式按钮、授权树翻译、bigint 参数推断、初始化 TCP/重载和安装状态判定。该插件的双库与浏览器证据引用锁定版本；参考包自身的未测部分仍保持未测。

新增 assets/permission-fixture（labpermit），保留提取自 Board Studio 的 MIT 许可，不需要原仓库或历史测试目录。附带两版 ZIP 生成、SQLite 权限登记/迁移/撤权/事务恢复、Python 六项安装状态与有界重试回归。self_test.py 将整个 skill 搬到含空格的新目录再运行；初始化器、示例生成器与 HTTP 测试通过自身位置找配套文件，基线仅从显式 --source 输入。

初始化器只支持已核对的 6.1.5/6.1.0 HTTP/Phinx 分支；实际安装器副本可能含前期本地修复，记录其 SHA256 而不宣称原始官方安装器。运行前提和双库命令见 [权限示例](permission-example.md)。CLI 测试令牌、私有状态和身份替身不进入示例 ZIP；HTTP 请求仍执行真正的 CheckLogin 与权限中间件，本轮不冒充浏览器登录/主题验收。

### 本轮实际结果（2026-11-16）

将最终 skill 整目录复制到含空格的新路径，从该副本分别创建 MySQL 8.4 与 PostgreSQL 17 的全新源码/网络/卷。使用 PHP 8.4、上述锁定基线和显式指定的本机镜像；基线运行安装器保留既有修复。PG 镜像为 amd64 模拟运行，不作原生性能结论。

| 项目 | MySQL | PostgreSQL |
|---|---|---|
| TCP 就绪、核心 HTTP 初始化、重载收敛与认证读取 | 通过 | 通过 |
| 1.0.0 ZIP 首装→造数/旧授权→1.1.0 ZIP 升级、归属/数据/映射保留 | 通过 | 通过 |
| 同版本重复上传拒绝、七动作拒绝仅菜单账号、匿名与无权账号拒绝 | 通过 | 通过 |
| 五范围列表、限页总数、聚合值、详情与嵌套资源 | 通过 | 通过 |
| 创建者防伪、修改不转移归属、混合有权/无权批量原子拒绝 | 通过 | 通过 |
| 同会话撤权、重复登记不重新授予、实例复用与异常范围 | 通过 | 通过 |
| 非空卸载拒绝、空库卸载保留角色/部门/共享菜单并清除自身表/迁移记录 | 通过 | 通过 |
| 新版空库重装与再次卸载 | 通过 | 通过 |
| TEMP 表 insertAll 42804 复现、回滚、绑定 VALUES、保护卸载后无闲置事务 | 不适用 | 通过 |

离线 SQLite、六项 Python 状态/有界重试测试、四个示例 ZIP 搬移自检、完整仓库验证均通过；宝塔官方文件逐文件校验保持不变。示例新增迁移失败回滚及按追踪账号清理数据，避免无条件 ORM delete；PG TEMP 表探针显式提供字段类型，避免将 ORM 的临时表元数据限制误当成绑定错误。安装/卸载响应未知时只读核对，不重复 POST；确认安装完成后重启临时后端，再做业务断言。失败调试轮不算作最终通过轮次，所有本轮实验室在取证后按各自 Compose 项目清理。

本轮没有重新做前端/浏览器验收：labpermit 是纯 API 示例；前端指令、菜单翻译及第四文件接入的证据来自上面锁定的 Board Studio 2.2.0。两层证据与各自能力边界分别记录。
