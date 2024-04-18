import logging

FORMAT = "%(asctime)s CT-ONTO-LIB: [%(filename)s - %(funcName)s] %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("ct-onto-lib")
logger.setLevel(logging.INFO)
