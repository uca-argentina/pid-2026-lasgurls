(function () {
  var MENSAJES_VACIO = {
    checkbox: "Marcá esta casilla para continuar.",
    date: "Elegí una fecha.",
    time: "Elegí un horario.",
    email: "Escribí tu email.",
    password: "Escribí tu contraseña.",
  };
  var EMAIL_INVALIDO = "Ese email no es válido. Por ejemplo: nombre@ejemplo.com";

  function problemaPassword(password) {
    if (password.length < 8) return "La contraseña debe tener al menos 8 caracteres";
    if (new TextEncoder().encode(password).length > 72) return "La contraseña no puede tener más de 72 caracteres";
    if (!/\p{Lu}/u.test(password)) return "La contraseña debe tener al menos una mayúscula";
    if (!/[^\p{L}\p{N}]/u.test(password)) return "La contraseña debe tener al menos un símbolo";
    return "";
  }

  function aplicarReglasPropias(campo) {
    var mensaje = "";
    if (campo.value && campo.dataset.password !== undefined) mensaje = problemaPassword(campo.value);
    var otro = campo.dataset.distintoDe && campo.form.elements[campo.dataset.distintoDe];
    if (otro && campo.value && campo.value === otro.value) mensaje = campo.dataset.mensajeDistinto;
    var fecha = campo.dataset.noPasado && campo.form.elements[campo.dataset.noPasado];
    var ahora = new Date();
    ahora.setSeconds(0, 0);
    if (fecha && fecha.value && campo.value && new Date(fecha.value + "T" + campo.value) < ahora) mensaje = "Ese horario ya pasó.";
    campo.setCustomValidity(mensaje);
  }

  function mensajeDe(campo) {
    var validez = campo.validity;
    if (validez.valueMissing) return campo.dataset.mensaje || MENSAJES_VACIO[campo.type] || "Completá este campo.";
    if ((validez.typeMismatch || validez.patternMismatch) && campo.type === "email") return EMAIL_INVALIDO;
    if (validez.tooLong) return "Es demasiado largo.";
    if (validez.rangeUnderflow) return campo.dataset.mensajeMinimo || "El valor es demasiado chico.";
    return campo.validationMessage;
  }

  function marcar(elemento, clave, mensaje) {
    var id = "error-" + clave;
    var error = document.getElementById(id);
    var campo = elemento.closest(".campo");
    if (campo) campo.classList.toggle("campo-invalido", Boolean(mensaje));

    if (!mensaje) {
      if (error) error.remove();
      elemento.removeAttribute("aria-invalid");
      return;
    }
    if (!error) {
      error = document.createElement("p");
      error.className = "campo-error";
      error.id = id;
      if (campo) campo.appendChild(error);
      else (elemento.closest("label") || elemento).after(error);
    }
    error.textContent = mensaje;
    elemento.setAttribute("aria-invalid", "true");
    elemento.setAttribute("aria-describedby", id);
  }

  function validar(formulario) {
    var conError = [];
    formulario.querySelectorAll("input, select, textarea").forEach(function (campo) {
      if (!campo.willValidate) return;
      aplicarReglasPropias(campo);
      var valido = campo.checkValidity();
      marcar(campo, campo.id || campo.name, valido ? "" : mensajeDe(campo));
      if (!valido) conError.push(campo);
    });
    formulario.querySelectorAll("[data-requiere-uno]").forEach(function (grupo, indice) {
      var valido = Boolean(grupo.querySelector("input:checked"));
      marcar(grupo, "grupo-" + indice, valido ? "" : grupo.dataset.requiereUno);
      if (!valido) conError.push(grupo.querySelector("input") || grupo);
    });
    return conError.sort(function (a, b) {
      return a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
    });
  }

  document.querySelectorAll("form").forEach(function (formulario) {
    formulario.noValidate = true;
  });

  document.addEventListener("submit", function (evento) {
    var formulario = evento.target;
    if (formulario.method === "dialog") return;
    formulario.dataset.intentado = "";
    var conError = validar(formulario);
    if (!conError.length) return;
    evento.preventDefault();
    evento.stopImmediatePropagation();
    conError[0].focus({ preventScroll: true });
    conError[0].scrollIntoView({ block: "center", behavior: "smooth" });
  }, true);

  function revalidar(evento) {
    var formulario = evento.target.form;
    if (formulario && formulario.dataset.intentado !== undefined) validar(formulario);
  }
  document.addEventListener("input", revalidar);
  document.addEventListener("change", revalidar);
})();
