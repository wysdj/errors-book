"""408 错题管理器 — 数据库模块"""

import sqlite3
import os
import json
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(__file__), 'errors.db')


def get_db():
    """获取数据库连接"""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row  # 让查询结果可以用 row['字段名'] 访问
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db():
    """初始化：建表（只执行一次）"""
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS errors (
            id              INTEGER PRIMARY KEY,
            question_text   TEXT NOT NULL,
            answer_text     TEXT,
            image_path      TEXT,
            ocr_text        TEXT,
            ocr_confidence  REAL,
            ai_subject      TEXT,
            ai_chapter      TEXT,
            ai_topics       TEXT,
            ai_difficulty   TEXT,
            subject         TEXT,
            chapter         TEXT,
            topics          TEXT,
            error_reason    TEXT,
            reference_answer TEXT,
            image_desc      TEXT,
            mastered        INTEGER DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            reviewed_at     TEXT
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id              INTEGER PRIMARY KEY,
            error_id        INTEGER NOT NULL,
            mode            TEXT DEFAULT 'guided',
            questions_json  TEXT,
            passed          INTEGER DEFAULT 0,
            score           INTEGER,
            created_at      TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (error_id) REFERENCES errors(id) ON DELETE CASCADE
        );
    ''')
    db.commit()
    db.close()


# ═══════════ 错题 CRUD ═══════════

def add_error(question_text, ocr_text='', ocr_confidence=0.0,
              ai_subject='', ai_chapter='', ai_topics='', ai_difficulty='',
              subject='', chapter='', topics='',
              answer_text='', reference_answer='', image_path='', image_desc='', error_reason=''):
    db = get_db()
    db.execute('''
        INSERT INTO errors (question_text, ocr_text, ocr_confidence,
            ai_subject, ai_chapter, ai_topics, ai_difficulty,
            subject, chapter, topics,
            answer_text, reference_answer, image_path, image_desc, error_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (question_text, ocr_text, ocr_confidence,
          ai_subject, ai_chapter, ai_topics, ai_difficulty,
          subject, chapter, topics,
          answer_text, reference_answer, image_path, image_desc, error_reason))
    db.commit()
    eid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return eid


def update_error(eid, **kwargs):
    """更新错题字段。kwargs 可以是任何字段名"""
    allowed = ['question_text','answer_text','subject','chapter','topics',
               'error_reason','mastered','reviewed_at','image_path']
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    sets = ', '.join(f'{k}=?' for k in updates)
    db = get_db()
    db.execute(f'UPDATE errors SET {sets} WHERE id=?',
               list(updates.values()) + [eid])
    db.commit(); db.close()
    return True


def delete_error(eid):
    db = get_db()
    db.execute('DELETE FROM errors WHERE id=?', (eid,))
    db.commit(); db.close()


def get_error(eid):
    db = get_db()
    row = db.execute('SELECT * FROM errors WHERE id=?', (eid,)).fetchone()
    db.close()
    return dict(row) if row else None


def list_errors(subject='', chapter='', mastered=None, search='',
                page=1, limit=20, sort='created_at', order='DESC'):
    """浏览错题列表，支持筛选、搜索、分页、排序"""
    db = get_db()
    conditions = []
    params = []

    if subject:
        conditions.append('subject=?'); params.append(subject)
    if chapter:
        conditions.append('chapter=?'); params.append(chapter)
    if mastered is not None and mastered != '':
        conditions.append('mastered=?'); params.append(int(mastered))
    if search:
        conditions.append('question_text LIKE ?'); params.append(f'%{search}%')

    where = ' AND '.join(conditions) if conditions else '1=1'
    total = db.execute(f'SELECT COUNT(*) FROM errors WHERE {where}', params).fetchone()[0]

    allowed_sort = ['created_at','reviewed_at','mastered']
    if sort not in allowed_sort: sort = 'created_at'
    if order.upper() not in ('ASC','DESC'): order = 'DESC'

    offset = (page - 1) * limit
    rows = db.execute(
        f'SELECT * FROM errors WHERE {where} ORDER BY {sort} {order} LIMIT ? OFFSET ?',
        params + [limit, offset]
    ).fetchall()
    db.close()

    return {
        'items': [dict(r) for r in rows],
        'total': total,
        'page': page,
        'pages': max(1, (total + limit - 1) // limit)
    }


# ═══════════ 复习记录 ═══════════

def add_review(error_id, mode='guided', questions=None, passed=False, score=0):
    db = get_db()
    db.execute('''
        INSERT INTO reviews (error_id, mode, questions_json, passed, score)
        VALUES (?, ?, ?, ?, ?)
    ''', (error_id, mode, json.dumps(questions or [], ensure_ascii=False),
          int(passed), score))
    db.commit()
    eid = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    # 更新最近复习时间
    db.execute("UPDATE errors SET reviewed_at=datetime('now','localtime') WHERE id=?",
               (error_id,))
    if passed:
        db.execute("UPDATE errors SET mastered=1 WHERE id=?", (error_id,))
    db.commit(); db.close()
    return eid


def get_reviews(error_id):
    db = get_db()
    rows = db.execute(
        'SELECT * FROM reviews WHERE error_id=? ORDER BY created_at DESC',
        (error_id,)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


# ═══════════ 统计 ═══════════

def get_stats():
    db = get_db()
    total = db.execute('SELECT COUNT(*) FROM errors').fetchone()[0]
    mastered = db.execute('SELECT COUNT(*) FROM errors WHERE mastered=1').fetchone()[0]

    # 学科分布
    subjects = {}
    for row in db.execute('''
        SELECT subject, COUNT(*) as cnt FROM errors
        WHERE subject != '' GROUP BY subject
    '''):
        subjects[row['subject']] = row['cnt']

    # 章节薄弱排行
    chapters = []
    for row in db.execute('''
        SELECT chapter, COUNT(*) as cnt FROM errors
        WHERE chapter != '' AND mastered=0
        GROUP BY chapter ORDER BY cnt DESC LIMIT 10
    '''):
        chapters.append({'chapter': row['chapter'], 'unmastered': row['cnt']})

    db.close()

    return {
        'total': total,
        'mastered': mastered,
        'mastered_rate': round(mastered / total, 2) if total > 0 else 0,
        'subjects': subjects,
        'weak_chapters': chapters
    }


# 启动时自动建表
init_db()
