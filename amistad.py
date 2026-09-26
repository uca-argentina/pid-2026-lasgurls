class Solicitud:
    def __init__(self,emisorID,receptorID):
        self.emisorID=emisorID
        self.receptorID=receptorID
        self.estado="Pendiente"

    def puedeResponder(self,usuarioID):
        return usuarioID==self.receptorID and self.estado=="Pendiente"

    def aceptar(self,usuarioID):
        if self.puedeResponder(usuarioID):
            self.estado="Aceptada"

    def rechazar(self,usuarioID):
        if self.puedeResponder(usuarioID):
            self.estado="Rechazada"

    def eliminar(self,usuarioID):
        esParte=usuarioID in (self.emisorID,self.receptorID)
        if esParte and self.estado=="Aceptada":
            self.estado="Eliminada"

    
    def esEntre(self,primerID,segundoID):
        mismoSentido=self.emisorID==primerID and self.receptorID==segundoID
        sentidoInverso=self.emisorID==segundoID and self.receptorID==primerID

        return mismoSentido or sentidoInverso


class GestorAmistades:
    def __init__(self,solicitudes=None):
        self.solicitudes=[]

        if solicitudes is not None:
            for fila in solicitudes:
                solicitud=Solicitud(fila.emisorID,fila.receptorID)
                solicitud.estado=fila.estado
                self.solicitudes.append(solicitud)

    def puedeEnviar(self,emisorID,receptorID):
        sonDistintos= emisorID!=receptorID
        hayPendiente=self.haySolicitudPendiente(emisorID,receptorID)
        yaSonAmigos = self.sonAmigos(emisorID,receptorID)
        return sonDistintos and not hayPendiente and not yaSonAmigos
    
    def sonAmigos(self,primerID,segundoID):
        for solicitud in self.solicitudes:
            esEntreUsuarios=solicitud.esEntre(primerID,segundoID)
            estaAceptada=(solicitud.estado=="Aceptada")
            if esEntreUsuarios and estaAceptada:
                return True
        return False
    
    def enviarSolicitud(self,emisorID,receptorID):
        if self.puedeEnviar(emisorID,receptorID):
            solicitud=Solicitud(emisorID,receptorID)
            self.solicitudes.append(solicitud)
            return solicitud

    def haySolicitudPendiente(self,emisorID,receptorID):
        for solicitud in self.solicitudes:
            esEntreUsuarios=solicitud.esEntre(emisorID,receptorID)
            estaPendiente=(solicitud.estado=="Pendiente")
            if esEntreUsuarios and estaPendiente:
                return True
        return False

    def solicitudesRecibidas(self,usuarioID):
        recibidas = []
        for solicitud in self.solicitudes:
            esReceptor= (solicitud.receptorID==usuarioID)
            estaPendiente= (solicitud.estado=="Pendiente")
            if esReceptor and estaPendiente:
                recibidas.append(solicitud)
        return recibidas

