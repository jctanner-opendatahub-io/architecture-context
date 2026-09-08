package embeddeddata

import (
	"os"
	"path/filepath"
	"testing"
)

func TestStageIncludesAcceptedAndLegacyArtifactsOnly(t *testing.T) {
	root := t.TempDir()
	source := filepath.Join(root, "architecture")
	destination := filepath.Join(root, "staged")
	overlays := filepath.Join(root, "overlays")
	mustWrite(t, filepath.Join(source, "rhoai-1", "component.md"))
	mustWrite(t, filepath.Join(source, "rhoai-1", "component.json"))
	mustWrite(t, filepath.Join(source, "rhoai-1", "component", "document.json"))
	mustWrite(t, filepath.Join(source, "rhoai-1", "component", "analyzer.json"))
	mustWrite(t, filepath.Join(source, "rhoai-1", "component", "synthesis.json"))
	mustWrite(t, filepath.Join(source, "rhoai-1", "component", "diagrams", "component.svg"))
	mustWrite(t, filepath.Join(source, "rhoai-1", "component", ".analyzer", "component-architecture.json"))
	mustWrite(t, filepath.Join(source, "rhoai-1", "component", ".analyzer", "analyzer_synthesis_context.md"))
	mustWrite(t, filepath.Join(source, "rhoai-1", "component", ".generation", "candidate.md"))
	mustWrite(t, filepath.Join(source, "rhoai-1", "component", "attempts", "01", "response.json"))
	mustWrite(t, filepath.Join(source, "rhoai-1", "contracts", "schemas", "component", "kind.json"))
	mustWrite(t, filepath.Join(overlays, "README.md"))
	if err := os.MkdirAll(destination, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink("rhoai-1", filepath.Join(source, "current")); err != nil {
		t.Fatal(err)
	}
	if err := Stage(source, destination, overlays); err != nil {
		t.Fatal(err)
	}

	for _, path := range []string{
		"rhoai-1/component.md", "rhoai-1/component.json",
		"rhoai-1/component/document.json", "rhoai-1/component/analyzer.json", "rhoai-1/component/synthesis.json",
		"rhoai-1/component/diagrams/component.svg", "rhoai-1/component/.analyzer/component-architecture.json",
		"rhoai-1/contracts/schemas/component/kind.json", "overlays/README.md", "symlinks.json",
	} {
		if _, err := os.Stat(filepath.Join(destination, path)); err != nil {
			t.Errorf("required staged path %s: %v", path, err)
		}
	}
	for _, path := range []string{
		"rhoai-1/component/.generation/candidate.md",
		"rhoai-1/component/attempts/01/response.json",
		"rhoai-1/component/.analyzer/analyzer_synthesis_context.md",
		"current",
	} {
		if _, err := os.Stat(filepath.Join(destination, path)); !os.IsNotExist(err) {
			t.Errorf("excluded path %s was staged", path)
		}
	}
	manifest, err := os.ReadFile(filepath.Join(destination, "symlinks.json"))
	if err != nil || string(manifest) != "{\"current\":\"rhoai-1\"}\n" {
		t.Fatalf("alias manifest = %q, %v", manifest, err)
	}
}

func mustWrite(t *testing.T, path string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(path), 0o644); err != nil {
		t.Fatal(err)
	}
}
