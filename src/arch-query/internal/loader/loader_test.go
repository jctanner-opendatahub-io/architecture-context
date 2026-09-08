package loader

import (
	"os"
	"strings"
	"testing"
	"testing/fstest"
)

func TestLoadVersionMergesComponentAnalyzerArtifacts(t *testing.T) {
	fsys := fstest.MapFS{
		"rhoai.next/example.md": {
			Data: []byte(`# Component: example

## Overview

Example component.
`),
		},
		"rhoai.next/example/.analyzer/component-architecture.json": {
			Data: []byte(`{
				"component": "example",
				"webhooks": [
					{
						"name": "vexample.kb.io",
						"type": "validating",
						"path": "/validate-example",
						"rules": [
							{"apiGroups": ["example.io"], "apiVersions": ["v1"], "resources": ["examples"], "operations": ["CREATE"]}
						]
					}
				],
				"platform_webhooks": [{"component": "example", "webhook": "vexample.kb.io"}],
				"controller_watches": [{"type": "Owns", "gvk": "apps/v1.Deployment", "controller": "example", "source": "controllers/example.go"}]
			}`),
		},
	}

	data, err := LoadVersion(fsys, nil, "rhoai.next")
	if err != nil {
		t.Fatalf("LoadVersion: %v", err)
	}
	doc := data.Components["example"]
	if doc == nil {
		t.Fatal("example component was not loaded")
	}
	if len(doc.Webhooks) != 1 {
		t.Fatalf("expected analyzer webhook to be merged, got %d", len(doc.Webhooks))
	}
	if len(doc.PlatformWebhooks) != 1 {
		t.Fatalf("expected platform webhook ref to be merged, got %d", len(doc.PlatformWebhooks))
	}
	if len(doc.ControllerWatches) != 1 {
		t.Fatalf("expected controller watch to be merged, got %d", len(doc.ControllerWatches))
	}
}

func TestLoadVersionAcceptedDocumentIsAuthoritative(t *testing.T) {
	document := readFixture(t, "../documentdata/testdata/rhoai.next/typed-only/document.json")
	fsys := fstest.MapFS{
		"rhoai.next/typed-only/document.json": {Data: document},
		"rhoai.next/typed-only.md": {Data: []byte(`# Component: wrong-markdown-name

## Purpose

**Short**: sibling Markdown must not supply accepted facts

## Extra Raw Section

raw-only-marker
`)},
		"rhoai.next/typed-only/.analyzer/component-architecture.json": {Data: []byte(`{"component":"typed-only","controller_watches":[{"type":"Owns","gvk":"wrong/v1.Fact","controller":"wrong","source":"wrong.go"}]}`)},
	}
	data, err := LoadVersion(fsys, nil, "rhoai.next")
	if err != nil {
		t.Fatal(err)
	}
	doc := data.Components["typed-only"]
	if doc == nil || doc.Name != "typed-only" || len(doc.ControllerWatches) != 1 || doc.ControllerWatches[0].GVK != "apps/v1.Deployment" {
		t.Fatalf("accepted document was not authoritative: %#v", doc)
	}
	if strings.Contains(doc.Purpose, "sibling Markdown") {
		t.Fatalf("sibling Markdown supplied accepted facts: %q", doc.Purpose)
	}
	if !strings.Contains(doc.RawSections["Extra Raw Section"], "raw-only-marker") {
		t.Fatalf("rendered sibling raw sections unavailable: %#v", doc.RawSections)
	}
}

func TestLoadVersionInvalidAcceptedDocumentNeverFallsBack(t *testing.T) {
	otherIdentity := readFixture(t, "../documentdata/testdata/rhoai.next/praxis-policy/document.json")
	tests := map[string]struct {
		document []byte
		want     string
	}{
		"unsupported": {[]byte(`{"schema_version":"2.0.0"}`), "schema_version"},
		"identity mismatch": {
			otherIdentity,
			"publication directory",
		},
	}
	for name, test := range tests {
		t.Run(name, func(t *testing.T) {
			fsys := fstest.MapFS{
				"rhoai.next/typed-only/document.json":                         {Data: test.document},
				"rhoai.next/typed-only.md":                                    {Data: []byte("# Component: typed-only\n\n## Purpose\n\nlegacy fallback\n")},
				"rhoai.next/typed-only/.analyzer/component-architecture.json": {Data: []byte(`{"component":"typed-only"}`)},
			}
			data, err := LoadVersion(fsys, nil, "rhoai.next")
			if err == nil || data != nil || !strings.Contains(err.Error(), test.want) {
				t.Fatalf("LoadVersion = %#v, %v; want actionable error containing %q", data, err, test.want)
			}
		})
	}
}

