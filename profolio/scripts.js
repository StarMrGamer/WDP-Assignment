/* ===========================
   MATTHIAS CHIAM — scripts.js
   =========================== */

document.addEventListener('DOMContentLoaded', () => {

    /* ── Navbar Scroll ── */
    const navbar = document.getElementById('navbar');
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('section[id]');

    window.addEventListener('scroll', () => {
        if (window.scrollY > 40) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        updateActiveNav();
    });

    function updateActiveNav() {
        let current = '';
        const scrollPos = window.scrollY + 150; // Offset for better detection
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            const sectionId = section.getAttribute('id');
            
            if (scrollPos >= sectionTop && scrollPos < sectionTop + sectionHeight) {
                current = sectionId;
            }
        });
        
        // Update nav links
        navLinks.forEach(link => {
            link.classList.remove('active');
            const href = link.getAttribute('href');
            if (href === '#' + current) {
                link.classList.add('active');
            }
        });
    }
    
    // Call once on load
    updateActiveNav();

    /* ── Mobile Menu ── */
    const hamburger = document.getElementById('hamburger');
    const mobileMenu = document.getElementById('mobileMenu');

    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('open');
        mobileMenu.classList.toggle('open');
    });

    document.querySelectorAll('.mob-link').forEach(link => {
        link.addEventListener('click', () => {
            hamburger.classList.remove('open');
            mobileMenu.classList.remove('open');
        });
    });

    /* ── Scroll Reveal ── */
    const fadeEls = document.querySelectorAll('.fade-up');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in-view');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });

    fadeEls.forEach(el => observer.observe(el));

    // Also observe section children that aren't explicitly .fade-up
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                revealObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    document.querySelectorAll('.exp-card, .edu-card, .cred-item, .badge').forEach((el, i) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = `opacity 0.5s ease ${i * 0.06}s, transform 0.5s ease ${i * 0.06}s`;
        revealObserver.observe(el);
    });

    /* ── CAROUSEL (click only, no auto) ── */
    const slides = document.querySelectorAll('.carousel-slide');
    const dotsContainer = document.getElementById('carouselDots');
    const prevBtn = document.getElementById('cPrev');
    const nextBtn = document.getElementById('cNext');
    
    if (slides.length > 0 && dotsContainer && prevBtn && nextBtn) {
        let current = 0;

        // Build dots
        slides.forEach((_, i) => {
            const d = document.createElement('div');
            d.className = 'dot' + (i === 0 ? ' active' : '');
            d.addEventListener('click', () => {
                goTo(i);
            });
            dotsContainer.appendChild(d);
        });

        function updateDots() {
            document.querySelectorAll('.dot').forEach((d, i) => {
                d.classList.toggle('active', i === current);
            });
        }

        function goTo(idx) {
            if (idx === current) return;
            slides[current].classList.remove('active');
            slides[current].classList.add('exit');
            const prevIdx = current;
            setTimeout(() => {
                slides[prevIdx].classList.remove('exit');
            }, 500);
            // Handle wrapping
            if (idx < 0) {
                current = slides.length - 1;
            } else if (idx >= slides.length) {
                current = 0;
            } else {
                current = idx;
            }
            slides[current].classList.add('active');
            updateDots();
        }

        prevBtn.addEventListener('click', (e) => {
            e.preventDefault();
            goTo(current - 1);
        });
        
        nextBtn.addEventListener('click', (e) => {
            e.preventDefault();
            goTo(current + 1);
        });

        // Touch swipe support
        const carouselWrapper = document.querySelector('.carousel-wrapper');
        let touchStartX = 0;
        if (carouselWrapper) {
            carouselWrapper.addEventListener('touchstart', e => {
                touchStartX = e.changedTouches[0].clientX;
            }, { passive: true });
            carouselWrapper.addEventListener('touchend', e => {
                const dx = e.changedTouches[0].clientX - touchStartX;
                if (Math.abs(dx) > 50) {
                    goTo(dx < 0 ? current + 1 : current - 1);
                }
            });
        }
    }

    /* ── Contact Form ── */
    const form = document.getElementById('contactForm');
    if (form) {
        form.addEventListener('submit', e => {
            e.preventDefault();
            const btn = form.querySelector('.form-submit');
            btn.textContent = 'Message Sent ✓';
            btn.style.background = 'linear-gradient(135deg, #22c55e, #16a34a)';
            btn.style.boxShadow = '0 10px 20px rgba(34,197,94,0.2)';
            setTimeout(() => {
                btn.textContent = 'Send Message →';
                btn.style.background = '';
                btn.style.boxShadow = '';
                form.reset();
            }, 3000);
        });
    }

    /* ── Hero Load Animation ── */
    // Make hero visible immediately
    document.querySelectorAll('#hero .fade-up').forEach((el, i) => {
        setTimeout(() => el.classList.add('in-view'), i * 100);
    });

});
