# Reporte del Proyecto: Planificador de Eventos para un Estudio de Grabación

## Introducción

La organización de actividades dentro de un estudio de grabación requiere coordinar una gran cantidad de recursos limitados. Equipos de audio, instrumentos musicales, salas especializadas y personal técnico deben estar disponibles en el momento adecuado para garantizar el correcto desarrollo de cada evento. A medida que aumenta la cantidad de actividades programadas, la gestión manual se vuelve más compleja y aumenta la probabilidad de cometer errores.

Con el objetivo de facilitar este proceso se desarrolló un sistema de planificación de eventos para estudios de grabación. La aplicación permite registrar eventos, verificar la disponibilidad de recursos, aplicar restricciones propias del dominio y mantener toda la información almacenada de forma persistente. El sistema fue implementado en Python y cuenta con una interfaz gráfica desarrollada mediante Streamlit para facilitar su utilización.

La idea principal del proyecto es simular un escenario real donde existen recursos compartidos y múltiples restricciones que deben cumplirse simultáneamente. En lugar de limitarse a almacenar información, la aplicación realiza validaciones automáticas que ayudan a evitar conflictos y errores durante la planificación.

## Descripción del problema

Los estudios de grabación suelen utilizar recursos costosos y limitados. Micrófonos, mezcladores, computadoras, instrumentos musicales y personal especializado deben distribuirse adecuadamente entre los distintos eventos programados.

En una planificación realizada manualmente pueden surgir varios problemas. Dos eventos pueden intentar utilizar el mismo recurso al mismo tiempo, una sala puede ser asignada a una actividad para la que no está preparada o puede faltar personal necesario para llevar a cabo una grabación. También es posible que un evento solicite un recurso sin incluir otros elementos indispensables para utilizarlo correctamente.

Por ejemplo, disponer de un micrófono sin soporte o sin audífonos puede impedir el desarrollo normal de una sesión de grabación. Del mismo modo, determinados tipos de eventos requieren instrumentos específicos o no pueden realizarse en ciertas salas debido a restricciones operativas.

El objetivo del sistema es detectar automáticamente estas situaciones antes de que un evento sea aceptado, reduciendo la posibilidad de errores y facilitando la gestión del estudio.

## Objetivos

El objetivo principal consiste en desarrollar una herramienta capaz de administrar la planificación de eventos dentro de un estudio de grabación, garantizando el cumplimiento de las restricciones establecidas y el uso correcto de los recursos disponibles.

Entre los objetivos específicos se encuentran:

* Registrar eventos de diferentes tipos.
* Mantener un inventario de recursos disponibles.
* Controlar la disponibilidad de salas.
* Gestionar el uso del personal técnico.
* Aplicar restricciones definidas por el dominio.
* Evitar conflictos entre eventos.
* Sugerir alternativas cuando una fecha no se encuentra disponible.
* Almacenar la información de manera persistente.

## Análisis del dominio

El dominio seleccionado fue un estudio de grabación profesional. Se trata de un entorno interesante porque involucra distintos tipos de recursos con relaciones entre sí y restricciones que no siempre son evidentes.

Dentro del estudio existen recursos físicos, recursos humanos y espacios de trabajo. Cada uno de ellos posee características particulares que deben tenerse en cuenta durante la planificación.

Los recursos físicos incluyen equipos de audio, computadoras, instrumentos musicales y accesorios necesarios para las grabaciones. Los recursos humanos están representados por técnicos de audio y productores musicales. Finalmente, las salas constituyen espacios limitados donde se desarrollan las actividades.

La combinación de estos elementos permite construir un problema suficientemente complejo como para requerir validaciones automáticas y reglas de negocio específicas.

## Recursos gestionados por el sistema

El sistema trabaja con un conjunto de recursos definidos en archivos JSON. Entre ellos se encuentran micrófonos, soportes, audífonos, mezcladores, computadoras, ecualizadores, cables y teleprompters.

También se incluyen instrumentos musicales como guitarras, pianolas, baterías y bajos.

Cada recurso posee una cantidad determinada disponible en el estudio. Cuando un evento solicita recursos, el sistema verifica que existan suficientes unidades libres considerando también otros eventos ya programados.

Esta verificación resulta especialmente importante porque los recursos pueden ser compartidos entre múltiples actividades y la disponibilidad real depende de la planificación existente.

