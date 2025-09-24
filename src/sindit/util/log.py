import logging

FORMAT = "%(asctime)s %(levelname)s: [%(filename)s - %(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("sindit")
logger.setLevel(logging.DEBUG)
