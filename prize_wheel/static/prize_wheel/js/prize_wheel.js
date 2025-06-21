document.addEventListener('DOMContentLoaded', function () {
    const actualWheel = document.getElementById('actualWheel');
    let prizes = [];
    let currentRotation = 0; // Para controlar a rotação da roda

    function parsePrizeData() {
        const prizeDataElement = document.getElementById('prize-data-json'); // ID usado pelo json_script do Django
        if (prizeDataElement) {
            try {
                // O json_script do Django cria um elemento <script> com id 'prize-data-json'.
                // O seu textContent é a string JSON.
                const jsonData = JSON.parse(prizeDataElement.textContent || prizeDataElement.innerHTML);
                // Se o json_script usou o id 'prize-data-json' para o conteúdo, teríamos que acessá-lo de forma diferente.
                // Assumindo que jsonData é o array de prémios diretamente ou um objeto que o contém.
                // Se o json_script serializa o queryset diretamente, pode ser uma string de um array de objetos.
                // Se for um array de objetos com 'pk', 'model', 'fields', precisamos extrair 'fields'.
                // Vamos assumir por agora que é um array de objetos onde cada objeto tem 'name', 'id', etc.
                // Se o output do json_script for como `[{'model': 'app.prize', 'pk':1, 'fields': {'name':'P1'}}, ...]`, 
                // precisaremos ajustar o parse.
                // Para o json_script, o Django serializa o queryset. Vamos verificar o formato exato no navegador.
                // Por agora, vamos assumir que é um array de objetos com os campos do modelo Prize.
                console.log('Raw Prize Data from JSON script:', jsonData);
                if (Array.isArray(jsonData)) {
                    prizes = jsonData.map(p => p.fields || p); // Se for serialização completa do Django, use p.fields
                } else if (jsonData && jsonData.prizes) {
                    prizes = jsonData.prizes; // Se estiver aninhado
                } else {
                    prizes = [];
                    console.error('Prize data is not in expected array format or jsonData.prizes');
                }
                console.log('Parsed Prizes:', prizes);
            } catch (e) {
                console.error('Error parsing prize data:', e);
                prizes = [];
            }
        }
        if (!prizes || prizes.length === 0) {
            console.warn('No prize data found or parsed. Wheel segments cannot be created.');
        }
    }

    function createWheelSegments() {
    console.log('[createWheelSegments] Called.');
    console.log('[createWheelSegments] actualWheel element:', actualWheel);
        if (!actualWheel) {
            console.error('[createWheelSegments] Aborting: actualWheel element not found.');
            return;
        }
        if (!prizes || prizes.length === 0) {
            console.error('[createWheelSegments] Aborting: No prize data available or prizes array is empty.');
            actualWheel.innerHTML = '<p class="text-center text-gray-500">No prizes to display.</p>';
            const existingSpinButton = document.getElementById('spinButton');
            if (existingSpinButton) existingSpinButton.remove();
            return;
        }
        actualWheel.innerHTML = ''; // Clear previous segments and spin button
        console.log('[createWheelSegments] actualWheel cleared.');
        // Re-adicionar o botão de spin se ele foi limpo
        const spinButtonHTML = `<button id="spinButton" 
                                    class="absolute w-20 h-20 bg-blue-500 hover:bg-blue-600 text-white font-bold rounded-full focus:outline-none focus:shadow-outline text-lg z-20 flex items-center justify-center shadow-md border-2 border-white">
                                Girar!
                            </button>`;
        actualWheel.insertAdjacentHTML('beforeend', spinButtonHTML);
        // Re-anexar o event listener ao novo botão spin, ou garantir que o original não seja removido.
        // A melhor abordagem é não limpar o botão spin. Vamos ajustar.
        // Vamos assumir que o botão spinButton está FORA do actualWheel para a geração de segmentos, ou que o actualWheel é um container para os segmentos apenas.
        // Pelo HTML, o spinButton está DENTRO do actualWheel. Isso complica a limpeza.
        // Solução: Criar um container para os segmentos DENTRO do actualWheel.

        let segmentContainer = actualWheel.querySelector('#segmentContainer');
        if (!segmentContainer) {
            actualWheel.innerHTML = ''; // Limpa tudo, incluindo o botão spin antigo se estiver aqui.
            segmentContainer = document.createElement('div');
            segmentContainer.id = 'segmentContainer';
            segmentContainer.className = 'absolute inset-0 w-full h-full'; // Ocupa todo o espaço da roda
            actualWheel.appendChild(segmentContainer);
            actualWheel.insertAdjacentHTML('beforeend', spinButtonHTML); // Adiciona o botão spin de volta
        } else {
            segmentContainer.innerHTML = ''; // Limpa apenas os segmentos antigos
        }

        const numPrizes = prizes.length;
        const anglePerPrize = 360 / numPrizes;
        console.log(`[createWheelSegments] Number of prizes: ${numPrizes}, Angle per prize: ${anglePerPrize}`);
        const anglePerSegment = 360 / numPrizes;

        prizes.forEach((prize, index) => {
            console.log(`[createWheelSegments] Creating segment ${index + 1} for prize:`, prize);
            const segment = document.createElement('div');
            segment.className = 'wheel-segment absolute w-full h-full origin-center'; 
            segment.style.border = `2px solid ${['red', 'green', 'blue', 'orange', 'purple'][index % 5]}`;
            segment.style.opacity = '0.7'; // DEBUG OPACITY
            segment.style.backgroundColor = index % 2 === 0 ? '#E0E0E0' : '#F5F5F5'; // Alternating light gray colors
            // Texto do prémio
            const prizeText = document.createElement('span');
            prizeText.textContent = prize.name || `Prémio ${index + 1}`;
            prizeText.className = 'prize-text absolute top-[10%] left-1/2 transform -translate-x-1/2 text-center w-1/2'; 
            prizeText.style.color = 'black'; 
            prizeText.style.backgroundColor = 'rgba(255, 255, 255, 0.8)'; 
            prizeText.style.padding = '2px';
            prizeText.style.fontSize = '10px'; // Ajustar posição
            
            segment.appendChild(prizeText);

            // Aplicar rotação para posicionar o segmento
            // Cada segmento tem 'anglePerSegment' de largura.
            // A rotação é (index * anglePerSegment) + (anglePerSegment / 2) para centralizar o texto, mas o clip-path cuidará da forma.
            segment.style.transform = `rotate(${index * anglePerSegment}deg)`;
            // Estilo para criar a forma de fatia (ex: usando clip-path ou pseudo-elementos)
            // Exemplo com cores alternadas simples (melhorar com Tailwind ou CSS dedicado)
            segment.style.backgroundColor = index % 2 === 0 ? 'rgba(255, 165, 0, 0.7)' : 'rgba(255, 192, 203, 0.7)';
            // Clip-path para forma de setor (simplificado, precisa de ajuste exato)
            // Este clip-path é para um setor de 0 a X graus. Precisamos de um por segmento.
            // Para um número N de segmentos, cada um tem 360/N graus.
            // Ex: clip-path: polygon(50% 50%, 100% 50%, 100% 0%); // Triângulo para 90 graus
            // A forma correta com clip-path para N segmentos é complexa.
            // Uma abordagem mais fácil pode ser usar um SVG ou uma biblioteca de rodas.
            // Por agora, vamos apenas colocar os divs rotacionados e coloridos.
            // O texto também precisa ser rotacionado corretamente dentro de cada segmento.

            // Para simplificar, vamos apenas colocar o texto rotacionado.
            // A estilização visual da roda com segmentos é complexa e iterativa.
            // Vamos focar na lógica primeiro.
            segment.style.border = '1px solid #ccc'; // Apenas para visualização
            segment.setAttribute('data-prize-id', prize.id || prize.pk);

            segmentContainer.appendChild(segment);
        });
        // Re-atribuir o listener ao spinButton se ele foi recriado
        // É melhor pegar o spinButton pelo ID novamente após a manipulação do innerHTML
        const newSpinButton = document.getElementById('spinButton');
        if (newSpinButton) {
            newSpinButton.addEventListener('click', handleSpinButtonClick); // Reanexar o handler
        } else {
            console.error('Spin button not found after creating segments!');
        }
    }


    console.log('Prize Wheel JS: DOMContentLoaded');
    const prizeWheelPopup = document.getElementById('prizeWheelPopup');
    console.log('Prize Wheel JS: prizeWheelPopup element:', prizeWheelPopup);
    const closePrizeWheelPopupButton = document.getElementById('closePrizeWheelPopup');
    const spinButton = document.getElementById('spinButton');
    const prizeWheelMessage = document.getElementById('prizeWheelMessage');
    const emailForm = document.getElementById('emailForm');
    const winnerEmailInput = document.getElementById('winnerEmail');
    const attemptIdInput = document.getElementById('attemptId');
    const prizeWonText = document.getElementById('prizeWonText');
    const submitEmailButton = document.getElementById('submitEmailButton');
    const attemptsLeftMessage = document.getElementById('attemptsLeftMessage');

    // Função para obter o CSRF token (necessário para requisições POST no Django)
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // --- Controle de Visibilidade do Popup ---
    // Exemplo: Mostrar o popup (pode ser acionado por um botão na página, etc.)
    // Para testar, podemos mostrar ao carregar a página se estiver em uma URL específica.
    // prizeWheelPopup.style.display = 'flex'; // Descomente para teste imediato

    const openPopupButton = document.getElementById('openPrizeWheelPopup');
    console.log('Prize Wheel JS: openPopupButton element:', openPopupButton);

    // Função para abrir o popup (pode ser chamada por outros scripts/eventos)
    window.openPrizeWheelPopup = function() {
        console.log('Prize Wheel JS: window.openPrizeWheelPopup function called');
        console.log('Prize Wheel JS: Attempting to display prizeWheelPopup:', prizeWheelPopup);
        if (prizeWheelPopup) prizeWheelPopup.style.display = 'flex'; else console.error('Prize Wheel JS: prizeWheelPopup element is null!');
        // Poderia carregar dados iniciais aqui, como tentativas restantes
        // ou verificar se a roda está ativa antes de mostrar.
        // Por enquanto, vamos assumir que o botão de girar faz a primeira verificação.
        prizeWheelMessage.textContent = 'Clique em Girar para tentar a sua sorte!';
        emailForm.style.display = 'none';
        spinButton.style.display = 'block';
        // TODO: Obter e mostrar tentativas restantes
    }

    if (openPopupButton) {
        console.log('Prize Wheel JS: Adding click listener to openPopupButton');
        openPopupButton.addEventListener('click', function() {
            console.log('Prize Wheel JS: openPopupButton clicked!');
            window.openPrizeWheelPopup(); // Chama a função definida para abrir o popup
        });
    }

    if (closePrizeWheelPopupButton) {
        closePrizeWheelPopupButton.addEventListener('click', function () {
            prizeWheelPopup.style.display = 'none';
        });
    }

    // --- Lógica de Girar a Roda ---
    function handleSpinButtonClick() {
        const spinButton = document.getElementById('spinButton'); // Obter o botão novamente
        if (!spinButton || spinButton.disabled) return;

        prizeWheelMessage.textContent = 'Girando...';
        spinButton.disabled = true;

        // Animação de rotação inicial (exemplo simples)
        let spinDuration = 3000; //ms
        let randomSpins = 3 + Math.floor(Math.random() * 3); // 3 a 5 voltas extras
        currentRotation += (360 * randomSpins); // Adiciona voltas aleatórias
        if (actualWheel) actualWheel.style.transition = `transform ${spinDuration}ms cubic-bezier(0.25, 0.1, 0.25, 1)`;
        if (actualWheel) actualWheel.style.transform = `rotate(${currentRotation}deg)`;

        fetch('/prize-wheel/api/spin/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
        })
        .then(response => response.json())
        .then(data => {
            prizeWheelMessage.textContent = data.message;
            console.log('Spin API Response Data:', data);
            if (data.prize_won) {
                console.log('>>> DETALHE DO PRÉMIO GANHO (API) <<< ID:', data.prize_won.id, 'Nome:', data.prize_won.name);
            } else {
                console.log('>>> NENHUM PRÉMIO GANHO segundo a API <<<');
            }
            console.log('Attempt ID from Spin API:', data.attempt_id);

            let finalAngle = currentRotation; // Ângulo base
            if (data.prize_won && prizes.length > 0) {
                const prizeWonId = data.prize_won.id;
                const prizeIndex = prizes.findIndex(p => (p.id || p.pk) === prizeWonId);
                
                if (prizeIndex !== -1) {
                    const anglePerSegment = 360 / prizes.length;
                    // Queremos que o ponteiro (no topo, 0 graus ou 360 graus na orientação da roda)
                    // aponte para o meio do segmento vencedor.
                    // Se o segmento 0 está no topo (0-anglePerSegment graus),
                    // o seu meio é anglePerSegment / 2.
                    // O ângulo do segmento `prizeIndex` é `prizeIndex * anglePerSegment`.
                    // O meio do segmento `prizeIndex` é `(prizeIndex * anglePerSegment) + (anglePerSegment / 2)`.
                    // A roda precisa girar para que este ângulo esteja no topo (0/360).
                    // Portanto, a rotação final deve ser -( (prizeIndex * anglePerSegment) + (anglePerSegment / 2) )
                    // Adicionamos `currentRotation` para que a rotação seja relativa e continue a girar para a frente.
                    // E garantimos que a roda pare no sítio certo após as voltas aleatórias.
                    let targetSegmentMiddleAngle = (prizeIndex * anglePerSegment) + (anglePerSegment / 2);
                    
                    // Ajustar finalAngle para que a roda pare no prémio correto
                    // A rotação é no sentido horário. O ponteiro está em cima (0 graus).
                    // Se o prémio 0 está em 0 graus, queremos que a roda pare em 0.
                    // Se o prémio 1 está em X graus, queremos que a roda pare em -X graus.
                    // O `currentRotation` já tem as voltas completas.
                    // Precisamos encontrar o múltiplo de 360 mais próximo abaixo de `currentRotation`
                    let baseRotation = Math.floor(currentRotation / 360) * 360;
                    let prizeAngleOffset = 360 - targetSegmentMiddleAngle; // Ângulo para trazer o meio do segmento para o topo (0 graus)
                    if (prizeAngleOffset === 360) prizeAngleOffset = 0;

                    finalAngle = baseRotation + prizeAngleOffset;
                    // Para garantir que a roda sempre gire para a frente e pare no sítio certo,
                    // podemos precisar de mais voltas se o prizeAngleOffset for menor que o ângulo atual dentro da volta.
                    if (finalAngle < currentRotation) {
                         finalAngle += 360 * (Math.ceil((currentRotation - finalAngle)/360) + randomSpins); // Adiciona mais voltas para garantir que gira para frente
                    }
                    // Garante que a animação pare no local certo após as voltas.
                    // A lógica de `currentRotation` e `finalAngle` precisa ser refinada para uma paragem suave e precisa.
                    // Esta é uma simplificação.
                    // A ideia é: currentRotation define as voltas, e o ângulo final é ajustado para o prémio.
                    // Vamos simplificar: a rotação total é N voltas + ângulo para o prémio.
                    finalAngle = (360 * (randomSpins + 2)) - targetSegmentMiddleAngle; // N voltas + ajuste para o prémio

                    // Atualiza a rotação da roda para o prémio ganho
                    if (actualWheel) actualWheel.style.transition = `transform ${spinDuration}ms cubic-bezier(0.25, 0.1, 0.25, 1)`; // Pode precisar de uma duração diferente para a paragem
                    if (actualWheel) actualWheel.style.transform = `rotate(${finalAngle}deg)`;
                    currentRotation = finalAngle; // Salva a rotação final

                    prizeWonText.textContent = `Prémio: ${data.prize_won.name} - ${data.prize_won.description}`;
                    attemptIdInput.value = data.attempt_id;
                    emailForm.style.display = 'block';
                    if(spinButton) spinButton.style.display = 'none'; // Esconder botão de girar
                } else {
                    console.error('Prémio ganho não encontrado na lista de prémios do frontend.');
                    if(spinButton) spinButton.disabled = false; // Reativar se houve erro
                }
            } else {
                // Sem prémio ganho, a roda para numa posição aleatória (ou na continuação da rotação)
                if(spinButton) spinButton.disabled = false; // Reativar se não ganhou e pode girar de novo
                emailForm.style.display = 'none';
            }
            
            if (data.can_spin_again === false) {
                if(spinButton) spinButton.style.display = 'none';
                if (!data.prize_won) {
                    prizeWheelMessage.textContent += ' Você atingiu o limite de tentativas por hoje.';
                }
            } else {
                // Se pode girar de novo e não ganhou, o botão já foi reativado.
                // Se ganhou, o botão foi escondido.
                if (!data.prize_won && spinButton) spinButton.disabled = false;
            }
        })
        .catch(error => {
            console.error('Erro ao girar a roda:', error);
            prizeWheelMessage.textContent = 'Erro ao conectar com o servidor. Tente novamente.';
            if(spinButton) spinButton.disabled = false;
        });
    }

    // Anexar o handler ao botão de girar inicial
    // Este event listener será para o botão que está inicialmente no HTML.
    // Se recriarmos o botão dinamicamente, precisaremos re-anexar.
    // No `createWheelSegments`, já estamos a tentar re-anexar ao botão recriado.
    const initialSpinButton = document.getElementById('spinButton');
    if (initialSpinButton) {
        initialSpinButton.addEventListener('click', handleSpinButtonClick);
    }

    // A lógica do spinButton foi movida para handleSpinButtonClick e anexada dinamicamente
    // if (spinButton) {
        // A lógica do spinButton foi movida para handleSpinButtonClick e anexada dinamicamente
        // spinButton.addEventListener('click', function () {


    // --- Lógica de Submeter Email ---
    if (emailForm) {
        emailForm.addEventListener('submit', function (event) {
            event.preventDefault();
            const email = winnerEmailInput.value;
            const attempt_id = attemptIdInput.value; // Este ID precisa ser o da SpinAttempt

            if (!attempt_id) {
                prizeWheelMessage.textContent = 'Erro: ID da tentativa não encontrado para submeter email.';
                return;
            }

            submitEmailButton.disabled = true;
            prizeWheelMessage.textContent = 'Enviando email...';

            console.log('Attempt ID value from input before submit:', attempt_id);
            fetch(`/prize-wheel/api/submit-email/${attempt_id}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded', // Django espera dados de formulário
                    'X-CSRFToken': csrftoken
                },
                body: `email=${encodeURIComponent(email)}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    prizeWheelMessage.textContent = `Erro: ${data.error}`;
                    submitEmailButton.disabled = false;
                } else {
                    prizeWheelMessage.textContent = data.message;
                    emailForm.style.display = 'none'; // Esconder formulário após sucesso
                    // O usuário não deve poder girar novamente imediatamente após ganhar e submeter email,
                    // a menos que a lógica de 'can_spin_again' da API de spin já contemple isso.
                    // Se o spinButton foi escondido, ele permanece escondido.
                    // Se a roda for fechada e reaberta, o estado de 'pode girar' será reavaliado.
                }
            })
            .catch(error => {
                console.error('Erro ao submeter email:', error);
                prizeWheelMessage.textContent = 'Erro ao enviar email. Tente novamente.';
                submitEmailButton.disabled = false;
            });
        });
    }

    // Inicializar a roda
    parsePrizeData();
    createWheelSegments();

    // Exemplo de como mostrar o popup numa página específica (coloque no seu template principal ou página)
    // if (window.location.pathname === '/pagina-especifica/') { 
    //     openPrizeWheelPopup();
    // }
});
