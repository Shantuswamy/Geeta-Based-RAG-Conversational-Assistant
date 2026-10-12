/**
 * ParticlesField
 * Spawns and manages atmospheric celestial golden sanctuary sparks and particles.
 */
export class ParticlesField {
  constructor(containerId = 'particles', count = 30) {
    this.container = document.getElementById(containerId);
    this.count = count;
  }

  init() {
    if (!this.container) return;
    this.container.innerHTML = '';

    for (let i = 0; i < this.count; i++) {
      const particle = document.createElement('div');
      particle.classList.add('particle', 'animate-particle');

      // Randomize size, position, and animation delay
      const size = Math.random() * 4 + 2; // 2px to 6px
      const left = Math.random() * 100; // 0% to 100%
      const top = Math.random() * 80 + 40; // Start below middle
      const delay = Math.random() * 10; // 0s to 10s delay
      const duration = Math.random() * 6 + 7; // 7s to 13s duration

      particle.style.width = `${size}px`;
      particle.style.height = `${size}px`;
      particle.style.left = `${left}%`;
      particle.style.top = `${top}%`;
      particle.style.animationDelay = `${delay}s`;
      particle.style.animationDuration = `${duration}s`;

      this.container.appendChild(particle);
    }
  }
}
