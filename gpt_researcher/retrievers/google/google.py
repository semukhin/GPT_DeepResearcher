# Google Custom Search API Retriever

import os
import json
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv
import googleapiclient.discovery

# Загружаем переменные окружения из .env файла
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(env_path)

logger = logging.getLogger(__name__)

def load_google_credentials():
    """Загрузка учетных данных из JSON файла"""
    api_key_path = os.getenv("GOOGLE_API_KEY")
    if not api_key_path:
        raise ValueError("Не указан путь к JSON файлу с ключом в GOOGLE_API_KEY")
    
    try:
        with open(api_key_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при чтении JSON файла с ключом: {str(e)}")
        raise

class GoogleSearch:
    """Класс для выполнения поисковых запросов через Google Custom Search API"""
    
    def __init__(
        self,
        query: str,
        api_key: Optional[str] = None,
        custom_search_engine_id: Optional[str] = None,
        safe_search: bool = True,
        language: Optional[str] = None,
        country: Optional[str] = None,
        query_domains: Optional[List[str]] = None,
        exact_terms: Optional[str] = None,
        file_type: Optional[str] = None,
        date_restrict: Optional[str] = None
    ):
        """
        Инициализация поискового клиента
        
        Args:
            query (str): Поисковый запрос
            api_key (Optional[str]): API ключ для Google Custom Search API
            custom_search_engine_id (Optional[str]): ID поисковой системы
            safe_search (bool): Включить безопасный поиск
            language (Optional[str]): Код языка для поиска (например, 'ru')
            country (Optional[str]): Код страны для поиска (например, 'RU')
            query_domains (Optional[List[str]]): Список доменов для поиска
            exact_terms (Optional[str]): Точное совпадение фразы
            file_type (Optional[str]): Тип файла для поиска
            date_restrict (Optional[str]): Ограничение по дате (например, 'd[number]')
        """
        self.query = query
        
        # Загружаем API ключ
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.custom_search_engine_id = custom_search_engine_id or os.getenv("GOOGLE_CX_KEY")
        
        if not self.api_key or not self.custom_search_engine_id:
            raise ValueError("Необходимо указать GOOGLE_API_KEY и GOOGLE_CX_KEY")
            
        # Удаляем кавычки из API ключа, если они есть
        self.api_key = self.api_key.strip('"')
            
        self.safe_search = "active" if safe_search else "off"
        self.language = language
        self.country = country
        self.query_domains = query_domains
        self.exact_terms = exact_terms
        self.file_type = file_type
        self.date_restrict = date_restrict
        
        # Создаем сервис с использованием API ключа
        self.service = googleapiclient.discovery.build(
            "customsearch", "v1",
            developerKey=self.api_key,
            cache_discovery=False
        )
        
        self.logger = logging.getLogger(__name__)
    
    def _make_search_request(self, start_index: int = 1) -> Dict:
        """
        Выполнение поискового запроса с учетом всех параметров
        
        Args:
            start_index (int): Начальный индекс для пагинации
            
        Returns:
            Dict: Результаты поиска
        """
        try:
            # Формируем базовый запрос
            search_params = {
                "q": self.query,
                "cx": self.custom_search_engine_id,
                "safe": self.safe_search,
                "start": start_index
            }
            
            # Добавляем опциональные параметры
            if self.language:
                search_params["lr"] = f"lang_{self.language}"
            
            if self.country:
                search_params["cr"] = f"country{self.country}"
            
            if self.query_domains:
                search_params["siteSearch"] = "|".join(self.query_domains)
                search_params["siteSearchFilter"] = "i"  # include only these sites
            
            if self.exact_terms:
                search_params["exactTerms"] = self.exact_terms
                
            if self.file_type:
                search_params["fileType"] = self.file_type
                
            if self.date_restrict:
                search_params["dateRestrict"] = self.date_restrict
            
            # Выполняем поиск
            self.logger.info(f"Выполняем поиск с параметрами: {json.dumps(search_params, ensure_ascii=False)}")
            result = self.service.cse().list(**search_params).execute()
            
            return result
            
        except googleapiclient.errors.HttpError as e:
            self.logger.error(f"Ошибка при выполнении поиска: {str(e)}")
            raise
    
    def search(self, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Выполнение поиска и получение результатов
        
        Args:
            max_results (int): Максимальное количество результатов
            
        Returns:
            List[Dict[str, str]]: Список результатов поиска
        """
        results = []
        start_index = 1
        
        while len(results) < max_results:
            try:
                response = self._make_search_request(start_index)
                
                if "items" not in response:
                    self.logger.warning("Поиск не вернул результатов")
                    break
                    
                for item in response["items"]:
                    if len(results) >= max_results:
                        break
                        
                    result = {
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "body": item.get("snippet", "")
                    }
                    
                    results.append(result)
                    
                if len(response["items"]) < 10:  # Google возвращает максимум 10 результатов за запрос
                    break
                    
                start_index += 10
                
            except Exception as e:
                self.logger.error(f"Ошибка при получении результатов: {str(e)}")
                break
        
        return results[:max_results]
