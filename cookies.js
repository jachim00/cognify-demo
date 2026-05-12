/**
 * Cognify — Cookie Consent (RODO/GDPR + Google Consent Mode v2)
 *
 * Zero zależności. Wstrzykuje DOM + style. Wykrywa język z <html lang="">.
 * Stan zapisany w localStorage pod kluczem `cognify_consent_v1`.
 * Po wyborze emituje:
 *   - window.dispatchEvent(new CustomEvent('cognify:consent', { detail }))
 *   - gtag('consent', 'update', {...}) — dla GA4/GTM/Ads (Consent Mode v2)
 *
 * Programmatic API (do footer/banner trigger):
 *   window.cognifyOpenCookieSettings()  — otwiera panel ustawień
 *   window.cognifyResetConsent()        — wycofuje zgodę (testing)
 */
(function () {
  'use strict';

  const STORAGE_KEY = 'cognify_consent_v1';
  const VERSION = 1;
  const EXPIRES_DAYS = 365;

  // ──────────────────────────────────────────────────────────
  // Google Consent Mode v2 — domyślny stan "denied" przed wyborem
  // (GA4/GTM podchwyci automatycznie nawet jeśli załadowane później)
  // ──────────────────────────────────────────────────────────
  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  window.gtag('consent', 'default', {
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    analytics_storage: 'denied',
    functionality_storage: 'denied',
    personalization_storage: 'denied',
    security_storage: 'granted',
    wait_for_update: 500
  });

  // ──────────────────────────────────────────────────────────
  // i18n
  // ──────────────────────────────────────────────────────────
  const I18N = {
    pl: {
      title: 'Używamy plików cookies',
      body: 'Aby zapewnić najlepsze działanie strony i analizować ruch, używamy plików cookies. Niektóre są niezbędne, inne pomagają nam ulepszać produkt.',
      acceptAll: 'Akceptuj wszystkie',
      rejectAll: 'Tylko niezbędne',
      customize: 'Dostosuj',
      save: 'Zapisz wybór',
      close: 'Zamknij',
      settings: 'Ustawienia cookies',
      privacy: 'Polityka prywatności',
      privacyHref: '/polityka-prywatnosci',
      modalTitle: 'Twoje preferencje cookies',
      modalDesc: 'Wybierz które kategorie cookies chcesz dopuścić. Twoja zgoda jest zapisywana lokalnie i ważna 12 miesięcy.',
      cats: {
        necessary: { name: 'Niezbędne', desc: 'Wymagane do działania strony (np. zapamiętanie Twojej zgody). Nie można wyłączyć.' },
        analytics: { name: 'Analityka', desc: 'Pomaga nam zrozumieć jak korzystasz ze strony (Google Analytics, Microsoft Clarity).' },
        marketing: { name: 'Marketing', desc: 'Używane do prezentowania reklam dopasowanych do Twoich zainteresowań.' },
        preferences: { name: 'Preferencje', desc: 'Zapamiętują Twoje wybory (np. język, ustawienia interfejsu).' }
      }
    },
    en: {
      title: 'We use cookies',
      body: 'To ensure the best experience and analyze traffic, we use cookies. Some are necessary, others help us improve. You can customize your preferences.',
      acceptAll: 'Accept all',
      rejectAll: 'Necessary only',
      customize: 'Customize',
      save: 'Save choices',
      close: 'Close',
      settings: 'Cookie settings',
      privacy: 'Privacy policy',
      privacyHref: '/en/privacy',
      modalTitle: 'Your cookie preferences',
      modalDesc: 'Choose which categories of cookies you accept. Your choice is stored locally for 12 months.',
      cats: {
        necessary: { name: 'Necessary', desc: 'Required for the site to function (e.g. remembering your consent). Cannot be disabled.' },
        analytics: { name: 'Analytics', desc: 'Helps us understand how you use the site (Google Analytics, Microsoft Clarity).' },
        marketing: { name: 'Marketing', desc: 'Used to show ads tailored to your interests.' },
        preferences: { name: 'Preferences', desc: 'Remember your choices (e.g. language, UI settings).' }
      }
    },
    de: {
      title: 'Wir verwenden Cookies',
      body: 'Für die beste Erfahrung und Traffic-Analyse verwenden wir Cookies. Einige sind notwendig, andere helfen uns zu verbessern. Sie können Ihre Präferenzen anpassen.',
      acceptAll: 'Alle akzeptieren',
      rejectAll: 'Nur notwendige',
      customize: 'Anpassen',
      save: 'Auswahl speichern',
      close: 'Schließen',
      settings: 'Cookie-Einstellungen',
      privacy: 'Datenschutzerklärung',
      privacyHref: '/de/privacy',
      modalTitle: 'Ihre Cookie-Präferenzen',
      modalDesc: 'Wählen Sie, welche Cookie-Kategorien Sie akzeptieren. Ihre Wahl wird lokal für 12 Monate gespeichert.',
      cats: {
        necessary: { name: 'Notwendig', desc: 'Für die Funktion der Website erforderlich (z.B. Speicherung Ihrer Zustimmung). Nicht deaktivierbar.' },
        analytics: { name: 'Analytik', desc: 'Hilft uns zu verstehen, wie Sie die Seite nutzen (Google Analytics, Microsoft Clarity).' },
        marketing: { name: 'Marketing', desc: 'Zeigt Werbung, die auf Ihre Interessen zugeschnitten ist.' },
        preferences: { name: 'Präferenzen', desc: 'Merkt sich Ihre Entscheidungen (z.B. Sprache, UI-Einstellungen).' }
      }
    },
    fr: {
      title: 'Nous utilisons des cookies',
      body: "Pour offrir la meilleure expérience et analyser le trafic, nous utilisons des cookies. Certains sont nécessaires, d'autres nous aident à améliorer. Vous pouvez personnaliser vos préférences.",
      acceptAll: 'Tout accepter',
      rejectAll: 'Nécessaires uniquement',
      customize: 'Personnaliser',
      save: 'Enregistrer',
      close: 'Fermer',
      settings: 'Paramètres cookies',
      privacy: 'Politique de confidentialité',
      privacyHref: '/fr/privacy',
      modalTitle: 'Vos préférences cookies',
      modalDesc: 'Choisissez les catégories de cookies que vous acceptez. Votre choix est conservé localement pendant 12 mois.',
      cats: {
        necessary: { name: 'Nécessaires', desc: 'Requis pour le fonctionnement du site (ex. mémorisation de votre consentement). Non désactivables.' },
        analytics: { name: 'Analytique', desc: 'Nous aide à comprendre votre utilisation (Google Analytics, Microsoft Clarity).' },
        marketing: { name: 'Marketing', desc: 'Utilisés pour afficher des publicités adaptées à vos intérêts.' },
        preferences: { name: 'Préférences', desc: 'Mémorisent vos choix (ex. langue, paramètres UI).' }
      }
    },
    no: {
      title: 'Vi bruker informasjonskapsler',
      body: 'For å sikre best mulig opplevelse og analysere trafikk bruker vi informasjonskapsler. Noen er nødvendige, andre hjelper oss å forbedre. Du kan tilpasse dine preferanser.',
      acceptAll: 'Godta alle',
      rejectAll: 'Kun nødvendige',
      customize: 'Tilpass',
      save: 'Lagre valg',
      close: 'Lukk',
      settings: 'Innstillinger for cookies',
      privacy: 'Personvernerklæring',
      privacyHref: '/no/privacy',
      modalTitle: 'Dine cookie-preferanser',
      modalDesc: 'Velg hvilke kategorier av informasjonskapsler du godtar. Valget lagres lokalt i 12 måneder.',
      cats: {
        necessary: { name: 'Nødvendige', desc: 'Kreves for at siden skal fungere (f.eks. å huske samtykket ditt). Kan ikke slås av.' },
        analytics: { name: 'Analyse', desc: 'Hjelper oss å forstå hvordan du bruker siden (Google Analytics, Microsoft Clarity).' },
        marketing: { name: 'Markedsføring', desc: 'Brukes til å vise reklame tilpasset dine interesser.' },
        preferences: { name: 'Preferanser', desc: 'Husker valgene dine (f.eks. språk, UI-innstillinger).' }
      }
    },
    hu: {
      title: 'Sütiket használunk',
      body: 'A legjobb élmény és forgalom elemzéséhez sütiket használunk. Néhány elengedhetetlen, mások segítenek nekünk a fejlesztésben. Testreszabhatja preferenciáit.',
      acceptAll: 'Összes elfogadása',
      rejectAll: 'Csak szükségesek',
      customize: 'Testreszabás',
      save: 'Mentés',
      close: 'Bezárás',
      settings: 'Süti beállítások',
      privacy: 'Adatvédelmi tájékoztató',
      privacyHref: '/hu/privacy',
      modalTitle: 'Süti preferenciái',
      modalDesc: 'Válassza ki, mely süti-kategóriákat fogadja el. Választása helyileg 12 hónapig tárolódik.',
      cats: {
        necessary: { name: 'Szükségesek', desc: 'A webhely működéséhez szükséges (pl. hozzájárulás megjegyzése). Nem kapcsolható ki.' },
        analytics: { name: 'Analitika', desc: 'Segít megérteni, hogyan használja az oldalt (Google Analytics, Microsoft Clarity).' },
        marketing: { name: 'Marketing', desc: 'Az érdeklődéséhez igazított hirdetések megjelenítésére szolgál.' },
        preferences: { name: 'Preferenciák', desc: 'Megjegyzi a választásait (pl. nyelv, UI beállítások).' }
      }
    }
  };

  function detectLang() {
    const html = document.documentElement.lang || 'pl';
    const code = html.toLowerCase().slice(0, 2);
    return I18N[code] ? code : 'pl';
  }

  // ──────────────────────────────────────────────────────────
  // Storage
  // ──────────────────────────────────────────────────────────
  function loadConsent() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      const c = JSON.parse(raw);
      if (c.version !== VERSION) return null;
      if (c.expires && Date.now() > c.expires) return null;
      return c;
    } catch (e) { return null; }
  }

  function saveConsent(choices) {
    const consent = {
      version: VERSION,
      timestamp: Date.now(),
      expires: Date.now() + EXPIRES_DAYS * 24 * 60 * 60 * 1000,
      necessary: true,
      analytics: !!choices.analytics,
      marketing: !!choices.marketing,
      preferences: !!choices.preferences
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(consent));
    applyConsent(consent);
    return consent;
  }

  function applyConsent(consent) {
    // Google Consent Mode v2 update
    window.gtag('consent', 'update', {
      analytics_storage: consent.analytics ? 'granted' : 'denied',
      ad_storage: consent.marketing ? 'granted' : 'denied',
      ad_user_data: consent.marketing ? 'granted' : 'denied',
      ad_personalization: consent.marketing ? 'granted' : 'denied',
      personalization_storage: consent.preferences ? 'granted' : 'denied',
      functionality_storage: consent.preferences ? 'granted' : 'denied'
    });
    // Custom event dla integracji własnych
    window.dispatchEvent(new CustomEvent('cognify:consent', { detail: consent }));
  }

  // ──────────────────────────────────────────────────────────
  // Style injection
  // ──────────────────────────────────────────────────────────
  const STYLE = `
.cog-cc-overlay,
.cog-cc-banner,
.cog-cc-modal,
.cog-cc-fab {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  box-sizing: border-box;
}
.cog-cc-overlay {
  position: fixed; inset: 0; background: rgba(3, 7, 18, 0.75);
  backdrop-filter: blur(8px); z-index: 9998; display: none;
  animation: cog-cc-fade 0.2s ease-out;
}
.cog-cc-overlay[data-open] { display: block; }
.cog-cc-banner {
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 9999;
  padding: 20px 24px; background: rgba(11, 15, 26, 0.96);
  backdrop-filter: blur(16px) saturate(140%);
  border-top: 1px solid rgba(34, 211, 238, 0.18);
  box-shadow: 0 -20px 60px rgba(0, 0, 0, 0.4);
  color: #e2e8f0; transform: translateY(100%);
  transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}
.cog-cc-banner[data-open] { transform: translateY(0); }
.cog-cc-banner-inner {
  max-width: 1100px; margin: 0 auto;
  display: grid; grid-template-columns: 1fr auto; gap: 20px; align-items: center;
}
@media (max-width: 768px) {
  .cog-cc-banner-inner { grid-template-columns: 1fr; gap: 14px; }
}
.cog-cc-banner-text { font-size: 14px; line-height: 1.55; color: #cbd5e1; }
.cog-cc-banner-text strong { color: #fff; font-weight: 600; }
.cog-cc-banner-text a { color: #22d3ee; text-decoration: underline; text-underline-offset: 2px; }
.cog-cc-banner-buttons { display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
@media (max-width: 768px) {
  .cog-cc-banner-buttons { justify-content: stretch; }
  .cog-cc-banner-buttons .cog-cc-btn { flex: 1; min-width: 0; }
}
.cog-cc-btn {
  padding: 10px 18px; border-radius: 9px; font-size: 13px; font-weight: 600;
  cursor: pointer; border: 1px solid transparent; white-space: nowrap;
  transition: transform 0.15s, background 0.2s, border-color 0.2s;
  font-family: inherit;
}
.cog-cc-btn:hover { transform: translateY(-1px); }
.cog-cc-btn-primary {
  background: linear-gradient(135deg, #22d3ee 0%, #a78bfa 100%);
  color: #030712;
}
.cog-cc-btn-ghost {
  background: rgba(255,255,255,0.06); color: #e2e8f0;
  border-color: rgba(255,255,255,0.12);
}
.cog-cc-btn-ghost:hover { background: rgba(255,255,255,0.1); border-color: rgba(34, 211, 238, 0.5); }
.cog-cc-btn-text {
  background: transparent; color: #94a3b8; padding: 10px 14px;
}
.cog-cc-btn-text:hover { color: #22d3ee; }

.cog-cc-modal {
  position: fixed; left: 50%; top: 50%; transform: translate(-50%, -50%);
  width: min(560px, calc(100% - 32px)); max-height: calc(100% - 32px);
  background: #0b0f1a; border: 1px solid rgba(34, 211, 238, 0.2);
  border-radius: 16px; padding: 28px; z-index: 10000;
  color: #e2e8f0; display: none; overflow-y: auto;
  box-shadow: 0 30px 80px rgba(0,0,0,0.6);
  animation: cog-cc-pop 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.cog-cc-modal[data-open] { display: block; }
.cog-cc-modal-title {
  font-size: 22px; font-weight: 800; color: #fff; margin: 0 0 8px;
  background: linear-gradient(135deg, #22d3ee, #a78bfa);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.cog-cc-modal-desc { font-size: 13px; line-height: 1.6; color: #94a3b8; margin: 0 0 20px; }
.cog-cc-cat {
  border: 1px solid rgba(255,255,255,0.08); border-radius: 10px;
  padding: 14px 16px; margin-bottom: 10px;
}
.cog-cc-cat-head {
  display: flex; justify-content: space-between; align-items: center;
  gap: 12px; margin-bottom: 6px;
}
.cog-cc-cat-name { font-weight: 600; color: #fff; font-size: 14px; }
.cog-cc-cat-desc { font-size: 12px; color: #94a3b8; line-height: 1.5; margin: 0; }

/* Toggle switch */
.cog-cc-switch {
  position: relative; width: 40px; height: 22px; flex-shrink: 0;
}
.cog-cc-switch input { opacity: 0; width: 0; height: 0; }
.cog-cc-switch-slider {
  position: absolute; inset: 0; cursor: pointer; background: rgba(255,255,255,0.12);
  border-radius: 22px; transition: 0.2s;
}
.cog-cc-switch-slider::before {
  content: ''; position: absolute; height: 16px; width: 16px; left: 3px; top: 3px;
  background: #cbd5e1; border-radius: 50%; transition: 0.2s;
}
.cog-cc-switch input:checked + .cog-cc-switch-slider { background: linear-gradient(135deg, #22d3ee, #a78bfa); }
.cog-cc-switch input:checked + .cog-cc-switch-slider::before { transform: translateX(18px); background: #030712; }
.cog-cc-switch input:disabled + .cog-cc-switch-slider { opacity: 0.5; cursor: not-allowed; }

.cog-cc-modal-footer {
  display: flex; gap: 8px; margin-top: 18px; padding-top: 16px;
  border-top: 1px solid rgba(255,255,255,0.06);
  flex-wrap: wrap; justify-content: flex-end;
}
.cog-cc-modal-footer .cog-cc-btn { flex: 1; min-width: 120px; }

/* Floating settings button */
.cog-cc-fab {
  position: fixed; right: 16px; bottom: 16px; z-index: 9997;
  width: 44px; height: 44px; border-radius: 50%; border: 1px solid rgba(34, 211, 238, 0.3);
  background: rgba(11, 15, 26, 0.85); backdrop-filter: blur(10px);
  color: #22d3ee; cursor: pointer; display: none;
  align-items: center; justify-content: center; font-size: 18px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.35);
  transition: transform 0.2s, background 0.2s;
}
.cog-cc-fab:hover { transform: scale(1.08); background: rgba(34, 211, 238, 0.1); }
.cog-cc-fab[data-visible] { display: flex; }
.cog-cc-fab[aria-label]::after {
  content: attr(aria-label); position: absolute; right: 54px; top: 50%;
  transform: translateY(-50%) translateX(8px); opacity: 0; pointer-events: none;
  background: rgba(11,15,26,0.95); color: #e2e8f0; padding: 5px 10px;
  border-radius: 6px; font-size: 12px; white-space: nowrap;
  transition: opacity 0.15s, transform 0.15s;
  border: 1px solid rgba(255,255,255,0.08);
}
.cog-cc-fab:hover::after { opacity: 1; transform: translateY(-50%) translateX(0); }

@keyframes cog-cc-fade { from { opacity: 0; } to { opacity: 1; } }
@keyframes cog-cc-pop { from { opacity: 0; transform: translate(-50%, -48%) scale(0.96); } to { opacity: 1; transform: translate(-50%, -50%) scale(1); } }
`;

  function injectStyle() {
    if (document.getElementById('cog-cc-style')) return;
    const s = document.createElement('style');
    s.id = 'cog-cc-style';
    s.textContent = STYLE;
    document.head.appendChild(s);
  }

  // ──────────────────────────────────────────────────────────
  // DOM
  // ──────────────────────────────────────────────────────────
  function buildBanner(t) {
    const div = document.createElement('div');
    div.className = 'cog-cc-banner';
    div.setAttribute('role', 'dialog');
    div.setAttribute('aria-live', 'polite');
    div.setAttribute('aria-label', t.title);
    div.innerHTML = `
      <div class="cog-cc-banner-inner">
        <div class="cog-cc-banner-text">
          <strong>${t.title}.</strong> ${t.body}
          <a href="${t.privacyHref}">${t.privacy}</a>
        </div>
        <div class="cog-cc-banner-buttons">
          <button class="cog-cc-btn cog-cc-btn-text" data-act="customize">${t.customize}</button>
          <button class="cog-cc-btn cog-cc-btn-ghost" data-act="reject">${t.rejectAll}</button>
          <button class="cog-cc-btn cog-cc-btn-primary" data-act="accept">${t.acceptAll}</button>
        </div>
      </div>
    `;
    return div;
  }

  function buildModal(t, current) {
    const div = document.createElement('div');
    div.className = 'cog-cc-modal';
    div.setAttribute('role', 'dialog');
    div.setAttribute('aria-modal', 'true');
    div.setAttribute('aria-label', t.modalTitle);
    const sw = (cat, checked, disabled) => `
      <div class="cog-cc-cat">
        <div class="cog-cc-cat-head">
          <span class="cog-cc-cat-name">${t.cats[cat].name}</span>
          <label class="cog-cc-switch">
            <input type="checkbox" data-cat="${cat}" ${checked ? 'checked' : ''} ${disabled ? 'disabled' : ''}>
            <span class="cog-cc-switch-slider"></span>
          </label>
        </div>
        <p class="cog-cc-cat-desc">${t.cats[cat].desc}</p>
      </div>
    `;
    div.innerHTML = `
      <h2 class="cog-cc-modal-title">${t.modalTitle}</h2>
      <p class="cog-cc-modal-desc">${t.modalDesc} · <a href="${t.privacyHref}" style="color:#22d3ee">${t.privacy}</a></p>
      ${sw('necessary', true, true)}
      ${sw('analytics', current && current.analytics)}
      ${sw('marketing', current && current.marketing)}
      ${sw('preferences', current && current.preferences)}
      <div class="cog-cc-modal-footer">
        <button class="cog-cc-btn cog-cc-btn-ghost" data-act="reject">${t.rejectAll}</button>
        <button class="cog-cc-btn cog-cc-btn-primary" data-act="save">${t.save}</button>
      </div>
    `;
    return div;
  }

  function buildOverlay() {
    const o = document.createElement('div');
    o.className = 'cog-cc-overlay';
    return o;
  }

  function buildFab(t) {
    const b = document.createElement('button');
    b.className = 'cog-cc-fab';
    b.setAttribute('aria-label', t.settings);
    b.innerHTML = '🍪';
    return b;
  }

  // ──────────────────────────────────────────────────────────
  // Main
  // ──────────────────────────────────────────────────────────
  function init() {
    const lang = detectLang();
    const t = I18N[lang];
    injectStyle();

    let current = loadConsent();
    const banner = buildBanner(t);
    const overlay = buildOverlay();
    const fab = buildFab(t);

    document.body.appendChild(overlay);
    document.body.appendChild(banner);
    document.body.appendChild(fab);

    let modal = null;
    function openModal() {
      if (modal) modal.remove();
      modal = buildModal(t, current);
      document.body.appendChild(modal);
      overlay.setAttribute('data-open', '');
      requestAnimationFrame(() => modal.setAttribute('data-open', ''));
      modal.addEventListener('click', (e) => {
        const act = e.target.closest('[data-act]')?.dataset.act;
        if (act === 'save') {
          const get = (cat) => modal.querySelector(`input[data-cat="${cat}"]`).checked;
          current = saveConsent({ analytics: get('analytics'), marketing: get('marketing'), preferences: get('preferences') });
          closeAll();
        } else if (act === 'reject') {
          current = saveConsent({ analytics: false, marketing: false, preferences: false });
          closeAll();
        }
      });
    }

    function closeAll() {
      banner.removeAttribute('data-open');
      overlay.removeAttribute('data-open');
      if (modal) { modal.removeAttribute('data-open'); setTimeout(() => modal && modal.remove(), 200); modal = null; }
      fab.setAttribute('data-visible', '');
    }

    banner.addEventListener('click', (e) => {
      const act = e.target.closest('[data-act]')?.dataset.act;
      if (act === 'accept') {
        current = saveConsent({ analytics: true, marketing: true, preferences: true });
        closeAll();
      } else if (act === 'reject') {
        current = saveConsent({ analytics: false, marketing: false, preferences: false });
        closeAll();
      } else if (act === 'customize') {
        openModal();
      }
    });

    overlay.addEventListener('click', () => {
      // Klik w overlay nie zapisuje wyboru — wymagamy świadomej decyzji
      // (zgodnie z RODO — brak zgody przez ignorowanie nie liczy się jako zgoda)
    });

    fab.addEventListener('click', openModal);

    // Stan początkowy
    if (current) {
      applyConsent(current);
      fab.setAttribute('data-visible', '');
    } else {
      requestAnimationFrame(() => banner.setAttribute('data-open', ''));
    }

    // API
    window.cognifyOpenCookieSettings = openModal;
    window.cognifyResetConsent = () => {
      localStorage.removeItem(STORAGE_KEY);
      location.reload();
    };
    window.cognifyGetConsent = () => loadConsent();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
