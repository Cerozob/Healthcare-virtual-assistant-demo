# Plantilla de Validación - Calculadora AWS
## Sistema de Gestión Sanitaria AWSomeBuilder2

**Fecha de Creación**: 30 de octubre de 2025  
**Región AWS**: us-east-1 (US East - N. Virginia)  
**Propósito**: Validación manual de estimaciones de costos usando AWS Pricing Calculator  
**Idioma**: Español (LATAM) con nombres de servicios AWS en inglés

---

## Instrucciones de Uso

Esta plantilla está diseñada para validar manualmente las estimaciones de costos del sistema AWSomeBuilder2 usando la **AWS Pricing Calculator** oficial. Complete cada escenario ingresando los valores especificados en la calculadora y registre los resultados obtenidos.

### Pasos para Validación:

1. **Acceder a AWS Pricing Calculator**: https://calculator.aws/
2. **Seleccionar Región**: us-east-1 (US East - N. Virginia)
3. **Agregar servicios** según cada escenario
4. **Ingresar valores** exactos especificados
5. **Registrar resultados** en las secciones correspondientes
6. **Comparar** con estimaciones internas
7. **Documentar discrepancias** y observaciones

---

## Escenario 1: Demo Actual (As-Is)
### Configuración Básica de Demostración

**Descripción**: Configuración actual del demo con usuarios limitados y funcionalidad básica.

#### Servicios AWS a Configurar:

##### 1. AWS Amplify
- **Servicio**: AWS Amplify
- **Tipo**: Hosting + Build
- **Configuración**:
  - Build minutes: `80 minutos/mes`
  - Hosting requests: `100,000 requests/mes`
  - Data transfer out: `50 GB/mes`
  - Storage: `5 GB`

**Resultado AWS Calculator**:
```
Build: $_______ /mes
Hosting: $_______ /mes
Data Transfer: $_______ /mes
Storage: $_______ /mes
Total Amplify: $_______ /mes
```

##### 2. Amazon Aurora PostgreSQL Serverless v2
- **Servicio**: Amazon Aurora
- **Configuración**:
  - Engine: PostgreSQL
  - Deployment: Serverless v2
  - ACU hours: `180 ACU-hours/mes` (promedio 6 ACU)
  - Storage: `50 GB`
  - I/O operations: `10 millones/mes`
  - Backup storage: `50 GB`

**Resultado AWS Calculator**:
```
Compute (ACU): $_______ /mes
Storage: $_______ /mes
I/O: $_______ /mes
Backup: $_______ /mes
Total Aurora: $_______ /mes
```

##### 3. AWS Lambda
- **Servicio**: AWS Lambda
- **Configuración**:
  - Requests: `500,000 requests/mes`
  - Duration: `200ms promedio`
  - Memory: `256 MB`
  - Architecture: x86_64

**Resultado AWS Calculator**:
```
Requests: $_______ /mes
Compute: $_______ /mes
Total Lambda: $_______ /mes
```

##### 4. Amazon API Gateway (HTTP API)
- **Servicio**: API Gateway
- **Configuración**:
  - API type: HTTP API
  - Requests: `500,000 requests/mes`
  - Data transfer: `5 GB/mes`

**Resultado AWS Calculator**:
```
Requests: $_______ /mes
Data Transfer: $_______ /mes
Total API Gateway: $_______ /mes
```

##### 5. Amazon S3
- **Servicio**: Amazon S3
- **Configuración**:
  - Standard storage: `100 GB`
  - PUT requests: `10,000/mes`
  - GET requests: `50,000/mes`
  - Data transfer out: `20 GB/mes`

**Resultado AWS Calculator**:
```
Storage: $_______ /mes
Requests: $_______ /mes
Data Transfer: $_______ /mes
Total S3: $_______ /mes
```

##### 6. Amazon Bedrock
- **Servicio**: Amazon Bedrock
- **Configuración**:
  - Model: Claude 3.5 Haiku
  - Input tokens: `10 millones/mes`
  - Output tokens: `4 millones/mes`

**Resultado AWS Calculator**:
```
Input tokens: $_______ /mes
Output tokens: $_______ /mes
Total Bedrock Models: $_______ /mes
```

