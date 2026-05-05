-- 清空 Nacos 配置
USE `flowmind-config`;
DELETE FROM config_info;

-- ==================== 开发环境配置 ====================

-- 通用配置
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(1, 'application-dev.yml', 'DEFAULT_GROUP', 'spring:\n  autoconfigure:\n    exclude: com.alibaba.druid.spring.boot.autoconfigure.DruidDataSourceAutoConfigure\nfeign:\n  sentinel:\n    enabled: true\n  okhttp:\n    enabled: true\n  httpclient:\n    enabled: false\n  client:\n    config:\n      default:\n        connectTimeout: 10000\n        readTimeout: 10000\n  compression:\n    request:\n      enabled: true\n      min-request-size: 8192\n    response:\n      enabled: true\nmanagement:\n  endpoints:\n    web:\n      exposure:\n        include: "*"', '9928f41dfb10386ad38b3254af5692e0', '2020-05-20 12:00:00', '2024-08-29 12:14:45', 'nacos', '0:0:0:0:0:0:0:1', '', '', '通用配置', 'null', 'null', 'yaml', '', '');

-- 网关配置
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(2, 'flowmind-gateway-dev.yml', 'DEFAULT_GROUP', 'spring:
  data:
    redis:
      host: localhost
      port: 16379
      password:
  cloud:
    gateway:
      discovery:
        locator:
          lowerCaseServiceId: true
          enabled: true
      routes:
        - id: flowmind-auth
          uri: lb://flowmind-auth
          predicates:
            - Path=/auth/**
          filters:
            - name: CacheRequestBody
              args:
                bodyClass: java.lang.String
            - ValidateCodeFilter
            - StripPrefix=1
        - id: flowmind-gen
          uri: lb://flowmind-gen
          predicates:
            - Path=/code/**
          filters:
            - StripPrefix=1
        - id: flowmind-job
          uri: lb://flowmind-job
          predicates:
            - Path=/schedule/**
          filters:
            - StripPrefix=1
        - id: flowmind-system
          uri: lb://flowmind-system
          predicates:
            - Path=/system/**
          filters:
            - StripPrefix=1
        - id: flowmind-file
          uri: lb://flowmind-file
          predicates:
            - Path=/file/**
          filters:
            - StripPrefix=1
        - id: flowmind-ai-flow
          uri: lb://flowmind-ai-flow
          predicates:
            - Path=/flowmind-ai/**
          filters:
            - StripPrefix=1
        - id: flowmind-flowable
          uri: lb://flowmind-flowable
          predicates:
            - Path=/flowable/**
          filters:
            - StripPrefix=1
security:
  captcha:
    enabled: true
    type: math
  xss:
    enabled: true
    excludeUrls:
      - /system/notice
  ignore:
    whites:
      - /auth/logout
      - /auth/login
      - /auth/register
springdoc:
  webjars:
    prefix:', '', NOW(), NOW(), 'system', '127.0.0.1', 'flowmind-gateway', '', 'FlowMind AI 网关路由配置 - 开发环境', 'null', 'null', 'yaml', 'null', '');

-- 工作流模块
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(3, 'flowmind-flowable-dev.yml', 'DEFAULT_GROUP', 'spring:\n  data:\n    redis:\n      host: localhost\n      port: 16379\n      password:\n  datasource:\n    druid:\n      stat-view-servlet:\n        enabled: true\n        loginUsername: ruoyi\n        loginPassword: 123456\n    dynamic:\n      primary: master\n      druid:\n        initial-size: 5\n        min-idle: 5\n        maxActive: 20\n        maxWait: 60000\n        connectTimeout: 30000\n        socketTimeout: 60000\n        timeBetweenEvictionRunsMillis: 60000\n        minEvictableIdleTimeMillis: 300000\n        validationQuery: SELECT 1 FROM DUAL\n        testWhileIdle: true\n        testOnBorrow: false\n        testOnReturn: false\n        poolPreparedStatements: true\n        maxPoolPreparedStatementPerConnectionSize: 20\n        filters: stat,slf4j\n        connectionProperties: druid.stat.mergeSql\\=true;druid.stat.slowSqlMillis\\=5000\n      datasource:\n        master:\n          driver-class-name: com.mysql.cj.jdbc.Driver\n          url: jdbc:mysql://localhost:13306/flowmind-cloud?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&serverTimezone=GMT%2B8&nullCatalogMeansCurrent=true\n          username: root\n          password: 123456\nmybatis-plus:\n  ddl:\n    enabled: false\n  type-aliases-package: com.ruoyi.flowable.**.domain\n  mapper-locations: classpath:mapper/**/*.xml\n  configuration:\n    map-underscore-to-camel-case: true\n    cache-enabled: false\n    autoMappingBehavior: PARTIAL\n    autoMappingUnknownColumnBehavior: NONE\n    logImpl: org.apache.ibatis.logging.slf4j.Slf4jImpl\nflowable:\n  database-schema-update: true\n  database-type: mysql', '848b666e18a30cd8cdd4ba232844b92d', '2025-01-16 01:54:58', '2025-01-16 01:54:58', null, '127.0.0.1', '', '', '工作流模块', 'null', 'null', 'yaml', 'null', '');

-- 认证中心
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(4, 'flowmind-auth-dev.yml', 'DEFAULT_GROUP', 'spring:\n  data:\n    redis:\n      host: localhost\n      port: 16379\n      password:', '72565b1a725e013154ee57c8fd3045c4', '2020-11-20 00:00:00', '2024-09-14 04:49:42', 'nacos', '0:0:0:0:0:0:0:1', '', '', '认证中心', 'null', 'null', 'yaml', '', '');

-- 系统模块
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(5, 'flowmind-system-dev.yml', 'DEFAULT_GROUP', 'spring:\n  data:\n    redis:\n      host: localhost\n      port: 16379\n      password:\n  datasource:\n    druid:\n      stat-view-servlet:\n        enabled: true\n        loginUsername: ruoyi\n        loginPassword: 123456\n    dynamic:\n      primary: master\n      druid:\n        initial-size: 5\n        min-idle: 5\n        maxActive: 20\n        maxWait: 60000\n        connectTimeout: 30000\n        socketTimeout: 60000\n        timeBetweenEvictionRunsMillis: 60000\n        minEvictableIdleTimeMillis: 300000\n        validationQuery: SELECT 1 FROM DUAL\n        testWhileIdle: true\n        testOnBorrow: false\n        testOnReturn: false\n        poolPreparedStatements: true\n        maxPoolPreparedStatementPerConnectionSize: 20\n        filters: stat,slf4j\n        connectionProperties: druid.stat.mergeSql\\=true;druid.stat.slowSqlMillis\\=5000\n      datasource:\n        master:\n          driver-class-name: com.mysql.cj.jdbc.Driver\n          url: jdbc:mysql://localhost:13306/flowmind-cloud?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&serverTimezone=GMT%2B8&nullCatalogMeansCurrent=true\n          username: root\n          password: 123456\nmybatis:\n  typeAliasesPackage: com.ruoyi.system\n  mapperLocations: classpath:mapper/**/*.xml', 'a79ae256018abb7f3bbaba923baeb6af', '2020-11-20 00:00:00', '2024-09-14 04:49:54', 'nacos', '0:0:0:0:0:0:0:1', '', '', '系统模块', 'null', 'null', 'yaml', '', '');

-- 代码生成b
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(6, 'flowmind-gen-dev.yml', 'DEFAULT_GROUP', 'spring:\n  data:\n    redis:\n      host: localhost\n      port: 16379\n      password:\n  datasource:\n    driver-class-name: com.mysql.cj.jdbc.Driver\n    url: jdbc:mysql://localhost:13306/flowmind-cloud?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&serverTimezone=GMT%2B8&nullCatalogMeansCurrent=true\n    username: root\n    password: 123456\nmybatis:\n  typeAliasesPackage: com.ruoyi.gen.domain\n  mapperLocations: classpath:mapper/**/*.xml\ngen:\n  author: FlowMind\n  packageName: com.ruoyi.system\n  autoRemovePre: false\n  tablePrefix: sys_\n  allowOverwrite: false', '669b20230daf5b2eddda1c87a1e755d7', '2020-11-20 00:00:00', '2024-12-25 08:39:25', 'nacos', '0:0:0:0:0:0:0:1', '', '', '代码生成', 'null', 'null', 'yaml', '', '');

-- 定时任务
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(7, 'flowmind-job-dev.yml', 'DEFAULT_GROUP', 'spring:\n  data:\n    redis:\n      host: localhost\n      port: 16379\n      password:\n  datasource:\n    driver-class-name: com.mysql.cj.jdbc.Driver\n    url: jdbc:mysql://localhost:13306/flowmind-cloud?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&serverTimezone=GMT%2B8&nullCatalogMeansCurrent=true\n    username: root\n    password: 123456\nmybatis:\n  typeAliasesPackage: com.ruoyi.job.domain\n  mapperLocations: classpath:mapper/**/*.xml', '225445e638148dbcbadda8d9774ce3fd', '2020-11-20 00:00:00', '2024-09-14 04:50:12', 'nacos', '0:0:0:0:0:0:0:1', '', '', '定时任务', 'null', 'null', 'yaml', '', '');

-- 文件服务
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(8, 'flowmind-file-dev.yml', 'DEFAULT_GROUP', 'file:\n  domain: http://127.0.0.1:9300\n  path: D:/ruoyi/uploadPath\n  prefix: /statics\nfdfs:\n  domain: http://127.0.0.1\n  soTimeout: 3000\n  connectTimeout: 2002\n  trackerList: 127.0.0.1:22122\nminio:\n  url: http://127.0.0.1:9000\n  accessKey: minioadmin\n  secretKey: minioadmin\n  bucketName: test\nreferer:\n  enabled: false\n  allowed-domains: localhost,127.0.0.1,ruoyi.vip,www.ruoyi.vip', '095791a04211d6e3d294359b21357394', '2020-11-20 00:00:00', '2025-09-02 05:10:11', 'nacos', '0:0:0:0:0:0:0:1', '', '', '文件服务', 'null', 'null', 'yaml', '', '');

-- 监控中心
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(9, 'flowmind-monitor-dev.yml', 'DEFAULT_GROUP', 'spring:\n  security:\n    user:\n      name: ruoyi\n      password: 123456\n  boot:\n    admin:\n      ui:\n        title: FlowMind 服务状态监控
      discovery:
        ignored-services:
          - flowmind-ai-flow', '6f122fd2bfb8d45f858e7d6529a9cd44', '2020-11-20 00:00:00', '2024-08-29 12:15:11', 'nacos', '0:0:0:0:0:0:0:1', '', '', '监控中心', 'null', 'null', 'yaml', '', '');

-- ==================== 生产环境配置 ====================

-- 通用配置
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(101, 'application-prod.yml', 'DEFAULT_GROUP', 'spring:\n  autoconfigure:\n    exclude: com.alibaba.druid.spring.boot.autoconfigure.DruidDataSourceAutoConfigure\nfeign:\n  sentinel:\n    enabled: true\n  okhttp:\n    enabled: true\n  httpclient:\n    enabled: false\n  client:\n    config:\n      default:\n        connectTimeout: 10000\n        readTimeout: 10000\n  compression:\n    request:\n      enabled: true\n      min-request-size: 8192\n    response:\n      enabled: true\nmanagement:\n  endpoints:\n    web:\n      exposure:\n        include: "*"', 'c1d2e3f4a5b6789012345678901234cd', NOW(), NOW(), null, '127.0.0.1', '', '', '共享配置', 'null', 'null', 'yaml', 'null', '');

-- 网关配置
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(102, 'flowmind-gateway-prod.yml', 'DEFAULT_GROUP', 'spring:
  data:
    redis:
      host: flowmind-redis
      port: 6379
      password:
  cloud:
    gateway:
      discovery:
        locator:
          lowerCaseServiceId: true
          enabled: true
      routes:
        - id: flowmind-auth
          uri: lb://flowmind-auth
          predicates:
            - Path=/auth/**
          filters:
            - name: CacheRequestBody
              args:
                bodyClass: java.lang.String
            - ValidateCodeFilter
            - StripPrefix=1
        - id: flowmind-gen
          uri: lb://flowmind-gen
          predicates:
            - Path=/code/**
          filters:
            - StripPrefix=1
        - id: flowmind-job
          uri: lb://flowmind-job
          predicates:
            - Path=/schedule/**
          filters:
            - StripPrefix=1
        - id: flowmind-system
          uri: lb://flowmind-system
          predicates:
            - Path=/system/**
          filters:
            - StripPrefix=1
        - id: flowmind-file
          uri: lb://flowmind-file
          predicates:
            - Path=/file/**
          filters:
            - StripPrefix=1
        - id: flowmind-ai-flow
          uri: lb://flowmind-ai-flow
          predicates:
            - Path=/flowmind-ai/**
          filters:
            - StripPrefix=1
        - id: flowmind-flowable
          uri: lb://flowmind-flowable
          predicates:
            - Path=/flowable/**
          filters:
            - StripPrefix=1
security:
  captcha:
    enabled: true
    type: math
  xss:
    enabled: true
    excludeUrls:
      - /system/notice
  ignore:
    whites:
      - /auth/logout
      - /auth/login
      - /auth/register
springdoc:
  webjars:
    prefix:', 'b2c3d4e5f6789012345678901234abcd', NOW(), NOW(), 'system', '127.0.0.1', 'flowmind-gateway', '', 'FlowMind AI 网关路由配置 - 生产环境', 'null', 'null', 'yaml', 'null', '');

-- 工作流模块
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(103, 'flowmind-flowable-prod.yml', 'DEFAULT_GROUP', 'spring:\n  data:\n    redis:\n      host: flowmind-redis\n      port: 6379\n      password:\n  datasource:\n    druid:\n      stat-view-servlet:\n        enabled: true\n        loginUsername: ruoyi\n        loginPassword: 123456\n    dynamic:\n      primary: master\n      druid:\n        initial-size: 5\n        min-idle: 5\n        maxActive: 20\n        maxWait: 60000\n        connectTimeout: 30000\n        socketTimeout: 60000\n        timeBetweenEvictionRunsMillis: 60000\n        minEvictableIdleTimeMillis: 300000\n        validationQuery: SELECT 1 FROM DUAL\n        testWhileIdle: true\n        testOnBorrow: false\n        testOnReturn: false\n        poolPreparedStatements: true\n        maxPoolPreparedStatementPerConnectionSize: 20\n        filters: stat,slf4j\n        connectionProperties: druid.stat.mergeSql\\=true;druid.stat.slowSqlMillis\\=5000\n      datasource:\n        master:\n          driver-class-name: com.mysql.cj.jdbc.Driver\n          url: jdbc:mysql://flowmind-mysql:3306/flowmind-cloud?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&serverTimezone=GMT%2B8&nullCatalogMeansCurrent=true\n          username: root\n          password: 123456\nmybatis-plus:\n  ddl:\n    enabled: false\n  type-aliases-package: com.ruoyi.flowable.**.domain\n  mapper-locations: classpath:mapper/**/*.xml\n  configuration:\n    map-underscore-to-camel-case: true\n    cache-enabled: false\n    autoMappingBehavior: PARTIAL\n    autoMappingUnknownColumnBehavior: NONE\n    logImpl: org.apache.ibatis.logging.slf4j.Slf4jImpl\nflowable:\n  database-schema-update: true\n  database-type: mysql', 'a1b2c3d4e5f6789012345678901234ab', NOW(), NOW(), null, '127.0.0.1', '', '', '工作流模块', 'null', 'null', 'yaml', 'null', '');

-- 认证中心
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(104, 'flowmind-auth-prod.yml', 'DEFAULT_GROUP', 'spring:\n  data:\n    redis:\n      host: flowmind-redis\n      port: 6379\n      password:', 'd2e3f4a5b6789012345678901234abcd', NOW(), NOW(), null, '127.0.0.1', '', '', '认证中心', 'null', 'null', 'yaml', 'null', '');

-- 系统模块
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(105, 'flowmind-system-prod.yml', 'DEFAULT_GROUP', 'spring:\n  data:\n    redis:\n      host: flowmind-redis\n      port: 6379\n      password:\n  datasource:\n    druid:\n      stat-view-servlet:\n        enabled: true\n        loginUsername: ruoyi\n        loginPassword: 123456\n    dynamic:\n      primary: master\n      druid:\n        initial-size: 5\n        min-idle: 5\n        maxActive: 20\n        maxWait: 60000\n        connectTimeout: 30000\n        socketTimeout: 60000\n        timeBetweenEvictionRunsMillis: 60000\n        minEvictableIdleTimeMillis: 300000\n        validationQuery: SELECT 1 FROM DUAL\n        testWhileIdle: true\n        testOnBorrow: false\n        testOnReturn: false\n        poolPreparedStatements: true\n        maxPoolPreparedStatementPerConnectionSize: 20\n        filters: stat,slf4j\n        connectionProperties: druid.stat.mergeSql\\=true;druid.stat.slowSqlMillis\\=5000\n      datasource:\n        master:\n          driver-class-name: com.mysql.cj.jdbc.Driver\n          url: jdbc:mysql://flowmind-mysql:3306/flowmind-cloud?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&serverTimezone=GMT%2B8&nullCatalogMeansCurrent=true\n          username: root\n          password: 123456\nmybatis:\n  typeAliasesPackage: com.ruoyi.system\n  mapperLocations: classpath:mapper/**/*.xml', 'e3f4a5b6789012345678901234abcd', NOW(), NOW(), null, '127.0.0.1', '', '', '系统模块', 'null', 'null', 'yaml', 'null', '');

-- 代码生成
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(106, 'flowmind-gen-prod.yml', 'DEFAULT_GROUP', 'spring:\n  data:\n    redis:\n      host: flowmind-redis\n      port: 6379\n      password:\n  datasource:\n    driver-class-name: com.mysql.cj.jdbc.Driver\n    url: jdbc:mysql://flowmind-mysql:3306/flowmind-cloud?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&serverTimezone=GMT%2B8&nullCatalogMeansCurrent=true\n    username: root\n    password: 123456\nmybatis:\n  typeAliasesPackage: com.ruoyi.gen.domain\n  mapperLocations: classpath:mapper/**/*.xml\ngen:\n  author: FlowMind\n  packageName: com.ruoyi.system\n  autoRemovePre: false\n  tablePrefix: sys_\n  allowOverwrite: false', 'a5b678901234567890abcd12345678', NOW(), NOW(), null, '127.0.0.1', '', '', '代码生成', 'null', 'null', 'yaml', 'null', '');

-- 定时任务
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(107, 'flowmind-job-prod.yml', 'DEFAULT_GROUP', 'spring:\n  data:\n    redis:\n      host: flowmind-redis\n      port: 6379\n      password:\n  datasource:\n    driver-class-name: com.mysql.cj.jdbc.Driver\n    url: jdbc:mysql://flowmind-mysql:3306/flowmind-cloud?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&serverTimezone=GMT%2B8&nullCatalogMeansCurrent=true\n    username: root\n    password: 123456\nmybatis:\n  typeAliasesPackage: com.ruoyi.job.domain\n  mapperLocations: classpath:mapper/**/*.xml', 'b678901234567890abcdef12345678', NOW(), NOW(), null, '127.0.0.1', '', '', '定时任务', 'null', 'null', 'yaml', 'null', '');

-- 文件服务
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(108, 'flowmind-file-prod.yml', 'DEFAULT_GROUP', 'file:\n  domain: http://flowmind-nginx/flowmind-ui\n  path: /flowmind/uploadPath\n  prefix: /statics\nminio:\n  url: http://flowmind-nginx:9000\n  accessKey: minioadmin\n  secretKey: minioadmin\n  bucketName: flowmind\nreferer:\n  enabled: false\n  allowed-domains: localhost,127.0.0.1', 'f4a5b678901234567890abcd123456', NOW(), NOW(), null, '127.0.0.1', '', '', '文件服务', 'null', 'null', 'yaml', 'null', '');

-- 监控中心
INSERT INTO config_info (id, data_id, group_id, content, md5, gmt_create, gmt_modified, src_user, src_ip, app_name, tenant_id, c_desc, c_use, effect, type, c_schema, encrypted_data_key) VALUES
(109, 'flowmind-monitor-prod.yml', 'DEFAULT_GROUP', 'spring:\n  security:\n    user:\n      name: ruoyi\n      password: 123456\n  boot:\n    admin:\n      ui:\n        title: FlowMind 服务状态监控
      discovery:
        ignored-services:
          - flowmind-ai-flow', '678901234567890abcdef123456789a', NOW(), NOW(), null, '127.0.0.1', '', '', '监控中心', 'null', 'null', 'yaml', 'null', '');
