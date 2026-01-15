# Guía de Tests

## Ejecutar todos los tests
```bash
pytest tests/ -v
```

## Ejecutar tests específicos
```bash
# Solo tests de pagos
pytest tests/test_pagos_servicio.py -v
pytest tests/test_pagos_repo.py -v

# Solo tests de faenas
pytest tests/test_faenas_servicio.py -v
```

## Cobertura de código
```bash
pytest tests/ --cov=src --cov-report=html
```

## Antes de ejecutar
Asegúrate de tener las dependencias instaladas:
```bash
pip install pytest pytest-mock
```
