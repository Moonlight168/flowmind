-- ----------------------------
-- Table structure for wf_draft
-- ----------------------------
DROP TABLE IF EXISTS `wf_draft`;
CREATE TABLE `wf_draft` (
  `draft_id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '草稿ID',
  `user_id` bigint(20) NOT NULL COMMENT '用户ID',
  `definition_id` varchar(255) NOT NULL COMMENT '流程定义ID',
  `deploy_id` varchar(64) DEFAULT '' COMMENT '部署ID',
  `process_name` varchar(255) DEFAULT '' COMMENT '流程名称',
  `form_data` longtext COMMENT '表单数据',
  `form_model` longtext COMMENT '表单模型',
  `del_flag` char(1) DEFAULT '0' COMMENT '删除标志（0代表存在 2代表删除）',
  `create_by` varchar(64) DEFAULT '' COMMENT '创建者',
  `create_time` datetime DEFAULT NULL COMMENT '创建时间',
  `update_by` varchar(64) DEFAULT '' COMMENT '更新者',
  `update_time` datetime DEFAULT NULL COMMENT '更新时间',
  `remark` varchar(500) DEFAULT NULL COMMENT '备注',
  PRIMARY KEY (`draft_id`),
  UNIQUE KEY `uk_user_definition` (`user_id`,`definition_id`) USING BTREE COMMENT '同一用户同一流程定义只能有一个草稿',
  KEY `idx_user_id` (`user_id`) USING BTREE,
  KEY `idx_definition_id` (`definition_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT='流程草稿表';