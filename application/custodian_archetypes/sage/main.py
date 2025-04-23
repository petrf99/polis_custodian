from front.frontend_bot import start_bot
from application.custodian_archetypes.sage.back.init_db import init_db
from application.tech_utils.log_set_up import setup_logging
from logging import getLogger

def main():
    setup_logging()
    logger = getLogger(__name__)
    logger.info("[Sage starting]")
    init_db()
    start_bot()

if __name__ == "__main__":
    main()