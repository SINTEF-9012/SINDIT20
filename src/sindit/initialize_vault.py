from sindit.common.vault.vault import FsVault, HashiCorpVault, Vault
from sindit.util.environment_and_configuration import (
    get_environment_variable,
    get_environment_variable_bool,
)
from sindit.util.log import logger

logger.info("Initializing vault ...")

use_hashicorp_vault = get_environment_variable_bool(
    "USE_HASHICORP_VAULT", optional=True, default="false"
)
if not use_hashicorp_vault:
    secret_vault: Vault = FsVault(get_environment_variable("FSVAULT_PATH"))
else:
    # setting up hashicorp vault
    hashicorp_url = get_environment_variable("HASHICORP_URL")
    hashicorp_token = get_environment_variable("HASHICORP_TOKEN")
    secret_vault: Vault = HashiCorpVault(hashicorp_url, hashicorp_token)
