from connectors.connector import Connector
from util.log import logger
from botocore.execeptions import ClientError
import boto3


class S3Connector(Connector):
    """S3 Object Storage Connector."""

    def __init__(
        self,
        endpoint_url: str = "localhost",
        access_key_id: str = "minioadmin",
        secret_access_key: str = "minioadmin",
        region_name: str = None,
    ):
        super().__init__()

        self.region_name = region_name
        self.endpoint_url = endpoint_url
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region_name,
        )

    def list_buckets(self):
        """List all buckets in the S3 storage."""
        response = self.client.list_buckets()
        return response

    def list_objects(self, bucket: str):
        """List all objects in a bucket."""
        response = self.client.list_objects_v2(Bucket=bucket)
        return response

    def get_object(self, bucket: str, key: str):
        """Get an object from a bucket."""
        response = self.client.get_object(Bucket=bucket, Key=key)
        return response

    def put_object(self, bucket: str, key: str, data: bytes):
        """Put an object to a bucket."""
        response = self.client.put_object(Bucket=bucket, Key=key, Body=data)
        return response

    def delete_object(self, bucket: str, key: str):
        """Delete an object from a bucket."""
        response = self.client.delete_object(Bucket=bucket, Key=key)
        return response

    def create_bucket(self, bucket: str):
        """Create a bucket."""
        response = self.client.create_bucket(Bucket=bucket)
        return response

    def delete_bucket(self, bucket: str):
        """Delete a bucket."""
        response = self.client.delete_bucket(Bucket=bucket)
        return response

    def create_presigned_url(
        self, bucket: str, key: str, object_name: str = None, expiration: int = 3600
    ):
        """Generate a presigned URL for an object."""
        response = self.client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expiration
        )
        return response

    def create_presigned_post(
        self,
        bucket_name: str,
        object_name: str,
        fields: dict = None,
        conditions: list = None,
        expiration: int = 3600,
    ):
        """Generate a presigned URL S3 POST request to upload a file

        :param bucket_name: string
        :param object_name: string
        :param fields: Dictionary of prefilled form fields
        :param conditions: List of conditions to include in the policy
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Dictionary with the following keys:
            url: URL to post to
            fields: Dictionary of form fields and values to submit with the POST
        :return: None if error.
        """

        # Generate a presigned S3 POST URL
        try:
            response = self.client.generate_presigned_post(
                bucket_name,
                object_name,
                Fields=fields,
                Conditions=conditions,
                ExpiresIn=expiration,
            )
        except ClientError as e:
            logger.error(e)
            return None

        # The response contains the presigned URL and required fields
        return response
