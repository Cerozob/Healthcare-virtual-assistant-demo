"""
Bedrock Guardrail Construct for Healthcare Workflow System.
"""

from aws_cdk import aws_bedrock as bedrock
from constructs import Construct


class BedrockGuardrailConstruct(Construct):
    """
    Construct for creating Bedrock Guardrails with healthcare-specific configurations.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.guardrails = bedrock.CfnGuardrail(
            self,
            "HealthCareGuardRails",
            blocked_input_messaging="Información sensible detectada y procesada de forma segura",
            blocked_outputs_messaging="Contenido procesado con protección de datos aplicada",
            name="HealthCareGuardRails",
            automated_reasoning_policy_config=None,

            content_policy_config=bedrock.CfnGuardrail.ContentPolicyConfigProperty(
                filters_config=[
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        input_strength="MEDIUM",
                        output_strength="MEDIUM",
                        type="HATE",
                        input_action="NONE",
                        input_enabled=True,
                        input_modalities=["TEXT", "IMAGE"],
                        output_action="NONE",
                        output_enabled=True,
                        output_modalities=["TEXT"]
                    ),
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        input_strength="MEDIUM",
                        output_strength="MEDIUM",
                        type="INSULTS",
                        input_action="NONE",
                        input_enabled=True,
                        input_modalities=["TEXT", "IMAGE"],
                        output_action="NONE",
                        output_enabled=True,
                        output_modalities=["TEXT"]
                    ),
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        input_strength="MEDIUM",
                        output_strength="MEDIUM",
                        type="VIOLENCE",
                        input_action="NONE",
                        input_enabled=True,
                        input_modalities=["TEXT", "IMAGE"],
                        output_action="NONE",
                        output_enabled=True,
                        output_modalities=["TEXT"]
                    ),
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        input_strength="MEDIUM",
                        output_strength="MEDIUM",
                        type="SEXUAL",
                        input_action="NONE",
                        input_enabled=True,
                        input_modalities=["TEXT", "IMAGE"],
                        output_action="NONE",
                        output_enabled=True,
                        output_modalities=["TEXT"]
                    )
                ],
                content_filters_tier_config=bedrock.CfnGuardrail.ContentFiltersTierConfigProperty(
                    tier_name="STANDARD"
                )
            ),
            contextual_grounding_policy_config=bedrock.CfnGuardrail.ContextualGroundingPolicyConfigProperty(
                filters_config=[
                    bedrock.CfnGuardrail.ContextualGroundingFilterConfigProperty(
                        threshold=0.2,  # Lower threshold to be less restrictive
                        type="GROUNDING"
                    ),
                    bedrock.CfnGuardrail.ContextualGroundingFilterConfigProperty(
                        threshold=0.2,  # Lower threshold to be less restrictive
                        type="RELEVANCE"
                    )
                ]
            ),
            cross_region_config=bedrock.CfnGuardrail.GuardrailCrossRegionConfigProperty(
                guardrail_profile_arn=f"arn:aws:bedrock:{self.region}:{self.account}:guardrail-profile/us.guardrail.v1:0"
            ),
            description="Guardrails for the healthcare assistant",
            sensitive_information_policy_config=self._create_sensitive_information_policy(),
            topic_policy_config=bedrock.CfnGuardrail.TopicPolicyConfigProperty(
                topics_config=[
                    bedrock.CfnGuardrail.TopicConfigProperty(
                        definition="Discusiones sobre trading de criptomonedas, consejos de inversión, especulación financiera, o promoción de criptomonedas específicas o plataformas de trading.",
                        name="TradingCriptomonedas",
                        type="DENY",
                        examples=[
                            "¿Cuál es la mejor criptomoneda para invertir ahora?",
                            "¿Cómo puedo ganar dinero haciendo trading con Bitcoin?",
                            "¿Debería comprar Ethereum o Dogecoin?",
                            "Cuéntame sobre las últimas estrategias de trading crypto",
                            "¿Qué plataforma de trading da los mejores rendimientos?"
                        ],
                        input_action="BLOCK",
                        input_enabled=True,
                        output_action="BLOCK",
                        output_enabled=True
                    ),
                    bedrock.CfnGuardrail.TopicConfigProperty(
                        definition="Discusiones sobre deportes extremos peligrosos, acrobacias arriesgadas, o actividades que podrían resultar en lesiones graves sin medidas de seguridad apropiadas.",
                        name="DeportesExtremosPeligrosos",
                        type="DENY",
                        examples=[
                            "¿Cómo hago un salto mortal desde un edificio?",
                            "¿Cuál es la mejor forma de saltar entre azoteas?",
                            "¿Cómo puedo hacer acrobacias peligrosas en moto?",
                            "Dime cómo escalar sin equipo de seguridad",
                            "¿Cómo hago trucos peligrosos en skateboard?"
                        ],
                        input_action="BLOCK",
                        input_enabled=True,
                        output_action="BLOCK",
                        output_enabled=True
                    )
                ],
                topics_tier_config=bedrock.CfnGuardrail.TopicsTierConfigProperty(
                    tier_name="STANDARD"
                )
            )
        )

        self.guardrail_version = bedrock.CfnGuardrailVersion(
            self, "AllNewGuardrailVersion",
            guardrail_identifier=self.guardrails.attr_guardrail_id,
            description="Guardrail with topic policies for cryptocurrency and extreme sports blocking"
        )

    def _create_sensitive_information_policy(self) -> bedrock.CfnGuardrail.SensitiveInformationPolicyConfigProperty:
        """
        Create sensitive information policy with PII entities and LATAM-specific regex patterns.

        CRITICAL DESIGN DECISION:
        - Patient identifiers (names, cédulas, medical records) are ALLOWED in INPUT for tool functionality
        - These same identifiers are ANONYMIZED in OUTPUT for privacy protection
        - This ensures patient lookup tools can function while protecting privacy in responses
        """
        return bedrock.CfnGuardrail.SensitiveInformationPolicyConfigProperty(
            pii_entities_config=[
                # NAME - Allow in input for patient lookup, anonymize in output
                # AGE - Detect but allow (medical relevance)
                bedrock.CfnGuardrail.PiiEntityConfigProperty(
                    type="AGE",
                    action="NONE",
                    input_action="NONE",
                    input_enabled=True,
                    output_action="NONE",
                    output_enabled=True
                ),
                # ADDRESS - Detect and anonymize
                bedrock.CfnGuardrail.PiiEntityConfigProperty(
                    type="ADDRESS",
                    action="ANONYMIZE",
                    input_action="NONE",
                    input_enabled=True,
                    output_action="ANONYMIZE",
                    output_enabled=True
                ),
                # EMAIL - Detect and anonymize
                bedrock.CfnGuardrail.PiiEntityConfigProperty(
                    type="EMAIL",
                    action="ANONYMIZE",
                    input_action="NONE",
                    input_enabled=True,
                    output_action="ANONYMIZE",
                    output_enabled=True
                ),
                # PHONE - Detect and anonymize (will catch LATAM formats)
                bedrock.CfnGuardrail.PiiEntityConfigProperty(
                    type="PHONE",
                    action="ANONYMIZE",
                    input_action="NONE",
                    input_enabled=True,
                    output_action="ANONYMIZE",
                    output_enabled=True
                ),
                # CREDIT_DEBIT_CARD_NUMBER - Detect and anonymize for billing/insurance
                bedrock.CfnGuardrail.PiiEntityConfigProperty(
                    type="CREDIT_DEBIT_CARD_NUMBER",
                    action="ANONYMIZE",
                    input_action="NONE",
                    input_enabled=True,
                    output_action="ANONYMIZE",
                    output_enabled=True
                )
            ],
            regexes_config=self._create_latam_regex_patterns()
        )

    def _create_latam_regex_patterns(self) -> list:
        """
        Create LATAM-specific regex patterns for healthcare data protection.
        """
        return [
            # Cédula de Ciudadanía Colombia (8-10 digits) - Allow in input, anonymize in output
            bedrock.CfnGuardrail.RegexConfigProperty(
                name="CedulaColombia",
                description="Cédula de Ciudadanía Colombia",
                pattern=r"\b\d{8,10}\b",
                action="ANONYMIZE",
                input_action="NONE",  # Allow cédulas in input for patient lookup
                input_enabled=True,
                output_action="ANONYMIZE",  # Anonymize cédulas in output for privacy
                output_enabled=True
            ),
            # LATAM Phone Numbers (various formats) - Detect and anonymize
            bedrock.CfnGuardrail.RegexConfigProperty(
                name="TelefonoLatam",
                description="Números telefónicos LATAM",
                pattern=r"\b(?:\+?[1-9]\d{1,3}[-.\s]?)?\(?[1-9]\d{2,3}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b",
                action="ANONYMIZE",
                input_action="NONE",
                input_enabled=True,
                output_action="ANONYMIZE",
                output_enabled=True
            ),
            # Número de Historia Clínica (Medical Record) - Allow in input, anonymize in output
            bedrock.CfnGuardrail.RegexConfigProperty(
                name="HistoriaClinica",
                description="Número de Historia Clínica",
                pattern=r"\b(?:HC|Historia|Expediente)\s*:?\s*\d{6,10}\b",
                action="ANONYMIZE",
                input_action="NONE",  # Allow medical record numbers in input for lookup
                input_enabled=True,
                output_action="ANONYMIZE",  # Anonymize medical record numbers in output
                output_enabled=True
            ),
            # Número de Seguro Social LATAM - Detect and anonymize
            bedrock.CfnGuardrail.RegexConfigProperty(
                name="SeguroSocialLatam",
                description="Número de Seguro Social LATAM",
                pattern=r"\b(?:EPS|ISSS|IMSS|Seguro)\s*:?\s*\d{8,12}\b",
                action="ANONYMIZE",
                input_action="NONE",
                input_enabled=True,
                output_action="ANONYMIZE",
                output_enabled=True
            ),
            # Medical License Numbers - Detect and anonymize
            bedrock.CfnGuardrail.RegexConfigProperty(
                name="LicenciaMedica",
                description="Números de licencia médica",
                pattern=r"\b(?:Lic|Licencia|Registro)\s*:?\s*[A-Z]{2,4}\d{4,8}\b",
                action="ANONYMIZE",
                input_action="NONE",
                input_enabled=True,
                output_action="ANONYMIZE",
                output_enabled=True
            ),
            # Patient ID Numbers - Allow in input, anonymize in output
            bedrock.CfnGuardrail.RegexConfigProperty(
                name="PacienteID",
                description="Números de identificación de paciente",
                pattern=r"\b(?:PAC|Patient|ID)\s*:?\s*\d{6,12}\b",
                action="ANONYMIZE",
                input_action="NONE",  # Allow patient IDs in input for lookup
                input_enabled=True,
                output_action="ANONYMIZE",  # Anonymize patient IDs in output
                output_enabled=True
            )
        ]

    @property
    def guardrail_id(self) -> str:
        """Return the guardrail ID."""
        return self.guardrails.attr_guardrail_id

    @property
    def guardrail_version_id(self) -> str:
        """Return the guardrail version ID."""
        return self.guardrail_version.attr_version

    @property
    def region(self) -> str:
        """Return the current region."""
        from aws_cdk import Stack
        return Stack.of(self).region

    @property
    def account(self) -> str:
        """Return the current account."""
        from aws_cdk import Stack
        return Stack.of(self).account
