"""
Service for s3 operations
"""

import logging
import tempfile
import uuid
from typing import overload

import aioboto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from typing_extensions import Self

from ..core.config import get_settings


class S3Service:
    """Service for s3 operations"""

    def __init__(self):
        """Initialize the service with a database session."""

        self.settings = get_settings()
        self.bucket_name = self.settings.AWS_BUCKET_NAME

    @overload
    async def __aenter__(self) -> Self:
        self.session = aioboto3.Session(
            aws_access_key_id=self.settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.settings.AWS_SECRET_ACCESS_KEY,
            region_name=self.settings.AWS_DEFAULT_REGION,
        )

        self.client = await self.session.client(
            "s3",
            endpoint_url=self.settings.AWS_ENDPOINT_URL,
            aws_session_token=None,
            verify=False,
        ).__aenter__()

        return self

    @overload
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.client.__aexit__(exc_type, exc_val, exc_tb)

    async def fetch_file_from_s3(self, s3_key: str):
        """
        given the s3 link of a file, fetch and return the text/bytes content
        """

        try:
            obj = await self.client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return await obj.get("Body").read()
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logging.error(f"Fetch File Error - Code: {error_code}")
            logging.error(f"Error Message: {error_message}")
            raise HTTPException(
                status_code=403,
                detail=f"S3 Fetch File Error: {error_code} - {error_message}",
            )
        except Exception as e:
            logging.error(f"Unexpected Fetch File Error: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Unexpected Fetch File Error: {str(e)}"
            )

    def get_s3_url(self, s3_key: str) -> str:
        return f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"

    async def generate_presigned_url(
        self,
        file_name: str,
        operation: str = "put_object",
        expiration: int = 3600,
        content_type: str = None,
    ):
        try:
            logging.info(
                f"Generating Presigned URL for file: {file_name}, operation: {operation}"
            )
            params = {"Bucket": self.bucket_name, "Key": file_name}
            if operation == "put_object" and content_type:
                params["ContentType"] = content_type

            presigned_url = await self.client.generate_presigned_url(
                operation, params, expiration
            )

            logging.info(f"Presigned URL generated successfully for {file_name}")
            return {
                "url": presigned_url,
                "fields": {
                    "key": file_name,
                    "bucket": self.bucket_name,
                    "content_type": content_type,
                },
            }
        except Exception as e:
            logging.error(f"Presigned URL Generation Error: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"AWS S3 Presigned URL Error: {str(e)}"
            )

    async def delete_file_from_s3(self, object_key: str) -> bool:
        """
        Delete a file from S3 by its object key.
        Returns True if deletion is successful.
        """
        try:
            logging.info(f"Deleting file from S3: {object_key}")
            await self.client.delete_object(Bucket=self.bucket_name, Key=object_key)

            logging.info(f"File {object_key} deleted from S3 bucket {self.bucket_name}")
            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logging.error(f"S3 Delete Error - Code: {error_code}")
            logging.error(f"Error Message: {error_message}")
            raise HTTPException(
                status_code=403,
                detail=f"S3 Delete Error: {error_code} - {error_message}",
            )
        except Exception as e:
            logging.error(f"Unexpected Delete Error: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Unexpected Delete Error: {str(e)}"
            )

    async def upload_file_to_s3(
        self, content: bytes, file_name: str, content_type: str
    ) -> str:
        """
        save the file on local storage (temporary) and upload the file to s3
        """
        try:
            logging.info(f"Attempting direct upload for {file_name}")

            # the key to uniquely identify this file
            s3_key = f"{file_name}--{uuid.uuid4().hex}"
            # save the file on disk temporarily
            with tempfile.NamedTemporaryFile("w+b") as f:
                f.write(content)
                await self.client.upload_fileobj(
                    f, self.bucket_name, s3_key, {"ContentType": content_type}
                )

            logging.info(f"Direct upload successful for {file_name}")
            return s3_key
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logging.error(f"Direct Upload Error - Code: {error_code}")
            logging.error(f"Error Message: {error_message}")
            raise HTTPException(
                status_code=403,
                detail=f"S3 Upload Error: {error_code} - {error_message}",
            )
        except Exception as e:
            logging.error(f"Unexpected Direct Upload Error: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Unexpected Direct Upload Error: {str(e)}"
            )
