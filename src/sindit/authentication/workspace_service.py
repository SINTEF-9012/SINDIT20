import os
import json
from sindit.util.log import logger

from sindit.authentication.models import User, Workspace
from sindit.util.environment_and_configuration import get_environment_variable

from sindit.knowledge_graph.graph_model import (
    KG_NS,
)


class WorkspaceService:
    def __init__(self):
        self.WORKSPACE_PATH = get_environment_variable(
            "WORKSPACE_PATH",
            optional=True,
            default="environment_and_configuration/workspace.json",
        )

        if os.path.exists(self.WORKSPACE_PATH):
            with open(self.WORKSPACE_PATH, "r") as f:
                try:
                    self.workspaces = json.load(f)
                except json.JSONDecodeError:
                    logger.error("Error decoding JSON from %s", self.WORKSPACE_PATH)
                    self.workspaces = {}
        else:
            logger.warning(
                "Workspace file %s does not exist, creating empty file",
                self.WORKSPACE_PATH,
            )
            with open(self.WORKSPACE_PATH, "w") as f:
                f.write("{}")
            self.workspaces = {}

    def create_workspace(self, user: User, workspace_name: str) -> Workspace:
        if user.username not in self.workspaces:
            self.workspaces[user.username] = {}

        # If workspace is a uri, extract the local part as workspace_name
        if workspace_name.startswith("http://") or workspace_name.startswith(
            "https://"
        ):
            # Split by both # and / and get the last non-empty part
            parts = workspace_name.replace("#", "/").split("/")
            workspace_name = next(
                (part for part in reversed(parts) if part), workspace_name
            )

        # Replace any special characters in workspacename and username with -
        workspace_name = "".join(
            c if c.isalnum() or c in ("-") else "-" for c in workspace_name
        )
        username = "".join(
            c if c.isalnum() or c in ("-") else "-" for c in user.username
        )

        # Set the new workspace as default, unset other workspaces as default
        for ws in self.workspaces[user.username].values():
            ws["is_default"] = False

        # Check if workspace with same name exists for user
        if workspace_name in self.workspaces[user.username]:
            new_workspace = Workspace(**self.workspaces[user.username][workspace_name])
            new_workspace.is_default = True
        else:
            new_workspace = Workspace(
                name=workspace_name,
                uri=f"{KG_NS}{username}/{workspace_name}",
                is_default=True,
            )

        self.workspaces[user.username][workspace_name] = new_workspace.model_dump()
        self._save_workspaces()
        return new_workspace

    def _save_workspaces(self):
        with open(self.WORKSPACE_PATH, "w") as f:
            json.dump(self.workspaces, f, indent=4)

    def get_current_workspace(self, user: User) -> Workspace:
        if user.username in self.workspaces:
            workspace_dict = self.workspaces[user.username]
            # Query for the default workspace, otherwise return the first one
            if workspace_dict:
                for ws_name, ws_data in workspace_dict.items():
                    if ws_data.get("is_default", False):
                        return Workspace(**ws_data)
                # Return first workspace if no default found
                first_workspace = next(iter(workspace_dict.values()))
                first_workspace["is_default"] = True
                self._save_workspaces()
                return Workspace(**first_workspace)

        # Otherwise return a default workspace
        default_workspace = self.create_workspace(user, "DefaultWorkspace")
        return default_workspace

    def list_workspaces(self, user: User) -> list[Workspace]:
        if user.username in self.workspaces:
            return [Workspace(**ws) for ws in self.workspaces[user.username].values()]
        return []
