import os

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
    _vault_path = get_environment_variable("FSVAULT_PATH")
    if not os.path.isabs(_vault_path):
        _vault_path = os.path.join(os.path.dirname(__file__), _vault_path)
    secret_vault: Vault = FsVault(_vault_path)
else:
    # setting up hashicorp vault
    hashicorp_url = get_environment_variable("HASHICORP_URL")
    hashicorp_token = get_environment_variable("HASHICORP_TOKEN")
    secret_vault: Vault = HashiCorpVault(hashicorp_url, hashicorp_token)
