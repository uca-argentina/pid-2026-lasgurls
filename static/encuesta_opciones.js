(function () {
  var contenedor = document.querySelector("[data-opciones-encuesta]");
  if (!contenedor) return;

  var maximo = parseInt(contenedor.dataset.maximo, 10);
  var minimo = parseInt(contenedor.dataset.minimo, 10);
  var plantilla = document.getElementById("plantilla-opcion");
  var agregar = document.querySelector("[data-agregar-opcion]");
  var contador = 0;

  function filas() {
    return contenedor.querySelectorAll(".opcion-encuesta");
  }

  // Cada campo necesita un id propio para que los mensajes de error no se pisen entre filas.
  function numerar(fila) {
    contador += 1;
    fila.querySelectorAll("input").forEach(function (campo) {
      campo.id = campo.name + "-" + contador;
      var etiqueta = campo.parentNode.querySelector("label");
      if (etiqueta) etiqueta.htmlFor = campo.id;
    });
  }

  function actualizar() {
    var cantidad = filas().length;
    agregar.hidden = cantidad >= maximo;
    contenedor.querySelectorAll("[data-quitar]").forEach(function (boton) {
      boton.hidden = cantidad <= minimo;
    });
  }

  filas().forEach(numerar);
  actualizar();

  agregar.addEventListener("click", function () {
    if (filas().length >= maximo) return;
    var fila = plantilla.content.firstElementChild.cloneNode(true);
    numerar(fila);
    contenedor.appendChild(fila);
    actualizar();
    fila.querySelector("input").focus();
  });

  contenedor.addEventListener("click", function (evento) {
    var boton = evento.target.closest("[data-quitar]");
    if (!boton || filas().length <= minimo) return;
    boton.closest(".opcion-encuesta").remove();
    actualizar();
  });
})();