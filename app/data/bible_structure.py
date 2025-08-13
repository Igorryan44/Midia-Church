"""
Estrutura e configuração da Bíblia
"""

# Versões disponíveis da Bíblia
BIBLE_VERSIONS = {
    'nvi': 'Nova Versão Internacional',
    'acf': 'Almeida Corrigida Fiel',
    'aa': 'Almeida Atualizada'
}

# Livros da Bíblia com informações básicas
BIBLE_BOOKS_INFO = {
    # Antigo Testamento
    'genesis': {'name': 'Gênesis', 'abbrev': 'Gn', 'testament': 'Antigo', 'order': 1},
    'exodus': {'name': 'Êxodo', 'abbrev': 'Ex', 'testament': 'Antigo', 'order': 2},
    'leviticus': {'name': 'Levítico', 'abbrev': 'Lv', 'testament': 'Antigo', 'order': 3},
    'numbers': {'name': 'Números', 'abbrev': 'Nm', 'testament': 'Antigo', 'order': 4},
    'deuteronomy': {'name': 'Deuteronômio', 'abbrev': 'Dt', 'testament': 'Antigo', 'order': 5},
    'joshua': {'name': 'Josué', 'abbrev': 'Js', 'testament': 'Antigo', 'order': 6},
    'judges': {'name': 'Juízes', 'abbrev': 'Jz', 'testament': 'Antigo', 'order': 7},
    'ruth': {'name': 'Rute', 'abbrev': 'Rt', 'testament': 'Antigo', 'order': 8},
    '1samuel': {'name': '1 Samuel', 'abbrev': '1Sm', 'testament': 'Antigo', 'order': 9},
    '2samuel': {'name': '2 Samuel', 'abbrev': '2Sm', 'testament': 'Antigo', 'order': 10},
    '1kings': {'name': '1 Reis', 'abbrev': '1Rs', 'testament': 'Antigo', 'order': 11},
    '2kings': {'name': '2 Reis', 'abbrev': '2Rs', 'testament': 'Antigo', 'order': 12},
    '1chronicles': {'name': '1 Crônicas', 'abbrev': '1Cr', 'testament': 'Antigo', 'order': 13},
    '2chronicles': {'name': '2 Crônicas', 'abbrev': '2Cr', 'testament': 'Antigo', 'order': 14},
    'ezra': {'name': 'Esdras', 'abbrev': 'Ed', 'testament': 'Antigo', 'order': 15},
    'nehemiah': {'name': 'Neemias', 'abbrev': 'Ne', 'testament': 'Antigo', 'order': 16},
    'esther': {'name': 'Ester', 'abbrev': 'Et', 'testament': 'Antigo', 'order': 17},
    'job': {'name': 'Jó', 'abbrev': 'Jó', 'testament': 'Antigo', 'order': 18},
    'psalms': {'name': 'Salmos', 'abbrev': 'Sl', 'testament': 'Antigo', 'order': 19},
    'proverbs': {'name': 'Provérbios', 'abbrev': 'Pv', 'testament': 'Antigo', 'order': 20},
    'ecclesiastes': {'name': 'Eclesiastes', 'abbrev': 'Ec', 'testament': 'Antigo', 'order': 21},
    'song': {'name': 'Cânticos', 'abbrev': 'Ct', 'testament': 'Antigo', 'order': 22},
    'isaiah': {'name': 'Isaías', 'abbrev': 'Is', 'testament': 'Antigo', 'order': 23},
    'jeremiah': {'name': 'Jeremias', 'abbrev': 'Jr', 'testament': 'Antigo', 'order': 24},
    'lamentations': {'name': 'Lamentações', 'abbrev': 'Lm', 'testament': 'Antigo', 'order': 25},
    'ezekiel': {'name': 'Ezequiel', 'abbrev': 'Ez', 'testament': 'Antigo', 'order': 26},
    'daniel': {'name': 'Daniel', 'abbrev': 'Dn', 'testament': 'Antigo', 'order': 27},
    'hosea': {'name': 'Oséias', 'abbrev': 'Os', 'testament': 'Antigo', 'order': 28},
    'joel': {'name': 'Joel', 'abbrev': 'Jl', 'testament': 'Antigo', 'order': 29},
    'amos': {'name': 'Amós', 'abbrev': 'Am', 'testament': 'Antigo', 'order': 30},
    'obadiah': {'name': 'Obadias', 'abbrev': 'Ob', 'testament': 'Antigo', 'order': 31},
    'jonah': {'name': 'Jonas', 'abbrev': 'Jn', 'testament': 'Antigo', 'order': 32},
    'micah': {'name': 'Miquéias', 'abbrev': 'Mq', 'testament': 'Antigo', 'order': 33},
    'nahum': {'name': 'Naum', 'abbrev': 'Na', 'testament': 'Antigo', 'order': 34},
    'habakkuk': {'name': 'Habacuque', 'abbrev': 'Hc', 'testament': 'Antigo', 'order': 35},
    'zephaniah': {'name': 'Sofonias', 'abbrev': 'Sf', 'testament': 'Antigo', 'order': 36},
    'haggai': {'name': 'Ageu', 'abbrev': 'Ag', 'testament': 'Antigo', 'order': 37},
    'zechariah': {'name': 'Zacarias', 'abbrev': 'Zc', 'testament': 'Antigo', 'order': 38},
    'malachi': {'name': 'Malaquias', 'abbrev': 'Ml', 'testament': 'Antigo', 'order': 39},
    
    # Novo Testamento
    'matthew': {'name': 'Mateus', 'abbrev': 'Mt', 'testament': 'Novo', 'order': 40},
    'mark': {'name': 'Marcos', 'abbrev': 'Mc', 'testament': 'Novo', 'order': 41},
    'luke': {'name': 'Lucas', 'abbrev': 'Lc', 'testament': 'Novo', 'order': 42},
    'john': {'name': 'João', 'abbrev': 'Jo', 'testament': 'Novo', 'order': 43},
    'acts': {'name': 'Atos', 'abbrev': 'At', 'testament': 'Novo', 'order': 44},
    'romans': {'name': 'Romanos', 'abbrev': 'Rm', 'testament': 'Novo', 'order': 45},
    '1corinthians': {'name': '1 Coríntios', 'abbrev': '1Co', 'testament': 'Novo', 'order': 46},
    '2corinthians': {'name': '2 Coríntios', 'abbrev': '2Co', 'testament': 'Novo', 'order': 47},
    'galatians': {'name': 'Gálatas', 'abbrev': 'Gl', 'testament': 'Novo', 'order': 48},
    'ephesians': {'name': 'Efésios', 'abbrev': 'Ef', 'testament': 'Novo', 'order': 49},
    'philippians': {'name': 'Filipenses', 'abbrev': 'Fp', 'testament': 'Novo', 'order': 50},
    'colossians': {'name': 'Colossenses', 'abbrev': 'Cl', 'testament': 'Novo', 'order': 51},
    '1thessalonians': {'name': '1 Tessalonicenses', 'abbrev': '1Ts', 'testament': 'Novo', 'order': 52},
    '2thessalonians': {'name': '2 Tessalonicenses', 'abbrev': '2Ts', 'testament': 'Novo', 'order': 53},
    '1timothy': {'name': '1 Timóteo', 'abbrev': '1Tm', 'testament': 'Novo', 'order': 54},
    '2timothy': {'name': '2 Timóteo', 'abbrev': '2Tm', 'testament': 'Novo', 'order': 55},
    'titus': {'name': 'Tito', 'abbrev': 'Tt', 'testament': 'Novo', 'order': 56},
    'philemon': {'name': 'Filemom', 'abbrev': 'Fm', 'testament': 'Novo', 'order': 57},
    'hebrews': {'name': 'Hebreus', 'abbrev': 'Hb', 'testament': 'Novo', 'order': 58},
    'james': {'name': 'Tiago', 'abbrev': 'Tg', 'testament': 'Novo', 'order': 59},
    '1peter': {'name': '1 Pedro', 'abbrev': '1Pe', 'testament': 'Novo', 'order': 60},
    '2peter': {'name': '2 Pedro', 'abbrev': '2Pe', 'testament': 'Novo', 'order': 61},
    '1john': {'name': '1 João', 'abbrev': '1Jo', 'testament': 'Novo', 'order': 62},
    '2john': {'name': '2 João', 'abbrev': '2Jo', 'testament': 'Novo', 'order': 63},
    '3john': {'name': '3 João', 'abbrev': '3Jo', 'testament': 'Novo', 'order': 64},
    'jude': {'name': 'Judas', 'abbrev': 'Jd', 'testament': 'Novo', 'order': 65},
    'revelation': {'name': 'Apocalipse', 'abbrev': 'Ap', 'testament': 'Novo', 'order': 66}
}

def get_book_by_name(name: str):
    """Encontra um livro pelo nome ou abreviação"""
    name_lower = name.lower()
    
    for book_key, book_info in BIBLE_BOOKS_INFO.items():
        if (book_info['name'].lower() == name_lower or 
            book_info['abbrev'].lower() == name_lower or
            book_key.lower() == name_lower):
            return book_key, book_info
    
    return None, None

def get_testament_books(testament: str):
    """Retorna livros de um testamento específico"""
    return {k: v for k, v in BIBLE_BOOKS_INFO.items() if v['testament'] == testament}

def get_books_by_order():
    """Retorna livros ordenados pela ordem bíblica"""
    return dict(sorted(BIBLE_BOOKS_INFO.items(), key=lambda x: x[1]['order']))