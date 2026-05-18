# Prompt: imagen de circuito → JSON estructurado

Úsalo cuando el usuario suba una **foto o esquema dibujado** y quieras preparar KiCad sin pegarte a una receta ya conocida.

## Instrucciones para el modelo (visión)

1. Describe con criterio técnico lo que ves (componentes, conexiones, alimentación).
2. Devuelve **solo** un bloque JSON válido (sin markdown alrededor), con la forma exacta de abajo.
3. Si algo no se lee bien, pon la duda en `ambiguities` — no inventes valores críticos (tensión, polaridad de electrolíticos, pines de IC).
4. Usa **símbolos y huellas de librería KiCad** cuando puedas (`Lib:Name`, huella estándar). Si no estás seguro de la huella, deja `footprint` vacío y explícalo en `notes`.

## Esquema JSON obligatorio

```json
{
  "circuit_guess": "breve descripción en lenguaje natural",
  "confidence": 0.0,
  "components": [
    {
      "ref": "U1",
      "symbol": "Timer:NE555",
      "footprint": "Package_DIP:DIP-8_W7.62mm",
      "value": "NE555",
      "notes": ""
    }
  ],
  "nets": [
    {
      "name": "VCC",
      "pins": ["U1-8", "U1-4"]
    }
  ],
  "ambiguities": [
    "texto de cada duda o elemento ilegible"
  ]
}
```

## Reglas para el agente MCP (después del JSON)

1. Si el **texto** del usuario (o `circuit_guess` + descripción) coincide con circuitos conocidos, llama  
   `parse_circuit_from_description(...)` **con la descripción completa** — puede devolver receta con `_matched_from`.
2. Si hay receta canónica pero con variantes, usa `get_pcb_workflow_recipe("<circuit_type>")` y **obedece el JSON** (componentes, nets, huellas).
3. Si **no** hay receta: usa este JSON como especificación para las herramientas del otro servidor (crear esquema, situar símbolos, cablear nets). Valida con `validate_circuit_logic` sobre `.kicad_sch` o `.net` cuando existan.
4. Antes de fabricar, sigue [RELEASE_PLAYBOOK.md](./RELEASE_PLAYBOOK.md).

## English (same rules for the model)

Return **only** valid JSON with `circuit_guess`, `confidence`, `components[]` (`ref`, `symbol`, `footprint`, `value`, `notes`), `nets[]` (`name`, `pins` as `REF-PIN`), and `ambiguities[]`. Then have the agent call `parse_circuit_from_description` when keywords match a known recipe; otherwise build from the JSON and follow the release playbook.
