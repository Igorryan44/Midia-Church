"""
Configurações de fuso horário para Palmas - TO
"""

import pytz
from datetime import datetime

# Fuso horário de Palmas - TO (UTC-3)
TIMEZONE = pytz.timezone('America/Araguaina')  # Palmas usa o mesmo fuso de Araguaína
TIMEZONE_NAME = "America/Araguaina"
TIMEZONE_DISPLAY = "Palmas - TO (UTC-3)"

def get_local_time():
    """Retorna a hora atual no fuso horário de Palmas-TO"""
    utc_now = datetime.utcnow()
    utc_tz = pytz.UTC
    utc_time = utc_tz.localize(utc_now)
    local_time = utc_time.astimezone(TIMEZONE)
    return local_time

def get_local_date():
    """Retorna a data atual no fuso horário de Palmas-TO"""
    return get_local_time().date()

def get_local_datetime_str():
    """Retorna data e hora formatada para Palmas-TO"""
    local_time = get_local_time()
    return local_time.strftime("%d/%m/%Y %H:%M:%S")

def get_local_date_str():
    """Retorna data formatada para Palmas-TO"""
    local_time = get_local_time()
    return local_time.strftime("%d/%m/%Y")

def get_local_time_str():
    """Retorna hora formatada para Palmas-TO"""
    local_time = get_local_time()
    return local_time.strftime("%H:%M:%S")

def convert_utc_to_local(utc_datetime):
    """Converte datetime UTC para horário local de Palmas-TO"""
    if isinstance(utc_datetime, str):
        utc_datetime = datetime.fromisoformat(utc_datetime.replace('Z', '+00:00'))
    
    if utc_datetime.tzinfo is None:
        utc_datetime = pytz.UTC.localize(utc_datetime)
    
    return utc_datetime.astimezone(TIMEZONE)

def convert_local_to_utc(local_datetime):
    """Converte datetime local de Palmas-TO para UTC"""
    if isinstance(local_datetime, str):
        local_datetime = datetime.fromisoformat(local_datetime)
    
    if local_datetime.tzinfo is None:
        local_datetime = TIMEZONE.localize(local_datetime)
    
    return local_datetime.astimezone(pytz.UTC)

def format_datetime_local(dt, format_str="%d/%m/%Y %H:%M"):
    """Formata datetime para o fuso horário local"""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
    
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    local_dt = dt.astimezone(TIMEZONE)
    return local_dt.strftime(format_str)

def get_timezone_info():
    """Retorna informações sobre o fuso horário configurado"""
    local_time = get_local_time()
    return {
        "timezone": TIMEZONE_NAME,
        "display_name": TIMEZONE_DISPLAY,
        "current_time": local_time.strftime("%H:%M:%S"),
        "current_date": local_time.strftime("%d/%m/%Y"),
        "utc_offset": local_time.strftime("%z"),
        "is_dst": local_time.dst() != local_time.dst().min
    }