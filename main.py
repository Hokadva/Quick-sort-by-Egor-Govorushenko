"""
CLI sorting app
"""
#pylint: disable=W0123
import argparse
import sys
from ast import literal_eval
from pathlib import Path
from typing import Callable, Optional

from my_sort import my_sort


class Excp(Exception):
    """
    Class for ignore pylint error W0718
    """
    def __init__(self, *args):
        super().__init__(*args)


def parse_arg():
    """
    That func parse arguments from call
    """
    parser = argparse.ArgumentParser(
        prog="quick sort",
        description=("Sorts an array with data using quick sort"),
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-a", "--array", type=str, help="Array")
    source.add_argument("-f", "--file", type=str, help="Filepath")

    parser.add_argument(
        "-r", "--reversed", help="Reverse sorting array", action="store_true"
    )
    parser.add_argument(
        "-k", "--key", help="Allows you to enter a function of a single variable " \
        "that converts an array object to a comparable value."
    )
    parser.add_argument(
        "-c", "--cmp", help="Allows you to enter a function of two variables " \
        "that compares the two values key(x) and key(y) and outputs the result " \
        "of the comparison as a Boolean variable, if the key is not specified, " \
        "then the work is with array objects."
    )
    parser.add_argument(
        "-o", "--output", type=str, help="Output filepath"
    )
    return parser.parse_args()

def base_key(x):
    return x

def base_cmp(x, y):
    return x <= y


FUNCS = {
    "key": base_key,
    "cmp": base_cmp
}


def str_to_func(func: str, name: str, *elements) -> Optional[Callable]:
    """
    Function convert string to function
    """
    if func is None:
        return FUNCS[name]

    try:
        func = eval(func)
        func(*elements)
    except Excp:
        print(f"{name} isn't valid")
        sys.exit(1)

    return func

def run():
    """
    Entry point of program
    """
    args = parse_arg()

    if args.file:
        path = Path(args.file)

        if not path.exists():
            print("File not found")
            sys.exit(1)

        if not path.is_file():
            print("Can't read file")
            sys.exit(1)

        array = path.read_text("utf-8")

    else:
        array = args.array

    try:
        array = literal_eval(array)
        if not isinstance(array, list):
            array = [array]
    except (ValueError, SyntaxError):
        print("Incorrent array format.")
        sys.exit(1)

    revers = args.reversed
    key = args.key
    cmp = args.cmp

    if len(array) > 1:
        key = str_to_func(key, "key", array[0])
        cmp = str_to_func(cmp, "cmp", key(array[0]), key(array[1]))

    else:
        key = base_key
        cmp = base_cmp

    try:
        result = my_sort(array, revers, key, cmp)
    except Excp:
        print("sorting error")
        sys.exit(1)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(str(result))
            print(f"Sorted array in {args.output}")
        except Excp:
            print("Can't create that file")
    else:
        print(result)

if __name__ == "__main__":
    run()
