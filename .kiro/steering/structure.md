# Project Structure

## Root Level

- `app.py`: CDK application entry point - defines and synthesizes the main stack
- `cdk.json`: CDK configuration file specifying app command and context settings
- `requirements.txt`: Production dependencies for CDK infrastructure
- `requirements-dev.txt`: Development dependencies (testing, linting)
- `source.bat`: Windows batch file for environment activation
- `.venv/`: Python virtual environment (auto-generated)

## Infrastructure Code

- `aw_some_builder2/`: Main CDK stack module
  - `aw_some_builder2_stack.py`: Primary infrastructure stack definition
  - Contains AWS resource definitions and configurations

## Application Code

- `apps/`: Application-specific code separate from infrastructure
  - `apps/core/`: Core business logic and services
    - `apps/core/api/`: API endpoints and handlers
  - `apps/frontend/`: Frontend application code (currently empty)

## Documentation & Samples

- `docs/`: Project documentation and sample data
  - `notes_spec.md`: Project requirements and specifications
  - `AWSomeBuilder2*.pdf/png/drawio`: Architecture diagrams
  - `bda_sample/`: Sample BDA (Bedrock Data Automation) outputs
  - `healthscribesample/`: Sample HealthScribe API responses
  - `transcribemedicalsample/`: Sample Transcribe Medical outputs
  - `historiamedica*`: Sample medical records and Textract processing results
  - `test_speech_esmx.mp3`: Sample audio file for testing

## Development Tools

- `.kiro/`: Kiro IDE configuration and steering rules
  - `.kiro/steering/`: AI assistant guidance documents
  - `.kiro/specs/`: Project specifications and requirements
- `.git/`: Git version control
- `.gitignore`: Git ignore patterns
- `agents/`: AI agent configurations (currently empty)

## Naming Conventions

- **Stacks**: PascalCase ending with "Stack" (e.g., `AwSomeBuilder2Stack`)
- **Resources**: Follow AWS CDK naming conventions with descriptive prefixes
- **Files**: snake_case for Python files, kebab-case for config files
- **Folders**: lowercase with underscores for Python modules, descriptive names for docs

## Key Patterns

- Infrastructure code is separated from application code
- Sample data and documentation are well-organized in `docs/`
- CDK stack follows standard AWS CDK project structure
- Healthcare-specific samples are preserved for reference during development
