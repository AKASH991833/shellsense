from shellsense.database.manager import DatabaseManager
from shellsense.knowledge.engine import KnowledgeEngine
from shellsense.utils.config import ConfigManager
from shellsense.utils.logging import get_logger, setup_logging
from shellsense.utils.paths import ensure_shellsense_dir

logger = get_logger(__name__)


def initialize(verbose: bool = False) -> None:
    ensure_shellsense_dir()

    config = ConfigManager()
    log_level = config.get("logging.level", "INFO")
    setup_logging(level=log_level, verbose=verbose)

    logger.info("ShellSense AI initializing...")

    db = DatabaseManager()
    db.initialize()

    engine = KnowledgeEngine(db)
    count = engine.seed()
    if count > 0:
        logger.info("Seeded %d commands into knowledge base", count)

    db.close()

    plugins_enabled = config.get("plugins.enabled", True)
    if plugins_enabled:
        _initialize_plugins(config)

    marketplace_enabled = config.get("marketplace.enabled", True)
    if marketplace_enabled:
        _initialize_marketplace(config)

    logger.info("ShellSense AI initialized successfully")


def _initialize_plugins(config: ConfigManager) -> None:
    try:
        from shellsense.cli.commands.shared import get_plugin_manager

        pm = get_plugin_manager()
        auto_discover = config.get("plugins.auto_discover", True)
        auto_load = config.get("plugins.auto_load", False)

        if auto_discover:
            discovered = pm.discover()
            logger.debug("Discovered %d plugin(s)", len(discovered))

        if auto_load:
            for info in pm.list_plugins():
                try:
                    pm.load(info.id)
                    auto_enable = config.get("plugins.auto_enable", False)
                    if auto_enable:
                        pm.enable(info.id)
                except Exception as e:
                    logger.warning("Failed to auto-load plugin '%s': %s", info.id, e)

        logger.info(
            "Plugin subsystem initialized (%d plugins discovered)", pm.registry.count()
        )
    except Exception as e:
        logger.warning("Plugin subsystem initialization failed: %s", e)


def _initialize_marketplace(config: ConfigManager) -> None:
    try:
        from shellsense.cli.commands.shared import get_marketplace_manager

        mm = get_marketplace_manager()
        auto_sync = config.get("marketplace.auto_sync", False)

        if auto_sync:
            results = mm.sync_all()
            synced = sum(1 for r in results if r.success)
            logger.info(
                "Marketplace sync: %d/%d repositories synced", synced, len(results)
            )

        logger.info("Marketplace subsystem initialized")
    except Exception as e:
        logger.warning("Marketplace subsystem initialization failed: %s", e)
