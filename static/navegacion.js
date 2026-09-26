(function () {
  var SELECTOR_CONTENEDOR = "[data-recargable]";

  var peticionActual = null;

  function resolverLocalmente(url, guardarHistorial) {
    if (typeof window.navegarLocalmente !== "function" || !window.navegarLocalmente(url, guardarHistorial)) return false;
    if (peticionActual) peticionActual.abort();
    return true;
  }

  function reemplazarContenido(html, url, guardarHistorial) {
    var documentoNuevo = new DOMParser().parseFromString(html, "text/html");
    var contenedorActual = document.querySelector(SELECTOR_CONTENEDOR);
    var contenedorNuevo = documentoNuevo.querySelector(SELECTOR_CONTENEDOR);

    if (!contenedorActual || !contenedorNuevo) {
      window.location.href = url;
      return;
    }

    contenedorActual.innerHTML = contenedorNuevo.innerHTML;
    document.title = documentoNuevo.title;
    var notificacionesActuales = document.querySelector("[data-notificaciones]");
    var notificacionesNuevas = documentoNuevo.querySelector("[data-notificaciones]");
    if (notificacionesActuales && notificacionesNuevas) notificacionesActuales.innerHTML = notificacionesNuevas.innerHTML;
    if (guardarHistorial) window.history.pushState({}, "", url);
    document.dispatchEvent(new CustomEvent("contenido-actualizado"));
  }

  function navegar(url, opciones, guardarHistorial) {
    if (guardarHistorial === undefined) guardarHistorial = true;
    if (peticionActual) peticionActual.abort();
    var controlador = new AbortController();
    peticionActual = controlador;
    opciones = Object.assign({}, opciones, { signal: controlador.signal });
    var contenedor = document.querySelector(SELECTOR_CONTENEDOR);
    if (contenedor) contenedor.classList.add("cargando");
    document.documentElement.classList.add("navegando");

    fetch(url, opciones)
      .then(function (respuesta) {
        if (!respuesta.ok) {
          window.location.reload();
          return null;
        }
        return respuesta.text().then(function (html) {
          return { html: html, url: respuesta.url };
        });
      })
      .then(function (resultado) {
        if (resultado) reemplazarContenido(resultado.html, resultado.url, guardarHistorial);
      })
      .catch(function (error) {
        if (error.name === "AbortError") return;
        window.location.href = url;
      })
      .finally(function () {
        if (peticionActual !== controlador) return;
        peticionActual = null;
        document.documentElement.classList.remove("navegando");
        var contenedorActual = document.querySelector(SELECTOR_CONTENEDOR);
        if (contenedorActual) contenedorActual.classList.remove("cargando");
      });
  }

  document.addEventListener("click", function (evento) {
    var link = evento.target.closest(SELECTOR_CONTENEDOR + " a");
    if (evento.button !== 0 || evento.ctrlKey || evento.metaKey || evento.shiftKey || evento.altKey) return;
    if (!link || link.target === "_blank" || link.origin !== window.location.origin) return;
    evento.preventDefault();
    if (!resolverLocalmente(link.href, true)) navegar(link.href);
  });

  document.addEventListener("submit", function (evento) {
    if (!evento.target.closest(SELECTOR_CONTENEDOR)) return;
    var form = evento.target;
    if (form.method === "dialog") return;
    evento.preventDefault();
    var metodo = (form.getAttribute("method") || "GET").toUpperCase();

    if (metodo === "GET") {
      var parametros = new URLSearchParams(new FormData(form));
      navegar(form.action.split("?")[0] + "?" + parametros.toString());
    } else {
      navegar(form.action, { method: "POST", body: new FormData(form) });
    }
  });

  window.addEventListener("popstate", function () {
    if (!resolverLocalmente(window.location.href, false)) navegar(window.location.href, undefined, false);
  });
})();
