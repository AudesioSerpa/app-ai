"""
Sistema Central de Custos & Margem — Facilita AI

Regras (aprovadas pelo dono do produto):
- Custos da API são a fonte econômica primária (por caractere, por imagem, por segundo).
- Margem BRUTA MÍNIMA de 70% SOBRE O PREÇO cobrado, não markup.
  Fórmula: preco_base = custo_total / (1 - target_gross_margin)
  Ex.: custo 0,30 BRL, margem 70% -> preço 1,00 BRL.
- Considerar buffer cambial (variação USD->BRL) antes de calcular preço.
- Considerar taxa do meio de pagamento (Mercado Pago ~5%) só quando houver venda.
- Nunca vender abaixo do preço mínimo protegido.

Este módulo NÃO vende créditos ainda — só é a fonte da verdade para:
1) validar limites de uso;
2) calcular custo estimado e real de cada geração;
3) registrar custo real no histórico (para termos dados antes de definir pacotes).
"""
from __future__ import annotations
import os
from typing import Any

# Overridável via env se necessário
_env = os.environ.get

AI_PRICING: dict[str, Any] = {
    # Câmbio & margens globais (podem ser sobrescritos pelo admin no futuro)
    "usd_to_brl": float(_env("USD_TO_BRL", "5.10")),
    "fx_safety_buffer": float(_env("FX_SAFETY_BUFFER", "0.10")),   # 10% proteção cambial
    "target_gross_margin": float(_env("TARGET_GROSS_MARGIN", "0.70")),  # 70% mínimo
    "mp_fee_rate": float(_env("MP_FEE_RATE", "0.05")),             # 5% Mercado Pago

    # ---------------- ÁUDIO ----------------
    "audio": {
        "provider": "elevenlabs",
        "model": _env("ELEVENLABS_MODEL", "eleven_flash_v2_5"),
        "voice_id_default": _env("ELEVENLABS_VOICE_ID", "HOfBIVLhom4mc9WvXfyH"),  # Andrea Lot - pt-BR
        "usd_per_char": float(_env("ELEVENLABS_USD_PER_CHAR", "0.00005")),
        # Estimativa apenas para pré-validação (nunca para cobrança)
        "estimate_chars_per_second": float(_env("AUDIO_EST_CHARS_PER_SEC", "15")),
        # Limites
        "free_daily_seconds": int(_env("AUDIO_FREE_DAILY_SEC", "60")),
        "free_max_seconds_per_gen": int(_env("AUDIO_FREE_MAX_SEC_GEN", "60")),
        # Premium: NUNCA ilimitado até definirmos pacotes reais.
        "premium_daily_seconds": int(_env("AUDIO_PREMIUM_DAILY_SEC", "300")),
        "premium_max_seconds_per_gen": int(_env("AUDIO_PREMIUM_MAX_SEC_GEN", "60")),
        # Proteção universal (soft limit — pode ser subido depois)
        "hard_max_chars_per_request": int(_env("AUDIO_HARD_MAX_CHARS", "3000")),
        # Créditos Facilita por char (unidade interna configurável)
        "credits_per_char": int(_env("AUDIO_CREDITS_PER_CHAR", "1")),
    },

    # ---------------- IMAGEM ----------------
    "image": {
        "provider": "fal_ai",
        "model": "fal-ai/flux/schnell",
        "usd_per_image": float(_env("FAL_USD_PER_IMAGE", "0.003")),
        "free_daily_generations": int(_env("IMG_FREE_DAILY", "3")),
        "premium_daily_generations": int(_env("IMG_PREMIUM_DAILY", "50")),
        "max_prompt_chars": int(_env("IMG_MAX_PROMPT_CHARS", "1000")),
        # Créditos Facilita por imagem (alinhado ao custo médio por caractere de áudio)
        "credits_per_image": int(_env("IMG_CREDITS_PER_GEN", "60")),
    },

    # ---------------- TEXTO ----------------
    # Emergent LLM Key é pré-paga pela plataforma — não cobra do usuário por token
    "text": {
        "provider": "emergent_llm",
        "provider_prepaid": True,
        "free_daily_generations": int(_env("TXT_FREE_DAILY", "3")),
        "premium_daily_generations": int(_env("TXT_PREMIUM_DAILY", "500")),
    },
}


def estimate_audio_seconds(text: str) -> float:
    """Estimativa RÁPIDA e conservadora só para pré-validação. Nunca use para cobrar."""
    cps = AI_PRICING["audio"]["estimate_chars_per_second"] or 15
    return round(len(text) / cps, 3)


def calc_audio_api_cost_usd(chars: int) -> float:
    """Custo real da API ElevenLabs em USD para X caracteres."""
    return chars * AI_PRICING["audio"]["usd_per_char"]


def calc_image_api_cost_usd(num_images: int = 1) -> float:
    return num_images * AI_PRICING["image"]["usd_per_image"]


def credits_for_audio(chars: int) -> int:
    """Custo em Créditos Facilita para gerar áudio com N caracteres."""
    return int(chars) * int(AI_PRICING["audio"]["credits_per_char"])


def credits_for_image(num_images: int = 1) -> int:
    return int(num_images) * int(AI_PRICING["image"]["credits_per_image"])


def usd_to_brl_protected(usd: float) -> float:
    """Converte USD -> BRL aplicando buffer cambial (fx_safety_buffer)."""
    base = AI_PRICING["usd_to_brl"]
    buf = AI_PRICING["fx_safety_buffer"]
    return usd * base * (1 + buf)


def min_sale_price_brl(cost_usd: float, *, apply_mp_fee: bool = False) -> float:
    """
    Preço MÍNIMO em BRL que preserva 70% margem BRUTA sobre o preço.
    Fórmula: preco_base = custo_brl / (1 - target_gross_margin)
    Se houver venda via MP, aplica também: preco / (1 - mp_fee_rate)
    """
    cost_brl = usd_to_brl_protected(cost_usd)
    m = AI_PRICING["target_gross_margin"]
    if m >= 1 or m < 0:
        raise ValueError("target_gross_margin fora do intervalo [0, 1)")
    price = cost_brl / (1 - m)
    if apply_mp_fee:
        fee = AI_PRICING["mp_fee_rate"]
        if 0 <= fee < 1:
            price = price / (1 - fee)
    # Arredonda 4 casas para observabilidade; a venda final trunca em 2 casas.
    return round(price, 4)


def pricing_snapshot() -> dict[str, Any]:
    """Snapshot público (sem segredos) para o admin/painel debugar cálculos."""
    return {
        "usd_to_brl": AI_PRICING["usd_to_brl"],
        "fx_safety_buffer": AI_PRICING["fx_safety_buffer"],
        "target_gross_margin": AI_PRICING["target_gross_margin"],
        "mp_fee_rate": AI_PRICING["mp_fee_rate"],
        "audio": {
            "model": AI_PRICING["audio"]["model"],
            "usd_per_char": AI_PRICING["audio"]["usd_per_char"],
            "free_daily_seconds": AI_PRICING["audio"]["free_daily_seconds"],
            "premium_daily_seconds": AI_PRICING["audio"]["premium_daily_seconds"],
            "free_max_seconds_per_gen": AI_PRICING["audio"]["free_max_seconds_per_gen"],
        },
        "image": {
            "model": AI_PRICING["image"]["model"],
            "usd_per_image": AI_PRICING["image"]["usd_per_image"],
            "free_daily_generations": AI_PRICING["image"]["free_daily_generations"],
            "max_prompt_chars": AI_PRICING["image"]["max_prompt_chars"],
        },
    }
