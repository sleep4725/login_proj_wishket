from elasticsearch import Elasticsearch

class RetElastic:

    INDEX_ = "wisket"

    @classmethod
    def get_elastic_node(cls):
        es = Elasticsearch(hosts=["127.0.0.1:9200"])
        response = es.cluster.health()
        if response["status"] == "yellow" or response["status"] == "green":
            print("Elasticsearch service alive !!")
            return es
        else:
            print("Elasticsearch service die !!")
            exit(1)