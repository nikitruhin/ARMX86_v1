#!/usr/bin/env python3
"""
Скрипт для извлечения pylint score из лога
"""

import re
import sys
from pathlib import Path

def get_pylint_score(log_file: str = "pylint_report.txt") -> float:
    """
    Читает файл с отчетом pylint и извлекает оценку
    """
    log_path = Path(log_file)
    
    if not log_path.exists():
        print(f"Файл {log_file} не найден")
        return 0.0
    
    try:
        content = log_path.read_text(encoding="utf-8")
        
        patterns = [
            r'rated at (\d+\.\d+)/10',
            r'Your code has been rated at (\d+\.\d+)/10',
            r'rated\s+at\s+([0-9]+(?:\.[0-9]+)?)\/10'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return float(match.group(1))
        
        # Альтернативный поиск
        lines = content.split('\n')
        for line in lines:
            if 'rated' in line and '/10' in line:
                numbers = re.findall(r'(\d+\.?\d*)/10', line)
                if numbers:
                    return float(numbers[0])
    
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
    
    return 0.0

if __name__ == "__main__":
    score = get_pylint_score()
    print(f"Pylint score: {score:.2f}/10")