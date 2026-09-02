<p align="center">
	<img alt="logo" src="https://oscimg.oschina.net/oscnet/up-b99b286755aef70355a7084753f89cdb7c9.png">
</p>
<h1 align="center" style="margin: 30px 0 30px; font-weight: bold;">FlowMind UI v2.0.0</h1>
<h4 align="center">基于 RuoYi-Vue3（Vue 3 + Element Plus）前端的工作流管理系统</h4>
<p align="center">
	<a href="https://gitee.com/wish168/flowmind"><img src="https://img.shields.io/badge/FlowMind-v2.0.0-brightgreen.svg"></a>
	<a href="https://github.com/Moonlight168/flowmind-ui/blob/master/LICENSE"><img src="https://img.shields.io/github/license/mashape/apistatus.svg"></a>
</p>

## 平台简介

本项目基于 [RuoYi-Vue](https://gitee.com/y_project/RuoYi-Vue) 前端框架进行扩展开发，集成 AI 智能流程设计功能。

**核心功能**：

- **全局 AI 助手**：悬浮式 AI 交互，支持对话历史管理
- **AI 智能设计**：分类、流程、表单的 AI 生成
- **审批中心**：待办、已办、待签、我的流程
- **草稿箱**：流程草稿的保存与管理

---

## 快速开始

### 环境要求

| 软件    | 版本          |
| ------- | ------------- |
| Node.js | 18+（Vite 6） |

### 安装运行

```bash
# 克隆项目
git clone https://github.com/Moonlight168/flowmind.git

# 进入项目目录
cd flowmind/flowmind-ui

# 安装依赖
npm install

# 启动服务
npm run dev

# 构建测试环境
npm run build:stage

# 构建生产环境
npm run build:prod
```

### 访问地址

| 环境     | 地址                          |
| -------- | ----------------------------- |
| 开发环境 | http://localhost:88           |
| 生产环境 | http://localhost（Nginx 80）  |

---

## 功能页面

### 工作台与审批

<table>
    <tr>
        <td><img src="./src/assets/images/README/工作台.png" alt="工作台" width="100%"/><br/><div style="text-align: center;">工作台</div></td>
        <td><img src="./src/assets/images/README/流程发起.png" alt="流程发起" width="100%"/><br/><div style="text-align: center;">流程发起</div></td>
    </tr>
    <tr>
        <td><img src="./src/assets/images/README/审批中心待办事项.png" alt="审批中心待办事项" width="100%"/><br/><div style="text-align: center;">审批中心待办事项</div></td>
        <td><img src="./src/assets/images/README/我的流程.png" alt="我的流程" width="100%"/><br/><div style="text-align: center;">我的流程</div></td>
    </tr>
    <tr>
        <td><img src="./src/assets/images/README/草稿箱.png" alt="草稿箱" width="100%"/><br/><div style="text-align: center;">草稿箱</div></td>
        <td><img src="./src/assets/images/README/个人信息.png" alt="个人信息" width="100%"/><br/><div style="text-align: center;">个人信息</div></td>
    </tr>
</table>

### AI 功能

<table>
    <tr>
        <td><img src="./src/assets/images/README/全局ai助手.png" alt="全局AI助手" width="100%"/><br/><div style="text-align: center;">全局 AI 助手</div></td>
        <td><img src="./src/assets/images/README/对话历史管理.png" alt="对话历史管理" width="100%"/><br/><div style="text-align: center;">对话历史管理</div></td>
    </tr>
    <tr>
        <td><img src="./src/assets/images/README/表单设计新增ai设计按钮.png" alt="表单设计AI按钮" width="100%"/><br/><div style="text-align: center;">表单设计 AI 按钮</div></td>
        <td><img src="./src/assets/images/README/流程设计新增ai设计按钮.png" alt="流程设计AI按钮" width="100%"/><br/><div style="text-align: center;">流程设计 AI 按钮</div></td>
    </tr>
</table>

### 流程管理

<table>
    <tr>
        <td><img src="./src/assets/images/README/流程分类.png" alt="流程分类" width="100%"/><br/><div style="text-align: center;">流程分类</div></td>
        <td><img src="./src/assets/images/README/流程部署.png" alt="流程部署" width="100%"/><br/><div style="text-align: center;">流程部署</div></td>
    </tr>
    <tr>
        <td><img src="./src/assets/images/README/流程设计.png" alt="流程设计" width="100%"/><br/><div style="text-align: center;">流程设计</div></td>
        <td><img src="./src/assets/images/README/表单编辑.png" alt="表单编辑" width="100%"/><br/><div style="text-align: center;">表单编辑</div></td>
    </tr>
</table>

### 系统管理

<table>
    <tr>
        <td><img src="https://oscimg.oschina.net/oscnet/cd1f90be5f2684f4560c9519c0f2a232ee8.jpg" alt="系统管理" width="100%"/><br/><div style="text-align: center;">系统管理</div></td>
        <td><img src="https://oscimg.oschina.net/oscnet/1cbcf0e6f257c7d3a063c0e3f2ff989e4b3.jpg" alt="用户管理" width="100%"/><br/><div style="text-align: center;">用户管理</div></td>
    </tr>
    <tr>
        <td><img src="https://oscimg.oschina.net/oscnet/up-8074972883b5ba0622e13246738ebba237a.png" alt="角色管理" width="100%"/><br/><div style="text-align: center;">角色管理</div></td>
        <td><img src="https://oscimg.oschina.net/oscnet/up-9f88719cdfca9af2e58b352a20e23d43b12.png" alt="菜单管理" width="100%"/><br/><div style="text-align: center;">菜单管理</div></td>
    </tr>
    <tr>
        <td><img src="https://oscimg.oschina.net/oscnet/up-39bf2584ec3a529b0d5a3b70d15c9b37646.png" alt="部门管理" width="100%"/><br/><div style="text-align: center;">部门管理</div></td>
        <td><img src="https://oscimg.oschina.net/oscnet/up-4148b24f58660a9dc347761e4cf6162f28f.png" alt="岗位管理" width="100%"/><br/><div style="text-align: center;">岗位管理</div></td>
    </tr>
    <tr>
        <td><img src="https://oscimg.oschina.net/oscnet/up-b2d62ceb95d2dd9b3fbe157bb70d26001e9.png" alt="字典管理" width="100%"/><br/><div style="text-align: center;">字典管理</div></td>
        <td><img src="https://oscimg.oschina.net/oscnet/up-d67451d308b7a79ad6819723396f7c3d77a.png" alt="参数设置" width="100%"/><br/><div style="text-align: center;">参数设置</div></td>
    </tr>
    <tr>
        <td><img src="https://oscimg.oschina.net/oscnet/5e8c387724954459291aafd5eb52b456f53.jpg" alt="通知公告" width="100%"/><br/><div style="text-align: center;">通知公告</div></td>
        <td><img src="https://oscimg.oschina.net/oscnet/644e78da53c2e92a95dfda4f76e6d117c4b.jpg" alt="日志管理" width="100%"/><br/><div style="text-align: center;">日志管理</div></td>
    </tr>
</table>

---

## 技术栈

| 技术               | 说明        |
| ------------------ | ----------- |
| Vue 3.5+           | 渐进式框架  |
| Element Plus 2.10+ | UI 组件库   |
| Vite 6.x           | 构建工具    |
| Pinia              | 状态管理    |
| Vue Router 4.x     | 路由管理    |
| Axios              | HTTP 客户端 |
| BPMN-JS            | 流程设计器  |
| v-form-designer    | 表单设计器  |

---

## 项目结构

```
flowmind-ui/
├── src/
│   ├── api/                 # API 接口
│   ├── assets/              # 资源文件
│   ├── components/          # 通用组件
│   ├── layout/              # 布局组件
│   ├── router/              # 路由配置
│   ├── store/               # 状态管理
│   ├── utils/               # 工具函数
│   ├── views/               # 页面组件
│   ├── App.vue              # 根组件
│   └── main.js              # 入口文件
├── vite.config.js           # Vite 配置
└── package.json             # 依赖配置
```

---

## 开发指南

### 环境变量

```bash
# .env.development
VITE_APP_TITLE=FlowMind后台管理系统
VITE_APP_BASE_API=/dev-api   # vite.config.js 将 /dev-api 代理到 http://localhost:9001（网关）

# .env.production
VITE_APP_BASE_API=/prod-api  # 生产由 Nginx 反向代理到网关
```

### 添加新页面

1. 在 `src/views/` 目录下创建页面组件
2. 在 `src/router/` 目录下配置路由
3. 在 `src/api/` 目录下创建 API 接口

---

## 浏览器支持

| 浏览器  | 版本   |
| ------- | ------ |
| Chrome  | 最新版 |
| Firefox | 最新版 |
| Safari  | 最新版 |
| Edge    | 最新版 |

---

**文档更新日期**: 2026-09-02
