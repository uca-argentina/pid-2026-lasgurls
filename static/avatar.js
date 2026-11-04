window.Avatar = (function () {
  function crear(texto, estilo, clase, conMarco) {
    estilo = estilo || {};
    var forma = estilo.forma ? " avatar-" + estilo.forma : "";
    var nucleo = document.createElement("span");
    nucleo.className = "avatar" + forma + (clase ? " " + clase : "");
    nucleo.textContent = texto;
    if (estilo.color) nucleo.style.background = estilo.color;
    if (conMarco === false || !estilo.marco) return nucleo;
    var marco = document.createElement("span");
    marco.className = "avatar-marco avatar-marco-" + estilo.marco + forma;
    marco.appendChild(nucleo);
    return marco;
  }

  function nombre(texto, estilo) {
    estilo = estilo || {};
    var contenedor = document.createDocumentFragment();
    var span = document.createElement("span");
    span.className = "nombre-con-estilo" + (estilo.degrade ? " nombre-degrade" : "");
    span.textContent = texto;
    contenedor.appendChild(span);
    if (estilo.racha) {
      var fuego = document.createElement("span");
      fuego.className = "racha-fuego";
      fuego.title = estilo.racha + " juntadas seguidas cumplidas";
      fuego.textContent = "🔥 " + estilo.racha;
      contenedor.appendChild(fuego);
    }
    return contenedor;
  }

  return { crear: crear, nombre: nombre };
})();
