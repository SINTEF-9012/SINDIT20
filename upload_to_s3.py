#!/usr/bin/env python3
"""
Script to upload a file to S3 using the SINDIT API.

This script:
1. Creates an S3 object node in the knowledge graph
2. Retrieves a presigned upload URL
3. Uploads the file using the presigned URL
4. Verifies the upload was successful

Usage:
    python upload_to_s3.py --help

Example:
    python upload_to_s3.py
        --file test.jpg --bucket my-bucket --key uploads/test.jpg
        --connection-uri http://sindit.sinef.cloud/quasar/connection
        --api-url http://localhost:8000
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

import requests


class S3Uploader:
    """Helper class for uploading files to S3 via SINDIT API."""

    def __init__(
        self,
        api_base_url: str = "http://localhost:8000",
        username: str = None,
        password: str = None,
        token: str = None,
    ):
        """
        Initialize the S3Uploader.

        Args:
            api_base_url: Base URL of the SINDIT API
            username: Username for authentication (if using username/password)
            password: Password for authentication (if using username/password)
            token: Bearer token for authentication (if already authenticated)
        """
        self.api_base_url = api_base_url.rstrip("/")
        self.session = requests.Session()
        self.token = token

        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"
        elif username and password:
            self._authenticate(username, password)

    def _authenticate(self, username: str, password: str):
        """Authenticate with the API and get a token."""
        auth_url = f"{self.api_base_url}/token"
        response = self.session.post(
            auth_url,
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        token_data = response.json()
        self.token = token_data["access_token"]
        self.session.headers["Authorization"] = f"Bearer {self.token}"
        print(f"✓ Authenticated as {username}")

    def create_s3_object_node(
        self,
        bucket: str,
        key: str,
        connection_uri: str,
        asset_uri: Optional[str] = None,
        label: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:
        """
        Create an S3 object node in the knowledge graph.

        Args:
            bucket: S3 bucket name
            key: S3 object key (path within bucket)
            connection_uri: URI of the S3 connection in the knowledge graph
            asset_uri: Optional URI to link this property to an asset
            label: Optional label for the node
            description: Optional description for the node

        Returns:
            Response from the API containing the node URI and upload information
        """
        endpoint = f"{self.api_base_url}/kg/s3_object"

        # Generate a URI for the S3 object node if not provided
        if asset_uri is None:
            asset_uri = f"http://sindit.sintef.no/s3/{bucket}/{key.replace('/', '-')}"

        payload = {
            "uri": asset_uri,
            "bucket": bucket,
            "key": key,
            "propertyConnection": {"uri": connection_uri},
        }

        if label:
            payload["label"] = label
        if description:
            payload["description"] = description

        print("\nCreating S3 object node...")
        print(f"  Bucket: {bucket}")
        print(f"  Key: {key}")
        print(f"  Connection: {connection_uri}")

        response = self.session.post(endpoint, json=payload)

        # Try to get error details before raising
        if not response.ok:
            try:
                error_detail = response.json()
                print(f"✗ API Error: {response.status_code}")
                print(f"  Detail: {json.dumps(error_detail, indent=2)}")
            except Exception as e:
                print(f"✗ API Error: {response.status_code}")
                print(f"  Response: {response.text}")
                print(f"  Exception: {e}")

        response.raise_for_status()
        result = response.json()

        print("✓ S3 object node created")
        return result

    def get_node_data(self, node_uri: str) -> dict:
        """
        Get the full node data from the knowledge graph.

        Args:
            node_uri: URI of the node

        Returns:
            Node data including upload/download URLs
        """
        endpoint = f"{self.api_base_url}/kg/node"
        params = {"node_uri": node_uri}

        response = self.session.get(endpoint, params=params)

        if not response.ok:
            try:
                error_detail = response.json()
                print(f"✗ Failed to retrieve node (status {response.status_code})")
                print(f"  Error: {json.dumps(error_detail, indent=2)}")
            except Exception as e:
                print(f"✗ Failed to retrieve node (status {response.status_code})")
                print(f"  Response: {response.text}")
                print(f"  Exception: {e}")

        response.raise_for_status()
        return response.json()

    def upload_file_with_presigned_post(
        self, upload_data: dict, file_path: str
    ) -> bool:
        """
        Upload a file using presigned POST data.

        Args:
            upload_data: Dictionary containing 'url' and 'fields' from presigned POST
            file_path: Path to the file to upload

        Returns:
            True if upload was successful
        """
        url = upload_data.get("url")
        fields = upload_data.get("fields", {})

        if not url:
            print("✗ No upload URL found in the data")
            return False

        print(f"\nUploading file: {file_path}")
        print(f"  Upload URL: {url}")
        print(f"  Form fields: {list(fields.keys())}")

        with open(file_path, "rb") as f:
            # Don't use 'files' parameter - use the presigned POST format
            # The 'file' field must be last
            files = {"file": (Path(file_path).name, f)}

            # Use requests without letting it set Content-Type header
            response = requests.post(url, data=fields, files=files)

        if response.status_code in (200, 204):
            print("✓ File uploaded successfully")
            return True
        else:
            print(f"✗ Upload failed with status {response.status_code}")
            print(f"  Response: {response.text[:500]}")
            return False

    def upload_file_with_presigned_put(self, upload_url: str, file_path: str) -> bool:
        """
        Upload a file using presigned PUT URL.

        Args:
            upload_url: Presigned PUT URL
            file_path: Path to the file to upload

        Returns:
            True if upload was successful
        """
        print(f"\nUploading file: {file_path}")
        print(f"  Upload URL: {upload_url[:80]}...")

        with open(file_path, "rb") as f:
            response = requests.put(upload_url, data=f)

        if response.status_code in (200, 204):
            print("✓ File uploaded successfully")
            return True
        else:
            print(f"✗ Upload failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    def wait_for_upload_url(
        self,
        node_uri: str,
        max_attempts: int = 6,
        delay: int = 2,
        initial_delay: int = 3,
    ) -> Optional[dict]:
        """
        Poll the node until upload URL is available.

        Args:
            node_uri: URI of the S3 object node
            max_attempts: Maximum number of polling attempts (default: 6)
            delay: Delay in seconds between attempts (default: 2)
            initial_delay: Initial delay before first attempt
                to allow connector to start (default: 3)

        Returns:
            Upload data if found, None otherwise
        """
        print(f"\nWaiting for upload URL to be generated...")

        # Wait initially to allow async connector startup
        if initial_delay > 0:
            print(f"  Waiting {initial_delay}s for connector startup...")
            time.sleep(initial_delay)

        for attempt in range(max_attempts):
            node_data = self.get_node_data(node_uri)

            # Debug: show what fields are present in the node
            if attempt == 0:
                available_fields = list(node_data.keys())
                print(f"  Node fields: {', '.join(available_fields)}")
                if "propertyValue" in node_data:
                    print(f"  propertyValue type: {type(node_data['propertyValue'])}")

            # Check for upload URL in various possible locations
            # Try 'propertyValue' first (standard field name in KG)
            if "propertyValue" in node_data:
                prop_value = node_data["propertyValue"]

                # Handle string URLs (PUT method)
                if isinstance(prop_value, str):
                    print("✓ Upload URL received (from propertyValue)")
                    return {"url": prop_value, "method": "PUT"}

                # Handle dict with url/fields (POST method)
                if isinstance(prop_value, dict) and "url" in prop_value:
                    print("✓ Upload URL received (from propertyValue)")
                    value = prop_value

                    # Handle case where 'fields' might be stored as a string
                    if "fields" in value and isinstance(value["fields"], str):
                        try:
                            import ast

                            value["fields"] = ast.literal_eval(value["fields"])
                            print("  (Parsed fields from string format)")
                        except Exception as e:
                            print(f"  Warning: Could not parse fields string: {e}")

                    value["method"] = "POST"
                    return value

            # Also check 'value' field
            if "value" in node_data:
                val = node_data["value"]

                # Handle string URLs
                if isinstance(val, str):
                    print("✓ Upload URL received (from value)")
                    return {"url": val, "method": "PUT"}

                # Handle dict
                if isinstance(val, dict) and "url" in val:
                    print("✓ Upload URL received (from value)")
                    value = val

                    # Handle case where 'fields' might be stored as a string
                    if "fields" in value and isinstance(value["fields"], str):
                        try:
                            import ast

                            value["fields"] = ast.literal_eval(value["fields"])
                            print("  (Parsed fields from string format)")
                        except Exception as e:
                            print(f"  Warning: Could not parse fields string: {e}")

                    value["method"] = "POST"
                    return value

            if "uploadUrl" in node_data:
                print("✓ Upload URL received")
                return {"url": node_data["uploadUrl"], "method": "PUT"}

            if attempt < max_attempts - 1:
                print(
                    f"  Attempt {attempt + 1}/{max_attempts}, retrying in {delay}s..."
                )
                time.sleep(delay)

        print(f"\n✗ Upload URL not available after {max_attempts} attempts")

        # Provide diagnostics if still failing
        if "propertyConnection" in node_data:
            conn = node_data["propertyConnection"]
            is_connected = conn.get("isConnected", False)
            if not is_connected:
                print(f"\n  Troubleshooting:")
                print(f"  - Connection is not active (isConnected: {is_connected})")
                print(f"  - Connection URI: {conn.get('uri', 'unknown')}")
                print(f"  - Verify S3 credentials in the vault")
                print(f"  - Check SINDIT API logs for connection errors")
                print(
                    f"  - Try restarting connections via /connection/refresh endpoint"
                )

        return None


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Upload a file to S3 using SINDIT API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload with specific connection URI
  python upload_to_s3.py --file data.json \\
      --bucket my-bucket --key data/file.json \\
      --api-url https://sindit.example.com \\
      --connection-uri http://sindit.sintef.no/quasar/connection

  # Upload with authentication
  python upload_to_s3.py --f test.jpg
      --b my-bucket --k uploads/test.jpg \\
      --api-url http://localhost:8000 \\
      --connection-uri http://sindit.sintef.no/quasar/connection
      --username admin --password secret
        """,
    )

    parser.add_argument(
        "--file", "-f", required=True, help="Path to the file to upload"
    )
    parser.add_argument("--bucket", "-b", required=True, help="S3 bucket name")
    parser.add_argument(
        "--key", "-k", required=True, help="S3 object key (path within bucket)"
    )
    parser.add_argument(
        "--api-url",
        required=True,
        help="""Base URL of the SINDIT API
        (e.g., http://localhost:8000 or https://api.example.com)""",
    )
    parser.add_argument(
        "--connection-uri",
        default="http://sindit.sintef.no/connection/s3",
        help="""URI of the S3 connection in the knowledge graph
        (e.g., http://sindit.sintef.no/connection/minio)""",
    )
    parser.add_argument("--username", help="Username for API authentication")
    parser.add_argument("--password", help="Password for API authentication")
    parser.add_argument("--token", help="Bearer token for API authentication")
    parser.add_argument(
        "--asset-uri", help="Optional URI to link this property to an asset"
    )
    parser.add_argument("--label", help="Optional label for the S3 object node")
    parser.add_argument(
        "--description", help="Optional description for the S3 object node"
    )

    args = parser.parse_args()

    # Validate file exists
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"✗ Error: File not found: {file_path}")
        sys.exit(1)

    print("=" * 80)
    print("SINDIT S3 File Upload")
    print("=" * 80)

    # Initialize uploader
    try:
        uploader = S3Uploader(
            api_base_url=args.api_url,
            username=args.username,
            password=args.password,
            token=args.token,
        )
    except requests.HTTPError as e:
        print(f"✗ Authentication failed: {e}")
        sys.exit(1)

    # Create S3 object node
    try:
        result = uploader.create_s3_object_node(
            bucket=args.bucket,
            key=args.key,
            connection_uri=args.connection_uri,
            asset_uri=args.asset_uri,
            label=args.label,
            description=args.description,
        )
    except requests.HTTPError as e:
        print(f"✗ Failed to create S3 object node: {e}")
        if e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"  Error details: {json.dumps(error_detail, indent=2)}")
            except Exception as e:
                print(f"  Response: {e.response.text}")
                print(f"  Exception: {e}")
        sys.exit(1)

    # Extract node URI from result
    # The API returns {'result': True} on success, so we use the URI we sent
    if args.asset_uri:
        node_uri = args.asset_uri
    elif "result" in result and isinstance(result["result"], str):
        # If API returns a URI string, use that
        node_uri = result["result"]
    else:
        # Otherwise, use the generated URI from the request
        node_uri = (
            f"http://sindit.sintef.no/s3/{args.bucket}/{args.key.replace('/', '-')}"
        )

    print(f"  Node URI: {node_uri}")

    # Wait for upload URL to be generated
    upload_data = uploader.wait_for_upload_url(node_uri)

    if not upload_data:
        print("\n✗ Failed to get upload URL")
        sys.exit(1)

    # Upload the file
    success = False
    method = upload_data.get("method", "PUT")

    if method == "POST" or "fields" in upload_data:
        # Presigned POST
        success = uploader.upload_file_with_presigned_post(upload_data, str(file_path))
    elif "url" in upload_data:
        # Presigned PUT (default)
        success = uploader.upload_file_with_presigned_put(
            upload_data["url"], str(file_path)
        )

    if success:
        print("\n" + "=" * 80)
        print("✓ Upload completed successfully!")
        print("=" * 80)
        print(f"\nFile: {file_path.name}")
        print(f"Bucket: {args.bucket}")
        print(f"Key: {args.key}")
        print(f"Node URI: {node_uri}")
    else:
        print("\n✗ Upload failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
