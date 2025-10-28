## AWSome Builder II

Link al AB1
<https://quip-amazon.com/n2yaAss0Bq2h/AWSome-Builder-I>

### Se asume que

* las bases de datos de las workloads de anycompany funcionan con o postgres o sql server (para elegir Aurora en RDS y migrar con DMS mas fácil, y ganar puntos mencionando Babelfish)
* La data no estructurada son Documentos y archivos sueltos que pueden importarse a S3, y son compatibles con Bedrock Data Automatíon
* Álvaro mencionó esto: usan Contenedores para las workloads actualmente, o algunas.
* Las operaciones que deben hacer los agentes están implementadas como endpoints REST (y se plantean como lambdas expuestas en API GW), o al menos algún tool ya disponible en Strands Agents.
* No hemos aclarado si
* Supongo que lo de residencia de datos que se reviso en el AB1 no debería ser problema
* Todos los servicios a usar deberían ser HIPAA eligible en principio (checklist al final)

### Decisiones de arquitectura hasta el momento

#### 1. Sobre los datos

* Se agrega un flujo para migrar de alguna base de datos on premise hacia Aurora Postgres, para ganar puntos con lo de sql server si se menciona, y para poder continuar partiendo de que se puede migrar con DMS.
* Sobre los archivos sueltos o documentos, se asume que se podrían migrar a S3 por ejemplo con DataSync, par a luego ser utilizados como parte de una knowledge Base de Bedrock

#### 2. Sobre las fuentes de datos

* Bedrock Knowledge bases sí, la cuestión es donde guardar los vectores:
  * S3 Vectors es cost effective, puede ser si lo logro hacer funcionar
  * ~~Otra opción es irse por OpenSearch Serverless que es como la de-facto para knowledge bases y GenAI en Bedrock, no lo tuve en cuenta~~
  * ~~Una tercera es usar una knowledge base a partir de un GenAI Index de Amazon Kendra, Kendra es interoperable con muchas fuentes de datos incluyendo varias fuera de AWS, parece una opción robusta pero también me paració out of scope.~~
  * Y por último, Bedrock Permite guardar los vectores en Aurora Postgres, parece buena opción ya que igual ya se planea usar Aurora para migrar, luego tiene sentido irse por ese mismo lado.
* Comprehend Medical permite extraer datos de condiciones médicas, prescripciones y las entidades ICD10 a partir de texto, parece muy útil para el caso de uso
  * Yo probé pasando mi historia médica en PDF por S3 → Bedrock Data Automatíon → Comprehend Medical y funciono perfecto, luego opté por eso.
* Se usará Bedrock Data Automation, primero para parsear documentos en la Knowledge Base, y porque Comprehend Medical requiere del texto para funcionar.
  * Aparte, con BDA se puede guardar la data relevante del paciente en la base de datos.
* HealthLake usa formato FHIR, se supone que se puede importar data no estructurada usando comprehend medical pero me parece out of scope y tampoco vi una forma intuitiva de hacerlo, lo único sería por gobernanza de datos pero optar por LakeFormation me parece mejor idea porque abarca todo tipo de data, igual, tene en cuenta pero outofscope
* para el tema de PII y PHI la idea es usar Bedrock GuardRails y Comprehend Medical porque a la final toda la interaccion es con la interfaz de chat (a ojos del AB).

#### 3. Sobre los Agentes de Bedrock

* Un agente se encargará de obtener información médica detallada a partir de 1: un diagnostico en texto, esto a partir de la knowledge base; 2. los códigos ICD10CM de Comprehend Medical, y del API externa <https://icd.who.int/icdapi> si es necesario, RxNorm está disponible en Comprehend medical pero ni idea al respect; 3. del paciente, como su expediente previo y, en particular, aquellos exámenes que haya tenido antes o recientemente.
* Se asume que el usuario final es un médico general o especialista que cuenta con el conocimiento necesario para aplicar el buen juicio “good judgement by a trained medical professional” según los docs de AWS.
* Un agente será el encargado de los tests/exámenes médicos, capaz de ver los exámenes médicos agendables (list), agendar uno nuevo (y confirmar) a un paciente, consultar disponibilidad de los exámenes y eso. La idea es NO recomendarle exámenes al médico porque esos datos si que no los conseguí. Por lo que se asume que el médico sabe qué debería hacerse. Un examen también puede ser programar una cita a futuro. Estos son basados en APIs y tools directamente y no recuperan info de ninguna knowledge base

#### 4. Nice to Have

* Agregar lo de migración
* ~~Ver lo de migrar workloads con contenedores~~
* Agregar asistencia por voz (voto por que no)? se podría probar agregar grabaciones con HealthScribe, O con Bedrock Data Automation + Comprehend Medical (HealthScribe no genera una transcripción completo sino solo los chunks?) ← miguermo@ mencionó que sería chévere, en particular, mencionó no usar BDA con audios por la terminología médica

