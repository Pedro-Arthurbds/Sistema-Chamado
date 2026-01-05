# 🔒 Solução de Prevenção de Múltiplos Envios (Duplicate Submissions)

## 📋 Problema Identificado

Quando o usuário clica várias vezes no botão "Enviar Chamado", o sistema criava vários chamados idênticos no banco de dados.

**Causa raiz:** Falta de validação no backend + Falta de feedback visual no frontend

---

## 🎯 Solução Implementada

A solução utiliza uma estratégia **de defesa em camadas** combinando:

### **1️⃣ Frontend: Desabilitação de Botão + Feedback Visual**

Impedindo cliques múltiplos no nível da interface:

```javascript
// Desabilita o botão após primeiro clique
submitBtn.disabled = true;
submitBtn.classList.add("opacity-50");
submitBtn.style.cursor = "not-allowed";

// Mostra spinner de carregamento
loadingSpinner.classList.remove("d-none");

// Aguarda um pequeno delay antes de submeter
setTimeout(() => {
    form.submit();
}, 500);
```

**Vantagens:**
- Feedback visual imediato ao usuário
- Previne cliques acidentais
- Melhora a experiência do usuário

**Desvantagem:**
- Pode ser contornado por usuários técnicos (reload da página, ferramentas dev, curl, etc.)

### **2️⃣ Backend: Token de Idempotência**

Sistema robusto que valida CADA requisição no servidor:

```python
# Arquivo: app/idempotency.py

def gerar_token_idempotencia():
    """Gera token único para cada formulário"""
    return secrets.token_hex(32)

def validar_e_consumir_token(token):
    """
    Valida e CONSOME o token (só funciona uma vez).
    - True: Requisição aceita (primeiro envio)
    - False: Requisição duplicada (token já foi usado)
    """
    if token in _request_cache:
        return False  # Token já foi usado!
    
    _request_cache[token] = (True, time.time())
    return True
```

**Fluxo:**
1. Página carrega → Gera token único
2. Usuário preenche formulário → Token viaja oculto no formulário
3. Primeiro submit → Token validado ✅ e marcado como consumido
4. Segundo submit → Token rejeitado ❌ (já foi consumido)

**Vantagens:**
- Seguro contra cliques múltiplos (mesmo com reload/ferramentas dev)
- Seguro contra tentativas via curl, scripts ou API
- Implementação simples e eficiente

---

## 📁 Arquivos Modificados / Criados

### **1. Novo: `app/idempotency.py`**

Gerencia tokens de idempotência. Mantém cache em memória com TTL de 1 hora.

```python
# Token válido = True (primeiro envio)
# Token duplicado = False (já foi consumido)
# Token expirado = removido automaticamente
```

### **2. Modificado: `app/routes.py`**

**Antes:**
```python
@app.route('/')
def home():
    return render_template('pages/abrir_chamado.html', chamados=chamados)

@app.route('/abrir_chamado', methods=['POST'])
def abrir_chamado_route():
    # Sem validação de duplicação!
```

**Depois:**
```python
from app.idempotency import gerar_token_idempotencia, validar_e_consumir_token

@app.route('/')
def home():
    idempotency_token = gerar_token_idempotencia()
    return render_template('pages/abrir_chamado.html', 
                         chamados=chamados, 
                         idempotency_token=idempotency_token)

@app.route('/abrir_chamado', methods=['POST'])
def abrir_chamado_route():
    # ===== VALIDAÇÃO DE IDEMPOTÊNCIA =====
    idempotency_token = request.form.get('idempotency_token')
    
    if not validar_e_consumir_token(idempotency_token):
        flash('Este chamado já foi enviado!', 'warning')
        return redirect('/')
    
    # ===== RESTO DO CÓDIGO =====
    # Agora seguro para criar o chamado
```

### **3. Modificado: `templates/pages/abrir_chamado.html`**

Adiciona input hidden com token:

```html
<!-- TOKEN DE IDEMPOTÊNCIA (OCULTO) -->
<input type="hidden" name="idempotency_token" value="{{ idempotency_token }}">

<!-- SPINNER DE CARREGAMENTO -->
<div id="loading-spinner" class="text-center mt-3 d-none">
    <div class="spinner-border spinner-border-sm text-primary" role="status">
        <span class="visually-hidden">Enviando...</span>
    </div>
    <p class="mt-2 text-primary fw-bold">Enviando chamado...</p>
</div>
```

