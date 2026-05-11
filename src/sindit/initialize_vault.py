import os

from sindit.common.vault.vault import (
    FsVault,
    FsVaultService,
    HashiCorpVault,
    HashiCorpVaultService,
    Vault,
    VaultService,
)
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
    vault_service: VaultService = FsVaultService(_vault_path)
else:
    # setting up hashicorp vault
    hashicorp_url = get_environment_variable("HASHICORP_URL")
    hashicorp_token = get_environment_variable("HASHICORP_TOKEN")
    secret_vault: Vault = HashiCorpVault(hashicorp_url, hashicorp_token)
    vault_service: VaultService = HashiCorpVaultService(hashicorp_url, hashicorp_token)


def get_vault_for_username(username: str | None) -> Vault:
    """Return the vault scoped to *username*, or the global vault as fallback."""
    if username:
        return vault_service.get_vault(username)
    return secret_vault


def get_username_from_graph_uri(graph_uri: str | None) -> str | None:
    """Extract the username from a workspace graph URI.

    Workspace URIs have the form ``http://sindit.sintef.no/2.0#<username>/<workspace>``.
    Returns ``None`` if the URI cannot be parsed.
    """
    if not graph_uri:
        return None
    try:
        fragment = str(graph_uri).split("#", 1)[1]  # "<username>/<workspace>"
        username = fragment.split("/")[0]
        return username or None
    except (IndexError, Exception):
        return None
