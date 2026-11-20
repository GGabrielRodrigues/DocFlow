import fs from "node:fs"
import path from "node:path"
import { fileURLToPath } from "node:url"

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const OPENAPI_PATH = path.resolve(__dirname, "../../../contracts/openapi.json")
const OUTPUT_PATH = path.resolve(__dirname, "../src/lib/api-schema.gen.ts")

function formatKey(key) {
  return /^[A-Za-z_$][A-Za-z0-9_$]*$/.test(key) ? key : JSON.stringify(key)
}

function schemaToTs(schema, indent = "") {
  if (!schema || typeof schema !== "object") {
    return "unknown"
  }

  if (schema.$ref) {
    const refName = schema.$ref.replace("#/components/schemas/", "")
    return `components["schemas"][${JSON.stringify(refName)}]`
  }

  if (Array.isArray(schema.anyOf)) {
    const parts = schema.anyOf.map((item) => schemaToTs(item, indent))
    return [...new Set(parts)].join(" | ")
  }

  if (Array.isArray(schema.oneOf)) {
    const parts = schema.oneOf.map((item) => schemaToTs(item, indent))
    return [...new Set(parts)].join(" | ")
  }

  if (Array.isArray(schema.enum)) {
    return schema.enum.map((v) => JSON.stringify(v)).join(" | ")
  }

  switch (schema.type) {
    case "string":
      return "string"
    case "integer":
    case "number":
      return "number"
    case "boolean":
      return "boolean"
    case "null":
      return "null"
    case "array": {
      const itemType = schemaToTs(schema.items, indent)
      return itemType.includes(" | ") ? `(${itemType})[]` : `${itemType}[]`
    }
    case "object": {
      if (schema.properties && Object.keys(schema.properties).length > 0) {
        const requiredSet = new Set(schema.required ?? [])
        const nextIndent = `${indent}  `
        const lines = ["{"]
        for (const [propName, propSchema] of Object.entries(
          schema.properties,
        )) {
          const isRequired = requiredSet.has(propName)
          const hasDefault =
            propSchema &&
            typeof propSchema === "object" &&
            "default" in propSchema
          const optionalMark = isRequired && !hasDefault ? "" : "?"
          const propType = schemaToTs(propSchema, nextIndent)
          lines.push(
            `${nextIndent}${formatKey(propName)}${optionalMark}: ${propType}`,
          )
        }
        lines.push(`${indent}}`)
        return lines.join("\n")
      }
      if (schema.additionalProperties) {
        if (schema.additionalProperties === true) {
          return "Record<string, unknown>"
        }
        const valueType = schemaToTs(schema.additionalProperties, indent)
        return `Record<string, ${valueType}>`
      }
      return "Record<string, unknown>"
    }
    default:
      return "unknown"
  }
}

