# Баг-репорт RISC-V Register Block

| # | Тип бага | Триггер | Статус |
|---|----------|---------|--------|
| 1 | Stale data | read/write → read | search |
| 2 | Deadlock | write(addr1)→read(addr2) | search |
| 3 | Data glitch | bus_width=64 | search |
