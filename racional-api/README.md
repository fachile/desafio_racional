# Investment API

API REST para gestión de inversiones: depósitos, retiros, órdenes de compra/venta y seguimiento de portafolios.

## Stack

- **Python 3.11** + **FastAPI**
- **PostgreSQL 15**
- **SQLAlchemy 2** (ORM) + **Alembic** (migraciones)
- **Docker Compose**

---

## Cómo ejecutar

### Requisitos
- Docker y Docker Compose instalados

### Pasos

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd investment-api

# 2. Crear el archivo de entorno
cp .env.example .env

# 3. Levantar todo (DB + migraciones + API)
docker compose up --build
```

La API estará disponible en: `http://localhost:8000`

Documentación interactiva (Swagger): `http://localhost:8000/docs`

---

## Rutas de la API

### Health check
| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Verificar que el servicio está corriendo |

### Usuarios
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/users` | Crear usuario (crea wallet automáticamente) |
| `GET` | `/users/{user_id}` | Obtener usuario |
| `PATCH` | `/users/{user_id}` | Editar información personal |

### Wallets
| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/wallets/by-user/{user_id}` | Obtener wallet de un usuario |
| `POST` | `/wallets/{wallet_id}/deposit` | Depositar fondos desde banco |
| `POST` | `/wallets/{wallet_id}/withdrawal` | Retirar fondos hacia banco |