function generateTypeScriptFromOpenApi(openapi) {
  const lines = [
    "// Este arquivo é gerado automaticamente a partir de contracts/openapi.json (FE-03).",
    "// Não edite manualmente. Execute `pnpm --dir apps/web run generate:api` para atualizar.",
    "",
    "export interface components {",
    "  schemas: {",
  ]

  const schemas = openapi.components?.schemas ?? {}
  const sortedSchemaNames = Object.keys(schemas).sort()

  for (const name of sortedSchemaNames) {
    const schema = schemas[name]
    const tsType = schemaToTs(schema, "    ")
    lines.push(`    ${formatKey(name)}: ${tsType}`)
  }

  lines.push("  }")
  lines.push("}")
  lines.push("")
  lines.push("export interface operations {")

  const paths = openapi.paths ?? {}
  const httpMethods = ["get", "post", "put", "patch", "delete"]

  for (const [, pathItem] of Object.entries(paths)) {
    for (const method of httpMethods) {
      const operation = pathItem?.[method]
      if (!operation || !operation.operationId) continue

      const opId = operation.operationId
      lines.push(`  ${formatKey(opId)}: {`)

      // Parameters (path, query, header)
      const params = Array.isArray(operation.parameters)
        ? operation.parameters
        : []
      const pathParams = params.filter((p) => p.in === "path")
      const queryParams = params.filter((p) => p.in === "query")
      const headerParams = params.filter((p) => p.in === "header")

      if (pathParams.length || queryParams.length || headerParams.length) {
        lines.push("    parameters: {")
        if (pathParams.length) {
          lines.push("      path: {")
          for (const p of pathParams) {
            const opt = p.required ? "" : "?"
            lines.push(
              `        ${formatKey(p.name)}${opt}: ${schemaToTs(p.schema, "        ")}`,
            )
          }
          lines.push("      }")
        }
        if (queryParams.length) {
          lines.push("      query?: {")
          for (const p of queryParams) {
            const opt = p.required ? "" : "?"
            lines.push(
              `        ${formatKey(p.name)}${opt}: ${schemaToTs(p.schema, "        ")}`,
            )
          }
          lines.push("      }")
        }
        if (headerParams.length) {
          lines.push("      header?: {")
          for (const p of headerParams) {
            const opt = p.required ? "" : "?"
            lines.push(
              `        ${formatKey(p.name)}${opt}: ${schemaToTs(p.schema, "        ")}`,
            )
          }
          lines.push("      }")
        }
        lines.push("    }")
      } else {
        lines.push("    parameters?: never")
      }

      // Request body
      const jsonReqSchema =
        operation.requestBody?.content?.["application/json"]?.schema
      if (jsonReqSchema) {
        const isReq = Boolean(operation.requestBody.required)
        lines.push(`    requestBody${isReq ? "" : "?"}: {`)
        lines.push("      content: {")
        lines.push(
          `        "application/json": ${schemaToTs(jsonReqSchema, "        ")}`,
        )
        lines.push("      }")
        lines.push("    }")
      } else {
        lines.push("    requestBody?: never")
      }

      // Responses
      lines.push("    responses: {")
      const responses = operation.responses ?? {}
      for (const [statusCode, responseObj] of Object.entries(responses)) {
        const jsonResSchema = responseObj?.content?.["application/json"]?.schema
        if (jsonResSchema) {
          lines.push(`      ${formatKey(statusCode)}: {`)
          lines.push("        content: {")
          lines.push(
            `          "application/json": ${schemaToTs(jsonResSchema, "          ")}`,
          )
          lines.push("        }")
          lines.push("      }")
        } else {
          lines.push(`      ${formatKey(statusCode)}: {`)
          lines.push("        content?: never")
          lines.push("      }")
        }
      }
      lines.push("    }")
      lines.push("  }")
    }
  }

  lines.push("}")
  lines.push("")
  lines.push("export interface paths {")

  for (const [routePath, pathItem] of Object.entries(paths)) {
    lines.push(`  ${JSON.stringify(routePath)}: {`)
    for (const method of httpMethods) {
      const operation = pathItem?.[method]
      if (!operation || !operation.operationId) continue
      lines.push(
        `    ${method}: operations[${JSON.stringify(operation.operationId)}]`,
      )
    }
    lines.push("  }")
  }

  lines.push("}")
  lines.push("")

  for (const name of sortedSchemaNames) {
    lines.push(
      `export type ${name} = components["schemas"][${JSON.stringify(name)}]`,
    )
  }

  lines.push("")
  return lines.join("\n")
}

function main() {
  const isCheck = process.argv.includes("--check")

  if (!fs.existsSync(OPENAPI_PATH)) {
    console.error(`Erro: contrato OpenAPI não encontrado em ${OPENAPI_PATH}`)
    process.exit(1)
  }

  const rawJson = fs.readFileSync(OPENAPI_PATH, "utf8")
  const openapi = JSON.parse(rawJson)
  const generated = generateTypeScriptFromOpenApi(openapi)

  if (isCheck) {
    if (!fs.existsSync(OUTPUT_PATH)) {
      console.error(
        `Erro: arquivo gerado não encontrado em ${OUTPUT_PATH}. Execute 'pnpm --dir apps/web run generate:api'.`,
      )
      process.exit(1)
    }
    const existing = fs.readFileSync(OUTPUT_PATH, "utf8").replace(/\r\n/g, "\n")
    const normalizedGenerated = generated.replace(/\r\n/g, "\n")
    if (existing !== normalizedGenerated) {
      console.error(
        "Erro: src/lib/api-schema.gen.ts está desatualizado em relação a contracts/openapi.json.",
      )
      console.error(
        "Execute 'pnpm --dir apps/web run generate:api' e faça commit do arquivo atualizado.",
      )
      process.exit(1)
    }
    console.log(
      "OK: Cliente TypeScript sincronizado com contracts/openapi.json.",
    )
    return
  }

  fs.writeFileSync(OUTPUT_PATH, generated, "utf8")
  console.log(`Cliente TypeScript gerado com sucesso em ${OUTPUT_PATH}`)
}

main()
