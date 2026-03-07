from riscv_reg_block import reg_access
import pytest


def test_32bit_addressing():
    """
    Прозвонка адресного пространства UART
    Проверяет какие адреса реально отвечают (ACK=True)
    """
    print("\n=== Проверка 32-битной адресации ===")

    # Ожидаемые адреса, согласно спецификации UART
    expected_addrs = [0x00, 0x04, 0x08, 0x0C, 0x10, 0x14, 0x18, 0x1C, 0x20, 0x24]

    found_alive = []  # список живых регистров

    for addr in range(0x00, 0x28, 4):
        read_res = reg_access(addr, 0, 'read')
        write_res = reg_access(addr, 0xBADC0DE, 'write')

        if read_res['ack'] and write_res.get('ack', False):
            found_alive.append(addr)
            print(f"Address 0x{addr:02x} - alive")
        else:
            print(f"Address 0x{addr:02x} - dead")

    print(f"\nНайденные живые адреса: {[hex(a) for a in found_alive]}")
    print(f"Ожидаемые адреса, согласно спецификации: {[hex(a) for a in expected_addrs]}")

    alive_set = set(found_alive)
    expected_set = set(expected_addrs)

    missing = expected_set - alive_set
    if missing:
        print(f"Отсутствуют ожидаемые адреса: {[hex(a) for a in missing]}")

    extra = alive_set - expected_set
    if extra:
        print(f"Лишние живые адреса: {[hex(a) for a in extra]}")

    assert len(extra) == 0, "Найдены регистры с неправильной адресацией"

    # Возвращаем данные (pytest их не использует, но для dashboard пригодятся)
    return {
        'alive': found_alive,
        'dead': [a for a in range(0x00, 0x28, 4) if a not in found_alive],
        'expected': expected_addrs,
        'missing': list(missing),
        'extra': list(extra)
    }
