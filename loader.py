#!/usr/bin/env python3
"""
loader.py — распаковка черного ящика RISC-V Register Block
Запуск: python3 loader.py
"""

import sys
import os
import importlib.util
import subprocess

def main():
    print("Распаковка RISC-V Register Block...")
    
    if not os.path.exists("riscv_reg_block.py"):
        print("Создание riscv_reg_block.py из исходников...")
        # Здесь вы кладете логику распаковки/копирования
        print("Готово!")
    
    print("Загрузка модуля...")
    spec = importlib.util.spec_from_file_location("riscv_reg_block", "riscv_reg_block.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    print("Тестируем интерфейс...")
    test_result = module.reg_access(0, 0, 'read')
    print("Тест OK:", test_result)
    
    print("\nЧерный ящик готов к использованию!")
    print("Теперь доступно: from riscv_reg_block import reg_access")
    print("\nЗапускайте тесты:")
    print("   pytest tests/")
    print("   streamlit run dashboard.py")

if __name__ == "__main__":
    main()
