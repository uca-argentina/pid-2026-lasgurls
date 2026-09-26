(function () {
  var panel = document.querySelector("[data-nueva-categoria]");
  if (!panel) return;

  var abrir = document.querySelector("[data-abrir-nueva-categoria]");
  var nombre = panel.querySelector("[data-nombre-categoria]");
  var error = panel.querySelector("[data-error-categoria]");

  function mostrarPanel(visible) {
    panel.hidden = !visible;
    abrir.hidden = visible;
    error.hidden = true;
    if (visible) nombre.focus();
    else nombre.value = "";
  }

  function agregarOpcion(categoria) {
    var opcion = document.createElement("label");
    opcion.className = "categoria-opcion";
    var radio = document.createElement("input");
    radio.type = "radio";
    radio.name = "categoria";
    radio.value = categoria.id;
    radio.checked = true;
    var chip = document.createElement("span");
    chip.className = "categoria-chip";
    var circulo = document.createElement("i");
    circulo.style.background = categoria.color;
    chip.append(circulo, categoria.nombre);
    opcion.append(radio, chip);
    abrir.before(opcion);
  }

  function guardar() {
    var datos = new FormData();
    datos.append("nombre", nombre.value);
    datos.append("color", panel.querySelector('input[name="color_nueva_categoria"]:checked').value);
    fetch(panel.dataset.url, { method: "POST", body: datos })
      .then(function (respuesta) {
        return respuesta.json().then(function (cuerpo) {
          if (!respuesta.ok) throw cuerpo;
          return cuerpo;
        });
      })
      .then(function (categoria) {
        if (panel.dataset.alCrear === "recargar") {
          window.location.reload();
          return;
        }
        agregarOpcion(categoria);
        mostrarPanel(false);
      })
      .catch(function (problema) {
        error.textContent = (problema && problema.error) || "No pudimos crear la categoría. Probá de nuevo.";
        error.hidden = false;
      });
  }

  abrir.addEventListener("click", function () {
    mostrarPanel(true);
  });
  panel.querySelector("[data-cancelar-categoria]").addEventListener("click", function () {
    mostrarPanel(false);
  });
  panel.querySelector("[data-guardar-categoria]").addEventListener("click", guardar);
  nombre.addEventListener("keydown", function (evento) {
    if (evento.key !== "Enter") return;
    evento.preventDefault();
    guardar();
  });
})();
