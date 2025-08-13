"""
Configurações para carregamento da Bíblia completa
"""

# APIs disponíveis para carregamento da Bíblia
BIBLE_APIS = {
    "abibliadigital": {
        "name": "A Bíblia Digital",
        "base_url": "https://www.abibliadigital.com.br/api",
        "versions": {
            "acf": "Almeida Corrigida Fiel",
            "nvi": "Nova Versão Internacional", 
            "aa": "Almeida Atualizada",
            "ra": "Almeida Revista e Atualizada"
        },
        "requires_token": False,
        "rate_limit": 100  # requests per minute
    },
    "bible_api": {
        "name": "Bible API",
        "base_url": "https://bible-api.com",
        "versions": {
            "almeida": "João Ferreira de Almeida"
        },
        "requires_token": False,
        "rate_limit": 60
    }
}

# Configurações de carregamento
LOADING_CONFIG = {
    "batch_size": 50,  # Número de versículos por lote
    "delay_between_requests": 0.1,  # Segundos entre requisições
    "max_retries": 3,
    "timeout": 30,
    "default_version": "acf"
}

# Mapeamento de livros para diferentes APIs
BOOK_MAPPING = {
    "abibliadigital": {
        "genesis": "gn",
        "exodus": "ex", 
        "leviticus": "lv",
        "numbers": "nm",
        "deuteronomy": "dt",
        "joshua": "js",
        "judges": "jz",
        "ruth": "rt",
        "1samuel": "1sm",
        "2samuel": "2sm",
        "1kings": "1rs",
        "2kings": "2rs",
        "1chronicles": "1cr",
        "2chronicles": "2cr",
        "ezra": "ed",
        "nehemiah": "ne",
        "esther": "et",
        "job": "jo",
        "psalms": "sl",
        "proverbs": "pv",
        "ecclesiastes": "ec",
        "song": "ct",
        "isaiah": "is",
        "jeremiah": "jr",
        "lamentations": "lm",
        "ezekiel": "ez",
        "daniel": "dn",
        "hosea": "os",
        "joel": "jl",
        "amos": "am",
        "obadiah": "ob",
        "jonah": "jn",
        "micah": "mq",
        "nahum": "na",
        "habakkuk": "hc",
        "zephaniah": "sf",
        "haggai": "ag",
        "zechariah": "zc",
        "malachi": "ml",
        "matthew": "mt",
        "mark": "mc",
        "luke": "lc",
        "john": "jo",
        "acts": "at",
        "romans": "rm",
        "1corinthians": "1co",
        "2corinthians": "2co",
        "galatians": "gl",
        "ephesians": "ef",
        "philippians": "fp",
        "colossians": "cl",
        "1thessalonians": "1ts",
        "2thessalonians": "2ts",
        "1timothy": "1tm",
        "2timothy": "2tm",
        "titus": "tt",
        "philemon": "fm",
        "hebrews": "hb",
        "james": "tg",
        "1peter": "1pe",
        "2peter": "2pe",
        "1john": "1jo",
        "2john": "2jo",
        "3john": "3jo",
        "jude": "jd",
        "revelation": "ap"
    }
}

def get_api_config(api_name="abibliadigital"):
    """Retorna configuração da API especificada"""
    return BIBLE_APIS.get(api_name, BIBLE_APIS["abibliadigital"])

def get_loading_config():
    """Retorna configurações de carregamento"""
    return LOADING_CONFIG

def get_book_mapping(api_name="abibliadigital"):
    """Retorna mapeamento de livros para a API especificada"""
    return BOOK_MAPPING.get(api_name, {})