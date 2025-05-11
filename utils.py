def number(text: str):
    """Return int or float"""
    return float(text) if '.' in text else int(text)


def str_sec(number: float | int) -> str:
    """Convert time in ms into sec string"""
    return f'{number / 1000:.2f} sec'


def str_number(number: float | int, accuracy: int = 0, unit: str = '') -> str:
    """Convert number to string with accuracy and unit"""
    if isinstance(number, int) and accuracy == 0:
        return str(number) + unit
    number = float(number)
    s = '{:.' + str(accuracy) + 'f}' + unit
    return s.format(number)

def str_bytes(byte_size: float) -> str:
    """Present memory as float [with accuracy=2] in KB, MB, GB."""
    BASE = 1024
    byte_units = ['B', 'KB', 'MB', 'GB', 'TB']
    for byte_unit in byte_units:
        if byte_size < BASE:
            return f'{byte_size:.2f} {byte_unit}'
        byte_size /= BASE
    return f'{byte_size} {byte_units[-1]}'

def str_bits_per_sec(byte_per_sec: float) -> str:
    """Present memory as float [with accuracy=2] in KB, MB, GB."""
    BASE = 1024
    bit_per_sec = byte_per_sec * 8
    byte_units = ['bits', 'Kbits', 'Mbits', 'Gbits', 'Tbits']
    for byte_unit in byte_units:
        if bit_per_sec < BASE:
            return f'{bit_per_sec:.2f} {byte_unit}/sec'
        bit_per_sec /= BASE
    return f'{bit_per_sec} {byte_units[-1]}/sec'


if __name__ == "__main__":
    print(1234.5, str_sec(1234.5))
    print(12.345, str_number(12.345))
    print(123, str_number(123))
    print(123, str_number(123, 2))
    print('1.16 GB', str_bytes(1245510451))
    print('1.21 GB', str_bytes(1302455137))
    print('1.22 KB', str_bytes(1245))
    print('124.00 B', str_bytes(124))
    print('5.73 Mbits/sec', str_bits_per_sec(751005))
    print('6.01 Mbits/sec', str_bits_per_sec(788091.40))
