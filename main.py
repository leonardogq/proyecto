import streamlit as st
from planificador import PlanificadorEventos
import json
from datetime import datetime



# Inicializar planificador y cargar eventos

planificador = PlanificadorEventos()
planificador.cargar_eventos_json()
planificador.cargar_recursos_json()
planificador.cargar_restricciones_json()


# Página principal

st.title(" Planificador de Eventos Musicales")

# Mostrar recursos y restricciones (desplegables)
with st.expander("Recursos disponibles", expanded=False):
    with open("data/recursos.json", "r", encoding="utf-8") as f:
        recursos = json.load(f)
    st.json(recursos)


# Opciones principales

opcion = st.radio(
    "Seleccione una opción",
    ["Agregar evento", "Eliminar evento", "Ver agenda"]
)


# Opción: Ver Agenda

if opcion == "Ver agenda":
    st.header(" Agenda de Eventos")
    if not planificador.eventos:
        st.info("No hay eventos registrados.")
    else:
        for e in planificador.eventos:
            st.markdown(f"**Tipo:** {e.get('tipo', 'Desconocido')}")
            st.markdown(f"**Sala:** {e.get('sala', 'Desconocida')}")
            st.markdown(f"**Fecha:** {e.get('fecha').strftime('%Y-%m-%d')}")
            st.markdown("**Recursos asignados:**")
            for rec, cant in e.get("recursos", {}).items():
                st.markdown(f"- {rec}: {cant}")
            st.markdown("---")

# Opción: Eliminar Evento

elif opcion == "Eliminar evento":
    st.header(" Eliminar Evento")

    if not planificador.eventos:
        st.info("No hay eventos planificados.")
    else:
        # Confirmación simple para limpiar agenda
        if "confirmar_borrado" not in st.session_state:
            st.session_state.confirmar_borrado = False

        if not st.session_state.confirmar_borrado:
            if st.button("Eliminar todos"):
                st.session_state.confirmar_borrado = True
                st.rerun()
        else:
            st.warning("¿Estás seguro de que quieres eliminar TODOS los eventos?")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("Sí, eliminar todo"):
                    cantidad = len(planificador.eventos)
                    planificador.eventos = []

                    with open("data/eventos.json", "w", encoding="utf-8") as f:
                        json.dump([], f, ensure_ascii=False, indent=2)

                    st.success(f"Se eliminaron {cantidad} eventos.")
                    st.session_state.confirmar_borrado = False
                    st.rerun()

            with col2:
                if st.button("Cancelar"):
                    st.session_state.confirmar_borrado = False
                    st.rerun()

        st.markdown("---")

        # Eliminar un solo evento
        opciones = [
            f"{e['tipo']} | {e['sala']} | {e['fecha'].strftime('%Y-%m-%d')}"
            for e in planificador.eventos
        ]

        seleccion = st.selectbox("Seleccione el evento a eliminar", opciones)
        indice = opciones.index(seleccion)
        evento_seleccionado = planificador.eventos[indice]

        if st.button("Eliminar"):
            exito, mensaje = planificador.eliminar_evento(
                evento_seleccionado["tipo"],
                evento_seleccionado["sala"],
                evento_seleccionado["fecha"].date()
            )

            if exito:
                st.success(mensaje)

                with open("data/eventos.json", "w", encoding="utf-8") as f:
                    json.dump(
                        [
                            {**ev, "fecha": ev["fecha"].date().isoformat()}
                            for ev in planificador.eventos
                        ],
                        f,
                        ensure_ascii=False,
                        indent=2
                    )

                st.rerun()
            else:
                st.error(mensaje)




# Opción: Agregar Evento

elif opcion == "Agregar evento":
    st.header(" Agregar Evento")


    # Inputs básicos
    tipo = st.selectbox("Tipo de evento", list(planificador.recursos.get("eventos", {})))
    sala = st.selectbox("Sala", list(planificador.recursos.get("salas", {}).keys()))
    fecha = st.date_input("Fecha del evento")

    # Recursos dinámicos 
    recursos_asignados = {}
    st.markdown("**Recursos para asignar**")

    for categoria, recursos_categoria in planificador.recursos.items():
        if isinstance(recursos_categoria, dict) and categoria != "salas":
            st.markdown(f"*{categoria.capitalize()}*")
            for rec in recursos_categoria.keys():
                cant = st.number_input(
                    f"{rec}",
                    min_value=0,
                    value=0,
                    step=1,
                    key=f"{categoria}_{rec}"
                )
                if cant > 0:
                    recursos_asignados[rec] = cant

    # Botón para agregar
    if st.button("Agregar Evento"):
        if not tipo or not sala or not fecha:
            st.warning("Complete todos los campos obligatorios.")
        else:
            # Construir objeto evento
            evento_nuevo = {
                "tipo": tipo,
                "sala": sala,
                "fecha": datetime.combine(fecha, datetime.min.time()),
                "recursos": recursos_asignados
            }

            # Intentar agregar evento
            exito, errores = planificador.agregar_evento(evento_nuevo)

            if exito:
                st.success("Evento agregado correctamente!")

                # Guardar en JSON
                with open("data/eventos.json", "w", encoding="utf-8") as f:
                    json.dump(
                        [
                            {**ev, "fecha": ev["fecha"].date().isoformat()}
                            for ev in planificador.eventos
                        ],
                        f,
                        ensure_ascii=False,
                        indent=2
                    )
                st.rerun()
            else:
                st.error("No se pudo agregar el evento. Corrija los siguientes errores:")
                for err in errores:
                    st.markdown(f"- {err}")
