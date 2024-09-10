import fastapi
from util.environment_and_configuration import ConfigGroups, get_configuration

description = """This is the API for the SINDIT project.
It provides access to the knowledge graph and the data stored in it."""

tags_metadata = [
    {
        "name": "Knowledge Graph",
        "description": "Operations related to the knowledge graph",
    },
    {
        "name": "Workspace",
        "description": "Operations related to the workspace",
    },
    {
        "name": "Connection",
        "description": "Operations related to the connections and properties",
    },
    {
        "name": "Vault",
        "description": "Operations related to the secret vault",
    },
    {
        "name": "Metamodel",
        "description": "Operations related to the metamodel (e.g., units, semantics)",
    },
]

api_version = get_configuration(ConfigGroups.API, "api_version")
app = fastapi.FastAPI(
    title="SINDIT API",
    description=description,
    version=api_version,
    openapi_tags=tags_metadata,
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)
