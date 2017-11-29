import mock
import pytest
from kafka.client_async import KafkaClient
from kafka.protocol.metadata import MetadataResponse
from kafka.protocol.admin import CreateTopicsResponse
from kafka.topic_admin import TopicAdmin 
from kafka.structs import BrokerMetadata
from kafka.future import Future

@pytest.fixture
def bootstrap_brokers():
    return 'fake-broker:9092'

@pytest.fixture
def controller_id():
    return 100

@pytest.fixture
def brokers():
   return [BrokerMetadata(nodeId=1,host="host",port=80,rack='rack')]
    

@pytest.fixture
def metadata_response(controller_id):
    return [MetadataResponse[1](
        [(1,'host',80,'rack')], controller_id, 
        [(37,'topic',False,[(7,1,2,[1,2,3],[1,2,3])])]        
    )]

@pytest.fixture
def topic_response():
    return CreateTopicsResponse[1]([(
        'topic',7,'timeout_exception'     
    )])

class TestTopicAdmin():

    def test_get_controller_id(
        self, 
        brokers, 
        controller_id, 
        bootstrap_brokers, 
        metadata_response
    ):
         with mock.patch(
              'kafka.topic_admin.KafkaClient', auto_spec=True
         ) as mock_kafka_client:
             mock_kafka_client.return_value.poll.return_value = metadata_response
             mock_kafka_client.return_value.cluster.brokers.return_value = brokers
             mock_kafka_client.return_value.send.return_value = Future()
             mock_kafka_client.return_value.connected.return_value = True
             admin = TopicAdmin(bootstrap_servers=bootstrap_brokers)
             assert admin.get_controller_id() == controller_id

    def test_create_topic_simple(
        self, 
        brokers,
        bootstrap_brokers,
        topic_response,
        metadata_response, 
    ):
         with mock.patch(
              'kafka.topic_admin.KafkaClient', auto_spec=True
         ) as mock_kafka_client:
             mock_kafka_client.return_value.poll.return_value = metadata_response
             mock_kafka_client.return_value.ready.return_value = True
             mock_kafka_client.return_value.cluster.brokers.return_value = brokers
             mock_kafka_client.return_value.send.return_value = Future()
             mock_kafka_client.return_value.connected.return_value = True
             admin = TopicAdmin(bootstrap_servers=bootstrap_brokers)
             mock_kafka_client.return_value.poll.return_value = topic_response
             response = admin.create_topic_simple('topic', 1, 1)
             assert response == topic_response 


