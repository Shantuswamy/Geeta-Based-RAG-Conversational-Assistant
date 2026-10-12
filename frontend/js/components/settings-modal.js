/**
 * SettingsModal
 * Manages the slide-out settings drawer, theme toggles, and persistent preferences.
 */
export class SettingsModal {
  constructor(onSettingsChange) {
    this.onSettingsChange = onSettingsChange || (() => {});
    this.overlay = document.getElementById('settings-overlay');
    this.openBtn = document.getElementById('open-settings-btn');
    this.closeBtn = document.getElementById('close-settings-btn');

    this.voiceSelect = document.getElementById('setting-voice');
    this.langSelect = document.getElementById('setting-lang');
    this.wsInput = document.getElementById('setting-ws-url');
    this.themeDuskBtn = document.getElementById('theme-dusk-btn');
    this.themeDawnBtn = document.getElementById('theme-dawn-btn');

    this.settings = this.loadSettings();
  }

  init() {
    this.applySettings(this.settings);
    this.bindEvents();
  }

  loadSettings() {
    const defaults = {
      voice: 'af_heart',
      language: 'en',
      theme: 'dusk',
      wsUrl: `ws://${window.location.hostname || 'localhost'}:8000/ws/voice-chat`
    };

    try {
      const saved = localStorage.getItem('gitarag_settings');
      if (saved) {
        return { ...defaults, ...JSON.parse(saved) };
      }
    } catch (_) {}

    return defaults;
  }

  saveSettings() {
    try {
      localStorage.setItem('gitarag_settings', JSON.stringify(this.settings));
    } catch (_) {}
    this.onSettingsChange(this.settings);
  }

  applySettings(settings) {
    if (this.voiceSelect) this.voiceSelect.value = settings.voice;
    if (this.langSelect) this.langSelect.value = settings.language;
    if (this.wsInput) this.wsInput.value = settings.wsUrl;

    this.setTheme(settings.theme, false);
  }

  setTheme(theme, save = true) {
    this.settings.theme = theme;
    if (theme === 'dawn') {
      document.documentElement.setAttribute('data-theme', 'dawn');
      if (this.themeDawnBtn) this.themeDawnBtn.classList.add('active');
      if (this.themeDuskBtn) this.themeDuskBtn.classList.remove('active');
    } else {
      document.documentElement.removeAttribute('data-theme');
      if (this.themeDuskBtn) this.themeDuskBtn.classList.add('active');
      if (this.themeDawnBtn) this.themeDawnBtn.classList.remove('active');
    }

    if (save) this.saveSettings();
  }

  bindEvents() {
    if (this.openBtn) {
      this.openBtn.addEventListener('click', () => this.open());
    }

    if (this.closeBtn) {
      this.closeBtn.addEventListener('click', () => this.close());
    }

    if (this.overlay) {
      this.overlay.addEventListener('click', (e) => {
        if (e.target === this.overlay) this.close();
      });
    }

    if (this.voiceSelect) {
      this.voiceSelect.addEventListener('change', (e) => {
        this.settings.voice = e.target.value;
        this.saveSettings();
      });
    }

    if (this.langSelect) {
      this.langSelect.addEventListener('change', (e) => {
        this.settings.language = e.target.value;
        this.saveSettings();
      });
    }

    if (this.wsInput) {
      this.wsInput.addEventListener('change', (e) => {
        this.settings.wsUrl = e.target.value.trim();
        this.saveSettings();
      });
    }

    if (this.themeDuskBtn) {
      this.themeDuskBtn.addEventListener('click', () => this.setTheme('dusk'));
    }

    if (this.themeDawnBtn) {
      this.themeDawnBtn.addEventListener('click', () => this.setTheme('dawn'));
    }
  }

  open() {
    if (this.overlay) this.overlay.classList.add('open');
  }

  close() {
    if (this.overlay) this.overlay.classList.remove('open');
  }
}
