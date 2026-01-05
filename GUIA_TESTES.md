# 🧪 Guia de Testes - Prevenção de Duplicate Submissions

## 📝 Instruções Práticas para Testar a Solução

---

## 1️⃣ TESTE MANUAL - Interface Web

### **Teste 1.1: Clique Simples (Baseline)**

```
OBJETIVO: Verificar que um envio normal funciona
PASSOS:
  1. Abrir navegador → http://localhost:5001/
  2. Preencher todos os campos do formulário
  3. Clicar "Enviar Chamado" 1 vez
  4. Aguardar redirecionamento
  
RESULTADO ESPERADO:
  ✅ Página redireciona para home
  ✅ Flash message: "Chamado aberto com sucesso!"
  ✅ E-mail enviado ao usuário
  ✅ Banco de dados: 1 novo chamado criado
  ✅ Console JS: Sem erros
```

### **Teste 1.2: Cliques Múltiplos Rápidos**

```
OBJETIVO: Verificar proteção contra cliques múltiplos
PASSOS:
  1. Abrir navegador → http://localhost:5001/
  2. Preencher todos os campos
  3. Clicar "Enviar Chamado" 10 vezes o mais rápido possível
  4. Aguardar resposta do servidor
  
RESULTADO ESPERADO:
  ✅ Botão fica DESABILITADO após 1º clique
  ✅ Botão muda de cor (opacity-50)
  ✅ Cursor muda para "not-allowed"
  ✅ Spinner apareça com "Enviando chamado..."
  ✅ Apenas 1 chamado criado no banco
  ✅ Flash message ao final
```

### **Teste 1.3: Clique + Recarregar Página**

```
OBJETIVO: Verificar proteção ao recarregar durante envio
PASSOS:
  1. Abrir navegador → http://localhost:5001/
  2. Preencher todos os campos
  3. Clicar "Enviar Chamado"
  4. Imediatamente pressionar F5 (recarregar)
  5. Aguardar
  
RESULTADO ESPERADO:
  ✅ Apenas 1 chamado criado (não 2)
  ✅ Nenhum erro no navegador
  ✅ Banco de dados: chamado único com ID correto
```

### **Teste 1.4: Novo Envio Após Sucesso**

```
OBJETIVO: Verificar que novo envio funciona com nova página
PASSOS:
  1. Enviar 1º chamado (sucesso)
  2. Recarregar página (F5)
  3. Preencher outro formulário
  4. Clicar "Enviar Chamado"
  
RESULTADO ESPERADO:
  ✅ Novo token gerado na recarrega
  ✅ 2º chamado criado com sucesso
  ✅ Banco de dados: 2 chamados diferentes
  ✅ IDs diferentes (ex: ID 1001 e ID 1002)
```

---

## 2️⃣ TESTE VIA CURL - Linha de Comando

### **Teste 2.1: Primeiro Envio (Sucesso)**

```bash
# 1. Copiar token do HTML
# Abrir navegador → Inspeção (F12) → Console
# Copiar o token de:
#   <input type="hidden" name="idempotency_token" value="COLE_AQUI">

IDEMPOTENCY_TOKEN="a7f3e2c1b4d6f8a9e2c4b6d8f0a2c4e6f8a0c2e4b6d8f0a2c4e6f8a0c2e4"

# 2. Enviar primeiro curl
curl -X POST http://localhost:5001/abrir_chamado \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "idempotency_token=$IDEMPOTENCY_TOKEN" \
  -d "nome=João Silva" \
  -d "contato=joao@example.com" \
  -d "setor=RH" \
  -d "descricao=Teste de chamado via curl" \
  -v

RESULTADO ESPERADO:
  ✅ HTTP 302 Redirect (sucesso)
  ✅ Location header: /
  ✅ Set-Cookie: session=...
  ✅ Flash message: "Chamado aberto com sucesso!"
  ✅ Banco de dados: 1 chamado criado
```

### **Teste 2.2: Segundo Envio (Mesmo Token - Bloqueado)**

```bash
# Usar MESMO token do teste anterior

IDEMPOTENCY_TOKEN="a7f3e2c1b4d6f8a9e2c4b6d8f0a2c4e6f8a0c2e4b6d8f0a2c4e6f8a0c2e4"

curl -X POST http://localhost:5001/abrir_chamado \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "idempotency_token=$IDEMPOTENCY_TOKEN" \
  -d "nome=João Silva" \
  -d "contato=joao@example.com" \
  -d "setor=RH" \
  -d "descricao=Teste de chamado via curl" \
  -v

RESULTADO ESPERADO:
  ✅ HTTP 302 Redirect
  ✅ Flash message: "Este chamado já foi enviado!"
  ✅ Banco de dados: Ainda apenas 1 chamado (NÃO 2)
  ❌ Chamado duplicado NÃO foi criado
```

