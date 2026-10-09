(function () {
  var DIAS = ["domingos", "lunes", "martes", "miércoles", "jueves", "viernes", "sábados"];

  function actualizar(form) {
    var bloque = form && form.querySelector("[data-repeticion]");
    if (!bloque) return;
    var fecha = form.elements.fecha.value;
    var desde = form.elements.hora_inicio.value;
    var hasta = form.elements.hora_fin.value;
    if (!fecha) return;

    var partes = fecha.split("-").map(Number);
    var dia = new Date(partes[0], partes[1] - 1, partes[2]);
    var fin = new Date(partes[0] + 1, partes[1] - 1, partes[2]);
    if (fin.getDate() !== partes[2]) fin.setDate(0);

    var horario = desde && hasta ? " de " + desde + " a " + hasta : "";
    bloque.querySelector("[data-repeticion-titulo]").textContent = "Se repite todos los " + DIAS[dia.getDay()] + horario;
    bloque.querySelector("[data-repeticion-detalle]").textContent = "Hasta el " + fin.toLocaleDateString("es-AR");
  }

  function formDeLaPagina() {
    var bloque = document.querySelector("[data-repeticion]");
    return bloque && bloque.closest("form");
  }

  document.addEventListener("input", function (evento) {
    if (evento.target.form) actualizar(evento.target.form);
  });
  document.addEventListener("change", function (evento) {
    if (evento.target.form) actualizar(evento.target.form);
  });
  document.addEventListener("click", function () {
    setTimeout(function () {
      actualizar(formDeLaPagina());
    });
  });
  document.addEventListener("contenido-actualizado", function () {
    actualizar(formDeLaPagina());
  });
  actualizar(formDeLaPagina());
})();
