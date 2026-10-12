/**
 * FlowMind 设计链路契约评估器（Langfuse Code Evaluator，TypeScript）。
 *
 * 与 Python 侧 `app/evaluation/golden_dataset.py::evaluate_contract` 保持同一套
 * 稳定契约指标，便于在 Langfuse 控制台对实验直接打分：
 *   status_match / required_fields / minimum_counts / node_type_coverage /
 *   widget_type_coverage / fallback_contract / artifact_validity /
 *   incremental_retention / contract_score
 *
 * 评估输入：
 *   - ctx.observation.output        实验 task 的返回（含 status、turn_outputs 等）
 *   - ctx.experiment.itemExpectedOutput  数据集项的期望输出契约
 * 两者可能是 JSON 字符串（Langfuse 服务端序列化），需先 decodeValue。
 *
 * 与 Python 版的差异（本文件受运行时约束，不引入 XML 解析器）：
 *   - flow_design 的产物有效性做轻量结构检查（process/startEvent/endEvent 标记），
 *     BPMN 连通性、网关条件等完整语义校验仍由 Python 评估器负责；
 *   - form_design 的产物校验完整移植（widgetList/formConfig 结构与组件必需字段）。
 */

type ToolCall = {
  id: string;
  name: string;
  arguments: unknown;
  type: string;
  index: number;
};

type EvaluationContext = {
  observation: {
    input: any;
    output: any;
    metadata: any;
    toolCalls: ToolCall[];
  };
  experiment:
    | {
        itemExpectedOutput: any;
        itemMetadata: any;
      }
    | undefined;
};

type Score = {
  name: string;
  value: number;
  dataType: "NUMERIC" | "BOOLEAN" | "CATEGORICAL" | "TEXT";
  comment?: string;
  metadata?: Record<string, unknown>;
};

type EvaluationResult = {
  scores: Score[];
};

type GoldenFallbackOutput = {
  error_types?: string[];
  message_required?: boolean;
  message_contains?: string[];
};

type GoldenExpectedOutput = {
  status?: string;
  required_paths?: string[];
  min_counts?: Record<string, number>;
  required_node_types?: string[];
  required_widget_types?: string[];
  message_contains?: string[];
  error_type?: string | null;
  fallback_output?: GoldenFallbackOutput | null;
};

// --- 基础工具 --------------------------------------------------------------

function decodeValue(value: unknown): unknown {
  if (typeof value !== "string") {
    return value;
  }
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}

function asRecord(value: unknown): Record<string, any> {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, any>)
    : {};
}

function resolvePath(value: unknown, path: string): unknown {
  let current: any = value;
  for (const part of path.split(".")) {
    if (current === null || typeof current !== "object" || Array.isArray(current)) {
      return undefined;
    }
    if (!(part in current)) {
      return undefined;
    }
    current = current[part];
  }
  return current;
}

function collectionSize(value: unknown): number {
  if (Array.isArray(value) || typeof value === "string") {
    return value.length;
  }
  if (value !== null && typeof value === "object") {
    return Object.keys(value).length;
  }
  return 0;
}

function itemValues(output: unknown, path: string, key: string): Set<string> {
  const names = new Set<string>();
  const items = resolvePath(output, path);
  if (!Array.isArray(items)) {
    return names;
  }
  for (const item of items) {
    const record = asRecord(item);
    if (record[key] !== undefined && record[key] !== null) {
      names.add(String(record[key]));
    }
  }
  return names;
}

function numericScore(name: string, value: number, comment: string): Score {
  return { name, value, dataType: "NUMERIC", comment };
}

function booleanScore(name: string, passed: boolean, comment: string): Score {
  return numericScore(name, passed ? 1 : 0, comment);
}

// --- 契约打分 --------------------------------------------------------------

function appendPathScores(
  scores: Score[],
  output: Record<string, any>,
  expected: GoldenExpectedOutput,
): void {
  const requiredPaths = expected.required_paths ?? [];
  if (requiredPaths.length > 0) {
    const matched = requiredPaths.filter((path) => {
      const resolved = resolvePath(output, path);
      return resolved !== undefined && resolved !== null;
    }).length;
    scores.push(
      numericScore(
        "required_fields",
        matched / requiredPaths.length,
        `必需字段 ${matched}/${requiredPaths.length}`,
      ),
    );
  }
  const minCounts = expected.min_counts ?? {};
  const minKeys = Object.keys(minCounts);
  if (minKeys.length > 0) {
    const passed = minKeys.filter(
      (path) => collectionSize(resolvePath(output, path)) >= minCounts[path],
    ).length;
    scores.push(
      numericScore(
        "minimum_counts",
        passed / minKeys.length,
        `最小数量约束 ${passed}/${minKeys.length}`,
      ),
    );
  }
}

