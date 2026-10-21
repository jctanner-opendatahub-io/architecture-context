/**
 * arch-context.mjs — the architecture-context port workflow: analyzer-baseline
 * validation, one child agent per component (analyzing the pre-cloned checkout
 * in its cwd against the analyzer baseline), then platform-level aggregation.
 * Port of the original pipeline's phases 2c (static-analysis validation),
 * 3 (generate) and 4/6 (collect/platform); P0's components.json is the
 * work-item source and P0's host-side arch-analyzer run is the baseline.
 *
 * Composition (port plan §1.1 req 9): everything structural is imported
 * primitives (validateInput / fanout / assertComplete / writeResults /
 * writeArtifact). The arch-specific surface is exactly three swappable
 * data blocks — another project ports this module by swapping them:
 *
 *   1. Input + SummarySchema   (input contract; summary sections = the
 *                               repo-to-architecture-summary template)
 *   2. promptFor()             (per-component prompt = the skill contract:
 *                               analyzer baseline as ground truth)
 *   3. renderComponentDoc() / renderPlatformDoc()  (template-shaped output)
 *
 * Stage gating (CLI parity, §5.5): `stages` selects which phases run —
 * fetch/parse are host-side by design (P0), analyze validates the prebuilt
 * analyzer baseline in-workflow, generate is the fan-out, collect/platform
 * publish. Diagrams are a non-goal. collect/platform without generate
 * requires durable journal replay (planned P5) and fails loudly for now.
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
		"Analyze a component set (work items from components.json, with analyzer baselines) and aggregate a platform architecture document",
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
		analyzerDir: { type: "string", minLength: 1 },
		promptContext: { type: "object" },
	},
	required: ["key", "repoDir"],
	additionalProperties: false,
};

// SummarySchema mirrors the section structure of
// .claude/skills/repo-to-architecture-summary/templates/architecture-template.md
// (the RHOAI-specific sections — AIPCC ecosystems, serving runtimes,
// kustomize parameterization detail, RBAC tables — are collapsed or
// dropped; empty arrays are valid where a section does not apply).
const SummarySchema = {
	type: "object",
	properties: {
		component: { type: "string", minLength: 1 },
		purpose: {
			type: "object",
			properties: {
				short: { type: "string", minLength: 1 },
				detailed: { type: "string", minLength: 1 },
			},
			required: ["short", "detailed"],
			additionalProperties: false,
		},
		architecturalAnalysis: { type: "string", minLength: 1 },
		architectureComponents: {
			type: "array",
			items: {
				type: "object",
				properties: {
					name: { type: "string", minLength: 1 },
					type: { type: "string", minLength: 1 },
					purpose: { type: "string", minLength: 1 },
				},
				required: ["name", "type", "purpose"],
				additionalProperties: false,
			},
		},
		subComponents: {
			type: "array",
			items: {
				type: "object",
				properties: {
					name: { type: "string", minLength: 1 },
					apiRoutes: {
						type: "array",
						items: {
							type: "object",
							properties: {
								path: { type: "string", minLength: 1 },
								methods: { type: "array", items: { type: "string" } },
							},
							required: ["path", "methods"],
							additionalProperties: false,
						},
					},
					upstreamDependencies: { type: "array", items: { type: "string" } },
					configuration: { type: "array", items: { type: "string" } },
				},
				required: ["name", "apiRoutes", "upstreamDependencies", "configuration"],
				additionalProperties: false,
			},
		},
		apisExposed: {
			type: "object",
			properties: {
				httpEndpoints: {
					type: "array",
					items: {
						type: "object",
						properties: {
							path: { type: "string", minLength: 1 },
							methods: { type: "array", items: { type: "string" } },
							description: { type: "string", minLength: 1 },
						},
						required: ["path", "methods", "description"],
						additionalProperties: false,
					},
				},
				grpcServices: {
					type: "array",
					items: {
						type: "object",
						properties: {
							name: { type: "string", minLength: 1 },
							description: { type: "string", minLength: 1 },
						},
						required: ["name", "description"],
						additionalProperties: false,
					},
				},
				customResourceDefinitions: {
					type: "array",
					items: {
						type: "object",
						properties: {
							group: { type: "string", minLength: 1 },
							version: { type: "string", minLength: 1 },
							kind: { type: "string", minLength: 1 },
							purpose: { type: "string", minLength: 1 },
						},
						required: ["group", "version", "kind", "purpose"],
						additionalProperties: false,
					},
				},
			},
			required: ["httpEndpoints", "grpcServices", "customResourceDefinitions"],
			additionalProperties: false,
		},
		dependencies: {
			type: "object",
			properties: {
				external: { type: "array", items: { type: "string" } },
				internalPlatform: { type: "array", items: { type: "string" } },
			},
			required: ["external", "internalPlatform"],
			additionalProperties: false,
		},
		deployment: {
			type: "object",
			properties: {
				summary: { type: "string", minLength: 1 },
				variants: { type: "array", items: { type: "string" } },
			},
			required: ["summary", "variants"],
			additionalProperties: false,
		},
		network: {
			type: "object",
			properties: {
				services: { type: "array", items: { type: "string" } },
				ingress: { type: "array", items: { type: "string" } },
				egress: { type: "array", items: { type: "string" } },
			},
			required: ["services", "ingress", "egress"],
			additionalProperties: false,
		},
		security: {
			type: "object",
			properties: {
				authentication: { type: "string", minLength: 1 },
				authorization: { type: "string", minLength: 1 },
				secrets: { type: "array", items: { type: "string" } },
				fipsCompliance: { type: "string", minLength: 1 },
			},
			required: ["authentication", "authorization", "secrets", "fipsCompliance"],
			additionalProperties: false,
		},
		multiTenancy: {
			type: "object",
			properties: {
				model: { type: "string", minLength: 1 },
				isolationMechanisms: { type: "array", items: { type: "string" } },
				sharedServices: { type: "array", items: { type: "string" } },
			},
			required: ["model", "isolationMechanisms", "sharedServices"],
			additionalProperties: false,
		},
		dataFlows: {
			type: "array",
			items: {
				type: "object",
				properties: {
					name: { type: "string", minLength: 1 },
					description: { type: "string", minLength: 1 },
				},
				required: ["name", "description"],
				additionalProperties: false,
			},
		},
		integrationPoints: {
			type: "array",
			items: {
				type: "object",
				properties: {
					name: { type: "string", minLength: 1 },
					description: { type: "string", minLength: 1 },
				},
				required: ["name", "description"],
				additionalProperties: false,
			},
		},
		concerns: { type: "array", items: { type: "string" } },
	},
	required: [
		"component",
		"purpose",
		"architecturalAnalysis",
		"architectureComponents",
		"subComponents",
		"apisExposed",
		"dependencies",
		"deployment",
		"network",
		"security",
		"multiTenancy",
		"dataFlows",
		"integrationPoints",
		"concerns",
	],
	additionalProperties: false,
};

// ---------------------------------------------------------------------------
// Swappable data block 2: per-component analysis prompt
// (port of the repo-to-architecture-summary skill contract)
// ---------------------------------------------------------------------------

function promptFor(item) {
	const ctx = item.promptContext || {};
	const lines = [
		`ANALYZE ${item.key}`,
		``,
		`You are generating the architecture summary for the repository checked out at the current working directory (${item.repoDir}).`,
	];
	// promptContext is optional enrichment (build metadata, overlay context
	// in the original pipeline; repo identity here) — never required.
	if (ctx.repo_url) lines.push(`Repository: ${ctx.repo_url}`);
	if (ctx.ref) lines.push(`Pinned ref: ${ctx.ref}`);
	if (ctx.checkout_branch) lines.push(`Branch: ${ctx.checkout_branch}`);
	if (ctx.type) lines.push(`Component type: ${ctx.type}`);
	if (item.analyzerDir) {
		lines.push(
			``,
			`BASELINE FACTS (ground truth — never contradict these):`,
			`- ${item.analyzerDir}/analyzer_synthesis_context.md — bounded, source-linked projection; read this FIRST`,
			`- ${item.analyzerDir}/analyzer_architecture.md — rendered analyzer baseline (its "Architectural Analysis" section is pending; writing that narrative is YOUR job)`,
			`- ${item.analyzerDir}/component-architecture.json — authoritative analyzer JSON`,
			``,
			`Use the analyzer facts as your baseline: they save you time and tokens. Read`,
			`repository source in the working directory as needed to write the narrative`,
			`and fill gaps. Do not invent facts that are in neither the baseline nor the`,
			`source.`,
		);
	} else {
		lines.push(``, `No analyzer baseline is provided; analyze the source directly.`);
	}
	lines.push(
		``,
		`Respond with ONLY the raw JSON object — no markdown code fences, no prose before or after.`,
		`The first character of the response must be '{' and the last must be '}'.`,
		`Every value must match the exact JSON type listed: narrative fields are strings`,
		`(write "none" or "not applicable" — never booleans or null); arrays may be empty.`,
		`The JSON must be strictly valid: escape every double quote inside string values`,
		`(write \\\" for each \") and avoid literal double quotes in URL paths (write`,
		`/{tenant}/ rather than /{"tenant"}/). Keep string values concise (under ~25 words).`,
		``,
		`JSON fields (the architecture template's sections; empty arrays where a`,
		`section does not apply):`,
		`- component: exactly ${JSON.stringify(item.key)}`,
		`- purpose: {short: one sentence, detailed: one paragraph}`,
		`- architecturalAnalysis: concise architecture narrative synthesized from analyzer facts and bounded source evidence`,
		`- architectureComponents: [{name, type, purpose}]`,
		`- subComponents: [{name, apiRoutes: [{path, methods}], upstreamDependencies: [], configuration: []}]`,
		`- apisExposed: {httpEndpoints: [{path, methods, description}], grpcServices: [{name, description}], customResourceDefinitions: [{group, version, kind, purpose}]}`,
		`- dependencies: {external: [], internalPlatform: []}`,
		`- deployment: {summary, variants: []}`,
		`- network: {services: [], ingress: [], egress: []}`,
		`- security: {authentication, authorization, secrets: [], fipsCompliance: string such as "not applicable" or a compliance summary}`,
		`- multiTenancy: {model, isolationMechanisms: [], sharedServices: []}`,
		`- dataFlows: [{name, description}]`,
		`- integrationPoints: [{name, description}]`,
		`- concerns: [] (architectural concerns or risks)`,
	);
	return lines.join("\n");
}

/** Corrective retry prompt: a fresh child session carrying the exact
 * failure (invalid JSON, schema violation) so the model can fix its
 * previous output. Used via the fanout primitive's retries option. */
