# 可反复创建的 Docker 实验室

脚本相对路径均以本 skill 目录为起点。只绑定 localhost 的随机宿主端口；数据库/Redis 不暴露宿主端口；Compose 服务名相同但每次 project 唯一，网络、数据库、node_modules、pnpm 存储均隔离。两个实验室不共享可写源码，不使用固定 container_name、external 卷或生产网络。

## 准备可复制基线

独立使用需要 Python3.9+、Git、Docker Engine/Compose 和下载依赖的网络。先进入解压后的 `saiadmin6-plugin` 目录。安装Skill时将此目录放入你的 Codex skills 目录；直接运行脚本也不要求安装。

在新目录克隆官方 `https://github.com/saithink/saiadmin6.x.git`，记录 `git rev-parse HEAD`。检查 composer.json 后在 PHP 容器运行 composer install，记录生成的 composer.lock；官方仓库若不提供锁，解析结果并不天然可复现。未来同轮测试用相同基线与锁，不每轮更新依赖。确保该基线未安装待测业务插件，没有运行数据或真实凭据。

```sh
git clone https://github.com/saithink/saiadmin6.x.git ./baseline
python3 scripts/lab.py create --source ./baseline
# 返回新建实验室的绝对路径（下文用 LAB 代指该实际路径）
python3 scripts/lab.py compose LAB build backend
python3 scripts/lab.py compose LAB run --rm --no-deps backend composer install --no-interaction --prefer-dist
python3 scripts/lab.py compose LAB up -d db redis backend
python3 scripts/lab.py compose LAB port backend 8787
```

若已准备干净 vendor：加 `--copy-vendor`。可加 `--php-image image:tag` 重用本机已验证镜像（须有 docker-php-entrypoint、PHP CLI、Composer、pdo_mysql、pcntl、posix、zip、mbstring、gd 等所需扩展），避免重复构建。附带 Dockerfile 是通用起点，锁文件新增扩展依赖时补装再验证；PostgreSQL 使用 `--db pgsql`（默认 postgres:17-alpine）；附带 Dockerfile 已包含 pdo_pgsql。通过 `--db-image` 指定版本。Mac ARM 上检查缓存镜像架构，不要把模拟运行当作原生性能测试。

`create` 只复制指定 server/saiadmin-artd 子树，排除后端 `.env`、runtime、node_modules 和 .git。它不净化任意定制源代码里的其他敏感文件，且复制会解引用符号链接，因此优先使用无外部符号链接的官方基线。复制过来的 config 中若写死外部数据库、缓存、对象存储地址，先修正临时副本；容器网络并不是禁止外连的沙盒。自有仓库须确认不含生产配置和已安装待测插件。

## 核心初始化

脚本通过容器环境变量指向 `db` / `redis`，不生成后端 `.env`，保留安装向导入口。打开上一步随机端口的 `/core/install`，数据库 host 填 `db`、库 `saiadmin`、MySQL用户 `root`、端口3306；PostgreSQL用户 `postgres`、端口5432，密码来自 `LAB/db-secret`（只在本地读取，不贴回聊天）。完成核心初始化后检查真实表与管理员登录。

自动化时先检查该版本 InstallController 与实际路由，再向已验证路径提交参数；不要猜测安装 API。不同版本用 SQL 导入或 Phinx 初始化，按真实源码选择；不要在同一数据库先跑向导又跑整套 SQL。`.env` 已存在时向导可能拒绝安装。复跑核心初始化应新建实验室，不删除现有业务库试运气。

## 启动前端与插件导入

```sh
python3 scripts/lab.py compose LAB up -d frontend
python3 scripts/lab.py compose LAB port frontend 3006
python3 scripts/lab.py compose LAB logs --tail 80 frontend backend
```

默认 Node22、Corepack、pnpm10.11.0（可用 `--pnpm-version` 指定）、锁定依赖安装，Vite 使用 `http://backend:8787` 代理。pnpm 版本以 packageManager/基线为准；如果旧 pnpm 锁不兼容，先在基线明确固定版本，再复用。镜像或 Corepack 不包含命令时先处理工具链，不能删锁绕过错误。依赖安装会影响该实验室的清单/锁，保留供比较。

