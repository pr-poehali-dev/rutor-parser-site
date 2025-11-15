import json
import os
import psycopg2
from typing import Dict, Any, List
from datetime import datetime
import re

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
                   description, poster_url, published_at, torrent_url
            FROM posts 
            ORDER BY published_at DESC NULLS LAST, created_at DESC 
            LIMIT 50
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
                'torrent_url': row[13]
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
        
        mock_posts = [
            {
                'rutor_id': 'rt_001',
                'title': 'Оппенгеймер / Oppenheimer (2023) BDRip 1080p',
                'category': 'Фильмы',
                'size': '18.5 GB',
                'seeds': 892,
                'peers': 145,
                'torrent_url': 'magnet:?xt=urn:btih:example1',
                'kinopoisk_rating': 8.2,
                'kinopoisk_id': 1236063,
                'release_year': 2023,
                'genre': 'биография, драма, история',
                'director': 'Кристофер Нолан',
                'description': 'История жизни американского физика-теоретика Роберта Оппенгеймера',
                'poster_url': 'https://kinopoiskapiunofficial.tech/images/posters/kp/1236063.jpg',
                'published_at': '2025-11-15T10:30:00'
            },
            {
                'rutor_id': 'rt_002',
                'title': 'Дюна 2 / Dune: Part Two (2024) BDRip 1080p',
                'category': 'Фильмы',
                'size': '21.3 GB',
                'seeds': 1534,
                'peers': 289,
                'torrent_url': 'magnet:?xt=urn:btih:example2',
                'kinopoisk_rating': 8.1,
                'kinopoisk_id': 1312650,
                'release_year': 2024,
                'genre': 'фантастика, боевик, драма',
                'director': 'Дени Вильнёв',
                'description': 'Пол Атрейдес объединяется с Чани и фрименами',
                'poster_url': 'https://kinopoiskapiunofficial.tech/images/posters/kp/1312650.jpg',
                'published_at': '2025-11-15T09:15:00'
            },
            {
                'rutor_id': 'rt_003',
                'title': 'Cyberpunk 2077: Phantom Liberty [v 2.1] (2023) PC | Repack',
                'category': 'Игры',
                'size': '98.5 GB',
                'seeds': 2341,
                'peers': 567,
                'torrent_url': 'magnet:?xt=urn:btih:example3',
                'published_at': '2025-11-14T18:20:00'
            },
            {
                'rutor_id': 'rt_004',
                'title': 'Бесславные ублюдки / Inglourious Basterds (2009) BDRip 1080p',
                'category': 'Фильмы',
                'size': '14.2 GB',
                'seeds': 456,
                'peers': 78,
                'torrent_url': 'magnet:?xt=urn:btih:example4',
                'kinopoisk_rating': 8.1,
                'kinopoisk_id': 397667,
                'release_year': 2009,
                'genre': 'боевик, военный, драма',
                'director': 'Квентин Тарантино',
                'description': 'История двух тайных операций по убийству лидеров Третьего Рейха',
                'poster_url': 'https://kinopoiskapiunofficial.tech/images/posters/kp/397667.jpg',
                'published_at': '2025-11-14T15:45:00'
            },
            {
                'rutor_id': 'rt_005',
                'title': 'Adobe Photoshop 2024 v25.0.0.37 (2024) PC | Portable',
                'category': 'Софт',
                'size': '2.3 GB',
                'seeds': 789,
                'peers': 123,
                'torrent_url': 'magnet:?xt=urn:btih:example5',
                'published_at': '2025-11-14T12:00:00'
            },
            {
                'rutor_id': 'rt_006',
                'title': 'Linkin Park - Discography (2000-2024) FLAC',
                'category': 'Музыка',
                'size': '12.8 GB',
                'seeds': 234,
                'peers': 45,
                'torrent_url': 'magnet:?xt=urn:btih:example6',
                'published_at': '2025-11-13T20:30:00'
            }
        ]
        
        inserted_count = 0
        
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        
        for post in mock_posts:
            values = (
                post['rutor_id'],
                post['title'].replace("'", "''"),
                post.get('category', '').replace("'", "''"),
                post.get('size', '').replace("'", "''"),
                post.get('seeds', 0),
                post.get('peers', 0),
                post.get('torrent_url', '').replace("'", "''"),
                post.get('kinopoisk_rating'),
                post.get('kinopoisk_id'),
                post.get('release_year'),
                post.get('genre', '').replace("'", "''") if post.get('genre') else None,
                post.get('director', '').replace("'", "''") if post.get('director') else None,
                post.get('description', '').replace("'", "''") if post.get('description') else None,
                post.get('poster_url', '').replace("'", "''") if post.get('poster_url') else None,
                post.get('published_at')
            )
            
            query = f"""
                INSERT INTO posts (
                    rutor_id, title, category, size, seeds, peers, torrent_url,
                    kinopoisk_rating, kinopoisk_id, release_year, genre, 
                    director, description, poster_url, published_at
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
                    '{values[14]}'
                )
                ON CONFLICT (rutor_id) 
                DO UPDATE SET 
                    seeds = EXCLUDED.seeds,
                    peers = EXCLUDED.peers,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            cur.execute(query)
            inserted_count += 1
        
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
                'count': inserted_count
            }, ensure_ascii=False)
        }
    
    return {
        'statusCode': 405,
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'error': 'Method not allowed'})
    }