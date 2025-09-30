from sindit.util.log import logger
from sindit.authentication.authentication_service import AuthService
from sindit.authentication.in_memory import InMemoryAuthService
from sindit.authentication.keycloak import KeycloakAuthService
from sindit.authentication.workspace_service import WorkspaceService
from sindit.util.environment_and_configuration import get_environment_variable_bool


USE_KEYCLOAK = get_environment_variable_bool(
    "USE_KEYCLOAK", optional=True, default=False
)
if USE_KEYCLOAK:
    logger.info("Using Keycloak for authentication")
    authService: AuthService = KeycloakAuthService()
else:
    logger.info("Using in-memory authentication")
    authService: AuthService = InMemoryAuthService()

workspaceService: WorkspaceService = WorkspaceService()