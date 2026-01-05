# 📊 Diagrama Visual - Fluxo de Prevenção de Duplicate Submissions

## 🎯 Visão Geral

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SISTEMA DE CHAMADOS                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ANTES (Problema)          →          DEPOIS (Solução)              │
│  ───────────────────────────────────────────────────────────       │
│                                                                       │
│  Clique 1 ✅                           Clique 1 ✅                   │
│  │                                     │                             │
│  └─→ Chamado 1001 criado              └─→ Token "T123" consumido     │
│                                           Chamado 1001 criado        │
│  Clique 2 ✅                           Clique 2 ❌                   │
│  │                                     │                             │
│  └─→ Chamado 1002 criado ❌           └─→ Token "T123" já usado     │
│      (DUPLICADO!)                         (Requisição bloqueada)    │
│                                                                       │
│  Resultado: ❌ 2 CHAMADOS              Resultado: ✅ 1 CHAMADO     │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Fluxo de Requisição Única

```
CLIENTE (Browser)                    SERVIDOR (Flask)
═════════════════════════════════════════════════════════════════════

1️⃣ GET /
   ├─→ Página carregada
   │
   └─→ Servidor gera token
       (secrets.token_hex(32))
       └─→ "a7f3e2c1b4d6..."
   
   ←── Retorna HTML com token oculto
       <input type="hidden" 
              name="idempotency_token" 
              value="a7f3e2c1b4d6...">

2️⃣ Usuário preenche formulário
   └─→ Clica "Enviar Chamado"
   
3️⃣ JavaScript
   ├─→ Desabilita botão 🔒
   ├─→ Muda cor (opacity-50)
   ├─→ Mostra spinner ⏳
   │
   └─→ Submete formulário
       (com token incluído)

4️⃣ POST /abrir_chamado
   (form data + token="a7f3e2c1b4d6...")
   ├─→ Servidor recebe
   │
   └─→ Backend valida
       validar_e_consumir_token("a7f3e2c1b4d6...")
       ├─→ Token no cache? NÃO
       ├─→ Marca token como consumido
       └─→ Retorna TRUE ✅

5️⃣ Processamento
   ├─→ Validação de arquivo ✅
   ├─→ Chamado criado no BD ✅
   ├─→ E-mail enviado ✅
   │
   └─→ Resposta: 302 Redirect
       + Flash: "Sucesso!"

6️⃣ Resultado
   ←── Redirecionado para /
       + Flash exibida
       + 1 chamado criado ✅
```

---

## 🛡️ Fluxo com Requisição Duplicada

```
CLIENTE (Browser)              SERVIDOR (Flask)
═══════════════════════════════════════════════════════

1️⃣ Usuário clica NOVAMENTE
   (antes de página recarregar)
   
2️⃣ JavaScript
   ├─→ Tenta clicar
   └─→ Botão já está .disabled = true
       └─→ Clique BLOQUEADO ❌
   
   (Proteção Frontend: Sucesso!)

─────────────────────────────────────────────────────

OU: Usuário contorna (DevTools, Curl, etc)

1️⃣ POST /abrir_chamado
   (form data + token="a7f3e2c1b4d6...")
   
2️⃣ Servidor valida
   validar_e_consumir_token("a7f3e2c1b4d6...")
   ├─→ Token no cache? SIM ✓
   ├─→ Já foi consumido! ⚠️
   └─→ Retorna FALSE ❌

3️⃣ Backend rejeita
   ├─→ registrar_requisicao_duplicada()
   ├─→ Flash: "Já foi enviado!"
   │
   └─→ Resposta: 302 Redirect

4️⃣ Resultado
   ←── Redirecionado para /
       + Flash warning: "Já foi enviado!"
       + Nenhum chamado criado ✅
   
   (Proteção Backend: Sucesso!)
```

---

## 📦 Arquitetura de Componentes

