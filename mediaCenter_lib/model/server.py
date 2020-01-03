from mediaCenter_lib.model import ServerStateHandler, ModelTableListDict
from pythread import threaded


class ServerModel(ServerStateHandler, ModelTableListDict):

    def __init__(self, servers, **kwargs):
        ModelTableListDict.__init__(self, [("ServerName", "name", False, None),
                                           ("SeverAddress", 'addr', False, None)], **kwargs)

        ServerStateHandler.__init__(self, servers)
        self.refresh()

    def refresh(self):
        data = []
        for server in self.servers.all(connected=True):
            data.append({"name": server.name, "addr": server.address+":"+str(server.port), "server": server})

        self.reset_data(data)
        self.end_refreshed()

    def on_connection(self, server_name):
        self.refresh()

    def on_disconnection(self, server_name):
        self.refresh()

    @threaded("httpCom")
    def start_script(self, name, server_name):
        self.servers.server(server_name).start_script(name)

    def get_progress_action(self, server_name):
        return self.servers.server(server_name).progress

    def get_last_progress(self, server_name):
        return self.servers.server(server_name).last_data_progress

    def close(self):
        self.servers.close()


class ServerTasksModel(ServerStateHandler, ModelTableListDict):
    def __init__(self, servers, server, **kwargs):
        ModelTableListDict.__init__(self, [("TaskName", "name", False, None),
                                           ("TaskDescription", 'description', False, None),
                                           ("Progress", "progress", False, None),
                                           ("String", "string", False, None)], **kwargs)

        ServerStateHandler.__init__(self, servers)
        self.server = server
        self.server.task.connect(self.on_task)
        self.refresh()

    def on_task(self, task):
        index = self.get_index_of("id", task["id"])
        if index is not None:
            self.setData(index, task)
        else:
            self.add_data(task)

    def refresh(self):
        self.reset_data(self.server.get_tasks())
        self.end_refreshed()

    def on_connection(self, server_name):
        if server_name == self.server.name:
            self.refresh()

    def on_disconnection(self, server_name):
        if server_name == self.server.name:
            self.refresh()
