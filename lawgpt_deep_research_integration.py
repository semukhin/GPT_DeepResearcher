# LawGPT Deep Research Integration Plan
# План интеграции модуля глубокого исследования в LawGPT

"""
Этот файл содержит план интеграции модуля глубокого исследования GPT-Researcher 
в систему LawGPT для расширения возможностей юридического анализа.
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class LegalResearchType(Enum):
    """Типы юридического исследования"""
    LEGISLATION_ANALYSIS = "legislation_analysis"
    CASE_LAW_RESEARCH = "case_law_research"
    CONTRACT_ANALYSIS = "contract_analysis"
    COMPLIANCE_CHECK = "compliance_check"
    LEGAL_OPINION = "legal_opinion"

@dataclass
class LegalResearchConfig:
    """Конфигурация для юридического глубокого исследования"""
    research_type: LegalResearchType
    jurisdiction: str = "russia"  # Российская юрисдикция
    legal_areas: List[str] = None  # Области права (гражданское, уголовное и т.д.)
    depth_levels: int = 3  # Уровни глубины исследования
    breadth_queries: int = 4  # Количество параллельных запросов
    include_case_law: bool = True  # Включить анализ судебной практики
    include_legislation: bool = True  # Включить анализ законодательства
    include_expert_opinions: bool = True  # Включить мнения экспертов

class LawGPTDeepResearchAdapter:
    """
    Адаптер для интеграции модуля глубокого исследования GPT-Researcher в LawGPT
    """
    
    def __init__(self, config: LegalResearchConfig):
        self.config = config
        self.legal_sources = {
            "legislation": [
                "Конституция РФ",
                "Гражданский кодекс РФ", 
                "Уголовный кодекс РФ",
                "Налоговый кодекс РФ",
                "Трудовой кодекс РФ"
            ],
            "case_law": [
                "Постановления Пленума ВС РФ",
                "Определения ВС РФ",
                "Решения арбитражных судов"
            ],
            "expert_sources": [
                "Комментарии к законодательству",
                "Научные статьи по праву",
                "Практические руководства"
            ]
        }
    
    async def generate_legal_queries(self, legal_question: str) -> List[Dict[str, str]]:
        """
        Генерирует юридические поисковые запросы на основе правового вопроса
        """
        queries = []
        
        # Базовые запросы по законодательству
        if self.config.include_legislation:
            queries.extend([
                {
                    "query": f"актуальная редакция законодательства {legal_question}",
                    "researchGoal": "Анализ действующего законодательства",
                    "source_type": "legislation"
                },
                {
                    "query": f"изменения в законодательстве {legal_question} 2024-2025",
                    "researchGoal": "Анализ последних изменений в законодательстве",
                    "source_type": "legislation"
                }
            ])
        
        # Запросы по судебной практике
        if self.config.include_case_law:
            queries.extend([
                {
                    "query": f"судебная практика {legal_question} ВС РФ",
                    "researchGoal": "Анализ позиции Верховного Суда РФ",
                    "source_type": "case_law"
                },
                {
                    "query": f"арбитражная практика {legal_question}",
                    "researchGoal": "Анализ арбитражной практики",
                    "source_type": "case_law"
                }
            ])
        
        # Запросы по экспертным мнениям
        if self.config.include_expert_opinions:
            queries.extend([
                {
                    "query": f"комментарии экспертов {legal_question}",
                    "researchGoal": "Анализ экспертных мнений",
                    "source_type": "expert"
                },
                {
                    "query": f"научные статьи {legal_question} право",
                    "researchGoal": "Анализ научных исследований",
                    "source_type": "expert"
                }
            ])
        
        return queries[:self.config.breadth_queries]
    
    async def conduct_legal_deep_research(self, legal_question: str) -> Dict[str, Any]:
        """
        Проводит глубокое юридическое исследование
        """
        # Импортируем GPTResearcher только при необходимости
        try:
            from gpt_researcher import GPTResearcher
            from gpt_researcher.utils.enum import ReportType, Tone
        except ImportError:
            raise ImportError("GPT-Researcher не установлен. Установите: pip install gpt-researcher")
        
        # Генерируем юридические запросы
        legal_queries = await self.generate_legal_queries(legal_question)
        
        # Инициализируем исследователя с юридической специализацией
        researcher = GPTResearcher(
            query=legal_question,
            report_type="deep",  # Включаем режим глубокого исследования
            tone=Tone.Objective,  # Объективный тон для юридического анализа
            config_path=None,  # Можно указать путь к конфигурации
        )
        
        # Настраиваем параметры глубокого исследования
        researcher.cfg.deep_research_breadth = self.config.breadth_queries
        researcher.cfg.deep_research_depth = self.config.depth_levels
        researcher.cfg.deep_research_concurrency = 2  # Ограничиваем для стабильности
        
        # Проводим исследование
        research_context = await researcher.conduct_research()
        
        # Генерируем юридический отчет
        legal_report = await researcher.write_report()
        
        return {
            "question": legal_question,
            "research_context": research_context,
            "legal_report": legal_report,
            "sources": researcher.get_research_sources(),
            "visited_urls": researcher.get_source_urls(),
            "research_type": self.config.research_type.value
        }

class LawGPTDeepResearchService:
    """
    Сервис для интеграции глубокого исследования в LawGPT
    """
    
    def __init__(self):
        self.adapters = {}
    
    def register_research_type(self, research_type: LegalResearchType, config: LegalResearchConfig):
        """Регистрирует новый тип юридического исследования"""
        self.adapters[research_type] = LawGPTDeepResearchAdapter(config)
    
    async def conduct_research(self, legal_question: str, research_type: LegalResearchType) -> Dict[str, Any]:
        """Проводит юридическое исследование указанного типа"""
        if research_type not in self.adapters:
            raise ValueError(f"Тип исследования {research_type} не зарегистрирован")
        
        adapter = self.adapters[research_type]
        return await adapter.conduct_legal_deep_research(legal_question)

# Пример использования
async def example_usage():
    """Пример использования интеграции"""
    
    # Создаем сервис
    service = LawGPTDeepResearchService()
    
    # Регистрируем типы исследований
    legislation_config = LegalResearchConfig(
        research_type=LegalResearchType.LEGISLATION_ANALYSIS,
        depth_levels=2,
        breadth_queries=3,
        include_case_law=True,
        include_legislation=True,
        include_expert_opinions=False
    )
    
    case_law_config = LegalResearchConfig(
        research_type=LegalResearchType.CASE_LAW_RESEARCH,
        depth_levels=3,
        breadth_queries=4,
        include_case_law=True,
        include_legislation=False,
        include_expert_opinions=True
    )
    
    service.register_research_type(LegalResearchType.LEGISLATION_ANALYSIS, legislation_config)
    service.register_research_type(LegalResearchType.CASE_LAW_RESEARCH, case_law_config)
    
    # Проводим исследование
    legal_question = "Ответственность за нарушение трудового законодательства"
    
    result = await service.conduct_research(
        legal_question, 
        LegalResearchType.LEGISLATION_ANALYSIS
    )
    
    print("Результат юридического исследования:")
    print(f"Вопрос: {result['question']}")
    print(f"Тип исследования: {result['research_type']}")
    print(f"Количество источников: {len(result['sources'])}")
    print(f"Отчет: {result['legal_report'][:500]}...")

if __name__ == "__main__":
    asyncio.run(example_usage()) 