"""Dataspace sync must only touch assets published by its own dataspace node.

Several SINDIT dataspace nodes (in different workspaces) can share one EDC
connector. Before this fix, sync treated every ``sindit-*`` asset as its own and
deleted the other node's offers.
"""

from types import SimpleNamespace

from sindit.dataspace.connector_dataspace import DataspaceConnector
from sindit.dataspace.edc_mapping import asset_belongs_to, build_http_asset

NS = "http://sindit.sintef.no/2.0#sindit/"
DS_A, WS_A = NS + "sintef-dataspace", NS + "NordicTestLab"
DS_B, WS_B = NS + "sindit-ds-connector", NS + "training-factory"


def asset(node_uri, dataspace_uri, workspace_uri=None):
    return build_http_asset(
        SimpleNamespace(uri=node_uri),
        sindit_api_base_url="http://sindit-2:9017",
        dataspace_uri=dataspace_uri,
        workspace_uri=workspace_uri,
    )


def test_belongs_to_own_node_and_workspace():
    assert asset_belongs_to(asset(NS + "a", DS_A, WS_A), DS_A, WS_A)


def test_other_dataspace_node_is_not_ours():
    assert not asset_belongs_to(asset(NS + "location1", DS_B, WS_B), DS_A, WS_A)


def test_same_node_uri_in_other_workspace_is_not_ours():
    assert not asset_belongs_to(asset(NS + "a", DS_A, WS_B), DS_A, WS_A)


def test_asset_without_workspace_matches_on_dataspace_only():
    assert asset_belongs_to(asset(NS + "a", DS_A), DS_A, WS_A)


def test_unknown_owner_and_foreign_assets_never_match():
    no_owner = {"@id": "sindit-0123", "dataAddress": {"type": "HttpData"}}
    foreign = {"@id": "mvd-test-asset", "dataAddress": {"queryParams": "x=1"}}
    assert not asset_belongs_to(no_owner, DS_A, WS_A)
    assert not asset_belongs_to(foreign, DS_A, WS_A)
    assert not asset_belongs_to("not a dict", DS_A, WS_A)


class FakeEDC:
    def __init__(self, assets):
        self.assets = {a["@id"]: a for a in assets}
        self.deleted_assets, self.deleted_cds = [], []

    def list_assets(self, query=None):
        return list(self.assets.values())

    def create_policy_definition(self, payload):
        return payload["@id"]

    def create_asset(self, payload):
        self.assets[payload["@id"]] = payload
        return payload["@id"]

    def create_contract_definition(self, payload):
        return payload["@id"]

    def delete_contract_definition(self, cd_id):
        self.deleted_cds.append(cd_id)
        return True

    def delete_asset(self, asset_id):
        self.deleted_assets.append(asset_id)
        self.assets.pop(asset_id, None)
        return True


def test_sync_removes_only_own_orphans():
    mine_listed = asset(NS + "chamber", DS_A, WS_A)
    mine_orphan = asset(NS + "old-node", DS_A, WS_A)
    other_nodes = asset(NS + "location1", DS_B, WS_B)
    edc = FakeEDC([mine_listed, mine_orphan, other_nodes])

    kg = SimpleNamespace(load_node_by_uri=lambda uri: SimpleNamespace(uri=uri))
    connector = DataspaceConnector(
        endpoint="http://edc/management",
        sindit_api_base_url="http://sindit-2:9017",
        sindit_workspace_uri=WS_A,
        uri=DS_A,
        kg_connector=kg,
    )
    connector.client = edc

    summary = connector.sync(
        SimpleNamespace(dataspaceAssets=[SimpleNamespace(uri=NS + "chamber")])
    )

    assert edc.deleted_assets == [mine_orphan["@id"]]
    assert other_nodes["@id"] in edc.assets
    assert summary == {"local": 1, "remote": 2, "published": 1, "removed": 1}
