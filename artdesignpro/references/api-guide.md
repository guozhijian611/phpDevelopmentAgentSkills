# 基础 API 与模板参考

保留原有框架/API示例供按需查阅。先阅读 [当前版本与来源](versions.md)，以目标项目源码和锁文件为准；示例中的中文文案、路径和配置不是可不经核对直接生成的业务实现。前端生成必须应用入口的主题与多语言要求。

# Art Design Pro 开发技能

> **生成时间**: 2026-02-08
> **官方文档**: https://www.artd.pro/
> **GitHub**: https://github.com/Daymychen/art-design-pro

---

## 一、技术栈

- **核心框架**: Vue 3、TypeScript、Vite
- **UI 组件库**: Element Plus
- **样式方案**: Tailwind CSS、Sass
- **代码质量**: ESLint、Prettier、Stylelint
- **工程化**: Husky、Lint-staged、cz-git
- **状态管理**: Pinia
- **图标库**: Iconify (Remix Icon)

---

## 二、项目结构

```
├── src
│   ├── api/                 # API 接口
│   ├── assets/              # 静态资源 (images/styles/svg)
│   ├── components/
│   │   ├── business/        # 业务组件
│   │   └── core/            # 核心组件 (banners/cards/charts/forms/tables...)
│   ├── config/              # 项目配置
│   ├── directives/          # Vue 自定义指令
│   ├── enums/               # 枚举定义
│   ├── hooks/               # Vue 3 Composable 函数
│   ├── locales/             # 国际化资源
│   ├── plugins/             # 插件配置
│   ├── router/
│   │   ├── routes/asyncRoutes.ts    # 动态路由
│   │   └── routes/staticRoutes.ts   # 静态路由
│   ├── store/               # Pinia 状态管理
│   ├── types/               # TypeScript 类型定义
│   ├── utils/               # 工具函数
│   └── views/               # 页面组件
├── .env                     # 通用环境变量
├── .env.development         # 开发环境变量
├── .env.production          # 生产环境变量
└── vite.config.ts           # Vite 配置
```

---

## 三、快速开始

### 环境要求

- Node.js 20.19.0+
- 推荐使用 pnpm

### 安装运行

```bash
# 克隆代码
git clone https://github.com/Daymychen/art-design-pro

# 安装依赖
pnpm install
# 仅在目标项目明确禁止生命周期脚本时使用 --ignore-scripts，并核对缺失生成物

# 开发运行 (默认端口 3006)
pnpm dev

# 生产构建
pnpm build

# 精简版本 (清理演示数据)
pnpm clean:dev
```

---

## 四、路由和菜单配置

### 4.1 路由类型

| 类型     | 配置位置                            | 说明                              |
| -------- | ----------------------------------- | --------------------------------- |
| 静态路由 | `src/router/routes/staticRoutes.ts` | 无需权限的基础页面 (登录/404/500) |
| 动态路由 | `src/router/routes/asyncRoutes.ts`  | 需要权限控制的业务页面            |

### 4.2 权限模式配置

在 `.env` 文件中配置：

```env
# frontend: 前端控制模式 (roles 字段)
# backend: 后端控制模式 (接口返回菜单)
VITE_ACCESS_MODE = frontend
```

### 4.3 动态路由示例

```typescript
// src/router/routes/asyncRoutes.ts
export const asyncRoutes: MenuListType[] = [
  {
    name: "System",
    path: "/system",
    component: "/index/index",
    meta: {
      title: "系统管理",
      icon: "ri:user-3-line",
      keepAlive: false,
    },
    children: [
      {
        path: "user",
        name: "User",
        component: "/system/user",
        meta: {
          title: "用户管理",
          keepAlive: true,
          roles: ["R_SUPER", "R_ADMIN"], // 前端模式下的角色权限
        },
      },
    ],
  },
];
```

### 4.4 菜单 Meta 属性

