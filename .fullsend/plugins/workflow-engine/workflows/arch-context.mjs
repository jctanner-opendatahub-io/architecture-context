/**
 * arch-context.mjs — the architecture-context port workflow: one child
 * agent per component (analyzing the pre-cloned checkout in its cwd),
 * then platform-level aggregation. Port of the original pipeline's
 * phase 3 (generate) + phases 4/6 (collect/platform), P0's components.json
 * being the work-item source.
 *
 * Composition (port plan §1.1 req 9): everything structural is imported
 * primitives (validateInput / fanout / assertComplete / writeResults /
 * writeArtifact). The arch-specific surface is exactly three swappable
 * data blocks — another project ports this module by swapping them:
 *
 *   1. Input + SummarySchema   (input contract, per-component sections)
 *   2. promptFor()             (per-component analysis prompt)
 *   3. renderPlatformDoc()     (aggregation renderer)
 *
 * Stage gating (CLI parity, §5.5): `stages` selects which phases run.
 * fetch/parse are host-side by design (P0); diagrams are a non-goal.
 * collect/platform without generate requires durable journal replay
 * (planned P5) and fails loudly for now.
 */

import fs from "node:fs";
import path from "node:path";

import {
	assertComplete,
	fanout,
	validateInput,
	writeArtifact,
	writeResults,
} from "../lib/primitives.mjs";

export const meta = {
	name: "arch-context",
	description:
		"Analyze a component set (work items from components.json) and aggregate a platform architecture document",
};

// ---------------------------------------------------------------------------
// Swappable data block 1: input contract + per-component summary schema
// ---------------------------------------------------------------------------

const Input = {
	type: "object",
	properties: {
		platform: { type: "string", minLength: 1 },
		stages: { type: "array", items: { type: "string", minLength: 1 } },
		concurrency: { type: "integer", minimum: 1 },
		timeoutMs: { type: "integer", minimum: 1000 },
		components: { type: "array", items: { type: "string", minLength: 1 } },
		items: { type: "array", items: { type: "object" } },
		architectureDir: { type: "string", minLength: 1 },
	},
	additionalProperties: false,
};

const WorkItem = {
	type: "object",
	properties: {
		key: { type: "string", minLength: 1 },
		repoDir: { type: "string", minLength: 1 },
		promptContext: { type: "object" },
	},
	required: ["key", "repoDir"],
	additionalProperties: false,
};

const SummarySchema = {
	type: "object",
	properties: {
		component: { type: "string", minLength: 1 },
		summary: { type: "string", minLength: 1 },
		responsibilities: {
			type: "array",
			items: { type: "string", minLength: 1 },
			minItems: 1,
		},
		interfaces: {
			type: "array",
			items: {
				type: "object",
				properties: {
					name: { type: "string", minLength: 1 },
					kind: { type: "string", minLength: 1 },
					description: { type: "string", minLength: 1 },
				},
				required: ["name", "kind", "description"],
				additionalProperties: false,
			},
		},
		dependencies: { type: "array", items: { type: "string" } },
		concerns: { type: "array", items: { type: "string" } },
	},
	required: [
		"component",
		"summary",
		"responsibilities",
		"interfaces",
		"dependencies",
		"concerns",
	],
	additionalProperties: false,
};

// ---------------------------------------------------------------------------
// Swappable data block 2: per-component analysis prompt
// ---------------------------------------------------------------------------

function promptFor(item) {
	const ctx = item.promptContext || {};
	const lines = [
		`ANALYZE ${item.key}`,
		``,
		`You are analyzing the repository checked out at the current working directory (${item.repoDir}).`,
	];
	// promptContext is optional enrichment (build metadata, overlay context
	// in the original pipeline; repo identity here) — never required.
	if (ctx.repo_url) lines.push(`Repository: ${ctx.repo_url}`);
	if (ctx.ref) lines.push(`Pinned ref: ${ctx.ref}`);
	if (ctx.checkout_branch) lines.push(`Branch: ${ctx.checkout_branch}`);
	if (ctx.type) lines.push(`Component type: ${ctx.type}`);
	lines.push(
		``,
		`Read the source in the working directory and produce a structured architecture summary of this component.`,
		``,
		`Respond with ONLY the raw JSON object — no markdown code fences, no prose before or after.`,
		`The first character of the response must be '{' and the last must be '}'.`,
		``,
		`JSON fields:`,
		`- component: exactly ${JSON.stringify(item.key)}`,
		`- summary: one paragraph describing what this component is and does`,
		`- responsibilities: non-empty array of its architectural responsibilities`,
		`- interfaces: array of {name, kind, description} for exposed APIs/CLIs/protocols`,
		`- dependencies: array of component or repository names it depends on`,
		`- concerns: array of architectural concerns or risks (may be empty)`,
	);
	return lines.join("\n");
}

