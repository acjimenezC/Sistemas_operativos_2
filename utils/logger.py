import logging
logger = logging.getLogger('recruitment_bot')
if not logger.handlers:
    h = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    h.setFormatter(formatter)
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
