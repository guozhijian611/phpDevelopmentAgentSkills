# 版本与来源

核对日期：2026-11-16。base 快照 `8277fab1eccf7464d4fe63310309ad5c35cc2ce9` 的 package.json 为 4.4.1、Node >=20、pnpm >=9、packageManager pnpm@10.10.0；main/CLI 快照 `6ec319432a59b3c1e8e1bf401a56c4a8a8d9dab4`。官网部分页标题仍为 4.1.1，因此不能把网页标题当成模板精确版本。

- [base 模板](https://github.com/feige996/unibest/tree/8277fab1eccf7464d4fe63310309ad5c35cc2ce9)
- [main 与 CLI](https://github.com/feige996/unibest/tree/6ec319432a59b3c1e8e1bf401a56c4a8a8d9dab4)
- [常见问题与分支说明](https://www.unibest.tech/base/14-faq)
- [更新日志](https://www.unibest.tech/changelog/CHANGELOG)

main 包含 CLI 与模板源码，base 是用户创建项目的纯模板。安装或升级以目标 lock、SDK/HBuilderX 和工具链为准；旧 FAQ 的 esbuild 0.20.2、Vue Official 2.2.8 或 oxlint/unocss 固定版本仅是对应历史问题线索，不作为所有项目降级方案。先比对实际宿主/二进制版本、锁文件与错误文本，再做最小调整。

本 skill 独立安装不包含本仓库根的参考手册。需要源码时可使用用户项目、上面的锁定源码链接，或在用户指定目录浅克隆 base/main；无需本次会话路径。仓库参考手册只是历史离线快照，不能作为当前上游版本保证。
