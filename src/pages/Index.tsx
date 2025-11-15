import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

interface Post {
  id: string;
  title: string;
  category: string;
  size: string;
  seeds: number;
  peers: number;
  date: string;
  url: string;
}

const mockPosts: Post[] = [
  {
    id: '1',
    title: 'Великий уравнитель 3 / The Equalizer 3 (2023) BDRip 1080p',
    category: 'Фильмы',
    size: '14.8 GB',
    seeds: 245,
    peers: 12,
    date: '15 ноя 2025',
    url: '#'
  },
  {
    id: '2',
    title: 'Cyberpunk 2077: Phantom Liberty [v 2.1] (2023) PC | Repack',
    category: 'Игры',
    size: '98.5 GB',
    seeds: 892,
    peers: 156,
    date: '15 ноя 2025',
    url: '#'
  },
  {
    id: '3',
    title: 'Adobe Photoshop 2024 v25.0.0.37 (2024) PC | Portable',
    category: 'Софт',
    size: '2.3 GB',
    seeds: 543,
    peers: 89,
    date: '14 ноя 2025',
    url: '#'
  },
  {
    id: '4',
    title: 'Ходячие мертвецы / The Walking Dead [S01-11] (2010-2022) WEB-DL 1080p',
    category: 'Сериалы',
    size: '287.4 GB',
    seeds: 1234,
    peers: 456,
    date: '14 ноя 2025',
    url: '#'
  },
  {
    id: '5',
    title: 'Linkin Park - Discography (2000-2024) FLAC',
    category: 'Музыка',
    size: '12.8 GB',
    seeds: 678,
    peers: 34,
    date: '13 ноя 2025',
    url: '#'
  },
  {
    id: '6',
    title: 'Python для анализа данных. 3-е издание (2023) PDF',
    category: 'Софт',
    size: '45 MB',
    seeds: 321,
    peers: 21,
    date: '13 ноя 2025',
    url: '#'
  }
];

const categories = ['Все', 'Фильмы', 'Сериалы', 'Игры', 'Софт', 'Музыка'];

const Index = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('Все');

  const filteredPosts = mockPosts.filter(post => {
    const matchesSearch = post.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'Все' || post.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <header className="mb-12">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center">
              <Icon name="Radio" size={24} className="text-primary-foreground" />
            </div>
            <h1 className="text-3xl font-bold text-foreground">Rutor Агрегатор</h1>
          </div>
          
          <div className="relative">
            <Icon name="Search" size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Поиск по названию..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 h-12 bg-card border-border text-foreground placeholder:text-muted-foreground"
            />
          </div>
        </header>

        <div className="flex flex-wrap gap-2 mb-8">
          {categories.map((category) => (
            <Badge
              key={category}
              variant={selectedCategory === category ? 'default' : 'outline'}
              className={`cursor-pointer px-4 py-2 text-sm font-medium transition-all hover:scale-105 ${
                selectedCategory === category
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-card text-foreground border-border hover:bg-muted'
              }`}
              onClick={() => setSelectedCategory(category)}
            >
              {category}
            </Badge>
          ))}
        </div>

        <div className="grid gap-4 animate-fade-in">
          {filteredPosts.length > 0 ? (
            filteredPosts.map((post) => (
              <Card
                key={post.id}
                className="p-5 bg-card border-border hover:border-primary/50 transition-all duration-200 hover:scale-[1.01] cursor-pointer"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-foreground mb-2 line-clamp-2">
                      {post.title}
                    </h3>
                    <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                      <Badge variant="secondary" className="bg-muted text-foreground">
                        {post.category}
                      </Badge>
                      <span className="flex items-center gap-1">
                        <Icon name="HardDrive" size={14} />
                        {post.size}
                      </span>
                      <span className="flex items-center gap-1">
                        <Icon name="Calendar" size={14} />
                        {post.date}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4 text-sm shrink-0">
                    <div className="flex items-center gap-1 text-green-400">
                      <Icon name="ArrowUp" size={16} />
                      <span className="font-medium">{post.seeds}</span>
                    </div>
                    <div className="flex items-center gap-1 text-red-400">
                      <Icon name="ArrowDown" size={16} />
                      <span className="font-medium">{post.peers}</span>
                    </div>
                    <Icon name="ExternalLink" size={18} className="text-primary" />
                  </div>
                </div>
              </Card>
            ))
          ) : (
            <div className="text-center py-16">
              <Icon name="Search" size={48} className="mx-auto text-muted-foreground mb-4" />
              <p className="text-lg text-muted-foreground">Ничего не найдено</p>
              <p className="text-sm text-muted-foreground mt-2">Попробуйте изменить запрос</p>
            </div>
          )}
        </div>

        {filteredPosts.length > 0 && (
          <div className="mt-8 text-center text-sm text-muted-foreground">
            Найдено постов: {filteredPosts.length}
          </div>
        )}
      </div>
    </div>
  );
};

export default Index;
