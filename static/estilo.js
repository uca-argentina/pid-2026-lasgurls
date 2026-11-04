(function () {
  var formulario = document.querySelector("[data-formulario-estilo]");
  var vista = document.querySelector("[data-vista-previa]");
  if (!formulario || !vista) return;

  function elegido(nombre) {
    var opcion = formulario.querySelector('input[name="' + nombre + '"]:checked');
    return opcion && !opcion.closest("fieldset").disabled ? opcion.value : "";
  }

  function actualizar() {
    var estilo = { color: elegido("color"), forma: elegido("forma"), marco: elegido("marco") };
    vista.replaceChildren(Avatar.crear(formulario.dataset.iniciales, estilo, "avatar-grande"));
  }

  formulario.addEventListener("change", actualizar);
})();
