from gpt_researcher.retrievers.custom.custom import CustomRetriever, ES_HOST, ES_INDICES
from elasticsearch import Elasticsearch
import json
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_elasticsearch_connection():
    """Проверяем подключение к ElasticSearch и наличие индексов"""
    print("\nПроверка подключения к ElasticSearch...")
    
    es = Elasticsearch([ES_HOST], retry_on_timeout=True, max_retries=3)
    if es.ping():
        print("✅ Подключение к ElasticSearch успешно!")
        
        print("\nПроверка индексов:")
        for name, index in ES_INDICES.items():
            if es.indices.exists(index=index):
                count = es.count(index=index)["count"]
                print(f"{index}: ✅ существует")
                print(f"  - Количество документов: {count}")
                
                # Получаем и выводим маппинг индекса
                print(f"\nМаппинг индекса {index}:")
                mapping = es.indices.get_mapping(index=index)
                mapping_dict = mapping.body
                print(json.dumps(mapping_dict, ensure_ascii=False, indent=2))
            else:
                print(f"{index}: ❌ не существует")
    else:
        print("❌ Не удалось подключиться к ElasticSearch")
        assert False

def test_information_extraction():
    """Проверяем извлечение информации из запросов пользователя"""
    print("\nПроверка извлечения информации из запросов...")
    
    test_queries = [
        {
            "query": "Привет! Приведи информацию по делу А03-13997/2019",
            "expected_case": "А03-13997/2019",
            "expected_company": None,
            "expected_doc_type": None
        },
        {
            "query": "Найди решения по ООО «Сахкомцентр»",
            "expected_case": None,
            "expected_company": "ООО «Сахкомцентр»",
            "expected_doc_type": None
        }
    ]
    
    for test_case in test_queries:
        print(f"\nЗапрос: {test_case['query']}")
        retriever = CustomRetriever(query=test_case['query'])
        
        # Проверяем извлечение номера дела
        case_number = retriever.extract_case_number(test_case['query'])
        print(f"Номер дела: {case_number}")
        assert case_number == test_case['expected_case'], f"Ожидали номер дела: {test_case['expected_case']}, получили: {case_number}"
        
        # Проверяем извлечение названия компании
        company = retriever.extract_company_name(test_case['query'])
        print(f"Компания: {company}")
        assert company == test_case['expected_company'], f"Ожидали название компании: {test_case['expected_company']}, получили: {company}"
        
        # Проверяем извлечение типа документа
        doc_type = retriever.extract_document_type(test_case['query'])
        print(f"Тип документа: {doc_type}")
        assert doc_type == test_case['expected_doc_type'], f"Ожидали тип документа: {test_case['expected_doc_type']}, получили: {doc_type}"

def test_elasticsearch_search():
    """Проверяем поиск в ElasticSearch через CustomRetriever"""
    # Сначала проверяем подключение
    test_elasticsearch_connection()
    
    print("\nНачинаем тестирование поиска...")
    
    # Тестовые запросы
    test_queries = [
        "Привет! Приведи информацию по делу А03-13997/2019",
        "Найди решения по ООО «Сахкомцентр»",
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Поиск по запросу: {query}")
        print(f"{'='*80}")
        
        # Создаем экземпляр CustomRetriever
        retriever = CustomRetriever(query=query)
        
        # Перехватываем и логируем запросы к ElasticSearch
        def log_es_request(self, method, url, body=None, *args, **kwargs):
            if body:
                print("\nЗапрос к ElasticSearch:")
                print(json.dumps(body, ensure_ascii=False, indent=2))
            return original_transport_perform_request(self, method, url, body, *args, **kwargs)
        
        # Сохраняем оригинальный метод
        original_transport_perform_request = retriever.es.transport.perform_request
        # Подменяем метод на наш с логированием
        retriever.es.transport.perform_request = log_es_request.__get__(retriever.es.transport)
        
        try:
            # Выполняем поиск
            results = retriever.search(max_results=10)
            
            if results:
                print(f"\nНайдено результатов: {len(results)}")
                for i, result in enumerate(results, 1):
                    print(f"\nРезультат #{i}:")
                    print(f"URL: {result.get('url', 'Нет URL')}")
                    
                    # Выводим основные поля, если они есть
                    if 'case_number' in result:
                        print(f"Номер дела: {result['case_number']}")
                    if 'court_name' in result:
                        print(f"Суд: {result['court_name']}")
                    if 'date' in result:
                        print(f"Дата: {result['date']}")
                    if 'subject' in result:
                        print(f"Предмет спора: {result['subject']}")
                    if 'claimant' in result:
                        print(f"Истец: {result['claimant']}")
                    if 'defendant' in result:
                        print(f"Ответчик: {result['defendant']}")
                    
                    # Выводим подсвеченные фрагменты
                    if 'highlights' in result and result['highlights']:
                        print("\nРелевантные фрагменты:")
                        for highlight in result['highlights']:
                            print(f"... {highlight} ...")
                    
                    print(f"\n{'-'*40}")
            else:
                print("\nРезультатов не найдено")
        
        finally:
            # Восстанавливаем оригинальный метод
            retriever.es.transport.perform_request = original_transport_perform_request
            
        print(f"\n{'='*80}")

if __name__ == "__main__":
    test_elasticsearch_search() 