function cookieBanner() {
    return {
        showBanner: true,
        init() {
            // Check if the cookie_consent cookie is already set
            if (document.cookie.split(';').some((item) => item.trim().startsWith('cookie_consent='))) {
                this.showBanner = false;
            }
        },
        acceptCookies() {
            // Set the cookie_consent cookie
            let date = new Date();
            date.setTime(date.getTime() + (365 * 24 * 60 * 60 * 1000)); // Expires in 1 year
            document.cookie = "cookie_consent=true; expires=" + date.toUTCString() + "; path=/; SameSite=Lax";
            this.showBanner = false;
        }
    }
}
window.cookieBanner = cookieBanner;
