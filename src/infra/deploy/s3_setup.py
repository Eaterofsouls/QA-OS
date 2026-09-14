"""
infra/deploy/s3_setup.py
========================
S3 / MinIO bucket bootstrap script for the AI QA Operating System.

Creates the ``qa-os-traces`` bucket if it does not exist, performs a test
write, and verifies the object is readable.  Designed to be run once at
infrastructure bootstrap time, and again safely in CI (idempotent).

Usage:
    uv run python infra/deploy/s3_setup.py

Environment variables (read from .env or shell):
    S3_ENDPOINT_URL     - MinIO/S3 endpoint (default: http://localhost:9000)
    AWS_ACCESS_KEY_ID   - Access key (default: minioadmin for local dev)
    AWS_SECRET_ACCESS_KEY - Secret key (default: minioadmin for local dev)
    AWS_REGION          - AWS region (default: us-east-1)
    S3_BUCKET_NAME      - Override the default bucket name (default: qa-os-traces)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

import boto3  # type: ignore[import]
from botocore.exceptions import ClientError, EndpointResolutionError  # type: ignore[import]
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
load_dotenv()

BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "qa-os-traces")
ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")

TEST_OBJECT_KEY: str = "_bootstrap/connectivity_test.json"


# ---------------------------------------------------------------------------
# S3 client factory
# ---------------------------------------------------------------------------

def build_s3_client() -> Any:
    """
    Build and return a configured boto3 S3 client.

    Uses ``S3_ENDPOINT_URL`` for MinIO/local S3-compatible endpoints.
    When running against real AWS, leave ``S3_ENDPOINT_URL`` unset (or set
    it to an empty string) and the standard AWS SDK endpoint resolution
    takes over.

    Returns
    -------
    botocore.client.S3
        A configured S3 client.
    """
    kwargs: dict[str, Any] = {
        "region_name": AWS_REGION,
        "aws_access_key_id": AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": AWS_SECRET_ACCESS_KEY,
    }
    if ENDPOINT_URL:
        kwargs["endpoint_url"] = ENDPOINT_URL

    return boto3.client("s3", **kwargs)


# ---------------------------------------------------------------------------
# Step 1: Ensure bucket exists
# ---------------------------------------------------------------------------

def ensure_bucket(s3: Any, bucket: str) -> None:
    """
    Create *bucket* if it does not already exist.

    Parameters
    ----------
    s3:
        A boto3 S3 client.
    bucket:
        Bucket name.

    Raises
    ------
    SystemExit
        On unexpected errors (permission denied, invalid region, etc.).
    """
    try:
        s3.head_bucket(Bucket=bucket)
        print(f"[OK]   Bucket '{bucket}' already exists — skipping creation.")
    except ClientError as exc:
        error_code = exc.response["Error"]["Code"]
        if error_code in ("404", "NoSuchBucket"):
            print(f"[INFO] Bucket '{bucket}' not found — creating ...", end=" ")
            try:
                # For us-east-1 we must NOT specify CreateBucketConfiguration
                if AWS_REGION == "us-east-1":
                    s3.create_bucket(Bucket=bucket)
                else:
                    s3.create_bucket(
                        Bucket=bucket,
                        CreateBucketConfiguration={"LocationConstraint": AWS_REGION},
                    )
                print("OK")
            except ClientError as create_exc:
                print(f"FAILED\n[ERROR] {create_exc}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"\n[ERROR] Unexpected S3 error: {exc}", file=sys.stderr)
            sys.exit(1)


# ---------------------------------------------------------------------------
# Step 2: Test write
# ---------------------------------------------------------------------------

def test_write(s3: Any, bucket: str) -> None:
    """
    Upload a small JSON sentinel object to verify write access.

    Parameters
    ----------
    s3:
        A boto3 S3 client.
    bucket:
        Target bucket name.

    Raises
    ------
    SystemExit
        If the upload fails.
    """
    payload: dict[str, Any] = {
        "service": "qa-os",
        "check": "bootstrap-write",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "bucket": bucket,
    }
    body: bytes = json.dumps(payload, indent=2).encode()

    print(f"[INFO] Writing test object: s3://{bucket}/{TEST_OBJECT_KEY} ...", end=" ")
    try:
        s3.put_object(
            Bucket=bucket,
            Key=TEST_OBJECT_KEY,
            Body=body,
            ContentType="application/json",
        )
        print("OK")
    except ClientError as exc:
        print(f"FAILED\n[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Step 3: Test read
# ---------------------------------------------------------------------------

def test_read(s3: Any, bucket: str) -> None:
    """
    Download the sentinel object that was just written and verify its content.

    Parameters
    ----------
    s3:
        A boto3 S3 client.
    bucket:
        Target bucket name.

    Raises
    ------
    SystemExit
        If the download or content verification fails.
    """
    print(f"[INFO] Reading back test object: s3://{bucket}/{TEST_OBJECT_KEY} ...", end=" ")
    try:
        response = s3.get_object(Bucket=bucket, Key=TEST_OBJECT_KEY)
        raw: bytes = response["Body"].read()
        data: dict[str, Any] = json.loads(raw)
    except ClientError as exc:
        print(f"FAILED\n[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"FAILED\n[ERROR] Invalid JSON in test object: {exc}", file=sys.stderr)
        sys.exit(1)

    if data.get("check") != "bootstrap-write":
        print(
            f"FAILED\n[ERROR] Unexpected object content: {data}",
            file=sys.stderr,
        )
        sys.exit(1)

    print("OK")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Orchestrate the full bucket bootstrap sequence.

    Steps:
    1. Build the S3 client.
    2. Ensure the target bucket exists.
    3. Write a test object.
    4. Read the test object back and verify it.

    Returns
    -------
    int
        ``0`` on success.  Failures call ``sys.exit(1)`` from sub-functions.
    """
    print(
        f"\n=== S3/MinIO Bucket Bootstrap ===\n"
        f"  Endpoint : {ENDPOINT_URL or 'AWS (default)'}\n"
        f"  Bucket   : {BUCKET_NAME}\n"
        f"  Region   : {AWS_REGION}\n"
    )

    try:
        s3 = build_s3_client()
    except Exception as exc:
        print(f"[ERROR] Failed to build S3 client: {exc}", file=sys.stderr)
        return 1

    ensure_bucket(s3, BUCKET_NAME)
    test_write(s3, BUCKET_NAME)
    test_read(s3, BUCKET_NAME)

    print(
        f"\n[SUCCESS] Bucket '{BUCKET_NAME}' is ready.\n"
        f"          Endpoint  : {ENDPOINT_URL or 'AWS'}\n"
        f"          Test key  : s3://{BUCKET_NAME}/{TEST_OBJECT_KEY}\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
