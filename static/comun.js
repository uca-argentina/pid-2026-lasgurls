(function () {
  var linkActivoOriginal = document.querySelector(".header-link-activo");

  function cerrarDesplegables(excepto) {
    document.querySelectorAll(".desplegable[open]").forEach(function (desplegable) {
      if (desplegable !== excepto) desplegable.open = false;
    });
  }

  function esClicNormal(evento) {
    return evento.button === 0 && !evento.ctrlKey && !evento.metaKey && !evento.shiftKey && !evento.altKey;
  }

  function moverSubrayado(link) {
    var subrayado = document.querySelector(".header-subrayado");
    var activo = document.querySelector(".header-link-activo");
    if (!subrayado || !activo || activo === link) return;
    var desde = activo.getBoundingClientRect();
    var hasta = link.getBoundingClientRect();
    subrayado.style.width = hasta.width + "px";
    subrayado.style.transform = "translateX(" + (hasta.left - desde.left) + "px)";
    activo.classList.remove("header-link-activo");
    link.classList.add("header-link-activo");
  }

  document.addEventListener("click", function (evento) {
    cerrarDesplegables(evento.target.closest(".desplegable"));

    var abrirDialogo = evento.target.closest("[data-abrir-dialogo]");
    if (abrirDialogo) document.getElementById(abrirDialogo.dataset.abrirDialogo).showModal();

    var link = evento.target.closest("a[href]");
    if (!link || !esClicNormal(evento) || link.target === "_blank" || link.closest("[data-recargable]")) return;
    if (link.origin !== window.location.origin || link.href === window.location.href) return;
    if (link.classList.contains("header-link")) moverSubrayado(link);
    document.documentElement.classList.add("navegando");
  });

  document.addEventListener("keydown", function (evento) {
    if (evento.key === "Escape") cerrarDesplegables(null);
  });

  document.addEventListener("submit", function (evento) {
    var dialogo = evento.target.closest("dialog");
    if (dialogo) dialogo.close();
    if (evento.target.method === "dialog") return;
    var volver = evento.target.querySelector('input[name="volver"]');
    if (volver) volver.value = window.location.pathname + window.location.search;
    if (!evento.target.closest("[data-recargable]")) document.documentElement.classList.add("navegando");
  });

  function actualizarNotificaciones() {
    var contenedor = document.querySelector("[data-notificaciones]");
    if (!contenedor || document.hidden || contenedor.querySelector(".desplegable[open]")) return;
    fetch(contenedor.dataset.notificaciones)
      .then(function (respuesta) {
        return respuesta.ok && !respuesta.redirected ? respuesta.text() : null;
      })
      .then(function (html) {
        if (html !== null && !contenedor.querySelector(".desplegable[open]")) contenedor.innerHTML = html;
      })
      .catch(function () {});
  }

  setInterval(actualizarNotificaciones, 15000);
  document.addEventListener("visibilitychange", actualizarNotificaciones);

  window.addEventListener("pageshow", function () {
    document.documentElement.classList.remove("navegando");
    var activo = document.querySelector(".header-link-activo");
    var subrayado = document.querySelector(".header-subrayado");
    if (activo && activo !== linkActivoOriginal) {
      activo.classList.remove("header-link-activo");
      linkActivoOriginal.classList.add("header-link-activo");
    }
    if (subrayado) subrayado.removeAttribute("style");
  });
})();
