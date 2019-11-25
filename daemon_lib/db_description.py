def movie_before_db(row):
    if "genre_ids" not in row:
        return row
    ret = ""
    for i in row["genre_ids"]:
        ret += str(i)+","
    if len(ret) > 0:
        row["genre_ids"] = ret[:-1]
    else:
        row["genre_ids"] = ""
    return row


def movie_after_db(row):
    if "genre_ids" not in row:
        return row
    ret = []
    for i in row["genre_ids"].split(","):
        if len(i) > 0:
            ret.append(int(i))
    row["genre_ids"] = ret
    return row


video_table = {
    "name": "videos",
    "attrs": {"video_id":       "INTEGER PRIMARY KEY AUTOINCREMENT",
            "path":             "TEXT NOT NULL UNIQUE",
            "media_type":       "INTEGER",
            "media_id":         "INTEGER",
            "duration":         "INTEGER",
            "bit_rate":         "INTEGER",
            "codecs_video":     "TEXT",
            "width":            "INTEGER",
            "height":           "INTEGER",
            "size":             "INTEGER",
            "m_time":           "TEXT",
            "junk":             "INTEGER",
            "last_time":        "INTEGER"}
}

movie_table = {
    "name": "movies",
    "attrs": {"id": "INTEGER NOT NULL UNIQUE",
            "original_title": "TEXT",
            "original_language": "TEXT",
            "title": "TEXT",
            "release_date": "TEXT",
            "overview": "TEXT",
            "vote_average": "INTEGER",
            "poster_path": "TEXT",
            "genre_ids": "TEXT"},
    "auto_joins": [("videos", "media_id", "id")],
    "auto_joins_where": {"media_type": 1},
    "exec_before": movie_before_db,
    "exec_after": movie_after_db,
}

genre_table = {
    "name": "genres",
    "attrs": {"id":               "INTEGER NOT NULL UNIQUE",
              "name":             "TEXT"}
}

database_description = [genre_table, video_table, movie_table]
