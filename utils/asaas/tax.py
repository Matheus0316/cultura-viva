from decimal import Decimal, ROUND_HALF_UP

def calculate_gross_up_credit_card(net_value, installments=1):
    """
    Calcula o valor bruto (gross up) para que o vendedor receba o valor líquido desejado,
    embutindo as taxas de cartão do Asaas.

    Taxas:
    - À vista: 2,99% + R$ 0,49
    - 2 a 6 parcelas: 3,49% + R$ 0,49
    - 7 a 12 parcelas: 3,99% + R$ 0,49
    """
    net_value = Decimal(str(net_value))
    fixed_fee = Decimal('0.49')
    
    if installments == 1:
        percentage_fee = Decimal('0.0299')
    elif 2 <= installments <= 6:
        percentage_fee = Decimal('0.0349')
    elif 7 <= installments <= 12:
        percentage_fee = Decimal('0.0399')
    else:
        # Assume a taxa máxima para mais de 12 parcelas
        percentage_fee = Decimal('0.0429')

    # Fórmula: Bruto = (Líquido + Taxa Fixa) / (1 - Taxa Percentual)
    gross_value = (net_value + fixed_fee) / (Decimal('1') - percentage_fee)
    
    return gross_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_gross_up_pix(net_value):
    net_value = Decimal(str(net_value))
    fixed_fee = Decimal('0.99')
    
    gross_value = (net_value + fixed_fee)
    
    return gross_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
def calculate_net_value(gross_value, payment_method, installments=1):
    gross_value = Decimal(str(gross_value))
    
    if payment_method == 'PIX':
        fixed_fee = Decimal('0.99')
        return (gross_value - fixed_fee).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    # Crédito
    fixed_fee = Decimal('0.49')
    if installments == 1:
        percentage_fee = Decimal('0.0299')
    elif 2 <= installments <= 6:
        percentage_fee = Decimal('0.0349')
    elif 7 <= installments <= 12:
        percentage_fee = Decimal('0.0399')
    else:
        percentage_fee = Decimal('0.0429')

    net_value = (gross_value * (Decimal('1') - percentage_fee)) - fixed_fee
    return net_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
