import http
import re


def chunk(path, seek, size=1024 * 5):
    with open(path, "rb") as f:
        f.seek(seek)
        ret = f.read(size)
    return seek + len(ret), ret


def chunks(path, seek=-1, chunk_size=65500):
    with open(path, "rb") as f:
        if seek > 0:
            f.seek(seek)
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data


def http_code_to_string(code):
    for el in http.HTTPStatus:
        if el.value == code:
            return el.phrase
    return ""


def http_parse_query(line):
    match = re.match(r"(.*) (.*) (.*)", line.decode())
    if match is not None:
        return match.group(1), match.group(2), match.group(3)
    else:
        raise Exception("Invalid Request", str(line))


def http_parse_field(line):
    match = re.match(r"(.*): (.*)", line.decode())
    if match is not None:
        return match.group(1), match.group(2)
    else:
        raise Exception("Invalid format field:", str(line))


HTTP_CONNECTION_ABORT = -1
HTTP_CONNECTION_CONTINUE = 0
HTTP_CONNECTION_UPGRADE = 1