function retryPromptFor(item, err) {
	return [
		`RETRY ANALYZE ${item.key}`,
		``,
		`Your previous response for this component was rejected:`,
		`${err.message}`,
		``,
		`Regenerate the complete architecture summary JSON for the repository at the`,
		`current working directory (${item.repoDir}), fixing the reported problem.`,
		...(item.analyzerDir
			? [`The analyzer baseline facts remain at ${item.analyzerDir}/.`]
			: []),
		``,
		`Respond with ONLY the raw JSON object — no markdown code fences, no prose.`,
		`The JSON must be strictly valid: escape every double quote inside string values,`,
		`never use booleans or null for narrative fields, and match the same field`,
		`structure as before (component must be exactly ${JSON.stringify(item.key)}).`,
	].join("\n");
}

// ---------------------------------------------------------------------------
// Swappable data block 3: aggregation renderers
// (markdown shaped like the architecture template)
// ---------------------------------------------------------------------------

function renderComponentDoc(result) {
	const lines = [
		`# Component: ${result.component}`,
		``,
		`## Purpose`,
		``,
		result.purpose.detailed,
		``,
		`## Architectural Analysis`,
		``,
		result.architecturalAnalysis,
		``,
		`## Architecture Components`,
		``,
		`| Component | Type | Purpose |`,
		`|----|----|-------|`,
	];
	for (const c of result.architectureComponents) {
		lines.push(`| ${c.name} | ${c.type} | ${c.purpose} |`);
	}
	lines.push(``);
	for (const sub of result.subComponents) {
		lines.push(`## Sub-Component: ${sub.name}`, ``);
		if (sub.apiRoutes.length > 0) {
			lines.push(`**API Routes:**`, ``, `| Path | Methods |`, `|----|--------|`);
			for (const route of sub.apiRoutes) {
				lines.push(`| ${route.path} | ${route.methods.join(", ")} |`);
			}
			lines.push(``);
		}
		if (sub.upstreamDependencies.length > 0) {
			lines.push(`**Upstream Dependencies:** ${sub.upstreamDependencies.join(", ")}`, ``);
		}
		if (sub.configuration.length > 0) {
			lines.push(`**Configuration:**`, ``, ...sub.configuration.map((c) => `- ${c}`), ``);
		}
	}
	const { apisExposed } = result;
	lines.push(`## APIs Exposed`, ``);
	if (apisExposed.httpEndpoints.length > 0) {
		lines.push(`### HTTP Endpoints`, ``, `| Path | Methods | Description |`, `|----|---------|-------------|`);
		for (const ep of apisExposed.httpEndpoints) {
			lines.push(`| ${ep.path} | ${ep.methods.join(", ")} | ${ep.description} |`);
		}
		lines.push(``);
	}
	if (apisExposed.grpcServices.length > 0) {
		lines.push(`### gRPC Services`, ``);
		for (const svc of apisExposed.grpcServices) lines.push(`- **${svc.name}**: ${svc.description}`);
		lines.push(``);
	}
	if (apisExposed.customResourceDefinitions.length > 0) {
		lines.push(`### Custom Resource Definitions (CRDs)`, ``, `| Group | Version | Kind | Purpose |`, `|-----|-------|-----|-------|`);
		for (const crd of apisExposed.customResourceDefinitions) {
			lines.push(`| ${crd.group} | ${crd.version} | ${crd.kind} | ${crd.purpose} |`);
		}
		lines.push(``);
	}
	if (result.dependencies.external.length > 0 || result.dependencies.internalPlatform.length > 0) {
		lines.push(`## Dependencies`, ``);
		if (result.dependencies.external.length > 0) {
			lines.push(`**External:** ${result.dependencies.external.join(", ")}`, ``);
		}
		if (result.dependencies.internalPlatform.length > 0) {
			lines.push(`**Internal Platform:** ${result.dependencies.internalPlatform.join(", ")}`, ``);
		}
	}
	lines.push(`## Deployment`, ``, result.deployment.summary, ``);
	if (result.deployment.variants.length > 0) {
		lines.push(`**Variants:** ${result.deployment.variants.join(", ")}`, ``);
	}
	const { network } = result;
	lines.push(`## Network Architecture`, ``);
	for (const [label, entries] of [
		["Services", network.services],
		["Ingress", network.ingress],
		["Egress", network.egress],
	]) {
		if (entries.length > 0) lines.push(`**${label}:**`, ``, ...entries.map((e) => `- ${e}`), ``);
	}
	const { security } = result;
	lines.push(
		`## Security`,
		``,
		`- **Authentication:** ${security.authentication}`,
		`- **Authorization:** ${security.authorization}`,
		`- **FIPS Compliance:** ${security.fipsCompliance}`,
		``,
	);
	if (security.secrets.length > 0) {
		lines.push(`**Secrets:**`, ``, ...security.secrets.map((s) => `- ${s}`), ``);
	}
	const { multiTenancy } = result;
	if (multiTenancy.model.toLowerCase() !== "none" || multiTenancy.isolationMechanisms.length > 0) {
		lines.push(`## Multi-Tenancy`, ``, `**Model:** ${multiTenancy.model}`, ``);
		if (multiTenancy.isolationMechanisms.length > 0) {
			lines.push(`**Isolation Mechanisms:**`, ``, ...multiTenancy.isolationMechanisms.map((m) => `- ${m}`), ``);
		}
		if (multiTenancy.sharedServices.length > 0) {
			lines.push(`**Shared Services:** ${multiTenancy.sharedServices.join(", ")}`, ``);
		}
	}
	if (result.dataFlows.length > 0) {
		lines.push(`## Data Flows`, ``);
		for (const flow of result.dataFlows) lines.push(`- **${flow.name}**: ${flow.description}`);
		lines.push(``);
	}
	if (result.integrationPoints.length > 0) {
		lines.push(`## Integration Points`, ``);
		for (const ip of result.integrationPoints) lines.push(`- **${ip.name}**: ${ip.description}`);
		lines.push(``);
	}
	if (result.concerns.length > 0) {
		lines.push(`## Concerns`, ``, ...result.concerns.map((c) => `- ${c}`), ``);
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
		lines.push(`## ${result.component}`, ``, result.purpose.short, ``);
		if (result.concerns.length > 0) {
			lines.push(`**Concerns:**`, ``, ...result.concerns.map((c) => `- ${c}`), ``);
		}
	}
	return lines.join("\n") + "\n";
}

