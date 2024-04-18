import logging

FORMAT = "%(asctime)s SINDIT: [%(filename)s - %(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("sindit")
logger.setLevel(logging.INFO)
