"""Phase 3: Generate component architecture documentation."""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from lib.agent_runner import (
    format_duration,
    get_model_display_name,
    run_agents_concurrently,
)
from lib.arch_doc import assemble_architecture_sections, ensure_arch_doc_binary
from lib.architecture_merge import merge_architecture_files
from lib.architecture_routing import load_architecture_agent_policy
from lib.architecture_surface_coverage import (
    build_surface_inventory,
    finalized_sidecar,
    load_sidecar,
    validate_surface_coverage,
)
from lib.cli import resolve_distribution
from lib.component_discovery import (
    apply_component_selection,
    apply_platform_overrides,
    get_component_map_metadata,
    read_component_map,
)
from lib.fetch import load_platform_config
from lib.insights import load_insight_artifact
from lib.phases.static_analysis import analyzer_output_dir
from lib.repo_naming import extra_repo_checkout_name
from lib.source_read_justifications import validate_source_read_justifications

CHANGE_RECORD_FILENAME = "ARCHITECTURE_CHANGES.md"
INSIGHT_ARTIFACT_FILENAME = "INSIGHTS_ARTIFACT.json"
SOURCE_READ_JUSTIFICATIONS_FILENAME = "SOURCE_READ_JUSTIFICATIONS.json"
SURFACE_INVENTORY_FILENAME = "SURFACE_INVENTORY.json"
SURFACE_COVERAGE_FILENAME = "SURFACE_COVERAGE.json"
PRESEED_FILENAME = "preseed.md"
CANDIDATE_FILENAME = "candidate.md"
MERGED_FILENAME = "merged.md"


def component_output_path(
    architecture_dir: str | Path, platform: str, component_key: str,
) -> Path:
    """Return the canonical generated document path for one component."""
    return (Path(architecture_dir) / platform / f"{component_key}.md").resolve()


def component_generation_dir(
    architecture_dir: str | Path, platform: str, component_key: str,
) -> Path:
    """Return the private sidecar directory for one generation run."""
    return (
        Path(architecture_dir) / platform / component_key / ".generation"
    ).resolve()


def component_generation_path(
    architecture_dir: str | Path,
    platform: str,
    component_key: str,
    filename: str,
) -> Path:
    """Return one private generation artifact path for a component."""
    return component_generation_dir(
        architecture_dir, platform, component_key,
    ) / filename


def _remove_legacy_component_outputs(
    architecture_dir: str | Path,
    platform: str,
    platform_config: dict,
    components,
) -> None:
    """Remove generated artifacts left under a component's former raw name.

    ``name_prefix`` changes the component key used by every downstream phase.
    Remove the old generated names during the transition so platform synthesis
    and diagram discovery cannot see both ``policy`` and ``praxis-policy``.
    """
    platform_dir = Path(architecture_dir) / platform
    diagrams_dir = platform_dir / "diagrams"
    for component in components.values():
        alias = extra_repo_checkout_name(
            platform_config, component.repo_org, component.repo_name,
        )
        if not alias or alias == component.repo_name or not component.repo_name:
            continue

        legacy_file = platform_dir / f"{component.repo_name}.md"
        if legacy_file.exists():
            legacy_file.unlink()
            print(f"  Removed legacy component document: {legacy_file}")

        for legacy_dir in (
            platform_dir / component.repo_name / ".analyzer",
            platform_dir / component.repo_name / ".generation",
        ):
            if legacy_dir.exists():
                shutil.rmtree(legacy_dir)
                print(f"  Removed legacy component artifacts: {legacy_dir}")
        legacy_component_dir = platform_dir / component.repo_name
        if legacy_component_dir.is_dir() and not any(legacy_component_dir.iterdir()):
            legacy_component_dir.rmdir()

        if diagrams_dir.exists():
            for diagram_file in diagrams_dir.glob(f"{component.repo_name}-*"):
                if diagram_file.is_file():
                    diagram_file.unlink()
                    print(f"  Removed legacy diagram: {diagram_file}")


