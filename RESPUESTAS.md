# Respuestas al reto — Sistema de Vacaciones

### 1. ¿Usaste IA para construir la solución? ¿Cuál(es) y para qué exactamente?

Sí, usé Claude y Cursor como apoyo, pero el proyecto lo llevé yo de principio a fin. Los usé sobre todo para acelerar la parte de escritura: plantear la estructura inicial, redactar los endpoints, y hacer las ediciones dentro del código una vez yo ya tenía claro qué necesitaba.

Ahora, en la práctica, ninguna de las dos herramientas entendía todo el contexto del proyecto de una sola vez. Varias veces tuve que corregirles el rumbo porque proponían algo que sonaba bien en teoría pero no encajaba con lo que yo ya había construido, o directamente se les olvidaba algún detalle que yo les había dado antes en la conversación. Así que terminé usándolas más como una herramienta de redacción rápida que como alguien en quien delegar decisiones. Las decisiones de qué construir, qué validar, y cómo reaccionar cuando algo fallaba, las tomé yo.

---

### 2. Cuéntanos una vez que la IA te dio algo mal o incompleto: ¿cómo te diste cuenta y qué hiciste?

Hubo varias, la verdad. La más clara fue con el control de saldo de días. Cuando ya tenía el flujo de aprobación funcionando, noté, revisando yo mismo el enunciado del reto punto por punto, que en ningún lado se estaba llevando la cuenta de cuántos días le quedaban a cada empleado. No fue algo que la IA me señalara, lo detecté yo comparando lo que tenía contra lo que realmente se pedía, y ahí fue cuando le pedí ayuda para implementarlo.

También durante el despliegue tuve que corregirla varias veces. En un momento me sugirió una forma de conectarme directamente a la base de datos en producción que simplemente no funcionó por un problema de red de mi lado, y tuve que insistir para que buscáramos una alternativa distinta. En otro momento, después de pedirle una corrección, el archivo seguía sin actualizarse en mi proyecto porque yo no había guardado el archivo en el editor, un detalle que la IA no podía ver por sí sola y que solo detectamos al revisar juntos por qué el cambio "no aparecía". En resumen, la IA proponía soluciones razonables, pero varias veces esas soluciones fallaban en la práctica o no tenían en cuenta detalles de mi entorno, y me tocó a mí notar el problema, señalarlo y buscar junto con ella un camino distinto.

---

### 3. ¿Por qué elegiste esta arquitectura y este stack? ¿Qué alternativa descartaste y por qué?

Elegí FastAPI para el backend porque ya lo había usado antes en proyectos académicos y porque su documentación automática (la interfaz de `/docs`) me permitía probar cada endpoint sin necesidad de herramientas externas como Postman, algo que terminó siendo clave para depurar problemas durante el despliegue.

Para la base de datos elegí PostgreSQL en vez de algo más simple como SQLite. Lo pensé bastante: SQLite me hubiera ahorrado tener que instalar y configurar un servidor de base de datos, pero el reto pedía algo cercano a un entorno de producción real, y Postgres además tiene soporte gratuito en el mismo proveedor donde desplegué el backend, así que tenía sentido usarlo desde el principio en vez de migrar después.

Para el frontend decidí no usar ningún framework, nada de React o Angular, y quedarme con HTML, CSS y JavaScript puro. El flujo que pedía el reto no es complejo en términos de interfaz, es esencialmente mostrar tarjetas de solicitudes y botones de decisión, así que un framework hubiera sido más tiempo de configuración sin ganancia real, y prefería invertir ese tiempo en que la lógica de negocio quedara sólida.

---

### 4. ¿Cómo garantizas que el control de días y los estados del flujo sean siempre correctos, sin importar el orden en que ocurran las acciones?

Esto lo resolví con dos ideas simples pero que se sostienen entre sí.

**Sobre los estados:** cada solicitud solo puede estar en un estado a la vez, y cada acción revisa primero en qué estado está antes de hacer cualquier cambio. Por ejemplo, el jefe solo puede actuar sobre una solicitud que esté "pendiente de jefe". Si ya la procesó antes, o si todavía no le corresponde a él sino a RRHH, el sistema lo rechaza con un mensaje claro en vez de dejar que ocurra dos veces o fuera de orden.

**Sobre el saldo de días:** decidí que el descuento real de días solo pasa en un único punto del flujo, cuando RRHH confirma. Y justo antes de descontar, se vuelve a comprobar que el empleado sí tenga saldo suficiente en ese momento exacto, no se confía en un cálculo que se hizo antes, porque el saldo pudo haber cambiado si RRHH ya confirmó otra solicitud del mismo empleado mientras tanto. Esa doble validación, una al crear la solicitud y otra al confirmarla, es lo que evita que, sin importar en qué orden RRHH procese varias solicitudes pendientes, el saldo termine en negativo.

También agregué una validación de fechas cruzadas: un empleado no puede tener dos solicitudes activas que se traslapen en el tiempo, lo cual evita otro tipo de inconsistencia que podría aparecer si las solicitudes se procesan en distinto orden.

---

### 5. ¿Le pusiste IA al producto? Si sí, ¿dónde, por qué ahí y cómo evitas que se equivoque?

Sí, integré un modelo de lenguaje, a través de Groq, en dos puntos muy concretos del flujo, elegidos porque son justo los momentos donde una persona tiene que tomar una decisión y un poco de contexto adicional ayuda.

