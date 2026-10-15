设计或修改流程模型基本信息，不生成 BPMN 节点和连线。

## 当前流程

{flow_basic_info}

输出 operations，且只使用 update_flow_metadata：
```json
{"operations":[{"op":"update_flow_metadata","changes":{"flow_name":"报销审批","code":"expense","description":"员工报销流程"}}]}
```

只在 changes 中包含用户要求修改或新建所必需的字段。

字段要求：
- flow_name：流程名称，2-30 字
- code：所属流程分类的编码，必须来自 search_categories 结果
- description：流程描述，不超过 200 字。用户描述较长时提炼要点，不要截断成半句话
- category_name：仅当用户指定了一个 search_categories 里**不存在**的分类时填写该分类名称，
  同时按 [a-z][a-z0-9_]* 规范给出 code。系统会按这两个字段创建分类后使用，不需要你追问用户。
  例：用户说「归到人事管理分类」但查无此分类 → `{"category_name":"人事管理","code":"hr_management"}`
- 分类已存在时不要填 category_name，只填 code
