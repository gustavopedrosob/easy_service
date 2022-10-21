CBRCREL = "Cbrcrel"
CCRCFI = "Ccrcfi"
EPCFI = "Epcfi"
PRODUCTS = (CBRCREL, CCRCFI, EPCFI)

INSTALLMENT = "Parcelado"
IN_CASH = "À vista"

FIRST_PROPOSAL_DAYS_FOR_PAYMENT = 1
ELSE_PROPOSALS_DAYS_FOR_PAYMENT = 3

REFUSAL_REASONS = {
    "Desemprego": "O cliente está desempregado, portanto não pode negociar.",
    "Doença": "O cliente está doente, portanto não pode negociar.",
    "Terceiro vai negociar": "O cliente não quer negociar, pois informa que um terceiro irá negociar.",
    "Nega-se a ouvir": "O cliente não quis ouvir as propostas.",
    "Nega-se a pagar": "O cliente nega-se a pagar o débito.",
    "Fora de prazo": "O cliente pretende realizar o pagamento, porém o prazo não viabiliza uma negociação."
}
