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
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'

    CHOICES = [
        (SCHEDULED, 'Scheduled'),
        (IN_PROGRESS, 'In progress'),
        (COMPLETED, 'Completed'),
        (RATE_CALCULATED, 'Rate calculated'),
    ]
