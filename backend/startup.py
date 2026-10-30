"""
TalentFlow AI — Subsystem Warm-Up Compatibility Bridge
Exposes warm_services from app.core.warmup for backward compatibility.
"""
from app.core.warmup import warm_services

__all__ = ["warm_services"]
