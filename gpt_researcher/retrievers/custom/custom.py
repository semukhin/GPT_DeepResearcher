from typing import Any, Dict, List, Optional
import requests
import os
from elasticsearch import Elasticsearch
import logging
import re
import json
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Конфигурация ElasticSearch
ES_HOST = "http://147.45.145.136:9200"
ES_USER = os.getenv("ES_USER", None)
ES_PASS = os.getenv("ES_PASS", None)
ES_INDICES = {
    "court_decisions": "court_decisions_index",
    "court_reviews": "court_reviews_index",
    "legal_articles": "legal_articles_index",
    "ruslawod_chunks": "ruslawod_chunks_index",
    "procedural_forms": "procedural_forms_index"
}

class CustomRetriever:
    """
    Кастомный ретривер для поиска по судебным документам через ElasticSearch
    """

    def __init__(self, query: str, query_domains=None):
        self.endpoint = os.getenv('RETRIEVER_ENDPOINT')
        self.params = self._populate_params() if self.endpoint else {}
        self.query = query
        
        try:
            self.es = self._get_es_client()
            logger.info("✅ Подключение к ElasticSearch успешно установлено")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к ElasticSearch: {str(e)}")
            self.es = None
            
            if not self.endpoint:
                logger.warning("⚠️ Нет доступных источников данных")

    def _populate_params(self) -> Dict[str, Any]:
        """Получение параметров из переменных окружения"""
        return {
            key[len('RETRIEVER_ARG_'):].lower(): value
            for key, value in os.environ.items()
            if key.startswith('RETRIEVER_ARG_')
        }

    def _get_es_client(self) -> Elasticsearch:
        """Создание клиента ElasticSearch с поддержкой авторизации"""
        try:
