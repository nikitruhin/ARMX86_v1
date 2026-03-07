from riscv_reg_block import reg_access
import pytest

live_registers = [0x00, 0x04, 0x08, 0x0C, 0x10, 0x14, 0x18, 0x1C, 0x20, 0x24]


@pytest.mark.bug
def test_deadlock_hunt():
    deadlocks_found = 0
    deadlock_pairs = []

    for write_addr in live_registers:
        reg_access(write_addr, 0xAAAAAAAA, 'write')

        for read_addr in live_registers:
            result = reg_access(read_addr, 0, 'read')
            if not result['ack']:
                print(f"DEADLOCK write 0x{write_addr:02X} → read 0x{read_addr:02X} NO ACK")
                deadlock_pairs.append((write_addr, read_addr))
                deadlocks_found += 1

    print(f"\nНайдено deadlock'ов: {deadlocks_found}")
    write_addrs = set([w for w, _ in deadlock_pairs])
    read_addrs = set([r for _, r in deadlock_pairs])
    print(f"Проблемные адреса записи: {[f'0x{x:02X}' for x in write_addrs]}")
    print(f"Проблемные адреса чтения: {[f'0x{x:02X}' for x in read_addrs]}")
