# math_validation.py
# Sistema de validação matemática para formulários
# Funciona através de sessões Flask

import random

def gerar_validacao_matematica(session):
    """
    Gera dois números aleatórios e os armazena na sessão.
    
    Args:
        session: Sessão do Flask
        
    Returns:
        tuple: (numero1, numero2)
    
    Exemplo:
        num1, num2 = gerar_validacao_matematica(session)
        # Pergunta ao usuário: "Quanto é {num1} + {num2}?"
    """
    numero1 = random.randint(0, 10)
    numero2 = random.randint(0, 10)
    
    # Armazena na sessão (seguro no servidor, não visível no cliente)
    session['math_num1'] = numero1
    session['math_num2'] = numero2
    session['math_resposta_correta'] = numero1 + numero2
    
    return numero1, numero2


def validar_resposta_matematica(session, resposta_usuario):
    """
    Valida a resposta do usuário contra a soma armazenada na sessão.
    
    Args:
        session: Sessão do Flask
        resposta_usuario: Resposta informada pelo usuário (string ou int)
        
    Returns:
        dict: {
            'valido': bool,
            'mensagem': str,
            'numero1': int,
            'numero2': int
        }
    """
    # Verifica se os números existem na sessão
    if 'math_resposta_correta' not in session:
        return {
            'valido': False,
            'mensagem': 'Validação expirou. Recarregue a página e tente novamente.',
            'numero1': None,
            'numero2': None
        }
    
    try:
        # Converte a resposta do usuário para inteiro
        resposta_int = int(resposta_usuario)
    except (ValueError, TypeError):
        return {
            'valido': False,
            'mensagem': 'Por favor, informe um número válido.',
            'numero1': session.get('math_num1'),
            'numero2': session.get('math_num2')
        }
    
    # Compara com a resposta correta
    resposta_correta = session['math_resposta_correta']
    numero1 = session['math_num1']
    numero2 = session['math_num2']
    
    if resposta_int == resposta_correta:
        return {
            'valido': True,
            'mensagem': 'Validação correta!',
            'numero1': numero1,
            'numero2': numero2
        }
    else:
        return {
            'valido': False,
            'mensagem': '❌ Resposta incorreta. Tente novamente!',
            'numero1': numero1,
            'numero2': numero2
        }


def limpar_validacao_matematica(session):
    """
    Remove os números da sessão após validação bem-sucedida.
    Previne reutilização da mesma validação.
    
    Args:
        session: Sessão do Flask
    """
    if 'math_num1' in session:
        del session['math_num1']
    if 'math_num2' in session:
        del session['math_num2']
    if 'math_resposta_correta' in session:
        del session['math_resposta_correta']


def obter_numeros_sessao(session):
    """
    Retorna os números armazenados na sessão atual.
    Usado para renderizar o template com a pergunta.
    
    Args:
        session: Sessão do Flask
        
    Returns:
        tuple: (numero1, numero2) ou (None, None) se não existir
    """
    numero1 = session.get('math_num1')
    numero2 = session.get('math_num2')
    
    return numero1, numero2
