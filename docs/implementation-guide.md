# Step-by-Step Implementation Guide

**Semana a semana del playbook "Build in Public"**

---

## Estado actual (MVP completado)

El proyecto base ya existe y funciona:

```
✅ kicad-circuit-ai/ — MVP funcional
   ✅ validate_circuit_logic() — detecta errores en NE555 (tu caso real)
   ✅ explain_error() — explicaciones en inglés y español
   ✅ suggest_fix() — sugerencias de corrección
   ✅ 5 componentes en la knowledge base (NE555, LM7805, ATmega328P, LM741, L293D)
   ✅ 25 tests pasando, sin KiCad requerido
   ✅ test fixture bad_555_netlist.xml — exactamente tu error de Práctica-7
   ✅ Primer commit hecho
```

---

## Semana 1: "La historia de origen" + Setup

### Día 1: El post

**Antes de tocar más código**, publica el post. La historia ya existe, el análisis forense ya está. No esperes a que el producto esté perfecto.

**Contenido del post (Instagram Reel / LinkedIn):**
- Screenshot del feedback de tu profesor
- La tabla de pines del 555 con los 5 errores marcados
- El output del validador corriendo sobre `bad_555_netlist.xml`
- CTA: "Estoy construyendo una herramienta para que esto no le pase a ningún estudiante"

**Comando para generar el output del post:**
```bash
cd /home/sebasvelace/kicad-circuit-ai
PYTHONPATH=src .venv/bin/python3 -c "
from kicad_circuit_ai.tools.validate import validate_from_file
print(validate_from_file('tests/fixtures/bad_555_netlist.xml', locale='es').format('es'))
"
```

### Día 2-3: GitHub

1. Crear repo en GitHub: `github.com/TU_USER/kicad-circuit-ai`
2. Push del primer commit:
```bash
cd /home/sebasvelace/kicad-circuit-ai
git remote add origin https://github.com/TU_USER/kicad-circuit-ai.git
git branch -M main
git push -u origin main
```
3. Configurar el repo:
   - Description: "Circuit Intelligence Layer for KiCad — detects logic errors ERC/DRC cannot see"
   - Topics: `kicad`, `mcp`, `electronics`, `circuit-validation`, `pcb`, `ai`, `anthropic`
   - Star your own repo to get it indexed

### Día 4-5: Conectar como MCP en Claude Code

```bash
# Activar el venv
source /home/sebasvelace/kicad-circuit-ai/.venv/bin/activate

# Instalar mcp package
pip install "mcp[cli]"

# Registrar el server en Claude Code
claude mcp add kicad-circuit-ai -- \
  /home/sebasvelace/kicad-circuit-ai/.venv/bin/python3 \
  -m kicad_circuit_ai.server
```

**Verificar que funciona:**
```bash
claude
# En Claude Code:
# "Valida mi esquemático: validate_circuit_logic('/home/sebasvelace/kicad-circuit-ai/tests/fixtures/bad_555_netlist.xml', locale='es')"
```

### Día 6-7: Post del primer demo

Video corto (60s):
1. Abrir terminal
2. Ejecutar el validador sobre el schematic roto
3. Mostrar los 4 errores detectados con emojis
4. CTA: "Si eres estudiante de electrónica y usas KiCad, dale una estrella"

---

## Semana 2: "El MCP server funciona" + Más componentes

### Día 8-10: Instalar mcp y probar el server real

```bash
cd /home/sebasvelace/kicad-circuit-ai
source .venv/bin/activate
pip install "mcp[cli]"

# Probar que el server arranca
python3 -m kicad_circuit_ai.server &
# Debería iniciar sin errores
```

**Demo con Claude Code (screencast):**
- Abre Claude Code
- `"Lista los componentes que conoces"`
- `"Valida este archivo: [ruta a tu esquemático]"`
- `"Explica el error WRONG_NET_CRITICAL en español"`

### Día 11-12: Componente #6 — ESP32

Crea `components/ESP32.yaml`:
```bash
cp components/NE555.yaml components/ESP32.yaml
# Editar según el datasheet del ESP32-WROOM-32
```

