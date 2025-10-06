
import os, sqlite3

def test_schema_exists():
    assert os.path.exists('schema.sql')

def test_can_create_db(tmp_path):
    dbpath = tmp_path / 'test.db'
    conn = sqlite3.connect(dbpath)
    conn.executescript(open('schema.sql', 'r', encoding='utf-8').read())
    conn.close()
    assert dbpath.exists()