### **Teste 2.3: Token Inválido**

```bash
IDEMPOTENCY_TOKEN="invalid_token_12345"

curl -X POST http://localhost:5001/abrir_chamado \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "idempotency_token=$IDEMPOTENCY_TOKEN" \
  -d "nome=João Silva" \
  -d "contato=joao@example.com" \
  -d "setor=RH" \
  -d "descricao=Token inválido"

RESULTADO ESPERADO:
  ✅ HTTP 302 Redirect
  ✅ Flash: "Este chamado já foi enviado!" (bloqueado)
  ❌ Chamado NÃO criado
```

### **Teste 2.4: Sem Token**

```bash
curl -X POST http://localhost:5001/abrir_chamado \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "nome=João Silva" \
  -d "contato=joao@example.com" \
  -d "setor=RH" \
  -d "descricao=Sem token"

RESULTADO ESPERADO:
  ✅ HTTP 302 Redirect
  ✅ Flash: "Este chamado já foi enviado!" (bloqueado)
  ❌ Chamado NÃO criado
```

---

## 3️⃣ TESTE AUTOMATIZADO - Python

```python
# Arquivo: test_duplicate_submissions.py

import requests
import json
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:5001"

def extrair_token():
    """Extrai token da página inicial"""
    response = requests.get(f"{BASE_URL}/")
    soup = BeautifulSoup(response.text, 'html.parser')
    token_input = soup.find('input', {'name': 'idempotency_token'})
    return token_input['value']

def enviar_chamado(token, nome, contato, setor, descricao):
    """Envia formulário de chamado"""
    data = {
        'idempotency_token': token,
        'nome': nome,
        'contato': contato,
        'setor': setor,
        'descricao': descricao,
        'arquivo': ''
    }
    
    response = requests.post(
        f"{BASE_URL}/abrir_chamado",
        data=data,
        allow_redirects=False
    )
    
    return response.status_code, response.text

# TESTE 1: Primeiro envio
print("TEST 1: Primeiro envio com token válido")
token = extrair_token()
status, response = enviar_chamado(
    token, 
    "João Silva", 
    "joao@example.com", 
    "RH", 
    "Teste automático"
)
print(f"  Status: {status}")
print(f"  Esperado: 302 (Redirect)")
assert status == 302, "Esperava 302!"
print("  ✅ PASSOU\n")

# TESTE 2: Segundo envio com MESMO token
print("TEST 2: Segundo envio com MESMO token")
status, response = enviar_chamado(
    token,  # <-- MESMO TOKEN!
    "João Silva",
    "joao@example.com",
    "RH",
    "Teste automático"
)
print(f"  Status: {status}")
print(f"  Esperado: 302 (Redirect com bloqueio)")
print(f"  Mensagem: 'Este chamado já foi enviado!'")
assert status == 302, "Esperava 302!"
assert "já foi enviado" in response, "Mensagem de bloqueio não encontrada!"
print("  ✅ PASSOU\n")

# TESTE 3: Novo envio com novo token
print("TEST 3: Novo envio com novo token")
novo_token = extrair_token()
status, response = enviar_chamado(
    novo_token,  # <-- NOVO TOKEN!
    "Maria Santos",
    "maria@example.com",
    "RH",
    "Outro teste"
)
print(f"  Status: {status}")
print(f"  Esperado: 302 (Sucesso)")
assert status == 302, "Esperava 302!"
print("  ✅ PASSOU\n")

print("=" * 50)
print("TODOS OS TESTES PASSARAM! ✅")
print("=" * 50)
```

**Executar:**
```bash
pip install requests beautifulsoup4
python test_duplicate_submissions.py
```

---

## 4️⃣ TESTE DE STRESS - Múltiplas Requisições Simultâneas

