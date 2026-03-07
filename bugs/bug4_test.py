from riscv_reg_block import reg_access
import pytest


@pytest.mark.bug
def test_register_access_bits():
    """
    Проверяет, что недоступные биты регистров не изменяются при записи
    По спецификации:
    - Адрес 0x00: должен корректно хранить 32-битные значения
    - Адрес 0x0C: доступны только биты 0:1, 3, 7
    """
    print("\n" + "=" * 60)
    print("ТЕСТ #4: Проверка доступности битов регистров")
    print("=" * 60)

    # Тест 1: Адрес 0x00 - проверка записи 32-битного значения
    addr1 = 0x00
    test_val1 = 0xFFFFFFFF

    reg_access(addr1, test_val1, 'write')
    result1 = reg_access(addr1, 0, 'read')
    read_val1 = result1['reg_value']

    print(f"\nТест 1: Адрес 0x{addr1:02X}")
    print(f"Записано: 0x{test_val1:08X}")
    print(f"Прочитано: 0x{read_val1:08X}")

    if read_val1 == test_val1:
        print(f"Адрес 0x{addr1:02X} работает корректно")
    else:
        print(f"БАГ: Адрес 0x{addr1:02X} - данные искажены")
        print(f"Ожидалось: 0x{test_val1:08X}, получено: 0x{read_val1:08X}")

    # Тест 2: Адрес 0x0C (LCR) - доступны биты 0:1, 3, 7
    addr2 = 0x0C

    print(f"\nТест 2: Адрес 0x{addr2:02X} (LCR)")
    print(f"  По спецификации доступны биты: 0, 1, 3, 7")

    # Запись только в доступные биты
    test_val2a = 0x8B  # 0x8B = 0b10001011 (биты 0,1,3,7)
    reg_access(addr2, test_val2a, 'write')
    result = reg_access(addr2, 0, 'read')
    state1 = result['reg_value']

    print(f"  Запись 0x{test_val2a:02X} (доступные биты) -> чтение 0x{state1:02X} ({state1})")

    # Попытка записи во все биты
    test_val2b = 0xFF  # 0xFF = 0b11111111
    reg_access(addr2, test_val2b, 'write')
    result = reg_access(addr2, 0, 'read')
    state2 = result['reg_value']

    print(f"  Запись 0x{test_val2b:02X} (все биты) -> чтение 0x{state2:02X} ({state2})")

    if state1 == state2:
        print(f"Адрес 0x{addr2:02X} работает корректно (недоступные биты не изменились)")
    else:
        changed_bits = state1 ^ state2
        print(f" БАГ: Адрес 0x{addr2:02X} - недоступные биты изменились")
        print(f"Было: 0x{state1:02X}, стало: 0x{state2:02X}")
        print(f"Изменились биты: {changed_bits:08b}")

        # Конкретно биты
        for bit in range(8):
            if (changed_bits >> bit) & 1:
                доступность = "доступен" if bit in [0, 1, 3, 7] else "НЕдоступен"
                было = (state1 >> bit) & 1
                стало = (state2 >> bit) & 1
                print(f"      Бит {bit} ({доступность}): {было} -> {стало}")

    print("\n" + "=" * 60)

    assert read_val1 == test_val1, f"БАГ #4.1: Адрес 0x00 - запись 0x{test_val1:X} дала 0x{read_val1:X}"
    assert state1 == state2, f"БАГ #4.2: Адрес 0x0C изменился с 0x{state1:X} на 0x{state2:X}"
