"""
Sistema de Carteira Universal — Créditos Facilita AI

Regras críticas (FASE 2 aprovada):
- 1 crédito Facilita = unidade INTEIRA interna (sem microcentavos no UI).
- Toda movimentação vai para `wallet_ledger` IMUTÁVEL (append-only).
- Operações atômicas: reserva usa `findOneAndUpdate` com condição `balance >= required`.
- Nunca permitir saldo negativo.
- Idempotência via `reservation_id` / `payment_id`.
- Modo SIMULATION: registra shadow ledger com `mode=simulation`, NÃO altera saldo real do usuário.
- Modo ACTIVE: registra ledger real e altera `credit_balance`.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional, Literal

# Tipos de movimentação no ledger
LedgerType = Literal[
    "purchase",           # +créditos comprados
    "consume",            # -créditos consumidos (commit real)
    "reserve",            # -créditos reservados (hold)
    "reserve_release",    # +créditos estornados de reserva (falha)
    "reserve_adjust",     # ± ajuste da reserva (diferença estimado vs real)
    "admin_grant",        # +créditos concedidos manualmente
    "admin_debit",        # -créditos removidos manualmente
    "refund",             # +créditos estornados por chargeback/reembolso
    "promo",              # +créditos promocionais (expiram)
    "premium_grant",      # +créditos mensais Premium
]

# Categoria de crédito (para futura ordenação FIFO de consumo)
CreditCategory = Literal["purchased", "promotional", "premium"]


class WalletService:
    def __init__(self, db):
        self.db = db

    # -------- Saldo & consulta --------
    async def get_balance(self, user_id: str) -> int:
        doc = await self.db.users.find_one({"id": user_id}, {"credit_balance": 1})
        return int((doc or {}).get("credit_balance") or 0)

    async def get_wallet_snapshot(self, user_id: str, ledger_limit: int = 20) -> dict:
        balance = await self.get_balance(user_id)
        entries = await self.db.wallet_ledger.find(
            {"user_id": user_id}, {"_id": 0}
        ).sort("created_at", -1).to_list(ledger_limit)
        return {"balance": balance, "recent": entries}

    # -------- Ledger helpers --------
    async def _append_ledger(
        self,
        *,
        user_id: str,
        type: LedgerType,
        credits: int,
        balance_before: int,
        balance_after: int,
        tool: Optional[str] = None,
        provider: Optional[str] = None,
        estimated_cost_usd: Optional[float] = None,
        real_cost_usd: Optional[float] = None,
        provider_usage: Optional[dict] = None,
        payment_id: Optional[str] = None,
        package_id: Optional[str] = None,
        reference_id: Optional[str] = None,
        category: Optional[CreditCategory] = None,
        mode: Literal["simulation", "active"] = "active",
        expires_at: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> dict:
        entry = {
            "id": str(uuid.uuid4()),
            "transaction_id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": type,
            "credits": int(credits),
            "balance_before": int(balance_before),
            "balance_after": int(balance_after),
            "tool": tool,
            "provider": provider,
            "estimated_cost_usd": estimated_cost_usd,
            "real_cost_usd": real_cost_usd,
            "provider_usage": provider_usage,
            "payment_id": payment_id,
            "package_id": package_id,
            "reference_id": reference_id,
            "category": category,
            "mode": mode,
            "expires_at": expires_at,
            "notes": notes,
            "currency": "credits_facilita",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.db.wallet_ledger.insert_one(entry.copy())
        entry.pop("_id", None)
        return entry

    # -------- SIMULATION (sombra) --------
    # Não altera saldo. Apenas grava no ledger com mode=simulation para análise.
    async def simulate_consume(
        self,
        *,
        user_id: str,
        credits: int,
        tool: str,
        provider: str,
        estimated_cost_usd: float,
        real_cost_usd: float,
        provider_usage: dict,
        reference_id: Optional[str] = None,
    ) -> dict:
        # No shadow mode não descontamos — balance_before == balance_after == saldo atual
        balance = await self.get_balance(user_id)
        return await self._append_ledger(
            user_id=user_id, type="consume", credits=-int(credits),
            balance_before=balance, balance_after=balance,
            tool=tool, provider=provider,
            estimated_cost_usd=estimated_cost_usd, real_cost_usd=real_cost_usd,
            provider_usage=provider_usage, reference_id=reference_id,
            mode="simulation",
            notes="Shadow: créditos que TERIAM sido debitados.",
        )

    # -------- ACTIVE (real) --------
    async def reserve_atomic(
        self, *, user_id: str, credits: int, tool: str, reference_id: str,
    ) -> Optional[dict]:
        """
        Reserva atômica de créditos. Retorna dict {balance_before, balance_after}
        ou None se saldo insuficiente. Usa findOneAndUpdate condicional.
        """
        if credits <= 0:
            return None
        # Atomic: só decrementa se balance >= credits
        result = await self.db.users.find_one_and_update(
            {"id": user_id, "credit_balance": {"$gte": credits}},
            {"$inc": {"credit_balance": -credits}},
            projection={"credit_balance": 1},
            return_document=True,  # retorna doc já atualizado
        )
        if result is None:
            return None
        balance_after = int(result.get("credit_balance", 0))
        balance_before = balance_after + credits
        await self._append_ledger(
            user_id=user_id, type="reserve", credits=-credits,
            balance_before=balance_before, balance_after=balance_after,
            tool=tool, reference_id=reference_id,
            mode="active",
            notes="Reserva antes de chamar API paga.",
        )
        return {"balance_before": balance_before, "balance_after": balance_after}

    async def release_reserve(
        self, *, user_id: str, credits: int, tool: str, reference_id: str, reason: str = "Falha na API",
    ) -> dict:
        """Estorno integral de reserva (+credits de volta)."""
        result = await self.db.users.find_one_and_update(
            {"id": user_id},
            {"$inc": {"credit_balance": credits}},
            projection={"credit_balance": 1},
            return_document=True,
        )
        if result is None:
            # usuário não existe — cria com saldo dos créditos estornados
            balance_after = credits
        else:
            balance_after = int(result.get("credit_balance", 0))
        balance_before = balance_after - credits
        return await self._append_ledger(
            user_id=user_id, type="reserve_release", credits=credits,
            balance_before=balance_before, balance_after=balance_after,
            tool=tool, reference_id=reference_id, mode="active", notes=reason,
        )

    async def commit_reserve(
        self,
        *,
        user_id: str,
        reserved_credits: int,
        actual_credits: int,
        tool: str,
        provider: str,
        reference_id: str,
        estimated_cost_usd: Optional[float] = None,
        real_cost_usd: Optional[float] = None,
        provider_usage: Optional[dict] = None,
    ) -> dict:
        """
        Ajusta reserva ao valor real e faz commit.
        Se actual_credits > reserved_credits → debita a diferença adicional (com proteção).
        Se actual_credits < reserved_credits → devolve a diferença.
        """
        diff = int(actual_credits) - int(reserved_credits)
        if diff > 0:
            # cobrar diferença; se não houver saldo, cobra o máximo disponível (nunca negativo)
            result = await self.db.users.find_one_and_update(
                {"id": user_id, "credit_balance": {"$gte": diff}},
                {"$inc": {"credit_balance": -diff}},
                projection={"credit_balance": 1},
                return_document=True,
            )
            if result is None:
                # saldo insuficiente para diferença — cobra até zerar
                doc = await self.db.users.find_one({"id": user_id}, {"credit_balance": 1}) or {}
                available = int(doc.get("credit_balance") or 0)
                if available > 0:
                    await self.db.users.update_one({"id": user_id}, {"$inc": {"credit_balance": -available}})
                    balance_after = 0
                    balance_before = available
                    debited = available
                else:
                    balance_after = 0; balance_before = 0; debited = 0
                await self._append_ledger(
                    user_id=user_id, type="reserve_adjust", credits=-debited,
                    balance_before=balance_before, balance_after=balance_after,
                    tool=tool, reference_id=reference_id, mode="active",
                    notes="Ajuste após consumo real superior ao reservado (proteção contra saldo negativo).",
                )
            else:
                balance_after = int(result["credit_balance"])
                balance_before = balance_after + diff
                await self._append_ledger(
                    user_id=user_id, type="reserve_adjust", credits=-diff,
                    balance_before=balance_before, balance_after=balance_after,
                    tool=tool, reference_id=reference_id, mode="active",
                )
        elif diff < 0:
            # devolve
            give_back = -diff
            result = await self.db.users.find_one_and_update(
                {"id": user_id}, {"$inc": {"credit_balance": give_back}},
                projection={"credit_balance": 1}, return_document=True,
            )
            balance_after = int((result or {}).get("credit_balance") or give_back)
            balance_before = balance_after - give_back
            await self._append_ledger(
                user_id=user_id, type="reserve_adjust", credits=give_back,
                balance_before=balance_before, balance_after=balance_after,
                tool=tool, reference_id=reference_id, mode="active",
            )
        # Registro final de "consume" com custos reais
        balance = await self.get_balance(user_id)
        return await self._append_ledger(
            user_id=user_id, type="consume", credits=-int(actual_credits),
            balance_before=balance, balance_after=balance,  # já reflete pós-ajuste
            tool=tool, provider=provider, reference_id=reference_id,
            estimated_cost_usd=estimated_cost_usd, real_cost_usd=real_cost_usd,
            provider_usage=provider_usage, mode="active",
            notes="Commit consumo real.",
        )

    # -------- Compra de créditos --------
    async def credit_purchase(
        self, *, user_id: str, credits: int, payment_id: str, package_id: str,
        price_brl: float, category: CreditCategory = "purchased",
    ) -> Optional[dict]:
        """Adiciona créditos comprados. Idempotente via payment_id."""
        # Idempotência: se já existe ledger com esse payment_id + type=purchase, ignora
        existing = await self.db.wallet_ledger.find_one({"payment_id": payment_id, "type": "purchase"})
        if existing:
            return None  # já processado
        result = await self.db.users.find_one_and_update(
            {"id": user_id}, {"$inc": {"credit_balance": credits}},
            projection={"credit_balance": 1}, return_document=True, upsert=False,
        )
        if result is None:
            return None
        balance_after = int(result["credit_balance"])
        balance_before = balance_after - credits
        return await self._append_ledger(
            user_id=user_id, type="purchase", credits=credits,
            balance_before=balance_before, balance_after=balance_after,
            payment_id=payment_id, package_id=package_id, category=category,
            mode="active", notes=f"Compra R$ {price_brl:.2f}",
        )

    async def admin_grant(self, *, user_id: str, credits: int, admin_id: str, notes: str = "") -> dict:
        result = await self.db.users.find_one_and_update(
            {"id": user_id}, {"$inc": {"credit_balance": credits}},
            projection={"credit_balance": 1}, return_document=True,
        )
        balance_after = int((result or {}).get("credit_balance") or credits)
        balance_before = balance_after - credits
        return await self._append_ledger(
            user_id=user_id,
            type="admin_grant" if credits > 0 else "admin_debit",
            credits=credits,
            balance_before=balance_before, balance_after=balance_after,
            reference_id=admin_id, mode="active", notes=notes or "Ação administrativa",
        )
