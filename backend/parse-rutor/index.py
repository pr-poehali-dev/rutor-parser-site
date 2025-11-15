import json
import os
import psycopg2
from typing import Dict, Any
from datetime import datetime, timedelta
import re
import urllib.request
from html.parser import HTMLParser

class RutorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.posts = []
        self.current_post = None
        self.in_title_link = False
        self.in_date_cell = False
        self.in_table_row = False
        self.cell_index = 0
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == 'tr' and attrs_dict.get('class') in ['gai', 'tum']:
            self.in_table_row = True
            self.current_post = {'seeds': 0, 'peers': 0}
            self.cell_index = 0
            
        if self.in_table_row and tag == 'td':
            self.cell_index += 1
            if self.cell_index == 1:
                self.in_date_cell = True
            
        if self.in_table_row and tag == 'a' and self.cell_index == 2:
            href = attrs_dict.get('href', '')
            if href.startswith('/torrent/'):
                self.in_title_link = True
                self.current_post['rutor_id'] = href.split('/')[2]
                self.current_post['torrent_url'] = f"http://rutor.info{href}"
                
        if self.in_table_row and tag == 'span' and self.cell_index == 4:
            span_class = attrs_dict.get('class', '')
            if 'green' in span_class:
                self.current_post['seeds_next'] = True
            elif 'red' in span_class:
                self.current_post['peers_next'] = True
    
    def handle_data(self, data):
        if self.in_date_cell:
            date_str = data.strip()
            if date_str:
                self.current_post['date_str'] = date_str
            self.in_date_cell = False
            
        if self.in_title_link:
            self.current_post['title'] = data.strip()
            self.in_title_link = False
            
        if self.in_table_row and self.current_post:
            if self.cell_index == 3:
                self.current_post['size'] = data.strip()
            elif self.cell_index == 4:
                if self.current_post.get('seeds_next'):
                    try:
                        self.current_post['seeds'] = int(data.strip())
                    except:
                        pass
                    self.current_post['seeds_next'] = False
                elif self.current_post.get('peers_next'):
                    try:
                        self.current_post['peers'] = int(data.strip())
                    except:
                        pass
                    self.current_post['peers_next'] = False
    
    def handle_endtag(self, tag):
        if tag == 'tr' and self.in_table_row:
            if self.current_post and self.current_post.get('title'):
                self.posts.append(self.current_post)
            self.in_table_row = False
            self.current_post = None
            self.cell_index = 0

def parse_rutor_date(date_str: str) -> datetime:
    now = datetime.now()
    
    months_ru = {
        'Янв': 1, 'Фев': 2, 'Мар': 3, 'Апр': 4, 'Май': 5, 'Июн': 6,
        'Июл': 7, 'Авг': 8, 'Сен': 9, 'Окт': 10, 'Ноя': 11, 'Дек': 12
    }
    
    if 'Сегодня' in date_str or 'Вчера' in date_str:
        time_match = re.search(r'(\d{2}):(\d{2})', date_str)
        if time_match:
            hour, minute = int(time_match.group(1)), int(time_match.group(2))
            if 'Вчера' in date_str:
                return now.replace(hour=hour, minute=minute, second=0, microsecond=0) - timedelta(days=1)
            else:
                return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    date_match = re.search(r'(\d{2})\s+(\w{3})\s+(\d{2})', date_str)
    if date_match:
        day = int(date_match.group(1))
        month_str = date_match.group(2)
        year = 2000 + int(date_match.group(3))
        month = months_ru.get(month_str, 1)
        return datetime(year, month, day)
    
    return now

def categorize_post(title: str) -> str:
    title_lower = title.lower()
    
    movie_keywords = ['bdrip', 'webrip', 'hdrip', 'dvdrip', '1080p', '720p', '2160p', 'bluray', 'hdtv']
    series_keywords = ['s01', 's02', 's03', 's04', 's05', 's06', 's07', 's08', 's09', 's10', 
                       'season', 'сезон', 'серии', 'series', 'episodes']
    
    if any(kw in title_lower for kw in series_keywords):
        return 'Сериалы'
    elif any(kw in title_lower for kw in movie_keywords):
        return 'Фильмы'
    
    return None

