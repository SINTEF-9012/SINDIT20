import fastapi
from util.environment_and_configuration import ConfigGroups, get_configuration
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


description = """This is the API for the SINDIT project.
It provides access to the knowledge graph and the data stored in it."""

tags_metadata = [
    {
        "name": "Knowledge Graph",
        "description": "Operations related to the knowledge graph",
    },
    {
        "name": "Connection",
        "description": "Operations related to the connections and properties",
    },
    {
        "name": "Dataspace",
        "description": "Operations related to the dataspace",
    },
    {
        "name": "Workspace",
        "description": "Operations related to the workspace",
    },
    {
        "name": "Vault",
        "description": "Operations related to the secret vault and authenitcation",
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

# Add ProxyHeadersMiddleware so FastAPI sees the correct scheme/host behind Traefik
# Otherwise, DELETE get into a https > http > https ping pong where auth header is lost
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")


# TODO: This should not be hardcoded
# TODO: For actual deployment, this needs to be set properly
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT"],
    allow_headers=["*"],
)
