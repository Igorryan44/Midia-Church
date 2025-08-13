"""
Carregador da Bíblia completa do repositório GitHub thiagobodruk/biblia
"""

import requests
import json
import os
import time
from pathlib import Path
from app.database.local_connection import db_manager
from app.data.bible_structure import BIBLE_BOOKS, BIBLE_VERSIONS
from sqlalchemy import text
import streamlit as st

class GitHubBibleLoader:
    def __init__(self):
        self.github_base_url = "https://raw.githubusercontent.com/thiagobodruk/biblia/master"
        self.data_dir = Path(__file__).parent / "bible_data"
        self.data_dir.mkdir(exist_ok=True)
        
        # Mapeamento das versões disponíveis no repositório
        self.available_versions = {
            'nvi': {
                'name': 'Nova Versão Internacional',
                'filename': 'json/nvi.json'
            },
            'acf': {
                'name': 'Almeida Corrigida e Fiel',
                'filename': 'json/acf.json'
            },
            'aa': {
                'name': 'Almeida Revisada Imprensa Bíblica',
                'filename': 'json/aa.json'
            }
        }
    
    def download_bible_version(self, version_code='nvi', progress_callback=None):
        """Baixa uma versão específica da Bíblia do GitHub"""
        try:
            if version_code not in self.available_versions:
                st.error(f"Versão '{version_code}' não disponível. Versões disponíveis: {list(self.available_versions.keys())}")
                return False
            
            version_info = self.available_versions[version_code]
            url = f"{self.github_base_url}/{version_info['filename']}"
            
            st.info(f"📥 Baixando {version_info['name']} do GitHub...")
            
            # Baixa o arquivo JSON
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            bible_data = response.json()
            
            # Salva localmente
            local_file = self.data_dir / f"github_bible_{version_code}.json"
            with open(local_file, 'w', encoding='utf-8') as f:
                json.dump(bible_data, f, ensure_ascii=False, indent=2)
            
            st.success(f"✅ {version_info['name']} baixada com sucesso!")
            
            # Processa e carrega no banco
            return self._process_github_bible_data(bible_data, version_code, progress_callback)
            
        except requests.RequestException as e:
            st.error(f"Erro ao baixar da internet: {str(e)}")
            return False
        except Exception as e:
            st.error(f"Erro inesperado: {str(e)}")
            return False
    
    def _process_github_bible_data(self, bible_data, version_code, progress_callback=None):
        """Processa os dados da Bíblia do formato GitHub para o formato do banco"""
        try:
            processed_verses = []
            total_books = len(bible_data)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Mapeamento de abreviações para códigos de livros
            abbrev_to_code = self._create_abbrev_mapping()
            
            for book_index, book_data in enumerate(bible_data):
                book_abbrev = book_data.get('abbrev', '').lower()
                book_name = book_data.get('book', '')
                chapters = book_data.get('chapters', [])
                
                status_text.text(f"Processando {book_name}...")
                
                # Encontra o código do livro
                book_code = abbrev_to_code.get(book_abbrev)
                if not book_code:
                    st.warning(f"Livro não mapeado: {book_abbrev} - {book_name}")
                    continue
                
                # Processa cada capítulo
                for chapter_index, chapter_verses in enumerate(chapters):
                    chapter_number = chapter_index + 1
                    
                    # Processa cada versículo
                    for verse_index, verse_text in enumerate(chapter_verses):
                        verse_number = verse_index + 1
                        
                        processed_verses.append({
                            'book_code': book_code,
                            'book_name': book_name,
                            'chapter': chapter_number,
                            'verse': verse_number,
                            'text': verse_text.strip(),
                            'version': version_code.upper()
                        })
                
                # Atualiza progresso
                progress = (book_index + 1) / total_books
                progress_bar.progress(progress)
            
            st.success(f"✅ {len(processed_verses)} versículos processados!")
            
            # Carrega no banco de dados
            return self._load_to_database(processed_verses, version_code, progress_callback)
            
        except Exception as e:
            st.error(f"Erro ao processar dados: {str(e)}")
            return False
    
    def _create_abbrev_mapping(self):
        """Cria mapeamento de abreviações para códigos de livros"""
        mapping = {
            # Antigo Testamento
            'gn': 'genesis', 'ex': 'exodus', 'lv': 'leviticus', 'nm': 'numbers', 'dt': 'deuteronomy',
            'js': 'joshua', 'jz': 'judges', 'rt': 'ruth', '1sm': '1samuel', '2sm': '2samuel',
            '1rs': '1kings', '2rs': '2kings', '1cr': '1chronicles', '2cr': '2chronicles',
            'ed': 'ezra', 'ne': 'nehemiah', 'et': 'esther', 'jó': 'job', 'sl': 'psalms',
            'pv': 'proverbs', 'ec': 'ecclesiastes', 'ct': 'song_of_solomon', 'is': 'isaiah',
            'jr': 'jeremiah', 'lm': 'lamentations', 'ez': 'ezekiel', 'dn': 'daniel',
            'os': 'hosea', 'jl': 'joel', 'am': 'amos', 'ob': 'obadiah', 'jn': 'jonah',
            'mq': 'micah', 'na': 'nahum', 'hc': 'habakkuk', 'sf': 'zephaniah',
            'ag': 'haggai', 'zc': 'zechariah', 'ml': 'malachi',
            
            # Novo Testamento
            'mt': 'matthew', 'mc': 'mark', 'lc': 'luke', 'jo': 'john', 'at': 'acts',
            'rm': 'romans', '1co': '1corinthians', '2co': '2corinthians', 'gl': 'galatians',
            'ef': 'ephesians', 'fp': 'philippians', 'cl': 'colossians', '1ts': '1thessalonians',
            '2ts': '2thessalonians', '1tm': '1timothy', '2tm': '2timothy', 'tt': 'titus',
            'fm': 'philemon', 'hb': 'hebrews', 'tg': 'james', '1pe': '1peter', '2pe': '2peter',
            '1jo': '1john', '2jo': '2john', '3jo': '3john', 'jd': 'jude', 'ap': 'revelation'
        }
        return mapping
    
    def _load_to_database(self, bible_data, version_code, progress_callback=None):
        """Carrega os dados processados no banco de dados"""
        try:
            with db_manager.get_db_session() as session:
                # Primeiro, carrega a estrutura dos livros se não existir
                self._ensure_books_structure(session)
                
                # Remove versículos existentes desta versão
                session.execute(text("DELETE FROM bible_verses WHERE version = :version"), 
                              {'version': version_code.upper()})
                
                total_verses = len(bible_data)
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Insere versículos em lotes para melhor performance
                batch_size = 1000
                for i in range(0, total_verses, batch_size):
                    batch = bible_data[i:i + batch_size]
                    
                    for verse in batch:
                        session.execute(text("""
                            INSERT INTO bible_verses (book_code, chapter, verse, text, version)
                            VALUES (:book_code, :chapter, :verse, :text, :version)
                        """), {
                            'book_code': verse['book_code'],
                            'chapter': verse['chapter'],
                            'verse': verse['verse'],
                            'text': verse['text'],
                            'version': verse['version']
                        })
                    
                    # Atualiza progresso
                    progress = min((i + batch_size) / total_verses, 1.0)
                    progress_bar.progress(progress)
                    status_text.text(f"Carregando versículos: {i + len(batch)}/{total_verses}")
                    
                    session.commit()
                
                session.commit()
                st.success(f"✅ {total_verses} versículos da versão {version_code.upper()} carregados com sucesso!")
                return True
                
        except Exception as e:
            st.error(f"Erro ao carregar no banco de dados: {str(e)}")
            return False
    
    def _ensure_books_structure(self, session):
        """Garante que a estrutura dos livros existe no banco"""
        try:
            # Verifica se já existem livros
            result = session.execute(text("SELECT COUNT(*) as count FROM bible_books")).fetchone()
            if result and result[0] > 0:
                return  # Já existem livros
            
            # Insere todos os livros
            for book_code, book_info in BIBLE_BOOKS.items():
                session.execute(text("""
                    INSERT OR IGNORE INTO bible_books (book_code, book_name, testament, book_order, chapters)
                    VALUES (:book_code, :book_name, :testament, :book_order, :chapters)
                """), {
                    'book_code': book_code,
                    'book_name': book_info['name'],
                    'testament': book_info['testament'],
                    'book_order': book_info['order'],
                    'chapters': book_info['chapters']
                })
            
            session.commit()
            
        except Exception as e:
            st.warning(f"Aviso ao carregar estrutura dos livros: {str(e)}")
    
    def check_available_versions(self):
        """Verifica quais versões estão disponíveis localmente e no banco"""
        try:
            with db_manager.get_db_session() as session:
                result = session.execute(text("""
                    SELECT version, COUNT(*) as verse_count 
                    FROM bible_verses 
                    GROUP BY version
                """)).fetchall()
                
                loaded_versions = {}
                for row in result:
                    version = row[0].lower()
                    if version in self.available_versions:
                        loaded_versions[version] = {
                            'name': self.available_versions[version]['name'],
                            'verse_count': row[1],
                            'status': 'loaded'
                        }
                
                # Adiciona versões não carregadas
                for version_code, version_info in self.available_versions.items():
                    if version_code not in loaded_versions:
                        loaded_versions[version_code] = {
                            'name': version_info['name'],
                            'verse_count': 0,
                            'status': 'not_loaded'
                        }
                
                return loaded_versions
                
        except Exception as e:
            st.error(f"Erro ao verificar versões: {str(e)}")
            return {}
    
    def load_all_versions(self, progress_callback=None):
        """Carrega todas as versões disponíveis"""
        success_count = 0
        total_versions = len(self.available_versions)
        
        for version_code in self.available_versions.keys():
            st.info(f"Carregando versão {version_code.upper()}...")
            if self.download_bible_version(version_code, progress_callback):
                success_count += 1
            time.sleep(1)  # Pausa entre downloads
        
        if success_count == total_versions:
            st.success(f"🎉 Todas as {total_versions} versões foram carregadas com sucesso!")
        else:
            st.warning(f"⚠️ {success_count}/{total_versions} versões carregadas com sucesso.")
        
        return success_count == total_versions