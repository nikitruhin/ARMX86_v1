from riscv_reg_block import reg_access
import pytest

uart_addrs = [0x00, 0x04, 0x08, 0x0C, 0x10, 0x14, 0x18, 0x1C, 0x20, 0x24]


@pytest.mark.bug
def test_64bit_truncation():
    """
    Проверяет, что 64-битные данные обрезаются до младших 32 бит
    """
    test_val = 0x0123456789ABCDEF
    expected = test_val & 0xFFFFFFFF  # 0x89ABCDEF

    glitch_count = 0
    glitch_details = []

    for addr in uart_addrs:
        orig = reg_access(addr, 0, 'read')['reg_value']

        reg_access(addr, test_val, 'write')
        read_val = reg_access(addr, 0, 'read')['reg_value']

        if read_val != expected:
            glitch_details.append({
                'addr': addr,
                'written': f"0x{test_val:016X}",
                'read': f"0x{read_val:08X}",
                'expected': f"0x{expected:08X}"
            })
            print(f"GLITCH addr=0x{addr:02X} read=0x{read_val:08X} expected=0x{expected:08X}")
            glitch_count += 1

        reg_access(addr, orig, 'write')

    print(f"\nНайдено glitch: {glitch_count}")
    if glitch_count > 0:
        print("Проблемные адреса:", [f"0x{addr:02X}" for addr in set(d['addr'] for d in glitch_details)])

    assert glitch_count == 0, f"БАГ: 64-bit glitch в {glitch_count} регистрах"
