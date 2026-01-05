// script-abrir-chamado.js
// Sistema para prevenir múltiplas submissões de formulário + Validação Matemática

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

// ===== VALIDAÇÃO DO FORMULÁRIO DE VALIDAÇÃO MATEMÁTICA =====
async function validarRespostaMatematica() {
    const resposta = document.getElementById("math_resposta").value.trim();
    
    if (!resposta) {
        alert("Por favor, responda a pergunta de validação.");
        return false;
    }
    
    // Verifica se é um número válido
    if (isNaN(resposta)) {
        alert("Por favor, informe um número válido.");
        return false;
    }
    
    // Valida no backend
    try {
        const response = await fetch('/validar_resposta', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                resposta: resposta
            })
        });
        
        const data = await response.json();
        
        if (!data.valido) {
            alert(`❌ ${data.mensagem}`);
            return false;
        }
        
        // Resposta correta!
        return true;
    } catch (error) {
        console.error('Erro ao validar:', error);
        alert("Erro ao validar resposta. Tente novamente.");
        return false;
    }
}

// ===== PREVENÇÃO DE MÚLTIPLAS SUBMISSÕES =====
document.getElementById("conteudo").addEventListener("submit", async function(event) {
    const submitBtn = document.getElementById("submit-btn");
    const loadingSpinner = document.getElementById("loading-spinner");
    const form = document.getElementById("conteudo");

    event.preventDefault();

    // ===== VALIDA RESPOSTA MATEMÁTICA =====
    const respostaValida = await validarRespostaMatematica();
    if (!respostaValida) {
        return;
    }

    // ===== DESABILITA O BOTÃO =====
    // Previne cliques adicionais enquanto o formulário está sendo processado
    submitBtn.disabled = true;
    submitBtn.classList.add("opacity-50");
    submitBtn.style.cursor = "not-allowed";

    // ===== MOSTRA SPINNER DE CARREGAMENTO =====
    // Fornece feedback visual ao usuário
    loadingSpinner.classList.remove("d-none");

    // ===== SUBMIT DO FORMULÁRIO =====
    // Aguarda um pequeno delay antes de submeter para garantir que o UI foi atualizado
    setTimeout(() => {
        form.submit();
    }, 500);
});