| 属性         | 类型     | 说明                    |
| ------------ | -------- | ----------------------- |
| `title`      | string   | 路由标题                |
| `icon`       | string   | 路由图标 (Iconify 格式) |
| `keepAlive`  | boolean  | 是否缓存页面            |
| `isHide`     | boolean  | 是否在菜单中隐藏        |
| `isHideTab`  | boolean  | 是否在标签页中隐藏      |
| `roles`      | string[] | 角色权限 (前端模式)     |
| `authList`   | Array    | 操作权限列表            |
| `link`       | string   | 外部链接                |
| `isIframe`   | boolean  | 是否为 iframe 内嵌      |
| `fixedTab`   | boolean  | 是否固定标签页          |
| `isFullPage` | boolean  | 是否全屏页面            |
| `activePath` | string   | 手动指定激活菜单路径    |

### 4.5 新建页面流程

1. 在 `src/views/` 下创建页面组件:

```vue
<template>
  <div class="page-content">
    <h1>新页面</h1>
  </div>
</template>
```

2. 在 `asyncRoutes.ts` 中注册路由:

```typescript
{
  path: "/mypage/index",
  name: "MyPage",
  component: "/mypage/index",
  meta: {
    title: "我的页面",
    keepAlive: true,
  },
}
```

---

## 五、useTable 组合式函数

### 5.1 基础用法

```vue
<template>
  <ArtTable
    :loading="loading"
    :data="data"
    :columns="columns"
    :pagination="pagination"
    @pagination:size-change="handleSizeChange"
    @pagination:current-change="handleCurrentChange"
  />
</template>

<script setup lang="ts">
import { useTable } from "@/hooks/core/useTable";
import { fetchGetUserList } from "@/api/system-manage";

const {
  data,
  loading,
  columns,
  pagination,
  handleSizeChange,
  handleCurrentChange,
} = useTable({
  core: {
    apiFn: fetchGetUserList,
    apiParams: { current: 1, size: 20 },
    columnsFactory: () => [
      { prop: "id", label: "ID" },
      { prop: "name", label: "姓名" },
      { prop: "email", label: "邮箱" },
    ],
  },
});
</script>
```

### 5.2 完整配置示例

```typescript
const {
  data,
  loading,
  error,
  pagination,
  searchParams,
  getData,
  refreshCreate,
  refreshUpdate,
  refreshRemove,
  clearCache,
} = useTable({
  // 核心配置
  core: {
    apiFn: fetchGetUserList,
    apiParams: { current: 1, size: 20, name: "", status: "" },
    immediate: true,
    columnsFactory: () => [
      { prop: "name", label: "姓名", sortable: true },
      { prop: "status", label: "状态", useSlot: true },
    ],
  },
  // 数据转换
  transform: {
    dataTransformer: (records) =>
      records.map((item) => ({
        ...item,
        statusText: item.status === 1 ? "激活" : "禁用",
      })),
  },
  // 性能优化
  performance: {
    enableCache: true,
    cacheTime: 5 * 60 * 1000,
    debounceTime: 300,
  },
  // 生命周期钩子
  hooks: {
    onSuccess: (data) => console.log("加载成功:", data.length),
    onError: (error) => ElMessage.error(error.message),
  },
});
```

### 5.3 核心配置项

| 参数             | 类型     | 默认值 | 说明                   |
| ---------------- | -------- | ------ | ---------------------- |
| `apiFn`          | Function | -      | **必需**，API 请求函数 |
| `apiParams`      | Object   | {}     | 默认请求参数           |
| `immediate`      | Boolean  | true   | 是否立即加载数据       |
| `columnsFactory` | Function | -      | 列配置工厂函数         |

### 5.4 刷新策略

| 方法              | 使用场景 | 说明                   |
| ----------------- | -------- | ---------------------- |
| `refreshData()`   | 手动刷新 | 清空所有缓存，重新获取 |
| `refreshCreate()` | 新增后   | 回到第一页             |
| `refreshUpdate()` | 编辑后   | 保持当前页             |
| `refreshRemove()` | 删除后   | 智能处理页码           |

### 5.5 CRUD 示例

```typescript
// 新增
const handleAdd = async () => {
  await addUser(userData);
  refreshCreate();
};

// 编辑
const handleEdit = async () => {
  await updateUser(userData);
  refreshUpdate();
};

// 删除
const handleDelete = async () => {
  await deleteUser(userId);
  refreshRemove();
};
```

