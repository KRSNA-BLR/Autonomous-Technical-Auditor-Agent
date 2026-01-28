# 🎨 Research Agent Dashboard

Dashboard moderno para interactuar con el Agente de Investigación Técnica.

## ⚡ Características

- 🔍 **Búsqueda Intuitiva**: Input con animaciones que responde a tu escritura
- 📊 **Resultados Visuales**: Tarjetas con síntesis, hallazgos y fuentes
- 📄 **Exportar PDF**: Genera reportes profesionales con un click
- 💾 **Memoria**: Historial de consultas anteriores
- 🌓 **Modo Oscuro/Claro**: Tema adaptable
- ✨ **Animaciones**: Transiciones suaves con Framer Motion

## 🚀 Inicio Rápido

```bash
# Instalar dependencias
npm install

# Modo desarrollo
npm run dev

# Abrir http://localhost:3000
```

## 🛠️ Stack Tecnológico

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| React | 19.x | UI Framework |
| Vite | 6.x | Build Tool |
| TypeScript | 5.x | Type Safety |
| Tailwind CSS | 4.x | Estilos |
| Framer Motion | 12.x | Animaciones |
| jsPDF | 4.x | Exportar PDF |
| Lucide React | - | Iconos |

## 📁 Estructura

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # Componentes base (Button, Card, etc.)
│   │   ├── Header.tsx       # Cabecera con logo y tema
│   │   ├── SearchInput.tsx  # Input de búsqueda animado
│   │   ├── LoadingState.tsx # Estados de carga
│   │   ├── ResultsCard.tsx  # Tarjeta de resultados
│   │   ├── MemoryPanel.tsx  # Panel de historial
│   │   └── StatusBadge.tsx  # Badge de estado API
│   ├── hooks/
│   │   ├── useResearch.ts   # Hook para investigaciones
│   │   ├── useMemory.ts     # Hook para historial
│   │   └── useExportPdf.ts  # Hook para exportar PDF
│   ├── lib/
│   │   ├── api.ts           # Cliente API
│   │   └── utils.ts         # Utilidades
│   ├── App.tsx              # Componente principal
│   ├── main.tsx             # Entry point
│   └── index.css            # Estilos globales
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## 🎯 Uso

### 1. Hacer una búsqueda

Escribe tu pregunta en el input y presiona Enter o el botón de búsqueda.

### 2. Ver resultados

- **Síntesis**: Resumen de la investigación
- **Hallazgos clave**: Puntos importantes numerados
- **Fuentes**: Links a las referencias usadas

### 3. Exportar a PDF

Haz click en "Exportar PDF" para descargar un reporte profesional.

### 4. Historial

Consulta tus búsquedas anteriores en el panel derecho.

## 🔧 Configuración

El frontend se conecta al backend en `http://localhost:8000` por defecto.

Para cambiar esto, modifica el proxy en `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://tu-servidor:puerto',
    }
  }
}
```

## 🐳 Docker

El frontend incluye un Dockerfile para producción:

```bash
# Build de producción
docker build -t research-frontend .

# Ejecutar
docker run -p 3000:80 research-frontend
```

## 📝 Scripts

| Comando | Descripción |
|---------|-------------|
| `npm run dev` | Servidor de desarrollo |
| `npm run build` | Build de producción |
| `npm run preview` | Preview del build |
| `npm run lint` | Linter |

## 🎨 Personalización

### Colores

Edita las CSS variables en `src/index.css`:

```css
:root {
  --primary: 240 5.9% 10%;
  --background: 0 0% 100%;
  /* ... */
}
```

### Animaciones

Las animaciones usan Framer Motion. Modifica los valores de `transition` en los componentes:

```tsx
<motion.div
  animate={{ opacity: 1 }}
  transition={{ duration: 0.5 }}
/>
```

---

⚡ Desarrollado con React + Vite + Tailwind CSS
