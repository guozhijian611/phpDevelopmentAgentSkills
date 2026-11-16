---
name: saiadmin
description: 开发维护 SaiAdmin 6.x 的控制器、Logic、Model、校验、权限与前端页面；遵循宿主主题和多语言，插件发行衔接 saiadmin6-plugin。
---

# SaiAdmin 6 业务开发

先检查项目规范、composer.lock、前端 package.json、相邻模块和真实路由。确认后端/前端路径、ORM、菜单权限中间件，不按文档假设运行副本。依据见 [版本与来源](references/versions.md)。

## 业务开发

- Controller 取参、校验和响应，Logic 处理业务，Model 定义映射、搜索及关联，Validate 定义规则；复用目标基类的实际签名与返回类型。
- 业务代码放自身模块，不生成到 saiadmin、saicode、saipackage 核心目录。继承 BaseController 不代替认证中间件；公开接口单独核对访问与数据范围。
- 菜单、按钮、接口权限编码一致，受限账号在服务端验证。行级、部门和租户条件来自服务器身份，不能信任前端隐藏或请求中的所有者字段。
- schema 变更遵循已有迁移机制，MySQL/PostgreSQL 分别核对；当前数据库不能代替可重复初始化。按已有任务授权执行必要构建与隔离测试，避免重复确认普通验证；生产变更不扩大范围。
- 前端代理和真实路由前缀分别核对。普通业务代码变化通常 reload，进程配置/依赖变化通常 restart，以实际进程管理方式为准并核对服务。

## 前端与插件发行

生成前读 [主题与多语言约定](references/frontend.md)。后台复用宿主布局、组件、语义 token、locale 和翻译入口；所有新增界面文案覆盖宿主支持语言，表头、规则和选项响应式翻译。主题/语言切换不重建丢失表单，用户标题、数据与画布颜色保持独立。

独立 ZIP 发行时使用可用的 saiadmin6-plugin 规范；未安装时直接核对安装器复制/迁移顺序，实现首装/升级自动接入、备份幂等、卸载数据保护及最终 ZIP 验收。正常安装不得要求用户额外跑接入脚本；依赖/构建沿用宿主流程，不等于自动部署。

## 按需查阅与验证

查 Controller/Logic/Model/SAI 组件时读 [API 与模板](references/api-guide.md)，替换占位符并本地化文案。SaiCode 先预览、核对目标表/菜单和 git diff，再生成；检查权限与真实接口。验证 PHP、逻辑/接口、受限账号、主题及语言；schema 或发行改动再增加隔离库生命周期测试。
