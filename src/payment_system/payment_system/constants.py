class AccountType(object):

    USER_ACCOUNT = 'user_account'
    TAXES_ACCOUNT = 'taxes_account'

    CHOICES = [
        (USER_ACCOUNT, 'User account'),
        (TAXES_ACCOUNT, 'Taxes account')
    ]


class PaymentTransactionStatus(object):
    SCHEDULED = 'scheduled'
    RATE_CALCULATED = 'rate_calculated'
    USER_MONEY_TRANSMITTED = 'user_money_transmitter'
    COMPLETED = 'completed'
    REJECTED = 'rejected'

    CHOICES = [
        (SCHEDULED, 'Scheduled'),
        (COMPLETED, 'Completed'),
        (RATE_CALCULATED, 'Rate calculated'),
        (REJECTED, 'rejected'),
        (USER_MONEY_TRANSMITTED, 'User money transmitter')
    ]
