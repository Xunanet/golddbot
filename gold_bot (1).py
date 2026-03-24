"""
Bot autónomo de Paper Trading — GOLD (XAU/USD)
================================================
- Consulta el precio real de GOLD cada 10 segundos
- Compra automáticamente cuando el precio está cerca del nivel de compra
- Vende automáticamente cuando el precio está cerca del nivel de venta
- Registra todo en consola y en gold_bot.log

Instalación:
    pip install requests

Uso:
    python gold_bot.py
"""

import time
import requests
import logging
from datetime import datetime

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
BUY_PRICE    = 4400.0   # Precio objetivo de COMPRA  ← cambia este valor
SELL_PRICE   = 4420.0   # Precio objetivo de VENTA   ← cambia este valor
TOLERANCE    = 2.0      # Distancia máxima permitida (±2 USD para GOLD)
QTY          = 1        # Cantidad de contratos/onzas
CHECK_EVERY  = 10       # Segundos entre cada consulta de precio
CAPITAL      = 100_000  # Capital inicial en paper trading (USD)

# ─── LOGGING ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler("gold_bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ─── ESTADO DEL BOT ───────────────────────────────────────────────────────────
state = {
    "capital":        CAPITAL,
    "posicion":       0,          # 0 = sin posición, 1 = comprado
    "precio_entrada": 0.0,
    "pnl_total":      0.0,
    "trades":         0,
    "ganadas":        0,
    "perdidas":       0,
}

# ─── OBTENER PRECIO REAL DE GOLD ──────────────────────────────────────────────
def obtener_precio() -> float | None:
    """Obtiene el precio actual de GOLD/USD desde Yahoo Finance (gratis, sin API key)."""
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5)
        data = r.json()
        precio = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return float(precio)
    except Exception as e:
        log.warning(f"⚠️  Error obteniendo precio: {e}")
        return None

# ─── LÓGICA DE TRADING ────────────────────────────────────────────────────────
def evaluar(precio: float):
    cerca_compra = abs(precio - BUY_PRICE)  <= TOLERANCE
    cerca_venta  = abs(precio - SELL_PRICE) <= TOLERANCE

    # ── COMPRA ────────────────────────────────────────────────────────────────
    if cerca_compra and state["posicion"] == 0:
        state["posicion"]       = 1
        state["precio_entrada"] = precio
        coste = precio * QTY
        state["capital"] -= coste
        log.info(f"🟢 COMPRA  | Precio: {precio:.2f} | Qty: {QTY} | Capital restante: ${state['capital']:,.2f}")

    # ── VENTA ─────────────────────────────────────────────────────────────────
    elif cerca_venta and state["posicion"] == 1:
        beneficio = (precio - state["precio_entrada"]) * QTY
        state["capital"]   += precio * QTY
        state["pnl_total"] += beneficio
        state["trades"]    += 1

        if beneficio >= 0:
            state["ganadas"] += 1
            emoji = "✅"
        else:
            state["perdidas"] += 1
            emoji = "❌"

        log.info(
            f"🔴 VENTA   | Precio: {precio:.2f} | Qty: {QTY} | "
            f"Beneficio: ${beneficio:+.2f} {emoji} | "
            f"Capital total: ${state['capital']:,.2f}"
        )
        state["posicion"]       = 0
        state["precio_entrada"] = 0.0

    else:
        dist_compra = abs(precio - BUY_PRICE)
        dist_venta  = abs(precio - SELL_PRICE)
        pos_txt = "EN POSICION" if state["posicion"] == 1 else "sin posición"
        log.info(
            f"👁  Precio: {precio:.2f} | "
            f"Dist.compra: {dist_compra:.2f} | Dist.venta: {dist_venta:.2f} | "
            f"{pos_txt}"
        )

# ─── RESUMEN PERIÓDICO ────────────────────────────────────────────────────────
def imprimir_resumen():
    winrate = (state["ganadas"] / state["trades"] * 100) if state["trades"] > 0 else 0
    log.info(
        f"\n{'─'*55}\n"
        f"  RESUMEN  |  Capital: ${state['capital']:,.2f}  |  "
        f"PnL: ${state['pnl_total']:+,.2f}\n"
        f"  Trades: {state['trades']}  |  Ganadas: {state['ganadas']}  |  "
        f"Perdidas: {state['perdidas']}  |  Winrate: {winrate:.0f}%\n"
        f"{'─'*55}"
    )

# ─── BUCLE PRINCIPAL ──────────────────────────────────────────────────────────
def main():
    log.info("=" * 55)
    log.info("  BOT GOLD — PAPER TRADING INICIADO")
    log.info(f"  Compra en: {BUY_PRICE} ± {TOLERANCE}")
    log.info(f"  Venta en:  {SELL_PRICE} ± {TOLERANCE}")
    log.info(f"  Capital inicial: ${CAPITAL:,}")
    log.info("=" * 55)

    ciclo = 0
    while True:
        precio = obtener_precio()

        if precio is not None:
            evaluar(precio)

        ciclo += 1
        # Resumen cada 30 ciclos (5 minutos si CHECK_EVERY=10)
        if ciclo % 30 == 0:
            imprimir_resumen()

        time.sleep(CHECK_EVERY)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("\n🛑 Bot detenido manualmente.")
        imprimir_resumen()
