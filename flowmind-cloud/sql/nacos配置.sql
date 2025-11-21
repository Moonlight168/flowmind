INSERT INTO `flowmind-config`.`config_info` (
	`id`,
	`data_id`,
	`group_id`,
	`content`,
	`md5`,
	`gmt_create`,
	`gmt_modified`,
	`src_user`,
	`src_ip`,
	`app_name`,
	`tenant_id`,
	`c_desc`,
	`c_use`,
	`effect`,
	`type`,
	`c_schema`,
	`encrypted_data_key` 
)
VALUES
	(
		10122,
		'ruoyi-flowable-dev.yml',
		'DEFAULT_GROUP',
		'# spring配置\r\nspring:\r\n  redis:\r\n    host: 192.168.0.133\r\n    port: 6379\r\n    password: \r\n  datasource:\r\n    druid:\r\n      stat-view-servlet:\r\n        enabled: true\r\n        loginUsername: ruoyi\r\n        loginPassword: 123456\r\n    dynamic:\r\n      druid:\r\n        initial-size: 5\r\n        min-idle: 5\r\n        maxActive: 20\r\n        maxWait: 60000\r\n        connectTimeout: 30000\r\n        socketTimeout: 60000\r\n        timeBetweenEvictionRunsMillis: 60000\r\n        minEvictableIdleTimeMillis: 300000\r\n        validationQuery: SELECT 1 FROM DUAL\r\n        testWhileIdle: true\r\n        testOnBorrow: false\r\n        testOnReturn: false\r\n        poolPreparedStatements: true\r\n        maxPoolPreparedStatementPerConnectionSize: 20\r\n        filters: stat,slf4j\r\n        connectionProperties: druid.stat.mergeSql\\=true;druid.stat.slowSqlMillis\\=5000\r\n      datasource:\r\n          # 主库数据源\r\n          master:\r\n            driver-class-name: com.mysql.cj.jdbc.Driver\r\n            url: jdbc:mysql://192.168.0.133:3306/flowmind-cloud?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=true&serverTimezone=GMT%2B8&nullCatalogMeansCurrent=true\r\n            username: root\r\n            password: 123456\r\n          # 从库数据源\r\n          # slave:\r\n            # username: \r\n            # password: \r\n            # url: \r\n            # driver-class-name: \r\n# mybatis配置\r\nmybatis-plus:\r\n    # 搜索指定包别名\r\n  mapperPackage: com.ruoyi\r\n  typeAliasesPackage: com.ruoyi.flowable\r\n    # 配置mapper的扫描，找到所有的mapper.xml映射文件\r\n  mapper-locations: classpath:mapper/**/*.xml\r\n  configuration:\r\n    map-underscore-to-camel-case: true\r\n    cache-enabled: false\r\n    # 自动驼峰命名规则（camel case）映射\r\n    mapUnderscoreToCamelCase: true\r\n    # MyBatis 自动映射策略\r\n    # NONE：不启用 PARTIAL：只对非嵌套 resultMap 自动映射 FULL：对所有 resultMap 自动映射\r\n    autoMappingBehavior: PARTIAL\r\n    # MyBatis 自动映射时未知列或未知属性处理策\r\n    # NONE：不做处理 WARNING：打印相关警告 FAILING：抛出异常和详细信息\r\n    autoMappingUnknownColumnBehavior: NONE\r\n    # 更详细的日志输出 会有性能损耗 org.apache.ibatis.logging.stdout.StdOutImpl\r\n    # 关闭日志记录 (可单纯使用 p6spy 分析) org.apache.ibatis.logging.nologging.NoLoggingImpl\r\n    # 默认日志输出 org.apache.ibatis.logging.slf4j.Slf4jImpl\r\n    logImpl: org.apache.ibatis.logging.slf4j.Slf4jImpl',
	'848b666e18a30cd8cdd4ba232844b92d',
	'2025-01-16 01:54:58',
	'2025-01-16 01:54:58',
	NULL,
	'127.0.0.1',
	'',
	'',
	'工作流模块',
	NULL,
	NULL,
	'yaml',
	NULL,
'' 
);