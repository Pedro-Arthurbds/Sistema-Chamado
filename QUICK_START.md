# ⚡ Início Rápido - Copiar e Colar

Se você quer apenas implementar rápido sem ler toda a documentação, siga este guia.

---

## 🚀 Setup em 3 Minutos

### **Passo 1: Criar arquivo `app/idempotency.py`**

Copie e cole todo o código:

```python
# app/idempotency.py

import hashlib
import secrets
import time
from datetime import datetime, timedelta
from app.db import conectar_bd

_request_cache = {}
_CACHE_TTL = 3600

def gerar_token_idempotencia():
    """Gera um token único de idempotência para cada formulário."""
    return secrets.token_hex(32)

def validar_e_consumir_token(token):
    """
    Valida e consome um token de idempotência.
    Returns: True (válido) ou False (duplicado)
    """
    if not token:
        return False
    
    agora = time.time()
    chaves_expiradas = [chave for chave, (_, timestamp) in _request_cache.items() 
                        if agora - timestamp > _CACHE_TTL]
    for chave in chaves_expiradas:
        del _request_cache[chave]
    
    if token in _request_cache:
        return False
    
    _request_cache[token] = (True, agora)
    return True

def invalidar_token(token):
    """Remove um token do cache."""
    if token in _request_cache:
        del _request_cache[token]

def registrar_requisicao_duplicada(token, nome, contato, setor):
    """Log de requisições duplicadas para auditoria."""
    print(f"[AVISO] Requisição duplicada detectada!")
    print(f"  Token: {token}")
    print(f"  Usuário: {nome} ({contato})")
    print(f"  Setor: {setor}")
    print(f"  Horário: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
```

✅ **Pronto!**

---

### **Passo 2: Modificar `app/routes.py`**

**2a. Adicione este import no topo:**

```python
from app.idempotency import gerar_token_idempotencia, validar_e_consumir_token, registrar_requisicao_duplicada
```

**2b. Modifique a rota `home()`:**

```python
@app.route('/')
def home():
    chamados = buscar_chamados_ativos()
    idempotency_token = gerar_token_idempotencia()  # ← ADICIONE ESTA LINHA
    return render_template('pages/abrir_chamado.html', chamados=chamados, idempotency_token=idempotency_token)
```

**2c. Modifique a rota `abrir_chamado_route()` (adicione NO INÍCIO):**

```python
@app.route('/abrir_chamado', methods=['POST'])
def abrir_chamado_route():
    # ===== VALIDAÇÃO DE IDEMPOTÊNCIA =====
    idempotency_token = request.form.get('idempotency_token')
    
    if not validar_e_consumir_token(idempotency_token):
        nome = request.form.get('nome', 'Usuário')
        contato = request.form.get('contato', 'N/A')
        setor = request.form.get('setor', 'N/A')
        registrar_requisicao_duplicada(idempotency_token, nome, contato, setor)
        flash('Este chamado já foi enviado! Não é possível enviar o mesmo chamado novamente.', 'warning')
        return redirect('/')
    
    # ===== RESTO DO CÓDIGO MANTÉM IGUAL =====
    nome = request.form['nome']
    # ... resto do código...
```

✅ **Pronto!**

---

### **Passo 3: Modificar `templates/pages/abrir_chamado.html`**

**3a. Adicione token oculto (logo após `<form ...>`):**

```html
<form id="conteudo" method="POST" action="/abrir_chamado" enctype="multipart/form-data">
    <input type="hidden" name="idempotency_token" value="{{ idempotency_token }}">
    
    <!-- resto do formulário -->
```

**3b. Adicione spinner (após o botão de envio):**

```html
        <button type="submit" id="submit-btn" class="btn btn-primary w-100 btn-lg">
            <i class="bi bi-send"></i> Enviar Chamado
        </button>
        
        <!-- SPINNER -->
        <div id="loading-spinner" class="text-center mt-3 d-none">
            <div class="spinner-border spinner-border-sm text-primary" role="status">
                <span class="visually-hidden">Enviando...</span>
            </div>
            <p class="mt-2 text-primary fw-bold">Enviando chamado...</p>
        </div>
```

✅ **Pronto!**

---

### **Passo 4: Modificar `static/js/script-abrir-chamado.js`**

Substitua TUDO o arquivo com isto:

