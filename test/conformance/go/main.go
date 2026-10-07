// Command conformance runs every fixture of the manifest through the Go side
// of the suite and prints one JSON line per (fixture, validator):
//
//	santhosh  santhosh-tekuri/jsonschema on the generated JSON Schema
//	go        the same verdict AND the document decoded into the struct
//	          pkl-gen-go generated for it (encoding/json, the types and nothing
//	          else: a generated Go type validates nothing, the schema does)
//	pkl       Pkl's own enforcement, through the typed loader (test/Load.pkl):
//	          the oracle every other validator is compared with
//
// usage: conformance <suite dir (test/)> <manifest> <generated schema dir>
package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"strings"

	"github.com/apple/pkl-go/pkl"
	"github.com/santhosh-tekuri/jsonschema/v6"
	yaml "go.yaml.in/yaml/v3"

	"conformance.invalid/gen/blocks"
	"conformance.invalid/gen/collections"
	"conformance.invalid/gen/conditions"
	"conformance.invalid/gen/declared"
	"conformance.invalid/gen/installed"
	"conformance.invalid/gen/literals"
	"conformance.invalid/gen/logarchiver"
	"conformance.invalid/gen/migrate"
	"conformance.invalid/gen/names"
	"conformance.invalid/gen/platform"
	"conformance.invalid/gen/prober"
	"conformance.invalid/gen/redirect"
	"conformance.invalid/gen/shortener"
	"conformance.invalid/gen/showcase"
	"conformance.invalid/gen/stat"
	"conformance.invalid/gen/union"
	"conformance.invalid/gen/urls"
	"conformance.invalid/gen/web"
)

type entry struct {
	ID, Schema, Path, Label, SchemaPath string
	Typed, SelfContained                bool
}
type doc struct{ Schema, Module string }

type result struct {
	ID        string `json:"id"`
	Validator string `json:"validator"`
	Accept    bool   `json:"accept"`
	Detail    string `json:"detail,omitempty"`
}

// The struct each document decodes into.
var structs = map[string]func() any{
	"web":        func() any { return &web.WebImpl{} },
	"urls":       func() any { return &urls.UrlsImpl{} },
	"redirect":   func() any { return &redirect.RedirectImpl{} },
	"stat":       func() any { return &stat.StatImpl{} },
	"prober":     func() any { return &prober.ProberImpl{} },
	"migrate":    func() any { return &migrate.Migrate{} },
	"log":        func() any { return &logarchiver.LogArchiverImpl{} },
	"shortener":  func() any { return &shortener.ShortenerImpl{} },
	"installed":  func() any { return &installed.InstalledImpl{} },
	"blocks":     func() any { return &blocks.Blocks{} },
	"collections": func() any { return &collections.Collections{} },
	"conditions": func() any { return &conditions.Conditions{} },
	"declared":   func() any { return &declared.Declared{} },
	"names":      func() any { return &names.Names{} },
	"literals":   func() any { return &literals.Literals{} },
	"union":      func() any { return &union.Union{} },
	"platform":   func() any { return &platform.Platform{} },
	"showcase":   func() any { return &showcase.Showcase{} },
}

func must(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
}

func firstLine(s string) string {
	if i := strings.IndexByte(s, '\n'); i > 0 {
		s = s[:i]
	}
	return s
}

func main() {
	suite, manifestPath, genDir := os.Args[1], os.Args[2], os.Args[3]
	var manifest []entry
	raw, err := os.ReadFile(manifestPath)
	must(err)
	must(json.Unmarshal(raw, &manifest))
	var docs map[string]doc
	raw, err = os.ReadFile(filepath.Join(suite, "conformance/documents.json"))
	must(err)
	must(json.Unmarshal(raw, &docs))

	schemas := loadSchemas(genDir)
	ctx := context.Background()
	ev, err := pkl.NewProjectEvaluator(ctx, &url.URL{Scheme: "file", Path: suite}, pkl.PreconfiguredOptions)
	must(err)
	defer ev.Close()

	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	emit := func(r result) { b, _ := json.Marshal(r); fmt.Fprintln(out, string(b)) }

	for _, e := range manifest {
		d := docs[e.Schema]
		data := readYAML(e.Path)
		schema := validate(schemas, e, data)
		emit(result{e.ID, "santhosh", schema.Accept, schema.Detail})
		if e.Typed {
			emit(decode(e, schema, data))
			emit(evalPkl(ctx, ev, suite, e, d))
		}
	}
}

