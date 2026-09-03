设计或修改流程分类。

## 当前分类

{flow_basic_info}

输出 operations，且只使用 update_category：
```json
{"operations":[{"op":"update_category","changes":{"category_name":"请假审批","code":"leave_approval","remark":"员工请假流程"}}]}
```

只在 changes 中包含用户要求修改或新建所必需的字段。创建或修改 code 前使用 search_categories 验证唯一性；发现冲突时应说明并追问，不得静默改成另一个 code。
