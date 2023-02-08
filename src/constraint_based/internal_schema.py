class TableSchema:
    def __init__(self, table_id: int, table_name: str, size_bound: int):
        self.table_id = table_id
        self.table_name = table_name
        self.columns = []
        self.size_bound = size_bound

    def __eq__(self, other):
        if self.table_name == other.table_name:
            for idx, column in enumerate(self.columns):
                if column != other.columns[idx]:
                    return False
            return True
        return False

    def get_info(self):
        return self.table_id, self.table_name

    def __getitem__(self, item):
        return self.columns[item]

    def __setitem__(self, key, value):
        if not isinstance(value, ColumnSchema):
            raise ValueError(f"{value} is not a Column_Schema type.")
        self.columns[key] = value

    def append(self, column):
        self.columns.append(column)

    def __len__(self):
        return len(self.columns)

    def __iter__(self):
        for column in self.columns:
            yield column

    def __str__(self):
        output_str = f"T{self.table_id}:["
        column_str = []
        for column in self.columns:
            column_str.append(str(column))
        column_str = ",".join(column_str)
        output_str += column_str + "]"
        return output_str


class ColumnSchema:
    def __init__(self, column_id: int, column_name: str, column_type: str, referred_table_name: str=None, agg_func: str=None):
        self.column_id = column_id
        self.column_name = column_name
        self.column_type = column_type
        self.referred_table_name = referred_table_name
        self.agg_func = agg_func

    def __eq__(self, other):
        return self.column_name == other.column_name and \
               self.column_type == other.column_type and \
               self.referred_table_name == other.referred_table_name and \
               self.agg_func == other.agg_func

    def get_info(self):
        return self.column_id, self.column_name, self.column_type, self.referred_table_name, self.agg_func

    def __str__(self):
        return f"c{self.column_id}({self.referred_table_name}):{self.column_type}"
