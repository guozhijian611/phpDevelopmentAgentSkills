---
name: elementplus
description: 使用 Element Plus 开发 Vue 3 表格、表单、弹窗、选择器和上传界面；按锁定版本核对 API、弃用项、主题、语言与无障碍。
---

# Element Plus 组件开发

先读目标 element-plus 精确版本、自动导入/样式、ConfigProvider 和封装组件。官网当前文档不等于旧项目能力；[版本与弃用项](references/versions.md)。

## 生成约束

- 复用宿主封装、语义 token、暗色方案、主色和 locale，不覆盖全局 body/组件。核对 Teleport 弹出层的主题和 scoped 样式。
- UI 文案走宿主 i18n，表头/校验/选项响应式翻译，组件库语言同步；业务数据不自动翻译。
- Checkbox/Radio 自 2.6.0 起用独立 value，label 只负责展示；label 充当值已弃用，3.0 移除。低于 2.6 的项目按原 API 处理。
- 新 API 先核对版本：InputTag 2.9、Splitter 2.10、ColorPickerPanel 2.11、InputOTP 2.14。不能仅按最新官网为旧项目生成不存在的控件。
- Table 使用稳定 row-key，服务端排序设 custom；明确跨页选择、动态列及语言变化后的布局策略。
- Form 的 model/prop/rules 对应，异步提交去重。Dialog/Drawer 用 v-model，区分新增、编辑、关闭及未保存确认，不用重建页面实现语言切换。
- Upload 自定义请求处理成功/失败/取消和凭据范围，服务端再校验文件；日期的显示格式、存储格式和时区分别处理。
- 保留键盘、焦点、可访问标签；核对长译文、空态、禁用状态、明暗主题和主色。

查属性/事件时按需读 [组件 API 参考](references/api-guide.md)，与目标类型定义核对；类型检查和构建不代替真实交互验收。