##### Observaciones de Álvaro

##### Observaciones de Paola

* entre menos agentes peor
  * El de exámenes si o si
  * el agente de icd10 sobra, porque tener un agente con un único action group no aguanta
    * Luego, yo voyo por tener un agente para information retrieval y que decida entre info de KB o info de ICD10 según la duda del médico o si quiere más detalles.
  * Sobre la base de conocimiento,

##### Observaciones de Miguel

* Ver lo de audios, a la final, usar healthscribe podría ser plausible

#### 5. HIPAA Compliance Checklist

* Seguridad y monitoreo

  * [x] KMS
  * [x] Secrets Manager
  * [x] IAM
  * [x] CloudWatch
  * [x] Cognito (en Amplify)

* Control de Infraestructura

  * [x] CloudFormation
  * [x] ECR
  * [x] Systems Manager Parameter Store

* Arquitectura general

  * [x] Amplify
  * [x] S3
  * [x] API Gateway
  * [x] Lambda
  * [x] Bedrock
  * [x] Aurora
  * [x] DMS
  * [x] DataSync
  * [x] Kendra

* * *

## Dry Run con Álvaro

maybe una dispo de intro a bedrock

cto y ver como la solucion nos apoya

no conozco mucho de la nube pero tengo conocimientos agnóstico

bienbien

CDN en Amplify?

textract y bda
contenedores no, maybe ecr no es fuerte

me pase minuto y medio

bien bien

chevere chevere todo. Que tenga el detalle

feedback de los que son expertos

en general bien,

preguntar de observabilidad en agentes, ver en strands

ver los diferentes tipos de agentes y cual conviene para que,

## dryrun 2

nicolas es cso
validar como desplegamos esta solución de la manera mas segura, usamos datos personales pii phi y queremos mantener los controles

jacayce es cto
entender tecnico por qué la solucion, mi propuesta, justificación

german
lider de inovación e ia en aws y como se compara con otros proveedores

german

active directory & amplify → auth → otra sesion!

nicolas
seguridad
paloalto firewall → revisar firewall externos

idioma!!!!

db vectorial hay que hacer las queries

#### Feedback Nicolás

active directory → eso faltó, paloalto firewall y WAF tiene alguas reglas

api gateway rest y que sirve con bedrock

guardrails NO es solo inglés

mencionar PGvector

una lambda alcanza

red flag es PoC. no me comprometo a hacer una PoC, llegar hasta algun lado, el backend incluir alguna que otra cosa del front seguridad no va, mejor manejo al tiempo muy grande y robusta, puede ser complicado.

##### respuestas feedback

idioma español

active directory: sí puedes usar saml  para autenticarte con tu userbase en cognito
sobre usar el msad on premise, sí, puedes configurar un conector en aws directory services

pgvector: , el modelo busca documentos relevantes en la KB según el query del usuario, el query es natural, no sql

firewall: sobre el firewall, hay opciones en marketplace, vm-series firewall entre otros

bedrock and apigw: sobre streaming, se puede usar websockets en apigateway y manejar los mensajes con lambdas para stremear el output del modelo, o usar appsync

#### Feedback Germán

#### Feedback Juan Andrés

DRYRUN 2

jose: CEO, no técnico pero igual

entender a un alto nivel los beneficios de la solución, incursionar al mundo de la ia

sergio: ciso

si la solución contempla las mejores practicas de seguridad: regulacion pii y phi

paola: lider de inovacion en ia, como funciona el genai en aws, poco contexto pero ejemplos como asistentes virtuales. seguridad pii phi estandares certificaciones.

usecase def: jose enfasis de automatizaciones: **como medir el impacto?, tarda actualmente x tiempo y el esfuerzo del médico. actualmente el medico se echa 2 y 3 minutos para capturar la info y agendar siguientes pasos y update del historial médico, reducir el tiempo.**

2000 peticiones por segundo, ese es el límite. Paola quiere el numero exacto

sergio pregunta por guardrails → como es el costo de guadrails?

jose pregunta alucinaciones, cumplimiento

human in the loop. guardrails reglas ahi mismo.

incluir manejo de PII/PHI

* * *
feedback de jose y paola

good:

jose

buen manejo del tiempo, ojo validar agenda y eso bien, expectativas.

chevere nombrar a cada uno de ellos.

mas pushback y preguntar mas cosas para los costos, sizing, consultas promedio al día, cuantos lugares hay y en base a eso calculo.

preparacion de costos de AB3

el final, es el joker q corono, IaC, si estoy corto lo mocho, lo de seguridad si o si va.

chevere saber quien levantó la mano

Paola

bien → same

mejorar:

jose:

importante darme tiempo al inicio que pregunto jose, para preguntar de vuelta, aparte si pregunto yo puedo pensar mejor la respuesta "ah tu quieres <parafrasear>"

lo de las 2K peticiones preguntar de eso,

hacer el disclaimer de decir que voy a tomar notas

