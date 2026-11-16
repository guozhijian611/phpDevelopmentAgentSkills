# 版本与来源

核对日期：2026-11-16。webman-framework master 快照 `263ef955d8ba6a0cb6fbc1bd0912589ed67c0c8d`。官方已有 2.1、2.2 升级指南；维护旧项目仍以 composer.lock 为准。

| 范围 | 约束 |
| --- | --- |
| 1.x / 2.0 | 不假定具备 2.1 协程/池 API，按原适配器与路由方式 |
| 2.1 | PHP >=8.1、Workerman >=5.1；Swoole/Swow/Fiber 和 eventLoop 显式配置，协程默认关闭 |
| 2.1 适配器 | webman/database、redis、cache、think-orm、think-cache 对应版本增加池支持，核对连接归还和事务行为 |
| 2.2 | 新增注解路由；注册与语法按目标源码，不强制迁移旧路由 |

- [2.1 升级](https://webman.workerman.net/doc/zh-cn/upgrade/2-1.html)
- [2.2 升级](https://webman.workerman.net/doc/zh-cn/upgrade/2-2.html)
- [协程前提与限制](https://webman.workerman.net/doc/zh-cn/coroutine/coroutine.html)
- [编程须知](https://webman.workerman.net/doc/zh-cn/attention.html)

不能照抄升级页中的全局 composer config 操作改变用户镜像；只在明确升级任务中调整项目依赖并检查 lock。框架宣称的基准性能不是用户服务的性能验收结果。协程中身份、日志上下文、事务与连接不得通过静态全局变量跨请求共享；异常/取消路径要释放资源。
