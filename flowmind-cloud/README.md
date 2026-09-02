# FlowMind Cloud 后端服务

FlowMind 后端服务基于 RuoYi-Cloud 框架，集成 Flowable 工作流引擎。

## 平台简介

**核心模块**：
- **Flowable 工作流**：流程设计、部署、执行和监控
- **认证服务**：用户认证、权限管理（JWT，AI 服务复用同一密钥解析）
- **系统管理**：用户、部门、角色、菜单等管理
- **查询接口**：流程分类、表单、角色、流程模型等查询接口，供 AI 服务（`integrations/backend`）检索真实数据

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
├── bin/run-all.bat             # 一键构建并启动（Gateway→Auth→System→Flowable）
├── ruoyi-gateway/              # 网关服务（9001）
├── ruoyi-auth/                 # 认证服务（9002）
├── ruoyi-modules/              # 业务模块
│   ├── ruoyi-system/           # 系统模块（9003）
│   ├── ruoyi-flowable/         # 工作流模块（9007）
│   ├── ruoyi-gen/              # 代码生成（9004）
│   ├── ruoyi-job/              # 定时任务（9005）
│   └── ruoyi-file/             # 文件服务（9006）
├── ruoyi-common/               # 公共模块
├── ruoyi-visual/               # 可视化/监控模块
└── pom.xml                     # 根构建
```

## 快速启动

前置：Docker 已启动基础环境（MySQL、Redis、Nacos），见仓库根 README 的 `bin/start.bat`。

```bash
cd flowmind-cloud
bin/run-all.bat
```

或进入各模块目录分别执行：

```bash
mvn spring-boot:run -Dspring.profiles.active=dev
```

## 服务端口（本地开发）

| 服务     | 端口 | 说明          |
|----------|------|---------------|
| Gateway  | 9001 | API 网关      |
| Auth     | 9002 | 认证服务      |
| System   | 9003 | 系统模块      |
| Flowable | 9007 | 工作流模块    |
| Gen      | 9004 | 代码生成（可选） |
| Job      | 9005 | 定时任务（可选） |
| File     | 9006 | 文件服务（可选） |

> Nacos / MySQL / Redis 的 Docker 宿主映射端口（18848 / 13306 / 16379）见仓库根 README「服务端口」。

---

**文档更新日期**: 2026-09-02
