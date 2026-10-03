import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory
import com.networknt.schema.JsonSchemaFactory
import com.networknt.schema.SpecVersion
import conformance.contract.*
import contracts.test.Showcase
import java.io.File
import java.nio.file.Path
import org.pkl.config.java.ConfigEvaluatorBuilder
import org.pkl.config.kotlin.forKotlin
import org.pkl.config.kotlin.to
import org.pkl.core.ModuleSource
import org.pkl.core.project.Project

private val yaml = ObjectMapper(YAMLFactory())
private val json = ObjectMapper()

private fun line(id: String, validator: String, accept: Boolean, detail: String = "") =
    println(json.writeValueAsString(mapOf("id" to id, "validator" to validator, "accept" to accept, "detail" to detail.lines().first().take(160))))

fun main(args: Array<String>) {
    val (suite, manifestPath, genDir) = args
    val manifest = json.readTree(File(manifestPath))
    val docs = json.readTree(File("$suite/conformance/documents.json"))
    // Every generated document is found by the `$id` it carries, as a loader would
    // find it in its jar; a chart's values schema embeds what it needs and has none.
    val byId = File(genDir).walk().filter { it.extension == "json" }.associate { json.readTree(it)["\$id"].asText() to "file://${it.path}" }
    val shared = JsonSchemaFactory.getInstance(SpecVersion.VersionFlag.V202012) { b -> b.schemaMappers { m -> m.mappings(byId) } }
    val alone = JsonSchemaFactory.getInstance(SpecVersion.VersionFlag.V202012)
    val project = Project.loadFromPath(Path.of("$suite/PklProject"))

    ConfigEvaluatorBuilder.preconfigured().applyFromProject(project).build().forKotlin().use { ev ->
        for (e in manifest) {
            val id = e["id"].asText()
            val instance = yaml.readTree(File(e["path"].asText())) ?: json.nullNode()
            val verdict = runCatching {
                val errs = (if (e["selfContained"]?.asBoolean() == true) alone else shared)
                    .getSchema(File(e["schemaPath"].asText()).readText()).validate(instance)
                Pair(errs.isEmpty(), errs.minByOrNull { it.instanceLocation.toString() }?.message ?: "")
            }
            val schemaOk = verdict.getOrNull()?.first ?: false
            line(id, "networknt", schemaOk, verdict.exceptionOrNull()?.toString() ?: verdict.getOrNull()!!.second)

            // The document, read into the class pkl-codegen-kotlin generated for it.
            // The generated classes are bound by pkl-config-kotlin, from what Pkl evaluates
            // (Jackson cannot read their enums), so Pkl's own enforcement is in this verdict;
            // the other half is the schema's. `platform` has union types, which the
            // generator refuses, so it has no class.
            val schema = e["schema"].asText()
            if (!e["typed"].asBoolean() || schema == "platform" || schema == "union") continue
            if (!schemaOk) { line(id, "kotlin", false, verdict.getOrNull()?.second ?: "schema error"); continue }
            val src = """
                import "pkl:yaml"
                import "file://$suite/Load.pkl"
                import "file://$suite/${docs[schema]["module"].asText()}" as M
                local data = new yaml.Parser { useMapping = false }.parse(read("file://${e["path"].asText()}"))
                output { value = Load.load(M, data) }
            """.trimIndent()
            val r = runCatching {
                val cfg = ev.evaluateOutputValue(ModuleSource.text(src))
                when (schema) {
                    "web" -> cfg.to<Web>()
                    "urls" -> cfg.to<Urls>()
                    "redirect" -> cfg.to<Redirect>()
                    "stat" -> cfg.to<Stat>()
                    "prober" -> cfg.to<Prober>()
                    "migrate" -> cfg.to<Migrate>()
                    "log" -> cfg.to<LogArchiver>()
                    "shortener" -> cfg.to<Shortener>()
                    "installed" -> cfg.to<Installed>()
                    "blocks" -> cfg.to<Blocks>()
                    "conditions" -> cfg.to<Conditions>()
                    "inherit" -> cfg.to<Inherit>()
                    "names" -> cfg.to<Names>()
                    "literals" -> cfg.to<Literals>()
                    "showcase" -> cfg.to<Showcase>()
                    else -> error("no generated class for $schema")
                }
            }
            line(id, "kotlin", r.isSuccess, "decode: " + (r.exceptionOrNull()?.message ?: ""))
        }
    }
}
