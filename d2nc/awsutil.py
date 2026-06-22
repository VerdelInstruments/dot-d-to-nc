"""Boto3 session helper. Kept tiny on purpose — credential errors are
translated to friendly hints at the CLI boundary (see cli.main).

boto3 is imported lazily so the CLI (--help) and the local backend work in an
environment without boto3 installed."""

# Class names of common credential failures, surfaced by cli.main as a hint.
CREDENTIAL_ERROR_NAMES = {
    "NoCredentialsError",
    "CredentialRetrievalError",
    "TokenRetrievalError",
    "SSOTokenLoadError",
    "UnauthorizedSSOTokenError",
}


def make_session(profile=None, region=None):
    import boto3

    return boto3.Session(profile_name=profile, region_name=region)