##### 7. Amazon Cognito
- **Servicio**: Amazon Cognito
- **Configuración**:
  - Monthly Active Users: `100 MAU`
  - Advanced Security Features: Habilitado

**Resultado AWS Calculator**:
```
MAU: $_______ /mes
Advanced Security: $_______ /mes
Total Cognito: $_______ /mes
```

#### Resumen Escenario 1 - Demo Actual
```
AWS Amplify: $_______ /mes
Aurora PostgreSQL: $_______ /mes
Lambda: $_______ /mes
API Gateway: $_______ /mes
S3: $_______ /mes
Bedrock: $_______ /mes
Cognito: $_______ /mes
Otros servicios: $_______ /mes
─────────────────────────────
TOTAL DEMO: $_______ /mes
TOTAL ANUAL: $_______ /año
```

**Comparación con Estimación Interna**:
- Estimación interna: $5,724.09/mes
- Calculadora AWS: $_______ /mes
- Diferencia: $_______ /mes (____%)

---

## Escenario 2: Producción - 1 Usuario
### Configuración Mínima de Producción

**Descripción**: Configuración de producción para validar costos base con un solo usuario activo.

#### Servicios AWS a Configurar:

##### 1. AWS Amplify
- **Configuración**:
  - Build minutes: `160 minutos/mes`
  - Hosting requests: `3,000 requests/mes`
  - Data transfer out: `6 GB/mes`
  - Storage: `10 GB`

**Resultado AWS Calculator**:
```
Total Amplify: $_______ /mes
```

##### 2. Amazon Aurora PostgreSQL Serverless v2
- **Configuración**:
  - ACU hours: `720 ACU-hours/mes` (1 ACU constante)
  - Storage: `100 GB`
  - I/O operations: `1 millón/mes`
  - Backup storage: `100 GB`

**Resultado AWS Calculator**:
```
Total Aurora: $_______ /mes
```

##### 3. AWS Lambda
- **Configuración**:
  - Requests: `60,000 requests/mes`
  - Duration: `300ms promedio`
  - Memory: `512 MB`

**Resultado AWS Calculator**:
```
Total Lambda: $_______ /mes
```

##### 4. Amazon Bedrock
- **Configuración**:
  - Model: Claude 3.5 Haiku
  - Input tokens: `400,000 tokens/mes`
  - Output tokens: `160,000 tokens/mes`

**Resultado AWS Calculator**:
```
Total Bedrock: $_______ /mes
```

##### 5. Amazon Cognito
- **Configuración**:
  - Monthly Active Users: `1 MAU`
  - Advanced Security Features: Habilitado

**Resultado AWS Calculator**:
```
Total Cognito: $_______ /mes
```

#### Resumen Escenario 2 - Producción 1 Usuario
```
TOTAL PRODUCCIÓN (1 usuario): $_______ /mes
Costo por usuario: $_______ /mes
```

---

## Escenario 3: Producción - Supuestos del Cliente
### Configuración Basada en Requisitos Reales

**Descripción**: Configuración de producción basada en los supuestos y requisitos proporcionados por el cliente durante las reuniones.

**Supuestos del Cliente**:
- 100,000 usuarios registrados totales
- 10,000 usuarios activos mensuales (10% de conversión)
- 30,000 peticiones por minuto en horas pico
- 20 interacciones por médico por sesión
- Sesiones de 15-30 minutos (máximo 1 hora)

#### Servicios AWS a Configurar:

##### 1. AWS Amplify
- **Configuración**:
  - Build minutes: `160 minutos/mes`
  - Hosting requests: `3,000,000 requests/mes`
  - Data transfer out: `1,200 GB/mes`
  - Storage: `10 GB`

**Resultado AWS Calculator**:
```
Total Amplify: $_______ /mes
```

##### 2. Amazon Aurora PostgreSQL Serverless v2
- **Configuración**:
  - ACU hours: `6,480 ACU-hours/mes`
  - Peak ACU: 15 ACU (12 horas/día)
  - Off-peak ACU: 3 ACU (12 horas/día)
  - Storage: `500 GB`
  - I/O operations: `200 millones/mes`
  - Backup storage: `500 GB`

