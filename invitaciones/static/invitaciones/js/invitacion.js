const pageData = document.body.dataset;
const intro = document.getElementById("intro");
const bgMusic = document.getElementById("bgMusic");
const musicToggle = document.getElementById("musicToggle");
const fechaEvento = new Date(pageData.eventDate).getTime();
const maxExtras = Number(pageData.maxExtras || 0);

window.abrirInvitacion = function abrirInvitacion() {
    if (intro) {
        intro.classList.add("opening");
        setTimeout(() => intro.classList.add("hidden"), 620);
    }
    reproducirMusica();
};

async function reproducirMusica() {
    if (!bgMusic || !musicToggle) return;

    try {
        bgMusic.volume = 0.55;
        await bgMusic.play();
        musicToggle.textContent = "♫";
    } catch (error) {
        musicToggle.textContent = "♪";
    }
}

function actualizarCountdown() {
    if (!fechaEvento) return;

    const ahora = new Date().getTime();
    const diferencia = Math.max(fechaEvento - ahora, 0);
    const dias = Math.floor(diferencia / (1000 * 60 * 60 * 24));
    const horas = Math.floor((diferencia % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutos = Math.floor((diferencia % (1000 * 60 * 60)) / (1000 * 60));
    const segundos = Math.floor((diferencia % (1000 * 60)) / 1000);

    setText("dias", dias);
    setText("horas", horas);
    setText("minutos", minutos);
    setText("segundos", segundos);
}

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
}

function limitarAcompanantes() {
    const adultos = document.getElementById("acompanantes_adultos");
    const ninos = document.getElementById("acompanantes_ninos");
    const noAsistira = document.getElementById("no_grupo");
    if (!adultos || !ninos) return;

    adultos.disabled = Boolean(noAsistira && noAsistira.checked);
    ninos.disabled = Boolean(noAsistira && noAsistira.checked);

    const total = Number(adultos.value || 0) + Number(ninos.value || 0);
    if (total > maxExtras) {
        ninos.value = Math.max(maxExtras - Number(adultos.value || 0), 0);
    }
}

if (musicToggle) {
    musicToggle.addEventListener("click", async () => {
        if (!bgMusic) return;

        if (bgMusic.paused) {
            await reproducirMusica();
        } else {
            bgMusic.pause();
            musicToggle.textContent = "♪";
        }
    });
}

document
    .querySelectorAll('input[name="asistira"], #acompanantes_adultos, #acompanantes_ninos')
    .forEach((input) => {
        input.addEventListener("change", limitarAcompanantes);
        input.addEventListener("input", limitarAcompanantes);
    });

actualizarCountdown();
limitarAcompanantes();
setInterval(actualizarCountdown, 1000);

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
if (!reduceMotion && "IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("is-visible");
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.16 });

    document.querySelectorAll(".section .panel").forEach((panel) => {
        panel.classList.add("reveal-panel");
        observer.observe(panel);
    });
} else {
    document.querySelectorAll(".section .panel").forEach((panel) => panel.classList.add("is-visible"));
}
