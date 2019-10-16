import sqlite3
from thread_mananger.threadMananger import ThreadMananger, threadedFunction, sequesterFunction


def dict_filter(old_dict, keys):
    new_dict = {}
    for key in keys:
        if key in old_dict:
            new_dict[key] = old_dict[key]
    return new_dict


def merge_dicts(*dict_args):
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


class DataBase(ThreadMananger):
    def __init__(self, path):
        ThreadMananger.__init__(self, nbr_thread=1)
        self.db = None
        self.db_description = None
        self.initialize_db(path)

    def create(self, db_description):
        self.db_description = db_description
        for table_description in db_description:
            self.create_table(table_description["name"], table_description["attrs"])

    def get(self, table_name, columns=None, where=None, joins=None, auto_joins=True):
        table_description = self.find_table(table_name)

        if "auto_joins" in table_description and auto_joins:
            if joins is None: joins = []
            joins += table_description["auto_joins"]
            if "auto_joins_where" in table_description:
                if where is None: where = {}
                where = merge_dicts(where, table_description["auto_joins_where"])

        for row in self.select_rows(table_name, columns=columns, where=where, joins=joins):
            if "exec_after" in table_description:
                row = table_description["exec_after"](row)
            yield row

    def set(self, table_name, row):
        table_description = self.find_table(table_name)

        if "exec_before" in table_description:
            row = table_description["exec_before"](row)

        self.update_row(table_description["name"], dict_filter(row, table_description["attrs"].keys()))

    def find_table(self, table_name):
        for table_description in self.db_description:
            if table_description["name"] == table_name:
                return table_description
        return None

    @threadedFunction()
    def initialize_db(self, path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = lambda C, R: {c[0]: R[i] for i, c in enumerate(C.description)}

    @sequesterFunction()
    def select_rows(self, table, columns=None, where=None, joins=None):
        if columns is None: columns = ["*"]
        if where is None:  where = {}
        if joins is None: joins = []

        data = []
        script = "SELECT "

        for column in columns:
            script += column
            script += ", "
        script = script[:-2]
        script += " FROM "+table+" "
        script += join_to_sql(table, joins)
        partial_script, partial_data = where_to_sql(where)
        script += partial_script
        data += partial_data

        with self.db as c:
            for row in c.execute(script, tuple(data)):
                yield row
        self.db.commit()

    @threadedFunction()
    def update_row(self, table, row_data):
        data = []

        script = "INSERT OR REPLACE INTO " + table + " "
        script += "("
        for key in row_data.keys():
            script += key + ", "
            data.append(row_data[key])
        script = script[:-2] + ") "
        script += "VALUES ("
        for i in range(0, len(data)):
            script += "?, "
        script = script[:-2] + ") "

        with self.db as c:
            c.execute(script, tuple(data))
        self.db.commit()

    @threadedFunction()
    def delete_row(self, table, where):
        data = []

        script = "DELETE FROM " + table + " "
        tmp_script, tmp_data = where_to_sql(where)
        script += tmp_script
        data += tmp_data

        with self.db as c:
            c.execute(script, tuple(data))
        self.db.commit()

    @threadedFunction()
    def create_table(self, table, constructor):
        script = "create table if not exists "
        script += table + " ("
        for var, var_type in constructor.items():
            if var_type is not None:
                script += var + " " + var_type + ", "
        script = script[:-2] + ')'
        with self.db as c:
            c.execute(script)
        self.db.commit()


def where_to_sql(where):
    script = ""
    data = []
    first = True
    for var in where.keys():
        if not first:
            script += " AND "
        else:
            script += "WHERE "
        if where.get(var) is None:
            script += var + " IS NULL"
        else:
            script += var + " = (?)"
            data.append(where.get(var))
        first = False
    return script, data


def join_to_sql(table, joins):
    script = ""
    for join in joins:
        script += "INNER JOIN "+join[0]+" ON "+join[0]+"."+join[1]+" = "+table+"."+join[2]+" "
    return script