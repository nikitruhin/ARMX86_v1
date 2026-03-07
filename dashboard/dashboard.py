from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Dict, List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent

ARTIFACT_DIR = PROJECT_ROOT / "artifacts"
BUGS_DIR = PROJECT_ROOT / "bugs"

COVERAGE_JSON_PATH = PROJECT_ROOT / "coverage.json"

ARTIFACT_DIR.mkdir(exist_ok=True)

UART_ADDRESSES = [0x00, 0x04, 0x08, 0x0C, 0x10, 0x14, 0x18, 0x1C, 0x20, 0x24]

# ----------------------------------------------------------------------
# Запуск тестов
# ----------------------------------------------------------------------
def run_bug_test(test_name: str) -> Dict:
    """Запускает конкретный тест и возвращает результаты"""
    test_file = BUGS_DIR / f"{test_name}.py"

    if not test_file.exists():
        return {
            'output': f"Файл не найден: {test_file}",
            'passed': False,
            'failed': True,
            'anomalies': []
        }

    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-s"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )

    output = result.stdout + result.stderr

    test_result = {
        'output': output,
        'passed': result.returncode == 0,
        'failed': result.returncode != 0,
        'returncode': result.returncode,
        'anomalies': []
    }

    # Баг 1: Stale Data
    stale_matches = re.findall(r'STALE DATA addr=(0x[0-9A-F]+).*', output)
    if stale_matches:
        test_result['anomalies'].append({
            'bug_id': 1,
            'name': 'Stale Data',
            'type': 'stale_data',
            'count': len(stale_matches),
            'addresses': stale_matches,
            'description': 'Данные не обновляются при повторной записи'
        })

    # Баг 2: Deadlock
    deadlock_matches = re.findall(r'DEADLOCK.*', output)
    if deadlock_matches:
        test_result['anomalies'].append({
            'bug_id': 2,
            'name': 'Deadlock',
            'type': 'deadlock',
            'count': len(deadlock_matches),
            'details': deadlock_matches,
            'description': 'Отсутствие ACK при чтении после записи'
        })

    # Баг 3: Overflow Glitch
    glitch_matches = re.findall(r'GLITCH addr=(0x[0-9A-F]+).*', output)
    glitch_details = re.findall(r'(GLITCH.*)', output)
    if glitch_matches:
        addresses = list(set(glitch_matches))
        test_result['anomalies'].append({
            'bug_id': 3,
            'name': 'Overflow Glitch',
            'type': 'glitch',
            'count': len(glitch_matches),
            'addresses': sorted(addresses),
            'details': glitch_details,
            'description': '64-битные данные обрезаются некорректно'
        })

    # Баг 4: Register bits access
    if ("БАГ #4.1" in output or "БАГ #4.2" in output or
        "изменился с 0x8B на 0xFF" in output or
        "139 не равно 255" in output):
        test_result['anomalies'].append({
            'bug_id': 4,
            'name': 'Register Bits Access',
            'type': 'reg_bits',
            'count': 1,
            'description': 'Недоступные биты регистров изменяются при записи'
        })

    return test_result


def run_address_map() -> Dict:
    """Запускает прозвонку адресов и возвращает карту памяти"""
    test_file = BUGS_DIR / "bug_address_map.py"

    if not test_file.exists():
        return {
            'alive': [],
            'dead': [],
            'expected': UART_ADDRESSES,
            'missing': [],
            'extra': [],
            'output': 'Файл bug_address_map.py не найден'
        }

    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-s"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )

    output = result.stdout + result.stderr

    alive = []
    for line in output.split('\n'):
        if "Address" in line and "alive" in line:
            match = re.search(r'Address (0x[0-9A-F]+)', line, re.IGNORECASE)
            if match:
                try:
                    addr = int(match.group(1), 16)
                    alive.append(addr)
                except:
                    pass

    alive = sorted(set(alive))
    dead = [a for a in UART_ADDRESSES if a not in alive]

    alive_set = set(alive)
    expected_set = set(UART_ADDRESSES)

    missing = list(expected_set - alive_set)
    extra = list(alive_set - expected_set)

    return {
        'alive': alive,
        'dead': dead,
        'expected': UART_ADDRESSES,
        'missing': sorted(missing),
        'extra': sorted(extra),
        'output': output
    }


