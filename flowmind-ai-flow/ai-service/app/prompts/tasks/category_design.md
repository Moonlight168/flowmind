设计或修改流程分类，只输出 `update_category` 操作。

## 当前分类

{flow_basic_info}

```json
{"operations":[{"op":"update_category","changes":{"category_name":"请假审批","code":"leave_approval","remark":"员工请假流程"}}]}
```

规则：

- `changes` 只包含用户要求修改的字段；新建时补齐必要字段。
- `code` 可以修改，但必须符合命名规范且全局唯一。
- 生成或修改 `code` 前调用 `search_categories`；编辑时当前 `categoryId` 对应的原 code 不算冲突。
- code 冲突时根据校验反馈重试，选择语义一致且不冲突的新编码。
- 分类名称允许重复，不得增加后端不存在的名称唯一性限制。
- 不得编造查询结果，不得修改用户未涉及的字段。
