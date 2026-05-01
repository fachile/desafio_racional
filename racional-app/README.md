# Racional App

Pequeña aplicación React + Vite para visualizar métricas de inversión (charts, indicadores y evolución intradía).

## Requisitos

- Node.js 18+ (o LTS compatible)
- npm o Yarn

## Instalación

1. Clona el repositorio.
2. Desde la raíz del proyecto instala dependencias:

```bash
npm install
# o
yarn install
```

## Configuración

Crea un archivo `.env` en la raíz con las siguientes variables:

- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_APP_ID`



## Ejecutar en desarrollo

Arranca el servidor de desarrollo con HMR:

```bash
npm run dev
# o
yarn dev
```

La app estará disponible en `http://localhost:5173` (o el puerto que indique Vite).

## Construir y desplegar

Generar build de producción:

```bash
npm run build
# o
yarn build
```


## Estructura relevante

- `src/` — código fuente React
- `src/components/` — componentes (charts, tarjetas, indicadores)
- `src/hooks/` — hooks personalizados para evolución e intraday
- `src/firebase.js` — inicialización de Firebase

## Uso de IA

Este proyecto fue desarrollado en colaboración con Claude y GitHub Copilot. El flujo de trabajo fue:

1. **Diseño conversacional:** antes de escribir código se discutió decisiones de arquitectura y diseño con Claude como contraparte técnica.
2. **Generación de código:** Se creo el proyecto con Vite, se generaron componentes y hooks iniciales utilizando Claude. Luego, se utilizó GitHub Copilot para iterar y mejorar el código.
4. **Revisión humana:** todas las decisiones de diseño y arquitectura fueron validadas y ajustadas por el desarrollador durante la conversación.