## Salas disponibles

El estudio cuenta con dos salas principales: una sala pequeña y una sala grande.

Cada sala posee características diferentes y, por tanto, restricciones específicas. No todas las actividades pueden desarrollarse en cualquier espacio. Esta decisión busca representar situaciones reales donde determinadas instalaciones poseen limitaciones físicas o técnicas.

Las salas forman parte fundamental del proceso de validación, ya que un evento no puede programarse en un espacio que incumpla las condiciones establecidas para su funcionamiento.

## Tipos de eventos

La aplicación permite gestionar varios tipos de eventos relacionados con la producción de contenido audiovisual y musical.

Entre ellos se encuentran:

* Grabación de podcast.
* Grabación de doblaje.
* Grabación de canción.
* Grabación instrumental.

Cada tipo de evento posee requisitos distintos y puede estar sujeto a restricciones particulares. Esto permite que el sistema represente escenarios variados y obliga a realizar validaciones específicas antes de aceptar una reserva.

## Diseño general de la solución

La lógica principal del proyecto se encuentra concentrada en la clase `PlanificadorEventos`. Esta clase actúa como núcleo del sistema y se encarga de coordinar las distintas operaciones necesarias para gestionar los eventos.

Sus responsabilidades incluyen:

* Cargar datos desde archivos JSON.
* Guardar modificaciones realizadas por el usuario.
* Agregar nuevos eventos.
* Eliminar eventos existentes.
* Verificar disponibilidad de recursos.
* Aplicar restricciones.
* Sugerir fechas alternativas.

Centralizar estas operaciones en una única clase permitió simplificar la organización del código y mantener separada la lógica de negocio de la interfaz gráfica.

## Persistencia de datos

La información utilizada por la aplicación se almacena mediante archivos JSON.

Se decidió utilizar este formato debido a su simplicidad, facilidad de lectura y compatibilidad con Python. Además, permite modificar los datos sin necesidad de utilizar sistemas de bases de datos más complejos.

El sistema emplea distintos archivos para almacenar recursos, restricciones y eventos programados.

Esta separación facilita el mantenimiento de la aplicación y permite actualizar determinadas configuraciones sin necesidad de modificar el código fuente.

## Sistema de validación

Uno de los aspectos más importantes del proyecto es el conjunto de validaciones implementadas para garantizar la consistencia de los datos.

Antes de registrar un evento, el sistema ejecuta una serie de verificaciones destinadas a comprobar que todas las condiciones necesarias se encuentren satisfechas.

Estas validaciones representan la mayor parte de la lógica del proyecto y son las que aportan valor al sistema más allá del simple almacenamiento de información.

## Validación de disponibilidad de recursos

Cuando se intenta registrar un evento, la aplicación calcula la cantidad de recursos ya ocupados por otros eventos.

Posteriormente compara esos valores con el inventario disponible y determina si existen suficientes unidades para satisfacer la nueva solicitud.

Gracias a este procedimiento se evita que varios eventos utilicen simultáneamente recursos que no existen en cantidades suficientes.

## Corequisitos entre recursos

Durante el desarrollo se incorporó un sistema de corequisitos para representar dependencias entre recursos.

Por ejemplo, un micrófono requiere la existencia de un soporte y de audífonos asociados. De forma similar, numerosos equipos e instrumentos necesitan cables para poder utilizarse correctamente.

La implementación de estas reglas evita configuraciones inconsistentes y representa de forma más realista el funcionamiento de un estudio de grabación.

Este fue uno de los aspectos más interesantes del proyecto porque obligó a considerar no solo la existencia de recursos individuales, sino también las relaciones entre ellos.

## Restricciones por sala

Las salas poseen limitaciones específicas definidas mediante reglas almacenadas en los archivos de configuración.

La sala pequeña no admite instrumentos musicales ni productor musical. Además, ciertos tipos de eventos no pueden desarrollarse en ella.

Por otro lado, la sala grande posee restricciones diferentes relacionadas con determinados equipos y actividades.

Estas reglas son verificadas automáticamente antes de aceptar una reserva.

## Restricciones por evento

Algunos eventos poseen condiciones especiales que deben cumplirse obligatoriamente.

La grabación instrumental constituye el ejemplo más representativo. Este tipo de actividad no puede incluir micrófonos y requiere la presencia de instrumentos musicales.

