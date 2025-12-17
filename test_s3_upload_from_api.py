"""
Test script to poll the /kg/node API for S3 credentials and upload a file to MinIO.
"""

import requests
import time
import json

# Configuration
API_BASE_URL = "http://localhost:9017"  # Adjust to your API URL
NODE_URI = "http://sindit.sintef.no/quasar-plim-test/s3/test-node"
USERNAME = "quasar"  # Adjust to your username
PASSWORD = "quasar"  # Adjust to your password

# Test file to upload
TEST_FILE_PATH = "test_file.txt"
TEST_FILE_CONTENT = b"This is a test file uploaded via API credentials"


def get_auth_token():
    """Get authentication token from the API."""
    print("Getting authentication token...")
    response = requests.post(
        f"{API_BASE_URL}/token",
        data={
            "username": USERNAME,
            "password": PASSWORD,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if response.status_code == 200:
        token_data = response.json()
        print(f"✓ Got token: {token_data['access_token'][:20]}...")
        return token_data["access_token"]
    else:
        print(f"✗ Failed to get token: {response.status_code}")
        print(f"Response: {response.text}")
        return None


def poll_node_for_credentials(token, max_attempts=10, poll_interval=2):
    """Poll the /kg/node API to get S3 credentials."""
    headers = {"Authorization": f"Bearer {token}"}

    for attempt in range(1, max_attempts + 1):
        print(
            f"\n[Attempt {attempt}/{max_attempts}] Polling /kg/node for credentials..."
        )

        try:
            response = requests.get(
                f"{API_BASE_URL}/kg/node",
                params={"node_uri": NODE_URI, "depth": 1},
                headers=headers,
            )

            if response.status_code == 200:
                node_data = response.json()
                print(f"✓ Got node data")
                print(f"Node data: {json.dumps(node_data, indent=2)}")

                # Extract S3 upload credentials from propertyValue
                property_value = node_data.get("propertyValue")
                url_mode = node_data.get("urlMode")  # New field

                if url_mode:
                    print(f"✓ URL Mode: {url_mode}")

                if property_value:
                    # Check if it's a presigned POST (dict with 'url' and 'fields')
                    if isinstance(property_value, dict) and "url" in property_value:
                        print(f"✓ Found presigned POST URL")
                        return property_value
                    # Check if it's a presigned PUT URL (string)
                    elif isinstance(property_value, str) and property_value.startswith(
                        "http"
                    ):
                        mode = url_mode if url_mode else "unknown"
                        print(f"✓ Found presigned URL (mode: {mode})")
                        return {"url": property_value, "method": "PUT", "urlMode": mode}
                    else:
                        print(f"⚠ Property value exists but not in expected format")
                else:
                    print(f"⚠ No propertyValue found yet, waiting...")
            else:
                print(f"✗ Failed to get node: {response.status_code}")
                print(f"Response: {response.text}")

        except Exception as e:
            print(f"✗ Error polling node: {e}")

        if attempt < max_attempts:
            print(f"Waiting {poll_interval} seconds before next attempt...")
            time.sleep(poll_interval)

    print(f"\n✗ Failed to get credentials after {max_attempts} attempts")
    return None


def upload_with_presigned_post(credentials, file_content):
    """Upload file using presigned POST."""
    url = credentials["url"]
    fields = credentials.get("fields", {})

    print(f"\nUploading with presigned POST to: {url}")
    print(f"Fields: {json.dumps(fields, indent=2)}")

    # Prepare the multipart form data
    files = {"file": ("test_file.txt", file_content)}

    response = requests.post(url, data=fields, files=files)

    if response.status_code in [200, 204]:
        print(f"✓ Upload successful! Status: {response.status_code}")
        return True
    else:
        print(f"✗ Upload failed! Status: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def upload_with_presigned_put(url, file_content):
    """Upload file using presigned PUT."""
    print(f"\nUploading with presigned PUT to: {url}")

    response = requests.put(url, data=file_content)

    if response.status_code in [200, 204]:
        print(f"✓ Upload successful! Status: {response.status_code}")
        return True
    else:
        print(f"✗ Upload failed! Status: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def verify_upload(token):
    """Poll the node again to verify the upload was detected."""
    print("\n" + "=" * 60)
    print("Verifying upload by polling node again...")
    print("=" * 60)

    headers = {"Authorization": f"Bearer {token}"}

    for attempt in range(1, 6):
        print(f"\n[Verification Attempt {attempt}/5]")

        try:
            response = requests.get(
                f"{API_BASE_URL}/kg/node",
                params={"node_uri": NODE_URI, "depth": 1},
                headers=headers,
            )

            if response.status_code == 200:
                node_data = response.json()
                property_value = node_data.get("propertyValue")
                url_mode = node_data.get("urlMode")

                if url_mode == "download":
                    # urlMode explicitly indicates download
                    print(f"✓ Upload verified! URL mode is now 'download'")
                    print(f"Download URL: {property_value}")
                    return True
                elif (
                    isinstance(property_value, str)
                    and "AWSAccessKeyId" not in property_value
                ):
                    # Fallback: It's now a download URL (not an upload URL)
                    print(f"✓ Upload verified! Node now has download URL")
                    print(f"Download URL: {property_value}")
                    return True
                else:
                    print(
                        f"⚠ Still shows upload URL (mode: {url_mode}), file may not be detected yet..."
                    )
        except Exception as e:
            print(f"✗ Error verifying: {e}")

        if attempt < 5:
            time.sleep(3)

    print(f"\n⚠ Could not verify upload (but it may still have succeeded)")
    return False


def main():
    print("=" * 60)
    print("S3 Upload Test via API")
    print("=" * 60)

    # Step 1: Get authentication token
    token = get_auth_token()
    if not token:
        print("\n✗ Cannot proceed without authentication token")
        return

    # Step 2: Poll for S3 credentials
    credentials = poll_node_for_credentials(token)
    if not credentials:
        print("\n✗ Cannot proceed without S3 credentials")
        return

    # Step 3: Upload file
    print("\n" + "=" * 60)
    print("Uploading file...")
    print("=" * 60)

    if "fields" in credentials:
        # Presigned POST
        success = upload_with_presigned_post(credentials, TEST_FILE_CONTENT)
    else:
        # Presigned PUT
        success = upload_with_presigned_put(credentials["url"], TEST_FILE_CONTENT)

    if not success:
        print("\n✗ Upload failed")
        return

    # Step 4: Verify upload
    verify_upload(token)

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
