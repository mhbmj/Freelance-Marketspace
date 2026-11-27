/**
 * Freelance Marketplace - Client-side Utilities
 * Show/Hide password toggle & Form helpers
 */

document.addEventListener('DOMContentLoaded', function () {
    // Show/Hide password toggles
    const toggleButtons = document.querySelectorAll('.password-toggle-btn');

    toggleButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('data-target');
            const targetInput = document.getElementById(targetId);

            if (!targetInput) return;

            const icon = this.querySelector('svg');
            if (targetInput.type === 'password') {
                targetInput.type = 'text';
                // Switch to eye-off icon
                this.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                        <line x1="1" y1="1" x2="23" y2="23"></line>
                    </svg>
                `;
                this.setAttribute('title', 'مخفی کردن رمز عبور');
            } else {
                targetInput.type = 'password';
                // Switch to eye icon
                this.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                `;
                this.setAttribute('title', 'نمایش رمز عبور');
            }
        });
    });

    // Frontend password match indicator
    const signupForm = document.getElementById('signup-form');
    if (signupForm) {
        const pass1 = document.getElementById('password');
        const pass2 = document.getElementById('password_confirm');
        const errorBox = document.getElementById('client-match-error');

        signupForm.addEventListener('submit', function (e) {
            if (pass1 && pass2 && pass1.value !== pass2.value) {
                e.preventDefault();
                if (errorBox) {
                    errorBox.textContent = 'رمز عبور و تکرار آن یکسان نیستند!';
                    errorBox.style.display = 'block';
                }
                pass2.focus();
            }
        });
    }

    // Password strength evaluator (سبز و قرمز)
    function setupPasswordStrength(inputId) {
        const input = document.getElementById(inputId);
        const container = document.getElementById('strength-container');
        const bar = document.getElementById('strength-bar');
        const text = document.getElementById('strength-text');

        if (!input || !container || !bar || !text) return;

        input.addEventListener('input', function () {
            const val = this.value;
            if (!val || val.length === 0) {
                container.style.display = 'none';
                return;
            }

            container.style.display = 'block';

            let score = 0;
            if (val.length >= 8) score++;
            if (val.length >= 12) score++;
            if (/[0-9]/.test(val) && /[a-zA-Z]/.test(val)) score++;
            if (/[^a-zA-Z0-9]/.test(val) || (/[A-Z]/.test(val) && /[a-z]/.test(val))) score++;

            // رد و ضعیف اعلام کردن رمزهای بسیار ساده
            const common = ['12345678', 'password', 'password123', 'qwerty123', '11111111', '123456789'];
            if (common.includes(val.toLowerCase()) || /^\d+$/.test(val) || /^[a-zA-Z]+$/.test(val)) {
                if (val.length < 12) score = 1;
            }

            bar.className = 'strength-bar-fill';
            text.className = 'strength-status-text';

            if (score <= 1) {
                bar.classList.add('weak');
                text.classList.add('weak');
                text.textContent = 'ضعیف و غیرقابل‌قبول (قرمز)';
            } else if (score === 2) {
                bar.classList.add('fair');
                text.classList.add('fair');
                text.textContent = 'متوسط';
            } else {
                bar.classList.add('strong');
                text.classList.add('strong');
                text.textContent = 'قوی و مطمئن (سبز)';
            }
        });
    }

    setupPasswordStrength('password');
    setupPasswordStrength('new_password');

    // جلوگیری از باز شدن فایل توسط رفتار پیش‌فرض مرورگر در صورت رها شدن تصادفی در هر جای صفحه
    window.addEventListener('dragover', function (e) {
        e.preventDefault();
    }, false);

    window.addEventListener('drop', function (e) {
        e.preventDefault();
    }, false);
});

// مدیریت نقطه اعلان پیام‌ها
function dismissMessageDot() {
    const dots = document.querySelectorAll('.nav-tiny-dot');
    dots.forEach(d => {
        d.style.opacity = '0';
        d.style.transform = 'scale(0)';
        setTimeout(() => { d.style.display = 'none'; }, 200);
    });
}
