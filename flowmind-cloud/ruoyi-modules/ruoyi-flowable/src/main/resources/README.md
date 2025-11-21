# 
# RuoYi-Cloud-Module-Flowable :foggy:  :zap: —若依微服务-flowable工作流模块-一键集成版

---

<div align="center">

[![star](https://gitee.com/bdn007/ruoyi-cloud-module-flowable//badge/star.svg?theme=dark)](https://gitee.com/bdn007/ruoyi-cloud-module-flowable/stargazers)
[![fork](https://gitee.com/bdn007/ruoyi-cloud-module-flowable//badge/fork.svg?theme=dark)](https://gitee.com/bdn007/ruoyi-cloud-module-flowable/members)
[![AUR](https://img.shields.io/badge/license-Apache%20License%202.0-blue.svg)](https://gitee.com/xddcode/free-fs/blob/master/LICENSE)

</div>

### 介绍
若依微服务的一个flowable扩展服务，目的是方便easy的在已有的微服务上集成flowable。
如果你已经在使用若依微服务-vue3版本，并且生态中提供的flowable扩展版本又与你使用的官网微服务版本结构不一样，没办法一键集成，那我这个就是你想要的
<br/>
ps:
<br/>
1.如果你不需要在自己已有的若依微服务项目上扩展，那你不需要自己按以下步骤集成，直接用我根据若依微服务（会定时同步若依最新代码）集成好的即可：[RuoYi-Cloud](https://gitee.com/bdn007/RuoYi-Cloud/tree/master)
<br/>
2.如果你需要另外一个彩蛋版本，就是将若依的代码生成和flowable联动起来的版本，具体可以看这个分支：[RuoYi-Cloud（Gen_master）](https://gitee.com/bdn007/RuoYi-Cloud/tree/Gen_master)

### 友情链接🔗 特别声明

- 本版本是根据[RuoYi-Flowable-Plus](https://gitee.com/KonBAI-Q/ruoyi-flowable-plus) 改造的更加easy集成到若依微服务的版本的服务，感谢作者的开源！

### 源码链接：

- Gitee：[https://gitee.com/bdn007/ruoyi-cloud-module-flowable]


### 技术栈

本项目使用以下技术栈构建：

- **前端**: Vue 3, Element Plus, Vite , js ,ps:如果你前端用的是ruoyi-vue3版本，那直接拷贝使用
- **后端**: 若依微服务，直接把模块复制进modules启动即可


### 安装指南

以下是安装和配置项目的步骤：

1. 先克隆若依/RuoYi-Cloud( **跑起若依微服务平台是前提！！！** ),再克隆此仓库：
   ```bash
   #若依微服务
   git clone https://gitee.com/y_project/RuoYi-Cloud.git
   #若依微服务前端VUE3版本
   git clone https://gitcode.com/yangzongzhuan/RuoYi-Cloud-Vue3.git
   #本仓库-若依微服务-工作流中心
   git clone https://gitee.com/bdn007/ruoyi-cloud-module-flowable.git

2. 将本[ruoyi-flowable](https://gitee.com/bdn007/ruoyi-cloud-module-flowable/tree/master/ruoyi-flowable)直接拷贝进若依微服务的ruoyi-modules目录
    <br/>
   ![拷贝ruoyi-flowable](useless/copyfile.jpg)  
   
3. 在RuoYi-Cloud/ruoyi-modules/pom.xml 里添加 ruoyi-flowable
   ```xml
    <modules>
        <module>ruoyi-system</module>
        <module>ruoyi-gen</module>
        <module>ruoyi-job</module>
        <module>ruoyi-file</module>
        <!--这是新增的模块-->
        <module>ruoyi-flowable</module>
    </modules>
4. 根据若依微服务官网进行nacos配置，然后执行[nacos配置.sql](https://gitee.com/bdn007/ruoyi-cloud-module-flowable/blob/master/sql/nacos%E9%85%8D%E7%BD%AE.sql)配置好工作流模块的配置,最后在网关配置新增以下：
   ```yml
   (1)routes配置
       ...
           # 工作流中心
           - id: ruoyi-flowable
             uri: lb://ruoyi-flowable
             predicates:
           - Path=/flowable/**
             filters:
           - StripPrefix=1
   (2)防止XSS攻击配置
       ...
          xss:
            enabled: true
            excludeUrls:
              - /system/notice
              # 这个是新加的，不然保存流程的时候会被拦截
              - /flowable/model/save
    ```

5. ruoyi-api新增几个接口，自己实现即可，就是简单的查查用户、角色
   <br/>
   ![自己实现几个查询api](useless/remoteapi.jpg)  
   <br/>
   ![简单api](useless/easyapi.jpg)  


6. 执行工作流模块[flowable相关表.sql](https://gitee.com/bdn007/ruoyi-cloud-module-flowable/blob/master/sql/flowable%E7%9B%B8%E5%85%B3%E8%A1%A8.sql)、[工作流中心菜单.sql](https://gitee.com/bdn007/ruoyi-cloud-module-flowable/blob/master/sql/%E5%B7%A5%E4%BD%9C%E6%B5%81%E4%B8%AD%E5%BF%83%E8%8F%9C%E5%8D%95.sql)

7. 在若依微服务的vue3版前端工程install以下几个依赖
   ```bash
   npm install bpmn-js@^8.10.0
   npm install bpmn-js-task-resize@^1.2.0
   npm install bpmn-js-token-simulation@^0.10.0
   npm install codemirror-editor-vue3@^2.8.0
   npm install diagram-js@^15.2.4
   npm install diagram-js-minimap@^5.2.0
   npm install screenfull@^6.0.2
   npm install vue-i18n@^11.0.1
   npm install x2js@^3.4.4
   npm install vform3-builds@^3.0.10


8. 在若依微服务的vue3版前端工程编辑以下代码
    <br/>
    (1)src/main.js:引入表单设计器
     ```js
     ...
     // 表单设计器
     import VForm3 from 'vform3-builds'  //引入VForm 3库
     import 'vform3-builds/dist/designer.style.css'  //引入VForm3样式
     // 全局组件挂载
     ...
     app.use(VForm3)
     ```
    (2)src/router/index.js:新增发起流程、流程详情的动态路由
     ```js
     ...
     // 动态路由，基于用户权限动态去加载
    export const dynamicRoutes = [
    ...
      {
        path: '/workflow/process',
        component: Layout,
        hidden: true,
        permissions: ['workflow:process:query'],
        children: [
          {
            path: 'start/:deployId([\\w|\\-]+)',
            component: () => import('@/views/workflow/work/start.vue'),
            name: 'WorkStart',
            meta: { title: '发起流程', activeMenu: '/workflow/process', icon: '' }
          },
          {
            path: 'detail/:procInsId([\\w|\\-]+)',
            component: () => import('@/views/workflow/work/detail.vue'),
            name: 'WorkDetail',
            meta: { title: '流程详情', activeMenu: '/work/own', icon: '' }
          }
        ]
      }
    ...
    ]
    ```
    (3)vite.config.js:新增预编译配置
    ```js
     // https://vitejs.dev/config/
     export default defineConfig(({ mode, command }) => {
       const env = loadEnv(mode, process.cwd())
       const { VITE_APP_ENV } = env
       return {
            ...
            // 预编译
            optimizeDeps: {
              include: [
                'vue',
                'vue-router',
                'pinia',
                'axios',
                '@vueuse/core',
                'echarts',
                'vue-i18n',
                '@vueup/vue-quill'
              ]
            }
          ...
      }
    ```
9. 拷贝本前端工程[RuoYI-Cloud-Vue3](https://gitee.com/bdn007/ruoyi-cloud-module-flowable/tree/master/RuoYi-Cloud-Vue3)的代码到若依微服务的vue3版前端工程( **注意：备份好自己的代码！！！以免被覆盖** )

10. 新增数据字典
   ```sql
    #字典类型
    insert into sys_dict_type values(500, '流程状态', 'wf_process_status',   '0', 'admin', sysdate(), '', null, '工作流程状态');

    #字典值
    insert into sys_dict_data values(501, 1,  '进行中',   'running',    'wf_process_status',   '',   'primary',  'N', '0', 'admin', sysdate(), '', null, '进行中状态');
    insert into sys_dict_data values(502, 2,  '已终止',   'terminated', 'wf_process_status',   '',   'danger',   'N', '0', 'admin', sysdate(), '', null, '已终止状态');
    insert into sys_dict_data values(503, 3,  '已完成',   'completed',  'wf_process_status',   '',   'success',  'N', '0', 'admin', sysdate(), '', null, '已完成状态');
    insert into sys_dict_data values(504, 4,  '已取消',   'canceled',   'wf_process_status',   '',   'warning',  'N', '0', 'admin', sysdate(), '', null, '已取消状态');
   ```
11. 至此，虽然不是一键，但是其实也没多少工作，启动你的项目即可

### 👀 界面预览

**流程分类：**  
![流程分类](useless/lcfl.png)  

<br/>

**表单配置：**  
![表单管理](useless/bdpz.png)  

<br/>

![表单配置](useless/bdpz2.png)  

<br/>

**流程模型：**  
![流程模型](useless/lcmx.png)  

<br/>

**部署管理：**  
![部署管理](useless/bsgl.png)  

<br/>

**新建流程：**  
![新建流程](useless/xjlc.png)  

<br/>

**我的流程：**  
![我的流程](useless/wdlc.png)  

<br/>

**抄送我的：**  
![抄送我的](useless/cswd.png)
 
<br/>


### 许可证

该项目采用 [ Apache-2.0 许可证](LICENSE) 进行授权 — 详情请参见许可证文件。

### 联系我们

如果你有任何问题或建议，请联系：

- 姓名: 冰山闪电
- 邮箱: 44787467616@qq.com
- gitee: [BDN007](https://gitee.com/bdn007)
- 微信:

 ![微信](/useless/wechat.jpg)

## ❤ 捐赠支持
如果你认为RuoYi-Cloud-Module-Flowable项目可以为你提供帮助，或者给你带来方便和灵感，或者你认同这个项目，可以给[RuoYi-Flowable-Plus](https://gitee.com/KonBAI-Q/ruoyi-flowable-plus)的作者赞助一下，又或者给我赞助一下，以下是请我喝咖啡的收款码！
<br/>
![coffeeMoney](/useless/coffeeMoney.jpg)