```
┌───────────────────────────────────────────────────────────┐
│                   APLICAÇÃO FLASK                         │
├───────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────┐      │
│  │          app/idempotency.py (NOVO)              │      │
│  ├─────────────────────────────────────────────────┤      │
│  │ • gerar_token_idempotencia()                    │      │
│  │ • validar_e_consumir_token(token)               │      │
│  │ • invalidar_token(token)                        │      │
│  │ • registrar_requisicao_duplicada(...)           │      │
│  │                                                  │      │
│  │ Cache: _request_cache = {}                      │      │
│  └─────────────────────────────────────────────────┘      │
│           ↑            ↑           ↑                       │
│           │            │           │                       │
│  ┌────────┴──┐  ┌──────┴──┐  ┌────┴─────────────┐        │
│  │ routes.py │  │template │  │script-*.js       │        │
│  │ (Modificado)│(Modific.)│  │(Modificado)      │        │
│  └───────────┘  └─────────┘  └──────────────────┘        │
│      │              │              │                       │
│      └──────────────┼──────────────┘                       │
│                     │                                       │
│                 Database                                   │
│                (chamados)                                  │
│                                                             │
└───────────────────────────────────────────────────────────┘
```

---

## ⏱️ Timeline de Execução

```
TIMESTAMP    EVENTO                              CACHE STATE
──────────────────────────────────────────────────────────────

00:00ms      Usuário acessa GET /
             └─→ Token gerado: "T123"              {}

             ← HTML com "T123" renderizado
               (input hidden)

00:100ms     Usuário clica "Enviar"              
             └─→ JS desabilita botão

00:150ms     POST /abrir_chamado
             └─→ Token: "T123" chega ao servidor

00:160ms     validar_e_consumir_token("T123")
             ├─→ Verifica: "T123" em cache?      {}
             ├─→ Não encontrado (novo)           
             └─→ Adiciona ao cache:              {T123: ...}

00:300ms     Processa chamado
             ├─→ Validação arquivo ✅
             ├─→ Insert BD ✅
             └─→ E-mail enviado ✅

00:400ms     Resposta: 302 Redirect
             ← Flash: "Sucesso!"

00:450ms     Novo GET /
             └─→ Novo token gerado: "T456"       {T123: ..., T456: ...}

═════════════════════════════════════════════════════════════════

Tentativa de duplicação (00:200ms - Mesmo que 00:150ms):

00:200ms     (Segundo clique simultâneo)
             └─→ JS: Botão já desabilitado ❌
                (Clique não funciona)

─────────────────────────────────────────────────────────────────

Tentativa via Curl (Mesmo token):

01:000ms     curl -X POST ... token="T123"
             
             validar_e_consumir_token("T123")
             ├─→ Verifica: "T123" em cache?      {T123: ..., T456: ...}
             ├─→ ENCONTRADO! (já consumido)      
             └─→ Retorna FALSE ❌

01:100ms     Resposta: 302 Redirect
             ← Flash: "Já foi enviado!"
             └─→ Nenhum chamado criado ✅

═════════════════════════════════════════════════════════════════

Limpeza Automática (01:3600s):

03600ms      Token "T123" expira (TTL=3600s)
             └─→ Removido do cache
             
                Cache limpo automaticamente      {T456: ...}
```

---

## 🔐 Diagrama de Segurança

