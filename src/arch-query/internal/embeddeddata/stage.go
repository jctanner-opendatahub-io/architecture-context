// Package embeddeddata stages the bounded architecture subset compiled into
// arch-query release binaries.
package embeddeddata

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

var acceptedArtifactNames = map[string]bool{
	"analyzer.json":  true,
	"document.json":  true,
	"synthesis.json": true,
}

// Stage copies queryable legacy and accepted architecture artifacts. The
// destination must already exist; callers own cleanup so tests never touch the
// repository's historical architecture tree.
func Stage(source, destination, overlays string) error {
	entries, err := os.ReadDir(source)
	if err != nil {
		return fmt.Errorf("read architecture source: %w", err)
	}
	symlinks := make(map[string]string)
	for _, entry := range entries {
		if entry.Type()&os.ModeSymlink != 0 {
			target, readErr := os.Readlink(filepath.Join(source, entry.Name()))
			if readErr != nil {
				return fmt.Errorf("read version alias %s: %w", entry.Name(), readErr)
			}
			symlinks[entry.Name()] = target
			continue
		}
		if !entry.IsDir() || entry.Name() == "diagrams" || entry.Name() == "overlays" {
			continue
		}
		if err := stageVersion(filepath.Join(source, entry.Name()), filepath.Join(destination, entry.Name())); err != nil {
			return fmt.Errorf("stage version %s: %w", entry.Name(), err)
		}
	}
	if err := writeSymlinks(filepath.Join(destination, "symlinks.json"), symlinks); err != nil {
		return err
	}
	if overlays != "" {
		if info, statErr := os.Stat(overlays); statErr == nil && info.IsDir() {
			if err := copyTree(overlays, filepath.Join(destination, "overlays")); err != nil {
				return fmt.Errorf("stage overlays: %w", err)
			}
		} else if statErr != nil && !os.IsNotExist(statErr) {
			return fmt.Errorf("inspect overlays: %w", statErr)
		}
	}
	return nil
}

func stageVersion(source, destination string) error {
	if err := os.MkdirAll(destination, 0o755); err != nil {
		return err
	}
	entries, err := os.ReadDir(source)
	if err != nil {
		return err
	}
	for _, entry := range entries {
		from := filepath.Join(source, entry.Name())
		to := filepath.Join(destination, entry.Name())
		if !entry.IsDir() {
			if strings.HasSuffix(entry.Name(), ".md") || strings.HasSuffix(entry.Name(), ".json") {
				if err := copyFile(from, to); err != nil {
					return err
				}
			}
			continue
		}
		if entry.Name() == "contracts" {
			if err := copyTree(from, to); err != nil {
				return err
			}
			continue
		}
		if err := stageComponent(from, to); err != nil {
			return err
		}
	}
	return nil
}

func stageComponent(source, destination string) error {
	entries, err := os.ReadDir(source)
	if err != nil {
		return err
	}
	for _, entry := range entries {
		from := filepath.Join(source, entry.Name())
		to := filepath.Join(destination, entry.Name())
		switch {
		case !entry.IsDir() && acceptedArtifactNames[entry.Name()]:
			if err := copyFile(from, to); err != nil {
				return err
			}
		case entry.IsDir() && entry.Name() == "diagrams":
			if err := copyTree(from, to); err != nil {
				return err
			}
		case entry.IsDir() && entry.Name() == ".analyzer":
			legacy := filepath.Join(from, "component-architecture.json")
			if info, statErr := os.Stat(legacy); statErr == nil && !info.IsDir() {
				if err := copyFile(legacy, filepath.Join(to, "component-architecture.json")); err != nil {
					return err
				}
			} else if statErr != nil && !os.IsNotExist(statErr) {
				return statErr
			}
		}
	}
	return nil
}

func copyTree(source, destination string) error {
	return filepath.WalkDir(source, func(path string, entry os.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		relative, err := filepath.Rel(source, path)
		if err != nil {
			return err
		}
		target := filepath.Join(destination, relative)
		if entry.IsDir() {
			return os.MkdirAll(target, 0o755)
		}
		return copyFile(path, target)
	})
}

func copyFile(source, destination string) error {
	if err := os.MkdirAll(filepath.Dir(destination), 0o755); err != nil {
		return err
	}
	input, err := os.Open(source)
	if err != nil {
		return err
	}
	defer input.Close()
	output, err := os.OpenFile(destination, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	if _, err := io.Copy(output, input); err != nil {
		_ = output.Close()
		return err
	}
	return output.Close()
}

func writeSymlinks(path string, aliases map[string]string) error {
	keys := make([]string, 0, len(aliases))
	for key := range aliases {
		keys = append(keys, key)
	}
	sort.Strings(keys)
	ordered := make(map[string]string, len(keys))
	for _, key := range keys {
		ordered[key] = aliases[key]
	}
	raw, err := json.Marshal(ordered)
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	return os.WriteFile(path, raw, 0o644)
}
