import uuid
from datetime import datetime
from typing import List, Union

from db_driver import get_current_db_driver
from db_driver.db_objects.article import Article
from db_driver.db_objects.cluster import Cluster
from db_driver.db_objects.db_objects_utils import get_db_object_from_dict
from db_driver.utils.consts import DBConsts
from db_driver.utils.exceptions import UpdateDataDBException, DataNotFoundDBException, CreateNewClusterException
from logger import get_current_logger, log_function
from db_utils.article_utils import ArticleUtils
from server_consts import ClusterConsts


class ClusterUtils:
    def __init__(self):
        self.logger = get_current_logger()
        self._db = get_current_db_driver()
        self.article_utils = ArticleUtils()

    # todo: separate first part of the function to another function called `_create_empty_cluster`
    @log_function
    def create_new_cluster(
            self, article: Article, classified_categories: List[str] = None, trend: str = None) -> Cluster:
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
                "categories": categories,
                "trend": trend
            }
            cluster: Cluster = Cluster(**cluster_data)
            _id = self._db.insert_one(table_name=DBConsts.CLUSTERS_TABLE_NAME, data=cluster.convert_to_dict())
            self.logger.info(f"Inserted cluster inserted_id: `{_id}`, cluster_id: `{cluster.cluster_id}`")
            self.article_utils.update_cluster_id(article_id=article.article_id, cluster_id=cluster_data["cluster_id"])
            return cluster
        except Exception as e:
            desc = f"Error insert cluster - {str(e)}"
            self.logger.exception(desc)
            raise CreateNewClusterException(desc)

    def create_cluster_from_articles_list(self, articles: List[Article],
                                          classified_categories: List[str] = None, trend: str = None) -> Cluster:
        if len(articles) == 0:
            desc = f"Cannot create cluster with empty list of articles"
            raise CreateNewClusterException(desc)

        first_article: Article = articles[0]
        cluster = self.create_new_cluster(
            article=first_article, classified_categories=classified_categories, trend=trend
        )
        articles.remove(first_article)
        for article in articles:
            cluster = self.add_article_to_cluster(cluster=cluster, article=article)
        return cluster

    @log_function
    def get_cluster(self, cluster_id: str) -> Cluster:
        data_filter = {"cluster_id": cluster_id}
        cluster_data = self._db.get_one(table_name=DBConsts.CLUSTERS_TABLE_NAME, data_filter=data_filter)
        cluster_object: Cluster = get_db_object_from_dict(object_dict=cluster_data, class_instance=Cluster)
        return cluster_object

    @log_function
    def get_cluster_by_trend(self, trend: str) -> Union[Cluster, None]:
        try:
            data_filter = {"trend": trend}
            cluster_data = self._db.get_one(table_name=DBConsts.CLUSTERS_TABLE_NAME, data_filter=data_filter)
            cluster_object: Cluster = get_db_object_from_dict(object_dict=cluster_data, class_instance=Cluster)
            return cluster_object
        except DataNotFoundDBException:
            return None

    @log_function
    def get_clusters(self, different_domain: str = None, category: List[str] = None) -> List[Cluster]:
        try:
            clusters: List[Cluster] = list()
            data_filter = dict()
            if different_domain:
                data_filter = {"domains": {"$nin": [different_domain]}}
            if category:
                data_filter.update({"categories": {"$in": category}})
            clusters_dicts = self._db.get_many(table_name=DBConsts.CLUSTERS_TABLE_NAME, data_filter=data_filter)
            for cluster_dict in clusters_dicts:
                cluster: Cluster = get_db_object_from_dict(object_dict=cluster_dict, class_instance=Cluster)
                clusters.append(cluster)
            return clusters
        except DataNotFoundDBException:
            return []

    @log_function
    def add_article_to_cluster(self, cluster: Cluster, article: Article) -> Cluster:

        # Article id
        if article.article_id in cluster.articles_id:
            self.logger.warning(f"Cannot add article to cluster that already has the article")
            return cluster

        cluster.articles_id.append(article.article_id)

        # Domain
        if article.domain not in cluster.domains:
            cluster.domains.append(article.domain)

        # Update
        data_filter = {"cluster_id": cluster.cluster_id}
        data = {"articles_id": cluster.articles_id, "domains": cluster.domains, "last_updated": datetime.now()}
        for try_counter in range(ClusterConsts.TIMES_TRY_UPDATE_CLUSTER):
            try:
                self._db.update_one(table_name=DBConsts.CLUSTERS_TABLE_NAME, data_filter=data_filter, new_data=data)
                self.article_utils.update_cluster_id(article_id=article.article_id, cluster_id=cluster.cluster_id)
                self.logger.info(f"Updated cluster cluster_id: `{cluster.cluster_id}`")
                return cluster
            except Exception as e:
                desc = f"Error insert article NO. {try_counter}/{ClusterConsts.TIMES_TRY_UPDATE_CLUSTER} - {str(e)}"
                self.logger.warning(desc)
                continue
        desc = f"Error inserting article into db after {ClusterConsts.TIMES_TRY_UPDATE_CLUSTER} tries"
        raise UpdateDataDBException(desc)

    def get_all_clusters(self):
        clusters: List[Cluster] = list()
        clusters_data = self._db.get_many(table_name=DBConsts.CLUSTERS_TABLE_NAME, data_filter={})
        for cluster_data in clusters_data:
            clusters.append(get_db_object_from_dict(object_dict=cluster_data, class_instance=Cluster))
        return clusters

    def get_all_domains(self) -> List[str]:
        clusters: List[Cluster] = self.get_all_clusters()
        domains = set()
        for cluster in clusters:
            for domain in cluster.domains:
                domains.add(domain)
        return list(domains)


# For debug
if __name__ == '__main__':
    article_utils = ArticleUtils()
    new_article: Article = article_utils.get_article_by_url(
        article_url="https://www.bbc.com/news/world-europe-65471904")
    cluster_utils = ClusterUtils()
    cluster_utils.create_new_cluster(article=new_article, classified_categories=["finance", "bitcoin"])
