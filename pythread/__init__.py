thread_mode_list = {}


def create_new_mode(group_mode, name, *args, **kwargs):
    if name not in thread_mode_list:
        thread_mode_list[name] = group_mode(name, *args, **kwargs)
    else:
        raise Exception("Mode already created ", name)
    return thread_mode_list[name]


def close_mode(name):
    get_mode(name).close()


def close_all_mode():
    for key in thread_mode_list.keys():
        get_mode(key).close()


def get_mode(name):
    mode = thread_mode_list.get(name)
    if mode is None:
        raise Exception("Mode", name, " unknown")
    return mode


def threaded(name, wait_return=False):
    def decorated(func):
        def wrapper(*args, **kwargs):
            if wait_return:
                return get_mode(name).process(func, *args, **kwargs).get_value()
            else:
                return get_mode(name).process(func, *args, **kwargs)
        return wrapper
    return decorated
