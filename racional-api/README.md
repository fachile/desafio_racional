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

# 2. Crear el archivo de entorno (ya incluido con defaults)
cp .env.example .env   # o usar el .env incluido

# 3. Levantar todo (DB + migraciones + API)
docker compose up --build
```

La API estará disponible en: `http://localhost:8000`

Documentación interactiva (Swagger): `http://localhost:8000/docs`

---

## Rutas de la API

### Usuarios
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/users` | Crear usuario (crea wallet automáticamente) |
| `GET` | `/users/{user_id}` | Obtener usuario |
| `PATCH` | `/users/{user_id}` | Editar información personal |

### Wallets
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/wallets/{wallet_id}/deposit` | Depositar fondos desde banco (idempotente) |
| `POST` | `/wallets/{wallet_id}/withdrawal` | Retirar fondos hacia banco |

### Portafolios
| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/portfolios?user_id=...` | Crear portafolio para un usuario |
| `PATCH` | `/portfolios/{portfolio_id}` | Editar nombre o descripción |
| `POST` | `/portfolios/{portfolio_id}/fund` | Transferir cash desde wallet al portafolio |
| `GET` | `/portfolios/{portfolio_id}/total` | Total valorizado del portafolio |
| `GET` | `/portfolios/{portfolio_id}/movements?limit=50` | Últimos movimientos |
| `POST` | `/portfolios/{portfolio_id}/orders` | Registrar orden de compra o venta |

---

## Flujo principal

```
1. POST /users                          → se crea usuario + wallet
2. POST /wallets/{id}/deposit           → se agrega cash a la wallet
3. POST /portfolios?user_id={id}        → se crea un portafolio
4. POST /portfolios/{id}/fund           → se mueve cash wallet → portafolio
5. POST /portfolios/{id}/orders         → se compran acciones
6. GET  /portfolios/{id}/total          → se consulta el valor total
```

---

## Modelo de datos

### `users`
Información personal del usuario. Se crea sin portafolio ni cash inicial.

### `wallets`
Relación 1:1 con `users`. Representa la cuenta de dinero del usuario (fuente de fondos). Se crea automáticamente al crear un usuario.

**Decisión:** separar la wallet del portafolio permite que el usuario tenga múltiples portafolios sin duplicar el saldo total.

### `portfolios`
Relación 1:N con `users`. Cada portafolio es un vehículo de inversión independiente con su propio `cash_balance`, fondeado desde la wallet.

### `cash_movements`
Registro de depósitos y retiros sobre la wallet.

**Idempotencia:** si el cliente envía un `idempotency_key`, la operación se ejecuta solo una vez. Reenvíos con la misma key devuelven el resultado original sin doble ejecución.

### `portfolio_transfers`
Audit trail de transferencias wallet → portafolio. Permite reconstruir el historial de asignación de capital.

### `holdings`
Posición actual por ticker en cada portafolio. Se actualiza en cada orden.

`avg_buy_price` usa **promedio ponderado**: si tienes 10 AAPL a $150 y compras 5 más a $160 → avg = (10×150 + 5×160) / 15 = $153.33.

### `orders`
Registro inmutable de órdenes ejecutadas. `price_at_execution` guarda el precio mock al momento de la operación.

### Precios mock

Los precios de acciones son estáticos y viven en `app/core/mock_prices.py`. Tickers disponibles:
`AAPL, GOOGL, MSFT, AMZN, TSLA, META, NVDA, JPM, BRK.B, V`

### Currency

Todos los modelos tienen un campo `currency` (USD, CLP, EUR). Hoy todas las transacciones usan la misma moneda, pero el modelo soporta expansión futura. Se valida que la moneda del movimiento coincida con la del portafolio/wallet.

---

## Decisiones de diseño

| Decisión | Justificación |
|----------|--------------|
| `cash_balance` como campo real (no calculado) | Evita sumas costosas sobre toda la historia de movimientos en cada consulta |
| Wallet como intermediario | Permite múltiples portafolios por usuario con un saldo central unificado |
| Órdenes ejecutadas inmediatamente | Simplifica el modelo para este contexto; se puede agregar estado `pending` luego |
| `avg_buy_price` en holdings | Estándar de la industria para calcular P&L real de una posición |
| Idempotencia con `idempotency_key` único en DB | Garantía a nivel de base de datos, no solo de aplicación |
| `Numeric(18,4)` para montos | Evita errores de punto flotante en operaciones financieras |

---

## Uso de IA

Este proyecto fue desarrollado en colaboración con Claude (Anthropic). El flujo de trabajo fue:

1. **Diseño conversacional:** antes de escribir código, se discutió el modelo de datos, decisiones de arquitectura (wallet vs cash en user, 1:1 vs 1:N portafolios, idempotencia, currency como campo) con Claude como contraparte técnica.
2. **Generación de código:** Claude generó los modelos SQLAlchemy, schemas Pydantic, servicios y routers siguiendo el diseño acordado.
3. **Toma de decisiones:** Claude aportó justificaciones técnicas para cada decisión (ej. `Numeric` sobre `Float`, promedio ponderado, atomicidad en órdenes).
4. **Revisión humana:** todas las decisiones de negocio y arquitectura fueron validadas y ajustadas por el desarrollador durante la conversación.
