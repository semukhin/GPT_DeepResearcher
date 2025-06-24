#!/usr/bin/env python3
"""
Тестовый скрипт для проверки качества исследований GPT-Researcher
Специально адаптирован для юридических тем и интеграции с LawGPT
"""

import asyncio
import time
import json
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
from dotenv import load_dotenv
import re
load_dotenv()

# Создаем директорию для результатов тестов
test_results_dir = Path("test_results")
test_results_dir.mkdir(exist_ok=True)

class GPTResearcherQualityTester:
    """Класс для тестирования качества исследований GPT-Researcher"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        self.report_counter = 1
        self.outputs_dir = Path("outputs")
        self.outputs_dir.mkdir(exist_ok=True)
        
    def _sanitize_filename(self, text: str) -> str:
        # Удаляет все символы, кроме букв, цифр, пробелов и подчёркиваний
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'\s+', '_', text)
        return text[:50]  # Ограничиваем длину

    def save_report(self, report: str, query: str, report_type: str):
        print(f"[DEBUG] Длина отчёта перед сохранением: {len(report)} символов")
        filename = f"report_{self.report_counter}_{self._sanitize_filename(query)}_{report_type}.md"
        filepath = self.outputs_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"📝 Полный отчёт сохранён: {filepath}")
        self.report_counter += 1

    async def test_basic_research(self, query: str, report_type: str = "research_report") -> Dict[str, Any]:
        """Тестирует базовое исследование"""
        try:
            from gpt_researcher import GPTResearcher
            from gpt_researcher.utils.enum import Tone
            
            print(f"\n🔍 Тестируем: {query}")
            print(f"📋 Тип отчета: {report_type}")
            
            start_time = time.time()
            # Усиленный промпт для русского языка
            system_prompt = (
                "ВАЖНО: Все ответы, пояснения, выводы и ссылки должны быть только на русском языке. "
                "Используй только российские источники, законы и судебную практику, если это применимо."
            )
            ru_query = f"{query}\n\nПожалуйста, сгенерируй отчёт на русском языке."
            researcher = GPTResearcher(
                query=ru_query,
                report_type=report_type,
                tone=Tone.Objective,
                headers={"system": system_prompt}
            )
            # Явно выбираем модель Gemini 2.5 Flash (google_genai:gemini-2.5-flash)
            researcher.cfg.smart_llm_provider = "google_genai"
            researcher.cfg.smart_llm_model = "gemini-2.5-flash"  # Gemini 2.5 Flash
            # Проводим исследование
            context = await researcher.conduct_research()
            # Генерируем отчёт
            report = await researcher.write_report()
            # Сохраняем полный отчёт
            self.save_report(report, query, report_type)
            end_time = time.time()
            duration = end_time - start_time
            
            # Собираем метрики
            sources = researcher.get_research_sources()
            visited_urls = researcher.get_source_urls()
            costs = researcher.get_costs()
            
            result = {
                "query": query,
                "report_type": report_type,
                "duration_seconds": duration,
                "context_length": len(context),
                "report_length": len(report),
                "sources_count": len(sources),
                "visited_urls_count": len(visited_urls),
                "costs": costs,
                "report_preview": report[:500] + "..." if len(report) > 500 else report,
                "sources": sources[:5],  # Первые 5 источников
                "visited_urls": list(visited_urls)[:5],  # Первые 5 URL
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
            print(f"✅ Завершено за {duration:.2f} секунд")
            print(f"📊 Источников: {len(sources)}, URL: {len(visited_urls)}")
            print(f"💰 Стоимость: ${costs:.4f}")
            print(f"📝 Длина отчета: {len(report)} символов")
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")
            return {
                "query": query,
                "report_type": report_type,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "success": False
            }
    
    async def test_deep_research(self, query: str) -> Dict[str, Any]:
        """Тестирует глубокое исследование"""
        try:
            from gpt_researcher import GPTResearcher
            from gpt_researcher.utils.enum import Tone
            
            print(f"\n🔬 Тестируем глубокое исследование: {query}")
            
            start_time = time.time()
            system_prompt = (
                "ВАЖНО: Все ответы, пояснения, выводы и ссылки должны быть только на русском языке. "
                "Используй только российские источники, законы и судебную практику, если это применимо."
            )
            ru_query = f"{query}\n\nПожалуйста, сгенерируй отчёт на русском языке."
            researcher = GPTResearcher(
                query=ru_query,
                report_type="deep",  # Режим глубокого исследования
                tone=Tone.Objective,
                headers={"system": system_prompt}
            )
            # Явно выбираем модель Gemini 2.5 Flash (google_genai:gemini-2.5-flash)
            researcher.cfg.smart_llm_provider = "google_genai"
            researcher.cfg.smart_llm_model = "gemini-2.5-flash"  # Gemini 2.5 Flash
            # Настраиваем параметры глубокого исследования
            researcher.cfg.deep_research_breadth = 3
            researcher.cfg.deep_research_depth = 2
            researcher.cfg.deep_research_concurrency = 2
            
            # Логируем промежуточные данные для отладки
            def on_progress(progress):
                print(f"📈 Прогресс: Глубина {progress.current_depth}/{progress.total_depth}, "
                      f"Ширина {progress.current_breadth}/{progress.total_breadth}, "
                      f"Запросы {progress.completed_queries}/{progress.total_queries}")
                if progress.current_query:
                    print(f"🔍 Текущий запрос: {progress.current_query}")
            
            # Проводим глубокое исследование
            context = await researcher.conduct_research(on_progress=on_progress)
            print(f"[DEBUG] Context for deep research: {context}")
            
            # Генерируем отчёт
            report = await researcher.write_report()
            print(f"[DEBUG] Report for deep research: {report[:500]}")
            
            # Сохраняем полный отчёт
            self.save_report(report, query, "deep_research")
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Собираем метрики
            sources = researcher.get_research_sources()
            visited_urls = researcher.get_source_urls()
            costs = researcher.get_costs()
            
            result = {
                "query": query,
                "report_type": "deep_research",
                "duration_seconds": duration,
                "context_length": len(context),
                "report_length": len(report),
                "sources_count": len(sources),
                "visited_urls_count": len(visited_urls),
                "costs": costs,
                "report_preview": report[:500] + "..." if len(report) > 500 else report,
                "sources": sources[:5],
                "visited_urls": list(visited_urls)[:5],
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
            print(f"✅ Глубокое исследование завершено за {duration:.2f} секунд")
            print(f"📊 Источников: {len(sources)}, URL: {len(visited_urls)}")
            print(f"💰 Стоимость: ${costs:.4f}")
            
            return result
            
        except Exception as e:
            print(f"❌ Ошибка в глубоком исследовании: {str(e)}")
            return {
                "query": query,
                "report_type": "deep_research",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "success": False
            }
    
    async def run_legal_tests(self):
        """Запускает тесты с юридическими темами"""
        print("🏛️ Запуск тестов качества GPT-Researcher для юридических тем")
        print("=" * 80)
        
        # Тестовые юридические запросы
        legal_queries = [
            "Переквалификация оснований расторжения договора подряда с 715 на 717 статью Гражданского кодекса Российской Федерации"
        ]
        
        # Тестируем базовые исследования
        print("\n📋 ТЕСТ 1: Базовые исследования")
        print("-" * 40)
        
        for query in legal_queries[:2]:  # Тестируем первые 2 запроса
            result = await self.test_basic_research(query, "research_report")
            self.results.append(result)
            await asyncio.sleep(2)  # Пауза между запросами
        
        # Тестируем детальные отчеты
        print("\n📋 ТЕСТ 2: Детальные отчеты")
        print("-" * 40)
        
        for query in legal_queries[2:3]:  # Тестируем 3-й запрос
            result = await self.test_basic_research(query, "detailed_report")
            self.results.append(result)
            await asyncio.sleep(2)
        
        # Тестируем глубокое исследование
        print("\n📋 ТЕСТ 3: Глубокое исследование")
        print("-" * 40)
        
        deep_query = legal_queries[0]  # Используем первый запрос для глубокого исследования
        result = await self.test_deep_research(deep_query)
        self.results.append(result)
    
    async def run_general_tests(self):
        """Запускает общие тесты для сравнения"""
        print("\n🌐 ТЕСТ 4: Общие темы для сравнения")
        print("-" * 40)
        
        general_queries = [
            "Последние достижения в области искусственного интеллекта",
            "Климатические изменения и их влияние на экономику"
        ]
        
        for query in general_queries:
            result = await self.test_basic_research(query, "research_report")
            self.results.append(result)
            await asyncio.sleep(2)
    
    def save_results(self):
        """Сохраняет результаты тестов"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = test_results_dir / f"gpt_researcher_test_results_{timestamp}.json"
        
        # Добавляем общую статистику
        summary = {
            "total_tests": len(self.results),
            "successful_tests": len([r for r in self.results if r.get("success", False)]),
            "failed_tests": len([r for r in self.results if not r.get("success", False)]),
            "total_duration": sum([r.get("duration_seconds", 0) for r in self.results if r.get("success", False)]),
            "total_costs": sum([r.get("costs", 0) for r in self.results if r.get("success", False)]),
            "average_report_length": sum([r.get("report_length", 0) for r in self.results if r.get("success", False)]) / max(1, len([r for r in self.results if r.get("success", False)])),
            "test_timestamp": datetime.now().isoformat()
        }
        
        output = {
            "summary": summary,
            "results": self.results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Результаты сохранены в: {filename}")
        
        # Выводим краткую статистику
        print("\n📊 КРАТКАЯ СТАТИСТИКА:")
        print(f"✅ Успешных тестов: {summary['successful_tests']}/{summary['total_tests']}")
        print(f"⏱️ Общее время: {summary['total_duration']:.2f} секунд")
        print(f"💰 Общая стоимость: ${summary['total_costs']:.4f}")
        print(f"📝 Средняя длина отчета: {summary['average_report_length']:.0f} символов")
        
        return filename

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования качества GPT-Researcher")
    print("=" * 80)
    
    tester = GPTResearcherQualityTester()
    
    try:
        # Запускаем юридические тесты
        await tester.run_legal_tests()
        
        # Запускаем общие тесты
        await tester.run_general_tests()
        
        # Сохраняем результаты
        results_file = tester.save_results()
        
        print(f"\n🎉 Тестирование завершено! Результаты в: {results_file}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка во время тестирования: {str(e)}")
        # Сохраняем частичные результаты
        if tester.results:
            tester.save_results()

if __name__ == "__main__":
    asyncio.run(main()) 