// readYAML parses a fixture the way a Go service would read its file.
func readYAML(path string) any {
	b, err := os.ReadFile(path)
	must(err)
	var v any
	must(yaml.Unmarshal(b, &v))
	return v
}

func loadSchemas(dir string) map[string]any {
	set := map[string]any{}
	must(filepath.WalkDir(dir, func(p string, d os.DirEntry, err error) error {
		if err != nil || d.IsDir() || filepath.Ext(p) != ".json" {
			return err
		}
		f, err := os.Open(p)
		if err != nil {
			return err
		}
		defer f.Close()
		doc, err := jsonschema.UnmarshalJSON(f)
		set[p] = doc
		return err
	}))
	return set
}

func validate(set map[string]any, e entry, data any) result {
	c := jsonschema.NewCompiler()
	c.DefaultDraft(jsonschema.Draft2020)
	var sch *jsonschema.Schema
	var err error
	if e.SelfContained {
		// A chart's values schema embeds every document it refers to: it is
		// compiled alone, so that a reference that needed fetching would fail.
		f, oerr := os.Open(e.SchemaPath)
		must(oerr)
		defer f.Close()
		d, uerr := jsonschema.UnmarshalJSON(f)
		must(uerr)
		must(c.AddResource("mem://values.schema.json", d))
		sch, err = c.Compile("mem://values.schema.json")
	} else {
		for _, d := range set {
			must(c.AddResource(d.(map[string]any)["$id"].(string), d))
		}
		sch, err = c.Compile(set[e.SchemaPath].(map[string]any)["$id"].(string))
	}
	if err != nil {
		return result{Detail: "schema: " + firstLine(err.Error())}
	}
	j, err := json.Marshal(data)
	must(err)
	inst, err := jsonschema.UnmarshalJSON(strings.NewReader(string(j)))
	must(err)
	if err := sch.Validate(inst); err != nil {
		return result{Detail: firstLine(err.Error())}
	}
	return result{Accept: true}
}

// decode is the Go verdict: the schema accepts the document, and the document
// decodes into the generated type.
func decode(e entry, schema result, data any) result {
	if !schema.Accept {
		return result{e.ID, "go", false, schema.Detail}
	}
	// A class that extends another is an interface in the generated Go
	// (pkl-gen-go), which encoding/json cannot fill; such a document has no
	// struct, and its Go verdict is the schema's.
	mk, ok := structs[e.Schema]
	if !ok {
		return result{e.ID, "go", true, ""}
	}
	j, err := json.Marshal(data)
	must(err)
	if err := json.Unmarshal(j, mk()); err != nil {
		return result{e.ID, "go", false, "decode: " + firstLine(err.Error())}
	}
	return result{e.ID, "go", true, ""}
}

// evalPkl loads the fixture as a typed instance of the contract's module, so
// that Pkl's own types, closed classes and constraints answer.
func evalPkl(ctx context.Context, ev pkl.Evaluator, suite string, e entry, d doc) result {
	mod := "file://" + filepath.Join(suite, d.Module)
	src := fmt.Sprintf(`
import "pkl:yaml"
import "file://%s/Load.pkl"
import "%s" as M
local data = new yaml.Parser { useMapping = false }.parse(read("file://%s"))
output { value = Load.load(M, data) }
`, suite, mod, e.Path)
	if _, err := ev.EvaluateOutputText(ctx, pkl.TextSource(src)); err != nil {
		return result{e.ID, "pkl", false, firstLine(strings.ReplaceAll(err.Error(), "–– Pkl Error ––\n", ""))}
	}
	return result{e.ID, "pkl", true, ""}
}
