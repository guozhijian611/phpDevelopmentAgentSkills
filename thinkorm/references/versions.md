# 版本与来源

核对日期：2026-11-16。官方 4.0 分支快照 `d13ab1b282fe5a8c9d09c676193bed5891f7d1bd`，要求 PHP >=8.0；该快照 psr/simple-cache 为 ^3.0。宿主的 Webman/Think 缓存适配版本仍须联动核对。

- [官方 4.0 发布与 Entity 分层说明](https://www.thinkphp.cn/news/370)
- [4.0 源码](https://github.com/top-think/think-orm/tree/d13ab1b282fe5a8c9d09c676193bed5891f7d1bd)
- [官方手册](https://doc.thinkphp.cn/@think-orm)

3.x 基础 API 参考继续明确标作 3.x。官方说明 4.0 增加 Entity，并且 3.0 不再更新功能；不据此擅自升级现有项目。4.x 中 Model 侧重查询、关联、事件与持久化，Entity 用于数据定义/展示/处理，复杂业务仍可独立服务层；具体声明、返回类型和访问方式读取该版本源码，不杜撰把旧 Model 改个类名就能使用的示例。

3.x 复现命令限定 ^3.0，4.x 新项目明确选择 ^4.0。官方兼容说明不代替目标项目测试，尤其 PSR 接口、模型属性、序列化、关系返回和框架连接池适配。不要直接在 Webman 中用独立 ORM 初始化覆盖宿主连接。
