text
# Спецификация регистров UART-контроллера

## Общее описание
UART-контроллер для асинхронной 8-битной передачи/приёма данных.  
**APB2 slave, 32-bit регистры, little-endian.**  
**Сигналы:** TX, RX, nRTS, nCTS.

## Протокол передачи данных
[ADDR][CMD][LEN][DATA...][CRC8]
1B 1B 1B N байт 1B

text
**ADDR:** 0x10-0x7F | **CMD:** 0x01=read,0x02=write | **LEN:** 0-255

## Адресное пространство
| Регистр   | Адрес | Описание              |
|-----------|-------|-----------------------|
| RBR_THR   | 0x00  | RX/TX данные          |
| DLL       | 0x04  | Делитель LSB (DLAB=1) |
| DLM       | 0x08  | Делитель MSB (DLAB=1) |
| LCR       | 0x0C  | Формат кадра          |
| IER       | 0x10  | IRQ enable            |
| IIR       | 0x14  | IRQ status            |
| FCR       | 0x18  | FIFO control          |
| LSR       | 0x1C  | Line status           |
| MCR       | 0x20  | Modem control         |
| MSR       | 0x24  | Modem status          |

## Детальное описание

### RBR_THR (0x00)
| Биты  | Имя | Тип | Сброс | Описание |
|-------|-----|-----|-------|----------|
| 31:8  | —   | R   | 0     | Reserved |
| 7:0   | DATA| R/W | 0x00  | Данные   |

### LCR (0x0C)
| Бит | Имя  | Сброс | Описание |
|-----|------|-------|----------|
| 7   | DLAB | 0     | Доступ к DLL/DLM |
| 1:0 | WLS  | 0x3   | 8 бит данных |
| 3   | PEN  | 0     | Parity     |

### LSR (0x1C) ← **ВАЖНО!**
| Бит | Имя  | Сброс | Описание      |
|-----|------|-------|---------------|
| 0   | DR   | 0     | Data Ready    |
| 1   | OE   | 0     | Overrun       |
| 2   | PE   | 0     | Parity Error  |
| 3   | FE   | 0     | Framing Error |
| 4   | BI   | 0     | Break         |
| 5   | THRE | 1     | TX Empty      |
| 6   | TEMT | 1     | Shift Empty   |

### IER (0x10), FCR (0x18), MCR (0x20)
**IER:** бит 0=RX IRQ, бит 1=TX IRQ  
**FCR:** бит 0=FIFO enable  
**MCR:** бит 1=RTS

## Инициализация
```c
write(0x0C, 0x80);     // LCR: DLAB=1
write(0x04, 0x0D);     // DLL (115200@50MHz)
write(0x08, 0x00);     // DLM
write(0x0C, 0x03);     // LCR: 8N1
Использование
c
// TX
while(!(read(0x1C)&0x20)); write(0x00, data);

// RX  
if(read(0x1C)&0x01) data = read(0x00);