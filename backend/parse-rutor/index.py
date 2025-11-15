import json
import os
import psycopg2
from typing import Dict, Any, List
from datetime import datetime, timedelta
import re
import urllib.request
import urllib.parse
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

def extract_year(title: str) -> int:
    matches = re.findall(r'\((\d{4})\)', title)
    if matches:
        year = int(matches[-1])
        if 1900 <= year <= 2025:
            return year
    return None

def get_kinopoisk_info(title: str, year: int, api_key: str) -> dict:
    if not api_key:
        return {}
    
    clean_title = re.sub(r'\(.*?\)', '', title)
    clean_title = re.sub(r'\[.*?\]', '', clean_title)
    clean_title = clean_title.split('/')[0].strip()
    
    try:
        search_url = f"https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword?keyword={urllib.parse.quote(clean_title)}"
        req = urllib.request.Request(search_url, headers={'X-API-KEY': api_key})
        
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            films = data.get('films', [])
            
            for film in films[:3]:
                film_year = film.get('year')
                if year and film_year and abs(int(film_year) - year) <= 1:
                    film_id = film.get('filmId')
                    
                    detail_url = f"https://kinopoiskapiunofficial.tech/api/v2.2/films/{film_id}"
                    req2 = urllib.request.Request(detail_url, headers={'X-API-KEY': api_key})
                    
                    with urllib.request.urlopen(req2, timeout=5) as resp2:
                        details = json.loads(resp2.read().decode())
                        
                        genres = ', '.join([g.get('genre', '') for g in details.get('genres', [])[:3]])
                        directors = [p.get('nameRu', '') or p.get('nameEn', '') 
                                   for p in details.get('staff', []) if p.get('professionKey') == 'DIRECTOR']
                        
                        return {
                            'kinopoisk_id': film_id,
                            'kinopoisk_url': f"https://www.kinopoisk.ru/film/{film_id}/",
                            'kinopoisk_rating': details.get('ratingKinopoisk'),
                            'genre': genres,
                            'director': directors[0] if directors else None,
                            'description': details.get('description', '')[:500],
                            'poster_url': details.get('posterUrl'),
                            'release_year': details.get('year')
                        }
    except Exception as e:
        print(f"Kinopoisk API error: {e}")
    
    return {}

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Parse rutor.info posts and store in database with Kinopoisk data
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
        kinopoisk_key = os.environ.get('KINOPOISK_API_KEY', '')
        
        all_parsed_posts = []
        two_days_ago = datetime.now() - timedelta(days=2)
        
        for page in range(0, 15):
            try:
                url = f"http://rutor.info/browse/{page}/0/000/0"
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                with urllib.request.urlopen(req, timeout=10) as response:
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
                print(f"Error parsing page {page}: {e}")
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
            
            kp_info = {}
            if kinopoisk_key and category == 'Фильмы':
                kp_info = get_kinopoisk_info(post['title'], year, kinopoisk_key)
            
            published_at = post.get('parsed_date', datetime.now()).isoformat()
            
            values = (
                str(post['rutor_id']).replace("'", "''"),
                post['title'].replace("'", "''"),
                category.replace("'", "''") if category else '',
                post.get('size', '').replace("'", "''"),
                post.get('seeds', 0),
                post.get('peers', 0),
                post.get('torrent_url', '').replace("'", "''"),
                kp_info.get('kinopoisk_rating'),
                kp_info.get('kinopoisk_id'),
                kp_info.get('release_year') or year,
                kp_info.get('genre', '').replace("'", "''") if kp_info.get('genre') else None,
                kp_info.get('director', '').replace("'", "''") if kp_info.get('director') else None,
                kp_info.get('description', '').replace("'", "''") if kp_info.get('description') else None,
                kp_info.get('poster_url', '').replace("'", "''") if kp_info.get('poster_url') else None,
                kp_info.get('kinopoisk_url', '').replace("'", "''") if kp_info.get('kinopoisk_url') else None,
                published_at
            )
            
            query = f"""
                INSERT INTO posts (
                    rutor_id, title, category, size, seeds, peers, torrent_url,
                    kinopoisk_rating, kinopoisk_id, release_year, genre, 
                    director, description, poster_url, kinopoisk_url, published_at
                ) VALUES (
                    '{values[0]}', '{values[1]}', '{values[2]}', '{values[3]}', 
                    {values[4]}, {values[5]}, '{values[6]}',
                    {values[7] if values[7] is not None else 'NULL'}, 
                    {values[8] if values[8] is not None else 'NULL'}, 
                    {values[9] if values[9] is not None else 'NULL'},
                    {'NULL' if values[10] is None else "'" + values[10] + "'"},
                    {'NULL' if values[11] is None else "'" + values[11] + "'"},
                    {'NULL' if values[12] is None else "'" + values[12] + "'"},
                    {'NULL' if values[13] is None else "'" + values[13] + "'"},
                    {'NULL' if values[14] is None else "'" + values[14] + "'"},
                    '{values[15]}'
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
                print(f"Error inserting post: {e}")
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
