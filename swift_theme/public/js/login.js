// Swift Theme Enterprise Login - Dynamic Theme Engine

document.addEventListener('DOMContentLoaded', async function() {
    // Fetch active theme configuration
    await loadThemeConfig();
    
    // Setup form submission
    setupLoginForm();
});

async function loadThemeConfig() {
    try {
        const response = await fetch('/api/method/swift_theme.swift_theme.doctype.swift_theme_settings.swift_theme_settings.get_active_theme_config');
        
        if (response.ok) {
            const config = await response.json();
            
            if (config.message) {
                applyTheme(config.message);
            }
        }
    } catch (error) {
        console.log('Using default theme:', error);
        // Default theme will be applied via CSS variables
    }
}

function applyTheme(config) {
    const root = document.documentElement;
    
    // Apply colors based on mode
    if (config.color_mode === 'Custom Gradient') {
        root.style.setProperty('--primary', config.primary || '#3b82f6');
        root.style.setProperty('--secondary', config.secondary || '#8b5cf6');
        root.style.setProperty('--bg1', config.gradient_start || '#0f172a');
        root.style.setProperty('--bg2', config.gradient_end || '#1e293b');
    } else {
        // Preset theme
        root.style.setProperty('--primary', config.primary || '#3b82f6');
        root.style.setProperty('--secondary', config.secondary || '#8b5cf6');
        root.style.setProperty('--bg1', config.bg1 || '#0f172a');
        root.style.setProperty('--bg2', config.bg2 || '#1e293b');
    }
    
    // Auto-switch dark/light mode based on theme brightness
    if (config.is_dark_mode !== undefined) {
        if (config.is_dark_mode) {
            document.body.classList.add('dark-mode');
            document.body.classList.remove('light-mode');
        } else {
            document.body.classList.add('light-mode');
            document.body.classList.remove('dark-mode');
        }
    }
    
    // Update custom text if provided
    if (config.custom_login_text) {
        const customTextElement = document.getElementById('custom-message');
        if (customTextElement) {
            customTextElement.textContent = config.custom_login_text;
        }
    }
    
    console.log('Theme applied:', config);
}

function setupLoginForm() {
    const loginForm = document.getElementById('login-form');

    if (!loginForm) return;

    loginForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const remember = document.querySelector('input[name="remember"]').checked;

        await playSound('submit');

        const submitBtn = loginForm.querySelector('.login-btn');
        const originalText = submitBtn.innerHTML;

        submitBtn.innerHTML = "<span>Signing In...</span>";
        submitBtn.disabled = true;

        try {
            const body = new URLSearchParams();
            body.append("usr", username);
            body.append("pwd", password);

            const response = await fetch("/api/method/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: body.toString(),
                credentials: "same-origin"
            });

            const data = await response.json();

            if (data.exc) {
                throw new Error("Invalid username or password.");
            }

            if (remember) {
                localStorage.setItem("remember_username", username);
            } else {
                localStorage.removeItem("remember_username");
            }

            window.location.href = "/app";

        } catch (err) {
            console.error(err);

            alert(
                err.message ||
                "Login failed. Please check your username and password."
            );

            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    });

    const savedUser = localStorage.getItem("remember_username");

    if (savedUser) {
        document.getElementById("username").value = savedUser;

        const rememberBox = document.querySelector(
            'input[name="remember"]'
        );

        if (rememberBox) {
            rememberBox.checked = true;
        }
    }
}

async function playSound(eventName) {
    try {
        const response = await fetch('/api/method/swift_theme.swift_theme.doctype.swift_theme_settings.swift_theme_settings.play_sound', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ event_name: eventName })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.message && data.message.enabled && data.message.sound_file) {
                const audio = new Audio(data.message.sound_file);
                audio.volume = data.message.volume_level / 100;
                await audio.play();
            }
        }
    } catch (error) {
        console.log('Sound playback failed:', error);
    }
}

// Add keyboard shortcut for quick login (Ctrl+Enter)
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'Enter') {
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.dispatchEvent(new Event('submit'));
        }
    }
});
