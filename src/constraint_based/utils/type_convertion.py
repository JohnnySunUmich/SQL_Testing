month_date = [31,28,31,30,31,30,31,31,30,31,30,31]
def date2int(date: str):
    year, month, day = date.split('-')
    return 365 * int(year) + sum(month_date[:int(month)-1]) + int(day) - 1

def int2date(n: int):
    n = -n if n < 0 else n
    year = n // 365
    if year < 1000:
        year += 1000
    year = str(year)
    rmdr = n % 365
    for i, md in enumerate(month_date):
        if rmdr > md:
            rmdr -= md
        else:
            month = i+1
            day = rmdr+1
            if day > month_date[month-1]:
                day = 1
                month += 1
            break
    return f'{year}-{month}-{day}'

def int2time(n: int):
    date_str = int2date(n)
    return f"{date_str} 00:00:00"

if __name__ == '__main__':
    print(date2int('2019-12-31'))
    print(int2date(date2int('2019-12-31')))