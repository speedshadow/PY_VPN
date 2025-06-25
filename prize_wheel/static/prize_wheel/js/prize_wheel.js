document.addEventListener('DOMContentLoaded', function () {
    const actualWheel = document.getElementById('actualWheel');
    let prizes = [];
    let currentRotation = 0; // To control the wheel's rotation

    function parsePrizeData() {
        const prizeDataElement = document.getElementById('prize-data-json'); // ID used by Django's json_script
        if (prizeDataElement) {
            try {
                // Django's json_script creates a <script> element with id 'prize-data-json'.
                // Its textContent is the JSON string.
                const jsonData = JSON.parse(prizeDataElement.textContent || prizeDataElement.innerHTML);
                // If the json_script used a different id for the content, we would have to access it differently.
                // Assuming jsonData is the array of prizes directly or an object containing it.
                // If json_script serializes the queryset directly, it might be a string of an array of objects.
                // If it's an array of objects with 'pk', 'model', 'fields', we need to extract 'fields'.
                // For now, let's assume it's an array of objects where each object has 'name', 'id', etc.
                // If the json_script output is like `[{'model': 'app.prize', 'pk':1, 'fields': {'name':'P1'}}, ...]`,
                // we will need to adjust the parsing.
                // For json_script, Django serializes the queryset. Let's check the exact format in the browser.
                // For now, let's assume it's an array of objects with the fields from the Prize model.
                console.log('Raw Prize Data from JSON script:', jsonData);
                if (Array.isArray(jsonData)) {
                    prizes = jsonData.map(p => p.fields || p); // If it's a full Django serialization, use p.fields
                } else if (jsonData && jsonData.prizes) {
                    prizes = jsonData.prizes; // If it's nested
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
        // Re-add the spin button if it was cleared
        const spinButtonHTML = `<button id="spinButton" 
                                    class="absolute w-20 h-20 bg-blue-500 hover:bg-blue-600 text-white font-bold rounded-full focus:outline-none focus:shadow-outline text-lg z-20 flex items-center justify-center shadow-md border-2 border-white">
                                Spin!
                            </button>`;
        actualWheel.insertAdjacentHTML('beforeend', spinButtonHTML);
        // Re-attach the event listener to the new spin button, or ensure the original one is not removed.
        // The best approach is not to clear the spin button. Let's adjust.
        // Let's assume the spinButton is OUTSIDE actualWheel for segment generation, or that actualWheel is a container for segments only.
        // From the HTML, the spinButton is INSIDE actualWheel. This complicates clearing.
        // Solution: Create a container for the segments INSIDE actualWheel.

        let segmentContainer = actualWheel.querySelector('#segmentContainer');
        if (!segmentContainer) {
            actualWheel.innerHTML = ''; // Clears everything, including the old spin button if it's here.
            segmentContainer = document.createElement('div');
            segmentContainer.id = 'segmentContainer';
            segmentContainer.className = 'absolute inset-0 w-full h-full'; // Occupies the entire wheel space
            actualWheel.appendChild(segmentContainer);
            actualWheel.insertAdjacentHTML('beforeend', spinButtonHTML); // Adds the spin button back
        } else {
            segmentContainer.innerHTML = ''; // Clears only the old segments
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
            // Prize text
            const prizeText = document.createElement('span');
            prizeText.textContent = prize.name || `Prize ${index + 1}`;
            prizeText.className = 'prize-text absolute top-[10%] left-1/2 transform -translate-x-1/2 text-center w-1/2'; 
            prizeText.style.color = 'black'; 
            prizeText.style.backgroundColor = 'rgba(255, 255, 255, 0.8)'; 
            prizeText.style.padding = '2px';
            prizeText.style.fontSize = '10px'; // Adjust position
            
            segment.appendChild(prizeText);

            // Apply rotation to position the segment
            // Each segment has 'anglePerSegment' width.
            // The rotation is (index * anglePerSegment) + (anglePerSegment / 2) to center the text, but clip-path will handle the shape.
            segment.style.transform = `rotate(${index * anglePerSegment}deg)`;
            // Style to create the slice shape (e.g., using clip-path or pseudo-elements)
            // Example with simple alternating colors (improve with Tailwind or dedicated CSS)
            segment.style.backgroundColor = index % 2 === 0 ? 'rgba(255, 165, 0, 0.7)' : 'rgba(255, 192, 203, 0.7)';
            // Clip-path for sector shape (simplified, needs exact adjustment)
            // This clip-path is for a sector from 0 to X degrees. We need one per segment.
            // For N segments, each has 360/N degrees.
            // Ex: clip-path: polygon(50% 50%, 100% 50%, 100% 0%); // Triangle for 90 degrees
            // The correct shape with clip-path for N segments is complex.
            // An easier approach might be to use an SVG or a wheel library.
            // For now, let's just place the rotated and colored divs.
            // The text also needs to be rotated correctly within each segment.

            // To simplify, let's just place the rotated text.
            // The visual styling of the wheel with segments is complex and iterative.
            // Let's focus on the logic first.
            segment.style.border = '1px solid #ccc'; // Just for visualization
            segment.setAttribute('data-prize-id', prize.id || prize.pk);

            segmentContainer.appendChild(segment);
        });
        // Re-assign the listener to spinButton if it was recreated
        // It's better to get the spinButton by ID again after innerHTML manipulation
        const newSpinButton = document.getElementById('spinButton');
        if (newSpinButton) {
            newSpinButton.addEventListener('click', handleSpinButtonClick); // Re-attach the handler
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

    // Function to get the CSRF token (necessary for POST requests in Django)
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

    // --- Popup Visibility Control ---
    // Example: Show the popup (can be triggered by a button on the page, etc.)
    // For testing, we can show it on page load if on a specific URL.
    // prizeWheelPopup.style.display = 'flex'; // Uncomment for immediate testing

    const openPopupButton = document.getElementById('openPrizeWheelPopup');
    console.log('Prize Wheel JS: openPopupButton element:', openPopupButton);

    // Function to open the popup (can be called by other scripts/events)
    window.openPrizeWheelPopup = function() {
        console.log('Prize Wheel JS: window.openPrizeWheelPopup function called');
        console.log('Prize Wheel JS: Attempting to display prizeWheelPopup:', prizeWheelPopup);
        if (prizeWheelPopup) prizeWheelPopup.style.display = 'flex'; else console.error('Prize Wheel JS: prizeWheelPopup element is null!');
        // Could load initial data here, like remaining attempts
        // or check if the wheel is active before showing.
        // For now, let's assume the spin button makes the first check.
        prizeWheelMessage.textContent = 'Click Spin to try your luck!';
        emailForm.style.display = 'none';
        spinButton.style.display = 'block';
        // TODO: Get and show remaining attempts
    }

    if (openPopupButton) {
        console.log('Prize Wheel JS: Adding click listener to openPopupButton');
        openPopupButton.addEventListener('click', function() {
            console.log('Prize Wheel JS: openPopupButton clicked!');
            window.openPrizeWheelPopup(); // Calls the function defined to open the popup
        });
    }

    if (closePrizeWheelPopupButton) {
        closePrizeWheelPopupButton.addEventListener('click', function () {
            prizeWheelPopup.style.display = 'none';
        });
    }

    // --- Logic for Spinning the Wheel ---
    function handleSpinButtonClick() {
        const spinButton = document.getElementById('spinButton'); // Get the button again
        if (!spinButton || spinButton.disabled) return;

        prizeWheelMessage.textContent = 'Spinning...';
        spinButton.disabled = true;

        // Initial rotation animation (simple example)
        let spinDuration = 3000; //ms
        let randomSpins = 3 + Math.floor(Math.random() * 3); // 3 to 5 extra spins
        currentRotation += (360 * randomSpins); // Adds random spins
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
                console.log('>>> WON PRIZE DETAIL (API) <<< ID:', data.prize_won.id, 'Name:', data.prize_won.name);
            } else {
                console.log('>>> NO PRIZE WON according to the API <<<');
            }
            console.log('Attempt ID from Spin API:', data.attempt_id);

            let finalAngle = currentRotation; // Base angle
            if (data.prize_won && prizes.length > 0) {
                const prizeWonId = data.prize_won.id;
                const prizeIndex = prizes.findIndex(p => (p.id || p.pk) === prizeWonId);
                
                if (prizeIndex !== -1) {
                    const anglePerSegment = 360 / prizes.length;
                    // We want the pointer (at the top, 0 or 360 degrees in the wheel's orientation)
                    // to point to the middle of the winning segment.
                    // If segment 0 is at the top (0-anglePerSegment degrees),
                    // its middle is anglePerSegment / 2.
                    // The angle of the `prizeIndex` segment is `prizeIndex * anglePerSegment`.
                    // The middle of the `prizeIndex` segment is `(prizeIndex * anglePerSegment) + (anglePerSegment / 2)`.
                    // The wheel needs to spin so that this angle is at the top (0/360).
                    // Therefore, the final rotation should be -( (prizeIndex * anglePerSegment) + (anglePerSegment / 2) )
                    // We add `currentRotation` so that the rotation is relative and continues to spin forward.
                    // And we ensure the wheel stops at the right place after the random spins.
                    let targetSegmentMiddleAngle = (prizeIndex * anglePerSegment) + (anglePerSegment / 2);
                    
                    // Adjust finalAngle so the wheel stops at the correct prize
                    // The rotation is clockwise. The pointer is at the top (0 degrees).
                    // If prize 0 is at 0 degrees, we want the wheel to stop at 0.
                    // If prize 1 is at X degrees, we want the wheel to stop at -X degrees.
                    // The `currentRotation` already has the full spins.
                    // We need to find the nearest multiple of 360 below `currentRotation`
                    let baseRotation = Math.floor(currentRotation / 360) * 360;
                    let prizeAngleOffset = 360 - targetSegmentMiddleAngle; // Angle to bring the middle of the segment to the top (0 degrees)
                    if (prizeAngleOffset === 360) prizeAngleOffset = 0;

                    finalAngle = baseRotation + prizeAngleOffset;
                    // To ensure the wheel always spins forward and stops at the right place,
                    // we might need more spins if the prizeAngleOffset is less than the current angle within the spin.
                    if (finalAngle < currentRotation) {
                         finalAngle += 360 * (Math.ceil((currentRotation - finalAngle)/360) + randomSpins); // Add more spins to ensure it spins forward
                    }
                    // Ensures the animation stops at the right place after the spins.
                    // The logic for `currentRotation` and `finalAngle` needs to be refined for a smooth and precise stop.
                    // This is a simplification.
                    // The idea is: currentRotation defines the spins, and the final angle is adjusted for the prize.
                    // Let's simplify: the total rotation is N spins + angle for the prize.
                    finalAngle = (360 * (randomSpins + 2)) - targetSegmentMiddleAngle; // N spins + adjustment for the prize

                    // Update the wheel's rotation to the won prize
                    if (actualWheel) actualWheel.style.transition = `transform ${spinDuration}ms cubic-bezier(0.25, 0.1, 0.25, 1)`; // Might need a different duration for the stop
                    if (actualWheel) actualWheel.style.transform = `rotate(${finalAngle}deg)`;
                    currentRotation = finalAngle; // Save the final rotation

                    prizeWonText.textContent = `Prize: ${data.prize_won.name} - ${data.prize_won.description}`;
                    attemptIdInput.value = data.attempt_id;
                    emailForm.style.display = 'block';
                    if(spinButton) spinButton.style.display = 'none'; // Hide spin button
                } else {
                    console.error('Won prize not found in the frontend prize list.');
                    if(spinButton) spinButton.disabled = false; // Re-enable if there was an error
                }
            } else {
                // No prize won, the wheel stops at a random position (or continues the rotation)
                if(spinButton) spinButton.disabled = false; // Re-enable if no prize was won and can spin again
                emailForm.style.display = 'none';
            }
            
            if (data.can_spin_again === false) {
                if(spinButton) spinButton.style.display = 'none';
                if (!data.prize_won) {
                    prizeWheelMessage.textContent += ' You have reached the limit of attempts for today.';
                }
            } else {
                // If can spin again and didn't win, the button has already been re-enabled.
                // If won, the button was hidden.
                if (!data.prize_won && spinButton) spinButton.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error spinning the wheel:', error);
            prizeWheelMessage.textContent = 'Error connecting to the server. Try again.';
            if(spinButton) spinButton.disabled = false;
        });
    }

    // Attach the handler to the initial spin button
    // This event listener will be for the button that is initially in the HTML.
    // If we recreate the button dynamically, we will need to re-attach.
    // In `createWheelSegments`, we are already trying to re-attach to the recreated button.
    const initialSpinButton = document.getElementById('spinButton');
    if (initialSpinButton) {
        initialSpinButton.addEventListener('click', handleSpinButtonClick);
    }

    // The spinButton logic was moved to handleSpinButtonClick and attached dynamically
    // if (spinButton) {
        // The spinButton logic was moved to handleSpinButtonClick and attached dynamically
        // spinButton.addEventListener('click', function () {


    // --- Email Submission Logic ---
    if (emailForm) {
        emailForm.addEventListener('submit', function (event) {
            event.preventDefault();
            const email = winnerEmailInput.value;
            const attempt_id = attemptIdInput.value; // This ID needs to be from the SpinAttempt

            if (!attempt_id) {
                prizeWheelMessage.textContent = 'Error: Attempt ID not found to submit email.';
                return;
            }

            submitEmailButton.disabled = true;
            prizeWheelMessage.textContent = 'Sending email...';

            console.log('Attempt ID value from input before submit:', attempt_id);
            fetch(`/prize-wheel/api/submit-email/${attempt_id}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded', // Django expects form data
                    'X-CSRFToken': csrftoken
                },
                body: `email=${encodeURIComponent(email)}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    prizeWheelMessage.textContent = `Error: ${data.error}`;
                    submitEmailButton.disabled = false;
                } else {
                    prizeWheelMessage.textContent = data.message;
                    emailForm.style.display = 'none'; // Hide form after success
                    // The user should not be able to spin again immediately after winning and submitting email,
                    // unless the 'can_spin_again' logic from the spin API already handles this.
                    // If the spinButton was hidden, it remains hidden.
                    // If the wheel is closed and reopened, the 'can spin' state will be re-evaluated.
                }
            })
            .catch(error => {
                console.error('Error submitting email:', error);
                prizeWheelMessage.textContent = 'Error sending email. Try again.';
                submitEmailButton.disabled = false;
            });
        });
    }

    // Initialize the wheel
    parsePrizeData();
    createWheelSegments();

    // Example of how to show the popup on a specific page (place in your main template or page)
    // if (window.location.pathname === '/specific-page/') { 
    //     openPrizeWheelPopup();
    // }
});