// ---------------------------------------------------------------------------
// Workflow body — primitive composition, no bespoke inline logic
// ---------------------------------------------------------------------------

const ALL_STAGES = ["fetch", "parse", "analyze", "generate", "collect", "diagrams", "platform"];
const HOST_SIDE_STAGES = new Set(["fetch", "parse"]);
const DEFAULT_STAGES = ["analyze", "generate", "collect", "platform"];

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

/** In-workflow analyze stage: validate the prebuilt analyzer baseline.
 * The arch-analyzer run itself is deterministic and host-side (P0);
 * generate depends on its outputs, so missing/invalid baselines must
 * fail loudly here, before any inference is spent. */
function validateAnalyzerBaselines(items, notes) {
	for (const item of items) {
		if (!item.analyzerDir) {
			notes.push(`${item.key}: no analyzer baseline; generate will analyze source without baseline facts`);
			continue;
		}
		const dir = path.resolve(item.analyzerDir);
		const jsonFile = path.join(dir, "component-architecture.json");
		const mdFile = path.join(dir, "analyzer_architecture.md");
		let facts;
		try {
			facts = JSON.parse(fs.readFileSync(jsonFile, "utf8"));
		} catch (err) {
			throw new Error(
				`arch-context analyze: ${item.key}: cannot read analyzer JSON (${jsonFile}): ${err.message}`,
			);
		}
		if (!fs.existsSync(mdFile) || fs.statSync(mdFile).size === 0) {
			throw new Error(
				`arch-context analyze: ${item.key}: missing or empty analyzer baseline ${mdFile}`,
			);
		}
		const factCount = Object.values(facts)
			.filter((v) => Array.isArray(v))
			.reduce((n, v) => n + v.length, 0);
		notes.push(`${item.key}: analyzer baseline validated (${factCount} facts)`);
	}
}

