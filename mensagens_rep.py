def gerar_mensagens(resumo):
    propostas = resumo.get("propostas", {})
    proposta_indicada = resumo.get("proposta_indicada", None)
    saldo_original = resumo.get("saldo_devedor_com_juros", 0)
    saldo_sem_juros = resumo.get("saldo_devedor_sem_juros", 0)
    
    def calcular_desconto(valor_original, valor_final):
        desconto = valor_original - valor_final
        percentual = (desconto / valor_original) * 100 if valor_original > 0 else 0
        return desconto, percentual
    
    msg_prop_1 = None
    msg_prop_2 = None
    msg_prop_3 = None
    
    if "proposta_1" in propostas:
        p = propostas["proposta_1"]
        desconto, percentual = calcular_desconto(saldo_original, p['valor_total'])
        msg_prop_1 = (
            f"💰 Seu saldo devedor atual é de R$ {saldo_original:,.2f}, "
            f"pensamos em uma proposta que reduz para R$ {p['valor_total']:,.2f} "
            f"(desconto de R$ {desconto:,.2f} - {percentual:.2f}%). "
            f"Você pode parcelar esse valor em {p['quantidade_parcelas']} vezes de R$ {p['valor_parcela']:,.2f}.\n"
            "Essa é a condição padrão, simples e direta, para você começar a se organizar. Vamos juntos nessa?!!! 💪"
        )

    if "proposta_2" in propostas:
        p = propostas["proposta_2"]
        desconto, percentual = calcular_desconto(saldo_original, p['valor_total'])
        msg_prop_2 = (
            f"✨ Boa notícia! Estamos oferecendo uma oferta irrecusável, com desconto de R$ {desconto:,.2f} "
            f"({percentual:.2f}%), totalizando R$ {p['valor_total']:,.2f}. "
            f"Você pode parcelar em {p['quantidade_parcelas']} vezes de R$ {p['valor_parcela']:,.2f}.\n"
            "É uma ótima chance para aliviar o orçamento e ainda colocar as contas em dia! 😊"
        )

    if "proposta_3" in propostas:
        p = propostas["proposta_3"]
        desconto, percentual = calcular_desconto(saldo_original, p['valor_total'])
        msg_prop_3 = (
            f"🎉 Excelente opção! A proposta 3 oferece desconto de R$ {desconto:,.2f} "
            f"({percentual:.2f}%), reduzindo o total para R$ {p['valor_total']:,.2f}. "
            f"São {p['quantidade_parcelas']} parcelas de R$ {p['valor_parcela']:,.2f}.\n"
            "Essa é a condição mais vantajosa que conseguimos oferecer pra você! Aproveite essa oportunidade. 🚀"
        )

    if proposta_indicada:
        p = proposta_indicada
        desconto, percentual = calcular_desconto(saldo_original, p['valor_total'])
        mensagem_indicada = (
            f"🎯 Encontramos a proposta ideal para você! Com desconto de R$ {desconto:,.2f} "
            f"({percentual:.2f}%), o valor total fica em R$ {p['valor_total']:,.2f}, "
            f"parcelado em {p['quantidade_parcelas']} vezes de R$ {p['valor_parcela']:,.2f}.\n"
            "Essa é a melhor opção, feita especialmente para facilitar sua negociação. Estamos aqui para ajudar! 🤝"
        )
    else:
        mensagem_indicada = (
            "Gostaríamos muito de atender ao valor solicitado, mas não é viável neste momento.\n"
            "Mas não se preocupe, estou te passando a melhor condição que conseguimos oferecer agora.\n"
        )

    return msg_prop_1, msg_prop_2, msg_prop_3, mensagem_indicada