function coverageScore(name: string, actual: Set<string>, required: string[]): Score {
  const matched = required.filter((item) => actual.has(item)).length;
  return numericScore(
    name,
    matched / required.length,
    `覆盖 ${matched}/${required.length}: ${required.join(", ")}`,
  );
}

function appendCoverageScores(
  scores: Score[],
  output: Record<string, any>,
  expected: GoldenExpectedOutput,
): void {
  const nodeTypes = expected.required_node_types ?? [];
  if (nodeTypes.length > 0) {
    scores.push(
      coverageScore("node_type_coverage", itemValues(output, "form_data.nodes", "type"), nodeTypes),
    );
  }
  const widgetTypes = expected.required_widget_types ?? [];
  if (widgetTypes.length > 0) {
    scores.push(
      coverageScore(
        "widget_type_coverage",
        itemValues(output, "form_data.widgetList", "type"),
        widgetTypes,
      ),
    );
  }
}

function fallbackContractMatches(
  output: Record<string, any>,
  expected: GoldenExpectedOutput,
): boolean | null {
  const hasExplicitContract =
    (expected.error_type !== undefined && expected.error_type !== null) ||
    (expected.message_contains ?? []).length > 0;
  const observedFallback =
    output.status === "error" && expected.fallback_output ? expected.fallback_output : null;
  if (!hasExplicitContract && !observedFallback) {
    return null;
  }
  const errorTypes = observedFallback
    ? observedFallback.error_types ?? []
    : expected.error_type
      ? [expected.error_type]
      : [];
  const errorMatches = errorTypes.length === 0 || errorTypes.includes(String(output.error_type));
  const message = String(output.message ?? "");
  const requiredText = observedFallback
    ? observedFallback.message_contains ?? []
    : expected.message_contains ?? [];
  let messageMatches = requiredText.every((text) => message.includes(text));
  if (observedFallback && observedFallback.message_required !== false) {
    messageMatches = message.trim().length > 0 && messageMatches;
  }
  return errorMatches && messageMatches;
}

function appendFallbackScore(
  scores: Score[],
  output: Record<string, any>,
  expected: GoldenExpectedOutput,
): void {
  const matches = fallbackContractMatches(output, expected);
  if (matches === null) {
    return;
  }
  scores.push(booleanScore("fallback_contract", matches, "错误类型与用户可见兜底文案契约"));
}

// --- 产物有效性 / 多轮保留 -------------------------------------------------

function* iterChildLists(widget: Record<string, any>): Generator<Record<string, any>[]> {
  if (Array.isArray(widget.widgetList)) {
    yield widget.widgetList;
  }
  for (const key of ["cols", "tabs", "rows"]) {
    const children = widget[key];
    if (!Array.isArray(children)) {
      continue;
    }
    for (const child of children) {
      if (child === null || typeof child !== "object" || Array.isArray(child)) {
        continue;
      }
      if (child.type) {
        yield [child];
      } else if (Array.isArray(child.widgetList)) {
        yield child.widgetList;
      }
      if (key === "rows") {
        const cells = child.cols ?? child.cells ?? [];
        for (const cell of cells) {
          if (cell === null || typeof cell !== "object" || Array.isArray(cell)) {
            continue;
          }
          if (cell.type) {
            yield [cell];
          } else if (Array.isArray(cell.widgetList)) {
            yield cell.widgetList;
          }
        }
      }
    }
  }
}

function* iterWidgets(widgets: Record<string, any>[]): Generator<Record<string, any>> {
  for (const widget of widgets) {
    yield widget;
    for (const childList of iterChildLists(asRecord(widget))) {
      yield* iterWidgets(childList);
    }
  }
}

function nestedWidgetNames(widgets: unknown): Set<string> {
  const names = new Set<string>();
  if (!Array.isArray(widgets)) {
    return names;
  }
  for (const widget of iterWidgets(widgets)) {
    const name = asRecord(widget.options).name;
    if (name) {
      names.add(String(name));
    }
  }
  return names;
}

function bpmnLooksValid(xml: string): boolean {
  // 轻量结构检查：仅确认关键元素存在，完整语义校验见 Python evaluate_contract
  return (
    /<(\w+:)?process[\s>]/i.test(xml) &&
    /<(\w+:)?startEvent[\s>]/i.test(xml) &&
    /<(\w+:)?endEvent[\s>]/i.test(xml)
  );
}