```
╔════════════════════════════════════════════════════════════╗
║              CAMADAS DE PROTEÇÃO                          ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Camada 1: FRONTEND                                       ║
║  ┌──────────────────────────────────────────────┐         ║
║  │ • Desabilita botão após 1º clique           │         ║
║  │ • Mostra spinner de carregamento             │         ║
║  │ • Muda cursor para "not-allowed"             │         ║
║  │ Proteção: Contra cliques acidentais ✅      │         ║
║  │ Bypass: Possível (DevTools, reload, etc)    │         ║
║  └──────────────────────────────────────────────┘         ║
║         ↓                                                   ║
║  Camada 2: BACKEND (CRÍTICA)                             ║
║  ┌──────────────────────────────────────────────┐         ║
║  │ • Token de idempotência único                │         ║
║  │ • Validação: Token nunca foi usado?          │         ║
║  │ • Consumo: Token usado = inválido para sempre│         ║
║  │ • Logging: Registra tentativas duplicadas    │         ║
║  │ Proteção: Contra requisições duplicadas ✅  │         ║
║  │ Bypass: Impossível (sem token válido)        │         ║
║  └──────────────────────────────────────────────┘         ║
║         ↓                                                   ║
║  Resultado: ✅ SEGURO EM MÚLTIPLAS CAMADAS               ║
║                                                            ║
║  Mesmo que Frontend seja contornado,                      ║
║  Backend bloqueia requisições duplicadas.                 ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

## 📊 Comparativo Visual

```
┌─────────────────────────┬──────────────┬──────────────┐
│ Situação                │ ANTES        │ DEPOIS       │
├─────────────────────────┼──────────────┼──────────────┤
│ Clique 1×               │ 1 chamado ✅ │ 1 chamado ✅ │
│ Clique 5×               │ 5 chamados❌ │ 1 chamado ✅ │
│ Clique + Reload         │ 2 chamados❌ │ 1 chamado ✅ │
│ Curl (mesmo token)      │ N chamados❌ │ 1 chamado ✅ │
│ Feedback visual         │ ❌ Nenhum    │ ✅ Spinner   │
│ Proteção Frontend       │ ❌ Não       │ ✅ Sim       │
│ Proteção Backend        │ ❌ Não       │ ✅ Sim       │
│ Logging de tentativas   │ ❌ Não       │ ✅ Sim       │
│ UX: Desabilita botão    │ ❌ Não       │ ✅ Sim       │
│ Segurança geral         │ ❌ Baixa     │ ✅ Alta      │
└─────────────────────────┴──────────────┴──────────────┘
```

---

## 🎯 Mapa Mental

```
                    DUPLICATE SUBMISSION
                           │
                    ┌──────┴──────┐
                    │             │
            PREVENÇÃO         DETECÇÃO
                │                 │
         ┌──────┴──────┐     ┌────┴─────┐
         │             │     │          │
      FRONTEND      BACKEND  LOGGING    │
         │             │              ALERTAS
         │             │
      BOTÃO         TOKEN
    DESABILITADO   IDEMPOTÊNCIA
         │             │
      SPINNER      VALIDAÇÃO
      LOADING      CONSUMO
                       │
                    CACHE
                    (1 hora)
```

---

## 📈 Gráfico de Chamados (Antes vs Depois)

```
ANTES (Problema):                 DEPOIS (Solução):
─────────────────────────────────────────────────────

Cliques: 1 2 3 4 5              Cliques: 1 2 3 4 5
         │ │ │ │ │                      │ ✓ ✓ ✓ ✓
         ▼ ▼ ▼ ▼ ▼                      ▼
        [1002][1003][1004][1005]       [1001]
         [1001]

Total: 5 chamados              Total: 1 chamado
Problema: CRÍTICO ❌           Status: RESOLVIDO ✅
```

---

## 🔑 Pontos-Chave

```
┌─────────────────────────────────────┐
│  1. TOKEN ÚNICO                     │
│     ├─ 64 caracteres aleatórios    │
│     ├─ Impossível adivinhar        │
│     └─ Gerado por: secrets.token_hex
│                                     │
│  2. USO ÚNICO                       │
│     ├─ Token = consumido após uso   │
│     ├─ Reutilização bloqueada       │
│     └─ Validado no servidor         │
│                                     │
│  3. TTL AUTOMÁTICO                  │
│     ├─ Expiração: 1 hora            │
│     ├─ Limpeza automática           │
│     └─ Sem memory leak              │
│                                     │
│  4. LOGGING                         │
│     ├─ Tentativas duplicadas        │
│     ├─ Auditoria completa           │
│     └─ Debug facilitado             │
│                                     │
│  5. DEFESA DUPLA                    │
│     ├─ Frontend: UX + segurança     │
│     └─ Backend: Validação crítica   │
└─────────────────────────────────────┘
```

---

**Versão:** 1.0  
**Data:** Janeiro 2025  
**Status:** Implementado ✅