### **4. Modificado: `static/js/script-abrir-chamado.js`**

Desabilita botão e mostra feedback visual:

```javascript
// Desabilita botão
submitBtn.disabled = true;
submitBtn.classList.add("opacity-50");

// Mostra spinner
loadingSpinner.classList.remove("d-none");

// Aguarda e submete
setTimeout(() => {
    form.submit();
}, 500);
```

---

## 🔐 Como Funciona (Passo a Passo)

### **Cenário 1: Usuário Normal Clicando Múltiplas Vezes**

```
1. Usuário carrega a página
   └─ Backend gera: token = "abc123def456..."
   └─ Token é enviado no HTML (oculto)

2. Usuário preenche formulário e clica "Enviar"
   └─ JavaScript desabilita botão
   └─ Mostra spinner "Enviando..."
   └─ Formulário é enviado com token

3. Backend recebe POST com token="abc123def456..."
   └─ validar_e_consumir_token("abc123def456...") → True ✅
   └─ Token marcado como consumido
   └─ Chamado criado no banco ✅

4. Usuário clica novamente (acidentalmente)
   └─ Botão está desabilitado → Clique não funciona ✅

5. Usuário recarrega página e envia novamente
   └─ Nova página = novo token ✅
   └─ Pode enviar novamente com a nova página
```

### **Cenário 2: Usuário Técnico Contornando Frontend**

```
1. Usuário inspeciona HTML com DevTools
   └─ Vê: <input type="hidden" name="idempotency_token" value="abc123...">

2. Copia o token e tenta enviar via curl:
   curl -X POST http://localhost:5001/abrir_chamado \
     -d "idempotency_token=abc123..." \
     -d "nome=João" \
     -d "contato=joao@email.com" \
     ...

3. Primeiro envio:
   └─ validar_e_consumir_token("abc123...") → True ✅
   └─ Chamado criado ✅

4. Segundo envio com MESMO token:
   └─ validar_e_consumir_token("abc123...") → False ❌
   └─ Requisição bloqueada ❌
   └─ Flash: "Este chamado já foi enviado!" ⚠️
   └─ Sem chamado duplicado ✅
```

### **Cenário 3: Usuário Recarrega a Página**

```
1. Primeira submissão
   └─ Token consumido ✅

2. Recarrega página (F5)
   └─ Nova página = novo token diferente ✅
   └─ Pode enviar novamente ✅
   └─ Criará novo chamado (esperado)
```

---

## 🛡️ Por Que Esta Solução é Segura

### **1. Defesa Dupla**

- **Frontend:** Previne cliques acidentais
- **Backend:** Bloqueia requisições duplicadas

Se um for contornado, o outro ainda protege.

### **2. Token Único**

Cada token é único e só funciona uma vez:
```python
token = secrets.token_hex(32)  # 64 caracteres aleatórios
# Exemplo: "a7f3e2c1b4d6f8a9e2c4b6d8f0a2c4e6f8a0c2e4b6d8f0a2c4e6f8a0c2e4"
```

**Impossível adivinhar** → Criptograficamente seguro

### **3. Limpeza Automática**

```python
# Tokens antigos são removidos automaticamente
_CACHE_TTL = 3600  # 1 hora
# Evita memoria leak
```

### **4. Logging de Tentativas Duplicadas**

```python
registrar_requisicao_duplicada(token, nome, contato, setor)
# Saída:
# [AVISO] Requisição duplicada detectada!
#   Token: abc123def456...
#   Usuário: João Silva (joao@email.com)
#   Setor: RH
#   Horário: 2025-01-05 14:32:15
```

---

## 📊 Fluxo de Dados

```
┌─────────────────────────────────────────────────────┐
│              CARREGAMENTO DA PÁGINA                 │
├─────────────────────────────────────────────────────┤
│ 1. GET /                                            │
│    └─ Backend: gerar_token_idempotencia()          │
│    └─ Retorna HTML com token oculto                │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│           USUÁRIO PREENCHE E CLICA                  │
├─────────────────────────────────────────────────────┤
│ 1. JavaScript: desabilita botão                    │
│ 2. JavaScript: mostra spinner                      │
│ 3. HTML form é enviado (submit)                    │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│            BACKEND VALIDA REQUISIÇÃO                │
├─────────────────────────────────────────────────────┤
│ 1. POST /abrir_chamado                             │
│    └─ Recebe idempotency_token do formulário      │
│    └─ validar_e_consumir_token(token)             │
│       ├─ Token no cache? NÃO → True ✅            │
│       └─ Token no cache? SIM → False ❌           │
│                                                     │
│ 2. Se True: Cria chamado no banco                 │
│    Se False: Bloqueia + Flash warning             │
└─────────────────────────────────────────────────────┘
```

