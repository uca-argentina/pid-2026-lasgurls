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

  var ultimasNotificaciones = null;
  var contenidoEnVivo = new WeakMap();

  function actualizarNotificaciones() {
    var contenedor = document.querySelector("[data-notificaciones]");
    if (!contenedor || document.hidden || contenedor.querySelector(".desplegable[open]")) return;
    fetch(contenedor.dataset.notificaciones)
      .then(function (respuesta) {
        return respuesta.ok && !respuesta.redirected ? respuesta.text() : null;
      })
      .then(function (html) {
        if (html === null || contenedor.querySelector(".desplegable[open]")) return;
        contenedor.innerHTML = html;
        if (ultimasNotificaciones !== null && html !== ultimasNotificaciones) actualizarEnVivo();
        ultimasNotificaciones = html;
      })
      .catch(function () {});
  }

  function guardarContenidoEnVivo() {
    document.querySelectorAll("[data-en-vivo]").forEach(function (zona) {
      contenidoEnVivo.set(zona, zona.innerHTML);
      delete zona.dataset.editando;
    });
  }

  function estaEditando(zona) {
    var activo = document.activeElement;
    return zona.dataset.editando === "si" || (zona.contains(activo) && activo.matches("input, textarea, select"));
  }

  function actualizarEnVivo() {
    var zonas = document.querySelectorAll("[data-en-vivo]");
    if (!zonas.length || document.hidden || document.querySelector("dialog[open]")) return;
    fetch(window.location.href)
      .then(function (respuesta) {
        return respuesta.ok && !respuesta.redirected ? respuesta.text() : null;
      })
      .then(function (html) {
        if (html === null || document.querySelector("dialog[open]")) return;
        var nuevo = new DOMParser().parseFromString(html, "text/html");
        var cambio = false;
        document.querySelectorAll("[data-en-vivo]").forEach(function (zona) {
          var otra = nuevo.querySelector('[data-en-vivo="' + zona.dataset.enVivo + '"]');
          if (!otra || estaEditando(zona) || otra.innerHTML === contenidoEnVivo.get(zona)) return;
          zona.innerHTML = otra.innerHTML;
          contenidoEnVivo.set(zona, zona.innerHTML);
          cambio = true;
        });
        if (cambio) document.dispatchEvent(new CustomEvent("contenido-actualizado"));
      })
      .catch(function () {});
  }

  document.addEventListener("input", function (evento) {
    var zona = evento.target.closest("[data-en-vivo]");
    if (zona) zona.dataset.editando = "si";
  });

  document.addEventListener("contenido-actualizado", guardarContenidoEnVivo);
  guardarContenidoEnVivo();

  setInterval(actualizarNotificaciones, 10000);
  setInterval(actualizarEnVivo, 10000);
  document.addEventListener("visibilitychange", actualizarEnVivo);

  var toast = document.querySelector("[data-toast]");
  if (toast) {
    setTimeout(function () {
      toast.classList.add("toast-saliendo");
      setTimeout(function () { toast.remove(); }, 400);
    }, 4500);
  }

  function mostrarInsignia(desplegable, cantidad) {
    var insignia = desplegable.querySelector(".insignia");
    if (!insignia) return;
    if (cantidad > 0) insignia.textContent = cantidad < 10 ? cantidad : "9+";
    else insignia.remove();
  }

  document.addEventListener("toggle", function (evento) {
    var desplegable = evento.target;
    if (!desplegable.dataset || desplegable.dataset.marcarLeidas === undefined) return;
    if (!desplegable.open) {
      if (desplegable.dataset.leidas) actualizarNotificaciones();
      return;
    }
    var avisos = Number(desplegable.dataset.avisos);
    if (!avisos || desplegable.dataset.leidas) return;
    desplegable.dataset.leidas = "si";
    fetch(desplegable.dataset.marcarLeidas, { method: "POST" })
      .then(function (respuesta) {
        if (respuesta.ok) mostrarInsignia(desplegable, Number(desplegable.dataset.pendientes) - avisos);
      })
      .catch(function () {});
  }, true);
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
