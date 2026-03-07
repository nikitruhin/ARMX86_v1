from riscv_reg_block import reg_access
import pytest

# Для каждого регистра, который можно писать
for addr in [0x00, 0x04, 0x08, 0x0C]:
    print(f'Регистр по адресу {addr}')
    reg_access(addr, 0x00000000, 'write')
    val0 = reg_access(addr, 0, 'read')['reg_value']
    
    
    # Запись всех единиц
    reg_access(addr, 0xFFFFFFFF, 'write')
    val1 = reg_access(addr, 0, 'read')['reg_value']
    
    # Проверяем переход 0→1 для каждого бита
    for bit in range(32):
        bit0 = (val0 >> bit) & 1
        bit1 = (val1 >> bit) & 1
        if bit0 == 0 and bit1 == 1:
            print(f"Бит {bit} переключился 0→1")
    
    # Снова запись 0
    reg_access(addr, 0x00000000, 'write')
    val2 = reg_access(addr, 0, 'read')['reg_value']
    
    # Проверяем переход 1→0
    for bit in range(32):
        bit1 = (val1 >> bit) & 1
        bit2 = (val2 >> bit) & 1
        if bit1 == 1 and bit2 == 0:
            print(f"Бит {bit} переключился 1→0")
