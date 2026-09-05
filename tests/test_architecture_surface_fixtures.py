"""Regression checks for source-verified architecture surface fixtures."""

import json
from pathlib import Path

ROOT = Path(__file__).parent
FIXTURE_DIR = ROOT / "fixtures" / "architecture_surface_coverage" / "rhods_operator"
SOURCE_PATH = FIXTURE_DIR / "metrics_authentication.go"
EXPECTED_PATH = FIXTURE_DIR / "metrics_authentication.expected.json"
BEHAVIOR_EXPECTED_PATH = FIXTURE_DIR / "behavioral_surfaces.expected.json"
CORPUS_PATH = FIXTURE_DIR.parent / "corpus.json"


def _load_expected() -> dict:
    return json.loads(EXPECTED_PATH.read_text())


def test_metrics_fixture_manifest_integrity() -> None:
    expected = _load_expected()
    assert SOURCE_PATH.read_text()

    assert expected["fixture_version"] == "architecture-surface-regression/v1"
    assert expected["source_revision"] == "4ada791819c522a4cda54f9029ab3e4056ed31ed"
    assert len(expected["source_revision"]) == 40
    int(expected["source_revision"], 16)
    assert expected["source_path"] == "cmd/main.go"
    assert expected["source_range"] == "480-500"
    assert expected["component_role"] == "operator"
    assert expected["surface_id"] == "authentication.metrics-enforcement"
    assert expected["parent_category"] == "authentication"
    assert expected["question"]
    assert expected["priority"] == "required"
    assert expected["applicability_basis"]

    locations = expected["candidate_locations"]
    assert isinstance(locations, list) and locations
    assert {location["path"] for location in locations} == {expected["source_path"]}
    assert {location["line_range"] for location in locations} == {
        expected["source_range"]
    }

    evidence = expected["expected_evidence"]
    assert set(evidence) == {
        "serving_surface",
        "condition",
        "enforcement_provider",
        "authentication",
        "authorization",
    }
    assert all(evidence.values())
    assert "unconditionally" in expected["forbidden_claims"][0]
    assert any("FIPS" in claim for claim in expected["forbidden_claims"])


def test_metrics_fixture_preserves_conditional_enforcement_flow() -> None:
    source = SOURCE_PATH.read_text()

    secure_guard = "if oconfig.MetricsSecure {"
    filter_assignment = (
        "opts.FilterProvider = filters.WithAuthenticationAndAuthorization"
    )
    guard_start = source.index(secure_guard)
    guard_end = source.index("\n\t\t\t}", guard_start) + 1
    guard_body = source[guard_start:guard_end]

    assert "Metrics: func() ctrlmetrics.Options" in source
    assert "opts := ctrlmetrics.Options{" in source
    assert "BindAddress:   oconfig.MetricsAddr" in source
    assert "SecureServing: oconfig.MetricsSecure" in source
    assert "TLSOpts:       tlsOpts" in source
    assert filter_assignment in guard_body
    assert source.count(filter_assignment) == 1
    assert "if oconfig.MetricsCertPath != \"\" {" in source
    assert "opts.CertDir = oconfig.MetricsCertPath" in source
    assert "opts.CertName = oconfig.MetricsCertName" in source
    assert "opts.KeyName = oconfig.MetricsCertKey" in source
    assert "}()," in source


def test_metrics_fixture_classifies_all_regression_cases() -> None:
    expected = _load_expected()
    cases = expected["cases"]
    assert len(cases) == 4
    assert {case["name"] for case in cases} == {
        "evidence_unavailable",
        "evidence_available_omitted",
        "explicit_unresolved",
        "unsupported_claim",
    }

    by_name = {case["name"]: case for case in cases}
    assert by_name["evidence_unavailable"]["disposition"] == "unresolved"
    assert by_name["evidence_unavailable"]["result"] == "extraction_gap"
    assert by_name["evidence_unavailable"]["candidate_source_present"] is False

    omitted = by_name["evidence_available_omitted"]
    assert omitted["disposition"] == "unresolved"
    assert omitted["result"] == "synthesis_omission"
    assert omitted["candidate_source_present"] is True
    assert omitted["evidence_present"] is True
    assert omitted["candidate_output_omits_behavior"] is True

    unresolved = by_name["explicit_unresolved"]
    assert unresolved["disposition"] == "unresolved"
    assert unresolved["result"] == "unresolved"
    assert unresolved["remaining_question"]
    assert unresolved["unsupported_claim_warning"] is False

    unsupported = by_name["unsupported_claim"]
    assert unsupported["disposition"] == "documented"
    assert unsupported["claim_support"] == "unsupported"
    assert unsupported["result"] == "unverifiable_coverage_claim"
    assert "unconditionally" in unsupported["candidate_claim"]
    assert unsupported["unsupported_claim_warning"] is True


