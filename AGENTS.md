# AGENTS.md - SINDIT Digital Twin Framework

## Project Overview
SINDIT (SINTEF Digital Twin) is a Python-based digital twin framework developed by SINTEF. It provides a semantic knowledge graph backend for managing digital twin assets, their properties, and connections to various data sources. The framework exposes a REST API for interacting with the knowledge graph and supports real-time data streaming from IoT devices and databases.

**Version:** 2.0.8
**Python:** 3.11 - 3.12
**License:** MIT
**Repository:** https://github.com/SINTEF-9012/SINDIT20

## Architecture Overview

### High-Level Components
```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI REST API                         │
│  (Authentication, KG Endpoints, Vault, Workspace, Dataspace)    │
├─────────────────────────────────────────────────────────────────┤
│                    Knowledge Graph Layer                        │
│         (RDF Models, SPARQL Queries, Graph Models)              │
├─────────────────────────────────────────────────────────────────┤
│                    Connector Layer                              │
│     (InfluxDB, MQTT, S3, PostgreSQL - Observer Pattern)         │
├─────────────────────────────────────────────────────────────────┤
│                    Persistence Layer                            │
│              (GraphDB, Vault, Workspace)                        │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack
- **API Framework:** FastAPI with uvicorn
- **Knowledge Graph:** GraphDB (RDF triple store)
- **Data Modeling:** RDFLib with Pydantic models
- **Authentication:** OAuth2 (in-memory or Keycloak)
- **Connectors:** InfluxDB, MQTT, S3/MinIO, PostgreSQL
- **Secret Management:** File-based vault or HashiCorp Vault

## Directory Structure

```
sindit/
├── src/
│   ├── sindit/                      # Main package
│   │   ├── api/                     # FastAPI endpoints
│   │   │   ├── api.py               # FastAPI app initialization
│   │   │   ├── kg_endpoints.py      # Knowledge graph CRUD operations
│   │   │   ├── kg_relationship_endpoints.py
│   │   │   ├── authentication_endpoints.py
│   │   │   ├── workspace_endpoints.py
│   │   │   ├── vault_endpoints.py
│   │   │   ├── dataspace_endpoints.py
│   │   │   ├── connection_endpoints.py
│   │   │   └── metamodel_endpoints.py
│   │   ├── authentication/          # Auth implementations
│   │   │   ├── authentication_service.py  # Base auth interface
│   │   │   ├── in_memory.py         # File-based auth
│   │   │   ├── keycloak.py          # Keycloak integration
│   │   │   └── workspace_service.py
│   │   ├── common/
│   │   │   ├── semantic_knowledge_graph/
│   │   │   │   ├── rdf_model.py     # Base RDF/Pydantic model
│   │   │   │   ├── SemanticKGPersistenceService.py
│   │   │   │   └── GraphDBPersistenceService.py
│   │   │   └── vault/
│   │   │       └── vault.py         # Secret management
│   │   ├── connectors/              # Data source connectors
│   │   │   ├── connector.py         # Base Connector/Property classes
│   │   │   ├── connector_factory.py # Factory pattern implementation
│   │   │   ├── connector_influxdb.py
│   │   │   ├── connector_mqtt.py
│   │   │   ├── connector_s3.py
│   │   │   ├── connector_postgresql.py
│   │   │   ├── property_influxdb.py
│   │   │   ├── property_mqtt.py
│   │   │   ├── property_s3.py
│   │   │   ├── property_postgresql.py
│   │   │   └── setup_connectors.py
│   │   ├── knowledge_graph/
│   │   │   ├── graph_model.py       # Domain models (Asset, Property, Connection)
│   │   │   ├── relationship_model.py
│   │   │   ├── dataspace_model.py
│   │   │   ├── kg_connector.py      # KG operations (CRUD, queries)
│   │   │   └── queries/             # SPARQL query templates
│   │   ├── dataspace/
│   │   │   └── connector_dataspace.py
│   │   ├── util/
│   │   │   ├── log.py
│   │   │   ├── environment_and_configuration.py
│   │   │   ├── datetime_util.py
│   │   │   └── client_api.py
│   │   ├── environment_and_configuration/
│   │   │   ├── config.cfg
│   │   │   ├── dev_environment_backend.env
│   │   │   └── docker_environment_backend.env
│   │   ├── run_sindit.py            # Application entry point
│   │   ├── initialize_kg_connectors.py
│   │   ├── initialize_vault.py
│   │   └── initialize_authentication.py
│   └── tests/                       # Test suite
├── GraphDB/                         # GraphDB Docker configuration
├── keycloak/                        # Keycloak configuration
├── docker-compose.yaml
├── Dockerfile
├── pyproject.toml                   # Poetry configuration
└── .gitlab-ci.yml                   # CI/CD pipeline
```

## Core Concepts

### 1. RDF Model System (`common/semantic_knowledge_graph/rdf_model.py`)
The `RDFModel` base class combines Pydantic validation with RDF serialization:
- Extends Pydantic `BaseModel` for data validation
- Provides `rdf()` method for turtle serialization
- `deserialize()` for loading from RDF graphs
- Handles circular references and nested objects
- Maps Python types to XSD datatypes

### 2. Domain Models (`knowledge_graph/graph_model.py`)
Core entities representing digital twin concepts:

- **`SINDITKG`** - Root knowledge graph container
- **`AbstractAsset`** - Base class for physical/virtual assets
- **`Connection`** - Data source connection configuration
- **`AbstractAssetProperty`** - Base property class
- **`DatabaseProperty`** - Properties backed by database queries
- **`StreamingProperty`** - Real-time streaming properties (MQTT)
- **`TimeseriesProperty`** - Time-series database properties (InfluxDB)
- **`S3ObjectProperty`** - Object storage references
- **`PropertyCollection`** - Grouped properties
- **`File`** - File references (deprecated, use S3ObjectProperty)

### 3. Relationship Models (`knowledge_graph/relationship_model.py`)
Predefined relationship types between assets:
- `ConsistOfRelationship`, `PartOfRelationship`
- `ConnectedToRelationship`, `DependsOnRelationship`
- `DerivedFromRelationship`, `MonitorsRelationship`
- `ControlsRelationship`, `SimulatesRelationship`
- `UsesRelationship`, `CommunicatesWithRelationship`
- `IsTypeOfRelationship`

### 4. Connector System (`connectors/`)
Observer pattern implementation for data source integration:

**Base Classes:**
- `Connector` - Observable that manages property observers
- `Property` - Observer that receives updates from connectors

**Implementations:**
- `InfluxDBConnector` - Time-series database queries
- `MQTTConnector` - Real-time message streaming
- `S3Connector` - Object storage with presigned URLs
- `PostgreSQLConnector` - Relational database queries

**Factory Pattern:**
- `connector_factory` - Creates connector instances by type
- `property_factory` - Creates property instances by type

### 5. Knowledge Graph Connector (`knowledge_graph/kg_connector.py`)
`SINDITKGConnector` provides high-level KG operations:
- `load_node_by_uri()` - Load single node with depth traversal
- `load_nodes_by_class()` - Paginated loading by type
- `save_node()` - Create/update nodes
- `delete_node()` - Remove nodes
- `find_node_by_attribute()` - Advanced search
- `get_relationships_by_node()` - Load relationships
- Named graph support via `set_graph_uri()`

### 6. API Endpoints
All endpoints require OAuth2 authentication token.

**Knowledge Graph (`/kg/*`):**
- `GET /kg/nodes` - List all nodes (paginated)
- `GET /kg/node` - Get node by URI
- `POST /kg/asset`, `/kg/connection`, `/kg/timeseries_property`, etc. - Create entities
- `DELETE /kg/node` - Delete by URI
- `GET /kg/stream` - SSE streaming for real-time properties
- `GET /kg/advanced_search_node` - Search with filters

**Workspace (`/workspace/*`):** Multi-tenant workspace management
**Vault (`/vault/*`):** Secret management
**Dataspace (`/dataspace/*`):** Data sharing configuration

## Development Guidelines

### Running Locally
```bash
# Install dependencies
poetry install

# Start GraphDB (from GraphDB/ directory)
bash graphdb_install.sh
bash graphdb_preload.sh
bash graphdb_start.sh

# Run API server
poetry run python src/sindit/run_sindit.py
```

### Running with Docker
```bash
docker-compose up --build
```

### Running Tests
```bash
# All tests (excluding slow and gitlab_exempt)
poetry run pytest -m "not slow and not gitlab_exempt"

# With coverage
poetry run coverage run -m pytest -m "not slow and not gitlab_exempt"
poetry run coverage report
```

### Test Markers
- `slow` - Long-running tests
- `gitlab_exempt` - Tests that don't work in CI
- `ble` - Tests requiring Bluetooth devices

### Code Style
- Formatter: Black (line length 88)
- Import sorting: isort (black profile)
- Linting: Use existing patterns in codebase

## Environment Variables

### Core Configuration
- `FAST_API_HOST` - API host (default: `0.0.0.0`)
- `FAST_API_PORT` - API port (default: `9017`)
- `GRAPHDB_HOST` - GraphDB host
- `GRAPHDB_PORT` - GraphDB port (default: `7200`)
- `GRAPHDB_USERNAME`, `GRAPHDB_PASSWORD` - GraphDB credentials
- `LOG_LEVEL` - Logging level (default: `INFO`)

### Authentication
- `USE_KEYCLOAK` - Enable Keycloak auth (`True`/`False`)
- `KEYCLOAK_SERVER_URL`, `KEYCLOAK_REALM`, `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET`
- `USER_PATH` - Path to user JSON (in-memory auth)
- `WORKSPACE_PATH` - Path to workspace JSON

### Secret Management
- `USE_HASHICORP_VAULT` - Enable HashiCorp Vault
- `FSVAULT_PATH` - File vault path

## Key Design Patterns

### 1. Observer Pattern (Connectors)
Connectors notify attached properties when data changes:
```python
connector.attach(property)  # Subscribe
connector.notify()          # Broadcast updates
property.update_value()     # Receive update
```

### 2. Factory Pattern (Connector Creation)
```python
connector_factory.register_builder("influxdb", InfluxDBConnectorBuilder())
connector = connector_factory.create("influxdb", host=..., port=...)
```

### 3. Repository Pattern (KG Operations)
`SINDITKGConnector` abstracts SPARQL operations behind a clean interface.

### 4. Named Graph Isolation
Multi-tenant support via named graphs - each workspace has its own graph URI.

## SPARQL Queries
Query templates in `knowledge_graph/queries/`:
- `load_node.sparql`, `load_nodes.sparql`
- `delete_node.sparql`, `delete_nodes.sparql`
- `insert_data.sparql`, `insert_delete.sparql`
- `get_uris_by_class_uri.sparql`
- `advanced_search_node.sparql`
- `find_unit.sparql`, `get_all_units.sparql`

## CI/CD Pipeline (GitLab)
Stages:
1. `test` - pytest, coverage
2. `analysis` - SonarQube
3. `build` - Docker images (sindit, sindit-graphdb)
4. `deploy` - Push to GitHub mirror

## Common Tasks

### Adding a New Connector Type
1. Create `connector_<type>.py` extending `Connector`
2. Create `property_<type>.py` extending `Property`
3. Register with factory: `connector_factory.register_builder()`
4. Add to `setup_connectors.py` initialization

### Adding a New Property Type
1. Create model in `graph_model.py` extending appropriate base
2. Add to `NodeURIClassMapping`
3. Add API endpoint in `kg_endpoints.py`
4. Add to response model unions

### Adding a New Relationship Type
1. Create class in `relationship_model.py`
2. Add to `RelationshipURIClassMapping`

## Namespace URIs
- **SINDIT Model:** `urn:samm:sindit.sintef.no:1.0.0#`
- **SINDIT KG:** `http://sindit.sintef.no/2.0#`
- **SAMM Units:** `urn:samm:org.eclipse.esmf.samm:unit:2.1.0#`
- **SAMM Meta:** `urn:samm:org.eclipse.esmf.samm:meta-model:2.1.0#`

## API Authentication Flow
1. `POST /token` with username/password (form data)
2. Receive JWT access token
3. Include `Authorization: Bearer <token>` in subsequent requests
4. Token validated via `get_current_active_user` dependency

## External Services
- **GraphDB** - Port 7200 (RDF triple store)
- **Keycloak** - Port 8080/8443 (Identity provider)
- **PostgreSQL** - Port 5433 (Keycloak backend)
- **pgAdmin** - Port 5050 (DB admin UI)
