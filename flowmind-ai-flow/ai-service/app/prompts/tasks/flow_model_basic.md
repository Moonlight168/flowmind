设计或修改流程模型基本信息，不生成 BPMN 节点和连线。

## 当前流程

{flow_basic_info}

输出 operations，且只使用 update_flow_metadata：
```json
{"operations":[{"op":"update_flow_metadata","changes":{"flow_name":"报销审批","code":"expense","description":"员工报销流程"}}]}
```

只在 changes 中包含用户要求修改或新建所必需的字段。code 必须来自 search_categories 返回的真实 code；没有可用分类时追问或明确报错，不得编造。