// ---------------------------------------------------------------------------
// Swappable data block 3: aggregation renderers
// ---------------------------------------------------------------------------

function renderComponentDoc(result) {
	const lines = [`# ${result.component}`, ``, result.summary, ``];
	lines.push(`**Responsibilities:**`, ``, ...result.responsibilities.map((r) => `- ${r}`), ``);
	if (result.interfaces.length > 0) {
		lines.push(`**Interfaces:**`, ``);
		for (const i of result.interfaces) lines.push(`- **${i.name}** (${i.kind}): ${i.description}`);
		lines.push(``);
	}
	if (result.dependencies.length > 0) {
		lines.push(`**Dependencies:** ${result.dependencies.join(", ")}`, ``);
	}
	if (result.concerns.length > 0) {
		lines.push(`**Concerns:**`, ``, ...result.concerns.map((c) => `- ${c}`), ``);
	}
	return lines.join("\n") + "\n";
}

function renderPlatformDoc(artifact) {
	const lines = [
		`# Platform Architecture — ${artifact.platform}`,
		``,
		`- Components analyzed: ${artifact.analyzed}/${artifact.expected}`,
		`- Complete: ${artifact.complete}`,
		``,
	];
	for (const stage of artifact.stages) lines.push(`- Stage: ${stage}`);
	lines.push(``);
	for (const result of artifact.results) {
		lines.push(`## ${result.component}`, ``, result.summary, ``);
		lines.push(`**Responsibilities:**`, ``, ...result.responsibilities.map((r) => `- ${r}`), ``);
		if (result.interfaces.length > 0) {
			lines.push(`**Interfaces:**`, ``);
			for (const i of result.interfaces) lines.push(`- **${i.name}** (${i.kind}): ${i.description}`);
			lines.push(``);
		}
		if (result.dependencies.length > 0) {
			lines.push(`**Dependencies:** ${result.dependencies.join(", ")}`, ``);
		}
		if (result.concerns.length > 0) {
			lines.push(`**Concerns:**`, ``, ...result.concerns.map((c) => `- ${c}`), ``);
		}
	}
	return lines.join("\n") + "\n";
}

// ---------------------------------------------------------------------------
// Workflow body — primitive composition, no bespoke inline logic
// ---------------------------------------------------------------------------

const ALL_STAGES = ["fetch", "parse", "generate", "collect", "diagrams", "platform"];
const HOST_SIDE_STAGES = new Set(["fetch", "parse"]);
const DEFAULT_STAGES = ["generate", "collect", "platform"];

function resolveStages(cfg) {
	const notes = [];
	let stages = cfg.stages || DEFAULT_STAGES;
	for (const stage of stages) {
		if (!ALL_STAGES.includes(stage)) {
			throw new Error(
				`arch-context: unknown stage ${JSON.stringify(stage)} (known: ${ALL_STAGES.join(", ")})`,
			);
		}
	}
	stages = stages.filter((stage) => {
		if (HOST_SIDE_STAGES.has(stage)) {
			notes.push(`stage '${stage}' is host-side by design (P0 pre-clone/prebuilt manifest); skipped in-workflow`);
			return false;
		}
		if (stage === "diagrams") {
			notes.push("stage 'diagrams' is a non-goal for this experiment; skipped");
			return false;
		}
		return true;
	});
	return { stages, notes };
}

