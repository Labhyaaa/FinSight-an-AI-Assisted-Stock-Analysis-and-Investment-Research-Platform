/**
 * FinSight – Auth JS
 * Handles: OTP Login, Password Login, Signup OTP verification
 */

// ══════════════════════════════════════════════════════════════
//  OTP LOGIN FLOW (login.html)
// ══════════════════════════════════════════════════════════════

let loginIdentifier = '';
let countdownInterval = null;

const identifierForm = document.getElementById('identifier-form');
if (identifierForm) {
    // ── Step 1: Send OTP ──
    identifierForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        loginIdentifier = document.getElementById('identifier-input').value.trim();
        const btn = document.getElementById('send-otp-btn');
        btn.disabled = true;
        btn.textContent = 'Sending...';

        try {
            const data = await api.post('/auth/send-otp', { identifier: loginIdentifier });
            document.getElementById('masked-contact').textContent = data.masked_contact || loginIdentifier;
            switchStep('step-identifier', 'step-otp');
            showToast('OTP sent! Check your email/console', 'success');
            startCountdown(30);
            // Focus first OTP digit
            setTimeout(() => document.querySelector('#otp-group .otp-digit')?.focus(), 100);
        } catch (err) {
            showToast(err.error || 'Failed to send OTP', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Get OTP';
        }
    });

    // ── OTP digit inputs: auto-advance + paste support ──
    document.querySelectorAll('#otp-group .otp-digit').forEach(input => {
        input.addEventListener('input', (e) => {
            const val = e.target.value.replace(/\D/g, '');
            e.target.value = val;
            if (val && parseInt(e.target.dataset.index) < 5) {
                e.target.nextElementSibling?.focus();
            }
            // Auto-submit when all 6 digits are filled
            const allDigits = document.querySelectorAll('#otp-group .otp-digit');
            const otp = Array.from(allDigits).map(d => d.value).join('');
            if (otp.length === 6) {
                verifyLoginOtp();
            }
        });
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && !e.target.value && parseInt(e.target.dataset.index) > 0) {
                e.target.previousElementSibling?.focus();
            }
        });
        // Handle paste
        input.addEventListener('paste', (e) => {
            e.preventDefault();
            const paste = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '');
            const digits = document.querySelectorAll('#otp-group .otp-digit');
            paste.split('').slice(0, 6).forEach((char, i) => {
                if (digits[i]) digits[i].value = char;
            });
            if (paste.length >= 6) verifyLoginOtp();
        });
    });
}


// ── Step 2: Verify OTP ──
window.verifyLoginOtp = async function() {
    const digits = document.querySelectorAll('#otp-group .otp-digit');
    const otp = Array.from(digits).map(d => d.value).join('');

    if (otp.length !== 6) {
        showToast('Please enter the complete 6-digit OTP', 'error');
        return;
    }

    const btn = document.getElementById('verify-otp-btn');
    btn.disabled = true;
    btn.textContent = 'Verifying...';

    try {
        const data = await api.post('/auth/verify-login-otp', {
            identifier: loginIdentifier,
            otp: otp
        });
        Auth.setToken(data.access_token);
        Auth.setUser(data.user);
        showToast('Login successful!', 'success');
        clearInterval(countdownInterval);
        setTimeout(() => {
            window.location.href = data.user.role === 'admin'
                ? '/pages/admin.html'
                : '/pages/dashboard.html';
        }, 500);
    } catch (err) {
        showToast(err.error || 'Invalid OTP', 'error');
        // Clear OTP inputs
        digits.forEach(d => d.value = '');
        digits[0]?.focus();
    } finally {
        btn.disabled = false;
        btn.textContent = 'Verify & Login';
    }
};


// ── Resend OTP ──
window.resendOtp = async function(e) {
    if (e) e.preventDefault();
    try {
        await api.post('/auth/resend-otp', { identifier: loginIdentifier });
        showToast('OTP resent!', 'success');
        startCountdown(30);
    } catch (err) {
        showToast(err.error || 'Failed to resend', 'error');
    }
};


// ── Password login fallback ──
window.showPasswordLogin = function() {
    switchStep('step-identifier', 'step-password');
};

