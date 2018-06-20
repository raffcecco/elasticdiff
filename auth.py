from requests_aws4auth import AWS4Auth
import boto3
from botocore.credentials import get_credentials
from botocore.session import Session

class Authentication:
    sts_client = None
    es_host = ''

    def __init__(self, es_host, region, aws_type):
        self.sts_client = boto3.client('sts')
        self.es_host = es_host
        self.region = region
        self.aws_type = aws_type

    def __auth(self):
        creds = get_credentials(Session())
        aws_auth = AWS4Auth(
        creds.access_key,
        creds.secret_key, self.region, self.aws_type,
        session_token=creds.token)
        return aws_auth

    def get_auth(self):
        print("Obtaining authentication data for AWS...")
        return self.__auth()