decirle que es una buena pregunta pa ganar tiempo

no decir *garantizar* ojo
al final con el pushy "uy quiero todo de una, maravilloso" → tener otra página del alcance de la PoC, si es el mismo nada, si

ojo, reap de lo que me llevo, me puedo llevar cosas, confirmación verbal de que digan si si pega, más dramatizado y realista "les envío un correo para agendar"

mejorar

paola:

el contexto es más charladito, imágenes y no sólo texto, más visual.

recomendaciones: acotar algunos como "limites y eso", parafrasear y ganar tiempo. Algunas le dí muchas vueltas, conocluir mejor. si no se paila "no sé" no estoy seguro y te digo x, pero a la fija y hablar con confianza, leerme los FAQs. evaluar modelos de bedrock, hay automaticos o a personas. FAQs, guardrails

step functions, desordenado → en BDA puedo hacer cosas y pareciera que comprehend medical es redundante. inglés, healthscribe eh, BDA, pero healthscribe si es mejor. comprehend medical más de PII y PHI

más vocal para el PoC y el AB3, duplicar y poner en otro lado

AB3: poner la sesión y decir exactamente cuando y qué vamos a ver, "qué les parece?", la confianza de proponer

si si hago todo, me vendo mejor y les digo si todo sisisisi, super plus

revisar la calculadora de datos para ver que puedo preguntar

* * *
feedback sergio:

abrebocas en la intro también, para sentirse escuchado

si o si auth con cognito al comienzo, o poner el iconito en vivo
hacer un eco y re-preguntar

a vecs respondi a muy alto nivel, ejemplo: costos de guardrails detallar más

debo conocer la forma de costo de cada servicio que use

al CEO le respondi muy técnico, revisar el rol del que pregunta y responder acorde

red flag: comprehend medical funciona bien, si el usecase, ojo con lo de solo soportar inglés, pueden tirar duro

tono: fluidez y confianza al hablar

*time* para manejar el cierre

* * *

# AB2 REAL

jacayce - esp desarrollo, entender como las tecnologias e implementarlas, técnico

paola, esp genai, propuestas de ia generativa, stack tecnologíco, best practices recomendaciones y abierta a manejar genai en aws

sergio, gerente de seguridad en anyhealthcare, ver seguridad tuve en cuenta
* * *

* dominios propios de amplify, sergio
* jacayce, ui components → bn
* jacayce, stagings
* sergio, permisos en cognito
* paola, control de costos limites por identidad? eso como es? saas? llevarmelo
* paola, anthropic? pq bedrock
* ruby, llevarmelo → yes
* revisar si cambian los terminos y condiciones de bedrock
* Metricas personalizadas en bedrock me lo llevo
* paola, si pero sacar los nuevos
* sergio, manejo de red, vpc verlo y redes, me lo llevo

* * *
ab2 suggestions daniela

* ver las faq
* simplificar mas
* pasar el recap a toda

ab2 suggestions gabriel

* security, incluso sec on aws physical
* concise, no divagar, pushback
* faqs y simplificar

* * *

# AWSomeBuilder2 - final

Nombres y roles

**hard stop paola 5pm**

paola esp genai ia - uso de IAGENERATIVA, Que modelos usamos, seguridad, info sensible.

sergio yepes, seguridad, la nube es insegura pero revisar

jacayce - desarrollo, entender como vamos a hacer esto, stack tecnológíco
* * *
sergio, notas escritas. Por ahora las notas, multimedia

pushback

solo notas?

github, jenkins.

react y vue.

sergio autenticacion

api interna, proceso de autenticación

paola → soconcurrentes

paola dice que openai, que modelo elegir

diferentes formatos
* * *
me llevo: proceso manual de autenticación custom - sergio, costos.

actualmente, 100000 usuarios sistemas. 10% activos al mes , cobran por todo o activos????

paola. solicitudes concurrentes → 30000 rpm, tradicional.

no hay metricas de texto en tokens → xdddddd

apigateway → la conversacion no se cae???

como revisar si se puede revisar codigo desplegado en producción

revision de vulnerabilidades → codeartifact

sergio, 20 interacciones de los medicos. 15 30 min o max 1 hora, concurrencia

manejo del tiempo no se eliminen

feedback

* calvazo
* mejoria notoria
* tecnicamente bien
* calvazo por codeartifact, revisar mejor eso
* sentarnos a ver shadows
* no se es no se, sin dar el otro vaino. Ponerle punto a las respuestas
* ojo con overexplaining, honesto, no se, voy y vuelvo

forma

* temas de forma,
* modular voz, calma, hablar despacio, pronunciar
* relajarse, controlado, seguro
* respuestas mas al grano, y si aporta de verdad decir algo mas, si no no.
* conciso
* estar seguro de lo que digo, aveces se sentía inseguro pero incluso estando bien

en el mundo real: dije algo mal, revise mal no es codeartifact es inspector y responder de UNA
