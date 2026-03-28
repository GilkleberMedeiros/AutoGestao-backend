# AutoGestão 

Projeto de Aplicativo mobile com backend (self-developed) para gerenciamento de projetos e finanças com foco no público autônomo e freelancer (pensado originalmente para profissionais  da área elétrica).  


## Comandos
### Rodar a aplicação em desenvolvimento
```bash
# Antes de iniciar a API, rode
uv run manage.py makemigrations 
# e
uv run manage.py migrate
# para criar as mais novas migrações e aplicar no banco de dados

uv run manage.py runserver
```

### Rodar os testes em desenvolvimento
```bash
uv run manage.py test
```