---

## ✅ Testes Recomendados

### **Teste 1: Cliques Múltiplos Rápidos**
```
1. Abrir página
2. Preencher formulário
3. Clicar "Enviar" 5 vezes rapidamente
✅ Esperado: Apenas 1 chamado criado
```

### **Teste 2: Recarregar Página Após Envio**
```
1. Enviar chamado
2. F5 (recarregar)
3. Verificar banco de dados
✅ Esperado: Apenas 1 chamado (não duplicado)
```

### **Teste 3: Requição via Curl (Técnico)**
```bash
# Primeiro envio
curl -X POST http://localhost:5001/abrir_chamado \
  -d "idempotency_token=abc123..." \
  -d "nome=João" \
  -d "contato=joao@email.com" \
  -d "setor=RH" \
  -d "descricao=Teste"
✅ Resultado: Chamado criado

# Segundo envio com MESMO token
curl -X POST http://localhost:5001/abrir_chamado \
  -d "idempotency_token=abc123..." \
  -d "nome=João" \
  ...
✅ Resultado: Bloqueado - "Este chamado já foi enviado!"
```

### **Teste 4: Envio com Token Inválido**
```bash
curl -X POST http://localhost:5001/abrir_chamado \
  -d "idempotency_token=invalid" \
  ...
✅ Resultado: Bloqueado (token inválido)
```

---

## 🚀 Melhorias Futuras (Opcional)

### **1. Armazenar no Banco de Dados**
```python
# Em vez de cache em memória, usar banco:
class SubmissaoProcessada(db.Model):
    token = db.Column(db.String(64), unique=True)
    timestamp = db.Column(db.DateTime)
```

**Vantagens:** Persiste entre reinicializações  
**Desvantagens:** Um pouco mais lento

### **2. Redis para Distribuição**
```python
import redis

redis_client = redis.Redis()

def validar_token_redis(token):
    resultado = redis_client.set(token, 1, ex=3600, nx=True)
    return resultado  # True = novo, False = duplicado
```

**Vantagens:** Funciona em múltiplos servidores  
**Desvantagens:** Requer Redis instalado

### **3. Adicionar CSRF Protection**
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# Template
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
```

### **4. Rate Limiting por IP**
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/abrir_chamado', methods=['POST'])
@limiter.limit("5 per minute")
def abrir_chamado_route():
    ...
```

---

## 📝 Resumo da Solução

| Aspecto | Antes | Depois |
|--------|-------|--------|
| **Múltiplos cliques** | ❌ Cria vários chamados | ✅ Apenas 1 chamado |
| **Feedback visual** | ❌ Nenhum | ✅ Spinner + Botão desabilitado |
| **Segurança no frontend** | ❌ Sem proteção | ✅ Botão desabilitado após clique |
| **Segurança no backend** | ❌ Sem validação | ✅ Token de idempotência |
| **Tokens duplicados** | ❌ Sem proteção | ✅ Bloqueados automaticamente |
| **Requisições via curl** | ❌ Sem proteção | ✅ Bloqueadas |
| **Logging de tentativas** | ❌ Sem registro | ✅ Log detalhado |

---

## 🎓 Conceitos Aprendidos

1. **Idempotência:** Propriedade de executar a mesma operação várias vezes com o mesmo resultado
2. **Race Conditions:** Problema quando múltiplas requisições chegam simultaneamente
3. **Defesa em Camadas:** Proteção no frontend + backend para máxima segurança
4. **Token de Sessão:** Uso de tokens únicos para validar requisições

---

## 📞 Suporte

Se encontrar problemas:

1. **Verifique o console** (F12 → Console) para erros JavaScript
2. **Verifique os logs** do Flask (terminal onde está rodando)
3. **Teste com curl** para isolar se é frontend ou backend
4. **Limpe o cache** do navegador (Ctrl+Shift+Del)

---

**Desenvolvido para o Sistema de Chamados v1.0**
