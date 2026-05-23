// SaleSense — main.js

// Auto dismiss flash messages after 4 seconds
document.addEventListener("DOMContentLoaded", () => {
  const flashes = document.querySelectorAll(".flash");
  flashes.forEach(f => {
    setTimeout(() => {
      f.style.transition = "opacity 0.5s";
      f.style.opacity = "0";
      setTimeout(() => f.remove(), 500);
    }, 4000);
  });
});