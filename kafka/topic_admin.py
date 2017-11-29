import time
from .client import KafkaClient
from .errors import BrokerNotAvailableError
from .protocol.admin import CreateTopicsRequest
from .protocol.metadata import MetadataRequest

class TopicAdmin(object):
    """
    An api to send CreateTopic requests
    
    """    
    def __init__(self, **configs):
        self.client = KafkaClient(**configs)
        self.nodes = [broker.nodeId for broker in self.client.cluster.brokers()]
        self.metadata_request = MetadataRequest[1]([])
        self.controller_id = self.get_controller_id()
        self.topic_request = CreateTopicsRequest[1]
    
    def get_controller_id(self):
        """ returns the controller id of the cluster."""
        for node in self.nodes:
            if self.client.connected(node) == True:
                future = self.client.send(node, self.metadata_request)
                response = self.client.poll(future)
                return response[0].controller_id

    def _send(self, request):
        future = self.client.send(self.controller_id, request)
        return self.client.poll(future)

    def _send_topic_request(self, topic_request, max_retry=10):
        retry = 0
        if self.client.ready(self.controller_id) == False:
            while(
                self.client.ready(self.controller_id) == False and
                retry <= max_retry
            ):
                if self.client.ready(self.controller_id) == True:
                    return self._send(topic_request)
                retry += 1
                # gives a breathing space before checking the node again
                time.sleep(0.2)
        else:
            return self._send(topic_request)
        
        raise BrokerNotAvailableError()
        
    def create_topic_simple(
        self, 
        name, 
        num_partitions, 
        replication_factor,
        validate_only=False,
        timeout=0, 
        max_retry=10,
    ):
        """ Creates a topic on the cluster 

        Arguments:
            name (string): name of the topic
            num_partitions (int): number of partitions 
            replication_factor (int): replication factor 
            validate_only (bool): True if we just want validate the request
            timeout (int): timeout in seconds 
            max_retry (int): num of times we want to retry to send a create
                topic request when the controller in not available

        Returns:
            CreateTopicResponse: response from the broker
        
        Raises: 
            BrokerNotAvailableError: if retry exceeds max_retry
        """
       
        request = self.topic_request([(
                name, num_partitions, replication_factor, [], []
            )], timeout, validate_only
        )
        return self._send_topic_request(request, max_retry)

    def create_topic_thorough(
        self, 
        name,
        replica_assignments,
        topic_configs,
        validate_only=False,
        timeout=0,
        max_retry=10,
    ):
        """ Creates a topic on the cluster 
        
        Arguments:
            name (string): name of the topic.
            timeout (int): timeout in seconds.
            replica_assignment (dict of int: [int]): A mapping containing 
                partition id and replicas to assign to it.
            topic_configs (dict of str: str): A mapping of config key 
                and value for the topic.
        Returns:
            CreateTopicResponse: response from the broker.
        
        Raises:
            BrokerNotAvailableError: if retry exceeds max_retry
        """
        replica_assignment_array = [
            (partition_id,replicas) for partition_id,replicas in 
            replica_assignments.iteritems()
        ]
        topic_configs_array = [
            (config_key,config_value) for config_key, config_value in 
            topic_configs.iteritems()
        ]
        request = self.topic_request([(
                name, -1, -1, replica_assignment_array, topic_configs_array
            )], timeout, validate_only
        )
        return self._send_topic_request(request, max_retry)
        

