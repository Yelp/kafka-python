import os
import time
import unittest
import pytest
from kafka.admin_client import AdminClient, NewTopic, NewPartitionsInfo
from kafka.protocol.metadata import MetadataRequest 
from test.fixtures import ZookeeperFixture, KafkaFixture
from test.testutil import KafkaIntegrationTestCase, env_kafka_version

KAFKA_ADMIN_TIMEOUT_SECONDS = 5

class TestKafkaAdminClientIntegration(KafkaIntegrationTestCase):
    
    @classmethod
    def setUpClass(cls):
        if not os.environ.get('KAFKA_VERSION'):
            return

        cls.zk = ZookeeperFixture.instance()
        cls.server = KafkaFixture.instance(0, cls.zk)

    @classmethod
    def tearDownClass(cls):  
        if not os.environ.get('KAFKA_VERSION'):
            return

        cls.server.close()
        cls.zk.close()
    
    @pytest.mark.skipif(env_kafka_version() < (0, 10, 1), reason='Unsupported Kafka Version')
    def test_create_delete_topics(self):
        admin = AdminClient(self.client_async)
        topic = NewTopic(
            name='topic', 
            num_partitions=1, 
            replication_factor=1,
        )
        metadata_request = MetadataRequest[1]()
        response = admin.create_topics(topics=[topic], timeout=KAFKA_ADMIN_TIMEOUT_SECONDS)
        # Error code 7 means that RequestTimedOut but we can safely assume
        # that topic is created or will be created eventually. 
        # see this https://cwiki.apache.org/confluence/display/KAFKA/
        # KIP-4+-+Command+line+and+centralized+administrative+operations
        self.assertTrue(
            response[0].topic_errors[0][1] == 0 or
            response[0].topic_errors[0][1] == 7
        )
        time.sleep(1) # allows the topic to be created
        delete_response = admin.delete_topics(['topic'], timeout=1)
        self.assertTrue(
            response[0].topic_errors[0][1] == 0 or
            response[0].topic_errors[0][1] == 7
        )

    @pytest.mark.skipif(env_kafka_version() < (1, 0, 0), reason='Unsupported Kafka Version')
    def test_create_partitions(self):
        admin = AdminClient(self.client_async)
        topic = NewTopic(
            name='topic',
            num_partitions=1,
            replication_factor=1,
        )
        metadata_request = MetadataRequest[1]()
        admin.create_topics(topics=[topic], timeout=KAFKA_ADMIN_TIMEOUT_SECONDS)

        time.sleep(1) # allows the topic to be created

        new_partitions_info = NewPartitionsInfo('topic', 2, [[0]])
        response = admin.create_partitions([new_partitions_info], timeout=1, validate_only=False)

        self.assertTrue(
            response[0].topic_errors[0][1] == 0 or
            response[0].topic_errors[0][1] == 7
        )