function loadWorkItems(cfg) {
	let items = cfg.items;
	if (!items) {
		const file = process.env.WORKFLOW_INPUT_FILE;
		if (!file || !file.trim()) {
			throw new Error(
				"arch-context: no work items — set input.items or WORKFLOW_INPUT_FILE (path to components.json)",
			);
		}
		let raw;
		try {
			raw = JSON.parse(fs.readFileSync(file, "utf8"));
		} catch (err) {
			throw new Error(`arch-context: cannot read work items from ${file}: ${err.message}`);
		}
		if (!Array.isArray(raw)) {
			throw new Error(`arch-context: ${file} must be a JSON array of work items`);
		}
		items = raw;
	}
	items = items.map((item) => validateInput(item, WorkItem, `arch-context item ${JSON.stringify(item?.key)}`));
	if (cfg.components) {
		const wanted = new Set(cfg.components);
		const selected = items.filter((item) => wanted.has(item.key));
		const missing = cfg.components.filter((key) => !items.some((item) => item.key === key));
		if (missing.length > 0) {
			throw new Error(`arch-context: unknown component(s) requested: ${missing.join(", ")}`);
		}
		items = selected;
	}
	if (items.length === 0) {
		throw new Error("arch-context: no work items to process");
	}
	return items;
}

export default async function run(wf, input) {
	const cfg = validateInput(input, Input, "arch-context");
	const { stages, notes } = resolveStages(cfg);
	const items = loadWorkItems(cfg);
	const platform = cfg.platform || "unknown";

	const runGenerate = stages.includes("generate");
	const runCollect = stages.includes("collect");
	const runPlatform = stages.includes("platform");
	if ((runCollect || runPlatform) && !runGenerate) {
		throw new Error(
			"arch-context: 'collect'/'platform' without 'generate' needs durable journal replay (planned P5); include 'generate' in stages",
		);
	}

	// Phase B — fan-out: one analysis child per component, in its checkout.
	// Real analysis runs minutes, not seconds: default timeout 5 min,
	// overridable via input.timeoutMs (host default of 120s is for
	// scripted children only).
	const summaries = await fanout(wf, items, {
		promptOf: promptFor,
		labelOf: (item) => `analyze:${item.key}`,
		schema: SummarySchema,
		cwdOf: (item) => item.repoDir,
		concurrency: cfg.concurrency ?? 2,
		timeoutMs: cfg.timeoutMs ?? 300000,
	});

	// Phase C — completeness, per-component results, platform aggregate.
	// Mirrors the original pipeline's phases 4+6: validated results are
	// published as markdown into <architectureDir>/<platform>/ (the
	// repo's conventional output tree) in addition to the run dir's
	// machine-readable copies. Publishing renders from validated JSON —
	// children never write markdown, so published files are
	// deterministic functions of validated results.
	assertComplete(items, summaries, {
		itemKey: (item) => item.key,
		resultKey: (summary) => summary.component,
		workflow: "arch-context",
	});
	const archDir = path.resolve(cfg.architectureDir || "architecture", platform);
	if (runCollect) {
		writeResults(wf, summaries, {
			fileOf: (summary) => `${summary.component}.json`,
			workflow: "arch-context",
		});
		fs.mkdirSync(archDir, { recursive: true });
		for (const summary of summaries) {
			fs.writeFileSync(path.join(archDir, `${summary.component}.md`), renderComponentDoc(summary));
		}
	}

	const artifact = {
		platform,
		stages,
		analyzed: summaries.length,
		expected: items.length,
		complete: summaries.length === items.length,
		components: items.map((item) => item.key),
		notes,
		results: summaries,
		summary: `${summaries.length}/${items.length} components analyzed (${platform})`,
	};
	writeArtifact(wf, artifact);
	if (runPlatform) {
		fs.writeFileSync(path.join(wf.runDir, "PLATFORM.md"), renderPlatformDoc(artifact));
		fs.mkdirSync(archDir, { recursive: true });
		fs.writeFileSync(path.join(archDir, "PLATFORM.md"), renderPlatformDoc(artifact));
	}
	if (!artifact.complete) {
		throw new Error(`arch-context: incomplete — ${summaries.length}/${items.length} components analyzed`);
	}
	return artifact;
}
