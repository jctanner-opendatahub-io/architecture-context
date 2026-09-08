package cmd

import (
	"os"
	"strings"
	"testing"
	"testing/fstest"
)

func TestAcceptedJSONOnlyComponentRawAccessIsActionable(t *testing.T) {
	raw, err := os.ReadFile("../internal/documentdata/testdata/rhoai.next/typed-only/document.json")
	if err != nil {
		t.Fatal(err)
	}
	previousFS, previousOverlay, previousVersion, previousOutput := archFS, overlayFS, versionArg, outputFormat
	t.Cleanup(func() {
		archFS, overlayFS, versionArg, outputFormat = previousFS, previousOverlay, previousVersion, previousOutput
	})
	archFS = fstest.MapFS{"rhoai.next/typed-only/document.json": {Data: raw}}
	overlayFS = nil
	versionArg = "rhoai.next"
	outputFormat = OutputRaw

	err = componentCmd.RunE(componentCmd, []string{"typed-only"})
	if err == nil || !strings.Contains(err.Error(), "reading rhoai.next/typed-only.md") {
		t.Fatalf("raw access error = %v", err)
	}
}
