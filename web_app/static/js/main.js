document.addEventListener('DOMContentLoaded', () => {
    // Theme Switcher Logic
    const themeBtns = document.querySelectorAll('.theme-btn');
    const savedTheme = localStorage.getItem('epi-theme') || 'blue';
    
    function setTheme(tname) {
        document.documentElement.setAttribute('data-theme', tname);
        localStorage.setItem('epi-theme', tname);
        themeBtns.forEach(btn => {
            if(btn.dataset.theme === tname) btn.classList.add('active');
            else btn.classList.remove('active');
        });
    }

    setTheme(savedTheme);

    themeBtns.forEach(btn => {
        btn.addEventListener('click', () => setTheme(btn.dataset.theme));
    });

    // Active Nav Highlighting
    const activePath = window.location.pathname;
    document.querySelectorAll('.nav-item').forEach(link => {
        if(link.getAttribute('href') === activePath || (activePath === '/' && link.getAttribute('href') === '/')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
    
    // Global toast message utility
    window.showToast = function(msg, isError=false) {
        let t = document.createElement('div');
        t.style.position = 'fixed';
        t.style.bottom = '40px';
        t.style.left = '50%';
        t.style.transform = 'translate(-50%, 20px)';
        t.style.padding = '12px 24px';
        t.style.borderRadius = '8px';
        t.style.background = isError ? 'rgba(239, 68, 68, 0.9)' : 'rgba(16, 185, 129, 0.9)';
        t.style.color = '#fff';
        t.style.fontWeight = '600';
        t.style.zIndex = '9999';
        t.style.boxShadow = '0 10px 25px rgba(0,0,0,0.5)';
        t.style.opacity = '0';
        t.style.transition = 'all 0.3s ease';
        t.style.pointerEvents = 'none';
        t.innerText = msg;
        document.body.appendChild(t);
        
        setTimeout(() => {
            t.style.transform = 'translate(-50%, 0)';
            t.style.opacity = '1';
        }, 10);
        
        setTimeout(() => {
            t.style.opacity = '0';
            t.style.transform = 'translate(-50%, 20px)';
            setTimeout(() => t.remove(), 300);
        }, 3000);
    }
});
