import asyncio
from front.frontend_bot import start_bot
from application.custodian_archetypes.chronicler.back.init_db import init_db
from application.tech_utils.log_set_up import setup_logging
from logging import getLogger

def main():
    setup_logging()
    logger = getLogger(__name__)
    logger.info("[Chronicle starting]")
    logger.info("[DB INIT STARTED]")
    init_db()
    logger.info("[DB INIT ENDED. STARTING BOT]")
    asyncio.run(start_bot())

if __name__ == "__main__":
    main()