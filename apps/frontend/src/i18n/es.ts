/**
 * Spanish (Latin American) language constants and translations
 */

export const es = {
  // Authentication
  auth: {
    signIn: 'Iniciar sesión',
    signUp: 'Registrarse',
    signOut: 'Cerrar sesión',
    email: 'Correo electrónico',
    password: 'Contraseña',
    confirmPassword: 'Confirmar contraseña',
    fullName: 'Nombre completo',
    forgotPassword: '¿Olvidó su contraseña?',
    resetPassword: 'Restablecer contraseña',
    backToSignIn: 'Volver a iniciar sesión',
    confirmSignUp: 'Confirmar registro',
    confirmationCode: 'Código de confirmación',
    resendCode: 'Reenviar código',
    submit: 'Enviar',
    submitting: 'Enviando...',
    verifyContact: 'Verificar contacto',
    code: 'Código',
    verify: 'Verificar',
  },
  
  // Navigation
  nav: {
    home: 'Inicio',
    chat: 'Chat',
    // dashboard removed - functionality integrated into chat
    configuration: 'Configuración',
    profile: 'Perfil',
    settings: 'Ajustes',
  },

  // Theme
  theme: {
    light: 'Modo claro',
    dark: 'Modo oscuro',
    system: 'Seguir sistema',
    toggle: 'Cambiar tema',
  },
  
  // Common
  common: {
    loading: 'Cargando...',
    error: 'Error',
    success: 'Éxito',
    cancel: 'Cancelar',
    save: 'Guardar',
    delete: 'Eliminar',
    edit: 'Editar',
    create: 'Crear',
    update: 'Actualizar',
    search: 'Buscar',
    filter: 'Filtrar',
    clear: 'Limpiar',
    close: 'Cerrar',
    confirm: 'Confirmar',
    yes: 'Sí',
    no: 'No',
    back: 'Volver',
    next: 'Siguiente',
    previous: 'Anterior',
    finish: 'Finalizar',
    required: 'Requerido',
    optional: 'Opcional',
    change: 'Cambiar a',
  },
  
  // Errors
  errors: {
    generic: 'Ha ocurrido un error. Por favor, intente nuevamente.',
    network: 'Error de conexión. Verifique su conexión a internet.',
    authentication: 'Error de autenticación. Por favor, inicie sesión nuevamente.',
    validation: 'Por favor, corrija los errores en el formulario.',
    notFound: 'No se encontró el recurso solicitado.',
    unauthorized: 'No tiene permisos para realizar esta acción.',
    serverError: 'Error del servidor. Por favor, intente más tarde.',
  },
  
  // Chat
  chat: {
    title: 'Asistente Virtual',
    placeholder: 'Envía un mensaje para iniciar una conversación',
    send: 'Enviar',
    uploadFile: 'Subir archivo',
    attachments: 'Archivos adjuntos',
    processing: 'Procesando...',
    typing: 'Escribiendo...',
    newSession: 'Nueva sesión',
    sessionHistory: 'Historial de sesiones',
  },
  
  // Patient
  patient: {
    title: 'Información del Paciente',
    id: 'ID del Paciente',
    firstName: 'Nombre',
    lastName: 'Apellido',
    dateOfBirth: 'Fecha de nacimiento',
    gender: 'Género',
    male: 'Masculino',
    female: 'Femenino',
    other: 'Otro',
    contactInfo: 'Información de contacto',
    phone: 'Teléfono',
    address: 'Dirección',
    medicalHistory: 'Historia médica',
    scheduledExams: 'Exámenes programados',
    status: 'Estado',
    selectPatient: 'Seleccionar paciente',
    searchPatient: 'Buscar paciente',
    noPatientSelected: 'No hay paciente seleccionado',
  },
  
  // Exams
  exam: {
    title: 'Examen',
    type: 'Tipo de examen',
    date: 'Fecha',
    time: 'Hora',
    medic: 'Médico',
    location: 'Ubicación',
    status: 'Estado',
    scheduled: 'Programado',
    inProgress: 'En progreso',
    completed: 'Completado',
    cancelled: 'Cancelado',
    results: 'Resultados',
    notes: 'Notas',
    duration: 'Duración',
    description: 'Descripción',
  },
  
  // Configuration
  config: {
    title: 'Configuración',
    patients: 'Pacientes',
    medics: 'Médicos',
    exams: 'Exámenes',
    reservations: 'Reservas',
    files: 'Archivos',
    settings: 'Configuración',
    manageEntities: 'Gestionar entidades',
    addNew: 'Agregar nuevo',
    editEntity: 'Editar entidad',
    deleteEntity: 'Eliminar entidad',
    confirmDelete: '¿Está seguro de que desea eliminar este elemento?',
  },
  
  // File upload
  fileUpload: {
    title: 'Subir archivo',
    dragDrop: 'Arrastre y suelte archivos aquí o haga clic para seleccionar',
    uploading: 'Subiendo...',
    uploaded: 'Archivo subido exitosamente',
    failed: 'Error al subir archivo',
    invalidType: 'Tipo de archivo no válido',
    tooLarge: 'El archivo es demasiado grande',
    maxSize: 'Tamaño máximo',
    supportedFormats: 'Formatos soportados',
  },
  
  // Notifications
  notifications: {
    title: 'Notificaciones',
    fileProcessingStarted: 'Procesamiento de archivo iniciado',
    fileProcessingCompleted: 'Procesamiento de archivo completado',
    fileProcessingFailed: 'Error al procesar archivo',
    fileUploading: 'Subiendo archivo',
    fileProcessing: 'Procesando archivo',
    patientUpdated: 'Paciente actualizado exitosamente',
    examScheduled: 'Examen programado exitosamente',
    reservationCreated: 'Reserva creada exitosamente',
    dismiss: 'Cerrar',
    retry: 'Reintentar',
    cancel: 'Cancelar',
  },
  
  // Validation messages
  validation: {
    required: 'Este campo es requerido',
    email: 'Ingrese un correo electrónico válido',
    minLength: 'Debe tener al menos {min} caracteres',
    maxLength: 'No debe exceder {max} caracteres',
    pattern: 'Formato inválido',
    passwordMismatch: 'Las contraseñas no coinciden',
    invalidDate: 'Fecha inválida',
    futureDate: 'La fecha debe ser futura',
    pastDate: 'La fecha debe ser pasada',
  },
};

export type Translations = typeof es;