**Resultado AWS Calculator**:
```
Total Aurora: $_______ /mes
```

##### 3. AWS Lambda
- **Configuración**:
  - Requests: `5,800,000 requests/mes`
  - Duration: `400ms promedio`
  - Memory: `512 MB`
  - Provisioned concurrency: `10 instancias`

**Resultado AWS Calculator**:
```
Total Lambda: $_______ /mes
```

##### 4. Amazon API Gateway (HTTP API)
- **Configuración**:
  - Requests: `6,000,000 requests/mes`
  - Data transfer: `30 GB/mes`

**Resultado AWS Calculator**:
```
Total API Gateway: $_______ /mes
```

##### 5. Amazon S3
- **Configuración**:
  - Standard storage: `2,400 GB`
  - Standard-IA: `500 GB`
  - Glacier Instant: `100 GB`
  - PUT requests: `500,000/mes`
  - GET requests: `2,000,000/mes`
  - Data transfer out: `100 GB/mes`

**Resultado AWS Calculator**:
```
Total S3: $_______ /mes
```

##### 6. Amazon Bedrock - Foundation Models
- **Configuración**:
  - Model: Claude 3.5 Haiku (90% del tráfico)
  - Input tokens: `3,600,000,000 tokens/mes`
  - Output tokens: `1,440,000,000 tokens/mes`
  - Cache reads: `5,400,000,000 tokens/mes`
  
  - Model: Claude 3.5 Sonnet (10% del tráfico)
  - Input tokens: `800,000,000 tokens/mes`
  - Output tokens: `300,000,000 tokens/mes`

**Resultado AWS Calculator**:
```
Claude 3.5 Haiku: $_______ /mes
Claude 3.5 Sonnet: $_______ /mes
Total Bedrock Models: $_______ /mes
```

##### 7. Amazon Bedrock - Data Automation
- **Configuración**:
  - Document processing: `200,000 páginas/mes`
  - Audio processing: `75,000 minutos/mes`
  - Video processing: `2,000 minutos/mes`
  - Batch processing: 80% del volumen

**Resultado AWS Calculator**:
```
Total Bedrock Data Automation: $_______ /mes
```

##### 8. Amazon Bedrock - Guardrails
- **Configuración**:
  - Text units processed: `24,000,000 unidades/mes`
  - Content policy: Habilitado
  - PII detection: Habilitado

**Resultado AWS Calculator**:
```
Total Bedrock Guardrails: $_______ /mes
```

##### 9. Amazon Cognito
- **Configuración**:
  - Monthly Active Users: `10,000 MAU`
  - Advanced Security Features: Habilitado

**Resultado AWS Calculator**:
```
Total Cognito: $_______ /mes
```

##### 10. VPC y Networking
- **Configuración**:
  - NAT Gateway: `1 gateway × 720 horas/mes`
  - Data processing: `500 GB/mes`

**Resultado AWS Calculator**:
```
Total VPC/NAT: $_______ /mes
```

#### Resumen Escenario 3 - Supuestos del Cliente
```
AWS Amplify: $_______ /mes
Aurora PostgreSQL: $_______ /mes
Lambda: $_______ /mes
API Gateway: $_______ /mes
S3: $_______ /mes
Bedrock Models: $_______ /mes
Bedrock Data Automation: $_______ /mes
Bedrock Guardrails: $_______ /mes
Cognito: $_______ /mes
VPC/Networking: $_______ /mes
Otros servicios: $_______ /mes
─────────────────────────────
TOTAL CLIENTE: $_______ /mes
TOTAL ANUAL: $_______ /año
Costo por MAU: $_______ /mes
```

**Comparación con Estimación Interna**:
- Estimación interna: $28,440.21/mes
- Calculadora AWS: $_______ /mes
- Diferencia: $_______ /mes (____%)

---

## Escenario 4: Crecimiento 5x (50,000 MAU)
### Configuración de Escalamiento

**Descripción**: Configuración para 50,000 usuarios activos mensuales (crecimiento 5x del escenario base).

#### Servicios AWS a Configurar:

