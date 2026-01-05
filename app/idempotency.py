# idempotency.py
# Sistema de tokens de idempotência para prevenir múltiplas submissões

import hashlib
import secrets
import time
from datetime import datetime, timedelta
from app.db import conectar_bd

# Dicionário em memória para cache de requisições processadas
# Em produção, isso deveria usar Redis ou banco de dados
_request_cache = {}
_CACHE_TTL = 3600  # Tempo de vida do cache em segundos (1 hora)


def gerar_token_idempotencia():
    """
    Gera um token único de idempotência para cada formulário.
    Este token garante que apenas uma submissão será aceita.
    """
    return secrets.token_hex(32)


def validar_e_consumir_token(token):
    """
    Valida e consome um token de idempotência.
    
    Returns:
        - True: Se o token é válido e ainda não foi usado (requisição aceita)
        - False: Se o token já foi usado (requisição duplicada)
        - False: Se o token é inválido
    """
    if not token:
        return False
    
    # Limpar tokens antigos do cache
    agora = time.time()
    chaves_expiradas = [chave for chave, (_, timestamp) in _request_cache.items() 
                        if agora - timestamp > _CACHE_TTL]
    for chave in chaves_expiradas:
        del _request_cache[chave]
    
    # Verificar se o token já foi usado
    if token in _request_cache:
        return False  # Token já foi consumido (requisição duplicada)
    
    # Marcar token como usado
    _request_cache[token] = (True, agora)
    return True  # Token válido e aceito


def invalidar_token(token):
    """
    Remove um token do cache (útil em caso de erro ou cancelamento).
    """
    if token in _request_cache:
        del _request_cache[token]


def registrar_requisicao_duplicada(token, nome, contato, setor):
    """
    Log de requisições duplicadas para auditoria.
    Em produção, isso deveria ser armazenado em banco de dados.
    """
    print(f"[AVISO] Requisição duplicada detectada!")
    print(f"  Token: {token}")
    print(f"  Usuário: {nome} ({contato})")
    print(f"  Setor: {setor}")
    print(f"  Horário: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
