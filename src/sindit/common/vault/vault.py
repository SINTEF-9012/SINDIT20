import os
import threading

import hvac
from jproperties import Properties
from sindit.util.log import logger


class Vault:
    """
    Interface for a vault service
    """

    def resolveSecret(self, secretPath) -> str:
        """
        Resolve a secret from the vault
        :param secretPath: The path to the secret
        :return: The secret value, None if the secret was not found
        """
        pass

    def storeSecret(self, secretPath, secretValue) -> bool:
        """
        Store a secret in the vault
        :param secretPath: The path to the secret
        :param secretValue: The value of the secret
        :return: True if the secret was stored successfully, False otherwise
        """
        pass

    def deleteSecret(self, secretPath) -> bool:
        """
        Delete a secret from the vault
        :param secretPath: The path to the secret
        :return: True if the secret was deleted successfully, False otherwise
        """

        pass

    def listSecretPaths(self):
        """
        List all secret paths in the vault
        :return: A list of secret paths
        """
        pass


class FsVault(Vault):
    """
    Implements a vault backed by a properties file.
    """

    def __init__(self, vaultPath):
        self.vaultPath = vaultPath
        configs = Properties()
        try:
            with open(vaultPath, "rb") as f:
                configs.load(f, "utf-8")
        except FileNotFoundError:
            with open(vaultPath, "wb") as f:
                pass  # Create an empty file
        self.configs = configs
        logger.info(f"Loaded vault from {vaultPath}")

    def resolveSecret(self, secretPath) -> str:
        secret = self.configs.get(secretPath)
        return secret.data if secret else None

    def storeSecret(self, secretPath, secretValue) -> bool:
        self.configs[secretPath] = secretValue
        with open(self.vaultPath, "wb") as f:
            self.configs.store(f, encoding="utf-8")
        return True

    def deleteSecret(self, secretPath) -> bool:
        del self.configs[secretPath]
        with open(self.vaultPath, "wb") as f:
            self.configs.store(f, encoding="utf-8")
        return True

    def listSecretPaths(self):
        return [key for key in self.configs.keys()]


# Warning: This implementation is not tested.
class HashiCorpVault(Vault):
    """
    Implements a vault backed by HashiCorp Vault.
    Warning: This implementation is not tested.
    """

    def __init__(self, vaultUrl, token):
        self.vaultUrl = vaultUrl
        self.token = token
        self.client = hvac.Client(url=vaultUrl, token=token)
        logger.info(f"Connected to HashiCorp Vault at {vaultUrl}")

    def resolveSecret(self, secretPath) -> str:
        response = self.client.secrets.kv.v2.read_secret_version(path=secretPath)
        return response["data"]["data"]["value"]

    def storeSecret(self, secretPath, secretValue) -> bool:
        self.client.secrets.kv.v2.create_or_update_secret(
            path=secretPath, secret=dict(value=secretValue)
        )
        return True

    def deleteSecret(self, secretPath) -> bool:
        self.client.secrets.kv.v2.delete_metadata_and_all_versions(path=secretPath)
        return True

    def listSecretPaths(self):
        try:
            response = self.client.secrets.kv.v2.list_secrets(path="")
            return response["data"]["keys"]
        except hvac.exceptions.InvalidPath:
            return []


class UserScopedHashiCorpVault(Vault):
    """Wraps a HashiCorpVault and transparently prefixes all paths with the username.

    This ensures secrets stored by user ``alice`` at path ``myConn/pass``
    live under ``alice/myConn/pass`` in HashiCorp Vault, isolated from
    other users.
    """

    def __init__(self, base_vault: "HashiCorpVault", username: str):
        self._base = base_vault
        self._prefix = username

    def _scoped(self, path: str) -> str:
        return f"{self._prefix}/{path}"

    def resolveSecret(self, secretPath) -> str:
        return self._base.resolveSecret(self._scoped(secretPath))

    def storeSecret(self, secretPath, secretValue) -> bool:
        return self._base.storeSecret(self._scoped(secretPath), secretValue)

    def deleteSecret(self, secretPath) -> bool:
        return self._base.deleteSecret(self._scoped(secretPath))

    def listSecretPaths(self):
        prefix = f"{self._prefix}/"
        all_paths = self._base.listSecretPaths()
        return [p[len(prefix) :] for p in all_paths if p.startswith(prefix)]


class VaultService:
    """Manages a pool of per-user :class:`Vault` instances.

    Subclasses implement :meth:`_create_vault` to build the appropriate vault
    type for a given username.
    """

    def __init__(self):
        self._vaults: dict[str, Vault] = {}
        self._lock = threading.Lock()

    def get_vault(self, username: str) -> Vault:
        """Return (lazily creating) the vault scoped to *username*."""
        with self._lock:
            if username not in self._vaults:
                self._vaults[username] = self._create_vault(username)
            return self._vaults[username]

    def _create_vault(self, username: str) -> Vault:
        raise NotImplementedError


class FsVaultService(VaultService):
    """Per-user file-system vault.

    Each user gets their own ``.properties`` file named
    ``<stem>_<username><suffix>`` placed next to the base vault file.
    For example, if the base vault is ``vault.properties`` and the user is
    ``alice``, her vault is stored in ``vault_alice.properties``.
    """

    def __init__(self, vault_path: str):
        super().__init__()
        base_dir = os.path.dirname(vault_path)
        base_name = os.path.basename(vault_path)
        stem, suffix = os.path.splitext(base_name)
        self._base_dir = base_dir
        self._stem = stem
        self._suffix = suffix

    def _create_vault(self, username: str) -> FsVault:
        user_vault_path = os.path.join(
            self._base_dir, f"{self._stem}_{username}{self._suffix}"
        )
        return FsVault(user_vault_path)


class HashiCorpVaultService(VaultService):
    """Per-user HashiCorp Vault.

    A single :class:`HashiCorpVault` client is shared; each user's secrets
    are transparently prefixed with ``<username>/`` via
    :class:`UserScopedHashiCorpVault`.
    """

    def __init__(self, vault_url: str, token: str):
        super().__init__()
        self._base_vault = HashiCorpVault(vault_url, token)

    def _create_vault(self, username: str) -> UserScopedHashiCorpVault:
        return UserScopedHashiCorpVault(self._base_vault, username)
