document.addEventListener('DOMContentLoaded', function() {
    console.log('Prize Wheel JS: DOMContentLoaded');
    
    const prizeWheelPopup = document.getElementById('prizeWheelPopup');
    const openPopupButton = document.getElementById('openPrizeWheelPopup');
    const closePopupButton = document.getElementById('closePrizeWheelPopup');
    const spinButton = document.getElementById('spinWheel');
    const prizeMessage = document.getElementById('prizeMessage');
    const actualWheel = document.getElementById('actualWheel');
    
    console.log('Prize Wheel JS: prizeWheelPopup element: ', prizeWheelPopup);
    
    let isSpinning = false;
    let prizes = [];
    let totalProbability = 0;
    
    // Get prize data from the JSON script tag
    try {
        const prizeDataScript = document.getElementById('prizeData');
        if (prizeDataScript) {
            const rawData = JSON.parse(prizeDataScript.textContent);
            console.log('Raw Prize Data from JSON script: ', rawData);
            prizes = rawData;
            prizes.forEach(prize => {
                totalProbability += prize.probability;
            });
            console.log('Parsed Prizes: ', prizes);
        } else {
            console.log('No prize data script found');
        }
    } catch (error) {
        console.error('Error parsing prize data:', error);
    }

    if (!prizes.length) {
        console.log('No prize data found or parsed. Wheel segments cannot be created.');
    }

    function createWheelSegments() {
        console.log('[createWheelSegments] Called.');
        console.log('[createWheelSegments] actualWheel element: ', actualWheel);
        
        if (!prizes.length) {
            console.log('[createWheelSegments] Aborting: No prize data available or prizes array is empty.');
            return;
        }

        // Clear existing segments
        actualWheel.innerHTML = '';

        const totalSegments = prizes.length;
        const segmentAngle = 360 / totalSegments;
        
        prizes.forEach((prize, index) => {
            const segment = document.createElement('div');
            segment.className = 'absolute inset-0';
            
            // Calculate rotation for this segment
            const rotation = index * segmentAngle;
            
            segment.style.cssText = `
                clip-path: polygon(50% 50%, 50% 0%, ${50 + 50 * Math.cos((rotation + segmentAngle) * Math.PI / 180)}% ${50 + 50 * Math.sin((rotation + segmentAngle) * Math.PI / 180)}%, 50% 50%);
                background-color: ${prize.color};
                transform: rotate(${rotation}deg);
            `;
            
            const label = document.createElement('div');
            label.className = 'absolute left-1/2 text-white font-bold text-sm';
            label.style.cssText = `
                transform: translateX(-50%) rotate(${rotation + segmentAngle/2}deg) translateY(-40%);
                transform-origin: bottom;
            `;
            label.textContent = prize.label;
            
            segment.appendChild(label);
            actualWheel.appendChild(segment);
        });
        
        // Add center point
        const centerPoint = document.createElement('div');
        centerPoint.className = 'absolute w-4 h-4 bg-blue-600 rounded-full';
        centerPoint.style.cssText = 'left: calc(50% - 0.5rem); top: calc(50% - 0.5rem);';
        actualWheel.appendChild(centerPoint);
    }

    function spinWheel() {
        if (isSpinning) return;
        isSpinning = true;
        
        // Generate random number for probability
        const rand = Math.random() * totalProbability;
        let currentSum = 0;
        let winningPrize;
        
        // Determine winning prize based on probabilities
        for (const prize of prizes) {
            currentSum += prize.probability;
            if (rand <= currentSum) {
                winningPrize = prize;
                break;
            }
        }
        
        // Calculate random spins (3-5 full rotations) plus the angle to the winning segment
        const totalSpins = (3 + Math.random() * 2) * 360;
        const prizeIndex = prizes.indexOf(winningPrize);
        const segmentAngle = 360 / prizes.length;
        const finalAngle = totalSpins + (prizeIndex * segmentAngle);
        
        // Apply the spinning animation
        actualWheel.style.transition = 'transform 4s cubic-bezier(0.17, 0.67, 0.12, 0.99)';
        actualWheel.style.transform = `rotate(${-finalAngle}deg)`;
        
        // Show the result after animation
        setTimeout(() => {
            prizeMessage.textContent = `Parabéns! Você ganhou ${winningPrize.label}!`;
            prizeMessage.classList.remove('hidden');
            isSpinning = false;
        }, 4000);
    }

    // Event Listeners
    if (openPopupButton) {
        console.log('Prize Wheel JS: Adding click listener to openPopupButton');
        openPopupButton.addEventListener('click', () => {
            prizeWheelPopup.style.display = 'flex';
            createWheelSegments();
            prizeMessage.classList.add('hidden');
            actualWheel.style.transition = 'none';
            actualWheel.style.transform = 'rotate(0deg)';
        });
    }

    if (closePopupButton) {
        closePopupButton.addEventListener('click', () => {
            prizeWheelPopup.style.display = 'none';
        });
    }

    if (spinButton) {
        spinButton.addEventListener('click', spinWheel);
    }
});
