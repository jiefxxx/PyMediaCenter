def movie_before_db(db, row):
    movie_id = row["id"]
    if "genre_ids" in row:
        for genre_id in row["genre_ids"]:
            db.set("switch_movies_genres", {"switch_movie_id": movie_id,
                                            "switch_genre_id": genre_id})

    elif "genres" in row:
        for genre in row["genres"]:
            db.set("switch_movies_genres", {"switch_movie_id": movie_id,
                                            "switch_genre_id": genre["id"]})
    return row


def tv_show_before_db(db, row):
    tv_id = row["id"]
    if "genre_ids" in row:
        for genre_id in row["genre_ids"]:
            db.set("switch_tvs_genres", {"switch_tv_id": tv_id,
                                         "switch_genre_id": genre_id})

    elif "genres" in row:
        for genre in row["genres"]:
            db.set("switch_tvs_genres", {"switch_tv_id": tv_id,
                                         "switch_genre_id": genre["id"]})
    return row


def exec_after_db(db, row):
    if 'switch_tv_id' in row:
        del(row["switch_tv_id"])

    if 'switch_movie_id' in row:
        del (row["switch_movie_id"])

    if 'switch_genre_id' in row:
        del (row["switch_genre_id"])

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
            "poster_path": "TEXT"},
    "group_by": "video_id",
    "group_concats": ["genre_name",
                      "genre_id",
                      "switch_movie_id",
                      "switch_genre_id"],
    "auto_joins": [("videos", "media_id", "movies", "id"),
                   ("switch_movies_genres", "switch_movie_id", "movies", "id"),
                   ("genres", "genre_id", "switch_movies_genres", "switch_genre_id")],
    "auto_joins_where": {"media_type": 1},
    "exec_before": movie_before_db,
    "exec_after": exec_after_db,
}

movie_genre_table = {
    "name": "switch_movies_genres",
    "attrs": {"switch_movie_id": "INTEGER NOT NULL",
              "switch_genre_id": "INTEGER NOT NULL"},
    "creation_constraints": "UNIQUE(switch_movie_id, switch_genre_id)"
}

tv_genre_table = {
    "name": "switch_tvs_genres",
    "attrs": {"switch_tv_id": "INTEGER NOT NULL",
              "switch_genre_id": "INTEGER NOT NULL"},
    "creation_constraints": "UNIQUE(switch_tv_id, switch_genre_id)"
}

genre_table = {
    "name": "genres",
    "attrs": {"genre_id":         "INTEGER NOT NULL UNIQUE",
              "genre_name":      "TEXT"}
}

tv_show_table = {
    "name": "tv_shows",
    "attrs": {"id":                "INTEGER NOT NULL UNIQUE",
              "name":              "TEXT",
              "original_language": "TEXT",
              "original_name":     "TEXT",
              "first_air_date":    "TEXT",
              "overview":          "TEXT",
              "vote_average":      "INTEGER",
              "poster_path":       "TEXT",
              },
    "group_concats": ["genre_name",
                      "genre_id",
                      "switch_tv_id",
                      "switch_genre_id"],
    "group_by": "id",
    "auto_joins": [("switch_tvs_genres", "switch_tv_id", "tv_shows", "id"),
                   ("genres", "genre_id", "switch_tvs_genres", "switch_genre_id")],
    "exec_before": tv_show_before_db,
    "exec_after": exec_after_db
}

tv_episode_table = {
    "name": "tv_episodes",
    "attrs": {"episode_id":        "INTEGER NOT NULL UNIQUE",
              "tv_id":             "INTEGER",
              "episode_name":      "TEXT",
              "air_date":          "TEXT",
              "episode_overview":  "TEXT",
              "episode_vote_average": "INTEGER",
              "season_number":     "INTEGER",
              "episode_number":    "INTEGER"},
    "group_concats": ["genre_name",
                      "genre_id",
                      "switch_tv_id",
                      "switch_genre_id"],
    "group_by": "video_id",
    "auto_joins": [("videos", "media_id", "tv_episodes", "episode_id"),
                   ("tv_shows", "id", "tv_episodes", "tv_id"),
                   ("switch_tvs_genres", "switch_tv_id", "tv_shows", "id"),
                   ("genres", "genre_id", "switch_tvs_genres", "switch_genre_id")],
    "auto_joins_where": {"media_type": 2},
    "exec_after": exec_after_db

}

database_description = [genre_table,
                        video_table,
                        movie_table,
                        tv_show_table,
                        tv_episode_table,
                        movie_genre_table,
                        tv_genre_table]
