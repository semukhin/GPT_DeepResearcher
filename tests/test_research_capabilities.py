import pytest
from unittest.mock import Mock, patch
from gpt_researcher.retrievers.google.google import GoogleSearch
import googleapiclient.errors
import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

@pytest.fixture(scope="session", autouse=True)
def debug_info():
    """Фикстура для вывода отладочной информации"""
    print("\n=== Отладочная информация ===")
    
    # Проверяем переменные окружения до загрузки .env
    print("\nПеременные окружения до загрузки .env:")
    print(f"GOOGLE_API_KEY: {os.getenv('GOOGLE_API_KEY')}")
    print(f"GOOGLE_CX_KEY: {os.getenv('GOOGLE_CX_KEY')}")
    
    # Загружаем переменные окружения из .env файла
    env_path = Path(__file__).parent.parent / '.env'
    print(f"\nПуть к .env: {env_path}")
    print(f"Файл .env существует: {env_path.exists()}")
    
    if env_path.exists():
        print("\nСодержимое .env:")
        with open(env_path, 'r') as f:
            content = f.read()
            print(content)
    
    load_dotenv(env_path)
    
    # Проверяем переменные окружения после загрузки .env
    print("\nПеременные окружения после загрузки .env:")
    print(f"GOOGLE_API_KEY: {os.getenv('GOOGLE_API_KEY')}")
    print(f"GOOGLE_CX_KEY: {os.getenv('GOOGLE_CX_KEY')}")
    
    print("\n===========================\n")
    sys.stdout.flush()

# Загружаем переменные окружения
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

# Константы для тестов
GOOGLE_API_KEY = "AIzaSyBp7NK3RotprHPYXKlutdawMdU7fACEVSI"
GOOGLE_CX_KEY = "31a742e3d78ce478c"

# Отладочная информация
print("\nОтладочная информация:")
print(f"Текущая директория: {os.getcwd()}")
print(f"Путь к .env: {env_path}")
print(f"GOOGLE_API_KEY: {GOOGLE_API_KEY}")
print(f"GOOGLE_CX_KEY: {GOOGLE_CX_KEY}")

@pytest.fixture
def google_credentials():
    """Получение учетных данных для Google Search"""
    return {
        "api_key": GOOGLE_API_KEY,
        "custom_search_engine_id": GOOGLE_CX_KEY
    }

@pytest.fixture
def google_search(google_credentials):
    """Создание экземпляра GoogleSearch"""
    return GoogleSearch(
        query="test query",
        api_key=google_credentials["api_key"],
        custom_search_engine_id=google_credentials["custom_search_engine_id"]
    )

def test_google_search(google_search):
    """Тест поиска через Google Custom Search API"""
    results = google_search.search()
    
    # Проверяем структуру результатов
    assert isinstance(results, list)
    assert len(results) > 0
    
    # Проверяем наличие обязательных полей
    for result in results:
        assert "title" in result
        assert "link" in result
        assert "body" in result  # Изменено с snippet на body

# ---------- Тесты для GoogleSearch ----------

