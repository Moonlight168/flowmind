/**
 * FlowMind 设计评测的唯一 Langfuse Code Evaluator。
 *
 * 每一轮均有非空输出且状态为 ready 或 needs_input 时通过。
 * needs_input 表示模型正常追问，不视为系统失败；error 视为失败。
 */

type Score = {
  name: string;
  value: number;
  dataType: "NUMERIC";
  comment: string;
};

type EvaluationContext = {
  observation?: { output?: unknown };
};

const SUCCESS_STATUSES = new Set(["ready", "needs_input"]);

function decodeValue(value: unknown): unknown {
  if (typeof value !== "string") return value;
  try {
    return JSON.parse(value);
  } catch {
    return value;
  }
}

function asRecord(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function outputsOf(output: Record<string, unknown>): Record<string, unknown>[] {
  const turns = output.turn_outputs;
  if (Array.isArray(turns) && turns.length > 0) {
    return turns.map(asRecord);
  }
  return [output];
}

function hasOutput(output: Record<string, unknown>): boolean {
  return Object.entries(output).some(([key, value]) => {
    if (["status", "thread_id", "case_id", "design_type"].includes(key)) {
      return false;
    }
    if (typeof value === "string") return value.trim().length > 0;
    if (Array.isArray(value)) return value.length > 0;
    if (value !== null && typeof value === "object") {
      return Object.keys(value as Record<string, unknown>).length > 0;
    }
    return value !== null && value !== undefined;
  });
}

function score(name: string, passed: boolean, comment: string): Score {
  return { name, value: passed ? 1 : 0, dataType: "NUMERIC", comment };
}

function evaluate(ctx: EvaluationContext): { scores: Score[] } {
  const output = asRecord(decodeValue(ctx.observation?.output));
  const turns = outputsOf(output);
  const outputPresent = turns.length > 0 && turns.every(hasOutput);
  const statusSuccess = turns.length > 0 && turns.every((turn) =>
    SUCCESS_STATUSES.has(String(turn.status ?? "")),
  );
  const casePass = outputPresent && statusSuccess;

  return {
    scores: [
      score("has_output", outputPresent, "每轮均返回有效输出"),
      score("status_success", statusSuccess, "每轮状态均为 ready 或 needs_input"),
      score("case_pass", casePass, "输出有效且处理状态成功"),
    ],
  };
}