##### 1. AWS Amplify
- **Configuración**:
  - Build minutes: `200 minutos/mes`
  - Hosting requests: `15,000,000 requests/mes`
  - Data transfer out: `6,000 GB/mes`
  - Storage: `15 GB`

**Resultado AWS Calculator**:
```
Total Amplify: $_______ /mes
```

##### 2. Amazon Aurora PostgreSQL Serverless v2
- **Configuración**:
  - ACU hours: `22,680 ACU-hours/mes`
  - Peak ACU: 35 ACU (12 horas/día)
  - Off-peak ACU: 8 ACU (12 horas/día)
  - Storage: `2,500 GB`
  - I/O operations: `1,000 millones/mes`
  - Backup storage: `2,500 GB`

**Resultado AWS Calculator**:
```
Total Aurora: $_______ /mes
```

##### 3. AWS Lambda
- **Configuración**:
  - Requests: `29,000,000 requests/mes`
  - Duration: `350ms promedio`
  - Memory: `512 MB`
  - Provisioned concurrency: `50 instancias`

**Resultado AWS Calculator**:
```
Total Lambda: $_______ /mes
```

##### 4. Amazon API Gateway (HTTP API)
- **Configuración**:
  - Requests: `30,000,000 requests/mes`
  - Data transfer: `150 GB/mes`

**Resultado AWS Calculator**:
```
Total API Gateway: $_______ /mes
```

##### 5. Amazon S3
- **Configuración**:
  - Standard storage: `12,000 GB`
  - Standard-IA: `2,500 GB`
  - Glacier Instant: `500 GB`
  - PUT requests: `2,500,000/mes`
  - GET requests: `10,000,000/mes`
  - Data transfer out: `500 GB/mes`

**Resultado AWS Calculator**:
```
Total S3: $_______ /mes
```

##### 6. Amazon Bedrock - Foundation Models
- **Configuración**:
  - Model: Claude 3.5 Haiku
  - Input tokens: `18,000,000,000 tokens/mes`
  - Output tokens: `7,200,000,000 tokens/mes`
  - Cache reads: `27,000,000,000 tokens/mes`
  
  - Model: Claude 3.5 Sonnet
  - Input tokens: `4,000,000,000 tokens/mes`
  - Output tokens: `1,500,000,000 tokens/mes`

**Resultado AWS Calculator**:
```
Total Bedrock Models: $_______ /mes
```

##### 7. Amazon Bedrock - Data Automation
- **Configuración**:
  - Document processing: `800,000 páginas/mes`
  - Audio processing: `300,000 minutos/mes`
  - Video processing: `8,000 minutos/mes`

**Resultado AWS Calculator**:
```
Total Bedrock Data Automation: $_______ /mes
```

##### 8. Amazon Bedrock - Guardrails
- **Configuración**:
  - Text units processed: `120,000,000 unidades/mes`

**Resultado AWS Calculator**:
```
Total Bedrock Guardrails: $_______ /mes
```

##### 9. Amazon Cognito
- **Configuración**:
  - Monthly Active Users: `50,000 MAU`
  - Advanced Security Features: Habilitado

**Resultado AWS Calculator**:
```
Total Cognito: $_______ /mes
```

#### Resumen Escenario 4 - Crecimiento 5x
```
AWS Amplify: $_______ /mes
Aurora PostgreSQL: $_______ /mes
Lambda: $_______ /mes
API Gateway: $_______ /mes
S3: $_______ /mes
Bedrock Models: $_______ /mes
Bedrock Data Automation: $_______ /mes
Bedrock Guardrails: $_______ /mes
Cognito: $_______ /mes
Otros servicios: $_______ /mes
─────────────────────────────
TOTAL 5x CRECIMIENTO: $_______ /mes
TOTAL ANUAL: $_______ /año
Costo por MAU: $_______ /mes
```

**Comparación con Estimación Interna**:
- Estimación interna: $127,980/mes
- Calculadora AWS: $_______ /mes
- Diferencia: $_______ /mes (____%)

---

## Análisis Comparativo de Escenarios

### Resumen de Todos los Escenarios

