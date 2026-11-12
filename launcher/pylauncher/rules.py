"""Sürüm JSON'larındaki 'rules' bloklarının değerlendirilmesi."""
import platform
import re

from .paths import os_arch, os_name


def rule_matches(rule, features) -> bool:
    os_rule = rule.get("os")
    if os_rule:
        if "name" in os_rule and os_rule["name"] != os_name():
            return False
        if "arch" in os_rule and os_rule["arch"] != os_arch():
            return False
        if "version" in os_rule:
            try:
                if not re.search(os_rule["version"], platform.version()):
                    return False
            except re.error:
                return False
    for key, wanted in (rule.get("features") or {}).items():
        if bool(features.get(key, False)) != wanted:
            return False
    return True


def allowed(rules, features=None) -> bool:
    """Kural yoksa serbest; varsa eşleşen son kuralın action'ı geçerlidir."""
    if not rules:
        return True
    features = features or {}
    result = False
    for rule in rules:
        if rule_matches(rule, features):
            result = rule.get("action") == "allow"
    return result
