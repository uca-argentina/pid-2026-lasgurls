(function () {
  var pagina = document.querySelector("[data-checkin]");
  var empezar = pagina && pagina.querySelector("[data-empezar]");
  if (!empezar) return;
  var estado = pagina.querySelector("[data-estado]");
  var modoLocal = Boolean(pagina.dataset.modoLocal);
  var UBICACION_SIMULADA = { latitude: -34.60373, longitude: -58.38157, accuracy: 20 };
  var posicion = null;

  function avisar(texto, esError) {
    estado.textContent = texto;
    estado.classList.toggle("checkin-error", !!esError);
  }

  function pedirUbicacion() {
    return new Promise(function (resolver, rechazar) {
      if (!window.isSecureContext || !navigator.geolocation) {
        rechazar(new Error("Tu navegador no deja usar la ubicación en esta página. Abrí JuntApp desde su dirección https."));
        return;
      }
      navigator.geolocation.getCurrentPosition(function (actual) {
        posicion = actual.coords;
        resolver(posicion);
      }, function (problema) {
        if (modoLocal) {
          posicion = UBICACION_SIMULADA;
          resolver(posicion);
          return;
        }
        rechazar(new Error(problema.code === 1
          ? "Necesitamos tu ubicación para el check-in. Habilitala para JuntApp en la configuración del navegador y recargá la página."
          : "No pudimos obtener tu ubicación. Revisá que el GPS esté prendido y probá de nuevo."));
      }, { enableHighAccuracy: true, timeout: 15000, maximumAge: 30000 });
    });
  }

  function seguirUbicacion() {
    navigator.geolocation.watchPosition(function (actual) {
      posicion = actual.coords;
    }, function () {}, { enableHighAccuracy: true, maximumAge: 30000 });
  }

  function datosDeUbicacion() {
    return { latitud: posicion.latitude, longitud: posicion.longitude, precision: posicion.accuracy };
  }

  function enviar(url, datos) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datos),
    }).then(function (respuesta) {
      return respuesta.json().catch(function () {
        throw new Error("Se cortó la sesión. Recargá la página.");
      }).then(function (cuerpo) {
        if (!respuesta.ok) throw new Error(cuerpo.error || "Algo salió mal. Probá de nuevo.");
        return cuerpo;
      });
    });
  }

  function mostrarQr() {
    var contenedor = pagina.querySelector("[data-qr]");
    var imagen = pagina.querySelector("[data-qr-imagen]");
    var tiempo = pagina.querySelector("[data-qr-tiempo]");
    var presentes = pagina.querySelector("[data-presentes]");
    var textoCodigo = pagina.querySelector("[data-qr-codigo]");
    var copiar = pagina.querySelector("[data-copiar]");
    if (copiar) copiar.addEventListener("click", function () {
      navigator.clipboard.writeText(textoCodigo.textContent).then(function () {
        copiar.textContent = "¡Copiado!";
        setTimeout(function () { copiar.textContent = "Copiar código"; }, 1500);
      });
    });

    function dibujarPresentes(nombres) {
      if (!nombres.length) {
        presentes.replaceChildren(crear("li", "checkin-nadie", "Todavía nadie"));
        return;
      }
      presentes.replaceChildren.apply(presentes, nombres.map(function (nombre) {
        return crear("li", "", nombre);
      }));
    }

    function renovar() {
      enviar(pagina.dataset.urlQr, datosDeUbicacion())
        .then(function (respuesta) {
          var qr = qrcode(0, "M");
          qr.addData(respuesta.codigo);
          qr.make();
          imagen.innerHTML = qr.createSvgTag({ cellSize: 8, margin: 2, scalable: true });
          if (textoCodigo) textoCodigo.textContent = respuesta.codigo;
          tiempo.style.animationDuration = respuesta.segundos + "s";
          tiempo.classList.remove("checkin-qr-tiempo-corriendo");
          void tiempo.offsetWidth;
          tiempo.classList.add("checkin-qr-tiempo-corriendo");
          contenedor.hidden = false;
          avisar("");
          dibujarPresentes(respuesta.presentes);
          setTimeout(renovar, (respuesta.segundos - 1) * 1000);
        })
        .catch(function (problema) {
          avisar(problema.message, true);
          contenedor.hidden = true;
          empezar.hidden = false;
        });
    }

    if (navigator.wakeLock) navigator.wakeLock.request("screen").catch(function () {});
    seguirUbicacion();
    renovar();
  }

  function crear(etiqueta, clase, texto) {
    var elemento = document.createElement(etiqueta);
    if (clase) elemento.className = clase;
    elemento.textContent = texto;
    return elemento;
  }

  function mandarCodigo(codigo) {
    var listo = pagina.querySelector("[data-listo]");
    var pegar = pagina.querySelector("[data-pegar]");
    avisar("Chequeando…");
    return enviar(pagina.dataset.urlCheckin, Object.assign({ codigo: codigo }, datosDeUbicacion()))
      .then(function (respuesta) {
        avisar("");
        listo.querySelector("[data-listo-mensaje]").textContent = respuesta.mensaje;
        var racha = listo.querySelector("[data-listo-racha]");
        racha.textContent = "🔥 Racha de " + respuesta.racha;
        racha.hidden = respuesta.racha < 1;
        listo.hidden = false;
        empezar.hidden = true;
        if (pegar) pegar.hidden = true;
      })
      .catch(function (problema) {
        avisar(problema.message, true);
        empezar.textContent = "Probar de nuevo";
        empezar.hidden = false;
      });
  }

  function escanear() {
    var lector = pagina.querySelector("[data-lector]");
    var camara = new Html5Qrcode(lector.id);
    var leyendo = false;

    function alLeer(codigo) {
      if (leyendo) return;
      leyendo = true;
      camara.stop().catch(function () {}).then(function () {
        lector.hidden = true;
        mandarCodigo(codigo);
      });
    }

    lector.hidden = false;
    avisar("Apuntá la cámara al QR");
    camara.start({ facingMode: "environment" }, { fps: 10, qrbox: { width: 220, height: 220 } }, alLeer, function () {})
      .catch(function () {
        lector.hidden = true;
        avisar("No pudimos abrir la cámara. Dale permiso a JuntApp para usarla y probá de nuevo.", true);
        empezar.hidden = false;
      });
  }

  var pegar = pagina.querySelector("[data-pegar]");
  if (pegar) pegar.addEventListener("submit", function (evento) {
    evento.preventDefault();
    var codigo = pegar.elements.codigo.value.trim();
    if (!codigo) return;
    (posicion ? Promise.resolve() : pedirUbicacion())
      .then(function () { mandarCodigo(codigo); })
      .catch(function (problema) { avisar(problema.message, true); });
  });

  empezar.addEventListener("click", function () {
    empezar.hidden = true;
    avisar("Buscando tu ubicación…");
    pedirUbicacion()
      .then(function () {
        if (pagina.dataset.organiza) mostrarQr();
        else escanear();
      })
      .catch(function (problema) {
        avisar(problema.message, true);
        empezar.hidden = false;
      });
  });
})();
