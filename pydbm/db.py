import sqlite3

from pythread import create_new_mode, threaded
from pythread.modes import ProcessMode


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


class DataBase:
    def __init__(self, path):
        self.db = None
        self.db_description = None
        self.initialize_db(path)

    def create(self, db_description):
        self.db_description = db_description
        for table_description in db_description:
            self.create_table(table_description["name"],
                              table_description["attrs"],
                              table_description.get("creation_constraints",None))

    def reset_table(self, table):
        for table_description in self.db_description:
            if table_description["name"] == table:
                self.drop_table(table_description["name"])
                self.create_table(table_description["name"], table_description["attrs"])

    def get(self, table_name, columns=None, where=None, joins=None, auto_joins=True):
        table_description = self.find_table(table_name)
        if not table_description:
            raise Exception("Can't find table " + str(table_name))

        if "auto_joins" in table_description and auto_joins:
            if joins is None: joins = []
            joins += table_description["auto_joins"]
            if "auto_joins_where" in table_description:
                if where is None: where = {}
                where = merge_dicts(where, table_description["auto_joins_where"])

        if columns is None:
            columns = list(table_description["attrs"].keys())
            if joins:
                for join_description in joins:
                    columns += list(self.find_table(join_description[0])["attrs"].keys())

        for row in self.select_rows(table_name, columns=columns, where=where, joins=joins):
            if "exec_after" in table_description:
                row = table_description["exec_after"](self, row)
            yield row

    def set(self, table_name, row, only_insert=False):
        table_description = self.find_table(table_name)

        if "exec_before" in table_description:
            row = table_description["exec_before"](self, row)

        self.update_row(table_description["name"], dict_filter(row, table_description["attrs"].keys()), only_insert)

    def find_table(self, table_name):
        for table_description in self.db_description:
            if table_description["name"] == table_name:
                return table_description
        return None

    def initialize_db(self, path):
        self.db = sqlite3.connect(path, check_same_thread=False)

        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                column_name = col[0]
                if column_name.startswith("GROUP_CONCAT("):
                    column_name = column_name[13:-1]
                    if row[idx] is not None:
                        d[column_name] = row[idx].split(",")
                    else:
                        d[column_name] = row[idx]
                else:
                    d[column_name] = row[idx]
            return d

        self.db.row_factory = dict_factory

    def select_rows(self, table, columns=None, where=None, joins=None):
        if columns is None: columns = ["*"]
        if where is None:  where = {}
        if joins is None: joins = []

        table_description = self.find_table(table)

        data = []
        script = "SELECT "

        for column in columns:
            if column in table_description.get("group_concats", []):
                script += "GROUP_CONCAT(" + column + ")"
            else:
                script += column
            script += ", "
        script = script[:-2]
        script += " FROM " + table + " "
        script += join_to_sql(table, joins)
        partial_script, partial_data = where_to_sql(where)
        script += partial_script
        data += partial_data
        group_by = table_description.get("group_by", None)
        if group_by:
            script += " GROUP BY " + group_by

        with self.db as c:
            for row in c.execute(script, tuple(data)):
                yield row
        self.db.commit()

    def update_row(self, table, row_data, only_insert=False):
        data = []
        script = "INSERT OR REPLACE INTO " + table + " "
        if only_insert:
            script = "INSERT INTO " + table + " "
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
            try:
                c.execute(script, tuple(data))
            except sqlite3.InterfaceError as e:
                print(e, script, tuple(data))

        self.db.commit()

    def delete_row(self, table, where):
        data = []

        script = "DELETE FROM " + table + " "
        tmp_script, tmp_data = where_to_sql(where)
        script += tmp_script
        data += tmp_data

        with self.db as c:
            c.execute(script, tuple(data))
        self.db.commit()

    def delete_all(self, table):
        self.delete_row(table, {})

    def delete_column(self, table, column, where):
        data = []
        script = "UPDATE " + table + " SET " + column + "=NULL "
        tmp_script, tmp_data = where_to_sql(where)
        script += tmp_script
        data += tmp_data

        with self.db as c:
            c.execute(script, tuple(data))
        self.db.commit()

    def drop_table(self, table):
        script = "DROP TABLE IF EXISTS " + table + ";"
        with self.db as c:
            c.execute(script)
        self.db.commit()

    def create_table(self, table, constructor, end_script=None):
        script = "create table if not exists "
        script += table + " ("
        for var, var_type in constructor.items():
            if var_type is not None:
                script += var + " " + var_type + ", "
        if end_script:
            script += " "
            script += end_script
        else:
            script = script[:-2]
        script += ")"
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
        script += "INNER JOIN " + join[0] + " ON " + join[0] + "." + join[1] + " = " + join[2] + "." + join[3] + " "
    return script