登录本地管理端，使用插件管理的上传 ZIP→安装→依赖处理流程。HTTP 自动化可复用浏览器已验证端点/令牌（不记录令牌）；登录含验证码时正常登录，不修改中间件绕过认证。逻辑层脚本能验证安装机制，但不能代替 HTTP 上传、权限和浏览器验收。

## 新轮次与清理

第二轮重新 `create` 并执行初始化；不会复用第一轮 runtime 或 DB。仅 `restart`、`up --force-recreate` 或 `down` 都不是干净重装。`down -v` 也保留 bind mount 源码及暂存记录；要全新首装应重新 create。

```sh
python3 scripts/lab.py compose LAB down -v --remove-orphans
```

此命令只删除该项目的容器、网络、声明卷；源码和日志留在 LAB。禁止 `docker system prune` / 批量删全部卷。确认不再需要证据后才删除这一 LAB 目录。每轮记录版本、ZIP SHA256、端口、断言与清理情况，不输出 env、密码或完整认证请求。

## CLI 逻辑层测试特别注意

6.1.0 `InstallLogic::install/uninstall` 使用 `self::restartServer()`，其内部可能调用 `posix_kill(posix_getppid(), SIGUSR1)`。在 `docker compose exec php test.php` 中父进程可能是 exec 的包装进程，导致退出码138；简单子类覆盖 restartServer 并不能拦截 `self::` 调用。优先 HTTP 正常请求。若专门做逻辑层测试，可在一次性测试 harness 内为 `Saithink\Saipackage\service` 命名空间提供隔离的 posix_kill stub，只屏蔽该测试进程的信号副作用，并明确标记未验证真实 reload；不要改框架源文件或把 stub 放进发行包。

## 已复现的 HTTP 重载竞争

saipackage6.1.0 在 Linux 安装/卸载结束时立即 SIGUSR1，有时导致 HTTP 响应发送前连接关闭。先查询列表和数据库，不能无条件重装。`python3 scripts/fix_reload.py LAB` 可对已核对形状的临时安装器副本应用 0.5 秒延迟重载，再 `compose LAB restart backend`。补丁保留真实重载；已通过 MySQL/PostgreSQL HTTP 生命周期验证。仅作用于实验室，不自动修改用户项目或 vendor，其他版本须先核对源代码。

核心初始化前提供 DB_NAME 环境变量可能让定时任务进程先查询尚未建立的表，日志出现表缺失；PG还可能提示 table_msg 不存在。核心迁移完成且重启后应消失。若仍存在，检查核心 CreatePgsqlHelpers 迁移，不能只建业务表绕过。

## 浏览器上传工具

本次 Chrome 扩展的 filechooser.setFiles 要求“允许访问文件网址”。缺少权限时不要误判为插件上传接口失败；使用系统选择器，或向用户明确请求此权限。上传按钮先打开应用弹窗，弹窗中的“点击上传”才触发系统文件选择器。验证码按工具要求逐次确认，不关停认证来完成界面验收。

安装返回成功后等待新路由可用：在最多15秒内有界轮询（无写入的GET），服务仍在reload时允许短暂404/连接断开。超时后保留日志检查，不自动重装。固定sleep 1秒不足以验证多worker收敛。

还须同时核对 package app/version/state、迁移和 schema。PG 健康检查已指定 TCP host；核心初始化延迟重载中断插件迁移等问题见 [实测排错](runtime-pitfalls.md)。新的 [权限示例](permission-example.md) 提供显式初始化器与双库命令，不依赖 Board Studio 或历史测试目录；原 labphinx 仍只是生命周期夹具。

## 独立生成示例包

在Skill根目录运行：

```sh
python3 scripts/build_example.py --output-dir ./output/examples
python3 scripts/self_test.py
```

先安装输出的labphinx-1.0.0.zip，再上传labphinx-1.0.1.zip测试升级；也可在另一干净环境直接安装1.0.1。示例无需本次会话文件，模板不会被修改。示例带已登录数据读取接口，不代表具备完整业务角色授权，请勿直接用于生产。
