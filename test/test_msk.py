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


@pytest.fixture
def boto_session():
    # To avoid a package dependency on the optional botocore library, we mock the module out
    sys.modules['botocore.session'] = mock.MagicMock()
    from botocore.session import Session  # pylint: disable=import-error

    boto_session = Session()
    boto_session.get_credentials = mock.MagicMock(return_value=mock.MagicMock(id='the_actual_credentials', access_key='akia', secret_key='secret', token=None))
    yield boto_session


def test_aws_msk_iam_region_from_config(boto_session):
    # Region determined by configuration
    boto_session.get_config_variable = mock.MagicMock(return_value='us-west-2')
    msk_client = AwsMskIamClient(
        host='localhost',
        boto_session = boto_session,
    )
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
        'x-amz-credential': '{}/{}/us-west-2/kafka-cluster/aws4_request'.format(msk_client.access_key, datetime.datetime.utcnow().strftime('%Y%m%d')),
        'x-amz-date': mock.ANY,
        'x-amz-signedheaders': 'host',
        'x-amz-expires': '900',
        'x-amz-signature': mock.ANY,
    }
    TestCase().assertEqual(actual, expected)


def test_aws_msk_iam_region_from_hostname(boto_session):
    # Region determined by hostname
    msk_client = AwsMskIamClient(
        host='localhost.us-east-1.amazonaws.com',
        boto_session = boto_session,
    )
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
        'x-amz-credential': '{}/{}/us-east-1/kafka-cluster/aws4_request'.format(msk_client.access_key, datetime.datetime.utcnow().strftime('%Y%m%d')),
        'x-amz-date': mock.ANY,
        'x-amz-signedheaders': 'host',
        'x-amz-expires': '900',
        'x-amz-signature': mock.ANY,
    }
    TestCase().assertEqual(actual, expected)


def test_aws_msk_iam_no_region(boto_session):
    # No region from config
    boto_session.get_config_variable = mock.MagicMock(return_value=None)

    with TestCase().assertRaises(Exception) as e:
        # No region from hostname
        msk_client = AwsMskIamClient(
            host='localhost',
            boto_session = boto_session,
        )
    assert 'Could not determine region from broker host(s) or aws configuration' == str(e.exception)


@pytest.mark.parametrize('session_token', [(None), ('the_token')])
def test_aws_msk_iam_permanent_and_temporary_credentials(session_token, request):
    boto_session = request.getfixturevalue('boto_session')
    if session_token:
        boto_session.get_credentials.return_value.token = session_token
    msk_client = AwsMskIamClient(
        host='localhost.us-east-1.amazonaws.com',
        boto_session = boto_session,
    )
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
        'x-amz-credential': '{}/{}/us-east-1/kafka-cluster/aws4_request'.format(msk_client.access_key, datetime.datetime.utcnow().strftime('%Y%m%d')),
        'x-amz-date': mock.ANY,
        'x-amz-signedheaders': 'host',
        'x-amz-expires': '900',
        'x-amz-signature': mock.ANY,
    }
    if session_token:
        expected['x-amz-security-token'] = session_token
    TestCase().assertEqual(actual, expected)