Reglas clave del ESP32:
- Pin EN: must NOT be GND (chip disabled), necesita pull-up 10kΩ
- PIN IO0: warn si GND en boot (modo flash, no es fatal pero es confuso)
- GND multiple pins: todos deben conectarse
- VCC/VDD 3.3V: must_not_be 5V (ESP32 no tolera 5V)

### Día 13-14: Post "¿Qué componente agrego primero?"

Encuesta en Instagram Stories / LinkedIn:
- ESP32
- STM32F103
- LM317 (regulador ajustable)
- L298N (motor driver)

---

## Semana 3: "La comunidad contribuye"

### Día 15-16: GitHub Actions para validar YAML

Crea `.github/workflows/validate-components.yml`:

```yaml
name: Validate Components

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install pyyaml pytest
      - run: pytest tests/ -v
      - name: Validate YAML schema
        run: python3 scripts/validate_component_yaml.py
```

Crea `scripts/validate_component_yaml.py`:
```python
#!/usr/bin/env python3
"""Validate that all component YAML files follow the schema."""
import yaml
import sys
from pathlib import Path

REQUIRED_KEYS = ["component", "pins"]
COMPONENT_KEYS = ["name", "aliases", "package", "category", "datasheet"]

errors = []
for yaml_file in Path("components").glob("*.yaml"):
    if yaml_file.name.startswith("_"):
        continue
    with open(yaml_file) as f:
        data = yaml.safe_load(f)
    for key in REQUIRED_KEYS:
        if key not in data:
            errors.append(f"{yaml_file.name}: missing '{key}'")
    comp = data.get("component", {})
    if "name" not in comp:
        errors.append(f"{yaml_file.name}: component.name is required")

if errors:
    for e in errors:
        print(f"ERROR: {e}")
    sys.exit(1)
print(f"OK: {len(list(Path('components').glob('*.yaml')))} component files validated")
```

### Día 17-18: Video tutorial "Cómo contribuir en 10 minutos"

Screencast:
1. Fork del repo
2. `cp components/NE555.yaml components/MiComponente.yaml`
3. Rellenar el YAML con el datasheet abierto
4. `pytest tests/` — pasan los tests existentes
5. `git push && gh pr create`

### Día 19-20: Buscar primeros contribuidores

- Publicar en grupos de Telegram de electrónica LatAm
- Postar en r/KiCad y r/electronics (en inglés)
- "Good first issue" en GitHub Issues:
  - "Add CD4017 decade counter"
  - "Add ULN2003 Darlington array"
  - "Add LM317 adjustable regulator"
  - "Add Spanish translations for remaining error messages"

### Día 21: Post "Comunidad contribuyó el componente #X"

Cuando llegue el primer PR, hazle un post. Menciona al contribuidor. Esto es combustible para la comunidad.

---

## Semana 4: "Demo completa end-to-end"

### Día 22-23: Wire tracing en .kicad_sch

El parser actual solo detecta conexiones directas (power symbol exactamente en el pin). Para detectar conexiones via wire:

```bash
# Estudiar el código existente en KiCAD-MCP-Server
cat /home/sebasvelace/KiCAD-MCP-Server/python/commands/wire_connectivity.py
```

Implementar en `src/kicad_circuit_ai/parser/schematic.py`:
1. Reusar `_parse_wires_sexp()` del repo existente
2. Build adjacency graph de los wire segments
3. Flood-fill desde pins hasta power symbols

**OU**: pedirle al usuario que exporte el netlist XML primero (es más confiable).

### Día 24-25: Video demo 5 minutos

Flujo completo mostrando los dos proyectos trabajando juntos:

```
1. "Hazme un esquemático del 555 astable"  → KiCAD-MCP-Server
2. "Valida mi esquemático"                  → kicad-circuit-ai detecta error
3. "Corrije el error del pin 8"             → KiCAD-MCP-Server mueve la conexión
4. "Valida de nuevo"                        → kicad-circuit-ai: ✅ sin errores
5. "Exporta Gerbers"                        → KiCAD-MCP-Server exporta
```

