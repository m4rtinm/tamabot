.pragma library

var DAYS = ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"];

function ago(ms, now) {
    var s = Math.max(0, Math.round((now - ms) / 1000));
    if (s < 10) return "ahora";
    if (s < 60) return "hace " + s + " s";
    var m = Math.round(s / 60);
    if (m < 60) return "hace " + m + " min";
    var h = Math.floor(m / 60);
    if (h < 24) return "hace " + h + " h";
    return "hace " + Math.floor(h / 24) + " d";
}

function until(epochSec, now) {
    var s = Math.max(0, Math.round(epochSec - now / 1000));
    var m = Math.floor(s / 60), h = Math.floor(m / 60);
    if (h >= 24) {
        var d = new Date(epochSec * 1000);
        return DAYS[d.getDay()] + " " + pad(d.getHours()) + ":" + pad(d.getMinutes());
    }
    if (h > 0) return "en " + h + " h " + pad(m % 60) + " min";
    if (m > 0) return "en " + m + " min";
    return "en " + s + " s";
}

function pad(n) { return n < 10 ? "0" + n : "" + n; }

function levelColor(p) {
    if (p >= 90) return "#FF453A";
    if (p >= 70) return "#FF9F0A";
    return "#D97757";
}

function stateColor(s) {
    return { working: "#D97757", waiting: "#FF9F0A", done: "#30D158", idle: "#8E8E93" }[s] || "#8E8E93";
}

function stateLabel(s) {
    return { working: "Trabajando", waiting: "Te espera", done: "Terminado", idle: "En espera" }[s] || s;
}

var OUTCOMES = {
    allow: ["Permitido", "#30D158"],
    always: ["Permitido siempre", "#30D158"],
    deny: ["Rechazado", "#FF453A"],
    answered: ["Respondida", "#30D158"],
    terminal: ["Enviado a la terminal", "#8E8E93"],
    elsewhere: ["Respondido en la terminal", "#8E8E93"],
    timeout: ["Sin respuesta", "#FF9F0A"],
    dropped: ["La sesión siguió", "#8E8E93"],
    quit: ["App cerrada", "#8E8E93"]
};

function outcomeLabel(o) { return (OUTCOMES[o] || [o])[0]; }
function outcomeColor(o) { return (OUTCOMES[o] || [o, "#8E8E93"])[1]; }

function clock(ts, now) {
    var d = new Date(ts * 1000), n = new Date(now);
    var hm = pad(d.getHours()) + ":" + pad(d.getMinutes());
    if (d.toDateString() === n.toDateString()) return hm;
    var y = new Date(now - 86400000);
    if (d.toDateString() === y.toDateString()) return "ayer " + hm;
    return pad(d.getDate()) + "/" + pad(d.getMonth() + 1) + " " + hm;
}
