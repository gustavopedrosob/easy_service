import re

DAYS_IN_ARREARS = re.compile(r"[1-9]\d{0,2}")
CPF = re.compile(r"(\d)(?!\1{10}|\1{2}\.\1{3}\.\1{3}-\1{2})(\d{10}|\d{2}\.\d{3}\.\d{3}-\d{2})")
PHONE = re.compile(r"\(?([14689][1-9]|2[12478]|3[1234578]|5[1345]|7[13457])"
                   r"((?<=\(\d{2}))?\)?\s{0,2}9?\s?\d{4}[\s-]?\d{4}")
BRL = re.compile(r"(?:R\$ {0,3})?[1-9]\d{0,2}(?:\.?\d{3})*,\d{2}", re.I)
EMAIL = re.compile(r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+", re.I)
PRODUCT = re.compile(r"(?P<CBR>cbr(?:crel)?)|(?P<CCR>ccr(?:cfi)?)|(?P<EP>ep(?:cfi)?)", re.I)
DATE = re.compile(r"(?:3[01]|[0-2]\d)/(?:0[1-9]|1[0-2])/\d{4}")
