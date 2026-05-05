# FlowMind Cloud 后端服务

FlowMind 后端服务基于 RuoYi-Cloud 框架，集成 Flowable 工作流引擎。

## 平台简介

**核心模块**：
- **Flowable 工作流**：流程设计、部署、执行和监控
- **认证服务**：用户认证、权限管理
- **系统管理**：用户、部门、角色、菜单等管理
- **AI 接口**：与 AI 服务通信的 API 模块

## 技术栈

| 技术 | 说明 |
|------|------|
| Spring Boot 3.x | 基础框架 |
| Spring Cloud 2023.x | 微服务框架 |
| Flowable 6.x | 工作流引擎 |
| Nacos | 注册中心 & 配置中心 |
| MySQL 8.0+ | 关系数据库 |
| Redis | 缓存服务 |

## 目录结构

```
flowmind-cloud/
├── docker/                      # Docker 配置
├── ruoyi-gateway/              # 网关服务
├── ruoyi-auth/                 # 认证服务
├── ruoyi-modules/              # 业务模块
│   ├── ruoyi-system/           # 系统模块
│   ├── ruoyi-flowable/         # 工作流模块
│   └── ...
├── ruoyi-common/               # 公共模块
└── flowmind-ai-api/            # AI 服务 API
```

## 快速启动

详细说明：[启动指南.md](../启动指南.md)

---

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Nacos | 8848 | 注册中心 & 配置中心 |
| MySQL | 3306 | 数据库 |
| Redis | 6379 | 缓存 |
| Gateway | 8080 | API 网关 |
| Auth | 9200 | 认证服务 |
| System | 9201 | 系统模块 |
| Flowable | 9204 | 工作流模块 |

---

**文档更新日期**: 2026-05-04
