"""
Модуль для отслеживания и отображения статусов багов в UART dashboard.
Не зависит от основного dashboard.py, может использоваться отдельно.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path


class BugSeverity(Enum):
    """Уровень серьезности бага."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BugStatus(Enum):
    """Статус бага."""
    FOUND = "found"
    NOT_FOUND = "not_found"
    PARTIALLY_FOUND = "partially_found"


@dataclass
class Bug:
    """Класс для описания бага."""
    id: int
    name: str
    description: str
    severity: BugSeverity
    expected_behavior: str
    actual_behavior: str
    affected_addresses: List[int]
    count: int = 0
    details: List[str] = None
    
    def to_dict(self) -> Dict:
        """Конвертирует баг в словарь."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'severity': self.severity.value,
            'expected_behavior': self.expected_behavior,
            'actual_behavior': self.actual_behavior,
            'affected_addresses': self.affected_addresses,
            'count': self.count,
            'details': self.details or []
        }


class BugTracker:
    """
    Класс для отслеживания статусов багов.
    Может работать как с результатами тестов, так и с файлами отчетов.
    """
    
    def __init__(self, test_results: Optional[Dict] = None):
        """
        Инициализация трекера багов.
        
        Args:
            test_results: Результаты тестов из run_bug_test
        """
        self.test_results = test_results or {}
        self.bugs = self._initialize_bugs()
        
    def _initialize_bugs(self) -> List[Bug]:
        """Инициализирует список всех возможных багов."""
        return [
            Bug(
                id=1,
                name="Sticky Data",
                description="Данные не обновляются при повторной записи",
                severity=BugSeverity.HIGH,
                expected_behavior="После записи 0xAA и 0x55 чтение должно вернуть 0x55",
                actual_behavior="Чтение возвращает предыдущее значение (залипает)",
                affected_addresses=[0x10, 0x14, 0x18, 0x1C, 0x20, 0x24]
            ),
            Bug(
                id=2,
                name="Deadlock",
                description="Отсутствие ACK при чтении после записи",
                severity=BugSeverity.CRITICAL,
                expected_behavior="Все операции чтения должны возвращать ACK=True",
                actual_behavior="Некоторые операции чтения возвращают ACK=False",
                affected_addresses=[0x00, 0x04, 0x08, 0x0C, 0x10, 0x14, 0x18, 0x1C, 0x20, 0x24]
            ),
            Bug(
                id=3,
                name="Overflow Glitch",
                description="64-битные данные обрезаются некорректно",
                severity=BugSeverity.MEDIUM,
                expected_behavior="Данные должны обрезаться до младших 32 бит (0x89ABCDEF)",
                actual_behavior="Данные XOR-ятся с 0xDEAD перед обрезкой",
                affected_addresses=[0x00, 0x04, 0x08, 0x0C, 0x10, 0x14, 0x18, 0x1C, 0x20, 0x24]
            ),
            Bug(
                id=4,
                name="Register Bits Access",
                description="Недоступные биты регистров изменяются при записи",
                severity=BugSeverity.MEDIUM,
                expected_behavior="Недоступные биты должны сохранять предыдущее значение",
                actual_behavior="Все биты изменяются при записи 0xFF",
                affected_addresses=[0x00, 0x0C]
            )
        ]
    
    def update_from_test_results(self, test_results: Dict) -> None:
        """Обновляет статусы багов из результатов тестов."""
        self.test_results = test_results
        
        for bug in self.bugs:
            key = f'bug{bug.id}'
            if key in test_results:
                anomalies = test_results[key].get('anomalies', [])
                for anomaly in anomalies:
                    if anomaly['bug_id'] == bug.id:
                        bug.count = anomaly['count']
                        bug.details = anomaly.get('details', [])
    
    def get_bug_status(self, bug_id: int) -> Dict:
        """Возвращает статус конкретного бага."""
        for bug in self.bugs:
            if bug.id == bug_id:
                return {
                    'found': bug.count > 0,
                    'count': bug.count,
                    'details': bug.details or [],
                    'bug': bug,
                    'status': BugStatus.FOUND if bug.count > 0 else BugStatus.NOT_FOUND
                }
        return {'found': False, 'count': 0, 'details': [], 'status': BugStatus.NOT_FOUND}
    
    def get_all_statuses(self) -> List[Dict]:
        """Возвращает статусы всех багов."""
        return [self.get_bug_status(i) for i in range(1, 5)]
    
    def get_summary(self) -> Dict:
        """Возвращает сводку по всем багам."""
        statuses = self.get_all_statuses()
        found = [s for s in statuses if s['found']]
        
        return {
            'total_bugs': len(self.bugs),
            'found_bugs': len(found),
            'found_count': len(found),
            'total_violations': sum(s['count'] for s in statuses),
            'bugs_found': found,
            'bugs_not_found': [s for s in statuses if not s['found']]
        }
    
    def get_sticky_bug_status(self) -> Dict:
        """Возвращает статус sticky бага (Баг #1)."""
        return self.get_bug_status(1)
    
    def get_deadlock_bug_status(self) -> Dict:
        """Возвращает статус deadlock бага (Баг #2)."""
        return self.get_bug_status(2)
    
    def get_overflow_bug_status(self) -> Dict:
        """Возвращает статус overflow glitch бага (Баг #3)."""
        return self.get_bug_status(3)
    
    def get_register_bits_bug_status(self) -> Dict:
        """Возвращает статус register bits бага (Баг #4)."""
        return self.get_bug_status(4)
    
    def get_affected_addresses(self, bug_id: int) -> List[int]:
        """Возвращает адреса, затронутые конкретным багом."""
        for bug in self.bugs:
            if bug.id == bug_id:
                return bug.affected_addresses
        return []
    
    def to_json(self, filepath: Path) -> None:
        """Сохраняет статусы багов в JSON файл."""
        data = {
            'summary': self.get_summary(),
            'bugs': [bug.to_dict() for bug in self.bugs],
            'statuses': self.get_all_statuses()
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, filepath: Path) -> 'BugTracker':
        """Загружает статусы багов из JSON файла."""
        tracker = cls()
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Здесь можно восстановить состояние
        return tracker


# Функции для удобного использования в Streamlit
def create_bug_display(bug_status: Dict) -> str:
    """Создает строку для отображения бага в Streamlit."""
    bug = bug_status['bug']
    emoji = "❌" if bug_status['found'] else "✅"
    return f"{emoji} Баг #{bug.id}: {bug.name} - {bug_status['status'].value}"


def get_bug_color(bug_status: Dict) -> str:
    """Возвращает цвет для отображения бага."""
    if not bug_status['found']:
        return "normal"
    if bug_status['count'] > 10:
        return "red"
    if bug_status['count'] > 5:
        return "orange"
    return "yellow"


# Пример использования в отдельном файле
if __name__ == "__main__":
    # Пример использования без Streamlit
    tracker = BugTracker()
    
    # Симуляция результатов тестов
    mock_results = {
        'bug1': {
            'anomalies': [{
                'bug_id': 1,
                'count': 6,
                'addresses': ['0x10', '0x14', '0x18', '0x1C', '0x20', '0x24']
            }]
        },
        'bug2': {
            'anomalies': [{
                'bug_id': 2,
                'count': 60,
                'details': ['DEADLOCK write 0x03 → read 0x04']
            }]
        },
        'bug3': {
            'anomalies': [{
                'bug_id': 3,
                'count': 10,
                'addresses': ['0x00', '0x04', '0x08', '0x0C', '0x10', '0x14', '0x18', '0x1C', '0x20', '0x24']
            }]
        },
        'bug4': {
            'anomalies': [{
                'bug_id': 4,
                'count': 1
            }]
        }
    }
    
    tracker.update_from_test_results(mock_results)
    
    # Получение статусов
    print("=== СТАТУСЫ БАГОВ ===")
    for status in tracker.get_all_statuses():
        print(create_bug_display(status))
        if status['found']:
            print(f"  Нарушений: {status['count']}")
    
    print("\n=== СВОДКА ===")
    summary = tracker.get_summary()
    print(f"Найдено багов: {summary['found_bugs']}/4")
    print(f"Всего нарушений: {summary['total_violations']}")
    
    # Сохранение в JSON
    tracker.to_json(Path("bug_status.json"))
    print("\nСтатусы сохранены в bug_status.json")