CBRCREL = "Cbrcrel"
CCRCFI = "Ccrcfi"
EPCFI = "Epcfi"
PRODUCTS = (CBRCREL, CCRCFI, EPCFI)

CBRCREL_MAX_INSTALMENTS = 24
CCRCFI_MAX_INSTALMENTS = 18
EPCFI_MAX_INSTALMENTS = 18

MAX_INSTALMENTS = {CBRCREL: CBRCREL_MAX_INSTALMENTS,
                   CCRCFI: CCRCFI_MAX_INSTALMENTS,
                   EPCFI: EPCFI_MAX_INSTALMENTS}

CANCEL_IN_DAYS = 10

INSTALLMENT = "Parcelado"
IN_CASH = "À vista"

IS_INSTALLMENT_TABLE = {True: INSTALLMENT, False: IN_CASH}

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

COUNTER_PROPOSAL = "Contra-Proposta"
ADD = "Adicionar"
EASY_SERVICE = "Atendimento fácil"
CPF = "CPF"
PHONE = "Telefone"
EMAIL = "Email"
PRODUCT = "Produto"
DELAYED = "Dias em atraso"
INSTALLMENTS = "Quantidade de parcelas"
FIRST_INSTALLMENT = "Entrada"
ELSE_INSTALLMENT = "Valor de parcelas"
D_PLUS = "Prazo para pagamento em dias"
DUE_DATE = "Vencimento"
TOTAL = "Total"
DISCOUNT = "Desconto sobre a ultima proposta"
OPTIONS = "Opções"
TOOLS = "Ferramentas"
ABOUT = "Sobre"
PAYED = "Pago"
VALUE = "Valor"
CREATE_DATE = "Data de criação"
EXCEPTION_PROPOSAL_HISTORIC = "Histórico de propostas de exceção"
AGREEMENT_CONTROL = "Controle de acordos"