| Escenario | MAU | Costo Mensual (Calculadora) | Costo por MAU | Costo Anual |
|-----------|-----|------------------------------|---------------|-------------|
| Demo Actual | 100 | $_______ | $_______ | $_______ |
| Producción 1 Usuario | 1 | $_______ | $_______ | $_______ |
| Supuestos Cliente | 10,000 | $_______ | $_______ | $_______ |
| Crecimiento 5x | 50,000 | $_______ | $_______ | $_______ |

### Comparación con Estimaciones Internas

| Escenario | Estimación Interna | Calculadora AWS | Diferencia | % Diferencia |
|-----------|-------------------|-----------------|------------|--------------|
| Demo Actual | $5,724.09 | $_______ | $_______ | ____% |
| Supuestos Cliente | $28,440.21 | $_______ | $_______ | ____% |
| Crecimiento 5x | $127,980.00 | $_______ | $_______ | ____% |

---

## Observaciones y Discrepancias

### Discrepancias Identificadas

#### Servicios con Mayor Diferencia:
1. **Servicio**: _________________
   - **Diferencia**: $_______ /mes
   - **Posible Causa**: _________________
   - **Acción Requerida**: _________________

2. **Servicio**: _________________
   - **Diferencia**: $_______ /mes
   - **Posible Causa**: _________________
   - **Acción Requerida**: _________________

3. **Servicio**: _________________
   - **Diferencia**: $_______ /mes
   - **Posible Causa**: _________________
   - **Acción Requerida**: _________________

### Servicios No Disponibles en Calculadora:
- [ ] Amazon Bedrock Data Automation
- [ ] Amazon Bedrock Guardrails
- [ ] Amazon Bedrock AgentCore
- [ ] Otros: _________________

### Limitaciones de la Calculadora:
1. _________________
2. _________________
3. _________________

---

## Supuestos Personales y Notas

### Supuestos Adicionales Aplicados:

#### Escenario Demo:
- _________________
- _________________
- _________________

#### Escenario Producción:
- _________________
- _________________
- _________________

#### Escenario Crecimiento:
- _________________
- _________________
- _________________

### Notas de Configuración:

#### Dificultades Encontradas:
1. _________________
2. _________________
3. _________________

#### Configuraciones Alternativas Utilizadas:
1. **Servicio**: _________________
   **Configuración Original**: _________________
   **Configuración Alternativa**: _________________
   **Razón**: _________________

2. **Servicio**: _________________
   **Configuración Original**: _________________
   **Configuración Alternativa**: _________________
   **Razón**: _________________

### Observaciones Generales:
_________________
_________________
_________________

---

## Recomendaciones

### Ajustes a Estimaciones Internas:
1. **Servicio**: _________________
   **Ajuste Recomendado**: _________________
   **Impacto**: $_______ /mes

2. **Servicio**: _________________
   **Ajuste Recomendado**: _________________
   **Impacto**: $_______ /mes

### Servicios a Investigar Más:
- [ ] _________________
- [ ] _________________
- [ ] _________________

### Próximos Pasos:
1. _________________
2. _________________
3. _________________

---

## Información de Validación

**Validado por**: _________________  
**Fecha de Validación**: _________________  
**Tiempo Invertido**: _______ horas  
**Versión de Calculadora AWS**: _________________  
**Región Utilizada**: us-east-1  

### Enlaces de Referencia:
- **AWS Pricing Calculator**: https://calculator.aws/
- **Estimación Guardada Demo**: _________________
- **Estimación Guardada Producción**: _________________
- **Estimación Guardada Crecimiento**: _________________

### Archivos Adjuntos:
- [ ] Capturas de pantalla de configuraciones
- [ ] Exportación CSV de resultados
- [ ] Enlaces compartidos de calculadora
- [ ] Documentación adicional

---

**Nota**: Esta validación debe realizarse periódicamente (mensualmente) para mantener la precisión de las estimaciones, especialmente considerando los cambios frecuentes en los precios de servicios de AWS y la introducción de nuevos servicios como Amazon Bedrock.

**Importante**: Los servicios de Amazon Bedrock pueden no estar completamente disponibles en la calculadora AWS debido a su reciente lanzamiento. En estos casos, utilice las estimaciones internas basadas en la documentación oficial de precios de AWS.
