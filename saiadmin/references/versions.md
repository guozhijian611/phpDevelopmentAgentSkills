# 版本与来源

核对日期：2026-11-16。SaiAdmin 6.x 源码提交 `598178195a27a9a024a3cd20a0188d3117b9e09f`。目标运行副本与 Composer vendor 可能不同，优先读取实际 plugin/saiadmin、middleware 与前端封装。

- [6.x 分层架构](https://saithink.top/documents/v6/back/develop.html)：Controller/Logic/Model/Validate。
- [6.x 前端开发](https://saithink.top/documents/v6/front/develop.html)：views/plugin 内部 API 与页面。
- [6.x 源码](https://github.com/saithink/saiadmin/tree/598178195a27a9a024a3cd20a0188d3117b9e09f)。

BaseController 继承 OpenController，但是否免登录由路由/中间件共同决定。前端与独立 Art Design Pro 的 API/路由/目录不同，不能因同一组件体系就照搬。安装目录由目标安装器决定，6.x 不能沿用旧 5.x 插件路径。自动接入仍需目标安装器生命周期支持；不默认给核心加补丁。
