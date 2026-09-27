(function(){
  document.addEventListener("click",function(evento){
    var boton=evento.target.closest("[data-grupo]");
    if(!boton)return;
    var miembros=boton.dataset.grupo.split(",");
    document.querySelectorAll('input[name="invitados"]').forEach(function(casilla){
      if(miembros.indexOf(casilla.value)!==-1&&!casilla.checked){
        casilla.checked=true;
        casilla.dispatchEvent(new Event("change",{bubbles:true}));
      }
    });
  });
})();
