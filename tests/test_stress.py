from riscv_reg_block import reg_access
import time

def test_stress_1000():
    """1000 быстрых операций"""
    start = time.time()
    for i in range(1000):
        addr = i % 0x100
        reg_access(addr, i, 'write')
        result = reg_access(addr, 0, 'read')
        assert result['ack'] == 'OK'
    print(f"Stress test: {time.time()-start:.2f}s")