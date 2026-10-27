# Quick Sort Project

Небольшой учебный проект с собственной реализацией quick-sort, CLI-обёрткой и визуализацией процесса.

## Модули проекта

- `my_sort.py` - содержит функцию `my_sort(...)`: рекурсивная сортировка (quick sort) с поддержкой `reverse`, `key`, `cmp`.
- `main.py` - CLI-программа: читает массив из аргумента или файла, сортирует и печатает/сохраняет результат.
- `visualize.py` - GUI-визуализатор сортировки на `PyQt6 + matplotlib`.

## Как пользоваться CLI (`main.py`)

### Базовый запуск

```bash
python main.py -a "[3, 1, 2]"
```

или из файла:

```bash
python main.py -f input.txt
```

где `input.txt` содержит, например:

```text
[3, 1, 2]
```

### Параметры

- `-a, --array` - массив строкой (например, `"[5, 2, 9]"`).
- `-f, --file` - путь к файлу с массивом.
- `-r, --reversed` - сортировка по убыванию.
- `-k, --key` - функция `key` строкой (пример: `"lambda x: abs(x)"`).
- `-c, --cmp` - функция сравнения строкой (пример: `"lambda x, y: x < y"`).
- `-o, --output` - путь для записи результата.

### Примеры

```bash
python main.py -a "[10, -2, 7, 0]" -r
python main.py -a "[-3, 1, -2]" -k "lambda x: abs(x)"
python main.py -f input.txt -o output.txt
python main.py -a "[-3, 1, -2]" -k "str" -c "lambda x,y: len(x) < len(y)"
```

## Как пользоваться `visualize.py` (GUI)

Запуск:

```bash
python visualize.py
```

После запуска:

1. Укажите диапазон значений (`Minimum possible value`, `Maximum possible value`).
2. Укажите размер массива (`Array size`) и скорость (`Speed`).
3. При необходимости включите `Sorting in reverse order`.
4. Нажмите `start` для старта, `pause` для паузы/продолжения, `restart` для генерации нового массива.