func TestLoadVersionJSONOnlyAcceptedAndMixedLegacyCorpus(t *testing.T) {
	document := readFixture(t, "../documentdata/testdata/rhoai.next/typed-only/document.json")
	fsys := fstest.MapFS{
		"rhoai.next/typed-only/document.json":                     {Data: document},
		"rhoai.next/typed-only/analyzer.json":                     {Data: []byte(`{"component":"typed-only"}`)},
		"rhoai.next/legacy.md":                                    {Data: []byte("# Component: legacy\n\n## Purpose\n\nlegacy component\n")},
		"rhoai.next/legacy/.analyzer/component-architecture.json": {Data: []byte(`{"component":"legacy","controller_watches":[{"type":"Owns","gvk":"v1.Pod","controller":"legacy","source":"legacy.go"}]}`)},
		"rhoai.next/run-metadata/attempts/01/response.json":       {Data: []byte(`{"component":"must-not-load"}`)},
		"rhoai.next/run-metadata/document.json":                   {Data: document},
		"rhoai.next/contracts/schemas/example/schema.json":        {Data: []byte(`{"component":"must-not-load"}`)},
	}
	data, err := LoadVersion(fsys, nil, "rhoai.next")
	if err != nil {
		t.Fatal(err)
	}
	if data.Version.ComponentCount != 2 || len(data.Components) != 2 {
		t.Fatalf("mixed component count = %d/%d, want 2", data.Version.ComponentCount, len(data.Components))
	}
	accepted := data.Components["typed-only"]
	if accepted == nil || accepted.FileName != "typed-only.md" || accepted.RawSections != nil || len(accepted.Webhooks) != 1 {
		t.Fatalf("JSON-only accepted component unavailable for typed queries: %#v", accepted)
	}
	if legacy := data.Components["legacy"]; legacy == nil || len(legacy.ControllerWatches) != 1 {
		t.Fatalf("legacy Markdown+analyzer path changed: %#v", legacy)
	}
	versions, err := DiscoverVersions(fsys, nil)
	if err != nil {
		t.Fatal(err)
	}
	if len(versions) != 1 || versions[0].ComponentCount != 2 {
		t.Fatalf("mixed version inventory = %#v", versions)
	}
}

func TestDiscoverVersionsPreservesSortedAliases(t *testing.T) {
	fsys := fstest.MapFS{"rhoai-1/example.md": {Data: []byte("# Component: example\n")}}
	versions, err := DiscoverVersions(fsys, map[string]string{"z-alias": "rhoai-1", "a-alias": "rhoai-1"})
	if err != nil {
		t.Fatal(err)
	}
	if len(versions) != 1 || strings.Join(versions[0].Aliases, ",") != "a-alias,z-alias" {
		t.Fatalf("version aliases = %#v", versions)
	}
}

func readFixture(t *testing.T, path string) []byte {
	t.Helper()
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	return raw
}

func TestLoadVersionExcludesVersionIndexFromComponents(t *testing.T) {
	fsys := fstest.MapFS{
		"rhoai.next/INDEX.md": {Data: []byte("# Index\n")},
		"rhoai.next/example.md": {Data: []byte(`# Component: example

## Overview

Example component.
`)},
	}

	data, err := LoadVersion(fsys, nil, "rhoai.next")
	if err != nil {
		t.Fatalf("LoadVersion: %v", err)
	}
	if _, exists := data.Components["INDEX"]; exists {
		t.Fatal("INDEX.md was loaded as a component")
	}
	if data.Components["example"] == nil {
		t.Fatal("example component was not loaded")
	}

	versions, err := DiscoverVersions(fsys, nil)
	if err != nil {
		t.Fatalf("DiscoverVersions: %v", err)
	}
	if len(versions) != 1 || versions[0].ComponentCount != 1 {
		t.Fatalf("expected one component in version inventory, got %#v", versions)
	}
}
