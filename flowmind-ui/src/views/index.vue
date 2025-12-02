<template>
  <div class="app-container home">
    <el-row :gutter="20">
      <el-col :sm="24" :lg="12" style="padding-left: 20px">
        <h2>FlowMind 企业级应用平台</h2>
        <p>
          FlowMind是一款基于Spring Cloud微服务架构的企业级应用平台，提供了完整的前后端解决方案。系统采用Vue3+Element Plus构建现代化前端界面，后端基于Spring Boot和Spring
          Cloud生态，为企业提供高效、稳定、可扩展的应用开发框架。
        </p>
        <p>
          <b>当前版本:</b> <span>v{{ version }}</span>
        </p>
        <p>
          <el-tag type="success">企业级应用平台</el-tag>
        </p>
        <p>
          <el-button type="primary" icon="Cloudy" plain
            @click="goTarget('https://gitee.com/y_project/RuoYi-Cloud.git')">访问码云</el-button>
          <el-button icon="HomeFilled" plain @click="goTarget('https://gitee.com/wish168/flowmind')">访问官网</el-button>
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
              <li>Spring Boot</li>
              <li>Spring Cloud</li>
              <li>Nacos</li>
              <li>Sentinel</li>
              <li>Seata</li>
              <li>MyBatis Plus</li>
              <li>...</li>
            </ul>
          </el-col>
          <el-col :span="6">
            <h4>前端技术</h4>
            <ul>
              <li>Vue 3</li>
              <li>Element Plus</li>
              <li>Vue Router</li>
              <li>Pinia</li>
              <li>Axios</li>
              <li>Tailwind CSS</li>
              <li>...</li>
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
              <span>关于我们</span>
            </div>
          </template>
          <div class="body">
            <p>
              <i class="el-icon-s-promotion"></i> 更多内容：<el-link href="https://codebyggbond.dpdns.org/series/myprojects/FlowMind/"
                target="_blank">https://codebyggbond.dpdns.org</el-link>
            </p>
            <p>
              <i class="el-icon-chat-dot-round"></i> 邮箱： <a
                href="mailto:contact@flowmind.example.com">hjf0893@163.com</a>
            </p>
            <p>
              <i class="el-icon-phone"></i> 电话： <a href="tel:400-123-4567">XXXXXXXXX</a>
            </p>
            <p>
              <i class="el-icon-location"></i> 地址： XXXXXXXXXX
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
            <el-collapse-item title="v1.0.0 - 2025-06-30">
              <ol>
                <li>新增FlowMind 企业级应用平台正式版</li>
                <li>基于Flowable引擎的工作流设计器</li>
                <li>支持BPMN 2.0标准流程建模</li>
                <li>可视化流程设计界面</li>
                <li>流程实例监控与管理</li>
                <li>任务分配与处理功能</li>
                <li>表单设计与自定义</li>
                <li>用户权限管理系统</li>
                <li>组织架构管理</li>
                <li>系统集成接口</li>
              </ol>
            </el-collapse-item>
            <el-collapse-item title="v0.9.0 - 2025-03-15">
              <ol>
                <li>新增流程设计器Beta版</li>
                <li>支持基本流程元素绘制</li>
                <li>基础表单设计器</li>
                <li>表单组件库</li>
                <li>流程模拟运行</li>
                <li>UI界面优化</li>
              </ol>
            </el-collapse-item>
            <el-collapse-item title="v0.5.0 - 2024-12-01">
              <ol>
                <li>项目初始化</li>
                <li>基础架构搭建</li>
                <li>核心模块设计</li>
                <li>数据库设计</li>
                <li>用户管理模块</li>
                <li>权限控制模块</li>
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
              <li>基于Flowable引擎的工作流设计器</li>
              <li>可视化表单设计器</li>
              <li>完整的权限管理系统</li>
              <li>组织架构管理</li>
              <li>流程实例监控与管理</li>
              <li>任务分配与处理</li>
              <li>系统集成接口</li>
              <li>移动端适配</li>
            </ul>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="Index">
const version = ref('1.0.0')

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