---

## 六、ArtSearchBar 搜索栏组件

### 6.1 基础用法

```vue
<template>
  <ArtSearchBar
    v-model="formData"
    :items="formItems"
    @search="handleSearch"
    @reset="handleReset"
  />
</template>

<script setup>
const formData = ref({ name: "", status: "" });

const formItems = [
  { label: "用户名", key: "name", type: "input", placeholder: "请输入用户名" },
  {
    label: "状态",
    key: "status",
    type: "select",
    props: {
      options: [
        { label: "启用", value: "1" },
        { label: "禁用", value: "0" },
      ],
    },
  },
];
</script>
```

### 6.2 支持的控件类型

| 类型            | 说明           |
| --------------- | -------------- |
| `input`         | 输入框         |
| `number`        | 数字输入框     |
| `select`        | 下拉选择器     |
| `cascader`      | 级联选择器     |
| `treeselect`    | 树选择器       |
| `datetime`      | 日期时间选择器 |
| `timepicker`    | 时间选择器     |
| `switch`        | 开关           |
| `radiogroup`    | 单选框组       |
| `checkboxgroup` | 复选框组       |
| `rate`          | 评分           |
| `slider`        | 滑块           |

### 6.3 Props 配置

| 参数            | 类型          | 默认值  | 说明       |
| --------------- | ------------- | ------- | ---------- |
| `modelValue`    | Object        | {}      | 表单数据   |
| `items`         | Array         | []      | 表单项配置 |
| `span`          | number        | 6       | 栅格数     |
| `gutter`        | number        | 12      | 栅格间隔   |
| `labelPosition` | string        | 'right' | 标签位置   |
| `labelWidth`    | string/number | '70px'  | 标签宽度   |

---

## 七、权限控制

### 7.1 按钮权限 - hasAuth 方法

```vue
<script setup>
import { useAuth } from "@/composables/useAuth";
const { hasAuth } = useAuth();
</script>

<template>
  <ElButton v-if="hasAuth('add')">添加</ElButton>
</template>
```

### 7.2 v-auth 指令

```vue
<ElButton v-auth="'add'">添加</ElButton>
<ElButton v-auth="'edit'">编辑</ElButton>
<ElButton v-auth="'delete'">删除</ElButton>
```

### 7.3 v-roles 指令

```vue
<el-button v-roles="['R_SUPER', 'R_ADMIN']">仅管理员可见</el-button>
<el-button v-roles="'R_ADMIN'">仅 ADMIN 可见</el-button>
```

---

## 八、主题配置

### 8.1 全局配置

配置文件: `src/config/index.ts`

```typescript
const appConfig: SystemConfig = {
  systemInfo: {
    name: "Art Design Pro", // 系统名称
  },
  systemMainColor: [
    "#5D87FF",
    "#B48DF3",
    "#1D84FF",
    "#60C041",
    "#38C0FC",
    "#F9901F",
    "#FF80C8",
  ],
};
```

### 8.2 主题切换

```typescript
import { useTheme } from "@/hooks/core/useTheme";
import { SystemThemeEnum } from "@/enums/appEnum";

const { switchThemeStyles } = useTheme();

switchThemeStyles(SystemThemeEnum.DARK); // 暗色
switchThemeStyles(SystemThemeEnum.LIGHT); // 亮色
switchThemeStyles(SystemThemeEnum.AUTO); // 跟随系统
```

### 8.3 CSS 变量

```css
/* 文字颜色 */
color: var(--art-gray-100);
color: var(--art-gray-900);

/* 主题色 */
color: var(--art-primary);
color: var(--art-success);
color: var(--art-warning);
color: var(--art-error);

/* 背景颜色 */
background-color: var(--default-bg-color);
background-color: var(--default-box-color);

/* 边框 */
border: 1px solid var(--default-border);
```

### 8.4 Tailwind 工具类

