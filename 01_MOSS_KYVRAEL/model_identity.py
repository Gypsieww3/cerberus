"""Deterministic display metadata for recognized Ollama model families.

The Ollama tag alone does not prove that local weights are authentic; all
attribution is to the publicly named model *family*, not to a checked hash.
Never infer that an arbitrary custom fine-tune was authored by its base vendor.
"""

KNOWN_FAMILIES = {
    "qwen2.5": ("Qwen2.5", "Equipa Qwen, Alibaba Cloud",
                "https://qwenlm.github.io/blog/qwen2.5/"),
    "qwen2.5-coder": ("Qwen2.5-Coder", "Equipa Qwen, Alibaba Cloud",
                      "https://qwenlm.github.io/blog/qwen2.5/"),
    "qwen2.5-math": ("Qwen2.5-Math", "Equipa Qwen, Alibaba Cloud",
                     "https://qwenlm.github.io/blog/qwen2.5/"),
}


def model_identity(model):
    """Return factual model-family metadata separate from LLM-generated text."""
    if not isinstance(model, str) or not 1 <= len(model) <= 100:
        raise ValueError("Invalid model")
    # Only exact official family identifiers. Custom names are never assigned
    # to the original developer without inspection of a model manifest.
    family_key = model.partition(":")[0].lower()
    known = KNOWN_FAMILIES.get(family_key)
    if known is None:
        return {
            "model": model,
            "family": "Não identificada pelo catálogo",
            "developer": "Origem por verificar",
            "source": None,
            "verification": "unverified",
            "note": "Um nome local ou modelo personalizado não comprova quem o treinou.",
        }
    family, developer, source = known
    return {
        "model": model,
        "family": family,
        "developer": developer,
        "source": source,
        "verification": "family_name",
        "note": "Origem da família pública; os pesos do modelo local não foram auditados.",
    }
