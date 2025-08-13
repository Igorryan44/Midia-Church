"""
Carregador de dados da Bíblia usando arquivos JSON completos
"""
import json
import os
from typing import Dict, List, Optional, Tuple
from app.database.local_connection import db_manager

class BibleLoader:
    """Carregador de dados da Bíblia"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'bible_data')
        self.available_versions = ['nvi', 'acf', 'aa']
        self.bible_data = {}
        
    def load_bible_version(self, version: str = 'nvi') -> bool:
        """Carrega uma versão específica da Bíblia"""
        if version not in self.available_versions:
            return False
            
        file_path = os.path.join(self.data_dir, f'{version}.json')
        if not os.path.exists(file_path):
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                self.bible_data[version] = json.load(f)
            return True
        except Exception as e:
            print(f"Erro ao carregar {version}: {e}")
            return False
    
    def get_books(self, version: str = 'nvi') -> List[Dict]:
        """Retorna lista de livros da Bíblia"""
        if version not in self.bible_data:
            if not self.load_bible_version(version):
                return []
        
        books = []
        for book_data in self.bible_data[version]:
            books.append({
                'name': book_data['name'],
                'abbrev': book_data['abbrev'],
                'chapters': len(book_data['chapters']),
                'testament': book_data.get('testament', 'Antigo' if len(books) < 39 else 'Novo')
            })
        return books
    
    def get_chapter(self, book_name: str, chapter: int, version: str = 'nvi') -> Optional[List[str]]:
        """Retorna os versículos de um capítulo específico"""
        if version not in self.bible_data:
            if not self.load_bible_version(version):
                return None
        
        for book_data in self.bible_data[version]:
            if book_data['name'].lower() == book_name.lower() or book_data['abbrev'].lower() == book_name.lower():
                if 1 <= chapter <= len(book_data['chapters']):
                    return book_data['chapters'][chapter - 1]
        return None
    
    def get_verse(self, book_name: str, chapter: int, verse: int, version: str = 'nvi') -> Optional[str]:
        """Retorna um versículo específico"""
        chapter_verses = self.get_chapter(book_name, chapter, version)
        if chapter_verses and 1 <= verse <= len(chapter_verses):
            return chapter_verses[verse - 1]
        return None
    
    def search_verses(self, query: str, version: str = 'nvi', limit: int = 50) -> List[Dict]:
        """Busca versículos que contenham o texto especificado"""
        if version not in self.bible_data:
            if not self.load_bible_version(version):
                return []
        
        results = []
        query_lower = query.lower()
        
        for book_data in self.bible_data[version]:
            book_name = book_data['name']
            
            for chapter_idx, chapter_verses in enumerate(book_data['chapters']):
                chapter_num = chapter_idx + 1
                
                for verse_idx, verse_text in enumerate(chapter_verses):
                    verse_num = verse_idx + 1
                    
                    if query_lower in verse_text.lower():
                        results.append({
                            'book': book_name,
                            'chapter': chapter_num,
                            'verse': verse_num,
                            'text': verse_text,
                            'reference': f"{book_name} {chapter_num}:{verse_num}"
                        })
                        
                        if len(results) >= limit:
                            return results
        
        return results
    
    def get_book_info(self, book_name: str, version: str = 'nvi') -> Optional[Dict]:
        """Retorna informações sobre um livro específico"""
        if version not in self.bible_data:
            if not self.load_bible_version(version):
                return None
        
        for book_data in self.bible_data[version]:
            if book_data['name'].lower() == book_name.lower() or book_data['abbrev'].lower() == book_name.lower():
                return {
                    'name': book_data['name'],
                    'abbrev': book_data['abbrev'],
                    'chapters': len(book_data['chapters']),
                    'total_verses': sum(len(chapter) for chapter in book_data['chapters']),
                    'testament': book_data.get('testament', 'Antigo' if book_data['name'] in ['Gênesis', 'Êxodo'] else 'Novo')
                }
        return None
    
    def save_to_database(self, version: str = 'nvi') -> bool:
        """Salva os dados da Bíblia no banco de dados"""
        if version not in self.bible_data:
            if not self.load_bible_version(version):
                return False
        
        try:
            # Criar tabelas se não existirem
            db_manager.execute_query("""
                CREATE TABLE IF NOT EXISTS bible_books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    abbrev TEXT NOT NULL,
                    testament TEXT NOT NULL,
                    book_order INTEGER NOT NULL,
                    chapters_count INTEGER NOT NULL,
                    version TEXT NOT NULL DEFAULT 'nvi'
                )
            """)
            
            db_manager.execute_query("""
                CREATE TABLE IF NOT EXISTS bible_verses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_name TEXT NOT NULL,
                    chapter INTEGER NOT NULL,
                    verse INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    version TEXT NOT NULL DEFAULT 'nvi',
                    UNIQUE(book_name, chapter, verse, version)
                )
            """)
            
            # Limpar dados existentes da versão
            db_manager.execute_query("DELETE FROM bible_books WHERE version = ?", (version,))
            db_manager.execute_query("DELETE FROM bible_verses WHERE version = ?", (version,))
            
            # Inserir livros
            for order, book_data in enumerate(self.bible_data[version], 1):
                testament = 'Antigo' if order <= 39 else 'Novo'
                db_manager.execute_query("""
                    INSERT INTO bible_books (name, abbrev, testament, book_order, chapters_count, version)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (book_data['name'], book_data['abbrev'], testament, order, len(book_data['chapters']), version))
                
                # Inserir versículos
                for chapter_idx, chapter_verses in enumerate(book_data['chapters']):
                    chapter_num = chapter_idx + 1
                    for verse_idx, verse_text in enumerate(chapter_verses):
                        verse_num = verse_idx + 1
                        db_manager.execute_query("""
                            INSERT OR REPLACE INTO bible_verses (book_name, chapter, verse, text, version)
                            VALUES (?, ?, ?, ?, ?)
                        """, (book_data['name'], chapter_num, verse_num, verse_text, version))
            
            return True
            
        except Exception as e:
            print(f"Erro ao salvar no banco: {e}")
            return False
    
    def get_random_verse(self, version: str = 'nvi') -> Optional[Dict]:
        """Retorna um versículo aleatório"""
        import random
        
        if version not in self.bible_data:
            if not self.load_bible_version(version):
                return None
        
        # Escolher livro aleatório
        book_data = random.choice(self.bible_data[version])
        
        # Escolher capítulo aleatório
        chapter_idx = random.randint(0, len(book_data['chapters']) - 1)
        chapter_verses = book_data['chapters'][chapter_idx]
        
        # Escolher versículo aleatório
        verse_idx = random.randint(0, len(chapter_verses) - 1)
        
        return {
            'book': book_data['name'],
            'chapter': chapter_idx + 1,
            'verse': verse_idx + 1,
            'text': chapter_verses[verse_idx],
            'reference': f"{book_data['name']} {chapter_idx + 1}:{verse_idx + 1}"
        }

# Instância global
bible_loader = BibleLoader()