```python
# Arquivo: test_stress_duplicate.py

import concurrent.futures
import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:5001"

def obter_token():
    response = requests.get(f"{BASE_URL}/")
    soup = BeautifulSoup(response.text, 'html.parser')
    token_input = soup.find('input', {'name': 'idempotency_token'})
    return token_input['value']

def enviar_chamado(token, numero):
    data = {
        'idempotency_token': token,
        'nome': f"Teste {numero}",
        'contato': f"teste{numero}@example.com",
        'setor': "RH",
        'descricao': f"Envio número {numero}"
    }
    
    response = requests.post(
        f"{BASE_URL}/abrir_chamado",
        data=data
    )
    return response.status_code

print("Teste de Stress: 50 requisições simultâneas com MESMO token")
print("=" * 60)

token = obter_token()
print(f"Token: {token}\n")

# Enviar 50 requisições em paralelo
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    resultados = list(executor.map(lambda i: enviar_chamado(token, i), range(1, 51)))

print(f"Total de requisições: 50")
print(f"Redirecionamentos (302): {resultados.count(302)}")
print(f"Outros: {50 - resultados.count(302)}")

print("\nResultado esperado:")
print("  ✅ 50 requisições com MESMO token")
print("  ✅ Apenas 1 chamado criado no banco")
print("  ✅ Nenhuma exceção/erro")
```

**Executar:**
```bash
python test_stress_duplicate.py
```

---

## 5️⃣ VERIFICAÇÃO NO BANCO DE DADOS

### **Teste 5.1: Contar Chamados**

```sql
-- Após executar vários testes acima

SELECT COUNT(*) as total_chamados FROM chamados;
-- Resultado esperado: Número de cliques únicos (NÃO multiplicado)

SELECT * FROM chamados ORDER BY id DESC LIMIT 5;
-- Verificar que não há duplicatas
```

### **Teste 5.2: Verificar Duplicatas**

```sql
-- Verificar se há duplicatas (NÃO deve retornar nada)

SELECT nome, contato, setor, COUNT(*) as duplicatas
FROM chamados
GROUP BY nome, contato, setor
HAVING COUNT(*) > 1;

-- Resultado esperado: (empty set)
```

---

## 6️⃣ TESTE DE LOGS

### **Verificar Logs no Terminal Flask**

```
[AVISO] Requisição duplicada detectada!
  Token: abc123def456...
  Usuário: João Silva (joao@email.com)
  Setor: RH
  Horário: 2025-01-05 14:32:15
```

**Aparece quando:** Usuário tenta enviar com token já consumido

---

## 7️⃣ CHECKLIST DE TESTES

- [ ] **T1.1:** Clique simples funciona
- [ ] **T1.2:** Cliques múltiplos criam apenas 1 chamado
- [ ] **T1.3:** Recarregar durante envio não duplica
- [ ] **T1.4:** Novo envio após sucesso funciona
- [ ] **T2.1:** Curl primeiro envio funciona
- [ ] **T2.2:** Curl segundo envio é bloqueado
- [ ] **T2.3:** Token inválido é bloqueado
- [ ] **T2.4:** Sem token é bloqueado
- [ ] **T3.1:** Teste automático Python passa
- [ ] **T4.1:** Stress test: 50 requisições = 1 chamado
- [ ] **T5.1:** Banco de dados: sem duplicatas
- [ ] **T5.2:** SQL GROUP BY: nenhuma duplicata
- [ ] **T6.1:** Logs aparecem no terminal Flask
- [ ] **UX1:** Botão fica desabilitado
- [ ] **UX2:** Spinner aparece durante envio
- [ ] **UX3:** Flash message é exibida

---

## 📊 Relatório de Teste

Após executar todos os testes, preencha:

```
Data: ___________
Teste por: ___________
Ambiente: Local / Staging / Produção

RESULTADOS:
  Testes Manuais: ____ / 4 PASSED
  Testes Curl: ____ / 4 PASSED
  Testes Python: ____ / 1 PASSED
  Testes Stress: ____ / 1 PASSED
  Verificação BD: ____ / 2 PASSED
  UX: ____ / 3 PASSED

STATUS GERAL:
  ✅ APROVADO
  ⚠️ CONDICIONAL
  ❌ REPROVADO

Observações:
___________________________________________________________________________
___________________________________________________________________________
```

---

## 🔧 Troubleshooting

| Problema | Solução |
|----------|---------|
| Teste falha: "Token não encontrado" | Verificar se Jinja2 está renderizando `{{ idempotency_token }}` |
| Chamado duplicado criado | Verificar se função `validar_e_consumir_token()` está sendo chamada |
| Botão não desabilita | Verificar console JS (F12) para erros |
| Flask não inicia | Verificar se `app/idempotency.py` existe |
| Token expires rapidamente | TTL = 3600s, está correto |

---

**Desenvolvido para Sistema de Chamados v1.0**
