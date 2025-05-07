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

# if __name__ == "__main__":
#     print(1234.5, str_sec(1234.5))
#     print(12.345, str_number(12.345))
#     print(123, str_number(123))
#     print(123, str_number(123, 2))
