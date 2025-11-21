// 初始化表单数据
export function initListenerForm(listener) {
  let self = {
    ...listener
  };
  if (listener.script) {
    self = {
      ...listener,
      ...listener.script,
      scriptType: listener.script.resource ? "externalScript" : "inlineScript"
    };
  }
  if (listener.event === "timeout" && listener.eventDefinitions) {
    if (listener.eventDefinitions.length) {
      let k = "";
      for (let key in listener.eventDefinitions[0]) {
        console.log(listener.eventDefinitions, key);
        if (key.indexOf("time") !== -1) {
          k = key;
          self.eventDefinitionType = key.replace("time", "").toLowerCase();
        }
      }
      console.log(k);
      self.eventTimeDefinitions = listener.eventDefinitions[0][k].body;
    }
  }
  return self;
}

export function initListenerType(listener) {
  let listenerType;
  if (listener.class) listenerType = "classListener";
  if (listener.expression) listenerType = "expressionListener";
  if (listener.delegateExpression) listenerType = "delegateExpressionListener";
  if (listener.script) listenerType = "scriptListener";
  return {
    ...JSON.parse(JSON.stringify(listener)),
    ...(listener.script ?? {}),
    listenerType: listenerType
  };
}

// 监听类型
export const LISTENER_TYPE = [
  { label: "Java 类", value: "classListener", prop: "class", key: "listener-class" },
  { label: "表达式", value: "expressionListener", prop: "expression", key: "listener-expression" },
  { label: "代理表达式", value: "delegateExpressionListener", prop: "delegateExpression", key: "listener-delegate" },
  // { label: "脚本", value: "scriptListener", prop: "scriptFormat", key: "listener-script-format" },
]
// 脚本类型
export const SCRIPT_TYPE = [
  { label: "内联脚本", value: "inlineScript" },
  { label: "外部脚本", value: "externalScript" },
]
// 任务监听器: 事件类型
export const TASK_EVENT_TYPE = [
  { label: "创建", value: "create" },
  { label: "指派", value: "assignment" },
  { label: "完成", value: "complete" },
  { label: "删除", value: "delete" },
  { label: "更新", value: "update" },
  { label: "超时", value: "timeout" },
]
// 执行监听器: 事件类型
export const EXECUTION_EVENT_TYPE = [
  { label: "开始", value: "start" },
  { label: "结束", value: "end" },
]
// 事件类型: 定时器类型
export const EVENT_DEFINITION_TYPE = [
  { label: "无", value: "null" },
  { label: "日期", value: "date" },
  { label: "持续时长", value: "duration" },
  { label: "循环", value: "cycle" },
]
// 字段配置
export const FIELD_TYPE = [
  { label: "字符串", value: "string" },
  { label: "表达式", value: "expression" },
]
