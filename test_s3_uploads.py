#!/usr/bin/env python3
"""
Test script for MinIO/S3 object storage.

This script tests S3 connectivity and operations directly with MinIO,
including listing buckets, listing objects, uploading and downloading objects.
"""

import argparse
import sys
from datetime import timedelta
from pathlib import Path

from minio import Minio
from minio.error import S3Error


class MinIOTester:
    """Helper class for testing MinIO/S3 operations."""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = True,
    ):
        """
        Initialize the MinIOTester.

        Args:
            endpoint: MinIO endpoint (e.g., minio.sintef.cloud or localhost:9000)
            access_key: Access key for MinIO
            secret_key: Secret key for MinIO
            secure: Use HTTPS if True, HTTP if False
        """
        self.endpoint = endpoint
        self.access_key = access_key
        self.secure = secure

        try:
            self.client = Minio(
                endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
            )
            print(f"✓ MinIO client initialized")
            print(f"  Endpoint: {endpoint}")
            print(f"  Secure: {secure}")
        except Exception as e:
            print(f"✗ Failed to initialize MinIO client: {e}")
            raise

    def list_buckets(self) -> list:
        """List all buckets."""
        try:
            buckets = self.client.list_buckets()
            return [{"name": b.name, "creation_date": b.creation_date} for b in buckets]
        except S3Error as e:
            print(f"✗ Failed to list buckets: {e}")
            return []

    def bucket_exists(self, bucket: str) -> bool:
        """Check if a bucket exists."""
        try:
            return self.client.bucket_exists(bucket)
        except S3Error as e:
            print(f"✗ Error checking bucket: {e}")
            return False

    def create_bucket(self, bucket: str) -> bool:
        """Create a new bucket."""
        try:
            if self.client.bucket_exists(bucket):
                print(f"⚠ Bucket '{bucket}' already exists")
                return False

            self.client.make_bucket(bucket)
            print(f"✓ Created bucket: {bucket}")
            return True
        except S3Error as e:
            print(f"✗ Failed to create bucket: {e}")
            return False

    def list_objects(
        self, bucket: str, prefix: str = "", recursive: bool = True
    ) -> list:
        """
        List objects in a bucket.

        Args:
            bucket: Bucket name
            prefix: Optional prefix to filter objects
            recursive: List recursively if True

        Returns:
            List of object information dictionaries
        """
        try:
            objects = self.client.list_objects(
                bucket, prefix=prefix, recursive=recursive
            )
            result = []
            for obj in objects:
                result.append(
                    {
                        "key": obj.object_name,
                        "size": obj.size,
                        "etag": obj.etag,
                        "last_modified": obj.last_modified,
                        "content_type": obj.content_type,
                    }
                )
            return result
        except S3Error as e:
            print(f"✗ Failed to list objects: {e}")
            return []

    def get_object_info(self, bucket: str, key: str) -> dict:
        """
        Get information about a specific object.

        Args:
            bucket: Bucket name
            key: Object key

        Returns:
            Object information dictionary
        """
        try:
            stat = self.client.stat_object(bucket, key)
            return {
                "key": key,
                "size": stat.size,
                "etag": stat.etag,
                "last_modified": stat.last_modified,
                "content_type": stat.content_type,
                "metadata": stat.metadata,
            }
        except S3Error as e:
            print(f"✗ Failed to get object info: {e}")
            return {}

    def download_object(self, bucket: str, key: str, output_path: str = None) -> bool:
        """
        Download an object from MinIO.

        Args:
            bucket: Bucket name
            key: Object key
            output_path: Optional path to save the file

        Returns:
            True if successful
        """
        try:
            if output_path:
                self.client.fget_object(bucket, key, output_path)
                print(f"✓ Downloaded to: {output_path}")
            else:
                response = self.client.get_object(bucket, key)
                data = response.read()
                response.close()
                response.release_conn()
                print(f"✓ Download successful ({len(data)} bytes)")
                print(f"  Preview: {data[:100]}")
            return True
        except S3Error as e:
            print(f"✗ Failed to download object: {e}")
            return False

    def upload_object(self, bucket: str, key: str, file_path: str) -> bool:
        """
        Upload a file to MinIO.

        Args:
            bucket: Bucket name
            key: Object key (destination path)
            file_path: Local file path to upload

        Returns:
            True if successful
        """
        try:
            path = Path(file_path)
            if not path.exists():
                print(f"✗ File not found: {file_path}")
                return False

            self.client.fput_object(bucket, key, str(path))
            print(f"✓ Uploaded: {file_path} -> {bucket}/{key}")
            return True
        except S3Error as e:
            print(f"✗ Failed to upload object: {e}")
            return False

    def delete_object(self, bucket: str, key: str) -> bool:
        """
        Delete an object from MinIO.

        Args:
            bucket: Bucket name
            key: Object key

        Returns:
            True if successful
        """
        try:
            self.client.remove_object(bucket, key)
            print(f"✓ Deleted: {bucket}/{key}")
            return True
        except S3Error as e:
            print(f"✗ Failed to delete object: {e}")
            return False

    def generate_presigned_url(self, bucket: str, key: str, expires: int = 3600) -> str:
        """
        Generate a presigned URL for an object.

        Args:
            bucket: Bucket name
            key: Object key
            expires: Expiration time in seconds

        Returns:
            Presigned URL string
        """
        try:
            url = self.client.presigned_get_object(
                bucket, key, expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            print(f"✗ Failed to generate presigned URL: {e}")
            return ""


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Test MinIO/S3 operations directly",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all buckets
  python test_s3_uploads.py \\
      --endpoint minio.sintef.cloud \\
      --access-key YOUR_ACCESS_KEY \\
      --secret-key YOUR_SECRET_KEY \\
      --secure \\ # use --secure for HTTPS (443)
      --command buckets

  # List objects in a bucket
  python test_s3_uploads.py \\
      --endpoint minio.sintef.cloud \\
      --access-key YOUR_ACCESS_KEY \\
      --secret-key YOUR_SECRET_KEY \\
      --secure \\ # omit this flag for HTTP endpoint
      --command list --bucket my-bucket

  # List objects with prefix
  python test_s3_uploads.py \\
      --endpoint minio.sintef.cloud \\
      --access-key YOUR_ACCESS_KEY \\
      --secret-key YOUR_SECRET_KEY \\
      --secure \\ # omit this flag for HTTP endpoint
      --command list --bucket my-bucket --prefix uploads/

  # Get object info
  python test_s3_uploads.py \\
      --endpoint minio.sintef.cloud \\
      --access-key YOUR_ACCESS_KEY \\
      --secret-key YOUR_SECRET_KEY \\
      --secure \\ # omit this flag for HTTP endpoint
      --command get --bucket my-bucket --key uploads/test.jpg

  # Download object
  python test_s3_uploads.py \\
      --endpoint minio.sintef.cloud \\
      --access-key YOUR_ACCESS_KEY \\
      --secret-key YOUR_SECRET_KEY \\
      --secure \\ # omit this flag for HTTP endpoint
      --command download --bucket my-bucket
      --key uploads/test.jpg \\
      --output downloaded.jpg

  # Upload object
  python test_s3_uploads.py \\
      --endpoint minio.sintef.cloud \\
      --access-key YOUR_ACCESS_KEY \\
      --secret-key YOUR_SECRET_KEY \\
      --secure \\ # omit this flag for HTTP endpoint
      --command upload --bucket my-bucket
      --key uploads/new-file.jpg \\
      --file local-file.jpg

  # Create bucket
  python test_s3_uploads.py \\
      --endpoint minio.sintef.cloud \\
      --access-key YOUR_ACCESS_KEY \\
      --secret-key YOUR_SECRET_KEY \\
      --secure \\ # omit this flag for HTTP endpoint
      --command create-bucket --bucket new-bucket

  # Generate presigned URL
  python test_s3_uploads.py \\
      --endpoint minio.sintef.cloud \\
      --access-key YOUR_ACCESS_KEY \\
      --secret-key YOUR_SECRET_KEY \\
      --secure \\
      --command presigned --bucket my-bucket
      --key uploads/test.jpg
        """,
    )

    parser.add_argument(
        "--endpoint",
        required=True,
        help="MinIO endpoint (e.g., minio.sintef.cloud or localhost:9000)",
    )
    parser.add_argument(
        "--access-key",
        required=True,
        help="MinIO access key",
    )
    parser.add_argument(
        "--secret-key",
        required=True,
        help="MinIO secret key",
    )
    parser.add_argument(
        "--secure",
        action="store_true",
        help="Use HTTPS (default: HTTP)",
    )

    parser.add_argument(
        "--command",
        choices=[
            "buckets",
            "create-bucket",
            "list",
            "get",
            "download",
            "upload",
            "delete",
            "presigned",
        ],
        default="buckets",
        help="Command to execute",
    )
    parser.add_argument("--bucket", help="Bucket name")
    parser.add_argument("--key", help="Object key")
    parser.add_argument("--prefix", default="", help="Prefix filter for listing")
    parser.add_argument("--file", help="Local file path (for upload)")
    parser.add_argument("--output", help="Output file path (for download)")
    parser.add_argument(
        "--expires", type=int, default=3600, help="Presigned URL expiration in seconds"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("MinIO/S3 Test Script")
    print("=" * 80)
    print(f"Endpoint: {args.endpoint}")
    print(f"Secure: {args.secure}")
    print(f"Command: {args.command}")
    print()

    # Initialize tester
    try:
        tester = MinIOTester(
            endpoint=args.endpoint,
            access_key=args.access_key,
            secret_key=args.secret_key,
            secure=args.secure,
        )
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        sys.exit(1)

    # Execute command
    try:
        if args.command == "buckets":
            print("Listing all buckets...")
            buckets = tester.list_buckets()

            if buckets:
                print(f"\n✓ Found {len(buckets)} bucket(s):")
                for bucket in buckets:
                    print(f"  - {bucket['name']}")
                    print(f"    Created: {bucket['creation_date']}")
            else:
                print("  No buckets found")

        elif args.command == "create-bucket":
            if not args.bucket:
                print("✗ --bucket is required for create-bucket command")
                sys.exit(1)

            print(f"Creating bucket '{args.bucket}'...")
            tester.create_bucket(args.bucket)

        elif args.command == "list":
            if not args.bucket:
                print("✗ --bucket is required for list command")
                sys.exit(1)

            # Check if bucket exists first
            if not tester.bucket_exists(args.bucket):
                print(f"✗ Bucket '{args.bucket}' does not exist")
                sys.exit(1)

            print(f"Listing objects in bucket '{args.bucket}'...")
            if args.prefix:
                print(f"  Prefix filter: '{args.prefix}'")

            objects = tester.list_objects(args.bucket, args.prefix)

            if objects:
                print(f"\n✓ Found {len(objects)} object(s):")
                for obj in objects:
                    print(f"\n  Key: {obj['key']}")
                    print(f"    Size: {obj['size']} bytes")
                    print(f"    Last Modified: {obj['last_modified']}")
                    print(f"    Content Type: {obj['content_type']}")
                    print(f"    ETag: {obj['etag']}")
            else:
                print("  No objects found")

        elif args.command == "get":
            if not args.bucket or not args.key:
                print("✗ --bucket and --key are required for get command")
                sys.exit(1)

            print(f"Getting object info: {args.bucket}/{args.key}")
            obj_info = tester.get_object_info(args.bucket, args.key)

            if obj_info:
                print("\n✓ Object Information:")
                print(f"  Key: {obj_info['key']}")
                print(f"  Size: {obj_info['size']} bytes")
                print(f"  Last Modified: {obj_info['last_modified']}")
                print(f"  Content Type: {obj_info['content_type']}")
                print(f"  ETag: {obj_info['etag']}")
                if obj_info.get("metadata"):
                    print(f"  Metadata: {obj_info['metadata']}")

        elif args.command == "download":
            if not args.bucket or not args.key:
                print("✗ --bucket and --key are required for download command")
                sys.exit(1)

            print(f"Downloading object: {args.bucket}/{args.key}")
            success = tester.download_object(args.bucket, args.key, args.output)

            if not success:
                sys.exit(1)

        elif args.command == "upload":
            if not args.bucket or not args.key or not args.file:
                print("✗ --bucket, --key, and --file are required for upload command")
                sys.exit(1)

            print(f"Uploading file: {args.file} -> {args.bucket}/{args.key}")
            success = tester.upload_object(args.bucket, args.key, args.file)

            if not success:
                sys.exit(1)

        elif args.command == "delete":
            if not args.bucket or not args.key:
                print("✗ --bucket and --key are required for delete command")
                sys.exit(1)

            print(f"Deleting object: {args.bucket}/{args.key}")
            success = tester.delete_object(args.bucket, args.key)

            if not success:
                sys.exit(1)

        elif args.command == "presigned":
            if not args.bucket or not args.key:
                print("✗ --bucket and --key are required for presigned command")
                sys.exit(1)

            print(f"Generating presigned URL for: {args.bucket}/{args.key}")
            print(f"  Expires in: {args.expires} seconds")

            url = tester.generate_presigned_url(args.bucket, args.key, args.expires)

            if url:
                print(f"\n✓ Presigned URL:")
                print(f"  {url}")
            else:
                sys.exit(1)

    except S3Error as e:
        print(f"\n✗ MinIO Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 80)
    print("✓ Operation completed successfully")
    print("=" * 80)


if __name__ == "__main__":
    main()