```javascript
// ===== VALIDAÇÃO DE ARQUIVO =====
document.addEventListener("DOMContentLoaded", function() {
    const arquivoInput = document.getElementById("arquivo");
    const fileError = document.getElementById("file-error");
    const clearFileBtn = document.getElementById("clear-file");
    const form = document.getElementById("conteudo");

    const extensoesPermitidas = ['.png', '.mp4', '.WMV', '.jpg', '.jpeg', '.gif', '.pdf', '.doc', '.docx'];

    arquivoInput.addEventListener("change", function() {
        if (arquivoInput.files.length > 0) {
            let arquivo = arquivoInput.files[0];
            let extensao = arquivo.name.substring(arquivo.name.lastIndexOf('.')).toLowerCase();

            if (!extensoesPermitidas.includes(extensao)) {
                fileError.innerText = "Tipo de arquivo não permitido. Envie apenas imagens, PDFs ou documentos do Word.";
                fileError.style.display = "block";
                arquivoInput.value = "";  
            } else {
                fileError.style.display = "none";
            }
        }
    });

    clearFileBtn.addEventListener("click", function() {
        arquivoInput.value = "";
        fileError.style.display = "none";
    });

    form.addEventListener("submit", function(event) {
        if (fileError.style.display === "block") {
            event.preventDefault();
            alert("Corrija os erros antes de enviar o chamado.");
        }
    });
});

// ===== VALIDAÇÃO DO reCAPTCHA =====
function removeError() {
    document.getElementById("recaptcha-error").classList.add("d-none");
}

// ===== PREVENÇÃO DE MÚLTIPLAS SUBMISSÕES =====
document.getElementById("conteudo").addEventListener("submit", function(event) {
    const submitBtn = document.getElementById("submit-btn");
    const loadingSpinner = document.getElementById("loading-spinner");
    const form = document.getElementById("conteudo");

    if (grecaptcha.getResponse() === "") {
        event.preventDefault();
        document.getElementById("recaptcha-error").classList.remove("d-none");
        return;
    }

    event.preventDefault();

    submitBtn.disabled = true;
    submitBtn.classList.add("opacity-50");
    submitBtn.style.cursor = "not-allowed";

    loadingSpinner.classList.remove("d-none");

    setTimeout(() => {
        form.submit();
    }, 500);
});
```

✅ **Pronto!**

---

## ✅ Verificação Rápida

Execute estes comandos:

```bash
# 1. Testar se arquivo Python existe
test -f app/idempotency.py && echo "✅ idempotency.py OK" || echo "❌ Arquivo não encontrado"

# 2. Testar se imports funcionam
python -c "from app.idempotency import gerar_token_idempotencia; print('✅ Import OK')"

# 3. Iniciar servidor
python run.py
```

---

## 🧪 Teste Rápido

1. Abrir navegador: `http://localhost:5001/`
2. Preencher formulário
3. Clicar "Enviar" 5 vezes rapidamente
4. Resultado esperado: **Apenas 1 chamado criado** ✅

---

## 🔍 Verificar Banco de Dados

```bash
# Após os testes, conectar ao MySQL:
mysql -u usuario -p database_name

# Contar chamados:
SELECT COUNT(*) FROM chamados;

# Listar últimos 5:
SELECT id, nome, contato FROM chamados ORDER BY id DESC LIMIT 5;
```

---

## ❓ Dúvidas Rápidas

**P: Preciso instalar algo novo?**  
R: Não! Usa `secrets` (built-in do Python).

**P: Vai quebrar meu código existente?**  
R: Não! Apenas adiciona funcionalidade.

**P: Token é salvo em banco de dados?**  
R: Não. Está em memória (mais rápido).

**P: E se reiniciar o servidor?**  
R: Cache é perdido, mas é normal. Para produção, use Redis.

**P: Como testo sem recarregar?**  
R: Via curl (ver arquivo `GUIA_TESTES.md`).

---

## 📞 Problemas?

1. **Botão não desabilita:**
   - F12 → Console → Verificar erros JavaScript

2. **Flask error `ImportError`:**
   - Verificar se `app/idempotency.py` existe
   - Verificar se está no mesmo diretório

3. **Token não aparece no HTML:**
   - Verificar se `{{ idempotency_token }}` está renderizando
   - Verificar F12 → Inspeção HTML

---

## 🎉 Pronto!

Sua aplicação agora está protegida contra múltiplos envios! 🛡️

**Próximas melhorias (opcional):**
- Redis para múltiplos servidores
- Flask-WTF para CSRF adicional
- Rate limiting com Flask-Limiter

---

**Versão:** 1.0  
**Status:** Implementado ✅
