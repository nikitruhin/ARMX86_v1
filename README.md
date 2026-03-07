cat > README.md << 'EOF'
# ARMX86_v1 | RISC-V Register Verifier

## Метрики YADRO (цель: 950/1000 → стажировка)

| Метрика | Цель | Текущий | Команда |
|---------|------|---------|---------|
| pytest coverage | ≥94% | 25% (работаем!) | pytest --cov |
| pylint | ≥8.0/10 | 7.5/10 | pylint *.py tests/ |
| Найденные баги | ≥3 | 0/3 | Авто в тестах |
| Dashboard | Live demo | Да | streamlit run dashboard.py |

Pylint источник: https://github.com/1irs/pylint_practice

## Запуск (пошагово)

```bash
# 1. Перейди в папку
cd ARMX86_v1/

# 2. Установи зависимости
pip install -r requirements.txt

# 3. Распакуй черный ящик (НЕ открывать riscv_reg_block.py!)
python3 loader.py

# 4. Запусти тесты + coverage
pytest tests/ --cov --cov-report=html:coverage_report/ --html=report.html

# 5. Проверка кодстайла YADRO
pylint *.py tests/ dashboard.py  # Цель: ≥8.0/10

# 6. Dashboard с live метриками
streamlit run dashboard.py

