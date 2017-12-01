import os

from kafka.protocol.admin import CreateTopicsRequest, DeleteTopicsRequest
from kafka.admin_client import AdminClient, NewTopic
from test.fixtures import ZookeeperFixture, KafkaFixture
from test.testutil import KafkaIntegrationTestCase

class TestKafkaAdminClientIntegration(KafkaIntegrationTestCase):
    
    @classmethod
    def setUpClass(cls):
        if not os.environ.get('KAFKA_VERSION'):
            return

        cls.zk = ZookeeperFixture.instance()
        cls.server = KafkaFixture.instance(0, cls.zk.host, cls.zk.port)

    @classmethod
    def tearDownClass(cls):  
        if not os.environ.get('KAFKA_VERSION'):
            return

        cls.server.close()
        cls.zk.close()

    def test_create_topics(self):
        admin = AdminClient(self.client_async)
        topic = NewTopic(
            name='topic', 
            num_partitions=1, 
            replication_factor=1,
        )

        response = admin.create_topics(topics=[topic], validate_only=False, timeout=1)
        assert response[0].error_code == 0

    def test_delete_topics(self):
        admin = AdminClient(self.client_async)
        response = admin.delete_topics(['topic'], timeout=1) 
        assert response[0].error_code == 0
       
        
