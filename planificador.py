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

        errores = []

        # 1. TODAS las validaciones de evento


        errores += self._validar_fechas(evento)
        errores += self._validar_disponibilidad_recursos(evento)

        if errores:
            return False, errores
        

        errores += self.validar_corequisitos_por_recurso(evento)
        errores += self.validar_corequisitos_por_categoria(evento)
        errores += self.validar_exclusiones_por_sala(evento)
        errores += self.validar_exclusiones_por_evento(evento)
        errores += self.validar_evento_por_sala(evento)
        errores += self._validar_reglas_evento(evento)
        errores += self._validar_personal_obligatorio(evento)
        


        if errores:
            return False, errores

        # aquí se valida sala y sugerencia
        errores += self._validar_disponibilidad_sala(evento)

        if errores:
            return False, errores
        
        # si hay recursos ocupados ese dia, sugiere fecha
        errores += self._validar_recursos_fecha(evento)

        if errores:
            return False, errores

        # 3. Guardar evento
        self.eventos.append(evento)
        self.eventos.sort(key=lambda e: e["fecha"])
        self.guardar_eventos_json()
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
        # no pueden haber eventos en fechas pasadas
        
        errores = []

        fecha = evento.get("fecha")
       

        if not isinstance(fecha, datetime):
            errores.append("La fecha debe ser un objeto datetime")
            return errores

        fecha_evento = fecha.date()
        fecha_hoy = date.today()
        fecha_maxima = fecha_hoy + timedelta(days=365)

        # No permitir fechas pasadas
        if fecha_evento < fecha_hoy:
            errores.append("No se pueden crear eventos en fechas anteriores a hoy")
        
        # limite de un año de anticipación
        if fecha_evento > fecha_maxima:
            errores.append("No se pueden crear eventos con más de un año de anticipación")


        return errores


    # reglas listo
    def _validar_reglas_evento(self, evento):
        errores = []

        tipo = evento.get("tipo")
        recursos = evento.get("recursos", {})

        reglas_evento = self.restricciones.get("reglas_evento", {})

        if tipo not in reglas_evento:
            errores.append(f"No existe el evento '{tipo}'")
            return errores

        reglas = reglas_evento[tipo]

        # Reglas de cantidad mínima por recurso
        for recurso, minimo in reglas.items():
            if not isinstance(minimo, int) or isinstance(minimo, bool):
                continue

            usados = recursos.get(recurso.capitalize(), 0)

            if usados < minimo:
                errores.append(
                    f"El evento '{tipo}' requiere al menos "
                    f"{minimo} {recurso} (se indicaron {usados})"
                )

        # Reglas lógicas adicionales
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
                        f"Si hay {cantidad_recurso} '{recurso}' debe haber {cantidad_recurso} '{req}' (se indicaron {cantidad_req})."
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
                    f"Se requieren {total_requerido} '{req}', pero solo se indicaron {total_en_evento}."
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

        recursos_solicitados = evento.get("recursos", {})

        for categoria in self.recursos.values():
            if not isinstance(categoria, dict):
                continue

            for recurso, total_disponible in categoria.items():
                solicitado = recursos_solicitados.get(recurso, 0)

                if solicitado > total_disponible:
                    errores.append(
                        f"Se disponen de {total_disponible} '{recurso}', "
                        f"pero se solicitaron {solicitado}."
                    )

        return errores








    def _validar_disponibilidad_sala(self, evento):
        errores = []

        sala = evento["sala"]
        fecha_evento = evento["fecha"].date()

        for e in self.eventos:
            if e["sala"] == sala and e["fecha"].date() == fecha_evento:
                sugerencia = self.sugerir_proxima_fecha_libre(sala, fecha_evento, evento)

                
                errores.append(
                    f"Ya existe un evento en la sala {sala} para el día {fecha_evento}. "
                    f"Sugerencia: próxima fecha con recursos libres {sugerencia}"
                    )
                break

        return errores


        



    def _validar_recursos_fecha(self, evento):
        errores = []

        fecha_evento = evento.get("fecha").date()
        recursos_solicitados = evento.get("recursos", {})

        recursos_ocupados = {}

        for e in self.eventos:
            if e.get("fecha").date() != fecha_evento:
                continue

            for recurso, cantidad in e.get("recursos", {}).items():
                recursos_ocupados[recurso] = recursos_ocupados.get(recurso, 0) + cantidad

        conflictos = []
        

        for categoria in self.recursos.values():
            if not isinstance(categoria, dict):
                continue

            for recurso, total_disponible in categoria.items():
                solicitado = recursos_solicitados.get(recurso, 0)
                usado = recursos_ocupados.get(recurso, 0)

                disponible_real = total_disponible - usado

                if solicitado > disponible_real:
                    conflictos.append(f"{recurso}:{disponible_real}")

        if conflictos:
            sugerencia = self.sugerir_proxima_fecha_libre(
                evento["sala"], fecha_evento, evento
            )

        

            errores.append(
                f"No hay suficientes recursos disponibles ese día: "
                f"{', '.join(conflictos)}. "
                f"Sugerencia: próxima fecha libre {sugerencia}."
            )

        return errores






    

    # otros

    def sugerir_proxima_fecha_libre(self, sala, fecha_inicial, evento):

        fecha = fecha_inicial
        recursos_solicitados = evento.get("recursos", {})

        MAX_DIAS = 365  # límite de búsqueda: 1 año

        for _ in range(MAX_DIAS):
            # Protección contra overflow
            try:
                fecha_actual = fecha
            except OverflowError:
                return None

            # 1. Verificar si la sala está libre ese día
            ocupada = any(
                e["sala"] == sala and e["fecha"].date() == fecha_actual
                for e in self.eventos
            )
            if ocupada:
                fecha = fecha_actual + timedelta(days=1)
                continue

            # 2. Verificar disponibilidad de recursos ese día
            recursos_ocupados = {}
            for e in self.eventos:
                if e["fecha"].date() != fecha_actual:
                    continue
                for recurso, cantidad in e["recursos"].items():
                    recursos_ocupados[recurso] = recursos_ocupados.get(recurso, 0) + cantidad

            recursos_ok = True
            for categoria in self.recursos.values():
                if not isinstance(categoria, dict):
                    continue
                for recurso, total_disponible in categoria.items():
                    usado = recursos_ocupados.get(recurso, 0)
                    solicitado = recursos_solicitados.get(recurso, 0)
                    if solicitado > (total_disponible - usado):
                        recursos_ok = False
                        break
                if not recursos_ok:
                    break

            if recursos_ok:
                return fecha_actual

            fecha = fecha_actual + timedelta(days=1)

        return None  # No existe fecha válida en el rango buscado




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
