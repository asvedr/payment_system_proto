from django_filters import filterset, filters

from payment_system.models import PaymentTransaction


class OutgoingTransactionFilter(filterset.FilterSet):

    class Meta:
        model = PaymentTransaction
        fields = {
            'created_at': ['gt', 'lt', 'gte', 'lte', 'exact'],
            'processed_at': ['gt', 'lt', 'gte', 'lte', 'exact'],
            'destination': ['exact'],
            'status': ['exact', 'in'],
            'amount': ['gt', 'lt', 'gte', 'lte', 'exact'],
            'currency': ['exact', 'in'],
            'spent': ['gt', 'lt', 'gte', 'lte', 'exact'],
        }


class IncomingTransactionFilter(filterset.FilterSet):

    class Meta:
        model = PaymentTransaction
        fields = {
            'created_at': ['gt', 'lt', 'gte', 'lte', 'exact'],
            'processed_at': ['gt', 'lt', 'gte', 'lte', 'exact'],
            'source': ['exact'],
            'amount': ['gt', 'lt', 'gte', 'lte', 'exact'],
        }
