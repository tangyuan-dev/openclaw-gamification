#!/usr/bin/env python3
"""
OpenClaw 游戏化学习系统 - 轻量级后端
使用 SQLite，无需额外配置
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import hashlib

DB_FILE = "gamification.db"

# 数据库初始化
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        github_id TEXT UNIQUE NOT NULL,
        github_username TEXT NOT NULL,
        email TEXT,
        avatar_url TEXT,
        points INTEGER DEFAULT 0,
        streak_days INTEGER DEFAULT 0,
        last_checkin DATE,
        level TEXT DEFAULT '新手',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # 活动表
    c.execute('''CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        activity_type TEXT NOT NULL,
        points INTEGER NOT NULL,
        description TEXT,
        source_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    
    # 成就表
    c.execute('''CREATE TABLE IF NOT EXISTS badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        icon TEXT NOT NULL,
        description TEXT,
        condition_type TEXT,
        condition_value INTEGER NOT NULL,
        points_reward INTEGER DEFAULT 0
    )''')
    
    # 用户成就表
    c.execute('''CREATE TABLE IF NOT EXISTS user_badges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        badge_id INTEGER,
        earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        card_generated INTEGER DEFAULT 0,
        card_pushed INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(badge_id) REFERENCES badges(id),
        UNIQUE(user_id, badge_id)
    )''')
    
    # 成就卡片表
    c.execute('''CREATE TABLE IF NOT EXISTS cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        badge_id INTEGER,
        card_type TEXT,
        image_url TEXT,
        push_status TEXT DEFAULT 'pending',
        push_channel TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        sent_at TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(badge_id) REFERENCES badges(id)
    )''')
    
    # 初始化成就数据
    badges = [
        ('新手', '🌱', '加入学习', 'points', 10, 0),
        ('学徒', '📖', '完成入门', 'points', 50, 10),
        ('开发者', '💻', '首次实战', 'points', 200, 20),
        ('坚持者', '🔥', '连续打卡', 'streak', 7, 30),
        ('修复者', '🐛', '提交Bug', 'activities', 1, 20),
        ('作者', '📝', '贡献教程', 'pr', 1, 50),
        ('导师', '🎓', '帮助他人', 'help', 10, 100),
        ('大师', '🏆', '排行榜顶尖', 'points', 1000, 200),
        ('传奇', '🌟', '特殊贡献', 'special', 1, 500),
    ]
    
    for badge in badges:
        c.execute('INSERT OR IGNORE INTO badges (name, icon, description, condition_type, condition_value, points_reward) VALUES (?, ?, ?, ?, ?, ?)', badge)
    
    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化完成: {DB_FILE}")

# 获取用户
def get_user(github_username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE github_username = ?', (github_username,))
    user = c.fetchone()
    conn.close()
    return user

# 创建用户
def create_user(github_id, github_username, email='', avatar_url=''):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (github_id, github_username, email, avatar_url) VALUES (?, ?, ?, ?)',
                  (github_id, github_username, email, avatar_url))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return get_user(github_username)[0]

# 记录活动
def record_activity(github_username, activity_type, points, description='', source_url=''):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 获取用户
    user = get_user(github_username)
    if not user:
        conn.close()
        return None
    
    user_id = user[0]
    
    # 记录活动
    c.execute('INSERT INTO activities (user_id, activity_type, points, description, source_url) VALUES (?, ?, ?, ?, ?)',
              (user_id, activity_type, points, description, source_url))
    
    # 更新用户积分
    c.execute('UPDATE users SET points = points + ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
              (points, user_id))
    
    conn.commit()
    conn.close()
    
    # 检查成就
    check_achievements(user_id)
    
    return user_id

# 检查成就
def check_achievements(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 获取用户信息
    c.execute('SELECT points, streak_days FROM users WHERE id = ?', (user_id,))
    user_data = c.fetchone()
    if not user_data:
        conn.close()
        return []
    
    points, streak = user_data
    
    # 获取所有成就
    c.execute('SELECT * FROM badges')
    all_badges = c.fetchall()
    
    # 获取已获得的成就
    c.execute('SELECT badge_id FROM user_badges WHERE user_id = ?', (user_id,))
    earned = [row[0] for row in c.fetchall()]
    
    new_badges = []
    for badge in all_badges:
        badge_id = badge[0]
        if badge_id in earned:
            continue
        
        condition_type = badge[4]
        condition_value = badge[5]
        
        # 检查是否达成
        earned_badge = False
        if condition_type == 'points' and points >= condition_value:
            earned_badge = True
        elif condition_type == 'streak' and streak >= condition_value:
            earned_badge = True
        
        if earned_badge:
            # 授予成就
            c.execute('INSERT INTO user_badges (user_id, badge_id) VALUES (?, ?)', (user_id, badge_id))
            
            # 更新等级
            level = get_level(points)
            c.execute('UPDATE users SET level = ? WHERE id = ?', (level, user_id))
            
            new_badges.append(badge)
            
            # 生成卡片
            c.execute('INSERT INTO cards (user_id, badge_id, card_type, push_status) VALUES (?, ?, ?, ?)',
                      (user_id, badge_id, 'achievement', 'pending'))
    
    conn.commit()
    conn.close()
    
    return new_badges

# 获取等级
def get_level(points):
    if points >= 1000: return '🏆 大师'
    if points >= 500: return '🎓 导师'
    if points >= 200: return '💻 开发者'
    if points >= 50: return '📖 学徒'
    return '🌱 新手'

# 获取排行榜
def get_leaderboard(limit=10):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT github_username, points, streak_days, level FROM users ORDER BY points DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

# 获取用户详情
def get_user_detail(github_username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('SELECT * FROM users WHERE github_username = ?', (github_username,))
    user = c.fetchone()
    
    if not user:
        conn.close()
        return None
    
    # 获取成就
    c.execute('''SELECT b.name, b.icon, b.description, ub.earned_at 
                 FROM user_badges ub 
                 JOIN badges b ON ub.badge_id = b.id 
                 WHERE ub.user_id = ?''', (user[0],))
    badges = c.fetchall()
    
    # 获取最近活动
    c.execute('SELECT activity_type, points, description, created_at FROM activities WHERE user_id = ? ORDER BY created_at DESC LIMIT 10',
              (user[0],))
    activities = c.fetchall()
    
    conn.close()
    
    return {
        'user': user,
        'badges': badges,
        'activities': activities
    }

# HTTP 处理
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        if path == '/api/health':
            self.send_json({'status': 'ok'})
        elif path == '/api/leaderboard':
            leaderboard = get_leaderboard()
            self.send_json({'leaderboard': leaderboard})
        elif path.startswith('/api/user/'):
            username = path.split('/')[-1]
            user = get_user_detail(username)
            if user:
                self.send_json(user)
            else:
                self.send_error(404, 'User not found')
        else:
            self.send_error(404, 'Not found')
    
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        data = parse_qs(body)
        
        if path == '/api/track':
            username = data.get('username', [''])[0]
            activity_type = data.get('type', ['unknown'])[0]
            points = int(data.get('points', [0])[0])
            description = data.get('description', [''])[0]
            source_url = data.get('url', [''])[0]
            
            record_activity(username, activity_type, points, description, source_url)
            self.send_json({'status': 'ok'})
        elif path == '/api/users/register':
            github_id = data.get('github_id', [''])[0]
            username = data.get('username', [''])[0]
            user_id = create_user(github_id, username)
            self.send_json({'user_id': user_id})
        else:
            self.send_error(404, 'Not found')
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

def run_server(port=3000):
    init_db()
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f"🚀 服务启动: http://localhost:{port}")
    server.serve_forever()

if __name__ == '__main__':
    run_server()
