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
