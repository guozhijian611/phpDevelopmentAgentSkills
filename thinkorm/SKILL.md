---
name: thinkorm
description: 使用 ThinkORM 3.x/4.x 开发查询、模型、关联、事务和实体分层，按锁文件区分版本、数据库方言及 Webman 连接池适配。
---

# ThinkORM 开发

先查 composer.lock 中 topthink/think-orm、框架适配器、think-helper 和 PSR 依赖。官方 4.x 已加入 Entity，3.x 基础示例仍可按版本使用；[版本与来源](references/versions.md)。

## 版本与建模

- 保留项目锁定版本，不自动升大版本。独立 3.x 示例安装用 composer require topthink/think-orm:^3.0；明确采用 4.x 才选 ^4.0 并核对适配器、PSR 缓存约束和回归。
- 3.x 使用 Model、搜索器、关联及服务层；4.x Entity/仓储分层按实际 API 使用，不把旧 Model 示例直接标作 Entity。
- Webman 优先复用 support/宿主封装的 Db、Model 与连接池，不能另建不同步的全局连接。

## 查询与保护

- 外部参数使用构造器或绑定，动态表/字段/排序白名单化。模型允许字段与身份/所有者校验分开，不任意写入整个请求。
- 列表、统计、导出、关联都保留身份/租户/软删除范围；管理员能力不自动推广给普通账号。
- 事务同连接执行，异常回滚，不跨协程共享。MySQL DDL 与 PostgreSQL 行为不同，事务不等于 DDL/文件全局回滚。
- 避免关联 N+1，明确一对多聚合的重复计数；分页稳定排序，检查真实 SQL 与计划。
- decimal 精度、null、JSON 和时间按实际类型处理。软删除、恢复和强制删除按业务授权，不用 force 绕过保留策略。

查基础 Query/Model/关联用 [API 参考](references/api-guide.md)，4.x 实体与适配用 [版本说明](references/versions.md)。验证数据库行为、事务异常和作用域，语法检查不能证明查询正确。
