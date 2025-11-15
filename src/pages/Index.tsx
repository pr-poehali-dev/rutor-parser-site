import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import { useToast } from '@/hooks/use-toast';

interface Post {
  id: string;
  title: string;
  category: string;
  size: string;
  seeds: number;
  peers: number;
  kinopoisk_rating?: number | null;
  release_year?: number | null;
  genre?: string | null;
  director?: string | null;
  description?: string | null;
  poster_url?: string | null;
  published_at?: string | null;
  torrent_url?: string | null;
}

const API_URL = 'https://functions.poehali.dev/a6c59edf-b051-497f-bef2-42f238045c58';
const categories = ['Все', 'Фильмы', 'Сериалы', 'Игры', 'Софт', 'Музыка'];

const Index = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('Все');
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const { toast } = useToast();

  const fetchPosts = async () => {
    setLoading(true);
    try {
      const response = await fetch(API_URL);
      const data = await response.json();
      setPosts(data.posts || []);
    } catch (error) {
      toast({
        title: 'Ошибка загрузки',
        description: 'Не удалось загрузить посты',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  const updatePosts = async () => {
    setUpdating(true);
    try {
      const response = await fetch(API_URL, { method: 'POST' });
      const data = await response.json();
      
      toast({
        title: 'Обновлено!',
        description: `Добавлено/обновлено постов: ${data.count}`
      });
      
      await fetchPosts();
    } catch (error) {
      toast({
        title: 'Ошибка обновления',
        description: 'Не удалось обновить базу',
        variant: 'destructive'
      });
    } finally {
      setUpdating(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, []);

  const filteredPosts = posts.filter(post => {
    const matchesSearch = post.title.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'Все' || post.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return 'Неизвестно';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <header className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center">
                <Icon name="Radio" size={24} className="text-primary-foreground" />
              </div>
              <h1 className="text-3xl font-bold text-foreground">Rutor Агрегатор</h1>
            </div>
            
            <Button 
              onClick={updatePosts} 
              disabled={updating}
              className="bg-primary hover:bg-primary/90"
            >
              {updating ? (
                <>
                  <Icon name="Loader2" size={16} className="mr-2 animate-spin" />
                  Обновление...
                </>
              ) : (
                <>
                  <Icon name="RefreshCw" size={16} className="mr-2" />
                  Обновить базу
                </>
              )}
            </Button>
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

        {loading ? (
          <div className="text-center py-16">
            <Icon name="Loader2" size={48} className="mx-auto text-primary animate-spin mb-4" />
            <p className="text-lg text-muted-foreground">Загрузка постов...</p>
          </div>
        ) : (
          <div className="grid gap-4 animate-fade-in">
            {filteredPosts.length > 0 ? (
              filteredPosts.map((post) => (
                <Card
                  key={post.id}
                  className="p-5 bg-card border-border hover:border-primary/50 transition-all duration-200 hover:scale-[1.01] cursor-pointer"
                  onClick={() => post.torrent_url && window.open(post.torrent_url, '_blank')}
                >
                  <div className="flex gap-4">
                    {post.poster_url && (
                      <div className="shrink-0 hidden md:block">
                        <img 
                          src={post.poster_url} 
                          alt={post.title}
                          className="w-24 h-36 object-cover rounded-lg"
                        />
                      </div>
                    )}
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <h3 className="text-lg font-semibold text-foreground line-clamp-2">
                          {post.title}
                        </h3>
                        
                        {post.kinopoisk_rating && (
                          <div className="flex items-center gap-1 shrink-0 px-2 py-1 bg-primary/20 rounded-md">
                            <Icon name="Star" size={16} className="text-primary fill-primary" />
                            <span className="font-bold text-primary">{post.kinopoisk_rating}</span>
                          </div>
                        )}
                      </div>

                      {post.description && (
                        <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                          {post.description}
                        </p>
                      )}
                      
                      <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground mb-3">
                        <Badge variant="secondary" className="bg-muted text-foreground">
                          {post.category}
                        </Badge>
                        
                        {post.genre && (
                          <span className="flex items-center gap-1">
                            <Icon name="Film" size={14} />
                            {post.genre}
                          </span>
                        )}
                        
                        {post.director && (
                          <span className="flex items-center gap-1">
                            <Icon name="User" size={14} />
                            {post.director}
                          </span>
                        )}
                        
                        {post.release_year && (
                          <span className="flex items-center gap-1">
                            <Icon name="Calendar" size={14} />
                            {post.release_year}
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-4 text-sm">
                        <span className="flex items-center gap-1 text-muted-foreground">
                          <Icon name="HardDrive" size={14} />
                          {post.size}
                        </span>
                        
                        <div className="flex items-center gap-1 text-green-400">
                          <Icon name="ArrowUp" size={16} />
                          <span className="font-medium">{post.seeds}</span>
                        </div>
                        
                        <div className="flex items-center gap-1 text-red-400">
                          <Icon name="ArrowDown" size={16} />
                          <span className="font-medium">{post.peers}</span>
                        </div>
                        
                        <span className="flex items-center gap-1 text-muted-foreground ml-auto">
                          <Icon name="Clock" size={14} />
                          {formatDate(post.published_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                </Card>
              ))
            ) : (
              <div className="text-center py-16">
                <Icon name="Search" size={48} className="mx-auto text-muted-foreground mb-4" />
                <p className="text-lg text-muted-foreground">Ничего не найдено</p>
                <p className="text-sm text-muted-foreground mt-2">
                  {posts.length === 0 ? 'Нажмите "Обновить базу" для загрузки постов' : 'Попробуйте изменить запрос'}
                </p>
              </div>
            )}
          </div>
        )}

        {filteredPosts.length > 0 && (
          <div className="mt-8 text-center text-sm text-muted-foreground">
            Найдено постов: {filteredPosts.length} из {posts.length}
          </div>
        )}
      </div>
    </div>
  );
};

export default Index;
