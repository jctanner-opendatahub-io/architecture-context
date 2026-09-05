"""Run discovery in a disposable workspace and promote validated output."""

import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

from lib.skill_paths import resolve_skill_file


async def run_isolated_discovery(run_agent, *, platform, architecture_dir, **job):
    """Keep the pipeline repository and previous results out of worker context."""
    if Path(platform).name != platform or platform in {".", ".."}:
        raise ValueError(f"Invalid platform: {platform!r}")
    destination = Path(architecture_dir).resolve() / platform / "component-map.json"
    log_file = Path(job["log_dir"]).resolve() / f"{job['name']}.log"
    with tempfile.TemporaryDirectory(prefix="architecture-discovery-") as temp:
        workspace = Path(temp)
        skill_dir = workspace / ".agents/skills/discover-components"
        shutil.copytree(
            resolve_skill_file("discover-components").parent,
            skill_dir,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        output_dir = workspace / "architecture"
        output_dir.mkdir()
        # Preserve the slash invocation while replacing its output argument.
        job["prompt"] = job["prompt"].replace(
            f"--architecture-dir={architecture_dir}",
            f"--architecture-dir={output_dir}",
            1,
        )
        job["prompt"] += (
            "\nExecute discover-components directly using the supplied checkout "
            "roots as evidence. Build a fresh map; do not read or reuse previous "
            "component maps or architecture documents. Exclusions are supplied "
            "by the parent; sync-config promotion and provenance are parent work. "
            "Only write the requested component-map.json and temporary scratch "
            "files in this workspace. Do not inspect or modify pipeline code, "
            "plans, work ledgers, or session logs, or launch main.py. "
            f"The skill directory (CLAUDE_SKILL_DIR) is {skill_dir}. "
            "Use its scripts and references directly."
        )
        job["cwd"] = str(workspace)
        job["log_dir"] = Path(job["log_dir"]).resolve()
        result = await run_agent(**job)
        if not result.get("success"):
            return result

        candidate = output_dir / platform / "component-map.json"
        try:
            if (
                candidate.is_symlink()
                or not candidate.resolve().is_relative_to(workspace)
            ):
                raise ValueError("Discovery output must stay in its workspace")
            validator = resolve_skill_file("discover-components").parent / (
                "scripts/validate_component_map.py"
            )
            spec = importlib.util.spec_from_file_location(
                "discovery_validator", validator,
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            errors = module.validate(str(candidate))
            with log_file.open("a") as log:
                log.write("\nPARENT VALIDATION:\n")
                log.write("\n".join(errors) if errors else "VALIDATION PASSED")
                log.write("\n")
            if errors:
                raise ValueError("Discovery output failed parent schema validation")
            data = json.loads(candidate.read_text())
            if data["metadata"]["platform"] != platform:
                raise ValueError("Discovery output platform does not match request")
            # A sibling temporary file makes replacement atomic across filesystems.
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                dir=destination.parent, delete=False,
            ) as staged:
                staged_path = Path(staged.name)
            try:
                shutil.copyfile(candidate, staged_path)
                staged_path.replace(destination)
            finally:
                staged_path.unlink(missing_ok=True)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            result = {**result, "success": False, "error": str(exc)}
        return result
