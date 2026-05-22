(function() {
  if (window._customAlertInitialized) return;
  window._customAlertInitialized = true;

  const style = document.createElement('style');
  style.textContent = `
    .custom-alert-overlay {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(15, 23, 42, 0.4);
      backdrop-filter: blur(8px);
      z-index: 100000;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      visibility: hidden;
      transition: all 0.3s ease;
    }
    .custom-alert-overlay.show {
      opacity: 1;
      visibility: visible;
    }
    .custom-alert-box {
      background: #ffffff;
      width: min(90%, 380px);
      border-radius: 20px;
      box-shadow: 0 24px 48px rgba(0,0,0,0.15);
      padding: 32px 24px;
      text-align: center;
      transform: translateY(20px) scale(0.95);
      transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
      font-family: 'Manrope', 'Sora', sans-serif;
      border: 1px solid rgba(148, 163, 184, 0.2);
    }
    .custom-alert-overlay.show .custom-alert-box {
      transform: translateY(0) scale(1);
    }
    .custom-alert-icon {
      font-size: 56px;
      margin-bottom: 16px;
      display: inline-block;
      line-height: 1;
    }
    .custom-alert-message {
      font-size: 16px;
      color: #1e293b;
      margin-bottom: 28px;
      line-height: 1.5;
      font-weight: 600;
      white-space: pre-wrap;
    }
    .custom-alert-btn {
      background: linear-gradient(135deg, #0f766e 0%, #0d9488 100%);
      color: white;
      border: none;
      padding: 12px 36px;
      border-radius: 999px;
      font-size: 15px;
      font-weight: 800;
      cursor: pointer;
      transition: all 0.2s;
      box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);
    }
    .custom-alert-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(13, 148, 136, 0.4);
    }
    .custom-alert-btn:active {
      transform: translateY(0);
    }
  `;
  document.head.appendChild(style);

  // Override window.alert
  window.alert = function(message) {
    const overlay = document.createElement('div');
    overlay.className = 'custom-alert-overlay';
    
    const msgLower = String(message).toLowerCase();
    const isError = msgLower.includes('error') || 
                    msgLower.includes('fail') || 
                    msgLower.includes('invalid') || 
                    msgLower.includes('first') ||
                    msgLower.includes('must be');
    const isSuccess = msgLower.includes('success') || 
                      msgLower.includes('verified') || 
                      msgLower.includes('welcome') ||
                      msgLower.includes('thank');
    
    let icon = '💬'; // default info
    if (isError) icon = '⚠️';
    if (isSuccess) icon = '🎉';

    overlay.innerHTML = \`
      <div class="custom-alert-box">
        <div class="custom-alert-icon">\${icon}</div>
        <div class="custom-alert-message">\${message}</div>
        <button class="custom-alert-btn">Got it</button>
      </div>
    \`;

    document.body.appendChild(overlay);

    // trigger animation
    requestAnimationFrame(() => {
      overlay.classList.add('show');
    });

    const btn = overlay.querySelector('.custom-alert-btn');
    btn.focus();

    const closeAlert = () => {
      overlay.classList.remove('show');
      setTimeout(() => overlay.remove(), 300);
    };

    btn.addEventListener('click', closeAlert);
    
    // allow enter/escape key to close
    overlay.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === 'Escape') {
        e.preventDefault();
        closeAlert();
      }
    });
  };
})();
