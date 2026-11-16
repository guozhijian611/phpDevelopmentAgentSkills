# 版本与来源

核对日期：2026-11-16。官方文档当前已包含 2.14 API；核对源码 dev 快照 `3b5d0ad35b1d309a3430b49db9be1369f0966321` 仅代表上游开发状态，不宣称其为稳定发行版，也不据此升级用户项目。

| 功能 | 最低/迁移边界 | 使用要求 |
| --- | --- | --- |
| Checkbox/Radio value | 2.6.0 | label 作为值已弃用，3.0 移除；旧版按原类型/API |
| InputTag | 2.9.0 | 先核对项目版本与自动导入配置 |
| Splitter | 2.10.0 | 核对可用属性与响应式尺寸 |
| ColorPickerPanel | 2.11.0 | 不等同于旧 ColorPicker API |
| InputOTP | 2.14.0 | 低版本不能直接生成该控件 |

- [Checkbox 迁移说明](https://element-plus.org/en-US/component/checkbox.html)
- [Radio](https://element-plus.org/en-US/component/radio.html)
- [国际化](https://element-plus.org/en-US/guide/i18n.html)
- [暗色模式](https://element-plus.org/en-US/guide/dark-mode.html)
- [上游源码快照](https://github.com/element-plus/element-plus/tree/3b5d0ad35b1d309a3430b49db9be1369f0966321)

使用示意（>=2.6，t 为宿主翻译函数）：

```vue
<el-checkbox-group v-model="features">
  <el-checkbox value="enabled">{{ t('feature.enabled') }}</el-checkbox>
</el-checkbox-group>
<el-radio-group v-model="status">
  <el-radio value="active">{{ t('status.active') }}</el-radio>
</el-radio-group>
```

ConfigProvider 的组件库 locale 与业务 i18n 同步；不要以给所有 label 加翻译替代真实运行时切换验收。原 API 参考是基础用法摘录，新属性以目标安装包的类型和对应文档为准。
