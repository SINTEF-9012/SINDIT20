from connectors.connector import Connector
from connectors.connector_factory import ObjectBuilder, connector_factory
from util.log import logger
import boto3
from botocore.exceptions import ClientError


class S3Connector(Connector):
    """S3 Object Storage Connector."""

    id: str = "s3"

    def __init__(
        self,
        endpoint_url: str = "http://localhost:9000",
        access_key_id: str = "minioadmin",
        secret_access_key: str = "minioadmin",
        region_name: str = None,
    ):
        super().__init__()

        self.region_name = region_name
        self.endpoint_url = endpoint_url
        self.__access_key_id = access_key_id
        self.__secret_access_key = secret_access_key

    def start(self, **kwargs):
        """Start the S3 client."""
        if self.__access_key_id and self.__secret_access_key:
            self.client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.__access_key_id,
                aws_secret_access_key=self.__secret_access_key,
                region_name=self.region_name,
            )

    def stop(self, **kwargs):
        """Stop the S3 client."""
        self.client.stop()

    def list_buckets(self):
        """List all buckets in the S3 storage."""
        response = self.client.list_buckets()
        return response

    def list_objects(self, bucket: str):
        """List all objects in a bucket."""
        response = self.client.list_objects_v2(Bucket=bucket)
        return response

    def get_object(self, bucket: str, key: str):
        """Get information about an object."""
        response = self.client.get_object(Bucket=bucket, Key=key)
        return response

    def put_object(self, bucket: str, key: str, data: bytes):
        """Put an object to a bucket.
        Bucket is the name of the bucket to upload the file to.
        The key is the full name of the file to upload. For example key='image.jpg'.
        The data is the file data to upload.
            :param bucket: string
            :param key: string
            :param data: bytes

        Example of usage:
        with open('test.jpg', 'rb') as data:
            s3.put_object(bucket='my-bucket', Key='test.jpg', Body=data)
        """
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

    def download_object(self, bucket: str, key: str, file_path: str) -> None:
        """Download an object from a bucket.
        Bucket is the name of the bucket containing the object.
        Key is the name of the object to download.
        Filepath is the path in which save the object.
            :param bucket: string
            :param key: string
            :param file_path: string
        """
        self.client.download_file(bucket, key, file_path)

    def create_presigned_url_for_download_object(
        self, bucket: str, key: str, expiration: int = 3600
    ):
        """Generate a presigned URL to download an object."""
        response = self.client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expiration
        )
        return response

    def create_presigned_url_for_upload_object(
        self,
        bucket_name: str,
        object_name: str,
        fields: dict = None,
        conditions: list = None,
        expiration: int = 3600,
    ):
        """Generate a presigned URL to POST request for upload a file to S3 bucket

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


class S3ConnectorBuilder(ObjectBuilder):
    """A class representing an S3 connector builder."""

    def build(
        self,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        region_name: str = None,
    ) -> S3Connector:
        connector = S3Connector(
            endpoint_url=endpoint_url,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            region_name=region_name,
        )
        return connector


connector_factory.register_builder(S3Connector.id, S3ConnectorBuilder())