function vform3LooksValid(document: Record<string, any>): boolean {
  if (!Array.isArray(document.widgetList)) {
    return false;
  }
  if (
    document.formConfig === null ||
    typeof document.formConfig !== "object" ||
    Array.isArray(document.formConfig)
  ) {
    return false;
  }
  for (const widget of iterWidgets(document.widgetList)) {
    if (["id", "key", "type", "options"].every((field) => field in widget)) {
      continue;
    }
    if (widget.internal && ["id", "type", "options"].every((field) => field in widget)) {
      continue;
    }
    return false;
  }
  return true;
}

function artifactIsValid(turn: unknown): boolean {
  const record = asRecord(turn);
  const artifact = asRecord(record.form_data);
  if (Object.keys(artifact).length === 0) {
    return false;
  }
  if (asRecord(record.validation).passed === false) {
    return false;
  }
  const designType = record.design_type;
  if (designType === "flow_design") {
    const bpmnXml = artifact.bpmn_xml;
    if (typeof bpmnXml === "string" && bpmnXml.trim().length > 0) {
      return bpmnLooksValid(bpmnXml);
    }
    return Boolean(artifact.flow_name);
  }
  if (designType === "form_design") {
    return vform3LooksValid(artifact);
  }
  if (designType === "category_design") {
    return Boolean(artifact.category_name);
  }
  return Object.keys(artifact).length > 0;
}

function removedTargets(operations: unknown): Set<string> {
  const targets = new Set<string>();
  if (!Array.isArray(operations)) {
    return targets;
  }
  for (const operation of operations) {
    const record = asRecord(operation);
    if (record.op === "remove_node" || record.op === "remove_widget") {
      targets.add(String(record.node_id ?? record.widget_name ?? ""));
    }
  }
  return targets;
}

function artifactElementIds(artifact: Record<string, any>): Set<string> {
  const ids = new Set<string>();
  if (Array.isArray(artifact.nodes)) {
    for (const node of artifact.nodes) {
      const id = asRecord(node).id;
      if (id) {
        ids.add(String(id));
      }
    }
  }
  for (const name of nestedWidgetNames(artifact.widgetList)) {
    ids.add(name);
  }
  return ids;
}

function retainsPreviousArtifact(turns: unknown[]): boolean {
  for (let index = 1; index < turns.length; index += 1) {
    const previous = asRecord(turns[index - 1]);
    const current = asRecord(turns[index]);
    const removed = removedTargets(current.operations);
    const currentIds = artifactElementIds(asRecord(current.form_data));
    for (const id of artifactElementIds(asRecord(previous.form_data))) {
      if (!removed.has(id) && !currentIds.has(id)) {
        return false;
      }
    }
  }
  return true;
}

function appendChainQualityScores(scores: Score[], output: Record<string, any>): void {
  const turns =
    Array.isArray(output.turn_outputs) && output.turn_outputs.length > 0
      ? output.turn_outputs
      : [output];
  const readyTurns = turns.filter((turn: unknown) => asRecord(turn).status === "ready");
  if (readyTurns.length > 0) {
    const valid = readyTurns.filter((turn: unknown) => artifactIsValid(turn)).length;
    scores.push(
      numericScore(
        "artifact_validity",
        valid / readyTurns.length,
        `可导入产物 ${valid}/${readyTurns.length}`,
      ),
    );
  }
  if (readyTurns.length > 1) {
    scores.push(
      booleanScore(
        "incremental_retention",
        retainsPreviousArtifact(readyTurns),
        "多轮修改保留未显式删除的既有元素",
      ),
    );
  }
}

// --- 入口 ------------------------------------------------------------------

function evaluate(ctx: EvaluationContext): EvaluationResult {
  const output = asRecord(decodeValue(ctx.observation?.output));
  const expected = asRecord(decodeValue(ctx.experiment?.itemExpectedOutput)) as GoldenExpectedOutput;
  const scores: Score[] = [];

  scores.push(booleanScore("status_match", output.status === expected.status, `期望 status=${expected.status}`));
  appendPathScores(scores, output, expected);
  appendCoverageScores(scores, output, expected);
  appendFallbackScore(scores, output, expected);
  appendChainQualityScores(scores, output);

  const total = scores.reduce((sum, score) => sum + Number(score.value), 0);
  scores.push(numericScore("contract_score", total / scores.length, "所有稳定契约指标的平均分"));

  return { scores };
}