<<<<<<< Updated upstream
            if ES_USER and ES_PASS and ES_USER.lower() != 'none' and ES_PASS.lower() != 'none':
                logger.info("Подключение к ElasticSearch с авторизацией")
                es = Elasticsearch(
                    ES_HOST,
                    basic_auth=(ES_USER, ES_PASS),
                    retry_on_timeout=True,
                    max_retries=3
                )
            else:
                logger.info("Подключение к ElasticSearch без авторизации")
                es = Elasticsearch(
                    ES_HOST,
                    retry_on_timeout=True,
                    max_retries=3
                )
            
            if es.ping():
                return es
            else:
                raise ConnectionError("Не удалось подключиться к ElasticSearch")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к ElasticSearch: {e}")
            raise

    def extract_case_number(self, query: str) -> Optional[str]:
        """Извлечение номера дела из текста запроса"""
        patterns = [
            r'[АA]\d{1,2}-\d+/\d{2,4}(?:-[А-Яа-яA-Za-z0-9]+)*',  # Основной формат
            r'[АA]-\d+/\d{2,4}(?:-[А-Яа-яA-Za-z0-9]+)*'  # Альтернативный формат
        ]
        
        if isinstance(query, bytes):
            query = query.decode('utf-8')
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                case_number = match.group(0)
                logger.info(f"Извлечен номер дела: {case_number}")
                
                # Нормализация года
                parts = case_number.split('/')
                if len(parts) > 1:
                    year_part = parts[1].split('-')[0]
                    if len(year_part) == 2:
                        full_year = f"20{year_part}" if int(year_part) < 50 else f"19{year_part}"
                        case_number = case_number.replace(f"/{year_part}", f"/{full_year}", 1)
                        logger.info(f"Нормализован год в номере дела: {case_number}")
                
                return case_number
        return None

    def extract_company_name(self, query: str) -> Optional[str]:
        """Извлечение названия компании из запроса"""
        patterns = [
            r'(?:ООО|ЗАО|ОАО|ПАО|АО)\s*[«"]([^»"]+)[»"]',
            r'(?:ООО|ЗАО|ОАО|ПАО|АО)\s+([А-Яа-яA-Za-z0-9\s\-]+)',
            r'(?:ИП\s+[А-Я][а-я]+\s+[А-Я][а-я]+\s+[А-Я][а-я]+)',
            r'ОГРН\s*:\s*(\d{13}|\d{15})',
            r'ИНН\s*:\s*(\d{10}|\d{12})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                company = match.group(0)
                logger.info(f"Извлечено название компании: {company}")
                return company
        return None

    def extract_document_type(self, query: str) -> Optional[str]:
        """Извлечение типа документа из запроса"""
        doc_types = {
            "исковое заявление": ["исковое заявление", "иск"],
            "отзыв": ["отзыв на исковое заявление", "отзыв"],
            "апелляционная жалоба": ["апелляционная жалоба", "апелляция"],
            "кассационная жалоба": ["кассационная жалоба", "кассация"],
            "заявление": ["заявление", "ходатайство"],
            "определение": ["определение суда"],
            "решение": ["решение суда"],
            "постановление": ["постановление суда", "постановление"]
        }
        
        query_lower = query.lower()
        for doc_type, variants in doc_types.items():
            for variant in variants:
                if variant in query_lower:
                    logger.info(f"Извлечен тип документа: {doc_type}")
                    return doc_type
        return None

    def search_court_decisions(self, query: str, limit: int = 10) -> List[Dict]:
        """Поиск в индексе судебных решений с учетом всех типов информации"""
        try:
            index_name = ES_INDICES["court_decisions"]
            
            # Извлекаем всю возможную информацию из запроса
            case_number = self.extract_case_number(query)
            company_name = self.extract_company_name(query)
            doc_type = self.extract_document_type(query)
            
            # Формируем поисковый запрос
            should_clauses = []
            must_clauses = []
            
            # Поиск по номеру дела (если есть)
            if case_number:
                variants = [case_number]
                if 'А' in case_number:
                    variants.append(case_number.replace('А', 'A'))
                else:
                    variants.append(case_number.replace('A', 'А'))
                
                should_clauses.extend([
                    {"term": {"case_number": {"value": variant, "boost": 10.0}}} for variant in variants
                ])
                should_clauses.extend([
                    {"match_phrase": {"full_text": {"query": variant, "boost": 5.0}}} for variant in variants
                ])
                must_clauses.append({"bool": {"should": should_clauses, "minimum_should_match": 1}})
                should_clauses = []

            # Поиск по названию компании (если есть)
            if company_name:
                # Нормализация названия компании
                normalized_company = company_name.replace('«', '"').replace('»', '"').replace("'", '"')
                clean_company = re.sub(r'^(ООО|ЗАО|ОАО|ПАО|АО)\s*[«"]?\s*', '', normalized_company)
                clean_company = re.sub(r'[»"]?\s*$', '', clean_company)
                
                company_clauses = [
                    {"match_phrase": {"claimant": {"query": normalized_company, "boost": 8.0}}},
                    {"match_phrase": {"defendant": {"query": normalized_company, "boost": 8.0}}},
                    {"match": {"claimant": {"query": clean_company, "boost": 4.0, "fuzziness": "AUTO"}}},
                    {"match": {"defendant": {"query": clean_company, "boost": 4.0, "fuzziness": "AUTO"}}},
                    {"match_phrase": {"full_text": {"query": normalized_company, "boost": 2.0}}}
                ]
                must_clauses.append({"bool": {"should": company_clauses, "minimum_should_match": 1}})

            # Поиск по типу документа (если есть)
            if doc_type:
                doc_clauses = [
                    {"term": {"vid_dokumenta": {"value": doc_type, "boost": 6.0}}},
                    {"match_phrase": {"full_text": {"query": doc_type, "boost": 3.0}}}
                ]
                must_clauses.append({"bool": {"should": doc_clauses, "minimum_should_match": 1}})

            # Если нет специальных критериев, используем общий поиск
            if not must_clauses:
                must_clauses.append({
                    "multi_match": {
                        "query": query,
                        "fields": [
                            "case_number^10",
                            "claimant^8",
                            "defendant^8",
                            "subject^6",
                            "court_name^4",
                            "judges^3",
                            "full_text^2"
                        ],
                        "type": "best_fields",
                        "operator": "and",
                        "fuzziness": "AUTO"
                    }
                })

            # Формируем итоговый запрос
            body = {
                "query": {
                    "bool": {
                        "must": must_clauses
                    }
                },
                "size": limit,
                "_source": [
                    "case_number", "court_name", "date", "decision_date",
                    "subject", "claimant", "defendant", "full_text",
                    "doc_id", "chunk_id", "instance", "region",
                    "judges", "arguments", "conclusion", "result",
                    "laws", "amount", "vid_dokumenta", "vidpr"
                ],
                "sort": [
                    {"_score": {"order": "desc"}},
                    {"date": {"order": "desc", "missing": "_last"}},
                    {"doc_id": {"order": "asc"}},
                    {"chunk_id": {"order": "asc"}}
                ],
                "highlight": {
                    "fields": {
                        "full_text": {
                            "type": "unified",
                            "pre_tags": ["<b>"],
                            "post_tags": ["</b>"],
                            "fragment_size": 300,
                            "number_of_fragments": 3,
                            "fragmenter": "span"
                        },
                        "case_number": {"pre_tags": ["<b>"], "post_tags": ["</b>"]},
                        "claimant": {"pre_tags": ["<b>"], "post_tags": ["</b>"]},
                        "defendant": {"pre_tags": ["<b>"], "post_tags": ["</b>"]},
                        "subject": {"pre_tags": ["<b>"], "post_tags": ["</b>"]},
                        "court_name": {"pre_tags": ["<b>"], "post_tags": ["</b>"]},
                        "judges": {"pre_tags": ["<b>"], "post_tags": ["</b>"]}
                    }
                }
            }
            
            logger.info(f"Поисковый запрос: {json.dumps(body, ensure_ascii=False, indent=2)}")
            response = self.es.search(index=index_name, body=body)
            hits = response.body["hits"]["hits"]
            
            logger.info(f"Найдено документов: {len(hits)}")
            if hits:
                for hit in hits:
                    logger.info(f"Документ: score={hit['_score']}, case_number={hit['_source'].get('case_number')}")
            
            # Формируем результаты в нужном формате
            results = []
            for hit in hits:
                source = hit["_source"]
                
                # Добавляем метаданные
                source["score"] = hit["_score"]
                source["url"] = f"es://{index_name}/{hit['_id']}"
                source["index"] = index_name
                source["doc_type"] = "court_decision"
                
                # Обрабатываем даты
                for date_field in ['date', 'decision_date', 'indexed_at']:
                    if date_field in source and source[date_field]:
                        try:
                            source[date_field] = datetime.strptime(
                                source[date_field], '%Y-%m-%d'
                            ).strftime('%Y-%m-%d')
                        except:
                            pass
                
                # Собираем подсветку
                source["highlights"] = []
                if "highlight" in hit:
                    for field, fragments in hit["highlight"].items():
                        if isinstance(fragments, list):
                            source["highlights"].extend(fragments)
                        else:
                            source["highlights"].append(fragments)
                
                results.append(source)
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка при поиске в court_decisions_index: {str(e)}")
            return []

    def search(self, max_results: int = 10) -> List[Dict]:
        """Основной метод поиска по всем индексам"""
        try:
            # Проверяем наличие номера дела
            case_number = self.extract_case_number(self.query)
            if case_number:
                logger.info(f"Поиск по номеру дела: {case_number}")
                results = self.search_court_decisions(self.query, max_results)
                if results:
                    logger.info(f"Найдено {len(results)} результатов по номеру дела")
                    return results
                logger.info("По номеру дела ничего не найдено, продолжаем поиск...")
            
            # Проверяем наличие названия компании
            company_name = self.extract_company_name(self.query)
            if company_name:
                logger.info(f"Поиск по названию компании: {company_name}")
                results = self.search_court_decisions(self.query, max_results)
                if results:
                    logger.info(f"Найдено {len(results)} результатов по названию компании")
                    return results
                logger.info("По названию компании ничего не найдено, продолжаем поиск...")
            
            # Общий поиск по всем индексам
            logger.info("Выполняем общий поиск по всем индексам")
            all_results = []
            
            # Распределяем лимит между индексами
            per_index_limit = max(2, max_results // len(ES_INDICES))
            
            # Поиск в каждом индексе
            for index_type, index_name in ES_INDICES.items():
                try:
                    body = {
                        "size": per_index_limit,
                        "query": {
                            "multi_match": {
                                "query": self.query,
                                "fields": ["*"],
                                "type": "best_fields",
                                "operator": "and",
                                "fuzziness": "AUTO"
                            }
                        },
                        "highlight": {
                            "fields": {
                                "*": {
                                    "pre_tags": ["<b>"],
                                    "post_tags": ["</b>"],
                                    "fragment_size": 300,
                                    "number_of_fragments": 3
                                }
                            }
                        }
                    }
                    
                    response = self.es.search(index=index_name, body=body)
                    hits = response.body["hits"]["hits"]
                    
                    for hit in hits:
                        source = hit["_source"]
                        source["score"] = hit["_score"]
                        source["url"] = f"es://{index_name}/{hit['_id']}"
                        source["index"] = index_name
                        source["doc_type"] = index_type.rstrip('_index')
                        
                        # Обработка дат
                        for date_field in ['date', 'decision_date', 'publication_date', 'creation_date', 'indexed_at']:
                            if date_field in source and source[date_field]:
                                try:
                                    source[date_field] = datetime.strptime(
                                        source[date_field], '%Y-%m-%d'
                                    ).strftime('%Y-%m-%d')
                                except:
                                    pass
                        
                        # Сбор подсветки
                        source["highlights"] = []
                        if "highlight" in hit:
                            for field, fragments in hit["highlight"].items():
                                if isinstance(fragments, list):
                                    source["highlights"].extend(fragments)
                                else:
                                    source["highlights"].append(fragments)
                        
                        all_results.append(source)
                    
                except Exception as e:
                    logger.error(f"Ошибка при поиске в индексе {index_name}: {str(e)}")
                    continue
            
            # Сортируем результаты по релевантности
            all_results.sort(key=lambda x: (x.get("score", 0), len(x.get("highlights", []))), reverse=True)
            
            logger.info(f"Общий поиск: найдено {len(all_results)} результатов")
            return all_results[:max_results]
            
        except Exception as e:
            logger.error(f"Ошибка при выполнении поиска: {str(e)}")
            return []
=======
            response = requests.get(self.endpoint, params={**self.params, 'query': self.query}, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to retrieve search results: {e}")
            return None
>>>>>>> Stashed changes