Estas validaciones permiten adaptar el comportamiento del sistema a las características particulares de cada actividad.

## Validación del personal

Además de los recursos materiales, el sistema controla la disponibilidad de personal.

Dependiendo de la sala utilizada, se exige la presencia de técnicos de audio y productores musicales en cantidades mínimas determinadas.

Esta funcionalidad contribuye a representar de manera más realista la operación de un estudio profesional y evita programaciones inviables.

## Sugerencia de fechas alternativas

Otra característica implementada consiste en la búsqueda de fechas disponibles cuando una solicitud no puede ser aceptada.

En lugar de limitarse a informar que existe un conflicto, el sistema intenta encontrar una alternativa válida para facilitar la planificación.

Aunque se trata de una funcionalidad relativamente sencilla, mejora la experiencia de uso y aporta un componente más inteligente a la aplicación.

## Interfaz gráfica

Para la construcción de la interfaz se utilizó Streamlit.

Esta herramienta permite desarrollar aplicaciones web interactivas utilizando únicamente Python, sin necesidad de conocimientos avanzados de desarrollo web.

La interfaz facilita la interacción con el sistema y permite realizar operaciones como registrar eventos, consultar información y visualizar resultados de manera intuitiva.

La elección de Streamlit permitió concentrar los esfuerzos en la lógica de negocio sin dedicar demasiado tiempo al diseño de una interfaz compleja.

## Cómo se utiliza el programa

La aplicación se ejecuta mediante Streamlit utilizando el siguiente comando:

streamlit run main.py


Una vez iniciada la aplicación, el usuario accede a una interfaz gráfica desde el navegador donde puede gestionar los eventos del estudio de grabación.

El uso básico del sistema consiste en seleccionar el tipo de evento que se desea registrar, elegir la sala correspondiente, especificar la fecha y los recursos necesarios. Antes de almacenar la información, el sistema realiza automáticamente todas las validaciones definidas para garantizar que la planificación sea válida.

### Ejemplo 1: Registro exitoso de un evento

Supóngase que se desea programar una grabación de podcast en una fecha donde existen recursos disponibles.

El usuario selecciona:

* Tipo de evento: Grabación de podcast.
* Sala: Sala Pequeña.
* Fecha: 2026-07-15.
* Recursos:

  * 2 micrófonos.
  * 2 soportes.
  * 2 audífonos.
  * 4 cables.
* Personal:

  * 1 técnico de audio.

Al cumplirse todas las restricciones y existir recursos suficientes, el sistema registra correctamente el evento y lo almacena en el archivo de eventos.

### Ejemplo 2: Recursos insuficientes

Supóngase que ya existen eventos programados que utilizan la mayoría de los micrófonos disponibles.

Si el usuario intenta registrar un nuevo evento solicitando más micrófonos de los que quedan libres, el sistema detecta la situación y muestra un mensaje similar a:

No hay suficientes recursos disponibles ese día: Micrófonos:3, Soportes de micrófono:3. Sugerencia: próxima fecha libre 2026-06-26.



### Ejemplo 3: Incumplimiento de corequisitos

Supóngase que se solicitan tres micrófonos pero únicamente un soporte.

El sistema verifica las relaciones definidas entre recursos y genera un error indicando que no se cumplen los requisitos mínimos y muestra el mensaje:

Si hay 3 'Micrófonos' debe haber 3 'Soportes de micrófono' (se indicaron 1)


### Ejemplo 4: Restricción por sala

Si se intenta programar una grabación instrumental en la Sala Pequeña, el sistema rechazará la solicitud debido a las restricciones definidas para dicha sala y muestra el mensaje:

El evento 'Grabación de instrumental' no se puede realizar en la sala 'Pequeña'.

### Ejemplo 5: Personal obligatorio

La Sala Grande requiere la participación de un técnico de audio y un productor musical.

Si alguno de estos recursos humanos no se encuentra disponible o no ha sido asignado al evento, el sistema informará el problema y evitará que la reserva sea registrada mostrando el mensaje:

En la sala Grande se requiere al menos 1 'Técnicos de audio' (se indicaron 0)
o
En la sala Grande se requiere al menos 1 'Productor musical' (se indicaron 0)

Estos ejemplos muestran cómo el programa ayuda a detectar conflictos antes de que ocurran, permitiendo una planificación más segura y consistente de las actividades del estudio.


