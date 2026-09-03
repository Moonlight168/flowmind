# BPMN 设计约束

- 支持的节点：START_EVENT、END_EVENT、USER_TASK、EXCLUSIVE_GATEWAY、PARALLEL_GATEWAY、INCLUSIVE_GATEWAY、COMPLEX_GATEWAY、EVENT_GATEWAY、INTERMEDIATE_THROW_EVENT。
- 一个流程只有一个开始事件，至少一个结束事件；开始事件只能有一条出边，结束事件允许多条入边。
- 网关可以是分支（至少两条出边）或汇聚（至少两条入边、一条出边）。并行分支应使用对应的并行汇聚。
- 排他分支最多一条默认出边。非默认出边必须有结构化 condition；默认出边设置 is_default=true 且不设置 condition。
- 条件字段只能引用表单中真实存在的 options.name，比较值类型应与表单字段类型一致。
- USER_TASK 的角色、人员和表单只能取自检索工具结果；工具无结果时不能伪造。
- 每条连线的 source、target 必须引用现有节点；禁止自环、悬空节点和不可达审批节点。
- 修改已有设计时输出最小操作集。不要复制未修改结构，也不要更换稳定 id。
