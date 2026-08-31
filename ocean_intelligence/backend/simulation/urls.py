from django.urls import path
from simulation.views import WhatIfSimulationView

urlpatterns = [
    path('what-if/', WhatIfSimulationView.as_view(), name='what-if'),
]
