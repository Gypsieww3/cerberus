"""Descriptive Lotofácil history. Past frequencies do not predict future draws."""
from collections import Counter,defaultdict
from datetime import date

def validate(numbers):
    if not isinstance(numbers,(list,tuple,set)) or len(numbers)!=15:
        raise ValueError("Exactly 15 numbers required")
    if len(set(numbers))!=15 or any(type(n) is not int or not 1<=n<=25 for n in numbers):
        raise ValueError("Only unique integers between 1 and 25")
    return frozenset(numbers)

def summarize(records):
    total=Counter()
    by_weekday=defaultdict(Counter)
    by_month=defaultdict(Counter)
    dates=set()
    count=0
    for record in records:
        day=date.fromisoformat(record["date"])
        if day in dates:
            raise ValueError("Duplicate date; use distinct draw IDs for multi-draw days")
        dates.add(day)
        numbers=validate(record["numbers"])
        total.update(numbers)
        by_weekday[day.weekday()].update(numbers)
        by_month[day.month].update(numbers)
        count+=1
    return dict(count=count,
        frequency={str(n):total[n] for n in range(1,26)},
        by_weekday={str(k):{str(n):v[n] for n in range(1,26)} for k,v in sorted(by_weekday.items())},
        by_month={str(k):{str(n):v[n] for n in range(1,26)} for k,v in sorted(by_month.items())},
        warning="Frequencies are descriptive, not a prediction strategy")