def test_named_watch_gateway_and_fips_fixtures_preserve_source_semantics() -> None:
    expected = json.loads(BEHAVIOR_EXPECTED_PATH.read_text())
    watches = (FIXTURE_DIR / "named_namespace_watches.go").read_text()
    gateway = (FIXTURE_DIR / "gateway_auth_modes.go").read_text()
    fips = (FIXTURE_DIR / "fips_signal.yaml").read_text()

    assert expected["source_revision"] == (
        "4ada791819c522a4cda54f9029ab3e4056ed31ed"
    )
    metrics_expectation = expected["surfaces"][
        "authentication.metrics-enforcement"
    ]
    assert metrics_expectation == {
        "behavior_kind": "conditional-metrics-enforcement",
        "status": "observed",
        "serving_surface": "controller-runtime metrics serving surface",
        "configuration_branch": "oconfig.MetricsSecure is true",
        "enforcement_provider": (
            "filters.WithAuthenticationAndAuthorization"
        ),
        "source_range": "cmd/main.go:485-500",
    }
    watch_expectation = expected["surfaces"][
        "controller.named-resource-watches"
    ]
    assert watch_expectation["controller_identity"] == (
        "internal/controller/services/auth.ServiceHandler"
    )
    assert sorted(watch_expectation["literal_names"]) == [
        "kuadrant-system",
        "models-as-a-service",
    ]
    assert watch_expectation["event_target"] == (
        "services.platform.opendatahub.io/v1alpha1/Auth/auth"
    )
    assert watch_expectation["source_ranges"] == [
        "internal/controller/services/auth/auth_controller.go:63-69",
        "internal/controller/services/auth/auth_controller.go:70-76",
    ]
    for namespace in watch_expectation["literal_names"]:
        assert f'CreatedOrUpdatedOrDeletedNamed("{namespace}")' in watches
    assert watches.count("Watches(") == 2
    assert watches.count("handlers.ToNamed(serviceapi.AuthInstanceName)") == 2

    for mode in ("AuthModeOIDC", "AuthModeIntegratedOAuth", "AuthModeNone"):
        assert f"case cluster.{mode}:" in gateway
    assert "request.CreateOAuthClient()" in gateway
    assert gateway.index("if mode == cluster.AuthModeIntegratedOAuth") < gateway.index(
        "request.CreateOAuthClient()"
    )
    assert "no gateway auth proxy" in gateway

    assert 'features.operators.openshift.io/fips-compliant: "false"' in fips
    assert 'features.operators.openshift.io/tls-profiles: "true"' in fips
    assert any(
        "TLS profile support" in claim
        for claim in expected["forbidden_claims"]
    )


def test_surface_fixture_corpus_is_local_representative_and_reproducible() -> None:
    corpus = json.loads(CORPUS_PATH.read_text())

    assert corpus["corpus_version"] == "architecture-surface-corpus/v1"
    assert {member["component_role"] for member in corpus["members"]} == {
        "operator",
        "service",
        "manifest",
    }
    for member in corpus["members"]:
        for relative in member.get("fixtures", []):
            assert (CORPUS_PATH.parent / relative).is_file()
        analyzer_fixture = member.get("analyzer_fixture")
        if analyzer_fixture:
            payload = json.loads(
                (CORPUS_PATH.parent / analyzer_fixture).read_text()
            )
            assert payload["component"] == member["id"]
    serialized = json.dumps(corpus)
    assert "logs/" not in serialized
    assert "architecture/rhoai" not in serialized
