// Controle de FOUC e inicialização de componentes
document.addEventListener("DOMContentLoaded", function() {
  // Aguardar carregamento de fontes
  document.fonts.ready.then(() => {
    document.documentElement.classList.add('fouc-ready');
  });

  if (window.lucide) {
    lucide.createIcons();
    console.log("Lucide icons initialized from custom_global_scripts.js");
  }

  // Skip to content for accessibility
  var skipLink = document.createElement('a');
  skipLink.href = '#main-content';
  // Classes base do Tailwind + classe customizada para estados
  skipLink.className = 'skip-link absolute left-0 bg-blue-600 text-white px-4 py-2 z-50'; 
  skipLink.textContent = 'Skip to main content';
  
  skipLink.addEventListener('focus', function() {
    this.classList.add('skip-link-focused');
  });
  
  skipLink.addEventListener('blur', function() {
    this.classList.remove('skip-link-focused');
  });
  
  document.body.insertBefore(skipLink, document.body.firstChild);
  console.log("Skip link added from custom_global_scripts.js");
});
