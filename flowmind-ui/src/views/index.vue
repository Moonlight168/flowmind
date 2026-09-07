<template>
  <div class="app-container home">
    <el-row :gutter="20">
      <el-col :sm="24" :lg="12" style="padding-left: 20px">
        <h2>FlowMind 智能流程审批平台</h2>
        <p>
          FlowMind 是一款基于微服务架构的智能流程审批系统，集成 AI 能力实现智能意图识别、流程自动生成和审批意见智能推荐。系统采用 Flowable 工作流引擎，结合 React 模式 Agent 架构，为企业提供高效、稳定、可扩展的审批解决方案。
        </p>
        <p>
          <b>当前版本:</b> <span>v{{ version }}</span>
        </p>
        <p>
          <el-tag type="success">智能审批平台</el-tag>
          <el-tag type="warning" class="ml-2">AI 驱动</el-tag>
          <el-tag type="info" class="ml-2">流式对话（SSE）</el-tag>
        </p>
        <p>
          <el-button type="primary" icon="Cloudy" plain
            @click="goTarget('https://github.com/Moonlight168/flowmind')">访问 GitHub</el-button>
          <el-button icon="HomeFilled" plain @click="goTarget('https://gitee.com/wish168/flowmind')">访问码云</el-button>
        </p>
      </el-col>

      <el-col :sm="24" :lg="12" style="padding-left: 50px">
        <el-row>
          <el-col :span="12">
            <h2>技术栈</h2>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="6">
            <h4>后端技术</h4>
            <ul>
              <li>Spring Boot 3.x</li>
              <li>Spring Cloud</li>
              <li>Flowable</li>
              <li>Nacos</li>
              <li>Redis</li>
              <li>MySQL</li>
              <li>LangChain/LangGraph</li>
            </ul>
          </el-col>
          <el-col :span="6">
            <h4>前端技术</h4>
            <ul>
              <li>Vue 3</li>
              <li>TypeScript</li>
              <li>Element Plus</li>
              <li>Pinia</li>
              <li>Axios</li>
              <li>Tailwind CSS</li>
              <li>BPMN-JS</li>
            </ul>
          </el-col>
        </el-row>
      </el-col>
    </el-row>
    <el-divider />
    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card class="update-log">
          <template v-slot:header>
            <div class="clearfix">
              <span>系统架构</span>
            </div>
          </template>
          <div class="body">
            <ul>
              <li><strong>flowmind-ui</strong> - Vue3 前端，端口 88（dev）/ 80（prod）</li>
              <li><strong>flowmind-cloud</strong> - Spring Cloud 微服务（Gateway 9001 / Auth 9002 / System 9003 / Flowable 9007）</li>
              <li><strong>flowmind-ai-flow</strong> - AI 服务（FastAPI + LangGraph），端口 8000</li>
            </ul>
            <p class="mt-4">
              <i class="el-icon-s-promotion"></i> 项目地址：<el-link href="https://gitee.com/wish168/flowmind"
                target="_blank">gitee.com/wish168/flowmind</el-link>
            </p>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card class="update-log">
          <template v-slot:header>
            <div class="clearfix">
              <span>更新日志</span>
            </div>
          </template>
          <el-collapse accordion>
            <el-collapse-item title="v3.6.6 - 2026-09">
              <ol>
                <li>AI 悬浮窗组件统一（AiFloatingWindow），助手/设计多场景复用与拖拽缩放</li>
                <li>AI 消息流式输出（SSE）与同步生成器桥接，聊天历史按用户隔离</li>
                <li>接入 Langfuse 全链路监控与黄金数据集评测</li>
                <li>提示词版本管理与灰度发布（Markdown 化管理）</li>
                <li>统一模型降级，支持多供应商/多模型自动切换</li>
                <li>增量 AI 设计校验、BPMN 基线反解析与会话/版本历史隔离</li>
                <li>AI 服务安全加固：JWT 校验、启动脚本一键启停全套服务</li>
              </ol>
            </el-collapse-item>
            <el-collapse-item title="v2.1.0 - 2026-06">
              <ol>
                <li>React 模式 Agent 架构，支持智能追问</li>
                <li>BPMN 设计与验证工具链</li>
                <li>适配器层简化优化</li>
              </ol>
            </el-collapse-item>
            <el-collapse-item title="v2.0.0 - 2026-05">
              <ol>
                <li>AI 设计功能：智能生成分类、流程、表单</li>
                <li>多轮对话持续优化设计</li>
                <li>多模型支持：Qwen、vLLM、Doubao</li>
              </ol>
            </el-collapse-item>
            <el-collapse-item title="v1.0.0 - 2025-12">
              <ol>
                <li>OA 工作台全新改版</li>
                <li>待办/已办/待签等功能完善</li>
                <li>集成 Flowable 引擎</li>
                <li>实现草稿箱功能</li>
                <li>基础审批流程</li>
              </ol>
            </el-collapse-item>
          </el-collapse>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="24" :md="12" :lg="8">
        <el-card class="update-log">
          <template v-slot:header>
            <div class="clearfix">
              <span>功能特性</span>
            </div>
          </template>
          <div class="body">
            <ul>
              <li>悬浮式 AI 助手：随时随地唤起，多窗口复用</li>
              <li>AI 流式对话（SSE）：逐字输出、可中断</li>
              <li>AI 多轮追问：主动询问细节完善设计</li>
              <li>AI 设计分类：自然语言描述自动生成流程分类</li>
              <li>AI 设计流程：自动生成 BPMN 流程结构</li>
              <li>AI 设计表单：自动生成 v-form-designer 表单</li>
              <li>多模型支持：Qwen / DeepSeek / vLLM，自动降级切换</li>
              <li>BPMN-JS 可视化流程设计器</li>
              <li>可视化表单设计器与完整权限管理</li>
            </ul>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="Index">
const version = ref('3.6.6')

function goTarget(url) {
  window.open(url, '__blank')
}
</script>

<style scoped lang="scss">
.home {
  blockquote {
    padding: 10px 20px;
    margin: 0 0 20px;
    font-size: 17.5px;
    border-left: 5px solid #eee;
  }

  hr {
    margin-top: 20px;
    margin-bottom: 20px;
    border: 0;
    border-top: 1px solid #eee;
  }

  .col-item {
    margin-bottom: 20px;
  }

  ul {
    padding: 0;
    margin: 0;
  }

  font-family: "open sans",
  "Helvetica Neue",
  Helvetica,
  Arial,
  sans-serif;
  font-size: 13px;
  color: #676a6c;
  overflow-x: hidden;

  ul {
    list-style-type: none;
  }

  h4 {
    margin-top: 0px;
  }

  h2 {
    margin-top: 10px;
    font-size: 26px;
    font-weight: 100;
  }

  p {
    margin-top: 10px;

    b {
      font-weight: 700;
    }
  }

  .update-log {
    ol {
      display: block;
      list-style-type: decimal;
      margin-block-start: 1em;
      margin-block-end: 1em;
      margin-inline-start: 0;
      margin-inline-end: 0;
      padding-inline-start: 40px;
    }
  }
}
</style>