def run_coverage() -> Dict:
    """Читает результаты coverage из JSON файла"""
    coverage_data = {
        'percent': 0.0,
        'covered': 0,
        'total': 0,
        'missing': 0,
        'files': {}
    }

    if COVERAGE_JSON_PATH.exists():
        try:
            with open(COVERAGE_JSON_PATH, 'r') as f:
                data = json.load(f)

            totals = data.get('totals', {})
            coverage_data['percent'] = totals.get('percent_covered', 0.0)
            coverage_data['covered'] = totals.get('covered_lines', 0)
            coverage_data['total'] = totals.get('num_statements', 0)
            coverage_data['missing'] = totals.get('missing_lines', 0)

            for file_path, file_data in data.get('files', {}).items():
                if 'riscv_reg_block' in file_path:
                    summary = file_data.get('summary', {})
                    coverage_data['files'][file_path] = {
                        'percent': summary.get('percent_covered', 0.0),
                        'covered': summary.get('covered_lines', 0),
                        'total': summary.get('num_statements', 0),
                        'missing': summary.get('missing_lines', 0),
                        'name': Path(file_path).name
                    }
        except Exception as e:
            coverage_data['error'] = str(e)

    return coverage_data


def _build_coverage_gauge(coverage_data: Dict) -> go.Figure:
    """Строит индикатор покрытия"""
    target = 94.0
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=coverage_data['percent'],
        delta={'reference': target},
        title={'text': f"Покрытие riscv_reg_block<br>Цель: {target}%"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#1D3557"},
            'steps': [
                {'range': [0, 50], 'color': '#FF6B6B'},
                {'range': [50, 75], 'color': '#FFD93D'},
                {'range': [75, 90], 'color': '#6BCB77'},
                {'range': [90, 100], 'color': '#2E8B57'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': target
            }
        }
    ))
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=60, b=20))
    return fig


