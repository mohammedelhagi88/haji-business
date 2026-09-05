"""Default module registration for the Haji AI runtime."""
from __future__ import annotations

from .module_registry import ModuleRegistry, ModuleSpec


def build_default_registry() -> ModuleRegistry:
    registry = ModuleRegistry()
    modules = [
        ("memory", "ذاكرة حاجي الدائمة والسياقية"),
        ("commands", "فهم وتنفيذ أوامر المستخدم الآمنة"),
        ("tasks", "إدارة المهام والمتابعة"),
        ("notifications", "الأحداث والتنبيهات والإشعارات"),
        ("prayer", "خدمات الصلاة والمواقيت"),
        ("sports", "المتابعة والتحليل الرياضي"),
        ("business", "مساعدة وتحليل الأعمال"),
        ("mashareq", "وحدة شركة المشارق الأولى"),
        ("trading", "تحليل الأسواق والتداول الآمن"),
        ("communication", "إعداد الرسائل والمكالمات والتواصل"),
        ("education", "الجامعات والتعليم والمنح"),
        ("vision", "تحليل الصور والمستندات والمخططات"),
        ("voice", "التعامل مع الصوت والتحويل إلى نص"),
    ]
    for name, description in modules:
        registry.register(ModuleSpec(name=name, description=description))
    return registry