```html
<!-- 文字颜色 -->
<div class="text-g-900">深色文字</div>
<div class="text-g-500">中等文字</div>

<!-- 背景颜色 -->
<div class="bg-box">卡片背景</div>

<!-- Flex 快捷类 -->
<div class="flex-c">
  <!-- flex + items-center -->
  <div class="flex-cb">
    <!-- flex + items-center + justify-between -->
    <div class="flex-cc">
      <!-- flex + items-center + justify-center -->

      <!-- 过渡动画 -->
      <div class="tad-200">
        <!-- transition-all duration-200 -->
        <div class="tad-300">
          <!-- transition-all duration-300 -->

          <!-- 边框 -->
          <div class="border-full-d">完整边框</div>
          <div class="border-b-d">底部边框</div>
        </div>
      </div>
    </div>
  </div>
</div>
```

---

## 九、图标使用

### 9.1 ArtSvgIcon 组件

```vue
<template>
  <!-- 基础使用 -->
  <ArtSvgIcon icon="ri:home-line" />

  <!-- 自定义大小和颜色 -->
  <ArtSvgIcon icon="ri:user-line" class="text-2xl text-primary" />
</template>

<script setup>
import ArtSvgIcon from "@/components/core/base/art-svg-icon/index.vue";
</script>
```

### 9.2 图标库

- **推荐**: [Remix Icon](https://remixicon.com/)
- **Iconify**: [https://icon-sets.iconify.design/ri/](https://icon-sets.iconify.design/ri/)

---

## 十、API 接口规范

### 10.1 基础响应格式

```typescript
// src/types/common/response.ts
interface BaseResponse<T = unknown> {
  code: number;
  msg: string;
  data: T;
}
```

### 10.2 菜单接口返回格式

```typescript
{
  code: 200,
  msg: "success",
  data: [
    {
      name: "Dashboard",
      path: "/dashboard",
      component: "/index/index",
      meta: {
        title: "menus.dashboard.title",
        icon: "ri:pie-chart-line"
      },
      children: [...]
    }
  ]
}
```

### 10.3 分页接口配置

配置文件: `src/utils/table/tableConfig.ts`

```typescript
export const tableConfig = {
  recordFields: ["list", "data", "records", "items", "result", "rows"],
  totalFields: ["total", "count"],
  currentFields: ["current", "page", "pageNum"],
  sizeFields: ["size", "pageSize", "limit"],
  paginationKey: {
    current: "current",
    size: "size",
  },
};
```

---

## 十一、环境变量

| 变量                    | 说明                        |
| ----------------------- | --------------------------- |
| `VITE_VERSION`          | 版本号                      |
| `VITE_PORT`             | 端口号 (默认 3006)          |
| `VITE_BASE_URL`         | 网站地址前缀                |
| `VITE_ACCESS_MODE`      | 权限模式 (frontend/backend) |
| `VITE_WITH_CREDENTIALS` | 是否携带 Cookie             |

---

## 十二、常用脚本命令

| 命令                  | 说明                    |
| --------------------- | ----------------------- |
| `pnpm dev`            | 启动开发服务器          |
| `pnpm build`          | 生产构建                |
| `pnpm lint`           | ESLint 检查             |
| `pnpm fix`            | ESLint 自动修复         |
| `pnpm lint:prettier`  | Prettier 格式化         |
| `pnpm lint:stylelint` | Stylelint 检查          |
| `pnpm commit`         | 规范化提交 (Commitizen) |
| `pnpm clean:dev`      | 精简项目 (清理演示数据) |

---

## 十三、常见问题

### 页面切换空白

**原因**: 组件存在多个根元素
**解决**: 确保 template 只有单个根元素

### 菜单点击自动刷新

**原因**: Vite 依赖预构建优化
**解决**: 在 `vite.config.ts` 的 `optimizeDeps.include` 中添加依赖

### 路由配置错误

**调试**: 打开浏览器控制台 (F12) 查看错误信息

---

## 十四、提交规范

```bash
feat     # 新增功能
fix      # 修复缺陷
docs     # 文档变更
style    # 代码格式
refactor # 代码重构
perf     # 性能优化
test     # 测试相关
build    # 构建流程
ci       # CI 配置
revert   # 回滚 commit
chore    # 其他变更
```

提交流程:

```bash
git add .
pnpm commit
git push
```

---
