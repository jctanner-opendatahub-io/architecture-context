// Package document exposes validation for accepted structured component
// documents without exposing the analyzer's internal document representation.
package document

import (
	"bytes"

	"github.com/jctanner/arch-analyzer/internal/structured"
)

// ValidateJSON strictly decodes and semantically validates an accepted
// structured component document.
func ValidateJSON(data []byte) error {
	_, err := structured.Decode(bytes.NewReader(data))
	return err
}
