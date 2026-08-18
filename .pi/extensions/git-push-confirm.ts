/**
 * Git Push 确认扩展（项目级）
 *
 * 在执行 git push 前弹窗确认，用户确认后才放行。
 * 防止 AI 未经用户同意直接推送代码。
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
	pi.on("tool_call", async (event, ctx) => {
		if (event.toolName !== "bash") return undefined;

		const command = event.input.command as string;
		// 匹配任意位置的 git push（含 git push origin xxx / git push -u 等）
		if (!/\bgit\s+push\b/.test(command)) return undefined;

		// 识别 force push（--force / -f）
		const isForce =
			/\bgit\s+push\b[^\n]*?(?:--force|-f\b)/.test(command) ||
			/(?:--force|-f\b)[^\n]*?\bgit\s+push\b/.test(command);

		if (!ctx.hasUI) {
			// 非交互模式（-p / json / print）默认阻止，避免无确认直接推送
			return { block: true, reason: "git push 需要用户确认（非交互模式默认阻止）" };
		}

		const title = isForce ? "⚠️ Git Force Push 确认" : "Git Push 确认";
		const confirmed = await ctx.ui.confirm(
			title,
			`检测到${isForce ? "强制 " : ""}push 操作，需你确认后才执行：\n\n  ${command}`,
		);

		if (!confirmed) {
			return { block: true, reason: "用户取消了 push" };
		}

		return undefined;
	});
}
