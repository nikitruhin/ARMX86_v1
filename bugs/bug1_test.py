from riscv_reg_block import reg_access
import pytest

live_registers = [0x00, 0x04, 0x08, 0x0C, 0x10, 0x14, 0x18, 0x1C, 0x20, 0x24]


@pytest.mark.bug
def test_stale_data_hunt():
    stale_found = 0
    stale_addresses = []

    for addr in live_registers:
        reg_access(addr, 0xAA, 'write')
        r1 = reg_access(addr, 0, 'read')['reg_value']

        reg_access(addr, 0x55, 'write')
        r2 = reg_access(addr, 0, 'read')['reg_value']

        if r1 == r2:
            print(f"STALE DATA addr=0x{addr:02X} val1=0x{r1:02X} val2=0x{r2:02X}")
            stale_addresses.append(addr)
            stale_found += 1

    print(f"\nНайдено stale data: {stale_found}")
    print(f"Проблемные адреса: {[f'0x{x:02X}' for x in stale_addresses]}")