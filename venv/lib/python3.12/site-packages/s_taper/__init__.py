import pickle
import sqlite3
import s_taper.consts
import s_taper.aio

class Taper:
    """
    Класс для работы с таблицами в базе данных SQLite.

    :param str table_name: Название таблицы.
    :param str file_name: Название файла базы данных SQLite.
    """

    class _Answer(list):
        """
        Внутренний класс, представляющий строку в таблице базы данных.

        Attributes:
            _row (dict): Словарь, сопоставляющий названия столбцов и их соответствующие индексы в строке.
            _columns (dict): Словарь, содержащий названия столбцов как ключи и их позиции в списке значений.
        """

        def __init__(self, read, columns):
            """
            Инициализирует новый экземпляр класса _Answer.

            Args:
                read (list): Список значений, соответствующих столбцам таблицы.
                columns (dict): Словарь, сопоставляющий названия столбцов и их позиции в списке значений.
            """
            self._row = {}
            for num, value in enumerate(read):
                self._row[list(columns.keys())[num]] = num

            super().__init__(read)
            self._columns = columns
            if read:
                self._set_attr(read)

        def _set_attr(self, values):
            """
            Устанавливает атрибуты экземпляра _Answer на основе предоставленных значений.

            Args:
                values (list): Список значений, соответствующих столбцам таблицы.
            """
            # Установка атрибутов для каждого столбца на основе переданных значений.
            for n, column_name in enumerate(self._columns):
                """
                Если тип столбца - boolean, устанавливает атрибут в значение True, если значение в ячейке "1",
                в противном случае устанавливает в значение False.
                """
                if self._columns[column_name] == "boolean":
                    super().__setattr__(column_name, True if values[n] == "1" else False)
                else:
                    super().__setattr__(column_name, values[n])

        def _set_item(self, key, value):
            """
            Устанавливает значение элемента с использованием ключа.

            Args:
                key: Ключ для установки значения.
                value: Значение, которое нужно установить.
            """
            # Установка значения элемента с использованием ключа.
            if key in ("_row", "_columns"):
                return
            else:
                try:
                    super().__setitem__(self._row[key], value)
                except KeyError:
                    raise KeyError("Такого столбца не существует в таблице, нельзя добавить этот атрибут.")

        def __setattr__(self, key, value):
            """
            Переопределяет метод __setattr__ для установки атрибута и вызова _set_item.

            Args:
                key: Ключ атрибута.
                value: Значение атрибута.
            """
            try:
                # Переопределение метода для установки атрибута и вызова _set_item.
                if key in ["_row", "_columns"]:
                    return super().__setattr__(key, value)
                elif key not in self._columns:
                    return
                else:
                    return super().__setattr__(key, value)
            finally:
                self._set_item(key, value)

        def __getitem__(self, item):
            """
            Переопределяет метод __getitem__ для доступа к элементам по индексу или ключу.

            Args:
                item: Индекс элемента или ключ атрибута.

            Returns:
                Значение элемента или атрибута.
            """
            if isinstance(item, slice) or isinstance(item, int):
                return super().__getitem__(item)
            return self.__dict__[item]

        def __setitem__(self, key, value):
            """
            Переопределяет метод __setitem__ для установки значения элемента по индексу или ключу.

            Args:
                key: Индекс элемента или ключ атрибута.
                value: Значение, которое нужно установить.
            """
            try:
                if isinstance(key, slice) or isinstance(key, int):
                    return super().__setitem__(key, value)
                else:
                    # Обращение как к словарю
                    return super().__setitem__(self._row[key], value)
            finally:
                # Обновление атрибутов после изменения
                self._set_attr(self)

    class _ColumnCountError(Exception):
        def __init__(self, *args):
            if args:
                self.message = args[0]
            else:
                self.message = None

    class _TooMuchColumnError(_ColumnCountError):
        def __init__(self):
            super().__init__()

        def __str__(self):
            if self.message:
                return f"Передано значений больше, чем столбцов в таблице. {self.message}"
            else:
                return f"Передано значений больше, чем столбцов в таблице."

    class _TooFewColumnError(_ColumnCountError):
        def __init__(self):
            super().__init__()

        def __str__(self):
            if self.message:
                return f"Передано значений меньше, чем столбцов в таблице. {self.message}"
            else:
                return f"Передано значений меньше, чем столбцов в таблице."

    def __init__(self, table_name: str, file_name: str):
        """
        Инициализирует экземпляр класса Taper.

        :param str table_name: Название таблицы.
        :param str file_name: Название файла базы данных SQLite.
        """
        self._table_name: str = table_name
        self._file_name: str = file_name
        # self.obj = self._Answer()
        self._columns = {}

    def write(self, values: list | tuple = None, table_name: str = None):
        """
        Записывает данные в таблицу.

        :param list | tuple values: Список или кортеж значений для записи.
        :param str table_name: Название таблицы. По умолчанию используется название, указанное при создании экземпляра класса.
        :raises: _TooMuchColumnError: Если передано значений больше, чем столбцов в таблице.
        :raises: _TooFewColumnError: Если передано значений меньше, чем столбцов в таблице.
        :return: Записанные значения.
        :rtype: list | tuple
        """
        if table_name is None:
            table_name = self._table_name

            a = type(values)

            if len(values) > len(self._columns):
                raise self._TooMuchColumnError
            if len(values) < len(self._columns):
                raise self._TooFewColumnError

        # pickle check
        values = list(values)
        for n, val in enumerate(values):
            if type(val) in (list, tuple, dict, set):
                values[n] = pickle.dumps(val)
        # /pickle check

        conn = sqlite3.connect(self._file_name)
        cur = conn.cursor()
        questions = "?"
        for x in range(len(values) - 1):
            questions += ", ?"

        cur.execute(f"INSERT or REPLACE into {table_name} VALUES({questions});", values)
        conn.commit()
        conn.close()
        return values

    def read(self, column_name: str, key: str | int):
        """
        Читает данные из таблицы по заданному столбцу и ключу.

        :param str column_name: Название столбца для поиска.
        :param str | int key: Значение ключа.
        :return: Результаты чтения из таблицы.
        :rtype: _Answer | list[_Answer]
        """
        conn = sqlite3.connect(self._file_name)
        cur = conn.cursor()
        cur.execute(f'SELECT * from {self._table_name} WHERE {column_name} = ? ', (key,))
        result = cur.fetchall()

        a = None
        if len(result) == 1:
            result = result[0]

            # pickle check
            result = list(result)
            for n, val in enumerate(result):
                if type(val) in (bytes, bytearray):
                    result[n] = pickle.loads(val)

            a = self._Answer(result, self._columns)
            # /pickle check

        else:
            answer = []
            # pickle check
            for n, row in enumerate(result):
                row = list(row)
                for m, val in enumerate(row):
                    if type(val) in (bytes, bytearray):
                        row[m] = pickle.loads(val)
                result[n] = row

            for row in result:
                answer.append(self._Answer(row, self._columns))
            a = answer


        return a

    def read_all(self, table_name: str = None):
        """
        Читает все данные из таблицы.

        :param str table_name: Название таблицы. По умолчанию используется название, указанное при создании экземпляра класса.
        :return: Список объектов _Answer, представляющих строки таблицы.
        :rtype: list[_Answer]
        """
        if table_name is None:
            table_name = self._table_name
        conn = sqlite3.connect(self._file_name)
        cur = conn.cursor()
        cur.execute(f"SELECT * from {table_name}")
        result = cur.fetchall()

        # pickle check
        if len(result) <= 1000:
            for n, row in enumerate(result):
                row = list(row)
                for m, val in enumerate(row):
                    if type(val) in (bytes, bytearray):
                        row[m] = pickle.loads(val)
                result[n] = row
        # /pickle check

        final = []
        for row in result:
            a = self._Answer(row, self._columns)
            final.append(a)

        conn.close()
        return final

    def delete_row(self, column_name: str = None, key: str | int = None, all_rows: bool = None):
        """
        Удаляет строку(и) из таблицы.

        :param str column_name: Название столбца для поиска. Если не указан, удаляются все строки (при условии all_rows=True).
        :param str | int key: Значение ключа. Если указан, удаляется строка с соответствующим значением в указанном столбце.
        :param bool all_rows: Если True, удаляются все строки из таблицы. По умолчанию False.
        """

        conn = sqlite3.connect(self._file_name)
        cur = conn.cursor()
        if all_rows:
            cur.execute(f'DELETE FROM {self._table_name}')
        else:
            cur.execute(f'DELETE FROM {self._table_name} WHERE {column_name} = ?', (key,))
        conn.commit()
        conn.close()

    def create_table(self, table: dict, table_name: str = None):
        """
        Создает новую таблицу.

        :param dict table: Словарь, содержащий названия столбцов и их типы данных.
        :param str table_name: Название новой таблицы. По умолчанию используется название, указанное при создании экземпляра класса.
        :return: Новый экземпляр класса Taper, связанный с созданной таблицей.
        :rtype: Taper
        """
        if table_name is None:
            table_name = self._table_name
        conn = sqlite3.connect(self._file_name)
        cur = conn.cursor()
        task = f"CREATE TABLE IF NOT EXISTS {table_name}("
        n = 0
        for key in table:
            n += 1
            task += f"{key} {table[key]}"
            if n != len(table):
                task += ", "
            else:
                task += ");"
        cur.execute(task)
        conn.commit()
        conn.close()

        temp = Taper(table_name, self._file_name)
        temp._columns = table
        # temp.__create_obj__()
        return temp

    def drop_table(self, table_name: str = None):
        """
        Удаляет таблицу из базы данных.

        :param str table_name: Название таблицы для удаления. Если не указано, используется название, указанное при создании экземпляра класса.
        """

        if not table_name:
            table_name = self._table_name
        conn = sqlite3.connect(self._file_name)
        cur = conn.cursor()
        cur.execute(f"DROP TABLE {table_name}")
        conn.commit()
        conn.close()

    def execute(self, sql: str, fetchall=True):
        """
                Выполняет произвольный SQL-запрос.

                :param str sql: Строка SQL-запроса.
                :param bool fetchall: Если True, возвращает все строки результата запроса. Если False, возвращает только первую строку. По умолчанию True.
                :return: Результат выполнения SQL-запроса.
                :rtype: list | tuple | None
        """
        conn = sqlite3.connect(self._file_name)
        cur = conn.cursor()
        result = cur.execute(sql)
        conn.commit()
        if fetchall:
            result = result.fetchall()
        else:
            result = result.fetchone()
        conn.close()
        return result
