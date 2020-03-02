from django_filters import filterset, filters

from payment_system.models import PaymentTransaction


class OutgoingTransactionFilter(filterset.FilterSet):

    class Meta:
        model = PaymentTransaction
        fields = {
            'id': ['exact'],
            'created_at': ['gte', 'lte', 'exact'],
            'processed_at': ['gte', 'lte', 'exact'],
            'destination': ['exact'],
            'status': ['exact', 'in'],
            'amount': ['gte', 'lte', 'exact'],
            'currency': ['exact', 'in']
        }


class IncomingTransactionFilter(filterset.FilterSet):

    class Meta:
        model = PaymentTransaction
        fields = {
            'id': ['exact'],
            'created_at': ['gte', 'lte', 'exact'],
            'processed_at': ['gte', 'lte', 'exact'],
            'source': ['exact'],
            'amount': ['gte', 'lte', 'exact']
        }
