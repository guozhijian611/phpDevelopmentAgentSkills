# 权限与 PostgreSQL 实测排错

以下来自 SaiAdmin 6.1.5 / saipackage 6.1.0、PHP 8.4、ThinkORM 分支的实际问题。先核对锁文件和运行副本，不把补丁应用到所有 6.x，也不自动扩展为宿主全局 RBAC 审计。

## 拒绝请求、按钮与授权树

- 基线 CheckAuth 经 SystemException 隐式 nullable 参数在 PHP 8.4 触发弃用异常，未授权请求变成 HTML/500。优先使用宿主修复；必要时仅在插件路由内适配，保留 CheckLogin/审计，复用 Permission 反射、UserAuthCache 和有效账号检查，缺少声明默认拒绝，稳定返回 JSON 401/403。不要关闭错误报告或绕过认证。
- Element Plus 下拉项可能是 fragment 根，v-permission 不生效；一次性移除 DOM 的指令也可能让动态弹窗恢复权限后按钮不回来。实测控制台和按钮，必要时改用宿主响应式 user store 与 v-if。只读页面不要自动请求未授权的连接结构、历史或令牌接口。
- 菜单保存 i18n 键时，角色授权树也须调用宿主 formatMenuTitle。导航正常翻译不代表授权树正常。必要接入采用完整预检/管理片段/卸载策略，不整份覆盖角色页面。
- 核对隐藏参数路由排序与默认落地页，用普通账号正常登录；不能让其落到 designer/:id 这样的占位路径。

## PostgreSQL bigint 批量插入 42804

该基线角色菜单的 insertAll（含 limit(100) 变体）生成 INSERT ... SELECT ... UNION，绑定参数推断为 text，插入 bigint role_id/menu_id 失败。单行 VALUES 不走这个推断路径。

```php
// 已完成原目标角色/可授菜单校验，且在原事务中；值来自服务器整理的绑定参数。
foreach ($rows as $row) {
    Db::table($ownedRelationTable)->insert($row);
}
```

也可用经验证的 VALUES 批量实现或正确类型绑定；不能拼接用户输入、全局修改 ORM、吞错或把 bigint 改成文本列。错误后先回滚再继续，并从其它连接检查 idle-in-transaction。插件自己的关系迁移使用显式列和绑定 VALUES，不照搬固定菜单 ID 的 MySQL SQL。

若业务确需修复宿主角色菜单 API，先考虑官方修复/确认依赖；必要的局部兼容只识别已核对语句，保留原路由、鉴权、事务和缓存，随安装升级自动接入、卸载准确还原。后端文件和全部前端文件一起预检、备份、回退；未知结构或被改动的管理片段明确拒绝。Board Studio 已验证第四个目标失败回退；附带通用示例不修改宿主文件、不冒充全局修复。

## 就绪、重载与安装状态

1. postgres 初始化时先启动 Unix socket 临时服务，未指定 host 的 pg_isready 可能提前成功。Compose 改用 pg_isready -h 127.0.0.1，并从 PHP 容器确认 db:5432 TCP；不能用固定 sleep 代替。
2. 核心初始化响应返回时，SIGUSR1 重载仍可能在途。一次性测试先完成重启，重新发现随机端口，认证读取核心 API，再开始插件 DDL；否则旧 worker 延迟退出会中断首次迁移。
3. 开发文件监视器可能在复制 ZIP 的 PHP 文件时重载。一次性环境可关闭开发文件监视器模拟生产行为，但保留安装器实际重载并记录该设置；不把它打进插件或改动现有项目。
4. 路由能读到不代表迁移成功。共同确认 package app/version/state、迁移、schema/权限点及受认证接口。依赖等待 4 与安装完成 1 分开；未安装依赖时不能人为标记完成。
5. 写入响应断开时只读核对，不能盲目重发上传/安装/删除；有界超时停止。容器重启可能改变宿主随机端口，重新 compose port。

权限测试还复现了重装后“某个 worker 返回成功，下一次请求却是旧路由 HTML”的窗口。附带工具在安装器的版本/state/路由检查完成后，统一重启该临时后端、重新发现端口并等认证接口就绪，再开始业务断言；保留此前实际安装重载过程，不用人工标记状态代替成功。卸载响应中断同样只读确认移除，不重复 POST。

prepare_fixture_lab.py 仅初始化明确版本的全新实验室，处理 TCP/重载并生成私有测试令牌。fixture_package.py 仅接收 labpermit，单次写入后检查版本+状态+路由。CLI 签发 JWT 是一次性造数，不导出浏览器会话、不修改 Web 认证，也不代表正常登录/验证码验收。

## 证据边界

锁定 [Board Studio 9367d71](https://github.com/guozhijian611/saiadmin-boardstudio/tree/9367d71430a0d132c2f398510fabd88e80628fa9) 的 [权限验收](https://github.com/guozhijian611/saiadmin-boardstudio/blob/9367d71430a0d132c2f398510fabd88e80628fa9/docs/permissions.md)。2.2.0 已通过双库真 ZIP 首装、2.1.1 升级、权限/撤权/卸载及 MySQL 普通账号浏览器保存发布。安装器存在已记录的本地修复，不能只引用官方 Git SHA 就宣称原始源码通过。任意新插件仍按自身资源 ACL、数据源及发布策略另行测试。
