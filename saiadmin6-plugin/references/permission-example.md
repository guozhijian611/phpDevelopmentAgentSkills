# 独立权限示例

assets/permission-fixture 是后台纯 API 的 labpermit 示例，不提供前端页面、数据源、缓存或发布功能；不把未实现的能力算作已测。原 labphinx 仍只用于表/种子生命周期。实际业务另外遵循 [验收矩阵](acceptance.md)。

## 生成和离线测试

从解压后的 skill 根运行；脚本用自身位置寻找 assets/tests，支持含空格的路径及任意当前工作目录。

```sh
python3 scripts/build_permission_example.py --output-dir ./output/permissions
php tests/permissions.php
python3 scripts/self_test.py
```

需要 Python 3.9+、PHP 8.4 CLI（PDO SQLite），完整配置自检需要 Docker Compose；无 Docker 加 --skip-docker。SQLite 只验证登记服务写入，不冒充 MySQL/PG 或 HTTP。

生成 1.0.0 与 1.1.0 两版 ZIP。旧 Controller/菜单使用 legacy:read/write；新版分成七动作，由第二个迁移按原对应授权映射。普通角色默认无授权，测试 harness 在独立库造数。重复接入保持 ID、不恢复后来撤销的权限。非空卸载在清理前拒绝；空库仅删自身权限，不删角色/部门/core:role:data。

## 全新双库 HTTP 测试

依赖 Docker、网络、附带 PHP 镜像及明确准备的干净 SaiAdmin 基线。初始化器仅验证 SaiAdmin 6.1.5 / saipackage 6.1.0 的 HTTP/Phinx 分支；基线须包含支持 Phinx 的安装器，存在本地修复时如实记录。工具生成 baseline-sha256.json，不下载或覆盖未知核心。

```sh
# 先按 docker-lab.md 准备 Composer 依赖；BASELINE 换成自己的路径。
python3 scripts/lab.py create --source /absolute/path/to/BASELINE --db mysql --copy-vendor
# 用返回的绝对目录替换 LAB；不复用已初始化的旧 LAB。
python3 scripts/lab.py compose LAB build backend
python3 scripts/lab.py compose LAB up -d db redis backend
python3 scripts/prepare_fixture_lab.py --lab LAB --disposable-fixture
python3 scripts/test_permissions_lab.py --lab LAB --disposable-fixture
python3 scripts/lab.py compose LAB down -v --remove-orphans
```

另一轮用 --db pgsql 重新 create，执行相同命令。--php-image 可指定已验证镜像，不传则构建附带 Dockerfile。未准备 vendor 时去掉 --copy-vendor，并在启动前用 compose run --rm --no-deps backend composer install --no-interaction --prefer-dist 安装锁定依赖。示例 config.json 无额外依赖，要求状态 1，不虚报依赖完成；纯 API 无需启动/构建管理端。

流程：旧版真实上传→合成数据授权→新版升级→同版本重复上传→七动作拒绝仅菜单账号→五范围 SQL 列表/总数/统计/子资源→混合删除原子性→伪造新增/修改归属→同会话撤权与重复接入→实例复用/异常范围→PG TEMP 表 insertAll 类型探针、回滚与 VALUES→保护卸载→清理示例数据→卸载保留系统资源→新版空库重装再卸载。已修复 ORM 可显示 reproduced=no，不强制重现历史错误。

工具只接受 lab.py 记录的 localhost，不接受远程 URL。JWT 仅在实验室私有文件保存，走实际 HTTP 中间件；CLI 身份替身仅用于单进程复用测试，不进入 Web。测试不代表正常登录/验证码或浏览器验收。

每轮必须没有 labpermit 或上轮 runtime/labpermit-fixture.json；命令会删除目标实验室的示例记录，成功/失败都保留实验室供检查，再由调用者按上面命令清理。不自动销毁卷、不读取本次历史临时目录，不把 helper、账号、令牌或 TEMP 探针放进业务包。

测试在每次确认 ZIP 安装完成后重启一次该实验室后端，等待全部 worker 使用新文件；初始化后的重载也先收敛。此设置记录为测试条件，不将一次成功响应当成所有 worker 已更新。保护卸载失败会显式回滚迁移事务，避免阻塞下一步清理。
