CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    category VARCHAR(50),
    size VARCHAR(50),
    seeds INTEGER DEFAULT 0,
    peers INTEGER DEFAULT 0,
    torrent_url TEXT,
    rutor_id VARCHAR(100) UNIQUE,
    
    kinopoisk_rating DECIMAL(3,1),
    kinopoisk_id INTEGER,
    release_year INTEGER,
    genre TEXT,
    director TEXT,
    description TEXT,
    poster_url TEXT,
    
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category);
CREATE INDEX IF NOT EXISTS idx_posts_published_at ON posts(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_rutor_id ON posts(rutor_id);