const passwordForm = document.getElementById('password-form');
if (passwordForm) {
    passwordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('pw-email').value.trim();
        const password = document.getElementById('pw-password').value;

        try {
            const data = await api.post('/auth/login', { email, password });
            Auth.setToken(data.access_token);
            Auth.setUser(data.user);
            showToast('Login successful!', 'success');
            setTimeout(() => {
                window.location.href = data.user.role === 'admin'
                    ? '/pages/admin.html'
                    : '/pages/dashboard.html';
            }, 500);
        } catch (err) {
            if (err.requires_verification) {
                showToast('Email not verified. Check your email for OTP.', 'info');
            } else {
                showToast(err.error || 'Login failed', 'error');
            }
        }
    });
}


// ══════════════════════════════════════════════════════════════
//  NAVIGATION HELPERS
// ══════════════════════════════════════════════════════════════

window.goBack = function(targetStepId) {
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    document.getElementById(targetStepId).classList.add('active');
};

function switchStep(fromId, toId) {
    document.getElementById(fromId).classList.remove('active');
    document.getElementById(toId).classList.add('active');
}

function startCountdown(seconds) {
    const timerSpan = document.getElementById('resend-timer');
    const resendLink = document.getElementById('resend-link');
    const countdownEl = document.getElementById('countdown');

    if (!timerSpan || !resendLink) return;

    clearInterval(countdownInterval);
    let remaining = seconds;

    timerSpan.style.display = 'inline';
    resendLink.style.display = 'none';
    resendLink.classList.add('disabled');
    if (countdownEl) countdownEl.textContent = remaining;

    countdownInterval = setInterval(() => {
        remaining--;
        if (countdownEl) countdownEl.textContent = remaining;
        if (remaining <= 0) {
            clearInterval(countdownInterval);
            timerSpan.style.display = 'none';
            resendLink.style.display = 'inline';
            resendLink.classList.remove('disabled');
        }
    }, 1000);
}


// ══════════════════════════════════════════════════════════════
//  SIGNUP FLOW (signup.html)
// ══════════════════════════════════════════════════════════════

const signupForm = document.getElementById('signup-form');
if (signupForm) {
    let signupEmail = '';

    // Password strength indicator
    const pwInput = document.getElementById('password');
    const pwBar = document.getElementById('pw-strength');
    if (pwInput && pwBar) {
        pwInput.addEventListener('input', () => {
            const len = pwInput.value.length;
            const pct = Math.min(len / 12, 1) * 100;
            pwBar.style.width = pct + '%';
            pwBar.style.background =
                pct < 40 ? 'var(--danger)' : pct < 70 ? 'var(--warning)' : 'var(--success)';
        });
    }

    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('name').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        signupEmail = email;

        try {
            const data = await api.post('/auth/register', { name, email, password });
            showToast('Account created! Enter the OTP to verify.', 'success');
            document.getElementById('step-register').classList.remove('active');
            document.getElementById('step-otp').classList.add('active');

            // Show dev OTP banner if server returned the code (DEBUG mode)
            if (data.dev_otp) {
                showDevOtp(data.dev_otp);
            }
        } catch (err) {
            showToast(err.error || 'Registration failed', 'error');
        }
    });

    // Verify OTP
    const verifyBtn = document.getElementById('verify-btn');
    if (verifyBtn) {
        verifyBtn.addEventListener('click', async () => {
            const otp = document.getElementById('otp-input').value.trim();
            try {
                await api.post('/auth/verify-otp', { email: signupEmail, otp });
                showToast('Email verified!', 'success');
                document.getElementById('step-otp').classList.remove('active');
                document.getElementById('step-success').classList.add('active');
            } catch (err) {
                showToast(err.error || 'Invalid OTP', 'error');
            }
        });
    }

    // Resend OTP
    const resendBtn = document.getElementById('resend-otp');
    if (resendBtn) {
        resendBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                const data = await api.post('/auth/resend-otp', { identifier: signupEmail });
                showToast('OTP resent!', 'info');
                if (data && data.dev_otp) showDevOtp(data.dev_otp);
            } catch (err) {
                showToast(err.error || 'Failed to resend', 'error');
            }
        });
    }
}

// ── Dev OTP helpers ──────────────────────────────────────────
function showDevOtp(otp) {
    const banner = document.getElementById('dev-otp-banner');
    const codeEl = document.getElementById('dev-otp-code');
    if (!banner || !codeEl) return;
    codeEl.textContent = otp;
    banner.classList.add('visible');
    // Auto-fill the input
    const input = document.getElementById('otp-input');
    if (input) input.value = otp;
}

window.copyOtp = function(el) {
    const otp = el.textContent;
    const input = document.getElementById('otp-input');
    if (input) {
        input.value = otp;
        input.focus();
        showToast('OTP auto-filled!', 'success');
    }
};
