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

        # Validaciones (todas devuelven listas)
        errores += self._validar_fechas(evento)
        errores += self._validar_reglas_evento(evento)
        errores += self.validar_corequisitos_por_recurso(evento)
        errores += self.validar_corequisitos_por_categoria(evento)
        errores += self.validar_exclusiones_por_sala(evento)
        errores += self.validar_exclusiones_por_evento(evento)
        errores += self.validar_evento_por_sala(evento)
        errores += self._validar_personal_obligatorio(evento)
        errores += self._validar_disponibilidad_recursos(evento)

        # Resultado final
        if errores:
            return False, errores

        # si todo ok, agregar evento
        self.eventos.append(evento)
        self.guardar_eventos_json()  # guardar cambios en JSON
    
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
                e.get("fecha").date() == fecha
            ):
                evento_a_eliminar = e
                break

        if evento_a_eliminar is None:
            return False, "Evento no encontrado"

        self.eventos.remove(evento_a_eliminar)
        self.guardar_eventos_json()  # actualizar JSON tras eliminar
        return True, "Evento eliminado correctamente"

    #             VALIDACIONES 

    # fechas listo
    def _validar_fechas(self, evento):
        
        # Valida la fecha del evento bajo la regla:
        # - Solo puede haber un evento por sala por día.
        
        errores = []

        fecha = evento.get("fecha")
        sala = evento.get("sala")

        if not isinstance(fecha, datetime):
            errores.append("La fecha debe ser un objeto datetime")
            return errores

        fecha_evento = fecha.date()
        fecha_hoy = date.today()

        # No permitir fechas pasadas
        if fecha_evento < fecha_hoy:
            errores.append("No se pueden crear eventos en fechas anteriores a hoy")

        for e in self.eventos:
            if e["sala"] == sala and e["fecha"].date() == fecha_evento:
                sugerencia = self.sugerir_proxima_fecha_libre( sala, fecha_evento, evento)
                errores.append(
                    f"Ya existe un evento en la sala {sala} para el día {fecha_evento}. "
                    f"Sugerencia: próxima fecha libre {sugerencia}"
                )
                break

        return errores


    # reglas listo
    def _validar_reglas_evento(self, evento):
        
        # Valida reglas específicas según el tipo de evento.
        
        errores = []

        tipo = evento.get("tipo")
        recursos = evento.get("recursos", {})

        reglas_evento = self.restricciones.get("reglas_evento", {})

        # si el evento no se encuentra dentro de los definidos(no ocurrira nunca pero lo pongo igual)
        if tipo not in reglas_evento:
            errores.append(f"No existe el evento '{tipo}'")
            return errores

        reglas = reglas_evento[tipo]

        # regla micrófonos (por ahora solo esta)
        if "micrófonos" in reglas:
            minimo = reglas["micrófonos"]
            usados = recursos.get("Micrófonos", 0)

            if usados < minimo:
                errores.append(
                    f"El evento '{tipo}' requiere al menos "
                    f"{minimo} micrófonos (se indicaron {usados})"
                )

                # Regla: evento requiere al menos un instrumento
        if reglas.get("requiere_instrumentos"):
            instrumentos = self.recursos.get("instrumentos", {})
            total_instrumentos = sum(
                cantidad for recurso, cantidad in recursos.items()
                if recurso in instrumentos
            )

            if total_instrumentos == 0:
                errores.append(
                    f"El evento '{tipo}' debe incluir al menos un instrumento."
                )


        return errores



    # co-requisitos por recurso
    def validar_corequisitos_por_recurso(self, evento):
        
        # Valida que cada recurso del evento cumpla con los corequisitos definidos entre recursos individuales.

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
        
        errores = []
        recursos_evento = evento.get("recursos", {})
        categorias = self.restricciones.get("corequisitos", {}).get("categorias", {})

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

        sala = evento.get("sala")
        recursos_evento = evento.get("recursos", {})

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
        
        errores = []

        tipo = evento.get("tipo")
        recursos_evento = evento.get("recursos", {})

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
        prohibidos_en_sala = eventos_prohibidos.get(evento.get("sala"), [])

        if evento.get("tipo") in prohibidos_en_sala:
            errores.append(
                f"El evento '{evento['tipo']}' no se puede realizar en la sala '{evento['sala']}'."
            )

        return errores

    


    # personal listo
    def _validar_personal_obligatorio(self, evento):
        
        # Valida que el evento incluya el personal obligatorio según la sala en la que se realiza.
        
        errores = []

        sala = evento.get("sala")
        recursos = evento.get("recursos", {})

        reglas_personal = self.restricciones.get("personal_obligatorio", {})

        if sala not in reglas_personal:
            return errores

        personal_requerido = reglas_personal[sala]

        for rol, minimo in personal_requerido.items():
            usados = recursos.get(rol, 0)
            if usados < minimo:
                errores.append(
                    f"En la sala {sala} se requiere al menos "
                    f"{minimo} '{rol}' (se indicaron {usados})"
                )

        return errores


    # disp recursos
    def _validar_disponibilidad_recursos(self, evento):
        
        # Valida que el evento pueda usar los recursos solicitados, considerando los recursos ya ocupados por otros eventos el mismo día.
        
        errores = []

        if not evento.get("recursos"):
            errores.append("El evento debe tener recursos especificados")
            return errores

        fecha_evento = evento.get("fecha").date()
        recursos_solicitados = evento.get("recursos", {})

        # Contar recursos ocupados por otros eventos el mismo día
        recursos_ocupados = {}

        for e in self.eventos:
            if e.get("fecha").date() != fecha_evento:
                continue

            for recurso, cantidad in e.get("recursos", {}).items():
                recursos_ocupados[recurso] = recursos_ocupados.get(recurso, 0) + cantidad

        # Verificar disponibilidad real
        for recursos_categoria in self.recursos.values():
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

    def sugerir_proxima_fecha_libre(self, sala, fecha_inicial, evento):
        fecha = fecha_inicial

        while True:
            # 1. Verificar si la sala está libre ese día
            sala_ocupada = any(
                e["sala"] == sala and e["fecha"].date() == fecha
                for e in self.eventos
            )

            if sala_ocupada:
                fecha += timedelta(days=1)
                continue

            # 2. Calcular recursos ya ocupados ese día
            recursos_ocupados = {}

            for e in self.eventos:
                if e["fecha"].date() == fecha:
                    for recurso, cantidad in e["recursos"].items():
                        recursos_ocupados[recurso] = recursos_ocupados.get(recurso, 0) + cantidad

            # 3. Verificar si hay recursos suficientes para el nuevo evento
            recursos_solicitados = evento["recursos"]

            recursos_ok = True
            for recursos_categoria in self.recursos.values():
                if not isinstance(recursos_categoria, dict):
                    continue

                for recurso, total_disponible in recursos_categoria.items():
                    usado = recursos_ocupados.get(recurso, 0)
                    solicitado = recursos_solicitados.get(recurso, 0)

                    if solicitado > (total_disponible - usado):
                        recursos_ok = False
                        break

                if not recursos_ok:
                    break

            # 4. Si todo está bien, devolver la fecha
            if recursos_ok:
                return fecha

            # 5. Si no, probar el siguiente día
            fecha += timedelta(days=1)




    def mostrar_agenda(self):
        
        # Devuelve la lista completa de eventos registrados, con toda su información.
        # Ordena por fecha para que se vea la agenda cronológicamente.
        
        if not self.eventos:
            return "No hay eventos programados."

        # Ordenamos los eventos por fecha
        eventos_ordenados = sorted(self.eventos, key=lambda e: e["fecha"])

        agenda = []
        for e in eventos_ordenados:
            tipo = e.get("tipo", "Desconocido")
            sala = e.get("sala", "No asignada")
            fecha = e.get("fecha", "No asignada")
            recursos = e.get("recursos", {})
            agenda.append(
                f"Evento: {tipo}\n"
                f"  Sala: {sala}\n"
                f"  Fecha: {fecha}\n"
                f"  Recursos: {recursos}\n"
            )

        return "\n".join(agenda)



    def guardar_eventos_json(self, archivo="data/eventos.json"):
        
        # Guarda todos los eventos actuales en un archivo JSON.
        # Cada fecha se convierte a ISO string para poder guardarla.
        
        eventos_a_guardar = []
        for e in self.eventos:
            evento_copia = e.copy()
            if isinstance(evento_copia.get("fecha"), datetime):
                evento_copia["fecha"] = evento_copia["fecha"].isoformat()
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
                if isinstance(e.get("fecha"), str):
                    e["fecha"] = datetime.fromisoformat(e["fecha"])
        except FileNotFoundError:
            self.eventos = []


    def cargar_recursos_json(self, archivo="data/recursos.json"):
        
        # Carga los recursos disponibles desde un archivo JSON.
        
        with open(archivo, "r", encoding="utf-8") as f:
            self.recursos = json.load(f)

    def cargar_restricciones_json(self, archivo="data/restricciones.json"):
        
        # Carga las restricciones desde un archivo JSON.
        
        with open(archivo, "r", encoding="utf-8") as f:
            self.restricciones = json.load(f)
