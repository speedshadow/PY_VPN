document.addEventListener('DOMContentLoaded', function() {
    // Adiciona verificação em tempo real do domínio
    const domainInput = document.getElementById('domain');
    if (!domainInput) {
        console.warn('Elemento com ID "domain" não encontrado na página https_setup.');
        return;
    }

    const domainStatus = document.createElement('div');
    domainStatus.className = 'mt-1 text-sm';
    
    // Garante que parentNode existe antes de tentar inserir
    if (domainInput.parentNode) {
        domainInput.parentNode.insertBefore(domainStatus, domainInput.nextSibling);
    } else {
        console.warn('Elemento "domainInput" não tem um parentNode.');
        return;
    }
    
    domainInput.addEventListener('blur', function() {
        const domain = this.value.trim();
        if (!domain) {
            domainStatus.textContent = ''; // Limpa status se o campo estiver vazio
            domainStatus.className = 'mt-1 text-sm';
            return;
        }
        
        domainStatus.textContent = 'Verificando domínio...';
        domainStatus.className = 'mt-1 text-sm text-blue-600';
        
        // Simples verificação de domínio (poderia ser uma chamada AJAX para o backend)
        if (domain.includes('.') && domain.length > 3) { // Adicionada verificação de comprimento mínimo
            domainStatus.textContent = 'Domínio parece válido';
            domainStatus.className = 'mt-1 text-sm text-green-600';
        } else {
            domainStatus.textContent = 'Domínio inválido. Use o formato: meusite.com';
            domainStatus.className = 'mt-1 text-sm text-red-600';
        }
    });
    console.log("https_setup_validation.js carregado e eventos anexados.");
});