## Problemas encontrados durante el desarrollo

Durante el desarrollo surgieron diversas dificultades relacionadas principalmente con la validación de restricciones.

Existe validar_exclusiones_por_evento pero ahora mismo no hay ninguna exclusión por evento.

El sistema fue diseñado para soportarlas. Durante el desarrollo existía una restricción sobre micrófonos en grabaciones instrumentales, pero posteriormente se eliminó al considerar que no representaba correctamente el dominio. Sin embargo, la funcionalidad se mantuvo porque puede ser útil para futuras extensiones del sistema.

Uno de los desafíos más importantes fue implementar correctamente los corequisitos entre recursos. Inicialmente se comprobaba únicamente la existencia de determinados elementos, pero posteriormente fue necesario considerar también las cantidades involucradas.

Otro problema consistió en gestionar la disponibilidad de recursos cuando varios eventos compartían fechas o utilizaban elementos similares. Esto obligó a realizar cálculos adicionales para determinar la cantidad realmente disponible en cada momento.

Durante el desarrollo se decidió almacenar las restricciones en archivos JSON en lugar de codificarlas directamente en el programa. Gracias a esto, reglas como exclusiones por sala, personal obligatorio o corequisitos pueden modificarse sin cambiar el código fuente. Esta separación entre datos y lógica facilitó el mantenimiento y permitió adaptar el comportamiento del sistema de forma más sencilla.

Otro aspecto que requirió especial atención fue la organización del proceso de validación. A medida que aumentaba la cantidad de restricciones implementadas, surgió el problema de que un mismo evento podía generar numerosos mensajes de error simultáneamente, muchos de ellos poco útiles para el usuario, incluso mensajes sin sentido como que se requieren cientos de cables, cuando solo hay 25.

Por ejemplo, si un evento solicitaba una cantidad imposible de recursos o presentaba problemas básicos de disponibilidad, no tenía sentido continuar evaluando reglas más específicas relacionadas con corequisitos, restricciones por sala o requisitos de personal. Mostrar todos esos errores al mismo tiempo podía resultar confuso y dificultar la identificación del problema principal.

Para resolver esta situación, las validaciones fueron organizadas en etapas. Primero se verifican aspectos fundamentales como las fechas y la disponibilidad general de recursos. Solo si estas comprobaciones son superadas se ejecutan las validaciones relacionadas con corequisitos, restricciones de salas y requisitos de personal. Finalmente se realizan las comprobaciones asociadas a la disponibilidad de la sala y a posibles conflictos con eventos existentes.

Este enfoque permite detener el proceso tan pronto como se detecta un problema crítico, evitando mensajes innecesarios o incoherentes y proporcionando información más clara al usuario. Además, mejora la mantenibilidad del código al separar las distintas responsabilidades de validación en bloques bien definidos.

## Posibles mejoras futuras

Aunque el sistema cumple los objetivos planteados inicialmente, existen múltiples posibilidades de mejora.

Una opción sería incorporar autenticación de usuarios para diferenciar administradores y operadores.

También podría añadirse una base de datos relacional que permita gestionar mayores volúmenes de información.

Otra mejora interesante consistiría en implementar un calendario visual donde los eventos pudieran observarse gráficamente según su fecha y sala asignada.

Actualmente los eventos se gestionan a nivel de fecha. Como mejora futura, podría incorporarse un sistema de horarios mediante horas de inicio y fin, permitiendo programar múltiples eventos en una misma sala durante un mismo día siempre que no exista solapamiento temporal. Esto haría el modelo más realista y flexible para escenarios de planificación complejos.

## Conclusiones

El proyecto permitió aplicar conceptos fundamentales de programación orientada a objetos, persistencia de datos, validación de reglas de negocio y desarrollo de interfaces gráficas.

La solución obtenida es capaz de gestionar eventos dentro de un estudio de grabación considerando recursos limitados, restricciones específicas y dependencias entre elementos. Gracias a las validaciones implementadas se reducen los errores de planificación y se garantiza una utilización más consistente de los recursos disponibles.

Además de resolver el problema planteado, el desarrollo del sistema permitió comprender la importancia de modelar adecuadamente un dominio real y de diseñar estructuras de datos capaces de representar sus reglas de funcionamiento. El resultado final es una herramienta funcional, extensible y suficientemente compleja para demostrar los conocimientos adquiridos durante el curso.