export default async function run(wf, input) {
	const cfg = validateInput(input, Input, "arch-context");
	const { stages, notes } = resolveStages(cfg);
	const items = loadWorkItems(cfg);
	const platform = cfg.platform || "unknown";

	const runAnalyze = stages.includes("analyze");
	const runGenerate = stages.includes("generate");
	const runCollect = stages.includes("collect");
	const runPlatform = stages.includes("platform");
	if ((runCollect || runPlatform) && !runGenerate) {
		throw new Error(
			"arch-context: 'collect'/'platform' without 'generate' needs durable journal replay (planned P5); include 'generate' in stages",
		);
	}

	// Phase 2c (in-workflow): validate the analyzer baseline generate depends on.
	if (runAnalyze) {
		validateAnalyzerBaselines(items, notes);
	}

	let summaries = [];
	if (runGenerate) {
		// Phase 3 — fan-out: one analysis child per component, in its
		// checkout, against the analyzer baseline. Real analysis runs
		// minutes, not seconds: default timeout 5 min, overridable via
		// input.timeoutMs (host default of 120s is for scripted children).
		summaries = await fanout(wf, items, {
			promptOf: promptFor,
			labelOf: (item) => `analyze:${item.key}`,
			schema: SummarySchema,
			cwdOf: (item) => item.repoDir,
			concurrency: cfg.concurrency ?? 2,
			timeoutMs: cfg.timeoutMs ?? 300000,
			// One corrective retry: models occasionally emit invalid JSON
			// (unescaped quotes in long outputs) or violate a leaf type;
			// the retry session carries the exact failure.
			retries: 1,
			retryPromptOf: retryPromptFor,
		});
		assertComplete(items, summaries, {
			itemKey: (item) => item.key,
			resultKey: (summary) => summary.component,
			workflow: "arch-context",
		});
	}

	// Phases 4+6 — per-component results and platform aggregate. Validated
	// results are published as markdown into <architectureDir>/<platform>/
	// (the repo's conventional output tree) in addition to the run dir's
	// machine-readable copies. Publishing renders from validated JSON —
	// children never write markdown, so published files are deterministic
	// functions of validated results.
	const archDir = path.resolve(cfg.architectureDir || "architecture", platform);
	if (runCollect && summaries.length > 0) {
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
		complete: runGenerate ? summaries.length === items.length : true,
		components: items.map((item) => item.key),
		notes,
		results: summaries,
		summary: runGenerate
			? `${summaries.length}/${items.length} components analyzed (${platform})`
			: `analyze-only: ${items.length} component(s) validated (${platform})`,
	};
	writeArtifact(wf, artifact);
	if (runPlatform && summaries.length > 0) {
		fs.writeFileSync(path.join(wf.runDir, "PLATFORM.md"), renderPlatformDoc(artifact));
		fs.mkdirSync(archDir, { recursive: true });
		fs.writeFileSync(path.join(archDir, "PLATFORM.md"), renderPlatformDoc(artifact));
	}
	if (runGenerate && !artifact.complete) {
		throw new Error(`arch-context: incomplete — ${summaries.length}/${items.length} components analyzed`);
	}
	return artifact;
}
