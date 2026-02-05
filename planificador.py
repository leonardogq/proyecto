from datetime import datetime, date, timedelta
import json

class PlanificadorEventos:
    
    # Clase principal del sistema.
    

    def __init__(self):
        
        self.recursos = None
        self.restricciones = None
        self.eventos = []

    # Métodos principales para agregar y eliminar eventos

    def agregar_evento(self, evento):
        
        # Intenta agregar un evento al planificador.
        # Ejecuta todas las validaciones en orden.
        # Devuelve (True, "") si se agrega correctamente.
        # Devuelve (False, lista_de_errores) si falla alguna validación.
        
        errores = []

        #  Validar fecha
        valido, mensaje = self._validar_fechas(evento)
        if not valido:
            errores.append(mensaje)

        #  Validar reglas específicas del tipo de evento
        valido, mensaje = self._validar_reglas_evento(evento)
        if not valido:
            errores.append(mensaje)

        #  Validar corequisitos
        errores += self.validar_corequisitos_por_recurso(evento)
        errores += self.validar_corequisitos_por_categoria(evento)

        #  Validar exclusiones
        errores += self.validar_exclusiones_por_sala(evento)
        errores += self.validar_exclusiones_por_evento(evento)

        #  Validar personal obligatorio
        valido, mensaje = self._validar_personal_obligatorio(evento)
        if not valido:
            errores.append(mensaje)

        #  Validar disponibilidad de recursos
        errores += self._validar_disponibilidad_recursos(evento)

        # Validar eventos prohibidos por sala
        errores += self.validar_evento_por_sala(evento)


        #  Resultado final
        if errores:
            return False, errores

        # si todo ok, agregar evento
        self.eventos.append(evento)
        self.guardar_eventos_json()  #  guardar cambios en JSON
    

        return True, "Evento agregado correctamente"

    def eliminar_evento(self, tipo, sala, fecha):
        
        # Elimina un evento del planificador buscando por:
        # - tipo de evento
        # - sala
        # - fecha (datetime.date o datetime)
        
        if isinstance(fecha, datetime):
            fecha = fecha.date()

        evento_a_eliminar = None
        for e in self.eventos:
            if (
                e.get("tipo") == tipo and
                e.get("sala") == sala and
                e.get("inicio").date() == fecha
            ):
                evento_a_eliminar = e
                break

        if evento_a_eliminar is None:
            return False, "Evento no encontrado"

        self.eventos.remove(evento_a_eliminar)
        self.guardar_eventos_json()  #  actualizar JSON tras eliminar
        return True, "Evento eliminado correctamente"

    # Validaciones internas

    # fechas listo
    def _validar_fechas(self, evento):
        
        # Valida la fecha del evento bajo la regla:
        # - Solo puede haber un evento por sala por día.
        
        # garantiza que haya fecha y sala
        if "inicio" not in evento or "sala" not in evento:
            return False, "El evento debe tener fecha de inicio y sala"

        inicio = evento["inicio"]
        sala = evento["sala"]

        if not isinstance(inicio, datetime):
            return False, "La fecha de inicio debe ser un objeto datetime"

        fecha_evento = inicio.date()
        fecha_hoy = date.today()

        # No permitir fechas pasadas
        if fecha_evento < fecha_hoy:
            return False, "No se pueden crear eventos en fechas anteriores a hoy"


        for e in self.eventos:
            if e["sala"] == sala and e["inicio"].date() == fecha_evento:
                # Hay conflicto, llamamos al método que sugiere próxima fecha libre
                sugerencia = self.sugerir_proxima_fecha_libre(sala, fecha_evento)
                return False, (
                    f"Ya existe un evento en la sala {sala} para el día {fecha_evento}. "
                    f"Sugerencia: próxima fecha libre {sugerencia}"
                )

        return True, ""


    # reglas listo
    def _validar_reglas_evento(self, evento):
        
        # Valida reglas específicas según el tipo de evento.
        
        # garantiza que haya un tipo
        if "tipo" not in evento:
            return False, "El evento debe tener un tipo"

        # garantiza que haya recursos
        if "recursos" not in evento:
            return False, "El evento debe especificar recursos"

        tipo = evento["tipo"]
        recursos = evento["recursos"]

        reglas_evento = self.restricciones.get("reglas_evento", {})

        # si el evento no se encuentra dentro de los 4 definidos devuelve false
        if tipo not in reglas_evento:
            return False, f"No existen reglas definidas para el evento '{tipo}'"

        reglas = reglas_evento[tipo]

        # regla micrófonos(podria hacerlo general pero por ahora solo esta esta)
        if "micrófonos" in reglas:
            minimo = reglas["micrófonos"]
            usados = recursos.get("Micrófonos", 0)

        
            if usados < minimo:
                return (
                    False,
                    f"El evento '{tipo}' requiere al menos "
                    f"{minimo} micrófonos (se indicaron {usados})"
                )

        return True, ""



    # co_requisitos ver luego
    def validar_corequisitos_por_recurso(self, evento):
        
        # Valida que cada recurso del evento cumpla con los corequisitos definidos entre recursos individuales.

        # Regla:
        # Por cada unidad de un recurso (clave), debe existir al menos la misma cantidad de cada recurso listado en su valor (lista de corequisitos).
    
        
        errores = []
        recursos_evento = evento.get("recursos", {})
        coreq_recursos = self.restricciones.get("corequisitos", {}).get("recursos", {})

        for recurso, requeridos in coreq_recursos.items():
            cantidad_recurso = recursos_evento.get(recurso, 0)
            if cantidad_recurso == 0:
                continue  # si no se usa el recurso principal, no hace falta revisar

            for req in requeridos:
                cantidad_req = recursos_evento.get(req, 0)
                if cantidad_req < cantidad_recurso:
                    errores.append(
                        f"'{recurso}' requiere al menos {cantidad_recurso} unidades de '{req}' (hay {cantidad_req})."
                    )

        return errores

    def validar_corequisitos_por_categoria(self, evento):
        
        # Valida que cada recurso del evento cumpla con los corequisitos definidos en su categoría.
        

        # Regla:
        # Por cada unidad de un recurso (que no esté en 'excepto'), debe haber al menos la misma cantidad de cada recurso en 'requiere'.
          
        
        errores = []
        recursos_evento = evento["recursos"]
        categorias = self.restricciones["corequisitos"]["categorias"]

        # Acumulador total de requerimientos (ej: cables)
        requerimientos_totales = {}

        for recurso, cantidad in recursos_evento.items():
            if cantidad == 0:
                continue

            # Determinar categoría del recurso
            categoria_recurso = None
            for categoria, recursos_categoria in self.recursos.items():
                if isinstance(recursos_categoria, dict) and recurso in recursos_categoria:
                    categoria_recurso = categoria
                    break

            if not categoria_recurso:
                continue

            reglas = categorias.get(categoria_recurso, {})
            requiere = reglas.get("requiere", [])
            excepto = reglas.get("excepto", [])

            if recurso in excepto:
                continue

            for req in requiere:
                requerimientos_totales[req] = requerimientos_totales.get(req, 0) + cantidad

        for req, total_requerido in requerimientos_totales.items():
            total_en_evento = recursos_evento.get(req, 0)
            if total_en_evento < total_requerido:
                errores.append(
                    f"Se requieren {total_requerido} '{req}', pero solo hay {total_en_evento}."
                )

        return errores



    # exclusiones listo
    def validar_exclusiones_por_sala(self, evento):
        
        # valida que el evento no incluya recursos prohibidos según la sala en la que se realiza.


        errores = []

        # garantiza que haya sala y recursos
        if "sala" not in evento or "recursos" not in evento:
            return ["El evento debe tener sala y recursos especificados"]


        sala = evento["sala"]
        recursos_evento = evento["recursos"]

        exclusiones_sala = self.restricciones.get("exclusiones", {}).get("por_sala", {})

        # Solo aplica si hay reglas para la sala específica
        reglas = exclusiones_sala.get(sala, {})
        if not reglas:
            return errores

        # Instrumentos prohibidos
        if reglas.get("instrumentos", False):
            for instrumento in recursos_evento:
                if instrumento in self.recursos.get("instrumentos", {}) and recursos_evento[instrumento] > 0:
                    errores.append(
                        f"El instrumento '{instrumento}' no puede usarse en la sala {sala}"
                    )

        # Equipos prohibidos
        for equipo in reglas.get("equipos", []):
            if recursos_evento.get(equipo, 0) > 0:
                errores.append(
                    f"El equipo '{equipo}' no puede usarse en la sala {sala}"
                )

        # Personal prohibido
        for rol in reglas.get("personal", []):
            if recursos_evento.get(rol, 0) > 0:
                errores.append(
                    f"El personal '{rol}' no puede asignarse en la sala {sala}"
                )

        return errores

    def validar_exclusiones_por_evento(self, evento):
            
            # Valida que el evento no incluya recursos prohibidos según el tipo de evento.
            # La manera en que esta hecha esta validacion permite que se puedan extender las exclusiones por evento sin modificar el codigo
            
            errores = []
            # garantiza que haya tipo y recursos
            if "tipo" not in evento or "recursos" not in evento:
                return ["El evento debe tener tipo y recursos especificados"]

            tipo = evento["tipo"]
            recursos_evento = evento["recursos"]

            exclusiones_evento = self.restricciones.get("exclusiones", {}).get("por_evento", {})

            if tipo not in exclusiones_evento:
                return errores

            reglas = exclusiones_evento[tipo]
            prohibidos = reglas.get("prohibido", [])

            for recurso in prohibidos:
                if recursos_evento.get(recurso, 0) > 0:
                    errores.append(
                        f"El evento '{tipo}' no puede incluir '{recurso}'"
                    )

            return errores


    # sala-evento prohibido listo
    def validar_evento_por_sala(self, evento):
        errores = []

        eventos_prohibidos = self.restricciones.get("exclusiones", {}).get("eventos_prohibidos", {})
        prohibidos_en_sala = eventos_prohibidos.get(evento["sala"], [])

        if evento["tipo"] in prohibidos_en_sala:
            errores.append(
                f"El evento '{evento['tipo']}' no se puede realizar en la sala '{evento['sala']}'."
            )

        return errores

    


    # personal listo
    def _validar_personal_obligatorio(self, evento):
        
        # Valida que el evento incluya el personal obligatorio según la sala en la que se realiza.
        
        # garantiza que haya sala y recursos
        if "sala" not in evento:
            return False, "El evento debe especificar una sala"

        if "recursos" not in evento:
            return False, "El evento debe especificar recursos"


        sala = evento["sala"]
        recursos = evento["recursos"]

        reglas_personal = self.restricciones.get("personal_obligatorio", {})

        if sala not in reglas_personal:
            return True, ""

        personal_requerido = reglas_personal[sala]

        for rol, minimo in personal_requerido.items():
            usados = recursos.get(rol, 0)
            if usados < minimo:
                return (
                    False,
                    f"En la sala {sala} se requiere al menos "
                    f"{minimo} '{rol}' (se indicaron {usados})"
                )

        return True, ""


    # disp recursos
    def _validar_disponibilidad_recursos(self, evento):
        
        # Valida que el evento pueda usar los recursos solicitados, considerando los recursos ya ocupados por otros eventos el mismo día.
        
        
        errores = []

        # garantiza que haya fecha y recursos
        if "inicio" not in evento or "recursos" not in evento:
            return ["El evento debe tener fecha de inicio y recursos especificados"]

        fecha_evento = evento["inicio"].date()
        recursos_solicitados = evento["recursos"]

        # Contar recursos ocupados por otros eventos el mismo día
        recursos_ocupados = {}

        for e in self.eventos:
            if e["inicio"].date() != fecha_evento:
                continue

            for recurso, cantidad in e["recursos"].items():
                recursos_ocupados[recurso] = recursos_ocupados.get(recurso, 0) + cantidad

        # Verificar disponibilidad real
        for categoria, recursos_categoria in self.recursos.items():
            if not isinstance(recursos_categoria, dict):
                continue

            for recurso, total_disponible in recursos_categoria.items():
                usado = recursos_ocupados.get(recurso, 0)
                solicitado = recursos_solicitados.get(recurso, 0)

                disponible_real = total_disponible - usado

                if solicitado > disponible_real:
                    errores.append(
                        f"No hay suficientes '{recurso}'. "
                        f"Disponibles: {disponible_real}, solicitados: {solicitado}."
                    )

        return errores

    

    # otros

    def sugerir_proxima_fecha_libre(self, sala, fecha_inicio):
        
        # Devuelve la próxima fecha libre para la sala indicada, sin modificar la lista de eventos ni la lógica de _validar_fechas.
        
        fecha = fecha_inicio
        fechas_ocupadas = {e["inicio"].date() for e in self.eventos if e["sala"] == sala}

        # Incrementamos día a día hasta encontrar uno libre
        while fecha in fechas_ocupadas:
            fecha += timedelta(days=1)

        return fecha



    def mostrar_agenda(self):
        
        # Devuelve la lista completa de eventos registrados, con toda su información.
        # Ordena por fecha de inicio para que se vea la agenda cronológicamente.
        
        if not self.eventos:
            return "No hay eventos programados."

        # Ordenamos los eventos por fecha de inicio
        eventos_ordenados = sorted(self.eventos, key=lambda e: e["inicio"])

        agenda = []
        for e in eventos_ordenados:
            tipo = e.get("tipo", "Desconocido")
            sala = e.get("sala", "No asignada")
            inicio = e.get("inicio", "No asignada")
            recursos = e.get("recursos", {})
            agenda.append(
                f"Evento: {tipo}\n"
                f"  Sala: {sala}\n"
                f"  Fecha y hora: {inicio}\n"
                f"  Recursos: {recursos}\n"
            )

        return "\n".join(agenda)



    def guardar_eventos_json(self, archivo="data/eventos.json"):
        
        # Guarda todos los eventos actuales en un archivo JSON.
        # Cada fecha se convierte a ISO string para poder guardarla.
        
        eventos_a_guardar = []
        for e in self.eventos:
            evento_copia = e.copy()
            if isinstance(evento_copia.get("inicio"), datetime):
                evento_copia["inicio"] = evento_copia["inicio"].isoformat()
            eventos_a_guardar.append(evento_copia)

        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(eventos_a_guardar, f, ensure_ascii=False, indent=2)



    def cargar_eventos_json(self, archivo="data/eventos.json"):
        
        # Carga eventos desde un archivo JSON.
        # Convierte las fechas de string ISO a datetime.
        
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                self.eventos = json.load(f)
            for e in self.eventos:
                if isinstance(e.get("inicio"), str):
                    e["inicio"] = datetime.fromisoformat(e["inicio"])
        except FileNotFoundError:
            self.eventos = []


    def cargar_recursos_json(self, archivo="data/recursos.json"):
        
        # Carga los recursos disponibles desde un archivo JSON.
        
        with open("data/recursos.json", "r", encoding="utf-8") as f:
            self.recursos = json.load(f)

    def cargar_restricciones_json(self, archivo="data/restricciones.json"):
        
        # Carga las restricciones desde un archivo JSON.
        
        with open("data/restricciones.json", "r", encoding="utf-8") as f:
            self.restricciones = json.load(f)