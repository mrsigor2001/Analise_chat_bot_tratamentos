import re

def validar_cpf(cpf):
    cpf = re.sub(r'\D', '', cpf or '')
    if len(cpf) != 11:
        return None
    if cpf == cpf[0] * 11:
        return None

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10) % 11
    digito1 = 0 if digito1 == 10 else digito1
    if digito1 != int(cpf[9]):
        return None

    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10) % 11
    digito2 = 0 if digito2 == 10 else digito2
    if digito2 != int(cpf[10]):
        return None

    return cpf