### Portafolios
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/portfolios?user_id=...` | Crear portafolio para un usuario |
| `GET` | `/portfolios/by-user/{user_id}` | Listar portafolios de un usuario |
| `PATCH` | `/portfolios/{portfolio_id}` | Editar nombre o descripción |
| `PUT` | `/portfolios/{portfolio_id}/allocations` | Actualizar asignaciones % por acción y rebalancear automáticamente |
| `POST` | `/portfolios/{portfolio_id}/fund` | Transferir cash desde wallet → portafolio e invertir según allocations |
| `POST` | `/portfolios/{portfolio_id}/withdraw` | Retirar fondos del portafolio (vende proporcional) y devuelve a wallet |
| `GET` | `/portfolios/{portfolio_id}/total` | Valuación detallada con market value, avg_buy_price, gain/loss por holding |
| `GET` | `/portfolios/{portfolio_id}/movements?limit=50` | Historial de órdenes ejecutadas |

---

## Flujo típico para un nuevo usuario

### Flujo básico
```
1. POST /users                                  → se crea usuario + wallet
2. POST /wallets/{id}/deposit                   → se agrega cash a la wallet
3. POST /portfolios?user_id={id}                → se crea un portafolio
4. POST /portfolios/{id}/fund                   → se mueve cash wallet → portafolio + compra automática según allocations (lo que no alcance queda como cash)
5. GET  /portfolios/{id}/total                  → se consulta el valor total
6. PUT  /portfolios/{id}/allocations            → rebalancear a nuevas asignaciones (vende/compra automático)
7. GET  /portfolios/{id}/movements              → historial de órdenes ejecutadas
8. POST /portfolios/{id}/withdraw {amount}      → retira fondos (vende proporcional, devuelve a wallet)
```


---

## Modelo de datos

### `users`
Información personal del usuario. Se crea sin portafolio y con una waller sin cash inicial.

### `wallets`
Relación 1:1 con `users`. Representa la cuenta de dinero del usuario (fuente de fondos). Se crea automáticamente al crear un usuario.

**Decisión:** separar la wallet del portafolio permite que el usuario tenga múltiples portafolios sin duplicar el saldo total.

### `portfolios`
Relación 1:N con `users`. Cada portafolio es un vehículo de inversión independiente con su propio `cash_balance`, fondeado desde la wallet.

### `cash_movements`
Registro de depósitos y retiros sobre la wallet.

### `portfolio_allocations`
Asignaciones target de cada acción en un portafolio. Permite rebalancing automático.

Ejemplo: `{AAPL: 40%, GOOGL: 30%, MSFT: 30%}` + `cash_target: 10%`

Al actualizar allocations, el sistema:
- Vende posiciones que exceden el target %
- Compra las que están por debajo
- Ejecuta órdenes automáticamente hasta alcanzar los % exactos


`avg_buy_price` usa **promedio ponderado**: si tienes 10 AAPL a $150 y compras 5 más a $160 → avg = (10×150 + 5×160) / 15 = $153.33.

### `orders`
Registro inmutable de órdenes ejecutadas. `price_at_execution` guarda el precio mock al momento de la operación.

### Precios mock

Los precios de acciones son estáticos y viven en `app/core/mock_prices.py`. Tickers disponibles:
`AAPL, GOOGL, MSFT, AMZN, TSLA, META, NVDA, JPM, BRK.B, V`

### Moneda

Todas las transacciones se expresan en **CLP** (pesos chilenos). 

**Almacenamiento:** para evitar errores de punto flotante, los montos se guardan como enteros:

---

## Decisiones de diseño

### Seguridad & Autenticación
| Decisión | Justificación |
|----------|--------------|
| **Sin password en usuarios** | Este es un backend didáctico enfocado en lógica de negocio, no en autenticación. Agregar auth requeriría JWT, bcrypt, refresh tokens, CORS, lo que añade complejidad significativa. La identificación se hace por `user_id` simple para debugging ágil y focus en portafolios. En producción, integrar OAuth2 o Keycloak |
| **Sin `idempotency_key` en DB** | Idempotencia agregaba: columna única, índice, validación pre-insert, manejo de collisiones. Para MVP de inversión, retries del cliente son controlados. Simplificamos: si el cliente re-envía un depósito, es responsabilidad del cliente usar lógica de retries en la aplicación. Cuando escale, agregar `Retry-After` headers y idempotency tokens |

### Almacenamiento & Tipos de Dato
| Decisión | Justificación |
|----------|--------------|
| **IDs como Integer (no UUID)** | UUIDs agregan 36 bytes por registro, complican debugging (es más fácil "ver user 5" que "ver user 550e8400-e29b-41d4-a716-446655440000"), requieren índices más grandes. Para un sistema interno, ints secuenciales son suficientes. UUIDs son mejores para distribución/merging de datos |
| **`cash_balance` como campo real** | Evita sums costosos en cada consulta sobre toda la historia. Alternativa: calcular on-the-fly = O(n), con esta = O(1). Trade-off: mantener actualizado en cada movimiento (atomicidad con transacciones) |
| **BigInteger para montos (centavos)** | Evita errores de punto flotante en operaciones financieras. Ejemplo: `0.1 + 0.2 != 0.3` en Float. Almacenar `1000000` (CLP) como entero es exacto: no hay redondeo. Las APIs devuelven Decimal (amigable) pero la BD almacena ints |
| **Moneda única: CLP** | Se eliminó columna `currency` en cada tabla por simplificación. Todas las transacciones son CLP. Reduce: bytes por fila, validaciones, conversiones. Si mañana se necesita EUR/USD, extender es trivial (agregar columna + validar conversión). MVP = simple |

### Arquitectura
| Decisión | Justificación |
|----------|--------------|
| Wallet como intermediario | Permite múltiples portafolios por usuario sin duplicar saldo. Wallet = fuente única de fondos, portafolios = inversiones independientes |
| Tabla `portfolio_allocations` | Habilita rebalancing automático declarativo. Usuario define `{AAPL: 40%, GOOGL: 30%}`, sistema ejecuta trades automáticos |
| Órdenes ejecutadas inmediatamente | Simplifica el modelo (no hay estado `pending`/`filled`). |

---

## Evolución del Schema

### v0.1 (Migración 0001)
- Schema inicial con soporte multi-currency (USD, CLP, EUR)
- Montos con `Numeric(18,4)` (decimales, riesgo de float)
- `idempotency_key` único en DB
- Justificación: "cubrir todas las posibilidades"
- Problema: complejidad innecesaria en MVP

### v0.2 (Migración 0002)
- Agrega tabla `portfolio_allocations`
- Soporta rebalancing automático

### v0.3 (Migración 0003 - Actual) ✅
**Simplificación por experiencia MVP:**

| Cambio | Antes | Ahora | Razón |
|--------|-------|-------|-------|
| **Moneda** | Multi-currency (USD, CLP, EUR) | CLP only | No hay conversión, reduce validaciones y bugs. Agregar currencies es trivial después |
| **Almacenamiento de montos** | `Numeric(18,4)` (decimales) | `BigInteger` (centavos) | Elimina errores de float. 1 CLP = 1 unidad (entero exacto) |
| **Idempotencia** | `idempotency_key` único en BD | ❌ Eliminado | MVP no requiere garantía transaccional de BD. Cliente maneja retries |
| **Date** | Date de tablas | ❌ Eliminado | Ya se tiene created_at |
| **Identifiers** | Podría ser UUID | ints secuenciales | Más simples, faster, mejor debugging. UUIDs si hay distribución/merging |

**Impacto:** menos bytes/row, operaciones más rápidas, código más simple, debugging más fácil.

---

## Filosofía de diseño: MVP con foco en lógica de negocio

Este proyecto prioriza **claridad y simplicidad**:

### ✅ Qué incluye
- Lógica de inversión correcta (compra/venta, rebalancing, valuación)
- Precisión financiera (sin float errors)
- Datos consistentes (transacciones atómicas)
- Extensibilidad (fácil agregar features)

### ❌ Qué NO incluye (y por qué)
| Feature | Razón de exclusión | Cómo agregar |
|---------|-------------------|-------------|
| **Passwords & Auth** | Focus en portafolios, no en seguridad. MVP sin multi-tenant | Agregar OAuth2 / Keycloak cuando escale |
| **Idempotency DB** | Retries se manejan en cliente | Agregar Stripe-style `idempotency_key` header + endpoint |
| **Multi-currency** | Una sola moneda reduce bugs | Agregar tabla `currencies` + foreign key si crece |
| **UUID IDs** | Ints son más simples para MVP | Cambiar a UUID si hay distribución/replicación |
| **Status pending** para órdenes | Órdenes = inmediatas | Agregar state machine si hay validaciones complejas |
| **Precios en tiempo real** | Precios mock fijos en `app/core/mock_prices.py`. MVP se centra en lógica de la API. | Agregar worker async + Redis para polling de precios. O integrar WebSocket de broker real (IBKR, Interactive Brokers) |

---

## Uso de IA

Este proyecto fue desarrollado en colaboración con Claude (Anthropic). El flujo de trabajo fue:

1. **Diseño conversacional:** antes de escribir código, se discutió el modelo de datos, decisiones de arquitectura (wallet vs cash en user, 1:1 vs 1:N portafolios, simplificaciones de MVP) con Claude como contraparte técnica.
2. **Generación de código:** Claude generó los modelos SQLAlchemy, schemas Pydantic, servicios y routers siguiendo el diseño acordado.
3. **Toma de decisiones:** Claude aportó justificaciones técnicas para cada decisión de MVP (ej. ints vs UUID, BigInteger vs Numeric, single currency).
4. **Revisión humana:** todas las decisiones de negocio y arquitectura fueron validadas y ajustadas por el desarrollador durante la conversación.
