-- FlowMind MySQL first-run initialization entrypoint.
-- The MySQL image executes this file only when /var/lib/mysql is empty.

SOURCE /opt/flowmind-sql/ry_config_20250902.sql;
SOURCE /opt/flowmind-sql/nacos配置.sql;
SOURCE /opt/flowmind-sql/ry_seata_20210128.sql;

USE `flowmind-cloud`;
SOURCE /opt/flowmind-sql/ry_20250523.sql;
SOURCE /opt/flowmind-sql/quartz.sql;
SOURCE /opt/flowmind-sql/flowable相关表.sql;
SOURCE /opt/flowmind-sql/wf_draft.sql;
