[![Quality Gate Status](https://kubikk-ekkolodd.sintef.cloud/api/project_badges/measure?project=SINDIT&metric=alert_status&token=sqb_daa44a05f36e549bc45f72c29dcb10b1b04bb781)](https://kubikk-ekkolodd.sintef.cloud/dashboard?id=SINDIT)
[![Coverage](https://kubikk-ekkolodd.sintef.cloud/api/project_badges/measure?project=SINDIT&metric=coverage&token=sqb_daa44a05f36e549bc45f72c29dcb10b1b04bb781)](https://kubikk-ekkolodd.sintef.cloud/dashboard?id=SINDIT)

![Code Style Black](https://img.shields.io/badge/code%20style-black-black)
![Python Version](https://img.shields.io/badge/python-3.11-blue)

# SINDIT
<img src="./docs/img/favicon.ico" width=100>

SINTEF Digital Twin project

The development of this project has just begun...s


## Run backend using Docker Compose
To start the backend run (add the --build flag to build images before starting containers (build from scratch)):
```bash
docker-compose up
docker-compose up --build
```

This will build the GraphDB docker image and the FastAPI docker image.

The GraphDB instance will be available at: `localhost:7200`

The FastAPI documentation will be exposed at: `http://0.0.0.0:9017`

## Run backend locally
Desription of how to start the backend locally outside docker.
The backend consists of a GraphDB database and a FastAPI server.

### GraphDB
To start GraphDB, run these scripts from the GraphDB folder:
```bash
bash graphdb_install.sh
bash graphdb_preload.sh
bash graphdb_start.sh
```

To test your graphbd connection run from your base folder (/sindit):
```bash
poetry run python run_test.py
```

Go to localhost:7200 to configure graphdb

### API uvicorn server
To start the FastAPI server, run:
```bash
poetry run python run_sindit.py
```


### Run using vscode launcher

```bash
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python Debugger: Current File",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "cwd": "/Users/gorans/projects/monorepo/projects/sindit",
            "justMyCode": false,
            "envFile": "/Users/gorans/projects/monorepo/projects/sindit/environment_and_configuration/dev_environment_backend.env",

        }
    ]
}
```
## Using the API

### Authentication
The API requires a valid authentication token for most endpoints. Follow these steps to authenticate and use the API:

1. **Generate a Token**:
   - Use the `/token` endpoint to generate an access token.
   - Example `curl` command:
     ```bash
     curl -X POST "http://127.0.0.1:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=new_user&password=new_password"
     ```
   - Replace `new_user` and `new_password` with the credentials provided below.

2. **Use the Token**:
   - Include the token in the `Authorization` header for all subsequent API calls:
     ```bash
     curl -X GET "http://127.0.0.1:8000/endpoint" \
     -H "Authorization: Bearer your_generated_token_here"
     ```

3. **Access API Documentation**:
   - The FastAPI documentation is available at: `http://127.0.0.1:8000/docs`

---

### Generate New Username and Password
To add a new user, update the `fake_users_db` in `authentication_endpoints.py` with the following credentials:

```python
fake_users_db = {
    "new_user": {
        "username": "new_user",
        "full_name": "New User",
        "email": "new_user@example.com",
        "hashed_password": "$2b$12$eW5j9GdY3.EciS3oKQxJjOyIpoUNiFZxrON4SXt3wVrgSbE1gDMba",  # Password: new_password
        "disabled": False,
    }
}
```

To generate a new hashed password, use the  Python snippet in `password_hash.py`.
Replace `"new_password"` with your desired password.

---