**Para el jefe:** puede pedir un resumen automático de la solicitud antes de aprobarla o rechazarla. Cuántos días pide el empleado, cuántos le quedan disponibles, y cuántas solicitudes ha hecho en el año. La idea es ahorrarle el trabajo de ir a buscar ese contexto manualmente.

**Para RRHH:** puede pedir una sugerencia de comentario profesional para acompañar su confirmación o rechazo, que después puede editar libremente antes de enviarla.

En ambos casos, la IA nunca decide nada por sí sola, solo informa o sugiere texto. Los cálculos que sí importan de verdad, el saldo de días, los cambios de estado, si algo se aprueba o se rechaza, siguen ocurriendo 100% en el backend, con reglas fijas que no dependen de ningún modelo de lenguaje. Si la IA no respondiera o se equivocara en el texto que sugiere, el flujo del sistema seguiría funcionando exactamente igual.

---

### 6. Si esto se usara de verdad con 200 empleados, ¿qué cambiarías o qué se rompería?

Varias cosas dejarían de ser suficientes:

- **El login simulado.** Un selector de usuario funciona para una prueba, pero con 200 personas reales necesitaría autenticación de verdad, con contraseñas o inicio de sesión corporativo.
- **La relación jefe-empleado**, que hoy es un campo simple, tendría que soportar casos más complejos: jefes que cambian de equipo, empleados con más de un aprobador según el tipo de ausencia, jerarquías con varios niveles.
- **El plan gratuito de hosting.** Ahora mismo el backend "se duerme" tras un rato sin uso y tarda unos segundos en responder de nuevo. Con 200 personas usándolo a diario, necesitaría un plan que se mantenga siempre activo.
- **Notificaciones.** Hoy el empleado tiene que entrar a la app para ver si le respondieron. Con más gente, haría falta avisar por correo o alguna notificación cuando cambie el estado de su solicitud.
- **Concurrencia.** El sistema ya valida saldo antes de confirmar, pero con muchas personas usando la aplicación al mismo tiempo, dos confirmaciones muy cercanas en el tiempo podrían necesitar un bloqueo más estricto a nivel de base de datos para evitar condiciones de carrera.

---

### 7. ¿Qué fue lo más difícil y cómo lo resolviste?

Lo más difícil no fue escribir el código del flujo en sí, sino todo lo que rodea llevarlo a un entorno real: el despliegue. Tuve que resolver, uno tras otro, varios problemas que en local nunca se hubieran notado: una dependencia faltante que tumbaba el backend al arrancar, un archivo de configuración duplicado que hacía que mis correcciones no surtieran efecto, y un problema de conexión al intentar administrar la base de datos en producción desde mi computador.

Para cada uno fui por partes. Primero confirmaba el síntoma exacto revisando los registros de error del servicio, después aislaba la causa comparando lo que tenía localmente contra lo que realmente estaba desplegado, y solo después de entender la causa real hacía el cambio. En el caso de la conexión a la base de datos que no lograba resolver, terminé optando por una solución distinta: en vez de conectarme yo directamente desde afuera, dejé que el propio backend hiciera el cambio necesario al arrancar, ya que él sí tiene una conexión interna y confiable con la base de datos.

---

### 8. Si tuvieras más tiempo, ¿qué le agregarías?

Agregaría notificaciones por correo cuando cambie el estado de una solicitud, para que el empleado no tenga que estar revisando manualmente. También me gustaría incorporar el contexto colombiano de festivos y "puentes" que menciona el reto, para que el sistema pueda advertir automáticamente si una solicitud incluye días no hábiles. Por último, agregaría un panel de reportes para RRHH, con una vista general de cuántos días ha tomado cada empleado en el año y quién tiene solicitudes próximas a vencer.

---

### 9. ¿Cuánto tiempo real te tomó? (Y si usaste IA, aproximadamente qué porcentaje hizo ella)

Empecé alrededor de la 1:00 p.m. y terminé cerca de la medianoche del mismo día, aunque el envío lo hago hasta la mañana siguiente. En total le dediqué cerca de 11 horas seguidas, contando desde estructurar el proyecto hasta dejarlo desplegado, probado y con este documento de respuestas listo.

En cuanto al reparto del trabajo, calculo que un 70% fue mío y un 30% de la IA. La IA me ayudó a escribir código más rápido y a depurar errores, pero no siempre entendía bien el contexto completo de lo que ya tenía construido, así que me tocó revisar, corregir y varias veces rehacer sus propuestas. Las decisiones de qué construir, cómo validar el flujo, y qué hacer cuando algo no cuadraba, las tomé yo en cada paso.

---

### 10. Cuéntanos una idea tuya que probaste aunque no te la pedimos

Al principio implementé que el jefe pudiera ver todas las solicitudes pendientes del sistema, sin distinguir de qué empleado eran. Funcionaba, pero no se sentía correcto: el reto decía explícitamente que el jefe debía ver las solicitudes "de su equipo", así que decidí ir más allá de lo mínimo y agregar una relación real entre cada empleado y su jefe, para que cada jefe solo vea a su propia gente, tal como pasaría en una empresa real, donde un jefe no debería estar aprobando vacaciones de gente que no le reporta a él.