async def run_generate_architecture_phase(args) -> None:
    """Run Phase 3: Generate architecture documentation."""
    print("\n" + "=" * 60)
    print("PHASE 3: Generating component architectures")
    print("=" * 60 + "\n")

    architecture_dir = getattr(args, "architecture_dir", "architecture")
    distribution = resolve_distribution(args.platform)

    # Load components from component-map.json
    components = read_component_map(args.platform, architecture_dir=architecture_dir)
    if components is None:
        print(f"ERROR: No component-map.json found for platform '{args.platform}'")
        print(f"Expected: {architecture_dir}/{args.platform}/component-map.json")
        print("\nRun discover-components first:")
        print(f"  uv run main.py discover-components --platform={args.platform}")
        return

    # Apply platform overrides (exclude_components, include_components, etc.)
    platform_config = load_platform_config(args.platform)
    if platform_config:
        checkouts_dir = getattr(args, "checkouts_dir", "checkouts")
        components = apply_platform_overrides(
            components,
            platform_config,
            checkouts_base=checkouts_dir,
        )
        _remove_legacy_component_outputs(
            architecture_dir, args.platform, platform_config, components,
        )
    components = apply_component_selection(
        components,
        get_component_map_metadata(args.platform, architecture_dir),
    )

    if not components:
        print("No components found with checkouts")
        return

    # Apply component filter if specified
    if args.component:
        if args.component in components:
            components = {args.component: components[args.component]}
            print(f"Filtered to single component: {args.component}\n")
        else:
            print(f"ERROR: Component '{args.component}' not found")
            print(f"Available components: {', '.join(sorted(components.keys()))}")
            return

    # Filter to components with actual checkouts on disk
    components = {
        k: v
        for k, v in components.items()
        if v.checkout_path and v.checkout_path.exists()
    }

    # Apply tier filter
    tier_filter = getattr(args, "tier", "all")
    if tier_filter == "significant":
        before = len(components)
        components = {
            k: v for k, v in components.items() if v.architecturally_significant
        }
        print(f"Tier filter 'significant': {before} -> {len(components)} components")
    elif tier_filter == "core":
        before = len(components)
        components = {
            k: v
            for k, v in components.items()
            if v.tier in ("core_platform", "optional_platform")
        }
        print(f"Tier filter 'core': {before} -> {len(components)} components")

    # Refresh has_architecture from the canonical architecture output tree.
    for component in components.values():
        arch_file = component_output_path(
            architecture_dir, args.platform, component.key,
        )
        component.has_architecture = arch_file.exists()

    # Handle --force: delete existing architecture documents
    if args.force:
        print("Force mode: Deleting existing component architecture files...\n")
        for component in components.values():
            arch_file = component_output_path(
                architecture_dir, args.platform, component.key,
            )
            if arch_file.exists():
                arch_file.unlink()
                print(f"  Deleted: {arch_file}")
                component.has_architecture = False  # Update status
            generation_dir = component_generation_dir(
                architecture_dir, args.platform, component.key,
            )
            if generation_dir.exists():
                shutil.rmtree(generation_dir)
        print()

    # Filter to components missing architecture
    # (unless --force, which already deleted them)
    missing_arch = [c for c in components.values() if not c.has_architecture]
    has_arch = [c for c in components.values() if c.has_architecture]

    print(f"Found {len(components)} components:")
    print(f"  Already documented: {len(has_arch)}")
    print(f"  Need architecture: {len(missing_arch)}")
    print()

    if not missing_arch:
        print("All components already have architecture documentation!")
        return

    # Prepare generation work. Every eligible component gets agent synthesis;
    # analyzer output is always preseeded for constrained routes.
    harness = getattr(args, "harness", "claude")
    model_display = (
        get_model_display_name(args.model, harness=harness)
        if harness != "claude"
        else get_model_display_name(args.model)
    )
    readiness_routing = getattr(args, "evidence_gated_merge", False)
    if readiness_routing:
        arch_doc_binary = ensure_arch_doc_binary()
        print(f"Using section assembler: {arch_doc_binary}")
    insight_version = getattr(args, "version", None) or args.platform
    work_items = []
    for component in sorted(missing_arch, key=lambda c: c.key):
        analyzer_root = analyzer_output_dir(
            architecture_dir, args.platform, component.key,
        )
        policy = load_architecture_agent_policy(
            component.checkout_path,
            readiness_routing=readiness_routing,
            analyzer_root=analyzer_root,
        )
        checkout_path = str(component.checkout_path.resolve())
        final_output_path = component_output_path(
            architecture_dir, args.platform, component.key,
        )
        generation_dir = component_generation_dir(
            architecture_dir, args.platform, component.key,
        )
        preseed_path = generation_dir / PRESEED_FILENAME
        candidate_path = generation_dir / CANDIDATE_FILENAME
        merged_path = generation_dir / MERGED_FILENAME
        change_path = generation_dir / CHANGE_RECORD_FILENAME
        insight_path = generation_dir / INSIGHT_ARTIFACT_FILENAME
        justification_path = generation_dir / SOURCE_READ_JUSTIFICATIONS_FILENAME
        surface_inventory_path = generation_dir / SURFACE_INVENTORY_FILENAME
        surface_coverage_path = generation_dir / SURFACE_COVERAGE_FILENAME
        surface_inventory = None
        analyzer_payload = None
        if policy.evidence_gated:
            try:
                analyzer_payload = json.loads(
                    (analyzer_root / "component-architecture.json").read_text()
                )
            except (OSError, json.JSONDecodeError):
                analyzer_payload = {}
            surface_inventory = build_surface_inventory(
                analyzer_payload,
                component=component.key,
            )
        prompt = ""
        prompt = (
            f"/repo-to-architecture-summary {checkout_path}"
            f" --analyzer-dir={analyzer_root}"
            f" --distribution={distribution}"
            f" --platform={distribution}"
            f" --version={insight_version}"
            f" --output={candidate_path}"
            f" --generated-by={model_display}"
            f" {policy.prompt_arguments()}"
            f" --read-justifications-output={justification_path}"
        )
        if policy.evidence_gated:
            prompt += f" --change-output={change_path}"
            prompt += f" --insights-output={insight_path}"
            prompt += f" --surface-inventory={surface_inventory_path}"
            prompt += f" --surface-coverage-output={surface_coverage_path}"

        output_paths = [
            candidate_path,
            change_path,
            insight_path,
            justification_path,
        ]
        if policy.evidence_gated:
            output_paths.append(surface_coverage_path)

        job = {
            "name": f"{component.key}",
            "cwd": ".",
            "prompt": prompt,
            "repo": f"{component.repo_org}/{component.repo_name}",
            "checkout_path": component.checkout_path,
            "analyzer_root": analyzer_root,
            "output_path": candidate_path,
            "preseed_path": preseed_path,
            "candidate_path": candidate_path,
            "merged_path": merged_path,
            "final_output_path": final_output_path,
            "output_paths": tuple(output_paths),
            "input_paths": (
                (surface_inventory_path,) if policy.evidence_gated else ()
            ),
            "change_path": change_path,
            "insight_path": insight_path,
            "justification_path": justification_path,
            "surface_inventory_path": surface_inventory_path,
            "surface_coverage_path": surface_coverage_path,
            "surface_inventory": surface_inventory,
            "surface_analyzer": analyzer_payload,
            "agent_policy": policy.to_dict(),
            "phase_timings": {},
        }
        work_items.append(job)

    # Apply limit if specified
    if args.limit:
        work_items = work_items[: args.limit]
        print(f"Limited to first {args.limit} component(s)\n")

    jobs = []
    for item in work_items:
        policy = item["agent_policy"]
        analyzer_root = Path(item["analyzer_root"])
        analyzer_file = analyzer_root / "analyzer_architecture.md"
        generation_dir = component_generation_dir(
            architecture_dir, args.platform, item["name"],
        )
        preseed_file = Path(item["preseed_path"])
        output_file = Path(item["candidate_path"])
        merged_file = Path(item["merged_path"])
        preseed_started = time.monotonic()
        generation_dir.mkdir(parents=True, exist_ok=True)
        for artifact in (
            preseed_file,
            output_file,
            merged_file,
            Path(item["change_path"]),
            Path(item["insight_path"]),
            Path(item["justification_path"]),
            Path(item["surface_inventory_path"]),
            Path(item["surface_coverage_path"]),
        ):
            if artifact.exists():
                artifact.unlink()
        if policy.get("route") in ('synthesis', 'partial'):
            shutil.copy2(analyzer_file, preseed_file)
            shutil.copy2(preseed_file, output_file)
            inventory = item.get("surface_inventory")
            if isinstance(inventory, dict):
                inventory_text = json.dumps(
                    inventory, indent=2, sort_keys=True
                ) + "\n"
                Path(item["surface_inventory_path"]).write_text(inventory_text)
                Path(item["surface_coverage_path"]).write_text(inventory_text)
        item["phase_timings"]["preseed_seconds"] = (
            time.monotonic() - preseed_started
        )
        jobs.append(item)

    # Display prepared jobs
    print(
        f"Prepared {len(jobs)} agent job(s):\n"
    )
    for i, job in enumerate(jobs, 1):
        print(f"{i:2d}. {job['name']:30s} {job['repo']}")
        print(f"    cwd: {job['cwd']}")
        print()

    # Create logs directory
    log_dir = Path(getattr(args, "log_dir", "logs/generate-architecture"))
    log_dir.mkdir(parents=True, exist_ok=True)
    print(f"Logs will be written to: {log_dir}\n")

    print(f"{'=' * 60}")
    print(f"Ready to process {len(work_items)} component(s)")
    print(f"Max concurrent agents: {args.max_concurrent}")
    print(f"Harness: {harness}")
    selected_model = args.model or (
        "opus" if harness == "claude" else "configured default"
    )
    print(f"Model: {selected_model}")
    print(f"{'=' * 60}\n")

    strace_prefix = (
        f"{args.platform}-generate-architecture"
        if getattr(args, "strace", False)
        else None
    )
    results = []
    if jobs:
        results = await run_agents_concurrently(
            jobs,
            log_dir,
            args.model,
            args.max_concurrent,
            enable_skills=True,
            strace_prefix=strace_prefix,
            phase_label="PHASE 3 · Component architecture synthesis",
            on_result=lambda index, job, result: _postprocess_agent_result(
                job,
                result,
                log_dir,
                readiness_routing=readiness_routing,
                platform=distribution,
                version=insight_version,
            ),
            harness=harness,
        )

    # Test doubles and older callers may not invoke the per-job callback.
    # Keep a compatibility pass so every successful result is still validated,
    # merged/promoted, and reported before the phase summary.
    finalized_results = []
    for job, result in zip(jobs, results):
        if isinstance(result, dict) and result.get("_postprocessed"):
            finalized_results.append(result)
            continue
        finalized_results.append(
            await _postprocess_agent_result(
                job,
                result,
                log_dir,
                readiness_routing=readiness_routing,
                platform=distribution,
                version=insight_version,
            )
        )
    results = finalized_results
    result_by_name = dict(zip((job["name"] for job in jobs), results))
    all_results = [result_by_name[item["name"]] for item in work_items]

    # Summary
    successful = [r for r in all_results if isinstance(r, dict) and r.get("success")]
    failed = [r for r in all_results if isinstance(r, dict) and not r.get("success")]
    exceptions = [r for r in all_results if isinstance(r, Exception)]

    print("\n" + "=" * 60)
    print("ARCHITECTURE GENERATION COMPLETE")
    print("=" * 60)
    print(f"Total components: {len(work_items)}")
    print(f"Agent invocations: {len(jobs)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    if exceptions:
        print(f"Exceptions: {len(exceptions)}")

    if failed:
        print("\nFailed components:")
        for r in failed:
            print(f"  x {r['name']}: {r.get('error', 'unknown error')}")
            if r.get("log_file"):
                print(f"    Log: {r['log_file']}")

    if exceptions:
        print("\nComponents with exceptions:")
        for i, exc in enumerate(exceptions):
            print(f"  x Exception {i + 1}: {exc}")

    print(f"\nAll generation logs available in: {log_dir}")
    print("=" * 60)


def _validate_generated_architecture(path: Path) -> None:
    """Validate a generated component document and raise on failure."""

    validator = (
        Path(__file__).resolve().parents[2]
        / ".claude/skills/repo-to-architecture-summary/scripts/validate_architecture.py"
    )
    validation = subprocess.run(
        [sys.executable, str(validator), str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if validation.returncode != 0:
        raise ValueError(
            "architecture validation failed: "
            + (validation.stdout + validation.stderr).strip()
        )


def _promote_component_output(source: Path, target: Path) -> None:
    """Atomically replace the canonical component document with source."""

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp")
    content = source.read_text()
    expected_heading = f"# Component: {target.stem}"
    lines = content.splitlines(keepends=True)
    if lines and lines[0].startswith("# Component:"):
        newline = "\n" if lines[0].endswith("\n") else ""
        lines[0] = expected_heading + newline
        content = "".join(lines)
    temporary.write_text(content)
    temporary.replace(target)


def _recover_agent_result(job, result, log_dir: Path):
    """Mark a crashed agent successful if it produced a real candidate delta."""

    if isinstance(result, dict) and result.get("success"):
        return result
    candidate = Path(job["candidate_path"])
    preseed = Path(job["preseed_path"]) if job.get("preseed_path") else Path()
    has_agent_delta, no_delta_reason = _candidate_has_substantive_delta(
        candidate, preseed
    )
    if not has_agent_delta:
        if isinstance(result, dict) and not result.get("error"):
            result["error"] = no_delta_reason
        return result
    if isinstance(result, Exception):
        recovered = {
            "name": job["name"],
            "success": True,
            "recovered": True,
            "error": str(result),
            "log_file": str(log_dir / f"{job['name'].replace('/', '_')}.log"),
            "duration_seconds": 0,
        }
    else:
        recovered = dict(result)
        recovered["success"] = True
        recovered["recovered"] = True
    err = str(recovered.get("error", ""))[:80]
    print(f"Recovered: {job['name']}: crashed ({err}) but output file exists")
    return recovered


def _candidate_has_substantive_delta(
    candidate: Path, preseed: Path,
) -> tuple[bool, str]:
    """Return whether candidate differs from the preseed beyond run metadata."""

    if not candidate.is_file():
        return False, f"agent produced no candidate output: {candidate}"
    if not preseed.is_file():
        return True, ""

    candidate_text = candidate.read_text(errors="ignore")
    preseed_text = preseed.read_text(errors="ignore")
    if _normalize_generated_candidate(candidate_text) == _normalize_generated_candidate(
        preseed_text
    ):
        no_delta = (
            "agent produced no substantive candidate changes; "
            "candidate matches preseed"
        )
        return (
            False,
            no_delta,
        )
    return True, ""


def _normalize_generated_candidate(text: str) -> str:
    """Normalize generation metadata before comparing preseed/candidate bodies."""

    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- **Generated By**:"):
            continue
        if stripped.startswith("*Generated in ") and stripped.endswith("total)*"):
            continue
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


def _append_generation_duration(job: dict, result: dict) -> None:
    """Append the durable generation duration footer to the final document."""

    if not result.get("success"):
        return
    final_output = Path(job["final_output_path"])
    if not final_output.exists():
        return
    elapsed = result.get("duration_seconds", 0)
    duration_line = (
        f"\n---\n*Generated in {format_duration(elapsed)} ({elapsed:.0f}s total)*\n"
    )
    with open(final_output, "a") as f:
        f.write(duration_line)


async def _postprocess_agent_result(
    job: dict,
    result,
    log_dir: Path,
    *,
    readiness_routing: bool,
    platform: str,
    version: str,
):
    """Validate, merge/promote, and report one completed agent result."""

    result = _recover_agent_result(job, result, log_dir)
    if not isinstance(result, dict):
        return result
    if result.get("_postprocessed"):
        return result
    result["routing"] = job["agent_policy"]
    result.setdefault("phase_timings", {}).update(
        job.get("phase_timings", {})
    )
    validation_started = time.monotonic()
    result["source_read_justifications"] = validate_source_read_justifications(
        Path(job["justification_path"]),
        result.get("telemetry"),
        repair_missing_observed=True,
        component=job["name"],
        gap_categories=job.get("agent_policy", {}).get("gap_categories", ()),
    )
    result["phase_timings"][
        "source_read_justification_validation_seconds"
    ] = (time.monotonic() - validation_started)
    warnings = result["source_read_justifications"]["warnings"]
    if warnings:
        print(
            f"Read-justification warning: {job['name']}: "
            f"{'; '.join(warnings)}"
        )
    if readiness_routing:
        _merge_agent_outputs(
            [job],
            [result],
            log_dir,
            platform=platform,
            version=version,
        )
    _promote_unmerged_agent_outputs([job], [result])
    _validate_and_archive_surface_coverage(job, result, log_dir)
    _append_generation_duration(job, result)
    result["_postprocessed"] = True
    _write_agent_run_reports([job], [result], log_dir)
    return result


def _promote_unmerged_agent_outputs(jobs, results) -> None:
    """Validate and promote successful non-merge candidate outputs."""

    for job, result in zip(jobs, results):
        if not isinstance(result, dict) or not result.get("success"):
            continue
        if result.get("merge"):
            continue
        candidate = Path(job["candidate_path"])
        final_output = Path(job["final_output_path"])
        promotion_started = time.monotonic()
        try:
            if not candidate.is_file():
                raise FileNotFoundError(f"missing agent candidate: {candidate}")
            _validate_generated_architecture(candidate)
            _promote_component_output(candidate, final_output)
            result["output"] = {
                "candidate": str(candidate),
                "final": str(final_output),
                "duration_seconds": time.monotonic() - promotion_started,
            }
        except Exception as error:
            result["success"] = False
            result["error"] = f"architecture promotion failed: {error}"
            result["output"] = {
                "candidate": str(candidate),
                "final": str(final_output),
                "error": str(error),
                "duration_seconds": time.monotonic() - promotion_started,
            }


def _merge_agent_outputs(
    jobs,
    results,
    log_dir: Path,
    *,
    platform: str,
    version: str,
) -> None:
    """Archive, evidence-gate, and validate successful agent candidates."""

    validator = (
        Path(__file__).resolve().parents[2]
        / ".claude/skills/repo-to-architecture-summary/scripts/validate_architecture.py"
    )
    for job, result in zip(jobs, results):
        if not isinstance(result, dict) or not result.get("success"):
            continue
        if job.get("agent_policy", {}).get("route") not in ('synthesis', 'partial'):
            continue
        checkout = Path(job["checkout_path"])
        analyzer = (
            Path(job.get("analyzer_root", checkout))
            / "analyzer_architecture.md"
        )
        candidate = Path(job.get("candidate_path", job["output_path"]))
        merged = Path(job.get("merged_path", job["output_path"]))
        final_output = Path(job.get("final_output_path", job["output_path"]))
        changes = Path(job["change_path"])
        name = str(job["name"]).replace("/", "_")
        raw_candidate = log_dir / f"{name}.candidate.md"
        archived_changes = log_dir / f"{name}.changes.md"
        report_json = log_dir / f"{name}.merge.json"
        report_markdown = log_dir / f"{name}.merge.md"
        merge_started = time.monotonic()
        try:
            if not analyzer.is_file():
                raise FileNotFoundError(f"missing analyzer baseline: {analyzer}")
            if not candidate.is_file():
                raise FileNotFoundError(f"missing agent candidate: {candidate}")
            if job.get("preseed_path"):
                has_agent_delta, no_delta_reason = _candidate_has_substantive_delta(
                    candidate, Path(job["preseed_path"])
                )
                if not has_agent_delta:
                    raise ValueError(no_delta_reason)
            shutil.copy2(candidate, raw_candidate)
            if changes.is_file():
                shutil.copy2(changes, archived_changes)
            merge_apply_started = time.monotonic()
            merge_result = merge_architecture_files(
                analyzer,
                raw_candidate,
                merged,
                changes=archived_changes if archived_changes.is_file() else None,
                report_json=report_json,
                report_markdown=report_markdown,
                component=job["name"],
                allowed_change_categories=tuple(
                    job.get("agent_policy", {}).get("gap_categories", ())
                ),
                section_assembler=assemble_architecture_sections,
            )
            merge_apply_seconds = time.monotonic() - merge_apply_started
            validation_started = time.monotonic()
            validation = subprocess.run(
                [sys.executable, str(validator), str(merged)],
                check=False,
                capture_output=True,
                text=True,
            )
            validation_seconds = time.monotonic() - validation_started
            if validation.returncode != 0:
                raise ValueError(
                    "merged architecture validation failed: "
                    + (validation.stdout + validation.stderr).strip()
                )
            _promote_component_output(merged, final_output)
            result["merge"] = {
                "candidate": str(candidate),
                "merged": str(merged),
                "final": str(final_output),
                "raw_candidate": str(raw_candidate),
                "changes": (
                    str(archived_changes) if archived_changes.is_file() else None
                ),
                "report_json": str(report_json),
                "report_markdown": str(report_markdown),
                "counts": merge_result.counts,
                "duration_seconds": time.monotonic() - merge_started,
                "merge_apply_seconds": merge_apply_seconds,
                "validation_seconds": validation_seconds,
            }
            print(
                f"Merged: {job['name']} "
                f"({json.dumps(merge_result.counts, sort_keys=True)})"
            )
        except Exception as error:
            original_route = job.get("agent_policy", {}).get("route", "unknown")
            fallback_reason = f"restricted-route merge failed: {error}"
            shutil.copy2(analyzer, merged)
            result["success"] = False
            result["error"] = fallback_reason
            result["merge"] = {
                "candidate": str(candidate),
                "merged": str(merged),
                "final": str(final_output),
                "duration_seconds": time.monotonic() - merge_started,
                "error": str(error),
                "fallback": "analyzer-baseline-not-promoted",
            }
            result["fallback"] = {
                "route": "analyzer-baseline",
                "reason": fallback_reason,
                "original_route": original_route,
                "action": "analyzer-baseline-not-promoted",
            }
            print(
                f"Merge fallback: {job['name']}: {error} "
                f"(kept analyzer baseline in generation artifacts; no final promotion)"
            )

        if not result.get("success"):
            continue
        if result.get("fallback"):
            result["insights"] = None
            continue
        insight_file = Path(job["insight_path"])
        archived_insights = log_dir / f"{name}.insights.json"
        insight_started = time.monotonic()
        try:
            if not insight_file.is_file():
                raise FileNotFoundError(
                    f"missing insight artifact: {insight_file}"
                )
            shutil.copy2(insight_file, archived_insights)
            artifact, insight_errors = load_insight_artifact(archived_insights)
            if insight_errors:
                raise ValueError(
                    "insight artifact validation failed: "
                    + "; ".join(insight_errors)
                )
            archived_insights.write_text(artifact.to_json())
            result["insights"] = {
                "artifact_path": str(archived_insights),
                "insight_count": len(artifact.insights),
                "validation_errors": [],
                "archive_validation_seconds": time.monotonic() - insight_started,
            }
            print(
                f"Insights: {job['name']} "
                f"({len(artifact.insights)} insight(s))"
            )
        except Exception as error:
            # Insight artifacts are supplementary, non-authoritative output.
            # A malformed or missing artifact must not turn a successfully
            # generated architecture document into a failed component run.
            # Preserve malformed agent output separately for diagnosis and
            # replace the report artifact with a valid empty artifact so all
            # downstream consumers have a stable shape.
            if archived_insights.is_file():
                invalid_insights = log_dir / f"{name}.insights.invalid.json"
                shutil.copy2(archived_insights, invalid_insights)
            fallback_artifact = {
                "schema_version": 1,
                "component": job["name"],
                "platform": platform,
                "version": version,
                "insights": [],
                "metadata": {
                    "fallback": "empty-artifact",
                    "validation_error": str(error),
                },
            }
            archived_insights.write_text(
                json.dumps(fallback_artifact, indent=2) + "\n"
            )
            result["insights"] = {
                "error": str(error),
                "artifact_path": str(archived_insights),
                "insight_count": 0,
                "validation_errors": [str(error)],
                "fallback": "empty-artifact",
                "archive_validation_seconds": time.monotonic() - insight_started,
            }
            print(f"Insight artifact failed: {job['name']}: {error}")


def _observed_read_records_from_telemetry(
    telemetry: object,
) -> list[dict[str, object]] | None:
    """Translate real harness observations without trusting the agent ledger."""

    if not isinstance(telemetry, dict):
        return None
    observation = telemetry.get("source_read_observation")
    ranges = telemetry.get("source_read_ranges")
    if observation not in {
        "claude-pre-tool-use-hooks",
        "successful-sdk-read-actions",
    } or not isinstance(ranges, list):
        return None
    result: list[dict[str, object]] = []
    for item in ranges:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            continue
        offset = item.get("offset")
        limit = item.get("limit")
        if isinstance(offset, int) and isinstance(limit, int) and limit > 0:
            line_range = f"{offset}-{offset + limit - 1}"
        elif isinstance(offset, int):
            line_range = f"{offset}-unknown"
        else:
            line_range = "unknown"
        result.append(
            {
                "path": item["path"],
                "line_range": line_range,
                "outcome": "observed-by-harness",
            }
        )
    return result


def _validate_and_archive_surface_coverage(
    job: dict,
    result: dict,
    log_dir: Path,
) -> None:
    """Validate surface accounting against the document selected for promotion."""

    inventory = job.get("surface_inventory")
    if not isinstance(inventory, dict):
        result["surface_coverage"] = None
        return

    started = time.monotonic()
    sidecar_path = Path(job["surface_coverage_path"])
    sidecar = load_sidecar(sidecar_path)
    promoted_path = Path(job["final_output_path"])
    candidate_path = Path(job["candidate_path"])
    report = validate_surface_coverage(
        inventory=inventory,
        sidecar=sidecar,
        promoted_document=promoted_path if promoted_path.is_file() else None,
        candidate_document=candidate_path if candidate_path.is_file() else None,
        observed_reads=_observed_read_records_from_telemetry(
            result.get("telemetry")
        ),
        analyzer_document=job.get("surface_analyzer"),
        source_root=job.get("checkout_path"),
    )
    if not report["structural_valid"] and sidecar_path.is_file():
        invalid_path = log_dir / (
            f"{str(job['name']).replace('/', '_')}.coverage.invalid.json"
        )
        shutil.copy2(sidecar_path, invalid_path)
    enriched = finalized_sidecar(sidecar, report, inventory=inventory)
    sidecar_path.write_text(json.dumps(enriched, indent=2, sort_keys=True) + "\n")
    name = str(job["name"]).replace("/", "_")
    archived_path = log_dir / f"{name}.coverage.json"
    shutil.copy2(sidecar_path, archived_path)
    result["phase_timings"]["surface_coverage_validation_seconds"] = (
        time.monotonic() - started
    )
    result["surface_coverage"] = {
        "artifact_path": str(archived_path),
        "structural_valid": report["structural_valid"],
        "structural_errors": report["structural_errors"],
        "coverage_accounting": report["coverage_accounting"],
        "summary": report["summary"],
        "read_observation": report["read_observation"],
        "unresolved_safety_critical_surfaces": report[
            "unresolved_safety_critical_surfaces"
        ],
        "validator_findings": report["validator_findings"],
        "warning_count": report["warning_count"],
        "status": report["status"],
    }
    if report["warning_count"]:
        classifications = sorted(
            {
                finding["classification"]
                for finding in report["validator_findings"]
            }
        )
        details = ", ".join(classifications) or "structural-invalid"
        print(
            f"Surface-coverage warning: {job['name']}: "
            f"{report['warning_count']} finding(s) ({details})"
        )


def _runtime_breakdown(result: dict) -> dict:
    """Return durable diagnostic timing/count buckets for one agent run."""

    telemetry = result.get("telemetry") or {}
    phase_timings = result.get("phase_timings") or {}
    merge = result.get("merge") or {}
    insights = result.get("insights") or {}
    api_ms = telemetry.get("duration_api_ms")
    agent_api_seconds = (
        round(float(api_ms) / 1000, 3)
        if isinstance(api_ms, int | float)
        else None
    )
    return {
        "total_seconds": result.get("duration_seconds"),
        "agent_api_seconds": agent_api_seconds,
        "orchestrator_seconds": {
            "preseed": phase_timings.get("preseed_seconds"),
            "merge_total": merge.get("duration_seconds"),
            "merge_apply": merge.get("merge_apply_seconds"),
            "merged_document_validation": merge.get("validation_seconds"),
            "insight_archive_validation": insights.get(
                "archive_validation_seconds"
            ),
            "source_read_justification_validation": phase_timings.get(
                "source_read_justification_validation_seconds"
            ),
            "surface_coverage_validation": phase_timings.get(
                "surface_coverage_validation_seconds"
            ),
        },
        "agent_activity_counts": {
            "analyzer_context_reads": (
                telemetry.get("tool_calls_by_activity", {})
                .get("analyzer_context_read", 0)
            ),
            "surface_inventory_reads": (
                telemetry.get("tool_calls_by_activity", {})
                .get("planning_input_read", 0)
            ),
            "targeted_source_reads": telemetry.get("source_read_operations", 0),
            "source_read_budget_exceeded": telemetry.get(
                "source_read_budget_exceeded", 0
            ),
            "discovery_budget_exceeded": telemetry.get(
                "discovery_budget_exceeded", 0
            ),
            "targeted_discovery_calls": (
                telemetry.get("tool_calls_by_activity", {})
                .get("targeted_discovery", 0)
            ),
            "architecture_output_edits": (
                telemetry.get("tool_calls_by_activity", {})
                .get("architecture_output_edit", 0)
            ),
            "sidecar_writes": (
                telemetry.get("tool_calls_by_activity", {})
                .get("sidecar_write", 0)
            ),
            "denied_calls": telemetry.get("denied_tool_calls", 0),
        },
        "denied_calls_by_category": telemetry.get(
            "denied_tool_calls_by_category", {}
        ),
    }


def _write_agent_run_reports(jobs, results, log_dir: Path) -> None:
    """Persist routing, usage, and merge telemetry for corpus aggregation."""

    for job, result in zip(jobs, results):
        if not isinstance(result, dict):
            continue
        name = str(job["name"]).replace("/", "_")
        report = {
            "schema_version": 1,
            "component": job["name"],
            "success": bool(result.get("success")),
            "error": result.get("error"),
            "duration_seconds": result.get("duration_seconds"),
            "routing": result.get("routing", job.get("agent_policy", {})),
            "runtime_breakdown": _runtime_breakdown(result),
            "phase_timings": result.get("phase_timings", {}),
            "telemetry": result.get("telemetry", {}),
            "merge": result.get("merge"),
            "insights": result.get("insights"),
            "source_read_justifications": result.get("source_read_justifications"),
            "surface_coverage": result.get("surface_coverage"),
            "fallback": result.get("fallback"),
            "log_file": result.get("log_file"),
        }
        (log_dir / f"{name}.run.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
