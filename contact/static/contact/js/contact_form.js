function contactForm() {
    return {
        form: { name: "", email: "", subject: "", message: "" },
        challenge: { num1: Math.floor(Math.random()*10)+1, num2: Math.floor(Math.random()*10)+1, answer: '' },
        success: false,
        error: "",
        loading: false,
        resetChallenge() {
            this.challenge.num1 = Math.floor(Math.random()*10)+1;
            this.challenge.num2 = Math.floor(Math.random()*10)+1;
            this.challenge.answer = '';
        },
        async submit() {
            this.loading = true;
            this.success = false;
            this.error = false;
            // Anti-spam validation
            if (parseInt(this.challenge.answer) !== (this.challenge.num1 + this.challenge.num2)) {
                this.error = 'Anti-spam: resposta errada.';
                this.loading = false;
                this.resetChallenge();
                return;
            }
            try {
                const response = await fetch(window.location.pathname, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-Requested-With": "XMLHttpRequest",
                        "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
                    },
                    body: JSON.stringify({ ...this.form, challenge_num1: this.challenge.num1, challenge_num2: this.challenge.num2, challenge_answer: this.challenge.answer }),
                });
                if (response.ok) {
                    this.success = true;
                    this.form = { name: "", email: "", subject: "", message: "" };
                    setTimeout(() => { this.success = false; }, 3000);
                } else {
                    const data = await response.json();
                    this.error = typeof data.error === 'string' ? data.error : "An error occurred.";
                }
            } catch (e) {
                this.error = "Network error.";
            }
            this.loading = false;
        },
    };
}