def extract_year(title: str):
    matches = re.findall(r'\((\d{4})\)', title)
    if matches:
        year = int(matches[-1])
        if 1900 <= year <= 2025:
            return year
    return None

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Parse rutor.info posts and store in database
    Args: event - HTTP event; context - execution context
    Returns: HTTP response with parsed posts count
    '''
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    if method == 'GET':
        dsn = os.environ.get('DATABASE_URL')
        
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, title, category, size, seeds, peers, 
                   kinopoisk_rating, release_year, genre, director, 
                   description, poster_url, published_at, torrent_url, kinopoisk_url
            FROM posts 
            WHERE category IN ('Фильмы', 'Сериалы')
            ORDER BY published_at DESC NULLS LAST, created_at DESC 
            LIMIT 200
        """)
        
        rows = cur.fetchall()
        posts = []
        
        for row in rows:
            posts.append({
                'id': str(row[0]),
                'title': row[1],
                'category': row[2] or 'Другое',
                'size': row[3] or 'N/A',
                'seeds': row[4] or 0,
                'peers': row[5] or 0,
                'kinopoisk_rating': float(row[6]) if row[6] else None,
                'release_year': row[7],
                'genre': row[8],
                'director': row[9],
                'description': row[10],
                'poster_url': row[11],
                'published_at': row[12].isoformat() if row[12] else None,
                'torrent_url': row[13],
                'kinopoisk_url': row[14]
            })
        
        cur.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'posts': posts}, ensure_ascii=False)
        }
    
    if method == 'POST':
        dsn = os.environ.get('DATABASE_URL')
        
        all_parsed_posts = []
        two_days_ago = datetime.now() - timedelta(days=2)
        
        for page in range(0, 10):
            try:
                url = f"http://rutor.info/browse/{page}/0/000/0"
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0'
                })
                
                with urllib.request.urlopen(req, timeout=3) as response:
                    html = response.read().decode('utf-8', errors='ignore')
                    
                parser = RutorParser()
                parser.feed(html)
                
                for post in parser.posts:
                    if post.get('date_str'):
                        post_date = parse_rutor_date(post['date_str'])
                        if post_date >= two_days_ago:
                            post['parsed_date'] = post_date
                            all_parsed_posts.append(post)
                
            except Exception as e:
                print(f"Error page {page}: {e}")
                continue
        
        inserted_count = 0
        
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        
        for post in all_parsed_posts:
            if not post.get('title') or not post.get('rutor_id'):
                continue
            
            category = categorize_post(post['title'])
            if category not in ['Фильмы', 'Сериалы']:
                continue
            
            year = extract_year(post['title'])
            published_at = post.get('parsed_date', datetime.now()).isoformat()
            
            rutor_id = str(post['rutor_id']).replace("'", "''")
            title = post['title'].replace("'", "''")
            cat = category.replace("'", "''")
            size = post.get('size', '').replace("'", "''")
            seeds = post.get('seeds', 0)
            peers = post.get('peers', 0)
            torrent_url = post.get('torrent_url', '').replace("'", "''")
            
            query = f"""
                INSERT INTO posts (
                    rutor_id, title, category, size, seeds, peers, torrent_url,
                    release_year, published_at
                ) VALUES (
                    '{rutor_id}', '{title}', '{cat}', '{size}', 
                    {seeds}, {peers}, '{torrent_url}',
                    {year if year else 'NULL'},
                    '{published_at}'
                )
                ON CONFLICT (rutor_id) 
                DO UPDATE SET 
                    seeds = EXCLUDED.seeds,
                    peers = EXCLUDED.peers,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            try:
                cur.execute(query)
                inserted_count += 1
            except Exception as e:
                print(f"Insert error: {e}")
                continue
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Posts parsed and saved',
                'count': inserted_count,
                'parsed_total': len(all_parsed_posts)
            }, ensure_ascii=False)
        }
    
    return {
        'statusCode': 405,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'error': 'Method not allowed'})
    }