def pytest_configure(config):
    """Проверка наличия необходимых переменных окружения"""
    required_env_vars = ["GOOGLE_API_KEY", "GOOGLE_CX_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        pytest.exit(f"Отсутствуют необходимые переменные окружения: {', '.join(missing_vars)}")

def test_google_search_initialization(google_search):
    """Тест инициализации класса GoogleSearch"""
    assert google_search.query == "test query"
    assert google_search.api_key == GOOGLE_API_KEY
    assert google_search.custom_search_engine_id == GOOGLE_CX_KEY
    assert google_search.safe_search == "active"
    assert google_search.language is None
    assert google_search.country is None
    assert google_search.query_domains is None
    assert google_search.exact_terms is None
    assert google_search.file_type is None
    assert google_search.date_restrict is None

def test_google_search_initialization_with_params():
    """Тест инициализации с дополнительными параметрами"""
    search = GoogleSearch(
        query="test",
        api_key=GOOGLE_API_KEY,
        custom_search_engine_id=GOOGLE_CX_KEY,
        safe_search=False,
        language="ru",
        country="RU",
        query_domains=["example.com"],
        exact_terms="exact phrase",
        file_type="pdf",
        date_restrict="d1"
    )
    
    assert search.query == "test"
    assert search.api_key == GOOGLE_API_KEY
    assert search.custom_search_engine_id == GOOGLE_CX_KEY
    assert search.safe_search == "off"
    assert search.language == "ru"
    assert search.country == "RU"
    assert search.query_domains == ["example.com"]
    assert search.exact_terms == "exact phrase"
    assert search.file_type == "pdf"
    assert search.date_restrict == "d1"

@pytest.mark.integration
def test_real_search_with_domains():
    """Интеграционный тест с реальным поиском юридической информации"""
    search = GoogleSearch(
        query="Расторжение договора подряда",
        api_key=GOOGLE_API_KEY,
        custom_search_engine_id=GOOGLE_CX_KEY,
        language="ru",
        safe_search=True
    )
    
    results = search.search(max_results=10)
    
    # Выводим результаты поиска
    print("\nНайденные результаты:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   Ссылка: {result['link']}")
        print(f"   Описание: {result['body'][:200]}...")
    
    # Проверяем, что получили результаты
    assert len(results) > 0
    
    # Проверяем структуру результатов
    for result in results:
        # Проверяем структуру результата
        assert "title" in result
        assert "link" in result
        assert "body" in result
        
        # Проверяем, что поля не пустые
        assert result["title"].strip()
        assert result["link"].strip()
        assert result["body"].strip()
        
        # Проверяем наличие юридических терминов в результатах
        legal_terms = [
            "договор",
            "подряд",
            "расторжение",
            "закон",
            "статья",
            "суд",
            "иск",
            "гк рф",
            "кодекс",
            "право"
        ]
        
        # Проверяем, что хотя бы один юридический термин присутствует в результате
        text_content = (result["title"] + " " + result["body"]).lower()
        assert any(term in text_content for term in legal_terms), \
            f"Не найдены юридические термины в результате: {result['title']}"

@pytest.mark.integration
def test_real_search_with_date_restrict():
    """Интеграционный тест поиска с ограничением по дате"""
    search = GoogleSearch(
        query="Изменения в ГК РФ",
        api_key=GOOGLE_API_KEY,
        custom_search_engine_id=GOOGLE_CX_KEY,
        date_restrict="m6",  # За последние 6 месяцев
        language="ru"
    )
    
    results = search.search(max_results=10)
    
    # Выводим результаты поиска
    print("\nНайденные результаты по запросу 'Изменения в ГК РФ' за последние 6 месяцев:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   Ссылка: {result['link']}")
        print(f"   Описание: {result['body'][:200]}...")
    
    # Проверяем, что получили результаты
    assert len(results) > 0
    
    # Проверяем структуру результатов
    for result in results:
        assert "title" in result
        assert "link" in result
        assert "body" in result
        assert all(result[key].strip() for key in ["title", "link", "body"])
        
        # Проверяем наличие юридических терминов
        legal_terms = [
            "закон",
            "гк",
            "кодекс",
            "изменения",
            "поправки",
            "статья",
            "федеральный",
            "право"
        ]
        
        # Проверяем, что хотя бы один юридический термин присутствует в результате
        text_content = (result["title"] + " " + result["body"]).lower()
        assert any(term in text_content for term in legal_terms), \
            f"Результат не содержит юридических терминов: {result['title']}"

@pytest.mark.integration
def test_real_search_russian_content():
    """Интеграционный тест поиска русскоязычного контента"""
    search = GoogleSearch(
        query="Новые законы РФ 2024",
        api_key=GOOGLE_API_KEY,
        custom_search_engine_id=GOOGLE_CX_KEY,
        language="ru",
        country="RU"
    )
    
    results = search.search(max_results=10)
    
    # Выводим результаты поиска
    print("\nНайденные результаты по запросу 'Новые законы РФ 2024':")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   Ссылка: {result['link']}")
        print(f"   Описание: {result['body'][:200]}...")
    
    # Проверяем, что получили результаты
    assert len(results) > 0
    
    # Проверяем структуру результатов
    for result in results:
        # Проверяем структуру результата
        assert "title" in result
        assert "link" in result
        assert "body" in result
        
        # Проверяем, что поля не пустые
        assert result["title"].strip()
        assert result["link"].strip()
        assert result["body"].strip()
        
        # Проверяем наличие юридических терминов
        legal_terms = [
            "закон",
            "право",
            "статья",
            "федеральный",
            "кодекс",
            "законодательство",
            "норма",
            "правовой",
            "коап",
            "рф",
            "изменения",
            "административный"
        ]
        
        # Проверяем, что хотя бы один юридический термин присутствует в результате
        text_content = (result["title"] + " " + result["body"]).lower()
        assert any(term in text_content for term in legal_terms), \
            f"Результат не содержит юридических терминов: {result['title']}"

# ---------- Здесь можно добавить другие тесты для проекта ---------- 