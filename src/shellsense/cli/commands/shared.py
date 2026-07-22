from __future__ import annotations

from shellsense.automation.engine import AutomationEngine
from shellsense.database.manager import DatabaseManager
from shellsense.intelligence.engine import IntelligenceEngine
from shellsense.marketplace.marketplace import MarketplaceManager
from shellsense.plugins.manager import PluginManager

_engine: IntelligenceEngine | None = None
_automation: AutomationEngine | None = None
_plugin_manager: PluginManager | None = None
_marketplace: MarketplaceManager | None = None


def get_engine() -> IntelligenceEngine:
    global _engine
    if _engine is None:
        db = DatabaseManager()
        _engine = IntelligenceEngine(db=db)
    return _engine


def get_automation_engine() -> AutomationEngine:
    global _automation
    if _automation is None:
        _automation = AutomationEngine()
    return _automation


def get_plugin_manager() -> PluginManager:
    global _plugin_manager
    if _plugin_manager is None:
        from shellsense.ai.core import AIEngine
        from shellsense.automation.engine import AutomationEngine
        from shellsense.database.manager import DatabaseManager
        from shellsense.intelligence.context_collectors import ContextCollector
        from shellsense.intelligence.formatter import ResponseFormatter
        from shellsense.knowledge.suggest import suggest_commands
        from shellsense.utils.config import ConfigManager

        db = DatabaseManager()
        ai_engine = AIEngine()
        automation = AutomationEngine()
        collector = ContextCollector()
        formatter = ResponseFormatter()
        config = ConfigManager()

        _plugin_manager = PluginManager(
            knowledge_engine=db,
            suggest_func=suggest_commands,
            ai_engine=ai_engine,
            context_collector=collector,
            automation_engine=automation,
            template_library=None,
            config_manager=config,
            shell_integration=None,
            formatter=formatter,
        )
        _plugin_manager.initialize()
    return _plugin_manager


def get_marketplace_manager() -> MarketplaceManager:
    global _marketplace
    if _marketplace is None:
        from shellsense.marketplace.enterprise import EnterprisePolicies
        from shellsense.utils.config import ConfigManager

        config = ConfigManager()
        pm = get_plugin_manager()
        enterprise = EnterprisePolicies(config_manager=config)

        _marketplace = MarketplaceManager(
            plugin_manager=pm,
            enterprise_policies=enterprise,
        )
        _marketplace.repos._load()
    return _marketplace
