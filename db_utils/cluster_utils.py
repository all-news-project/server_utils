import uuid
from datetime import datetime
from typing import List

from db_driver import get_current_db_driver, DBConsts
from db_driver.db_objects.article import Article
from db_driver.db_objects.cluster import Cluster
from db_driver.db_objects.db_objects_utils import get_db_object_from_dict
from db_utils.article_utils import ArticleUtils
from logger import get_current_logger, log_function


class ClusterUtils:
    def __init__(self):
        self.logger = get_current_logger()
        self._db = get_current_db_driver()

    @log_function
    def create_new_cluster(self, article: Article, classified_categories: List[str] = None) -> str:
        try:
            current_time = datetime.now()
            categories = classified_categories if classified_categories else list()
            cluster_data = {
                "cluster_id": str(uuid.uuid4()),
                "articles_id": [article.article_id],
                "main_article_id": article.article_id,
                "creation_time": current_time,
                "last_updated": current_time,
                "domains": [article.domain],
                "categories": categories
            }
            cluster: Cluster = Cluster(**cluster_data)
            _id = self._db.insert_one(table_name=DBConsts.CLUSTERS_TABLE_NAME, data=cluster.convert_to_dict())
            self.logger.info(f"Inserted cluster inserted_id: `{_id}`, cluster_id: `{cluster.cluster_id}`")
            return _id
        except Exception as e:
            desc = f"Error insert cluster - {str(e)}"
            self.logger.exception(desc)

    def get_cluster(self, cluster_id: str) -> Cluster:
        data_filter = {"cluster_id": cluster_id}
        cluster_data = self._db.get_one(table_name=DBConsts.CLUSTERS_TABLE_NAME, data_filter=data_filter)
        cluster_object: Cluster = get_db_object_from_dict(object_dict=cluster_data, class_instance=Cluster)
        return cluster_object

    def get_all_clusters(self):
        clusters: List[Article] = list()
        clusters_data = self._db.get_many(table_name=DBConsts.CLUSTERS_TABLE_NAME, data_filter={})
        for cluster_data in clusters_data:
            clusters.append(get_db_object_from_dict(object_dict=cluster_data, class_instance=Cluster))
        return clusters


# For debug
if __name__ == '__main__':
    article_utils = ArticleUtils()
    new_article: Article = article_utils.get_article_by_url(
        article_url="https://www.bbc.com/news/world-europe-65471904")
    cluster_utils = ClusterUtils()
    cluster_utils.create_new_cluster(article=new_article, classified_categories=["finance", "bitcoin"])