Config de Claude Code para ambos servers:
```json
{
  "mcpServers": {
    "kicad": {
      "command": "node",
      "args": ["/home/sebasvelace/KiCAD-MCP-Server/dist/index.js"]
    },
    "kicad-circuit-ai": {
      "command": "/home/sebasvelace/kicad-circuit-ai/.venv/bin/python3",
      "args": ["-m", "kicad_circuit_ai.server"],
      "env": {
        "KICAD_AI_COMPONENTS_DIR": "/home/sebasvelace/kicad-circuit-ai/components",
        "KICAD_AI_LOCALE": "es"
      }
    }
  }
}
```

### Día 26-27: Launch post

**Hacker News:**
```
Title: Show HN: kicad-circuit-ai – MCP server that detects schematic errors KiCad ERC cannot

Show HN: I'm an electronics engineering student. My professor rejected my PCB
because 5 of 8 pins of an NE555 were accidentally wired to GND. KiCad's ERC
passed. Gerbers exported cleanly. I only found out when the board came back.

I built a Python MCP server that checks component pin connections against a
semantic knowledge base (YAML files, one per IC). It detects errors like VCC→GND
that ERC/DRC cannot see because they don't know what pins are supposed to do.

GitHub: [link]

Currently supports NE555, LM7805, ATmega328P, LM741, L293D. Easy to add more
(~10 minutes per component). Looking for contributors who've had similar stories.
```

**r/KiCad:**
```
Title: I built an MCP server that catches schematic errors KiCad ERC misses

[same story, show the output screenshot]
```

**r/electronics**, grupos de Telegram LatAm, KiCad forums.

### Día 28: Publicar en PyPI

```bash
cd /home/sebasvelace/kicad-circuit-ai
source .venv/bin/activate
pip install build twine

python3 -m build
python3 -m twine upload dist/*
```

Esto hace que `uvx kicad-circuit-ai` funcione globalmente.

---

## Próximos pasos después del mes

### v0.2 Targets
- `scripts/validate_component_yaml.py` — validar schema en CI
- Más componentes: ESP32, STM32F103, LM317, L298N, CD4017, ULN2003, MAX232, AMS1117
- Portuguese error messages (mercado brasileño)
- `check_before_export` hook: auto-validate antes de cada `export_gerber`

### Integración con KiCAD-MCP-Server
Puedes enviar un PR al repo de mixelpixx añadiendo `validate_before_export`:
```typescript
// En src/tools/export.ts — antes de exportar Gerbers
if (process.env.KICAD_AI_VALIDATE) {
  const result = await validateWithCircuitAI(schematicPath);
  if (result.hasCriticalErrors) {
    return { error: "Validation failed: " + result.summary };
  }
}
```

---

## Comandos de referencia rápida

```bash
# Activar el proyecto
cd /home/sebasvelace/kicad-circuit-ai && source .venv/bin/activate

# Correr tests
pytest tests/ -v

# Validar el schematic roto (demo)
PYTHONPATH=src python3 -c "
from kicad_circuit_ai.tools.validate import validate_from_file
print(validate_from_file('tests/fixtures/bad_555_netlist.xml', locale='es').format('es'))
"

# Agregar componente nuevo
cp components/NE555.yaml components/NUEVO_IC.yaml
# Editar con datasheet abierto
pytest tests/ -v  # verificar que no rompiste nada

# Publicar a PyPI (cuando esté listo)
python3 -m build && python3 -m twine upload dist/*
```

---

## Métricas para trackear

| Semana | Objetivo | Cómo medirlo |
|--------|----------|--------------|
| 1 | 20 GitHub stars | GitHub repo insights |
| 2 | MCP server corriendo en tu Claude Code | Demo funcional |
| 3 | 10+ componentes, 3+ contributors | GitHub contributors page |
| 4 | 100+ stars, post con 5k+ impresiones | GitHub + LinkedIn analytics |
