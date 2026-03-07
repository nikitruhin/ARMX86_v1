from riscv_reg_block import reg_access
import pytest

def test_read_zero():
    result = reg_access(0x0000, 0, 'read')
    assert 'reg_value' in result
    assert result['ack'] is not None

def test_write_read():
    reg_access(0x0001, 0xDEADBEEF, 'write')
    result = reg_access(0x0001, 0, 'read')
    assert result['ack'] == 'OK'