def _create_error_heatmap(test_results: Dict) -> go.Figure:
    """
    Создает тепловую карту количества ошибок по каждому адресу
    """
    # Словарь для подсчета ошибок по каждому адресу
    error_count = {addr: 0 for addr in UART_ADDRESSES}
    
    # Собираем ошибки из всех тестов
    for test_name, result in test_results.items():
        anomalies = result.get('anomalies', [])
        for anomaly in anomalies:
            # Баг 1: Stale Data
            if anomaly['type'] == 'stale_data' and 'addresses' in anomaly:
                for addr_str in anomaly['addresses']:
                    try:
                        addr = int(addr_str, 16)
                        if addr in error_count:
                            error_count[addr] += 1
                    except:
                        pass
            
            # Баг 2: Deadlock
            if anomaly['type'] == 'deadlock' and 'details' in anomaly:
                for detail in anomaly['details']:
                    addrs = re.findall(r'0x([0-9A-F]+)', detail)
                    for addr_str in addrs:
                        try:
                            addr = int(addr_str, 16)
                            if addr in error_count:
                                error_count[addr] += 1
                        except:
                            pass
            
            # Баг 3: Overflow Glitch
            if anomaly['type'] == 'glitch' and 'addresses' in anomaly:
                for addr_str in anomaly['addresses']:
                    try:
                        addr = int(addr_str, 16)
                        if addr in error_count:
                            error_count[addr] += 1
                    except:
                        pass
            
            # Баг 4: Register Bits Access
            if anomaly['type'] == 'reg_bits':
                error_count[0x00] += 1
                error_count[0x0C] += 1
    
    # Создаем матрицу 2x5 для отображения
    matrix = [[0 for _ in range(5)] for _ in range(2)]
    hover_text = [["" for _ in range(5)] for _ in range(2)]
    
    # Заполняем матрицу:
    # Верхняя строка (row=0) - адреса 0x14, 0x18, 0x1C, 0x20, 0x24
    # Нижняя строка (row=1) - адреса 0x00, 0x04, 0x08, 0x0C, 0x10
    for idx, addr in enumerate(UART_ADDRESSES):
        if idx < 5:  # адреса 0x00, 0x04, 0x08, 0x0C, 0x10
            row = 1  # нижняя строка
            col = idx
        else:  # адреса 0x14, 0x18, 0x1C, 0x20, 0x24
            row = 0  # верхняя строка
            col = idx - 5
        matrix[row][col] = error_count[addr]
        hover_text[row][col] = f"Адрес 0x{addr:02X}<br>Ошибок: {error_count[addr]}"
    
    # Определяем максимальное количество ошибок
    max_errors = max(error_count.values()) if error_count.values() else 1
    if max_errors == 0:
        max_errors = 1
    
    # Создаем тепловую карту
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=["0", "1", "2", "3", "4"],
        y=["Адреса 0x14-0x24 (верхняя строка)", "Адреса 0x00-0x10 (нижняя строка)"],
        colorscale='Reds',
        zmin=0,
        zmax=max_errors,
        showscale=True,
        colorbar=dict(
            title="Количество ошибок"
        ),
        hovertemplate='%{text}<extra></extra>',
        text=hover_text
    ))
    
    # Добавляем подписи адресов
    annotations = []
    for idx, addr in enumerate(UART_ADDRESSES):
        if idx < 5:
            row = 1
            col = idx
        else:
            row = 0
            col = idx - 5
        annotations.append(dict(
            x=col,
            y=row,
            text=f"0x{addr:02X}",
            showarrow=False,
            font=dict(
                color='white' if matrix[row][col] > max_errors/2 else 'black',
                size=12
            )
        ))
    
    fig.update_layout(
        title={
            'text': "Распределение ошибок по адресам",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Номер колонки",
        yaxis_title="",
        width=700,
        height=350,
        annotations=annotations,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig


# ----------------------------------------------------------------------
# Основное приложение
# ----------------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title="UART Verification Dashboard", layout="wide")

    st.title("UART BlackBox Verification Dashboard")
    st.caption("Результаты тестирования UART контроллера")

    if 'test_results' not in st.session_state:
        st.session_state.test_results = {}
    if 'address_map' not in st.session_state:
        st.session_state.address_map = None
    if 'coverage_data' not in st.session_state:
        st.session_state.coverage_data = None

    with st.sidebar:
        st.header("Управление")

        if st.button("ЗАПУСТИТЬ ВСЕ ТЕСТЫ", type="primary"):
            with st.spinner("Запуск тестов..."):
                st.session_state.test_results = {
                    'bug1': run_bug_test('bug1_test'),
                    'bug2': run_bug_test('bug2_test'),
                    'bug3': run_bug_test('bug3_test'),
                    'bug4': run_bug_test('bug4_test')
                }
            st.rerun()

        if st.button("ПРОЗВОНИТЬ АДРЕСА"):
            with st.spinner("Прозвонка адресного пространства..."):
                st.session_state.address_map = run_address_map()
            st.rerun()

        if st.button("ПОКАЗАТЬ COVERAGE"):
            with st.spinner("Чтение данных покрытия..."):
                st.session_state.coverage_data = run_coverage()
            st.rerun()

        st.divider()

        if st.session_state.test_results:
            all_anomalies = []
            for r in st.session_state.test_results.values():
                all_anomalies.extend(r.get('anomalies', []))
            st.metric("Типов багов", len(all_anomalies))
            st.metric("Всего нарушений", sum(a['count'] for a in all_anomalies))

        if st.session_state.address_map:
            a = st.session_state.address_map
            st.metric("Живые адреса", len(a['alive']))
            st.metric("Мертвые адреса", len(a['dead']))

        if st.session_state.coverage_data:
            c = st.session_state.coverage_data
            st.metric("Покрытие", f"{c['percent']:.1f}%")

    if (not st.session_state.test_results and
        not st.session_state.address_map and
        not st.session_state.coverage_data):
        st.info("Нажмите кнопки в боковой панели для запуска тестов или анализа")
        return

    tab_bugs, tab_address, tab_coverage = st.tabs([
        "Поиск багов", "Адресное пространство", "Покрытие кода"
    ])

    # ========== Вкладка "Поиск багов" ==========
    with tab_bugs:
        if st.session_state.test_results:
            results = st.session_state.test_results
            
            # Тепловая карта ошибок
            st.subheader("Распределение ошибок по адресам")
            st.plotly_chart(_create_error_heatmap(results), use_container_width=True)
            
            st.divider()

            # Сводная таблица
            st.subheader("Сводка результатов тестов")
            summary = []
            for bug_id in range(1, 5):
                key = f'bug{bug_id}'
                if key in results:
                    anom = results[key].get('anomalies', [])
                    if anom:
                        for a in anom:
                            summary.append({
                                "Баг": f"#{a['bug_id']}",
                                "Название": a['name'],
                                "Нарушений": a['count'],
                                "Статус": "НАЙДЕН"
                            })
                    else:
                        summary.append({
                            "Баг": f"#{bug_id}",
                            "Название": f"Тест {bug_id}",
                            "Нарушений": 0,
                            "Статус": "OK"
                        })

            if summary:
                df_summary = pd.DataFrame(summary)
                st.dataframe(df_summary, use_container_width=True, hide_index=True)

            st.divider()

            # Детали по каждому багу
            st.subheader("Детальное описание багов")
            for bug_id in range(1, 5):
                key = f'bug{bug_id}'
                anom = results.get(key, {}).get('anomalies', [])
                with st.expander(f"Баг #{bug_id}", expanded=bool(anom)):
                    if anom:
                        for a in anom:
                            st.write(f"**{a['name']}**")
                            st.write(a['description'])
                            if 'addresses' in a:
                                addr_list = ', '.join(a['addresses'])
                                st.write(f"Проблемные адреса: {addr_list}")
                            if 'details' in a:
                                st.code('\n'.join(a['details'][:5]))
                    else:
                        st.write("Баг не обнаружен")
        else:
            st.info("Запустите тесты из боковой панели")

    # ========== Вкладка "Адресное пространство" ==========
    with tab_address:
        if st.session_state.address_map:
            addr = st.session_state.address_map

            st.subheader("Результаты прозвонки адресов")

            col1, col2, col3 = st.columns(3)
            col1.metric("Всего адресов", 10)
            col2.metric("Живые адреса", len(addr['alive']))
            col3.metric("Мертвые адреса", len(addr['dead']))

            if addr['missing']:
                st.warning(f"Отсутствуют ожидаемые: {', '.join([hex(a) for a in addr['missing']])}")
            if addr['extra']:
                st.error(f"Лишние живые: {', '.join([hex(a) for a in addr['extra']])}")

            # Таблица со статусами адресов
            st.subheader("Статус каждого адреса")
            
            # Создаем таблицу с цветовой индикацией
            data = []
            for address in UART_ADDRESSES:
                if address in addr['alive']:
                    status = "жив"
                elif address in addr['expected']:
                    status = "ожидаемый"
                else:
                    status = "мертв"
                data.append({
                    "Адрес": f"0x{address:02X}",
                    "Статус": status
                })
            
            df = pd.DataFrame(data)
            
            # Функция для раскрашивания строк
            def color_rows(row):
                if row['Статус'] == "жив":
                    return ['background-color: #c8e6c9'] * len(row)
                elif row['Статус'] == "ожидаемый":
                    return ['background-color: #fff3e0'] * len(row)
                else:
                    return ['background-color: #ffcdd2'] * len(row)
            
            styled_df = df.style.apply(color_rows, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

            with st.expander("Показать полный вывод прозвонки"):
                st.code(addr['output'])
        else:
            st.info("Запустите прозвонку адресов из боковой панели")

    # ========== Вкладка "Покрытие кода" ==========
    with tab_coverage:
        if st.session_state.coverage_data:
            cov = st.session_state.coverage_data

            st.subheader(f"Покрытие кода: {cov['percent']:.1f}%")

            col1, col2 = st.columns([1, 1])
            with col1:
                st.plotly_chart(_build_coverage_gauge(cov), use_container_width=True)
            with col2:
                st.metric("Всего строк кода", cov['total'])
                st.metric("Покрыто тестами", cov['covered'])
                st.metric("Не покрыто", cov['missing'])

                if cov['percent'] >= 94:
                    st.success("Цель по покрытию достигнута (≥94%)")
                else:
                    st.warning(f"До цели {94 - cov['percent']:.1f}%")

            if cov['files']:
                st.subheader("Детализация по файлам")
                df_files = pd.DataFrame([
                    {"Файл": v['name'], "Покрытие": f"{v['percent']:.1f}%"}
                    for v in cov['files'].values()
                ])
                st.dataframe(df_files, use_container_width=True, hide_index=True)

            if COVERAGE_JSON_PATH.exists():
                st.caption(f"Данные из файла: {COVERAGE_JSON_PATH}")
        else:
            st.info("Запустите анализ покрытия из боковой панели")


if __name__ == "__main__":
    main()