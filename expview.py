from flask import Response, Flask, request, jsonify
import sqlite3
import json
from dateutil import parser
import webbrowser

app = Flask(__name__)

sqlite_file = "explog.db"


def group_format(identifier):
    if identifier == "year":
        return '%Y-01-01T00:00:00.000'
    if identifier == "month":
        return '%Y-%m-01T00:00:00.000'
    if identifier == "day":
        return '%Y-%m-%dT00:00:00.000'
    if identifier == "hour":
        return '%Y-%m-%dT%H:00:00.000'

    return '%Y-%m-%dT%H:%M:00.000'


def load_response(sql):
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    c.execute(sql)
    response = jsonify(c.fetchall())
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers['Cache-Control'] = 'public, max-age=0'
    conn.close()
    return response


@app.route("/rate")
def rate():
    duration = request.args.get("duration") or 1
    character = request.args.get("character")
    group_by = request.args.get("group") or "day"
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    sql = """
    SELECT t1.skill, avg(rate), max(t2.ranks)
    FROM (
        SELECT skill, max(rank + (perc/100.0)) - min(rank + (perc/100.0)) as rate
        FROM skills
        WHERE character = '{character}'
        AND timestamp > (SELECT DATETIME('now', '-{duration} day'))
        GROUP BY skill, strftime('{group}', timestamp)
    ) t1
    INNER JOIN
    (
        SELECT max(rank + (perc/100.0)) - min(rank + (perc/100.0)) as ranks, skill, max(rank + (perc/100.0))
        FROM skills
        WHERE character = '{character}'
        AND timestamp > (SELECT DATETIME('now', '-{duration} day'))
        GROUP BY skill
    ) as t2 ON t1.skill = t2.skill
    GROUP BY t1.skill
    ORDER by t2.ranks DESC;
        """.format(character=character, group=group_format(group_by), duration=duration)
    c.execute(sql)
    response = jsonify(c.fetchall())
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers['Cache-Control'] = 'public, max-age=0'
    conn.close()
    return response


@app.route('/chartdata')
def chartdata():
    skill = request.args.get("skill")
    duration = request.args.get("duration") or 1
    character = request.args.get("character")
    group_by = request.args.get("group") or "day"
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    sql = """
        SELECT rank + (perc/100.0), strftime('{group}', timestamp)
        FROM skills
        WHERE skill = '{skill}'
        AND character = '{character}'
        AND timestamp > (SELECT DATETIME('now', '-{duration} day'))
        GROUP BY strftime('{group}', timestamp);
        """.format(skill=skill, character=character, group=group_format(group_by), duration=duration)
    c.execute(sql)
    response = jsonify(c.fetchall())
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers['Cache-Control'] = 'public, max-age=0'
    conn.close()
    return response


@app.route('/characters')
def characters():
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    sql = """
    SELECT DISTINCT character
    FROM skills
    """
    c.execute(sql)
    response = jsonify([item for sublist in c.fetchall() for item in sublist])
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers['Cache-Control'] = 'public, max-age=0'
    conn.close()
    return response


@app.route("/weekday_playtime")
def weekday():
    duration = request.args.get("duration") or 1000
    character = request.args.get("character")
    sql = """
        SELECT SUM(maxBits) - SUM(minBits) as bits, weekday FROM (
            SELECT MAX(skills.rank), 
                min(skills.rank), 
                skill,	
                (
                    SELECT SUM(bits) FROM bits WHERE rank = MAX(skills.rank) 
                ) as maxBits,
                (
                    SELECT SUM(bits) FROM bits WHERE rank = MIN(skills.rank) 
                ) as minBits,
                strftime('%w', timestamp) as weekday
            FROM skills
            WHERE character='{character}' AND timestamp > (SELECT DATETIME('now', '-{duration} day'))
            GROUP BY skill, strftime('%w', timestamp)
        )
        GROUP BY weekday

    """.format(character=character, duration=duration)
    return load_response(sql)


@app.route("/bits")
def bits():
    duration = request.args.get("duration") or 1000
    group_by = request.args.get("group") or "day"
    character = request.args.get("character")
    sql = """
        SELECT SUM(maxBits) - SUM(minBits) as bits, grouped_time FROM (
            SELECT MAX(skills.rank), 
                min(skills.rank), 
                skill,	
                (
                    SELECT SUM(bits) FROM bits WHERE rank = MAX(skills.rank) 
                ) as maxBits,
                (
                    SELECT SUM(bits) FROM bits WHERE rank = MIN(skills.rank) 
                ) as minBits,
                strftime('{group}', timestamp) as grouped_time
            FROM skills
            WHERE character='{character}' AND timestamp > (SELECT DATETIME('now', '-{duration} day'))
            GROUP BY skill, strftime('{group}', timestamp)
        )
        GROUP BY grouped_time

    """.format(character=character, duration=duration, group=group_format(group_by))
    return load_response(sql)


@app.route("/skill_gain")
def project():
    character = request.args.get("character")
    duration = request.args.get("duration") or 1000
    sql = """
        SELECT skill, min(rank + (perc/100.0)) as minRank, max(rank + (perc/100.0)) as maxRank, min(timestamp), max(timestamp)
        from skills
        WHERE character='{character}' AND timestamp > (SELECT DATETIME('now', '-{duration} day'))
        group by skill
    """.format(character=character, duration=duration)
    return load_response(sql)


def create_bits_table():
    conn = sqlite3.connect(sqlite_file)
    c = conn.cursor()
    c.execute(
        ''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='bits' ''')
    if c.fetchone()[0] != 1:
        print("Generating bits table")
        cc = conn.cursor()
        cc.execute("CREATE TABLE bits (rank NUMERIC, bits NUMERIC);")
        for i in range(1, 1750):
            ic = conn.cursor()
            ic.execute("INSERT INTO bits (rank, bits) VALUES ({rank}, {bitss});".format(
                rank=i, bits=(i * (i + 399))/2))
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return """
        <!DOCTYPE html><html lang=en><head><meta charset=utf-8><meta http-equiv=X-UA-Compatible content="IE=edge"><meta name=viewport content="width=device-width,initial-scale=1"><link rel=icon href=/favicon.ico><title>EXP Viewer</title><link href=http://s3.amazonaws.com/drexpviewer/css/app.css rel=preload as=style><link href=http://s3.amazonaws.com/drexpviewer/css/chunk-vendors.css rel=preload as=style><link href=http://s3.amazonaws.com/drexpviewer/js/app.js rel=preload as=script><link href=http://s3.amazonaws.com/drexpviewer/js/chunk-vendors.js rel=preload as=script><link href=http://s3.amazonaws.com/drexpviewer/css/chunk-vendors.css rel=stylesheet><link href=http://s3.amazonaws.com/drexpviewer/css/app.css rel=stylesheet></head><body><noscript><strong>We're sorry but expviewer-ui doesn't work properly without JavaScript enabled. Please enable it to continue.</strong></noscript><div id=app></div><script src=http://s3.amazonaws.com/drexpviewer/js/chunk-vendors.js></script><script src=http://s3.amazonaws.com/drexpviewer/js/app.js></script></body></html>
        """


if __name__ == '__main__':
    create_bits_table()
    webbrowser.open('http://localhost:5000/', new=2)
    app.run()
