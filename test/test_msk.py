import datetime
import json
import sys

import pytest
from unittest import TestCase

from kafka.msk import AwsMskIamClient

try:
    from unittest import mock
except ImportError:
    import mock


@pytest.fixture(params=[{'session_token': 'session_token', 'host': 'localhost'}, {'session_token': None, 'host': 'localhost.us-east-1.amazonaws.com'}])
def msk_client(request):
    # To avoid a package dependency on the optional botocore library, we mock the module out
    sys.modules['botocore.session'] = mock.MagicMock()
    from botocore.session import Session  # pylint: disable=import-error

    session = Session()
    session.get_credentials = mock.MagicMock(return_value=mock.MagicMock(id='the_actual_credentials', access_key='akia', secret_key='secret', token=request.param['session_token']))
    yield AwsMskIamClient(
        host=request.param["host"],
        boto_session = session,
    )


def test_aws_msk_iam(msk_client):
    msg = msk_client.first_message()
    assert msg
    assert isinstance(msg, bytes)
    actual = json.loads(msg.decode('utf-8'))

    expected = {
        'version': '2020_10_22',
        'host': msk_client.host,
        'user-agent': 'kafka-python',
        'action': 'kafka-cluster:Connect',
        'x-amz-algorithm': 'AWS4-HMAC-SHA256',
        'x-amz-credential': '{}/{}/{}/kafka-cluster/aws4_request'.format(msk_client.access_key, datetime.datetime.utcnow().strftime('%Y%m%d'), 'us-west-2' if msk_client.host == 'localhost' else 'us-east-1'),
        'x-amz-date': mock.ANY,
        'x-amz-signedheaders': 'host',
        'x-amz-expires': '900',
        'x-amz-signature': mock.ANY,
    }
    if msk_client.token:
        expected['x-amz-security-token'] = msk_client.token
    TestCase().assertEqual(actual, expected)
